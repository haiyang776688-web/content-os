"""Local font acceptance fixture; no cloud calls, no redistributed system font bytes."""
import argparse, json, sys, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from vnext.contracts import Role,utc_now
from vnext.core.runtime import Runtime
from vnext.phase2.knowledge import Knowledge
from vnext.phase2.fonts import Fonts
from vnext.phase2.production import CommandBus,Production,mechanical
from vnext.renderers.remotion.adapter import RemotionAdapter
from vnext.storage.store import Store


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--data',default='phase2_preview_data');args=parser.parse_args()
    store=Store(Path(args.data).resolve());pid=store.create_project('Font Test · CJK / Regular / Medium / Bold / Italic / TTC / Variable').project_id
    k=Knowledge(store);k.initialize(pid)
    text='复杂规则讲简单 XIAO-Y 2026 ABC xyz 0123456789'
    k.source(pid,{'source_id':'FONT_TEST','source_type':'MANUAL','title':'Typography test string', 'retrieved_at':utc_now(),'excerpt':text})
    k.fact_pack(pid,{'facts':[]})
    script=CommandBus(store).execute(pid,'SCRIPT','REPLACE_SCRIPT',{'payload':{'text':text,'segments':[{'segment_id':'SEG1','text':text}]}})
    runtime=Runtime(store);runtime.select_worker(pid,Role.AUDIT,'MOCK');runtime.run(pid,Role.AUDIT,[script['artifact_id']],request_id='font-audit');runtime.approve_h2(pid,script['artifact_id'],True)
    fonts=Fonts(store)
    paths=['/System/Library/Fonts/STHeiti Light.ttc','/System/Library/Fonts/SFNS.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf','/System/Library/Fonts/Supplemental/Arial Bold.ttf','/System/Library/Fonts/Supplemental/Arial Italic.ttf']
    if not all(Path(p).is_file() for p in paths):raise RuntimeError('Update fixture paths to locally installed CJK, variable, regular, bold, italic fonts')
    scan=fonts.scan(paths);records=fonts.list()
    get=lambda p:next(f for f in records if f['file_path']==p)
    cjk=next(f for f in records if f['family']=='Heiti SC');variable=get(paths[1]);regular=get(paths[2]);bold=get(paths[3]);italic=get(paths[4])
    roles={r:{'font_id':cjk['font_id'],'weight':300,'size':52 if r!='SUBTITLE' else 42} for r in ('TITLE','BODY','SUBTITLE','KEYWORD','NUMBER','LABEL','CTA','UI')}
    for r,f,w in [('TITLE',regular,400),('LABEL',regular,400),('KEYWORD',bold,700),('CTA',italic,400),('UI',variable,500),('NUMBER',regular,400)]:roles[r]={'font_id':f['font_id'],'weight':w,'size':48}
    CommandBus(store).execute(pid,'TYPOGRAPHY_PROFILE','SET_TYPOGRAPHY_PROFILE',{'profile':{'profile_id':'LOCAL_FONT_TEST','roles':roles}})
    Production(store).ir(pid,{'script_artifact_id':script['artifact_id'],'scenes':[{'scene_id':'SC1','purpose':'Typography acceptance','script_range':['SEG1'],'narrative_function':'TEST','retention_goal':'NONE','estimated_duration':10,'beat_ids':['B1']}], 'beats':[{'beat_id':'B1','scene_id':'SC1','script_segment_id':'SEG1','purpose':'Font sample','visual_focus':'Font face fidelity','visual_form':'NUMBER','pattern_id':'NUMBER_EMPHASIS','keyword':'XIAO-Y','timing_intent':10,'slots':{'number':'2026'}}]})
    edt=Production(store).generate_edt(pid);bus=CommandBus(store)
    for c in edt['payload']['clips']:bus.execute(pid,'EDT','DELETE',{'clip_id':c['clip_id']})
    lines=[('TITLE','LOCAL FONT TEST 2026',.1),('BODY','复杂规则讲简单 · 中文字形',.25),('LABEL','Regular 400 ABC xyz 0123456789',.40),('UI','Medium 500 Variable ABC xyz',.53),('KEYWORD','Bold 700 ABC xyz 0123456789',.66),('CTA','Italic ABC xyz 0123456789',.79),('SUBTITLE','单行白字软阴影固定基线',.91)]
    for role,value,y in lines:
        edt=bus.execute(pid,'EDT','ADD',{'track':'SUBTITLE' if role=='SUBTITLE' else 'TEXT','timeline_out':10,'source_out':10,'position':{'x':.5,'y':y},'motion':{'kind':'HOLD'},'metadata':{'text':value,'typography_role':role}})
    qa=mechanical(store,pid,edt['artifact_id'])
    if qa['verdict']=='FAIL':raise RuntimeError(json.dumps(qa,ensure_ascii=False))
    still=RemotionAdapter(ROOT,store).still(pid,edt['artifact_id'])
    prepared=json.loads(Path(still['payload']['props_path']).read_text())
    board=Production(store).storyboard(pid,ROOT)
    Production(store).storyboard_gate(pid,board['artifact_id'],'APPROVE','SIMULATED FONT TESTER','Font acceptance fixture, not user approval')
    from vnext.media.library.service import MediaLibrary
    from vnext.exporters.jianying.adapter import JianyingExporter
    from vnext.phase2.intelligence import VisualQA
    from vnext.phase2.production import Review
    tone=store.root/'projects'/pid/'voice/font-test-tone.wav';tone.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-f','lavfi','-i','sine=frequency=440:duration=10','-af','volume=0.2',str(tone)],check=True)
    media=MediaLibrary(store).register(pid,tone,'AUDIO','VOICE','LOCAL_ONLY',source='FONT_TEST_TONE')
    store.create_artifact(pid,'VOICE',{'media_asset_id':media.asset_id,'duration':10,'status':'MOCK','warning':'Test tone, not spoken TTS'},role='VOICE',dependencies=[store.dependency(script['artifact_id'])])
    edt=bus.execute(pid,'EDT','ADD',{'track':'VOICE','asset_id':media.asset_id,'source_out':10,'timeline_out':10})
    qa=mechanical(store,pid,edt['artifact_id'],True)
    if qa['verdict']=='FAIL':raise RuntimeError(json.dumps(qa,ensure_ascii=False))
    store.create_artifact(pid,'MECHANICAL_QA',qa,role='MECHANICAL_QA',dependencies=[store.dependency(edt['artifact_id'])])
    video=RemotionAdapter(ROOT,store).video(pid,edt['artifact_id'])
    VisualQA(store).run(pid,video['artifact_id'])
    native=JianyingExporter(store).export_transfer_bundle(pid,edt['artifact_id'])
    review=Review(store).build(pid)
    report={'project_id':pid,'data_root':str(store.root),'model_mode':'MOCK','human_gates':'SIMULATED_TEST_FIXTURE','font_file_count':5,'families':sorted({f['family'] for f in records if f['file_path'] in paths}), 'faces':[{'family':f['family'],'style':f['style'],'weight':f['weight'],'file_hash':f['file_hash'],'face_index':f['face_index'],'variable':f['variable']} for f in records if f['file_path'] in paths], 'scan':scan,'mechanical_qa':qa,'preview':still['payload']['preview_path'],'browser_renderer_same_cached_bytes':all(f['preview_hash']==Path(f['src']).name.removesuffix('.otf') for f in prepared['fonts']), 'packaged_font_bytes':False,'font_export_mapping':'UNSUPPORTED_OR_APPROXIMATED_IN_JIANYING'}
    report.update(video=video['payload']['preview_path'],voice='TEST_TONE_NOT_TTS',storyboard=board['artifact_id'],native=native,review_pack=review['artifact_id'],human_gate_pending=True)
    output=ROOT/'examples/FONT_ACCEPTANCE_REPORT.json';output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'preview':report['preview'],'project_id':pid,'report':str(output)},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
