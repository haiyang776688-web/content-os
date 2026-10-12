from starlette.concurrency import run_in_threadpool
"""Same-origin settings center. Credentials never returned; requests require CSRF token."""
import json,secrets,time,threading,uuid,subprocess,re
from pathlib import Path
from fastapi import Request,HTTPException
from fastapi.responses import JSONResponse,FileResponse
from vnext.providers.settings import Settings,configure,error_code,privacy
from vnext.secrets.secure import redact,install_logging_redaction
from vnext.contracts import Role,VoiceRequest
from vnext.storage.store import digest

class Consents:
    def __init__(self):self.values={};self.lock=threading.Lock()
    def issue(self,pid,action,provider_id,payload):
        token=secrets.token_urlsafe(32)
        with self.lock:self.values[token]=(pid,action,provider_id,digest(payload),time.monotonic()+300)
        return token
    def consume(self,token,pid,action,provider_id,payload):
        with self.lock:value=self.values.pop(token,None)
        if not value or value[:4]!=(pid,action,provider_id,digest(payload)) or value[4]<time.monotonic():raise PermissionError('UPLOAD_CONSENT_INVALID_OR_USED')
        return True

def attach(app,store,root,runtime):
    configure(store.root);install_logging_redaction();settings=Settings();csrf=secrets.token_urlsafe(32);consents=Consents()
    def checked(fn):
        try:return redact(fn())
        except PermissionError as e:raise HTTPException(403,redact(str(e))) from None
        except Exception as e:raise HTTPException(400,redact(str(e))) from None
    @app.middleware('http')
    async def secure_settings(request,call_next):
        if request.url.path.startswith('/api/settings'):
            host=request.url.hostname
            if host not in ('127.0.0.1','localhost','::1'):return JSONResponse({'detail':'LOCALHOST_ONLY'},403)
            expected=str(request.base_url).rstrip('/')
            if request.headers.get('origin') and request.headers['origin']!=expected:return JSONResponse({'detail':'ORIGIN_REJECTED'},403)
            if request.headers.get('sec-fetch-site')=='cross-site':return JSONResponse({'detail':'ORIGIN_REJECTED'},403)
            if request.method not in ('GET','HEAD') and not secrets.compare_digest(request.headers.get('x-contentos-csrf',''),csrf):return JSONResponse({'detail':'CSRF_REJECTED'},403)
        response=await call_next(request)
        if request.url.path.endswith(('.js','.css')) or request.url.path=='/':response.headers['Cache-Control']='no-store'
        if request.url.path.startswith('/api/settings'):response.headers['Cache-Control']='no-store';response.headers['X-Content-Type-Options']='nosniff'
        return response
    @app.get('/production-ux.js')
    def production_js():return FileResponse(root/'vnext/apps/workbench/production-ux.js',media_type='application/javascript')
    @app.get('/settings.js')
    def js():return FileResponse(root/'vnext/apps/workbench/settings.js',media_type='application/javascript')
    @app.get('/api/settings/bootstrap')
    def bootstrap():return {'csrf_token':csrf,'providers':settings.list(),'protocols':[{'id':'OPENAI_COMPATIBLE','available':True},{'id':'ANTHROPIC','available':False},{'id':'GEMINI','available':False},{'id':'CUSTOM_ADAPTER','available':False}]}
    @app.get('/api/settings/providers')
    def providers():return checked(settings.list)
    @app.post('/api/settings/providers')
    async def create_provider(request:Request):
        value=await request.json();return await run_in_threadpool(checked,lambda:settings.save(value))
    @app.put('/api/settings/providers/{pid}')
    async def update_provider(pid:str,request:Request):
        value=await request.json();return await run_in_threadpool(checked,lambda:settings.save(value,pid))
    @app.delete('/api/settings/providers/{pid}')
    def delete_provider(pid:str):return checked(lambda:(settings.delete(pid,store) or {'deleted':True}))
    @app.get('/api/settings/export')
    def export():return {'providers':settings.export(),'credentials_included':False}
    @app.post('/api/settings/import')
    async def imported(request:Request):
        value=await request.json()
        def run():
            count=0
            for item in value.get('providers',[]):
                pid=item['provider_id'];data={k:v for k,v in item.items() if k in ('display_name','protocol','base_url','default_model','enabled','authentication','timeout','declared_capabilities')}
                if pid in settings.configs():settings.save(data,pid)
                else:
                    if not re.fullmatch(r'custom_[a-z0-9_]+',pid):raise ValueError('PROVIDER_ID_INVALID')
                    created=settings.save(data);temporary=created['provider_id'];entry=settings.raw()[temporary];entry['provider_id']=pid
                    settings.delete(temporary,store);settings.put(entry)
                count+=1
            return {'imported':count,'credentials_included':False}
        return await run_in_threadpool(checked,run)
    @app.post('/api/settings/import-key-file')
    async def key_file(request:Request):
        raw=await request.body()
        if len(raw)>128000:raise HTTPException(400,'FILE_TOO_LARGE')
        def run():
            if raw.startswith(b'{\\rtf'):
                rawtext=subprocess.run(['textutil','-convert','txt','-stdin','-stdout'],input=raw,capture_output=True,check=True).stdout.decode('utf-8')
            else:rawtext=raw.decode('utf-8')
            saved=[]
            for name,pid in [('deepseek','DEEPSEEK'),('Minimax','MINIMAX'),('GLM','GLM')]:
                m=re.search(re.escape(name)+r'\s*[:：]\s*(\S+)',rawtext,re.I)
                if m:settings.save({'api_key':m[1]},pid);saved.append(pid)
            bearer=re.search(r'Authorization:\s*Bearer\s+([^\s"\']+)',rawtext,re.I)
            if bearer:
                model=re.search(r'"model"\s*:\s*"([^"]+)"',rawtext);base=re.search(r'curl\s+(https?://[^\s]+)',rawtext)
                settings.save({'api_key':bearer[1],**({'default_model':model[1]} if model else {}),**({'base_url':base[1]} if base else {})},'DOUBAO');saved.append('DOUBAO')
            if not saved:raise ValueError('KEY_FILE_NOT_RECOGNIZED')
            return {'configured':saved,'secret_source':'MACOS_KEYCHAIN','automatic_run':False}
        return await run_in_threadpool(checked,run)
    def provider_for(pid,role):
        from vnext.registries.catalog import ROLE_CONTRACTS
        p=store.get_project(pid);return p.worker_assignments.get(role,ROLE_CONTRACTS[Role(role)].default_worker)
    @app.post('/api/settings/projects/{pid}/consent')
    async def consent(pid:str,request:Request):
        v=await request.json();return await run_in_threadpool(checked,lambda:{'consent_token':consents.issue(pid,v['action'],v['provider_id'],v['payload']),'expires_in':300,'one_time':True})
    def authorize(pid,action,provider_id,payload,token):
        if provider_id.startswith('MOCK'):return False
        p=store.get_project(pid);classification=privacy(settings.get(provider_id)['base_url'])
        external_search=action=='RESEARCH' and payload.get('web_search')
        rates=p.model_pricing.get(payload.get('profile') or provider_id,{})
        unknown=not rates or action=='VIDEO_QA' and 'video_per_input' not in rates or payload.get('capability') in ('VIDEO_INPUT','IMAGE_INPUT') and payload['capability'].split('_')[0].lower()+'_per_input' not in rates
        cost_ask=action!='MODELS' and settings.project_policy(pid)['cost_unknown_policy']=='ASK' and unknown
        if classification=='LOCAL' and not external_search and not cost_ask:return False
        if p.privacy_mode=='LOCAL_ONLY' and (classification!='LOCAL' or external_search):raise PermissionError('LOCAL_ONLY_MODEL_UPLOAD_FORBIDDEN')
        if p.privacy_mode=='ASK_BEFORE_UPLOAD' or cost_ask:return consents.consume(token or '',pid,action,provider_id,payload)
        return True
    @app.post('/api/settings/providers/{provider_id}/probe')
    async def probe(provider_id:str,request:Request):
        v=await request.json()
        def run():
            pid=v['project_id'];payload={'capability':v.get('capability','STRUCTURED_OUTPUT')}
            permission=authorize(pid,'PROBE',provider_id,payload,v.get('consent_token'))
            return settings.probe(provider_id,store,pid,payload['capability'],permission)
        return await run_in_threadpool(checked,run)
    @app.post('/api/settings/providers/{provider_id}/models')
    async def models(provider_id:str,request:Request):
        v=await request.json()
        def run():
            authorize(v['project_id'],'MODELS',provider_id,{},v.get('consent_token'))
            p=settings.get(provider_id)
            try:p['models']=[str(x['id']) for x in settings.request(provider_id,'models').get('data',[])];p['model_discovered']=bool(p['models']);p['models_error']=None
            except Exception as e:p['models_error']=error_code(e);p['model_discovered']=False
            return settings.put(p)
        return await run_in_threadpool(checked,run)
    @app.get('/api/settings/projects/{pid}/roles')
    def roles(pid:str):
        from vnext.registries.catalog import ROLE_CONTRACTS,worker_options
        return checked(lambda:[{'role':r.value,'selected':provider_for(pid,r.value),'required':[c.value for c in ROLE_CONTRACTS[r].required_capabilities],'workers':worker_options(r)} for r in (Role.RESEARCH,Role.SCRIPT_PRIMARY,Role.SCRIPT_EDITOR,Role.AUDIT,Role.DIRECTOR,Role.VIDEO_QA)])
    @app.post('/api/settings/projects/{pid}/roles')
    async def assign(pid:str,request:Request):
        value=await request.json();return await run_in_threadpool(checked,lambda:runtime.select_worker(pid,Role(value['role']),value['provider_id']))
    @app.get('/api/settings/projects/{pid}/policy')
    def project_policy(pid:str):
        store.get_project(pid);return settings.project_policy(pid)
    @app.post('/api/settings/projects/{pid}/config')
    async def config(pid:str,request:Request):
        v=await request.json()
        def run():
            if set(v)-{'privacy_mode','budget','fallback_policy','fallback_workers','model_pricing','voice_profile','cost_unknown_policy'}:raise ValueError('SETTING_FIELD_NOT_ALLOWED')
            cost_policy=v.pop('cost_unknown_policy',None)
            if cost_policy is not None and cost_policy not in ('ALLOW','ASK','BLOCK'):raise ValueError('COST_POLICY_INVALID')
            p=store.get_project(pid).model_dump();p.update(v)
            from vnext.contracts import ProjectConfig
            updated=ProjectConfig.model_validate(p);store.save_project(updated)
            if cost_policy is not None:settings.save_project_policy(pid,cost_policy)
            return updated.model_dump()
        return await run_in_threadpool(checked,run)
    @app.post('/api/settings/projects/{pid}/run/{role}')
    async def run_role(pid:str,role:str,request:Request):
        v=await request.json()
        def run():
            provider_id=provider_for(pid,role);payload={'source_artifact_ids':v.get('source_artifact_ids',[]),'config':v.get('config',{})}
            permit=authorize(pid,'RUN_'+role,provider_id,payload,v.get('consent_token'))
            config={**payload['config'],'upload_confirmed':permit,'cost_confirmed':permit}
            operation=lambda:runtime.run(pid,Role(role),payload['source_artifact_ids'],request_id=v.get('request_id') or uuid.uuid4().hex,config=config)
            if store.get_project(pid).phase2_enabled and role in ('RESEARCH','SCRIPT_PRIMARY','SCRIPT_EDITOR','AUDIT','DIRECTOR'):
                from vnext.phase2.stages import StageCache
                from vnext.phase2.knowledge import Knowledge
                snapshot=Knowledge(store).snapshot(pid,role,config.get('skill_layers'))
                identity=settings.identity(provider_id) if not provider_id.startswith('MOCK') else {'provider_id':provider_id}
                return StageCache(store).run(pid,role,[*payload['source_artifact_ids'],snapshot['artifact_id']],operation,config={**payload['config'],'provider_identity':identity},worker=provider_id,prompt=snapshot['artifact_id'],skills=snapshot['output_hash'])
            return operation()
        return await run_in_threadpool(checked,run)
    @app.get('/api/settings/projects/{pid}/costs')
    def costs(pid:str):
        from vnext.phase2.hardening.model_runs import ModelRuns
        from vnext.gateways.model.gateway import ModelGateway
        return checked(lambda:ModelRuns(store,ModelGateway()).rows(pid))
    from vnext.providers.workflow import attach_workflow
    attach_workflow(app,store,root,settings,checked,authorize,provider_for)
