"""Native voice adapters, independent of LLM protocol settings."""
import json,base64,uuid,subprocess,os
from pathlib import Path
import urllib.request
from vnext.contracts import VoiceArtifact,utc_now
from vnext.providers.settings import Settings,ROOT,NoRedirect
from vnext.secrets.secure import SecureSecrets
from vnext.migration.legacy import sha

def path():
    from vnext.providers import settings
    return Path(settings.ROOT or Path.home()/'.content-os')/'settings/voices.json'
def raw():return json.loads(path().read_text()) if path().exists() else {}
def detected():
    legacy_root=os.getenv('CONTENT_OS_LEGACY_ROOT')
    if not legacy_root:return {'available':False}
    config=Path(legacy_root).expanduser()/'production/voice/VOICE-0001.json'
    if not config.is_file():return {'available':False}
    v=json.loads(config.read_text());required=['python_path','runtime_path','legacy_matcha_path','model_path','reference_audio']
    ready=all(Path(v[k]).exists() for k in required) and sha(Path(v['reference_audio']))==v['reference_audio_sha256']
    return {'available':ready,'display_name':'本地克隆声音 · CosyVoice3','reference_hash_matches':ready,'config':v}
def save(value):
    allowed={'profile','enabled','model','voice_id','base_url','api_key','resource_id','local_authorized'}
    if set(value)-allowed:raise ValueError('VOICE_SETTING_INVALID')
    pid=value['profile'];values=raw();old=values.get(pid,{})
    if value.get('api_key'):SecureSecrets().set(pid,value['api_key'])
    value={k:v for k,v in value.items() if k!='api_key'}
    if pid=='YU_LOCAL_V1':
        d=detected()
        if value.get('enabled') and (not value.get('local_authorized') or not d['available']):raise ValueError('LOCAL_VOICE_AUTHORIZATION_REQUIRED')
        value['local_config']=d.get('config')
    elif pid not in ('MINIMAX_TTS','DOUBAO_TTS'):raise ValueError('VOICE_PROFILE_UNKNOWN')
    values[pid]={**old,**value};path().parent.mkdir(parents=True,exist_ok=True);path().write_text(json.dumps(values,ensure_ascii=False,indent=2));os.chmod(path(),0o600)
    return list_profiles()
def list_profiles():
    settings=Settings();values=raw();rows=[]
    for pid,provider,model,speaker,base in [('MINIMAX_TTS','MINIMAX','speech-2.8-hd','Chinese (Mandarin)_Reliable_Executive',('https://api.minimax.cn/v1/t2a_v2' if 'minimax.cn' in settings.get('MINIMAX')['base_url'] else 'https://api.minimax.io/v1/t2a_v2')),('DOUBAO_TTS','DOUBAO','seed-tts-2.0','zh_female_vv_uranus_bigtts','https://openspeech.bytedance.com/api/v3/tts/unidirectional')]:
        p={'profile':pid,'enabled':False,'model':model,'voice_id':speaker,'base_url':base,'resource_id':'seed-tts-2.0',**values.get(pid,{})};own=SecureSecrets().get(pid)
        rows.append({**p,'provider':provider,'execution_mode':'CLOUD','display_name':pid,'configured':bool((own or settings.key(provider)) and p['enabled']),'secret_configured':bool(own or settings.key(provider)),
          'secret_source':'MACOS_KEYCHAIN' if own or settings.secret.get(provider) else 'ENVIRONMENT' if settings.key(provider) else 'NOT_CONFIGURED','adapter_implemented':True,'live_verified':bool(p.get('last_preview')), 'last_probe_result':p.get('last_preview'),'production_accepted':False})
    local=values.get('YU_LOCAL_V1',{});d=detected()
    rows.append({'profile':'YU_LOCAL_V1','display_name':'本地克隆声音 · CosyVoice3','execution_mode':'LOCAL','provider':'LOCAL','configured':bool(local.get('enabled') and d['available']),'detected':d['available'],'adapter_implemented':True,'live_verified':bool(local.get('last_preview')),'last_probe_result':local.get('last_preview'),'production_accepted':False,'local_authorized':bool(local.get('local_authorized'))})
    return rows

def native_execute(request,output_dir,privacy='LOCAL_ONLY',upload_confirmed=False):
    row=next((x for x in list_profiles() if x['profile']==request.voice_profile),None)
    if not row or not row['configured']:raise RuntimeError('VOICE_PROVIDER_NOT_CONFIGURED')
    output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    out=output_dir/('VOICE-'+uuid.uuid4().hex[:12]+'.mp3');words=None;phrases=None;usage={}
    if row['execution_mode']=='LOCAL':
        cfg=raw()['YU_LOCAL_V1']['local_config'];out=out.with_suffix('.wav')
        driver=Path(__file__).with_name('local_voice_bridge.py')
        env={**os.environ,'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1'}
        v=subprocess.run([cfg['python_path'],str(driver)],input=json.dumps({'config':cfg,'text':request.text,'output_path':str(out)}),capture_output=True,text=True,timeout=600,env=env)
        if v.returncode:raise RuntimeError('LOCAL_VOICE_SYNTHESIS_FAILED:'+__import__('vnext.secrets.secure',fromlist=['redact']).redact(v.stderr[-1400:]))
        model=cfg['model_id']
    else:
        if privacy=='LOCAL_ONLY' or privacy=='ASK_BEFORE_UPLOAD' and not upload_confirmed:raise PermissionError('VOICE_UPLOAD_NOT_AUTHORIZED')
        key=SecureSecrets().get(row['profile']) or Settings().key(row['provider'])
        if row['profile']=='MINIMAX_TTS':
            body={'model':row['model'],'text':request.text,'stream':False,'output_format':'hex','voice_setting':{'voice_id':row['voice_id'],'speed':request.prosody.rate,'vol':1,'pitch':0},'audio_setting':{'sample_rate':request.sample_rate,'format':'mp3','channel':1}}
            headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'}
        else:
            body={'user':{'uid':'content-os-local'},'req_params':{'text':request.text,'speaker':row['voice_id'],'audio_params':{'format':'mp3','sample_rate':request.sample_rate},'additions':json.dumps({'enable_timestamp':True})}}
            headers={'X-Api-Key':key,'X-Api-Resource-Id':row['resource_id'],'X-Api-Request-Id':uuid.uuid4().hex,'Content-Type':'application/json'}
        from vnext.providers.settings import url
        endpoint=url(row['base_url'])
        req=urllib.request.Request(endpoint,data=json.dumps(body).encode(),headers=headers)
        with urllib.request.build_opener(NoRedirect()).open(req,timeout=180) as r:
            data=r.read(30_000_000)
        if row['profile']=='MINIMAX_TTS':
            response=json.loads(data)
            if response.get('base_resp',{}).get('status_code',0)!=0:
                detail=response['base_resp'];message=__import__('vnext.secrets.secure',fromlist=['redact']).redact(str(detail.get('status_msg','')));code=detail.get('status_code')
                error='AUTH_INVALID' if code in (1004,2049) else 'BALANCE_INSUFFICIENT' if code in (1008,) else 'RATE_LIMITED' if code in (1002,) else 'VOICE_NOT_FOUND' if code==2054 else 'TTS_PROVIDER_REJECTED'
                raise RuntimeError(error+': '+str(code)+' '+message)
            out.write_bytes(bytes.fromhex(response['data']['audio']));usage=response.get('usage',{})
        else:
            chunks=[];words=[]
            for line in data.splitlines():
                if not line.strip():continue
                if line.startswith(b'data:'):line=line[5:].strip()
                part=json.loads(line)
                if part.get('code') not in (0,20000000):raise RuntimeError('TTS_PROVIDER_REJECTED')
                if part.get('data'):chunks.append(base64.b64decode(part['data'],validate=True))
                for w in part.get('sentence',{}).get('words',[]):words.append({'text':w['word'],'start':w['startTime'],'end':w['endTime']})
                usage.update(part.get('usage',{}))
            out.write_bytes(b''.join(chunks));words=words or None
        model=row['model']
    from vnext.media.library.service import MediaLibrary
    duration=float(MediaLibrary._probe(out).get('duration') or 0)
    if not duration:raise RuntimeError('TTS_AUDIO_INVALID')
    if request.output_format=='wav' and out.suffix!='.wav':
        wav=out.with_suffix('.wav');subprocess.run(['ffmpeg','-v','error','-y','-i',str(out),'-ar',str(request.sample_rate),'-ac',str(request.channels),str(wav)],check=True,capture_output=True);out=wav
    import wave
    if out.suffix=='.wav':
        with wave.open(str(out),'rb') as f:actual_rate,actual_channels=f.getframerate(),f.getnchannels()
    else:
        info=json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-of','json',str(out)],check=True,capture_output=True,text=True).stdout)
        stream=next(s for s in info['streams'] if s['codec_type']=='audio');actual_rate,actual_channels=int(stream['sample_rate']),int(stream['channels'])
    duration=float(MediaLibrary._probe(out).get('duration') or 0)
    with __import__('vnext.providers.settings',fromlist=['LOCK']).LOCK:
        values=raw();values.setdefault(request.voice_profile,{}).pop('last_failed_probe',None);values[request.voice_profile]['last_preview']={'executed_at':utc_now(),'duration':duration,'audio_hash':sha(out),'adapter':'NATIVE_V1'}
        path().write_text(json.dumps(values,ensure_ascii=False,indent=2));os.chmod(path(),0o600)
    return VoiceArtifact(voice_artifact_id=out.stem,provider=row['provider'],model=model,voice_profile=request.voice_profile,audio_path=str(out),duration=duration,
       sample_rate=actual_rate,channels=actual_channels,status='READY',word_timestamps=words,phrase_timestamps=phrases,
       provenance={'adapter':'COSYVOICE3_LOCAL_V1' if row['execution_mode']=='LOCAL' else row['profile']+'_NATIVE_V1','live_verified':True,'executed_at':utc_now(),'timestamps_original':True,'usage':usage,'reference_audio_hash':raw().get('YU_LOCAL_V1',{}).get('local_config',{}).get('reference_audio_sha256') if row['execution_mode']=='LOCAL' else None})
