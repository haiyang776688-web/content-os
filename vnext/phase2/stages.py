"""Rebuildable stage cache. Artifacts, never this projection, define truth."""
import json
from vnext.phase2.contracts import StageState
from vnext.phase2.knowledge import Knowledge
from vnext.storage.store import digest

STAGES=['RESEARCH','SCRIPT_PRIMARY','SCRIPT_EDITOR','AUDIT','H2','DIRECTOR','MEDIA','STORYBOARD',
        'ALIGNMENT',
        'VOICE','EDT','RENDER','MECHANICAL_QA','VIDEO_QA','REVIEW']


class StageCache:
    active_runs=set()
    def __init__(self,store):
        self.store=store
        with store.connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS stage_cache(project_id TEXT, stage TEXT, data TEXT, PRIMARY KEY(project_id,stage))')

    def run(self,pid,stage,inputs,operation,config=None,worker='',prompt='',skills=''):
        if stage not in STAGES: raise ValueError('UNKNOWN_STAGE')
        from vnext.phase2.knowledge import reusable_script
        for aid in inputs:
            item=self.store.get_artifact(aid)
            if item['project_id']!=pid:raise ValueError('CROSS_PROJECT_ARTIFACT')
            if not (stage=='SCRIPT_EDITOR' and reusable_script(self.store,aid)):
                Knowledge(self.store).require(pid,aid)
        value=StageState(stage=stage,input_hash=digest([(a,self.store.get_artifact(a)['output_hash']) for a in inputs]),
            config_hash=digest(config or {}),worker=worker,prompt=prompt,skills=skills,status='RUNNING')
        old=self.store.latest(pid,'STAGE_'+stage)
        if old:
            cached=StageState.model_validate(old['payload'])
            if all(getattr(cached,f)==getattr(value,f) for f in ('input_hash','config_hash','worker','prompt','skills')):
                if cached.output_artifact and (self.store.is_usable_input(cached.output_artifact) or
                    stage in ('SCRIPT_PRIMARY','SCRIPT_EDITOR') and reusable_script(self.store,cached.output_artifact)):
                    return {**self.store.get_artifact(cached.output_artifact),'stage_cache_hit':True,
                        'historical_stage_output':not self.store.is_usable_input(cached.output_artifact)}
        self._save(pid,value)
        self.active_runs.add((str(self.store.database),pid,stage))
        try:
            result=operation()
            aid=result['artifact_id']
            Knowledge(self.store).require(pid,aid)
            value.output_artifact=aid
            value.status='COMPLETED'
            self.store.create_artifact(pid,'STAGE_'+stage,value.model_dump(),role='STAGE_CACHE',
                dependencies=[self.store.dependency(x) for x in dict.fromkeys([*inputs,aid])
                    if x==aid or self.store.get_artifact(x)['artifact_type']!=result['artifact_type']])
            self._save(pid,value)
            return result
        except Exception as error:
            value.status='FAILED'; value.error=str(error)
            self._save(pid,value)
            self.store.event(pid,'STAGE_FAILED',stage=stage,error=str(error))
            raise
        finally:
            self.active_runs.discard((str(self.store.database),pid,stage))

    def record(self,pid,stage,inputs,result,config=None,worker='',prompt='',skills=''):
        """Record checks that must run fresh (file availability, QA and human gates)."""
        aid=result['artifact_id']
        value=StageState(stage=stage,input_hash=digest([(a,self.store.get_artifact(a)['output_hash']) for a in inputs]),
            config_hash=digest(config or {}),worker=worker,prompt=prompt,skills=skills,
            output_artifact=aid,status='COMPLETED')
        self.store.create_artifact(pid,'STAGE_'+stage,value.model_dump(),role='STAGE_CACHE',
            dependencies=[self.store.dependency(a) for a in dict.fromkeys([*inputs,aid])
                if a==aid or self.store.get_artifact(a)['artifact_type']!=result['artifact_type']])
        self._save(pid,value)
        return result

    def _save(self,pid,value):
        with self.store.connection() as db:
            db.execute('INSERT OR REPLACE INTO stage_cache VALUES (?,?,?)',(pid,value.stage,value.model_dump_json()))

    def states(self,pid):
        result=[]
        with self.store.connection() as db:
            rows=db.execute('SELECT stage,data FROM stage_cache WHERE project_id=?',(pid,)).fetchall()
        cached={r['stage']:json.loads(r['data']) for r in rows}
        for stage in STAGES:
            item=self.store.latest(pid,'STAGE_'+stage)
            value=cached.get(stage) or (item['payload'].copy() if item else {'stage':stage,'status':'CLEAN'})
            if value.get('output_artifact') and not self.store.is_usable_input(value['output_artifact']):
                from vnext.phase2.knowledge import reusable_script
                if stage in ('SCRIPT_PRIMARY','SCRIPT_EDITOR') and reusable_script(self.store,value['output_artifact']):
                    value['historical_stage_output']=True
                else:value['status']='DIRTY'
            if value.get('status')=='RUNNING' and (str(self.store.database),pid,stage) not in self.active_runs:
                value['status']='BLOCKED'; value['error']='Interrupted run; rerun this stage'
            result.append(value)
        return result
