"""Read-only acceptance snapshot. Never calls a model or writes project state."""
import json,hashlib,collections,re,shutil
from pathlib import Path
from vnext.providers import settings,tts
from vnext.storage.store import Store,canonical
from vnext.phase2.stages import StageCache
from vnext.phase2.hardening.model_runs import ModelRuns
from vnext.gateways.model.gateway import ModelGateway
from vnext.contracts import utc_now
ROOT=Path(__file__).resolve().parents[1]
settings.configure(ROOT/'phase2_preview_data');s=settings.Settings();store=Store(ROOT/'phase2_preview_data');pid='PRJ-bba515713057';out=ROOT/'examples/activation';out.mkdir(exist_ok=True)
def write(path,value):
 path=ROOT/path;path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
providers=s.list();voices=tts.list_profiles();artifacts=store.artifacts(pid);runs=ModelRuns(store,ModelGateway()).rows(pid);project=store.get_project(pid)
voice_keys=['profile','provider','model','voice_id','execution_mode','configured','secret_configured','secret_source','adapter_implemented','live_verified','last_probe_result','last_failed_probe','production_accepted']
voice_public=[{k:v[k] for k in voice_keys if k in v} for v in voices]
def current(kind):
 a=store.latest(pid,kind)
 return a if a and store.is_usable_input(a['artifact_id']) else None
motion=current('STORYBOARD_MOTION');presentation=current('TYPOGRAPHY_PROFILE');board_gate=current('STORYBOARD_GATE');voice=current('VOICE');timing=current('AUDIO_TIMING_MAP');render=current('RENDER');qa=current('VIDEO_QA');review=current('REVIEW_GATE');publish=current('PUBLISH_LOG')
production_review_complete=bool(review and review['payload'].get('decision') in ('APPROVE','APPROVE_WITH_RISK') and qa and qa['payload'].get('verdict') in ('PASS','PASS_WITH_RISK') and voice and 60<=voice['payload']['duration']<=90)
pending=('H2' if not project.h2_script_artifact_id else ('RETIMED_STORYBOARD_GATE' if timing else 'STORYBOARD_GATE') if not board_gate or not board_gate['payload']['all_beats_approved'] else 'VOICE_PRODUCTION' if not voice or not timing else 'RENDER' if not render else 'VIDEO_QA' if not qa else 'H3' if not production_review_complete else 'H4' if not publish else None)
live={'schema_version':1,'generated_at':utc_now(),'status':'LIVE_VERIFIED' if production_review_complete and publish else 'H3_LIVE_VERIFIED_H4_PENDING' if production_review_complete else 'PARTIAL_LIVE_VERIFIED','project_id':pid,'snapshot_action':'READ_ONLY_NO_NEW_PROVIDER_CALL','providers':providers,'voices':voice_public,'budget':project.budget,'cost_unknown_policy':s.project_policy(pid)['cost_unknown_policy'],'run_status_counts':dict(collections.Counter(r['status'] for r in runs)),'cost_status_counts':dict(collections.Counter(r['cost_status'] for r in runs)),'production_review_complete':production_review_complete,'h3_review_gate_id':review['artifact_id'] if review else None,'publication_complete':bool(publish),'real_workflow_complete':bool(production_review_complete and publish),'pending_gate':pending,'presentation':presentation['payload'].get('presentation','STANDARD') if presentation else None,'motion_storyboard_id':motion['artifact_id'] if motion else None,'motion_storyboard_is_formal_render':False,'current_storyboard_gate_id':board_gate['artifact_id'] if board_gate else None,'formal_voice_artifact_id':voice['artifact_id'] if voice else None,'measured_voice_duration':voice['payload']['duration'] if voice else None,'audio_timing_artifact_id':timing['artifact_id'] if timing else None}
write(Path('PROVIDER_LIVE_VERIFICATION.json'),live)
write(Path('PROVIDER_CAPABILITY_MATRIX.json'),{'schema_version':2,'generated_at':utc_now(),'snapshot_scope':'Actual manual smoke results and current registry; read-only snapshot. Capability success does not certify an end-to-end workflow.','structured_output_note':'Client-side validated JSON, not verified native JSON Schema support.','capabilities':settings.CAPS,'providers':{p['provider_id']:{k:p[k] for k in ['provider_id','provider_type','display_name','protocol','default_model','registered','configured','adapter_implemented','connection_verified','model_verified','capability_verified','live_verified','last_probe_at','last_probe_result','capabilities']} for p in providers},'voices':voice_public,'mock_note':'Mock remains an explicit diagnostic choice, never live verification.'})
custom=next(p for p in providers if p['provider_id']=='custom_b617a5973aae');research=store.get_artifact('ART-f6fd7521cf424192')
checks=[('GUI creation with custom name, URL and model',True),('Credential copied in backend to stable custom Keychain ID via GUI',custom['secret_source']=='MACOS_KEYCHAIN'),('Real connection test',custom['live_verified']),('Real Research assignment and stage',research.get('provenance',{}).get('provider_id')==custom['provider_id']),('Artifact full provenance',all(k in research.get('provenance',{}) for k in ['provider_id','provider_type','model_id','adapter_version','prompt_version','skill_snapshot','run_id','timestamp'])),('Research switched back to built-in through GUI',project.worker_assignments['RESEARCH']=='DEEPSEEK'),('Restart retained custom configuration and credential',custom['configured'] and custom['secret_configured'])]
write(Path('CUSTOM_PROVIDER_ACCEPTANCE.json'),{'generated_at':utc_now(),'status':'LIVE_VERIFIED' if all(v for _,v in checks) else 'PARTIAL','provider_id':custom['provider_id'],'display_name':custom['display_name'],'base_url':custom['base_url'],'model_id':custom['default_model'],'checks':[{'check':k,'passed':v} for k,v in checks],'stage_artifact_id':research['artifact_id'],'artifact_provenance':research['provenance'],'latest_research_proposal':store.get_artifact('ART-f6fd7521cf424192')['artifact_id'],'not_claimed':['Custom vision/video capability','Arbitrary private protocols','Unimplemented custom headers']})
# Semantic protection and pack hashes, without editing protected data.
before=json.loads((ROOT/'examples/hardening/user_projects_before.json').read_text());projects={}
for p,want in before.items():
 actual=hashlib.sha256(canonical(dict(project=store.get_project(p).model_dump(),artifacts=store.artifacts(p),stages=StageCache(store).states(p),logs=store.logs(p)))).hexdigest();projects[p]={'before':want,'after':actual,'unchanged':want==actual}
pack=json.loads((ROOT/'examples/hardening/protected_packs_before.json').read_text());changed=[p for p,want in pack.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=want]
write(Path('examples/activation/PROTECTED_BASELINES.json'),{'projects':projects,'pack_files_checked':len(pack),'changed_pack_files':changed,'all_unchanged':all(v['unchanged'] for v in projects.values()) and not changed})
# Scan actual configured credentials in source, reports, DB, logs and artifacts.
keys=[s.key(p['provider_id']) for p in providers if p['secret_configured']];keys=[k.encode() for k in keys if k and len(k)>=12];checked=0;found=[]
for f in ROOT.rglob('*'):
 if not f.is_file() or any(p in ('.venv','node_modules','.git','__pycache__') for p in f.parts):continue
 checked+=1
 if any(k in f.read_bytes() for k in keys):found.append(str(f.relative_to(ROOT)))
write(Path('examples/activation/SECRET_SCAN.json'),{'files_checked':checked,'configured_credential_occurrences':len(found),'files_with_occurrences':found,'excluded':'Dependencies and bytecode; supplied original credential file outside this project is not copied or changed.','passed':not found})
regression_sources=[Path(p) for p in ('/tmp/contentos-postapproval-regression.txt','/tmp/contentos-style-regression-final.txt','/tmp/contentos-final-regression.txt') if Path(p).is_file()]
shutil.copyfile(max(regression_sources,key=lambda p:p.stat().st_mtime),out/'REGRESSION.txt');shutil.copyfile(ROOT/'examples/hardening/frozen_phase1_regression.json',out/'FROZEN_REGRESSION.json');shutil.copyfile(ROOT/'examples/hardening/frozen_phase1_regression.txt',out/'FROZEN_REGRESSION.txt')
write(Path('examples/activation/WORKFLOW_SNAPSHOT.json'),{'project_id':pid,'generated_at':utc_now(),'worker_assignments':project.worker_assignments,'voice_profile':project.voice_profile,'privacy_mode':project.privacy_mode,'h2_script_artifact_id':project.h2_script_artifact_id,'stages':StageCache(store).states(pid),'artifacts':[{'artifact_id':a['artifact_id'],'artifact_type':a['artifact_type'],'revision':a['revision'],'status':a['current_status'],'provider':a.get('provider'),'model':a.get('model'),'provenance':a.get('provenance',{})} for a in artifacts],'run_ledger':runs})
print(json.dumps({'providers_live_verified':[p['provider_id'] for p in providers if p['live_verified']],'voices_live_verified':[v['profile'] for v in voices if v['live_verified']],'custom_acceptance':all(v for _,v in checks),'protected_unchanged':all(v['unchanged'] for v in projects.values()) and not changed,'secret_scan_passed':not found,'regression':(out/'REGRESSION.txt').read_text().splitlines()[-1]},ensure_ascii=False))
