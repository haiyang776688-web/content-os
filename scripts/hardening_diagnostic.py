"""Isolated 2.9-second contract fixture. Test tone, no live providers or approvals.
The diagnostic renderer consumes identical props but is NOT formal production.
"""
import copy,json,tempfile,subprocess
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vnext.storage.store import Store,digest,canonical
from vnext.contracts import utc_now,Role,VoiceRequest
from vnext.phase2.knowledge import Knowledge
from vnext.phase2.production import Production,mechanical
from vnext.phase2.fonts import Fonts
from vnext.phase2.hardening.evidence import EvidenceIntegrity,text_hash,content_hash
from vnext.phase2.hardening.audio import AudioClock
from vnext.phase2.hardening.dependencies import Dependencies
from vnext.phase2.hardening.visual import VisualResolver
from vnext.phase2.hardening.voices import governed_voice
from vnext.core.runtime import Runtime
from vnext.core.preflight import check
from vnext.media.library.service import MediaLibrary
from vnext.migration.legacy import sha
from vnext.renderers.remotion.resolver import CompositionResolver
from vnext.renderers.remotion.adapter import RemotionAdapter
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'examples/hardening';OUT.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='content-os-hardening-fixture-') as temp:
 s=Store(Path(temp)/'data');p=s.create_project('Isolated hardening test fixture',character_pack='XIAO-Y_V1',style_pack='XIAO-Y_STYLE_V1',element_pack='XIAO-Y_ELEMENTS_V1',voice_profile='MOCK_VOICE_V1')
 pid=p.project_id;k=Knowledge(s);k.initialize(pid);e=EvidenceIntegrity(s);e.enable(pid)
 source=k.source(pid,{'source_id':'S1','source_type':'USER_DOCUMENT','title':'Synthetic contract fixture','retrieved_at':utc_now(),'excerpt':'Alpha has 3 items'})
 e.evidence(pid,{'evidence_id':'E1','source_id':'S1','locator':{'media_type':'TEXT','character_span':{'start':0,'end':17}},'excerpt':'Alpha has 3 items','excerpt_hash':text_hash('Alpha has 3 items'),'source_content_hash':content_hash(source['payload'])})
 k.fact_pack(pid,{'facts':[{'fact_id':'F1','statement':'Alpha has 3 items','source_ids':['S1'],'evidence_ids':['E1'],'support_status':'SUPPORTED','confidence':1}]})
 text='Alpha has 3 items. Alpha has 3 items.'
 claim=lambda i,start:{'claim_id':f'C{i}','segment_id':'SEG1','text_span':{'start':start,'end':start+17},'claim_text':'Alpha has 3 items','claim_type':'NUMERIC','fact_ids':['F1'],'support_status':'SUPPORTED'}
 script=k.bound_script(pid,{'contract_version':2,'text':text,'segments':[{'segment_id':'SEG1','text':text,'claim':True,'fact_ids':['F1']}],'claim_units':[claim(1,0),claim(2,19)]})
 runtime=Runtime(s);runtime.select_worker(pid,Role.AUDIT,'MOCK');runtime.run(pid,Role.AUDIT,[script['artifact_id']],request_id='fixture-audit');runtime.approve_h2(pid,script['artifact_id'],risk_acknowledged=True)
 fonts=Fonts(s);fonts.scan(['/System/Library/Fonts/Supplemental/Arial.ttf'],'SYSTEM');f=next(f for f in fonts.list() if f['weight']==400)
 fonts.profile(pid,{'profile_id':'FIXTURE','roles':{r:{'font_id':f['font_id'],'weight':400,'size':32 if r=='SUBTITLE' else 60,'shadow':'0 2px 4px #0008'} for r in ['TITLE','BODY','SUBTITLE','KEYWORD','NUMBER','LABEL','CTA','UI']}})
 ir={'script_artifact_id':script['artifact_id'],'scenes':[{'scene_id':'SC1','purpose':'Synthetic fixture','script_range':['SEG1'],'narrative_function':'EXPLAIN','retention_goal':'INFORMATION_CHANGE','estimated_duration':10,'beat_ids':['B1']}],
 'beats':[{'beat_id':'B1','scene_id':'SC1','script_segment_id':'SEG1','purpose':'Explain synthetic count','visual_focus':'Alpha','visual_form':'KEYWORD','pattern_id':'CHARACTER_EXPLAIN_KEYWORD','semantic_pattern':'EXPLAIN','template_id':'CHARACTER_LEFT_TEXT_RIGHT','character_intent':'EXPLAIN','element_ids':['ELM-CHECK'],'keyword':'Alpha / 3 items','timing_intent':10,'slots':{'keyword':'Alpha / 3 items'},'motion_intent':'FADE','reveal_order':['PRIMARY']}]}
 prod=Production(s);prod.ir(pid,ir);initial=prod.generate_edt(pid)
 # Formal audio gate must not deadlock pre-voice Storyboard preparation.
 RemotionAdapter(ROOT,s).prepare(pid,initial['artifact_id'],purpose='STORYBOARD')
 voice=governed_voice(s,pid,VoiceRequest(text=text,language='en-US',voice_profile='MOCK_VOICE_V1'),Path(temp)/'voice')
 media=MediaLibrary(s).register(pid,Path(voice.audio_path),'AUDIO','VOICE','LOCAL_ONLY')
 artifact=s.create_artifact(pid,'VOICE',{**voice.model_dump(),'media_asset_id':media.asset_id},role='VOICE',dependencies=[s.dependency(script['artifact_id'])]).model_dump()
 timing={'audio_artifact_id':artifact['artifact_id'],'script_artifact_id':script['artifact_id'],'audio_hash':media.hash,'duration':voice.duration,'provenance':{'method':'TEST_ALIGNMENT','worker':'CONTRACT_FIXTURE','version':'1'},'entries':[{'audio_id':media.asset_id,'segment_id':'SEG1','start':0,'end':voice.duration,'duration':voice.duration,'phrase_ranges':[{'text':'Alpha has 3 items','start':0,'end':voice.duration/2},{'text':'Alpha has 3 items','start':voice.duration/2,'end':voice.duration}]}]}
 amap=AudioClock(s).create(pid,timing,'ALIGNMENT');edt=prod.generate_edt(pid)
 before=canonical({'project':s.get_project(pid).model_dump(),'artifacts':s.artifacts(pid)})
 preview=CompositionResolver(ROOT,s).resolve(pid,edt['artifact_id']);diagnostic=RemotionAdapter(ROOT,s).prepare(pid,edt['artifact_id'],purpose='STORYBOARD')
 assert preview['props']==diagnostic['props'] and preview['fingerprint']==diagnostic['composition_fingerprint']
 assert before==canonical({'project':s.get_project(pid).model_dump(),'artifacts':s.artifacts(pid)})
 formal=check(s,pid,edt['artifact_id']);assert not formal['ok'] and 'VOICE_PRODUCTION_NOT_ACCEPTED' in formal['issues']
 (OUT/'diagnostic_props.json').write_text(json.dumps(preview['props'],ensure_ascii=False,indent=2))
 for command,out in [('render',OUT/'DIAGNOSTIC_AUDIO_CLOCK_FIXTURE.mp4'),('still',OUT/'DIAGNOSTIC_AUDIO_CLOCK_FIXTURE.png')]:
  args=['npx','remotion',command,'src/index.tsx','ContentOSPreview',str(out),'--props',str(OUT/'diagnostic_props.json'),*RemotionAdapter._browser_args()]
  if command=='render':args+=['--codec','h264','--concurrency','2']
  else:args+=['--frame','30']
  run=subprocess.run(args,cwd=ROOT/'vnext/renderers/remotion/project',capture_output=True,text=True,timeout=180)
  (OUT/('diagnostic_'+command+'.txt')).write_text(run.stdout+run.stderr)
  if run.returncode:raise RuntimeError('DIAGNOSTIC_RENDER_FAILED:'+run.stderr[-500:])
 report={'fixture_only':True,'formal_production_accepted':False,'live_provider_verified':False,'real_voice_verified':False,'test_tone':True,'duration':voice.duration,'frames':preview['props']['duration_frames'],'director_estimate':10,
  'audio_timing_hash':amap['output_hash'],'resolved_composition_hash':s.latest(pid,'RESOLVED_VISUAL_COMPOSITION')['output_hash'],'edt_hash':edt['output_hash'],'preview_render_identical_props':True,'readonly_projection':True,'formal_gate_issues':formal['issues'],'geometry':mechanical(s,pid,edt['artifact_id'])}
 (OUT/'DIAGNOSTIC_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='geometry'},ensure_ascii=False))
 for kind in ['SOURCE_S1','EVIDENCE_E1','FACT_F1','CLAIM_C1','SCRIPT','CLAIM_COVERAGE_REPORT','AUDIT','H2_GATE','DIRECTOR_IR','AUDIO_TIMING_MAP','RESOLVED_VISUAL_COMPOSITION','EDT']:
  a=s.latest(pid,kind);(OUT/(kind+'.json')).write_text(json.dumps(a,ensure_ascii=False,indent=2))
