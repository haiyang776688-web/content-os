"""Copy diagnostic evidence, never user databases, secrets or local font files."""
import json, shutil, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from vnext.storage.store import Store
from vnext.phase2.production import Production
from vnext.phase2.stages import StageCache
from vnext.registries.export import export

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def main():
    report=json.loads((ROOT/'examples/PHASE2_DIAGNOSTIC_REPORT.json').read_text())
    store=Store(Path(report['data_root']));pid=report['project_id'];out=ROOT/'examples/phase2';out.mkdir(parents=True,exist_ok=True)
    kinds=['FACT_PACK','SCRIPT','AUDIT','SCRIPT_GATE','H2_GATE','DIRECTOR_IR','STORYBOARD','STORYBOARD_GATE',
        'EDT','MECHANICAL_QA','VIDEO_QA','REVIEW_PACK','REVIEW_GATE','TYPOGRAPHY_PROFILE','PROJECT_FONT_SNAPSHOT','RULE_CATALOG','MEDIA_SELECTION']
    for kind in kinds:
        value=store.latest(pid,kind)
        if not value:raise RuntimeError('Missing evidence: '+kind)
        write(out/(kind+'.json'),value)
    write(out/'DIRECTOR_DESIGN_TABLE.json',Production(store).design_table(pid))
    write(out/'STAGE_STATES.json',StageCache(store).states(pid))
    write(out/'SOURCE_REFERENCES.json',[a for a in store.artifacts(pid) if a['artifact_type'].startswith('SOURCE_')])
    write(out/'FAIL_REPAIR_HISTORY.json',[a for a in store.artifacts(pid) if a['artifact_type'] in ('SCRIPT','AUDIT','SCRIPT_GATE','ERROR_CANDIDATE','CHANGE_REQUEST')])
    for name in ('error_events.jsonl','rule_events.jsonl','CURRENT_RULES.md'):
        shutil.copy2(store.root/'projects'/pid/'audit'/name,out/name)
    shutil.copy2(store.root/'projects'/pid/'research/source_ledger.jsonl',out/'source_ledger.jsonl')
    shutil.copy2(report['video'],out/'DIAGNOSTIC_60S_MOCK.mp4')
    board=store.get_artifact(report['storyboard'])
    for entry in board['payload']['entries']:
        for index,source in enumerate(entry['images']):
            target=out/'storyboard'/f"{entry['beat_id']}-{index}.png";target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    native=report['native']
    write(out/'JIANYING_EXPORT_REPORT.json',native)
    font=json.loads((ROOT/'examples/FONT_ACCEPTANCE_REPORT.json').read_text())
    shutil.copy2(font['preview'],out/'FONT_TEST.png')
    if font.get('video'):shutil.copy2(font['video'],out/'FONT_TEST_MOCK.mp4')
    write(out/'FONT_ACCEPTANCE_REPORT.json',font)
    write(out/'EVIDENCE_MANIFEST.json',{'project_id':pid,'font_project_id':font['project_id'],
        'model_mode':'MOCK','voice':'TEST_TONE_NOT_TTS','gates':'SIMULATED_TEST_FIXTURE',
        'original_artifact_paths_are_machine_specific':True,'font_bytes_redistributed':False,
        'native_draft_path':native['native_draft_path'],'native_full_acceptance':False,
        'phase2_complete':False})
    export(ROOT)
    from vnext.phase2.production import PATTERNS
    from vnext.phase2.knowledge import DEFAULT_RULES,LAYERS
    write(ROOT/'registries/visual_patterns/VISUAL_PATTERN_REGISTRY.json',[p.model_dump() for p in PATTERNS])
    write(ROOT/'registries/skills/WRITING_DEFAULT.json',DEFAULT_RULES.model_dump())
    write(ROOT/'registries/skills/RESOLUTION_ORDER.json',{'layers':LAYERS,'reserved':['CONSTITUTION','SYSTEM'],'hard_rules_override':False})
    write(ROOT/'registries/typography/XIAO-Y_TYPOGRAPHY_PROFILE_V1.json',{'profile_id':'XIAO-Y_TYPOGRAPHY_PROFILE_V1',
        'font_assignment':'USER_LOCAL_SELECTION_REQUIRED','roles':['TITLE','BODY','SUBTITLE','KEYWORD','NUMBER','LABEL','CTA','UI'],
        'subtitle':{'single_line':True,'color':'#ffffff','background':None,'baseline':.91,'shadow':'0 2px 4px #0008'},
        'palette':{'background':'#ffffff','ink':'#111111','highlight':'#ffcc00','emphasis':'#ff3333'},'no_bundled_font_bytes':True})
    print(json.dumps({'evidence':str(out),'project_id':pid},ensure_ascii=False))
if __name__=='__main__':main()
