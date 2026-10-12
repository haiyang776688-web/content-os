"""Phase 2 endpoints attached to the existing local workbench."""
from pathlib import Path
from typing import Literal
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import Field
from vnext.contracts import StrictModel, Role
from vnext.phase2.fonts import Fonts
from vnext.phase2.knowledge import Knowledge
from vnext.phase2.production import CommandBus, Production, Review, PATTERNS, mechanical
from vnext.phase2.intelligence import AssetIntelligence, VisualQA
from vnext.phase2.stages import StageCache


class CommandIn(StrictModel):
    target: str
    operation: str
    arguments: dict = Field(default_factory=dict)
    actor: str = 'HUMAN'
    actor_type: Literal['HUMAN','AGENT','SYSTEM'] = 'HUMAN'
    reason: str = 'Manual edit'
    expected_revision: str | None = None


class DataIn(StrictModel):
    payload: dict
    actor: str


class GateIn(StrictModel):
    artifact_id: str
    decision: str
    reviewer: str = Field(min_length=1)
    comments: str = ''
    beat_ids: list[str] | None = None
    accepted_risks: list[str] = Field(default_factory=list)


def attach(app,store,root,runtime):
    from vnext.phase2.hardening.api import attach as hardening_attach
    hardening_attach(app,store,root)
    fonts=Fonts(store); knowledge=Knowledge(store); production=Production(store)
    def checked(fn):
        try: return fn()
        except PermissionError as error: raise HTTPException(403,str(error)) from error
        except KeyError as error: raise HTTPException(404,str(error)) from error
        except Exception as error: raise HTTPException(400,str(error)) from error

    @app.get('/phase2.js')
    def javascript(): return FileResponse(root/'vnext/apps/workbench/phase2.js',media_type='application/javascript')

    @app.post('/api/projects/{pid}/phase2/enable')
    def enable(pid:str): return checked(lambda:knowledge.initialize(pid))

    @app.get('/api/projects/{pid}/phase2')
    def state(pid:str):
        from vnext.phase2.alignment.runtime import AlignmentRuntime
        return checked(lambda:{'project':store.get_project(pid).model_dump(),'artifacts':store.artifacts(pid),
            'design_table':production.design_table(pid),'patterns':[p.model_dump() for p in PATTERNS],
            'stages':StageCache(store).states(pid),'rules_read_only':True,
            'alignment':AlignmentRuntime(store).status(pid).model_dump()})

    @app.get('/api/projects/{pid}/phase2/alignment')
    def alignment_state(pid:str):
        from vnext.phase2.alignment.runtime import AlignmentRuntime
        return checked(lambda:AlignmentRuntime(store).status(pid).model_dump())

    @app.post('/api/projects/{pid}/phase2/alignment/mode')
    def alignment_mode(pid:str,value:DataIn):
        def update():
            if value.actor!='HUMAN':raise PermissionError('HUMAN_ALIGNMENT_OPT_IN_REQUIRED')
            mode=value.payload.get('mode')
            if mode not in ('CURRENT','ALIGNED_OPT_IN'):raise ValueError('INVALID_TIMING_MODE')
            project=store.get_project(pid);project.timing_mode=mode;store.save_project(project)
            from vnext.phase2.alignment.runtime import AlignmentRuntime
            return AlignmentRuntime(store).status(pid).model_dump()
        return checked(update)

    @app.post('/api/projects/{pid}/phase2/alignment/bindings')
    def alignment_bindings(pid:str,value:DataIn):
        from vnext.phase2.alignment.runtime import AlignmentRuntime
        return checked(lambda:AlignmentRuntime(store).create_bindings(pid,value.payload,value.actor))

    @app.post('/api/projects/{pid}/phase2/alignment/enqueue')
    def alignment_enqueue(pid:str):
        from vnext.phase2.alignment.runtime import AlignmentRuntime
        return checked(lambda:AlignmentRuntime(store).enqueue(pid))

    @app.post('/api/projects/{pid}/phase2/alignment/{job_id}/cancel')
    def alignment_cancel(pid:str,job_id:str):
        from vnext.phase2.alignment.runtime import AlignmentRuntime
        return checked(lambda:AlignmentRuntime(store).cancel(pid,job_id))

    @app.post('/api/projects/{pid}/phase2/source')
    def source(pid:str,value:DataIn): return checked(lambda:knowledge.source(pid,value.payload,value.actor))

    @app.post('/api/projects/{pid}/phase2/facts')
    def facts(pid:str,value:DataIn): return checked(lambda:knowledge.fact_pack(pid,value.payload,value.actor))

    @app.post('/api/projects/{pid}/phase2/disagreement')
    def disagreement(pid:str,value:DataIn):
        if value.actor!='AUDIT': raise HTTPException(403,'AUDIT_REQUIRED')
        return checked(lambda:knowledge.disagreement(pid,value.payload['target_artifact_id'],value.payload['opinions']))

    @app.post('/api/projects/{pid}/phase2/disagreement/{aid}/resolve')
    def resolve(pid:str,aid:str,value:DataIn):
        return checked(lambda:knowledge.resolve_disagreement(pid,aid,value.payload['evidence_ids'],value.payload['reason'],value.actor))

    @app.post('/api/projects/{pid}/phase2/script')
    def script(pid:str,value:DataIn): return checked(lambda:CommandBus(store).execute(pid,'SCRIPT','REPLACE_SCRIPT',
        {'payload':value.payload},actor=value.actor,actor_type='HUMAN' if value.actor=='HUMAN' else 'AGENT'))

    @app.post('/api/projects/{pid}/phase2/humanize/{aid}')
    def humanize(pid:str,aid:str,value:DataIn):
        if value.actor!='SCRIPT_EDITOR': raise HTTPException(403,'SCRIPT_EDITOR_REQUIRED')
        return checked(lambda:CommandBus(store).execute(pid,'SCRIPT','HUMANIZE',{'original_id':aid,'payload':value.payload},
            actor='SCRIPT_EDITOR',actor_type='AGENT'))

    @app.post('/api/projects/{pid}/phase2/rules/{kind}')
    def rules(pid:str,kind:str,value:DataIn): return checked(lambda:knowledge.rules(pid,kind,value.payload,value.actor))

    @app.post('/api/projects/{pid}/phase2/director')
    def director(pid:str,value:DataIn): return checked(lambda:CommandBus(store).execute(pid,'DIRECTOR_IR','REPLACE_IR',
        {'payload':value.payload},actor=value.actor,actor_type='AGENT'))

    @app.post('/api/projects/{pid}/phase2/commands')
    def command(pid:str,value:CommandIn):
        fields=value.model_dump();fields['args']=fields.pop('arguments')
        return checked(lambda:CommandBus(store).execute(pid,**fields))

    @app.post('/api/projects/{pid}/phase2/edt')
    def edt(pid:str):
        def run():
            inputs=production.edt_inputs(pid)
            from vnext.phase2.hardening.visual import LAYOUTS
            from vnext.storage.store import digest
            return StageCache(store).run(pid,'EDT',inputs,lambda:CommandBus(store).execute(pid,'EDT','GENERATE',{}),
                config={'layout_hash':digest(LAYOUTS),'resolver_source':__import__('hashlib').sha256((root/'vnext/phase2/hardening/visual.py').read_bytes()).hexdigest()})
        return checked(run)

    @app.post('/api/projects/{pid}/phase2/storyboard')
    def storyboard(pid:str, expected_director_revision:str|None=None, expected_edt_revision:str|None=None):
        def run():
            ir=store.latest(pid,'DIRECTOR_IR'); visual=store.latest(pid,'VISUAL_EDT')
            if not ir or not visual:raise ValueError('DIRECTOR_EDT_REQUIRED')
            edt=store.latest(pid,'EDT')
            if expected_director_revision and ir['artifact_id']!=expected_director_revision:
                raise ValueError('EDIT_REVISION_CONFLICT')
            if expected_edt_revision and (not edt or edt['artifact_id']!=expected_edt_revision):
                raise ValueError('EDIT_REVISION_CONFLICT')
            from vnext.migration.legacy import sha
            return StageCache(store).run(pid,'STORYBOARD',[ir['artifact_id'],visual['artifact_id']],lambda:production.storyboard(pid,root),
                config={'renderer_source':sha(root/'vnext/renderers/remotion/project/src/Composition.tsx')})
        return checked(run)

    @app.post('/api/projects/{pid}/phase2/storyboard-job')
    def storyboard_job(pid:str, expected_director_revision:str|None=None, expected_edt_revision:str|None=None):
        def submit():
            from vnext.core.jobs.engine import JobEngine
            ir=store.latest(pid,'DIRECTOR_IR');edt=store.latest(pid,'EDT');visual=store.latest(pid,'VISUAL_EDT')
            if not ir or not edt or not visual:raise ValueError('DIRECTOR_EDT_REQUIRED')
            if expected_director_revision!=ir['artifact_id'] or expected_edt_revision!=edt['artifact_id']:
                raise ValueError('EDIT_REVISION_CONFLICT')
            target=':'.join((ir['artifact_id'],edt['artifact_id'],visual['artifact_id']))
            return JobEngine(store).submit(pid,'P0_STORYBOARD',target,
                lambda: storyboard(pid,expected_director_revision,expected_edt_revision),
                idempotency_key='P0_STORYBOARD:'+target,stage='Rendering storyboard stills',
                current_target=lambda:':'.join((
                    (store.latest(pid,'DIRECTOR_IR') or {}).get('artifact_id',''),
                    (store.latest(pid,'EDT') or {}).get('artifact_id',''),
                    (store.latest(pid,'VISUAL_EDT') or {}).get('artifact_id','')))).model_dump()
        return checked(submit)

    @app.get('/api/projects/{pid}/phase2/storyboard/{aid}/{beat}/{index}/file')
    def storyboard_file(pid:str,aid:str,beat:str,index:int):
        board=checked(lambda:knowledge.require(pid,aid,'STORYBOARD'))
        entry=next((x for x in board['payload']['entries'] if x['beat_id']==beat),None)
        if not entry or index not in (0,1): raise HTTPException(404,'STILL_NOT_FOUND')
        return FileResponse(entry['images'][index])

    @app.post('/api/projects/{pid}/phase2/storyboard/gate')
    def story_gate(pid:str,value:GateIn):
        return checked(lambda:production.storyboard_gate(pid,value.artifact_id,value.decision,value.reviewer,value.comments,value.beat_ids))

    @app.post('/api/projects/{pid}/phase2/storyboard-motion')
    def story_motion(pid:str):
        from vnext.renderers.remotion.adapter import RemotionAdapter
        return checked(lambda:RemotionAdapter(root,store).storyboard_motion(pid,store.get_project(pid).timeline_artifact_id))

    @app.get('/api/projects/{pid}/phase2/storyboard-motion/{aid}/file')
    def story_motion_file(pid:str,aid:str):
        artifact=checked(lambda:knowledge.require(pid,aid,'STORYBOARD_MOTION'))
        return FileResponse(artifact['payload']['preview_path'],media_type='video/mp4')

    @app.post('/api/projects/{pid}/phase2/mechanical-qa')
    def mechanical_qa(pid:str):
        def run():
            aid=store.get_project(pid).timeline_artifact_id
            report=mechanical(store,pid,aid,require_voice=True)
            result=store.create_artifact(pid,'MECHANICAL_QA',report,role='MECHANICAL_QA',dependencies=[store.dependency(aid)]).model_dump()
            return StageCache(store).record(pid,'MECHANICAL_QA',[aid],result)
        return checked(run)

    @app.post('/api/projects/{pid}/phase2/video-qa')
    async def videoqa(pid:str,request:Request):
        data=await request.json()
        def run():
            result=VisualQA(store).run(pid,data['render_id'],data.get('worker','MOCK'),data.get('issues'),data.get('upload_confirmed',False))
            return StageCache(store).record(pid,'VIDEO_QA',[data['render_id']],result,worker=data.get('worker','MOCK'))
        return checked(run)

    @app.post('/api/projects/{pid}/phase2/review')
    def review(pid:str):
        def run():
            result=Review(store).build(pid)
            return StageCache(store).record(pid,'REVIEW',[d['artifact_id'] for d in result['dependencies']],result)
        return checked(run)

    @app.post('/api/projects/{pid}/phase2/review/gate')
    def reviewgate(pid:str,value:GateIn):
        return checked(lambda:Review(store).gate(pid,value.artifact_id,value.decision,value.reviewer,value.accepted_risks,value.comments))

    @app.post('/api/projects/{pid}/phase2/media/{aid}/analyze')
    async def analyze(pid:str,aid:str,request:Request):
        annotation=await request.json()
        return checked(lambda:AssetIntelligence(store).analyze(pid,aid,annotation))

    @app.get('/api/projects/{pid}/phase2/media/search')
    def search(pid:str,q:str=''): return checked(lambda:AssetIntelligence(store).search(pid,q))

    @app.post('/api/projects/{pid}/phase2/media/{aid}/caption-cloud')
    def cloud_caption(pid:str,aid:str,value:DataIn):
        if value.actor!='HUMAN':raise HTTPException(403,'HUMAN_UPLOAD_DECISION_REQUIRED')
        return checked(lambda:AssetIntelligence(store).caption_cloud(pid,aid,value.payload.get('upload_confirmed',False)))

    @app.post('/api/projects/{pid}/phase2/media/{aid}/cloud-policy')
    def media_policy(pid:str,aid:str,value:DataIn):
        if value.actor!='HUMAN':raise HTTPException(403,'HUMAN_PRIVACY_DECISION_REQUIRED')
        from vnext.media.library.service import MediaLibrary
        return checked(lambda:MediaLibrary(store).cloud_policy(pid,aid,value.payload['policy']))

    @app.get('/api/fonts')
    def list_fonts(q:str='',source:str='',classification:str=''): return fonts.list(q,source,classification)

    @app.post('/api/fonts/rescan')
    async def scan(request:Request):
        data=await request.json()
        return checked(lambda:fonts.scan(data.get('paths'),data.get('source','SYSTEM')))

    @app.post('/api/fonts/import')
    async def import_font(request:Request):
        data=await request.json()
        return checked(lambda:fonts.scan([data['path']],'USER'))

    @app.get('/api/fonts/{font_id}')
    def font_detail(font_id:str): return checked(lambda:fonts.get(font_id).model_dump())

    @app.get('/api/fonts/{font_id}/file')
    def font_file(font_id:str):
        value=checked(lambda:fonts.face(font_id))
        return FileResponse(value.preview_path,media_type='font/otf',headers={'X-Font-SHA256':value.preview_hash})

    @app.get('/api/fonts/{font_id}/coverage')
    def coverage(font_id:str,text:str):
        def inspect():
            from fontTools.ttLib import TTFont
            value=fonts.face(font_id); font=TTFont(value.preview_path,lazy=True)
            cmap=font.getBestCmap() or {}; font.close()
            return {'missing':sorted({c for c in text if not c.isspace() and ord(c) not in cmap}),
                    'font_hash':value.preview_hash,'preview_only':True}
        return checked(inspect)

    @app.get('/api/projects/{pid}/typography-profiles')
    def profiles(pid:str): return checked(lambda:store.artifacts(pid,'TYPOGRAPHY_PROFILE'))
