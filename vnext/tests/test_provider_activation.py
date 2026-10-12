"""Activation regressions never contact a provider or macOS Keychain."""
import json,logging,io
import pytest
from vnext.providers import settings as module
from vnext.providers.settings import Settings,url,privacy
from vnext.secrets.secure import SecureSecrets,redact,RedactingFormatter
from vnext.storage.store import Store
from vnext.contracts import Role,ModelRequest,ModelMessage
from vnext.registries.catalog import WORKERS,worker_options
from vnext.gateways.model.gateway import ModelGateway
from vnext.phase2.hardening.model_runs import ModelRuns

class MemoryKeychain:
 def __init__(self):self.data={}
 def get_password(self,s,a):return self.data.get((s,a))
 def set_password(self,s,a,v):self.data[s,a]=v
 def delete_password(self,s,a):self.data.pop((s,a),None)

@pytest.fixture
def env(tmp_path,monkeypatch):
 old=WORKERS.copy();backend=MemoryKeychain();secret=SecureSecrets(backend)
 monkeypatch.setattr(module,'SecureSecrets',lambda:secret);monkeypatch.setattr(module,'ROOT',tmp_path/'data')
 store=Store(tmp_path/'data');settings=Settings();settings.sync();pid=store.create_project('Activation',privacy_mode='CLOUD_ALLOWED').project_id
 yield settings,store,pid,secret,backend
 WORKERS.clear();WORKERS.update(old)

def custom(settings,**kwargs):return settings.save({'display_name':'我的模型','base_url':'https://model.example/v1','default_model':'user-model','api_key':'fixture-key-activation-123456',**kwargs})
def fake_transport(monkeypatch,content='{"ok":true}'):
 calls=[]
 def post(*a):calls.append(a);return {'choices':[{'message':{'content':content}}],'usage':{'prompt_tokens':4,'completion_tokens':3}}
 monkeypatch.setattr(ModelGateway,'_post',staticmethod(post));return calls

def test_custom_provider_can_be_created(env):
 s,*_=env;p=custom(s);assert p['provider_type']=='CUSTOM' and p['provider_id'] in WORKERS and p['default_model']=='user-model'
def test_custom_provider_has_stable_id(env):
 s,*_=env;p=custom(s);renamed=s.save({'display_name':'新名字'},p['provider_id']);assert renamed['provider_id']==p['provider_id'] and renamed['secret_configured']
def test_custom_provider_secret_saved_to_keychain(env):
 s,_,_,_,backend=env;p=custom(s);assert backend.data[('ContentOS/providers','provider.'+p['provider_id']+'.api_key')]=='fixture-key-activation-123456'
def test_custom_provider_secret_never_returned(env):
 s,*_=env;custom(s);assert 'fixture-key-activation' not in json.dumps(s.list()) and 'api_key' not in s.file.read_text()
def test_custom_provider_secret_not_exported(env):
 s,*_=env;custom(s);assert 'fixture-key-activation' not in json.dumps(s.export())
@pytest.mark.parametrize('base',['https://example.com/v1/','https://example.com/v1','https://example.com/v1/chat/completions'])
def test_custom_provider_url_validation(base):assert url(base,'chat/completions')=='https://example.com/v1/chat/completions'
@pytest.mark.parametrize('base',['http://remote.example/v1','https://key:password@example.com','https://example.com?token=abc','file:///etc/passwd'])
def test_custom_provider_url_rejects_unsafe(base):
 with pytest.raises(ValueError):url(base)
def test_custom_provider_local_url_and_no_auth(env):
 s,*_=env;p=custom(s,base_url='http://127.0.0.1:11434/v1',authentication='NONE',api_key='');assert p['configured'] and p['privacy_classification']=='LOCAL' and not p['secret_configured']
def test_custom_provider_model_is_user_editable(env):
 s,*_=env;p=custom(s);assert s.save({'default_model':'completely-new-model'},p['provider_id'])['default_model']=='completely-new-model'
def test_custom_provider_connection_probe(env,monkeypatch):
 s,store,pid,*_=env;p=custom(s);calls=fake_transport(monkeypatch);verified=s.probe(p['provider_id'],store,pid);assert verified['live_verified'] and verified['connection_verified'] and len(calls)==1
 assert verified['capabilities']['STRUCTURED_OUTPUT']['state']=='VERIFIED'
def test_custom_provider_failed_probe_not_live_verified(env,monkeypatch):
 s,store,pid,*_=env;p=custom(s)
 monkeypatch.setattr(ModelGateway,'_post',staticmethod(lambda *a:(_ for _ in ()).throw(RuntimeError('AUTH_INVALID'))))
 verified=s.probe(p['provider_id'],store,pid);assert not verified['live_verified'] and verified['last_probe_result']['error_code']=='AUTH_INVALID'
def test_custom_provider_capability_verified_vs_declared(env,monkeypatch):
 s,store,pid,*_=env;p=custom(s,declared_capabilities=['VIDEO_INPUT']);fake_transport(monkeypatch);verified=s.probe(p['provider_id'],store,pid,'TEXT')
 assert verified['capabilities']['TEXT']['state']=='VERIFIED' and verified['capabilities']['VIDEO_INPUT']['state']=='DECLARED' and verified['capabilities']['STRUCTURED_OUTPUT']['state']=='UNKNOWN'
 option=next(w for w in worker_options(Role.VIDEO_QA) if w['worker_id']==p['provider_id']);assert option['disabled'] and 'VIDEO_INPUT' in option['missing_capabilities']
def test_custom_provider_role_assignment(env,monkeypatch):
 s,store,pid,*_=env;p=custom(s);fake_transport(monkeypatch);s.probe(p['provider_id'],store,pid)
 from vnext.core.runtime import Runtime
 Runtime(store).select_worker(pid,Role.RESEARCH,p['provider_id']);assert store.get_project(pid).worker_assignments['RESEARCH']==p['provider_id']
def test_custom_provider_delete_blocked_when_in_use(env):
 s,store,pid,*_=env;p=custom(s);project=store.get_project(pid);project.worker_assignments['DIRECTOR']=p['provider_id'];store.save_project(project)
 with pytest.raises(ValueError,match='PROVIDER_IN_USE'):s.delete(p['provider_id'],store)
def test_custom_provider_model_change_resets_verification(env,monkeypatch):
 s,store,pid,*_=env;p=custom(s);fake_transport(monkeypatch);s.probe(p['provider_id'],store,pid)
 assert not s.save({'default_model':'new-model'},p['provider_id'])['live_verified']
def test_name_and_key_excluded_from_content_identity(env):
 s,*_=env;p=custom(s);identity=s.identity(p['provider_id']);s.save({'display_name':'renamed','api_key':'fixture-rotated-credential-1234'},p['provider_id']);assert identity==s.identity(p['provider_id'])
def test_api_key_never_logged(env):
 s,*_=env;custom(s);stream=io.StringIO();handler=logging.StreamHandler(stream);handler.setFormatter(RedactingFormatter());logger=logging.getLogger('activation-secret-test');logger.handlers=[handler];logger.propagate=False;logger.setLevel(logging.INFO)
 logger.error('Authorization: Bearer %s','fixture-key-activation-123456');assert 'fixture-key-activation' not in stream.getvalue()
 assert redact({'api_key':'x','h3_is_not_publish_authorization':True})=={'api_key':'[REDACTED]','h3_is_not_publish_authorization':True}
def test_secret_content_rejected_without_mutating_script(env):
 s,store,pid,*_=env;custom(s)
 with pytest.raises(ValueError,match='SECRET_CONTENT'):store.create_artifact(pid,'SCRIPT',{'text':'fixture-key-activation-123456'},role='HUMAN')
def test_provider_without_secret_not_ready(env):
 s,*_=env;p=custom(s,api_key='');assert not p['configured'] and p['status']=='SECRET_MISSING'
def test_upload_consent_is_one_time_and_payload_bound():
 from vnext.providers.api import Consents
 c=Consents();ticket=c.issue('p','RUN','provider',{'a':1});assert c.consume(ticket,'p','RUN','provider',{'a':1})
 with pytest.raises(PermissionError):c.consume(ticket,'p','RUN','provider',{'a':1})
 ticket=c.issue('p','RUN','provider',{'a':1})
 with pytest.raises(PermissionError):c.consume(ticket,'p','RUN','provider',{'a':2})
def test_cross_origin_secret_write_rejected(env):
 from fastapi import FastAPI
 from fastapi.testclient import TestClient
 from vnext.providers.api import attach
 from vnext.core.runtime import Runtime
 s,store,pid,*_=env;app=FastAPI();attach(app,store,__import__('pathlib').Path(__file__).resolve().parents[2],Runtime(store));client=TestClient(app,base_url='http://127.0.0.1')
 token=client.get('/api/settings/bootstrap').json()['csrf_token']
 assert client.post('/api/settings/providers',json={},headers={'Origin':'https://evil.example','X-ContentOS-CSRF':token}).status_code==403
 assert client.post('/api/settings/providers',json={}).status_code==403
 assert client.get('/api/settings/providers',headers={'Origin':'https://evil.example'}).status_code==403
 assert client.get('/api/settings/providers').headers['cache-control']=='no-store'
def test_privacy_local_only_blocks_cloud(env,monkeypatch):
 s,store,pid,*_=env;p=custom(s);fake_transport(monkeypatch);s.probe(p['provider_id'],store,pid);project=store.get_project(pid);project.privacy_mode='LOCAL_ONLY';store.save_project(project)
 r=ModelRequest(role=Role.RESEARCH,worker_profile=p['provider_id'],prompt_version='TEST',system_prompt='test',messages=[ModelMessage(role='user',content='test')])
 with pytest.raises(RuntimeError,match='LOCAL_ONLY'):ModelRuns(store,ModelGateway()).invoke(pid,r)
def test_budget_gate(env,monkeypatch):
 s,store,pid,*_=env;p=custom(s);fake_transport(monkeypatch);s.probe(p['provider_id'],store,pid);project=store.get_project(pid);project.budget['project']=1;store.save_project(project)
 r=ModelRequest(role=Role.RESEARCH,worker_profile=p['provider_id'],prompt_version='TEST',system_prompt='test',messages=[ModelMessage(role='user',content='test')])
 with pytest.raises(RuntimeError,match='BUDGET_'):ModelRuns(store,ModelGateway()).invoke(pid,r)
def test_phase2_run_uses_selected_worker_not_mock():
 from pathlib import Path
 source=(Path(__file__).resolve().parents[1]/'apps/workbench/phase2.js').read_text();assert "worker_id:'MOCK'" not in source and 'app.settings.runRole(role' in source

def test_security_redaction_preserves_privacy_and_publish_semantics():
 assert redact('ASK_BEFORE_UPLOAD')=='ASK_BEFORE_UPLOAD'
 assert redact({'h3_is_not_publish_authorization':True})=={'h3_is_not_publish_authorization':True}
 assert redact('api_key=sk-fixture-activation-12345')!='api_key=sk-fixture-activation-12345'

def test_selected_custom_worker_stage_provenance(env,monkeypatch):
 s,store,pid,*_=env;p=custom(s);fake_transport(monkeypatch);s.probe(p['provider_id'],store,pid)
 from vnext.core.runtime import Runtime
 rt=Runtime(store);rt.select_worker(pid,Role.SCRIPT_PRIMARY,p['provider_id']);fake_transport(monkeypatch,'{"text":"测试主稿"}')
 source=store.create_artifact(pid,'RESEARCH',{'text':'来源'},role='RESEARCH')
 result=rt.run(pid,Role.SCRIPT_PRIMARY,[source.artifact_id],request_id='custom-stage')
 assert result['worker']==p['provider_id'] and result['provenance']['provider_id']==p['provider_id']
 assert result['provenance']['model_id']=='user-model' and result['provenance']['provider_type']=='CUSTOM' and result['provenance']['run_id']

@pytest.mark.parametrize('policy,confirmed,allowed',[('ALLOW',False,True),('BLOCK',True,False),('ASK',False,False),('ASK',True,True)])
def test_unknown_cost_policy_is_enforced(env,policy,confirmed,allowed):
 s,store,pid,*_=env;p=custom(s);s.save_project_policy(pid,policy)
 req=ModelRequest(role=Role.RESEARCH,worker_profile=p['provider_id'],system_prompt='x',prompt_version='COST_POLICY_TEST_V1',messages=[ModelMessage(role='user',content='x')],config={'cost_confirmed':confirmed})
 ledger=ModelRuns(store,ModelGateway());worker=WORKERS[p['provider_id']]
 if allowed:
  row=ledger.reserve(pid,req,worker,0,None);assert row['cost_status']=='UNKNOWN' and row['estimated_cost'] is None
 else:
  with pytest.raises(RuntimeError,match='COST_UNKNOWN'):ledger.reserve(pid,req,worker,0,None)
  assert ledger.rows(pid)[-1]['status']=='BLOCKED'

def test_secret_headers_and_refresh_tokens_redacted_without_breaking_gates():
 assert redact({'X-Api-Key':'fixture','refresh_token':'fixture','h3_is_not_publish_authorization':True})=={'X-Api-Key':'[REDACTED]','refresh_token':'[REDACTED]','h3_is_not_publish_authorization':True}

def test_activation_dag_has_all_four_capabilities_and_no_cycle():
 from pathlib import Path
 from graphlib import TopologicalSorter
 from vnext.phase2.hardening.capabilities import graph
 road=json.loads((Path(__file__).resolve().parents[2]/'UPDATED_CAPABILITY_ROADMAP.json').read_text())
 order=list(TopologicalSorter(graph(road['capabilities'])).static_order());assert len(order)==33
 assert order.index('CAP-025')<order.index('CAP-028')<order.index('CAP-026')

def test_script_derived_fields_do_not_rewrite_claim_semantics():
 from vnext.providers.script_contract import prepare
 original={'contract_version':2,'text':'duplicated differently','segments':[{'segment_id':'s','text':'前言。已支持的声明。'}],'claim_units':[{'claim_id':'c','segment_id':'s','claim_text':'已支持的声明','text_span':{'start':0,'end':1},'fact_ids':['F1'],'support_status':'SUPPORTED'}]}
 value,changes=prepare(original);assert value['text']=='前言。已支持的声明。' and value['claim_units'][0]['text_span']=={'start':3,'end':9}
 assert value['claim_units'][0]['fact_ids']==['F1'] and original['text']=='duplicated differently' and changes
 original['claim_units'][0]['claim_text']='另一句不在原文'
 with pytest.raises(ValueError,match='CLAIM_SPAN_MISMATCH'):prepare(original)

@pytest.mark.parametrize('profile',['MINIMAX_TTS','DOUBAO_TTS'])
def test_native_tts_protocol_and_measured_audio(env,monkeypatch,tmp_path,profile):
 import wave,base64
 from vnext.providers import tts
 from vnext.contracts import VoiceRequest
 s,store,pid,secret,_=env;monkeypatch.setattr(tts,'SecureSecrets',lambda:secret)
 tts.save({'profile':profile,'enabled':True,'api_key':'fixture-native-tts-credential-1234'})
 audio=io.BytesIO()
 with wave.open(audio,'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(b'\0\0'*24000)
 raw=audio.getvalue();calls=[]
 class Response:
  def __enter__(self):return self
  def __exit__(self,*a):pass
  def read(self,*a):
   if profile=='MINIMAX_TTS':return json.dumps({'data':{'audio':raw.hex()},'base_resp':{'status_code':0}}).encode()
   return json.dumps({'code':0,'data':base64.b64encode(raw).decode()}).encode()+b'\n'+json.dumps({'code':20000000}).encode()
 class Opener:
  def open(self,req,**kwargs):calls.append(req);return Response()
 monkeypatch.setattr(tts.urllib.request,'build_opener',lambda *a:Opener())
 result=tts.native_execute(VoiceRequest(text='声音协议测试',language='zh-CN',voice_profile=profile),tmp_path/'audio',privacy='ASK_BEFORE_UPLOAD',upload_confirmed=True)
 assert result.status=='READY' and result.duration==pytest.approx(1) and result.sample_rate==24000 and result.word_timestamps is None
 req=calls[0];body=json.loads(req.data)
 if profile=='MINIMAX_TTS':assert '/t2a_v2' in req.full_url and body['voice_setting']['voice_id'] and req.get_header('Authorization')
 else:assert '/tts/unidirectional' in req.full_url and body['req_params']['speaker'] and req.get_header('X-api-key')
 assert store.latest(pid,'VOICE') is None # A native synthesis/preview never creates production artifacts.

def test_native_cloud_tts_respects_local_only_before_network(env,monkeypatch,tmp_path):
 from vnext.providers import tts
 from vnext.contracts import VoiceRequest
 *_,secret,backend=env;monkeypatch.setattr(tts,'SecureSecrets',lambda:secret)
 tts.save({'profile':'MINIMAX_TTS','enabled':True,'api_key':'fixture-native-tts-credential-1234'})
 monkeypatch.setattr(tts.urllib.request,'build_opener',lambda *a:pytest.fail('must not access network'))
 with pytest.raises(PermissionError,match='VOICE_UPLOAD'):tts.native_execute(VoiceRequest(text='测试',language='zh-CN',voice_profile='MINIMAX_TTS'),tmp_path)

@pytest.mark.parametrize('invalid',[False,True])
def test_owner_rework_creates_new_draft_and_revalidates_facts(env,invalid):
 from vnext.phase2.knowledge import Knowledge
 from vnext.core.runtime import Runtime
 from vnext.contracts import utc_now
 from vnext.providers.api import attach
 from fastapi import FastAPI
 from fastapi.testclient import TestClient
 from pathlib import Path
 s,store,pid,*_=env;k=Knowledge(store);k.initialize(pid)
 k.source(pid,{'source_id':'S1','source_type':'USER_DOCUMENT','title':'source','retrieved_at':utc_now(),'excerpt':'Alpha has 3 items'})
 k.fact_pack(pid,{'facts':[{'fact_id':'F1','statement':'Alpha has 3 items','source_ids':['S1'],'support_status':'SUPPORTED','confidence':1}]})
 body={'text':'Alpha has 3 items','segments':[{'segment_id':'s','text':'Alpha has 3 items','claim':True,'fact_ids':['F1']}]};a=k.bound_script(pid,body)
 text='Alpha has 4 items' if invalid else 'Alpha has 3 items, as explained.'
 proposal=k.humanize(pid,a['artifact_id'],{**body,'text':text,'segments':[{'segment_id':'s','text':text,'claim':True,'fact_ids':['F1']}]});assert proposal['status']=='BLOCKED'
 app=FastAPI();attach(app,store,Path(__file__).resolve().parents[2],Runtime(store));c=TestClient(app,base_url='http://127.0.0.1');token=c.get('/api/settings/bootstrap').json()['csrf_token']
 response=c.post(f'/api/settings/projects/{pid}/script-rework',json={},headers={'X-ContentOS-CSRF':token})
 if invalid:assert response.status_code==400 and 'NUMBER_MISMATCH' in response.json()['detail'] and store.latest(pid,'SCRIPT')['artifact_id']==proposal['artifact_id']
 else:
  assert response.status_code==200 and response.json()['artifact_id']!=proposal['artifact_id'] and response.json()['payload']['semantic_status']=='AUDIT_REQUIRED'
  assert store.get_artifact(proposal['artifact_id'])['payload']==proposal['payload']
  with pytest.raises(Exception,match='AUDIT'):Runtime(store).approve_h2(pid,response.json()['artifact_id'])

def test_video_review_copy_removes_cloned_speech_track(tmp_path):
 import subprocess
 from vnext.phase2.intelligence import visual_review_copy
 source=tmp_path/'original.mp4'
 subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=white:s=64x64:r=10','-f','lavfi','-i','sine=frequency=300:sample_rate=24000','-t','1','-c:v','libx264','-c:a','aac',str(source)],check=True)
 original=source.read_bytes();target,provenance=visual_review_copy(source,tmp_path/'review')
 assert source.read_bytes()==original and provenance['audio_transmitted'] is False and target!=source
 streams=json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-of','json',str(target)],check=True,capture_output=True,text=True).stdout)['streams']
 assert [s['codec_type'] for s in streams]==['video'] and provenance['review_scope']=='VISUAL_ONLY'


def test_native_voice_not_found_has_specific_safe_error():
 from vnext.providers.settings import error_code
 assert error_code(RuntimeError('VOICE_NOT_FOUND: 2054 voice id not exist'))=='VOICE_NOT_FOUND'


def test_public_snapshot_rejects_private_and_mixed_dns(monkeypatch):
 from vnext.providers import research
 monkeypatch.setattr(research.socket,'getaddrinfo',lambda *a,**k:[(2,1,6,'',('8.8.8.8',443)),(2,1,6,'',('127.0.0.1',443))])
 with pytest.raises(ValueError,match='PRIVATE_SOURCE'):research.public_url('https://example.com')

def test_public_snapshot_pins_ip_but_verifies_original_tls_host(monkeypatch):
 from vnext.providers import research
 targets=[];tls=[]
 class Sock:
  def close(self):pass
 class Context:
  def wrap_socket(self,sock,server_hostname):tls.append(server_hostname);return sock
 monkeypatch.setattr(research.socket,'create_connection',lambda address,timeout:targets.append(address) or Sock())
 connection=research.PinnedHTTPS('public.example','8.8.8.8');connection._context=Context();connection.connect()
 assert targets==[('8.8.8.8',443)] and tls==['public.example']

def test_real_director_request_binds_exact_approved_script_and_rejects_invented_id(env,monkeypatch):
 from vnext.phase2.knowledge import Knowledge
 from vnext.core.runtime import Runtime
 from vnext.contracts import utc_now
 import copy
 settings,store,pid,*_=env;k=Knowledge(store);k.initialize(pid)
 k.source(pid,{'source_id':'S1','source_type':'USER_DOCUMENT','title':'source','retrieved_at':utc_now(),'excerpt':'Alpha has 3 items'})
 k.fact_pack(pid,{'facts':[{'fact_id':'F1','statement':'Alpha has 3 items','source_ids':['S1'],'support_status':'SUPPORTED','confidence':1}]})
 script=k.bound_script(pid,{'text':'Alpha has 3 items','segments':[{'segment_id':'SEG1','text':'Alpha has 3 items','claim':True,'fact_ids':['F1']}]})
 runtime=Runtime(store);runtime.select_worker(pid,Role.AUDIT,'MOCK');runtime.run(pid,Role.AUDIT,[script['artifact_id']],request_id='fixture-audit');runtime.approve_h2(pid,script['artifact_id'],risk_acknowledged=True)
 settings.save({'api_key':'fixture-director-credential-1234'},'GLM');runtime.select_worker(pid,Role.DIRECTOR,'GLM')
 value={'script_artifact_id':script['artifact_id'],'scenes':[{'scene_id':'SC1','purpose':'Explain','script_range':['SEG1'],'narrative_function':'EXPLAIN','retention_goal':'VALUE','estimated_duration':10,'beat_ids':['B1']}],'beats':[{'beat_id':'B1','scene_id':'SC1','script_segment_id':'SEG1','purpose':'Explain','visual_focus':'Alpha','visual_form':'NUMBER','pattern_id':'NUMBER_EMPHASIS','keyword':'Alpha','timing_intent':10,'slots':{'number':'3'}}]}
 calls=[]
 def post(url,key,body):
  calls.append(copy.deepcopy(body));reply={**value,'script_artifact_id':'invented-id'} if len(calls)==1 else value
  return {'choices':[{'message':{'content':json.dumps(reply)}}],'usage':{}}
 monkeypatch.setattr(ModelGateway,'_post',staticmethod(post))
 result=runtime.run(pid,Role.DIRECTOR,[script['artifact_id']],request_id='fixture-real-director')
 assert len(calls)==2 and result['payload']['script_artifact_id']==script['artifact_id']
 message=json.loads(calls[0]['messages'][1]['content'].split('\n',1)[1]);assert message[0]['artifact_id']==script['artifact_id']
 assert script['artifact_id'] in calls[0]['messages'][0]['content'] and store.latest(pid,'SCRIPT')['artifact_id']==script['artifact_id']


def test_director_without_media_cannot_request_invented_media_or_elements(env):
 from vnext.providers.director_contract import request_contract
 from vnext.contracts import ProjectConfig
 from jsonschema import Draft202012Validator
 _,store,pid,*_=env;p=store.get_project(pid);p.h2_script_artifact_id='approved-fixture';store.save_project(p)
 schema,instructions=request_contract(store,pid);slots=schema['$defs']['Beat']['properties']['slots']
 assert list(Draft202012Validator(slots).iter_errors({'media_asset_id':'invented-media'}))
 assert list(Draft202012Validator(slots).iter_errors({'steps':'wrong string instead of list'}))
 assert not list(Draft202012Validator(slots).iter_errors({'steps':['Alpha','Beta']}))
 props=schema['$defs']['Beat']['properties'];assert props['element_ids']['maxItems']==0
 assert 'SCREEN_DETAIL' not in props['pattern_id']['enum'] and 'CHARACTER_REACTION_MEDIA' not in props['pattern_id']['enum']
 assert 'available_media_asset_ids' in instructions


def test_director_pattern_required_slots_are_validated_before_owner_submission(env):
 from vnext.providers.director_contract import request_contract
 from jsonschema import Draft202012Validator
 _,store,pid,*_=env;p=store.get_project(pid);p.h2_script_artifact_id='approved-fixture';store.save_project(p)
 schema,_=request_contract(store,pid);beat=schema['$defs']['Beat'];value={'beat_id':'B1','scene_id':'SC1','script_segment_id':'SEG1','purpose':'Explain','visual_focus':'Alpha','visual_form':'KEYWORD','pattern_id':'CHARACTER_EXPLAIN_KEYWORD','keyword':'Alpha','timing_intent':4,'slots':{}}
 validator=Draft202012Validator(beat);assert list(validator.iter_errors(value))
 assert not list(validator.iter_errors({**value,'slots':{'keyword':'Alpha'}}))

def test_comparison_presenter_stays_clear_of_both_text_columns(env):
 from vnext.phase2.hardening.visual import VisualResolver
 from vnext.phase2.hardening.geometry import checks
 from vnext.contracts import EDT,EDTClip
 _,store,pid,*_=env;project=store.get_project(pid);project.character_pack='XIAO-Y_V1';project.style_pack='XIAO-Y_STYLE_V1';store.save_project(project)
 store.create_artifact(pid,'TYPOGRAPHY_PROFILE',{'roles':{'BODY':{'size':52,'line_height':1.15}}},role='TYPOGRAPHY')
 beat={'beat_id':'COMPARE','scene_id':'SC1','script_segment_id':'SEG1','pattern_id':'A_B_COMPARE','character_intent':'SERIOUS','timing_intent':4,'slots':{'a':'镜头过短：来不及读完','b':'镜头太长无变化：画面停住'},'motion_intent':'FADE','reveal_order':['PRIMARY','SECONDARY']}
 resolver=VisualResolver(store);value=resolver.plan(pid,{'scenes':[{'beat_ids':['COMPARE']}],'beats':[beat]})
 resolved={'payload':value,'output_hash':'fixture','artifact_id':'fixture'};clips=[EDTClip.model_validate(c) for c in resolver.clips(pid,resolved)]
 assert len([c for c in clips if c.track=='CHARACTER'])==1 and len([c for c in clips if c.track=='TEXT'])==2
 edt=EDT(edt_id='compare',project_id=pid,revision=1,clips=clips)
 assert not checks(store,pid,edt,True)
