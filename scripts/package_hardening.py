"""Freeze the same source project, omitting secrets, user data and runtime caches."""
import os,json,hashlib,shutil,subprocess,tempfile,zipfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT.parents[1]/'outputs/content-os-vnext-phase2-hardening'
if DEST.exists():raise RuntimeError('REFUSE_TO_OVERWRITE_FROZEN_RELEASE')
DEST.mkdir()
blocked={'.venv','node_modules','__pycache__','.pytest_cache','.DS_Store','.env','public','font_cache'}
def ignore(path,names):return [name for name in names if name in blocked or name.endswith(('.pyc','.pyo'))]
for p in ROOT.iterdir():
 if p.is_dir() and p.name in {'assets','contracts','docs','examples','migration','registries','scripts','vnext'}:shutil.copytree(p,DEST/p.name,ignore=ignore)
 elif p.is_file() and (p.suffix in {'.md','.json'} or p.name in {'.env.example','.gitignore','requirements.txt','requirements-media-optional.txt'}):shutil.copy2(p,DEST/p.name)
# Isolated fresh-data ASGI smoke test against this release, with no provider invocation.
code="""
import json
from fastapi.testclient import TestClient
from vnext.apps.workbench.server import app
with TestClient(app) as c:
 assert c.get('/').status_code==200
 assert c.get('/api/projects').json()==[]
 assert c.get('/hardening.js').status_code==200
 assert c.get('/program-monitor').status_code==200
 assert c.get('/monitor.bundle.js').status_code==200
 for lang in ['zh-CN','en-US']:assert c.get('/api/i18n/'+lang).status_code==200
 p=c.post('/api/projects',json={'name':'Isolated release smoke'});assert p.status_code==200;pid=p.json()['project_id']
 state=c.get('/api/projects/'+pid+'/hardening');assert state.status_code==200
 assert not state.json()['strict'] and not state.json()['providers']['ANTHROPIC']['adapter_implemented']
 rejected=c.post('/api/projects/'+pid+'/hardening/enable',json={'actor':'SCRIPT_PRIMARY','payload':{}});assert rejected.status_code==403
 enabled=c.post('/api/projects/'+pid+'/hardening/enable',json={'actor':'HUMAN','payload':{}});assert enabled.status_code==200
 assert c.get('/api/projects/'+pid+'/hardening').json()['strict']
 print(json.dumps({'fresh_release_import':True,'web_ui':True,'program_monitor_bundle':True,'i18n_both_languages':True,'create_project':True,'hardening_read':True,'owner_veto':True,'strict_enable':True,'real_model_called':False,'temporary_data_only':True}))
"""
with tempfile.TemporaryDirectory(prefix='content-os-release-smoke-') as tmp:
 env={**os.environ,'CONTENT_OS_DATA':tmp,'PYTHONPATH':str(DEST),'PYTHONDONTWRITEBYTECODE':'1'}
 result=subprocess.run([sys.executable,'-c',code],cwd=DEST,env=env,capture_output=True,text=True)
 if result.returncode:raise RuntimeError(result.stdout+result.stderr)
 smoke=json.loads(result.stdout.strip().splitlines()[-1]);(ROOT/'examples/hardening/RELEASE_COLD_START.json').write_text(json.dumps(smoke,indent=2)+'\n')
 shutil.copy2(ROOT/'examples/hardening/RELEASE_COLD_START.json',DEST/'examples/hardening/RELEASE_COLD_START.json')
files={str(p.relative_to(DEST)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DEST.rglob('*')) if p.is_file()}
manifest={'release':'Phase 2 Architecture Hardening','date':'2026-09-27','same_source_project':True,'phase2_complete':False,'ready':13,'implementing':11,'current_tests_passed':126,'frozen_phase1_tests_passed':12,'real_provider_live_verified':0,'real_voice_live_verified':0,'no_user_data_or_secrets':True,'fresh_data_smoke':smoke,'files':files}
(DEST/'RELEASE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
archive=DEST.with_suffix('.zip')
if archive.exists():raise RuntimeError('REFUSE_TO_OVERWRITE_FROZEN_ZIP')
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(DEST.rglob('*')):
  if p.is_file():z.write(p,Path(DEST.name)/p.relative_to(DEST))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 assert len(z.namelist())==len(files)+1
 assert not any(any(x in name.split('/') for x in blocked) for name in z.namelist())
checksum=hashlib.sha256(archive.read_bytes()).hexdigest();archive.with_suffix('.zip.sha256').write_text(checksum+'  '+archive.name+'\n')
print(json.dumps({'directory':str(DEST),'zip':str(archive),'files':len(files)+1,'size_mib':round(archive.stat().st_size/1024/1024,2),'sha256':checksum,'smoke':smoke}))
