"""Registry driven providers; configurations exclude credentials and display names from content identity."""
import json,os,uuid,threading,ipaddress,socket,time,urllib.request,urllib.error
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
from vnext.secrets.secure import SecureSecrets,redact
ROOT=None
LOCK=threading.RLock()
PRESETS={
 'DEEPSEEK':('DeepSeek','https://api.deepseek.com','deepseek-flash'),
 'DOUBAO':('豆包','https://ark.cn-beijing.volces.com/api/v3','doubao-seed-evolving'),
 'GLM':('GLM','https://open.bigmodel.cn/api/paas/v4','glm-4.7'),
 'MINIMAX':('MiniMax','https://api.minimax.io/v1','MiniMax-M3'),
 'OPENAI':('OpenAI','https://api.openai.com/v1',''),
 'ANTHROPIC':('Anthropic','',''), 'GEMINI':('Gemini','',''),
 'QWEN':('Qwen','https://dashscope.aliyuncs.com/compatible-mode/v1',''),
 'KIMI':('Kimi','https://api.moonshot.cn/v1',''), 'GROK':('Grok','https://api.x.ai/v1',''),
 'LOCAL_OPENAI':('本地模型','http://127.0.0.1:11434/v1',''),
 'CUSTOM_OPENAI':('兼容 API','','')}
ADAPTER='OPENAI_CHAT_V2'
CAPS=['TEXT','STRUCTURED_OUTPUT','VISION','IMAGE_INPUT','VIDEO_INPUT','AUDIO_INPUT','TOOL_CALLING','STREAMING','REASONING','JSON_SCHEMA']
def configure(root):
    global ROOT
    ROOT=Path(root);Settings().sync()

def url(value,suffix=None):
    s=urlsplit(str(value).strip())
    if s.scheme not in ('https','http') or not s.hostname or s.username or s.password or s.query or s.fragment:raise ValueError('URL_INVALID')
    local=s.hostname.lower() in ('localhost','127.0.0.1','::1')
    if s.scheme=='http' and not local:raise ValueError('HTTPS_REQUIRED')
    try:s.port
    except ValueError:raise ValueError('URL_INVALID') from None
    path=s.path.rstrip('/')
    if path.endswith('/chat/completions'):path=path[:-17].rstrip('/')
    if suffix:path+='/'+suffix.lstrip('/')
    return urlunsplit((s.scheme,s.netloc,path,'',''))
def privacy(base):return 'LOCAL' if urlsplit(base).hostname in ('localhost','127.0.0.1','::1') else 'REMOTE' if base else 'UNKNOWN'

def error_code(e):
    msg=str(e).lower();status=getattr(e,'code',None)
    for known in ('AUTH_INVALID','BALANCE_INSUFFICIENT','RATE_LIMITED','VOICE_NOT_FOUND','TTS_PROVIDER_REJECTED'):
        if str(e).startswith(known):return known
    if status in (401,403):return 'AUTH_INVALID'
    if status==402 or 'balance' in msg or 'insufficient' in msg or 'quota' in msg:return 'BALANCE_INSUFFICIENT'
    if status==429:return 'RATE_LIMITED'
    if status==404 or 'model_not_found' in msg:return 'MODEL_NOT_FOUND'
    if isinstance(e,(TimeoutError,socket.timeout)) or 'timed out' in msg:return 'REQUEST_TIMEOUT'
    if isinstance(e,urllib.error.URLError):return 'NETWORK_UNREACHABLE'
    if isinstance(e,(KeyError,IndexError,TypeError,json.JSONDecodeError)):return 'RESPONSE_UNRECOGNIZED'
    if status==400:return 'PROTOCOL_INCOMPATIBLE'
    return str(e) if str(e).isupper() and len(str(e))<100 else 'PROVIDER_REQUEST_FAILED'

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise RuntimeError('REDIRECT_NOT_ALLOWED')

class Settings:
    def __init__(self,root=None,secrets=None):
        self.root=Path(root or ROOT or Path.home()/'.content-os');self.secret=secrets or SecureSecrets()
        self.file=self.root/'settings/providers.json'
    def raw(self):return json.loads(self.file.read_text()) if self.file.exists() else {}
    def default(self,pid):
        n,b,m=PRESETS[pid];prefix=pid
        return dict(provider_id=pid,provider_type='BUILTIN',display_name=n,protocol='ANTHROPIC' if pid=='ANTHROPIC' else 'GEMINI' if pid=='GEMINI' else 'OPENAI_COMPATIBLE',
          base_url=os.environ.get(prefix+'_BASE_URL',b),default_model=os.environ.get(prefix+'_MODEL',m),enabled=True,authentication='API_KEY',timeout=60,declared_capabilities=[],verified_capabilities=[],live_verified=False,models=[],revision=0,last_probe_at=None,last_probe_result=None)
    def configs(self):return {**{p:self.default(p) for p in PRESETS},**self.raw()}
    def get(self,pid):
        p=self.configs().get(pid)
        if not p:raise ValueError('PROVIDER_NOT_FOUND')
        return p
    def key(self,pid):return self.secret.get(pid) or os.environ.get(pid+'_API_KEY')
    def environment(self,name):
        for pid,p in self.configs().items():
            if name in (pid+'_BASE_URL',pid+'_MODEL',pid+'_API_KEY'):
                return self.key(pid) if name.endswith('_API_KEY') else p['base_url'] if name.endswith('_BASE_URL') else p['default_model']
        return None
    def put(self,p):
        with LOCK:
            self.file.parent.mkdir(parents=True,exist_ok=True);data=self.raw();data[p['provider_id']]=p
            temp=self.file.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2));os.chmod(temp,0o600);temp.replace(self.file)
        self.sync();return self.public(p['provider_id'])
    def save(self,value,pid=None):
        allowed={'display_name','protocol','base_url','default_model','enabled','authentication','timeout','declared_capabilities','api_key','reuse_secret_from'}
        if set(value)-allowed:raise ValueError('UNKNOWN_SETTING_FIELD')
        old=self.get(pid) if pid else None
        pid=pid or 'custom_'+uuid.uuid4().hex[:12]
        p={**(old or dict(provider_id=pid,provider_type='CUSTOM',protocol='OPENAI_COMPATIBLE',authentication='API_KEY',enabled=True,timeout=60,declared_capabilities=[],verified_capabilities=[],live_verified=False,models=[],revision=0,last_probe_at=None,last_probe_result=None)),**{k:v for k,v in value.items() if k not in ('api_key','reuse_secret_from')}}
        if p['protocol'] not in ('OPENAI_COMPATIBLE','ANTHROPIC','GEMINI','CUSTOM_ADAPTER'):raise ValueError('PROTOCOL_INVALID')
        p['display_name']=str(p.get('display_name','')).strip();p['default_model']=str(p.get('default_model','')).strip()
        if not p['display_name']:raise ValueError('PROVIDER_NAME_REQUIRED')
        p['base_url']=url(p.get('base_url',''))
        if not p['default_model']:raise ValueError('MODEL_REQUIRED')
        if p['authentication'] not in ('API_KEY','NONE'):raise ValueError('AUTHENTICATION_INVALID')
        if not isinstance(p['timeout'],(int,float)) or not 3<=p['timeout']<=180:raise ValueError('TIMEOUT_INVALID')
        if not set(p['declared_capabilities'])<=set(CAPS):raise ValueError('CAPABILITY_INVALID')
        if value.get('reuse_secret_from'):
            source=self.get(value['reuse_secret_from']);copied=self.key(source['provider_id'])
            if not copied:raise ValueError('SECRET_MISSING')
            self.secret.set(pid,copied)
        if value.get('api_key'):self.secret.set(pid,str(value['api_key']).strip())
        if not old or any(old.get(k)!=p.get(k) for k in ('base_url','default_model','protocol','authentication')) or value.get('api_key') or value.get('reuse_secret_from'):
            p.update(live_verified=False,verified_capabilities=[],connection_verified=False,model_verified=False,last_probe_at=None,last_probe_result=None)
        p['revision']+=1
        return self.put(p)
    def caps(self,p):
        if p['protocol']!='OPENAI_COMPATIBLE':return []
        mapped=['TEXT','STRUCTURED_OUTPUT']
        if p['provider_id']=='MINIMAX' and p['default_model']=='MiniMax-M3':mapped+=['VISION','IMAGE_INPUT','VIDEO_INPUT']
        return mapped
    def public(self,pid):
        p=self.get(pid);key=self.key(pid);kc=self.secret.get(pid)
        ready=p['enabled'] and bool(p['base_url'] and p['default_model']) and bool(key or p['authentication']=='NONE') and bool(self.caps(p))
        status='CUSTOM_ADAPTER_REQUIRED' if not self.caps(p) else 'SECRET_MISSING' if not key and p['authentication']!='NONE' else 'READY_TO_USE' if ready and p['live_verified'] else 'CONFIGURED_NOT_VERIFIED' if ready else 'NOT_CONFIGURED'
        return {**p,'adapter_id':ADAPTER if self.caps(p) else None,'registered':True,'configured':ready,'adapter_implemented':bool(self.caps(p)),
          'secret_configured':bool(key),'secret_source':'MACOS_KEYCHAIN' if kc else 'ENVIRONMENT' if key else 'NOT_CONFIGURED',
          'credentials_available':bool(key or p['authentication']=='NONE'),'privacy_classification':privacy(p['base_url']),
          'connection_verified':p.get('connection_verified',False),'model_verified':p.get('model_verified',False),'capability_verified':bool(p['verified_capabilities']),
          'capabilities':{c:{'state':'VERIFIED' if c in p['verified_capabilities'] else 'DECLARED' if c in p['declared_capabilities'] else 'UNKNOWN','adapter_supported':c in self.caps(p)} for c in CAPS},'status':status}
    def list(self):return [self.public(p) for p in self.configs()]
    def export(self):return [{k:p[k] for k in ('provider_id','provider_type','display_name','protocol','base_url','default_model','enabled','authentication','timeout','declared_capabilities')} for p in self.configs().values()]
    def project_policy(self,pid):
        path=self.root/'settings/project_policies.json'
        return (json.loads(path.read_text()) if path.exists() else {}).get(pid,{'cost_unknown_policy':'ALLOW'})
    def save_project_policy(self,pid,policy):
        if policy not in ('ALLOW','ASK','BLOCK'):raise ValueError('COST_POLICY_INVALID')
        path=self.root/'settings/project_policies.json'
        with LOCK:
            values=json.loads(path.read_text()) if path.exists() else {};values[pid]={'cost_unknown_policy':policy};path.parent.mkdir(parents=True,exist_ok=True)
            temp=path.with_suffix('.tmp');temp.write_text(json.dumps(values,indent=2));temp.replace(path)
        return values[pid]
    def identity(self,pid):
        p=self.get(pid)
        return {k:p[k] for k in ('provider_id','provider_type','protocol','base_url','default_model')}|{'adapter_version':ADAPTER}
    def delete(self,pid,store):
        if pid in PRESETS:raise ValueError('BUILTIN_CANNOT_DELETE')
        used=[{'project':p.project_name,'role':r} for p in store.projects() for r,w in p.worker_assignments.items() if w==pid]
        used += [{'project':p.project_name,'role':'FALLBACK'} for p in store.projects() if pid in p.fallback_workers]
        if used:raise ValueError('PROVIDER_IN_USE:'+json.dumps(used,ensure_ascii=False))
        with LOCK:
            data=self.raw();data.pop(pid,None);self.file.write_text(json.dumps(data,ensure_ascii=False,indent=2))
        self.secret.delete(pid)
        from vnext.registries.catalog import WORKERS
        WORKERS.pop(pid,None)
    def sync(self):
        from vnext.registries.catalog import WORKERS
        from vnext.contracts import WorkerProfile,ProviderProtocol,Capability
        for pid,p in self.configs().items():
            if pid in WORKERS:WORKERS[pid]=WORKERS[pid].model_copy(update={'display_name':p['display_name'],'model':p['default_model']})
            else:WORKERS[pid]=WorkerProfile(worker_id=pid,display_name=p['display_name'],provider=pid,model=p['default_model'],protocol=ProviderProtocol.CUSTOM_OPENAI_COMPATIBLE,
                endpoint_env=pid+'_BASE_URL',model_env=pid+'_MODEL',api_key_env=pid+'_API_KEY',capabilities=[Capability.TEXT,Capability.STRUCTURED_OUTPUT])
    def request(self,pid,path,body=None):
        p=self.get(pid);key=self.key(pid)
        if not p['enabled'] or not self.caps(p):raise ValueError('CUSTOM_ADAPTER_REQUIRED')
        if not key and p['authentication']!='NONE':raise ValueError('SECRET_MISSING')
        headers={'Content-Type':'application/json'}
        if key:headers['Authorization']='Bearer '+key
        req=urllib.request.Request(url(p['base_url'],path),data=json.dumps(body).encode() if body is not None else None,headers=headers)
        try:
            with urllib.request.build_opener(NoRedirect()).open(req,timeout=p['timeout']) as r:return json.load(r)
        except urllib.error.HTTPError as e:
            try:detail=redact(e.read(8192).decode(errors='replace'))
            except Exception:detail=''
            code=error_code(e)
            if 'balance' in detail.lower() or 'insufficient' in detail.lower():code='BALANCE_INSUFFICIENT'
            raise ValueError(code) from None
    def probe(self,pid,store,project_id,capability='STRUCTURED_OUTPUT',upload_confirmed=False):
        from vnext.contracts import ModelRequest,ModelMessage,ContentBlock,Role,utc_now
        from vnext.gateways.model.gateway import ModelGateway
        from vnext.phase2.hardening.model_runs import ModelRuns
        p=self.get(pid);started=time.monotonic();request=ModelRequest(role=Role.SCRIPT_PRIMARY,worker_profile=pid,prompt_version='PROVIDER_PROBE_V1',system_prompt='Connection smoke test. Return only {"ok":true}.',
          messages=[ModelMessage(role='user',content='Return {"ok":true}.')],response_schema={'type':'object','required':['ok'],'properties':{'ok':{'const':True}}},config={'max_output_tokens':256,'stage':'PROVIDER_PROBE','upload_confirmed':upload_confirmed,'cost_confirmed':upload_confirmed})
        if capability=='TEXT':request=request.model_copy(update={'response_schema':None})
        if capability in ('IMAGE_INPUT','VIDEO_INPUT'):
            if capability not in self.caps(p):raise ValueError('ADAPTER_CAPABILITY_UNSUPPORTED')
            root=Path(__file__).resolve().parents[2]
            fp=root/'examples/hardening'/('DIAGNOSTIC_AUDIO_CLOCK_FIXTURE.mp4' if capability=='VIDEO_INPUT' else 'DIAGNOSTIC_AUDIO_CLOCK_FIXTURE.png')
            import base64
            uri='data:'+('video/mp4' if capability=='VIDEO_INPUT' else 'image/png')+';base64,'+base64.b64encode(fp.read_bytes()).decode()
            request=request.model_copy(update={'content_blocks':[ContentBlock(type='VIDEO' if capability=='VIDEO_INPUT' else 'IMAGE',uri=uri)],'config':{**request.config,'cloud_policy':store.get_project(project_id).privacy_mode}})
        try:
            result=ModelRuns(store,ModelGateway()).invoke(project_id,request)
            if not result.text.strip():raise ValueError('RESPONSE_UNRECOGNIZED')
            exercised=['TEXT']+(['STRUCTURED_OUTPUT'] if result.structured_output else [])+([capability,'VISION'] if capability in ('VIDEO_INPUT','IMAGE_INPUT') else [])
            p.update(live_verified=True,connection_verified=True,model_verified=True,verified_capabilities=sorted(set(p['verified_capabilities']+exercised)),last_probe_at=utc_now(),
              last_probe_result={'status':'SUCCESS','latency_ms':round((time.monotonic()-started)*1000),'checks':['NETWORK','AUTHENTICATION' if p['authentication']=='API_KEY' else 'NO_AUTHENTICATION','MODEL_CALLABLE','OPENAI_PROTOCOL','TEXT_RESPONSE'],'tested_capability':capability})
        except Exception as e:
            p.update(live_verified=False,verified_capabilities=[],connection_verified=False,model_verified=False,last_probe_at=utc_now(),last_probe_result={'status':'FAILED','error_code':error_code(e),'latency_ms':round((time.monotonic()-started)*1000)})
        return self.put(p)
