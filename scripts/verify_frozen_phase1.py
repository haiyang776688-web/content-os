"""Run frozen source in a disposable copy, preserving the actual frozen folder."""
import json,hashlib,shutil,tempfile,subprocess,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FROZEN=ROOT.parents[1]/'outputs/content-os-vnext-phase1'
def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and not any(x in p.parts for x in ('.venv','node_modules','__pycache__','.pytest_cache'))}
before=hashes(FROZEN)
with tempfile.TemporaryDirectory(prefix='content-os-frozen-regression-') as temp:
 copy=Path(temp)/'phase1';shutil.copytree(FROZEN,copy,ignore=shutil.ignore_patterns('.venv','node_modules','__pycache__','.pytest_cache'))
 runtime_install=subprocess.run(['npm','ci','--no-audit','--no-fund'],cwd=copy/'vnext/renderers/remotion/project',capture_output=True,text=True)
 if runtime_install.returncode:raise RuntimeError(runtime_install.stderr)
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(copy),'CONTENT_OS_DATA':str(Path(temp)/'data')}
 result=subprocess.run([sys.executable,'-m','pytest','-p','no:cacheprovider','vnext/tests/test_phase1.py','-q'],cwd=copy,env=env,capture_output=True,text=True)
 output=ROOT/'examples/hardening';output.mkdir(exist_ok=True);(output/'frozen_phase1_regression.txt').write_text(result.stdout+result.stderr)
 after=hashes(FROZEN);report={'source':str(FROZEN),'isolated_copy':True,'returncode':result.returncode,'frozen_files_unchanged':before==after,'protected_files':len(before)}
 (output/'frozen_phase1_regression.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));sys.exit(result.returncode)
