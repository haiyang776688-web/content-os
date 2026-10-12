"""Voice registry truth separate from model workers; explicit local/cloud modes."""
import json,os,subprocess,base64,uuid
from pathlib import Path
from vnext.contracts import VoiceProfile,VoiceArtifact,utc_now
from vnext.secrets.store import SecretStore
ROOT=Path(__file__).resolve().parents[3]

def voices(store=None):
    secrets=SecretStore();result=[]
    for path in sorted((ROOT/'registries/voices').glob('*.json')):
        v=VoiceProfile.model_validate_json(path.read_text());mock=v.execution_mode=='MOCK'
        local=v.execution_mode=='LOCAL';configured=mock or bool(secrets.get('CONTENT_OS_LOCAL_TTS_COMMAND' if local else 'CONTENT_OS_CLOUD_TTS_URL'))
        result.append({**v.model_dump(),'voice_id':v.voice_profile_id,'language':v.language,'style':'PROFILE_DEFINED',
            'capabilities':['SYNTHESIZE','PHRASE_TIMESTAMPS_OPTIONAL'],'privacy':'LOCAL_CLONED_VOICE' if local else 'CLOUD_TTS' if not mock else 'MOCK',
            'registered':True,'configured':configured,'adapter_implemented':True,'credentials_available':local or mock or secrets.configured('CONTENT_OS_CLOUD_TTS_KEY'),
            'model_discovered':False,'capability_verified':False,'live_verified':False,'last_probe_at':None,'last_probe_result':None,
            'production_accepted':False,'mock_only':mock})
    from vnext.providers.settings import ROOT as SETTINGS_ROOT
    if SETTINGS_ROOT is not None:
        from vnext.providers.tts import list_profiles
        for native in list_profiles():
            if not native["configured"]:continue
            item={**native,'voice_id':native['profile'],'voice_profile_id':native['profile'],'capabilities':['SYNTHESIZE'],'mock_only':False,'provider_voice_id':native.get('voice_id','ZERO_SHOT_REF_C0042044'),'consent_status':'VERIFIED' if native.get('local_authorized') else 'NOT_REQUIRED','status':'ACTIVE' if native['configured'] else 'UNAVAILABLE','language':'zh-CN'}
            result=[r for r in result if r['voice_id']!=item['voice_id']]+[item]
    if store:
        from vnext.migration.legacy import sha
        for project in store.projects():
            voice=store.latest(project.project_id,'VOICE')
            if voice and voice['payload'].get('status')=='READY' and voice['payload'].get('provenance',{}).get('live_verified') and store.is_usable_input(voice['artifact_id']):
                path=Path(voice['payload']['audio_path'])
                from vnext.media.library.service import MediaLibrary
                asset=next((a for a in MediaLibrary(store).assets(project.project_id) if a.asset_id==voice['payload'].get('media_asset_id')),None)
                if path.is_file() and asset and sha(path)==asset.hash:
                    row=next((v for v in result if v['voice_id']==voice['payload']['voice_profile']),None)
                    if row:row.update(live_verified=True,capability_verified=True,last_probe_at=voice['payload']['provenance'].get('executed_at'),last_probe_result={'result':'SYNTHESIS_SUCCEEDED','artifact_id':voice['artifact_id']})
    return result

def execute(request,output_dir,privacy='LOCAL_ONLY',upload_confirmed=False):
    profile=next((v for v in voices() if v['voice_id']==request.voice_profile),None)
    if not profile or not profile['configured']:raise RuntimeError('VOICE_PROVIDER_NOT_CONFIGURED')
    if profile['status']!='ACTIVE' or profile['consent_status']=='PENDING':raise RuntimeError('VOICE_CONSENT_OR_ACTIVE_PROFILE_REQUIRED')
    secrets=SecretStore();output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    if profile['execution_mode']=='LOCAL':
        # Only argv JSON and stdin; no shell and no cloud adapter/fallback.
        command=json.loads(secrets.get('CONTENT_OS_LOCAL_TTS_COMMAND'));target=output_dir/('VOI-'+uuid.uuid4().hex[:12]+'.wav')
        payload={**request.model_dump(),'provider_voice_id':profile['provider_voice_id'],'output_path':str(target),'network_allowed':False}
        run=subprocess.run(command,input=json.dumps(payload),capture_output=True,text=True,timeout=180,check=True)
        response=json.loads(run.stdout);path=Path(response['audio_path']).resolve()
        if output_dir.resolve() not in path.parents or not path.is_file():raise RuntimeError('LOCAL_TTS_OUTPUT_OUTSIDE_PROJECT')
    else:
        if profile['voice_type'] in ('LOCAL_CLONED','REFERENCE_BASED'):raise RuntimeError('LOCAL_CLONE_CLOUD_UPLOAD_FORBIDDEN')
        if privacy=='LOCAL_ONLY' or (privacy=='ASK_BEFORE_UPLOAD' and not upload_confirmed):raise RuntimeError('VOICE_UPLOAD_NOT_AUTHORIZED')
        import urllib.request
        endpoint=secrets.get('CONTENT_OS_CLOUD_TTS_URL');key=secrets.get('CONTENT_OS_CLOUD_TTS_KEY')
        if not key:raise RuntimeError('VOICE_CREDENTIALS_REQUIRED')
        req=urllib.request.Request(endpoint,data=json.dumps({**request.model_dump(),'provider_voice_id':profile['provider_voice_id']}).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
        with urllib.request.urlopen(req,timeout=60) as r:response=json.load(r)
        path=output_dir/('VOI-'+uuid.uuid4().hex[:12]+'.'+request.output_format);path.write_bytes(base64.b64decode(response['audio_base64'],validate=True))
    from vnext.media.library.service import MediaLibrary
    info=MediaLibrary._probe(path);duration=float(info.get('duration') or 0)
    if not duration:raise RuntimeError('TTS_AUDIO_INVALID')
    return VoiceArtifact(voice_artifact_id=path.stem,provider=profile['provider'],model=response.get('model','CUSTOM_TTS_CONTRACT_V1'),voice_profile=request.voice_profile,
        audio_path=str(path),duration=duration,sample_rate=request.sample_rate,channels=request.channels,status='READY',phrase_timestamps=response.get('phrase_timestamps'),word_timestamps=response.get('word_timestamps'),
        provenance={'adapter':'LOCAL_COMMAND_V1' if profile['execution_mode']=='LOCAL' else 'CUSTOM_CLOUD_TTS_V1','executed_at':utc_now(),'live_verified':True,'timestamps_original':True,'usage':response.get('usage',{})})

def governed_voice(store,pid,request,output_dir,upload_confirmed=False):
    """TTS shares the monetary gate; local/mock has zero remote provider charge."""
    from vnext.phase2.hardening.model_runs import ModelRuns
    from vnext.gateways.model.gateway import ModelGateway
    from vnext.gateways.voice.gateway import VoiceGateway
    from vnext.contracts import ModelRequest,ModelMessage,Role,WorkerProfile,ProviderProtocol
    profile=next((v for v in voices(store) if v['voice_id']==request.voice_profile),None)
    if not profile:raise RuntimeError('VOICE_PROFILE_NOT_REGISTERED')
    p=store.get_project(pid);local=profile['execution_mode'] in ('LOCAL','MOCK')
    if not local and (p.privacy_mode=='LOCAL_ONLY' or p.privacy_mode=='ASK_BEFORE_UPLOAD' and not upload_confirmed):raise RuntimeError('VOICE_UPLOAD_NOT_AUTHORIZED')
    worker=WorkerProfile(worker_id=request.voice_profile,display_name=profile['display_name'],provider=profile['provider'],model='VOICE_ADAPTER_V1',protocol=ProviderProtocol.MOCK if local else ProviderProtocol.CUSTOM_REST,capabilities=[])
    r=ModelRequest(role=Role.VOICE,worker_profile=request.voice_profile,system_prompt='',messages=[ModelMessage(role='user',content=request.text)],prompt_version='VOICE_REQUEST_V1',config={'max_output_tokens':0,'stage':'VOICE','cost_confirmed':upload_confirmed})
    ledger=ModelRuns(store,ModelGateway());row=ledger.reserve(pid,r,worker,0,None,zero=local)
    row['metadata']['voice_mode']=profile['execution_mode'];row['metadata']['remote_provider_charge_only']=True
    import time
    started=time.monotonic()
    try:
        result=VoiceGateway().synthesize(request,output_dir,privacy=p.privacy_mode,upload_confirmed=upload_confirmed)
        row.update(model=result.model,model_id=result.model)
        ledger.finish(row,started,{'usage':result.provenance.get('usage',{})})
        return result.model_copy(update={'provenance':{**result.provenance,'provider_id':request.voice_profile,'provider_type':'LOCAL' if local else 'BUILTIN','model_id':result.model,'run_id':row['run_id'],'prompt_version':'VOICE_REQUEST_V1','skill_snapshot':None,'timestamp':utc_now()}})
    except Exception as e:ledger.finish(row,started,error=e);raise
