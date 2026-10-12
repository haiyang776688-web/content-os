"""Explicit file identity pins and hash-checked relink; locale is excluded."""
import json
from pathlib import Path
from vnext.storage.store import digest
from vnext.migration.legacy import sha
ROOT=Path(__file__).resolve().parents[3]

class Dependencies:
    def __init__(self,store,root=ROOT):self.store,self.root=store,Path(root)
    def path(self,pid):return self.store.root/'projects'/pid/'dependency_relinks.json'
    def relinks(self,pid):
        p=self.path(pid);return json.loads(p.read_text()) if p.exists() else {}
    def resolved(self,pid,aid,original,expected):
        path=Path(self.relinks(pid).get(aid,str(original)))
        if not path.is_file() or sha(path)!=expected:raise ValueError("DEPENDENCY_HASH_OR_LOCATION_INVALID:"+aid)
        return path
    def model_config(self,pid):
        p=self.store.get_project(pid)
        # Neither UI locale nor credentials are emitted or hashed into artifacts.
        config={k:getattr(p,k) for k in ('worker_assignments','fallback_policy','fallback_workers','privacy_mode','model_pricing','content_language','subtitle_language')}
        from vnext.registries.catalog import WORKERS,ROLE_CONTRACTS,PROMPTS
        from vnext.secrets.store import SecretStore
        secrets=SecretStore()
        selected={p.worker_assignments.get(role.value,contract.default_worker) for role,contract in ROLE_CONTRACTS.items()}|set(p.fallback_workers)
        config['worker_configuration']={wid:{'model':secrets.get(WORKERS[wid].model_env or '') or WORKERS[wid].model,'protocol':WORKERS[wid].protocol.value,'endpoint_hash':digest(secrets.get(WORKERS[wid].endpoint_env or ''))} for wid in sorted(selected) if wid in WORKERS}
        return config
    def pin_config(self,pid,role=None):
        payload=self.model_config(pid)
        kind='MODEL_EXECUTION_CONFIG'+('_'+role if role else '')
        if role:
            from vnext.registries.catalog import ROLE_CONTRACTS
            from vnext.contracts import Role
            worker=payload['worker_assignments'].get(role,ROLE_CONTRACTS[Role(role)].default_worker)
            payload['worker_assignments']={role:worker}
            payload['worker_configuration']={wid:payload['worker_configuration'].get(wid) for wid in sorted({worker,*payload['fallback_workers']})}
            from vnext.registries.catalog import PROMPTS
            payload['prompt_hash']=digest(PROMPTS[ROLE_CONTRACTS[Role(role)].prompt_id])
        old=self.store.latest(pid,kind)
        if old and old['output_hash']==digest(payload):return old
        return self.store.create_artifact(pid,kind,payload,role='HUMAN').model_dump()
    def collect(self,pid):
        p=self.store.get_project(pid);items=[];relinks=self.relinks(pid)
        old=self.store.latest(pid,'PROJECT_DEPENDENCY_MANIFEST');old_items={i['asset_id']:i for i in old['payload']['items']} if old else {}
        def add(kind,aid,path,expected=None):
            path=Path(path);prior=old_items.get(aid)
            expected=expected or (prior['expected_hash'] if prior else sha(path) if path.is_file() else '')
            location=relinks.get(aid,str(path));resolved=Path(location)
            status='MISSING' if not resolved.is_file() else 'HASH_MISMATCH' if not expected or sha(resolved)!=expected else 'RESOLVED'
            if status=='MISSING' and str(path)!=location:status='RELINK_REQUIRED'
            items.append({'kind':kind,'asset_id':aid,'expected_hash':expected,'original_location':str(path),'resolved_location':location,'status':status})
        style=None
        for field,folder in [('character_pack','characters'),('element_pack','assets'),('style_pack','styles')]:
            pack=getattr(p,field)
            if not pack:continue
            path=self.root/'registries'/folder/(pack+'.json');add(field,pack,path)
            data=json.loads(path.read_text()) if path.is_file() else {}
            if field=='style_pack':style=data
            records=data.get('actions',data.get('elements',[]))
            for a in records:add(field+'_file',a.get('asset_id') or a.get('id') or a['element_id'],self.root/'assets'/a['path'],a['sha256'])
        template=(style or {}).get('template_pack','XIAO-Y_TEMPLATES_V1');add('template_pack',template,self.root/'registries/styles'/(template+'.json'))
        snapshot=self.store.latest(pid,'PROJECT_FONT_SNAPSHOT')
        for f in snapshot['payload']['fonts'] if snapshot else []:add('font',f['font_id'],f['preview_path'],f['preview_hash'])
        from vnext.media.library.service import MediaLibrary
        for m in MediaLibrary(self.store).assets(pid):add('media',m.asset_id,m.original_path,m.hash)
        if p.voice_profile:add('voice_profile',p.voice_profile,self.root/'registries/voices'/(p.voice_profile+'.json'))
        voice=self.store.latest(pid,'VOICE')
        if voice:
            audio_path=voice['payload'].get('audio_path')
            if not audio_path:
                audio=next((m for m in MediaLibrary(self.store).assets(pid) if m.asset_id==voice['payload'].get('media_asset_id')),None)
                audio_path=audio.original_path if audio else str(self.store.root/'MISSING_VOICE_AUDIO')
            path=Path(audio_path);add('voice_audio',voice['artifact_id'],path)
        add('prompt_version','PROMPT_REGISTRY',self.root/'registries/prompts/PROMPT_REGISTRY.json')
        # Skill snapshots are immutable artifact identities with pinned dependencies.
        snapshots=[a for a in self.store.artifacts(pid) if a['artifact_type'].startswith('EFFECTIVE_SKILL_SNAPSHOT_') and self.store.is_latest_revision(a['artifact_id'])]
        return {'schema_version':1,'items':items,'skill_versions':[{'artifact_id':a['artifact_id'],'output_hash':a['output_hash'],'dependencies_valid':self.store.dependencies_valid(a['artifact_id'])} for a in snapshots],
            'model_config':self.model_config(pid),'model_config_hash':digest(self.model_config(pid)),
            'usable':all(i['status']=='RESOLVED' for i in items) and all(self.store.is_usable_input(a['artifact_id']) for a in snapshots),
            'locale_affects_dependency':False}
    def build(self,pid):
        value=self.collect(pid);config=self.pin_config(pid)
        return self.store.create_artifact(pid,'PROJECT_DEPENDENCY_MANIFEST',value,role='DEPENDENCY_RESOLVER',
            dependencies=[self.store.dependency(config['artifact_id'])],status='READY' if value['usable'] else 'BLOCKED').model_dump()
    def validate(self,pid):
        value=self.collect(pid);old=self.store.latest(pid,'PROJECT_DEPENDENCY_MANIFEST')
        if old and value['model_config_hash']!=old['payload']['model_config_hash']:value['usable']=False;value['issues']=['MODEL_CONFIG_CHANGED']
        return value
    def relink(self,pid,aid,path,actor):
        if actor!='HUMAN':raise PermissionError('RELINK_HUMAN_REQUIRED')
        old=self.store.latest(pid,'PROJECT_DEPENDENCY_MANIFEST')
        if not old:raise ValueError('MANIFEST_REQUIRED')
        item=next((i for i in old['payload']['items'] if i['asset_id']==aid),None)
        candidate=Path(path).expanduser().resolve()
        if not item or not candidate.is_file() or sha(candidate)!=item['expected_hash']:raise ValueError('RELINK_HASH_MISMATCH')
        values=self.relinks(pid);values[aid]=str(candidate);self.path(pid).write_text(json.dumps(values,indent=2))
        if item['kind']=='media':
            from vnext.media.library.service import MediaLibrary
            MediaLibrary(self.store).relink(pid,aid,candidate)
            voice=self.store.latest(pid,'VOICE')
            if voice and voice['payload'].get('media_asset_id')==aid:
                values[voice['artifact_id']]=str(candidate);self.path(pid).write_text(json.dumps(values,indent=2))
        if item['kind'] in ('character_pack_file','element_pack_file'):
            # Pack source resolution reads the explicit relink map, not a same-name search.
            pass
        self.store.event(pid,'DEPENDENCY_RELINKED',asset_id=aid,expected_hash=item['expected_hash'],path=str(candidate))
        return self.build(pid)
