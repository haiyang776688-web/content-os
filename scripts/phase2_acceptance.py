"""60-second diagnostic. All model reviews, voice and human gates are simulated.

Run: .venv/bin/python scripts/phase2_acceptance.py --data phase2_preview_data
Fonts are local and never copied into the source distribution.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from vnext.contracts import Role, utc_now
from vnext.core.runtime import Runtime
from vnext.core.governance import Governance
from vnext.contracts import ErrorCandidate,RuleRecord
from vnext.exporters.jianying.adapter import JianyingExporter
from vnext.media.library.service import MediaLibrary
from vnext.phase2.fonts import Fonts
from vnext.phase2.intelligence import VisualQA
from vnext.phase2.knowledge import Knowledge
from vnext.phase2.production import Production, CommandBus, Review, mechanical
from vnext.phase2.stages import StageCache
from vnext.registries.export import export
from vnext.renderers.remotion.adapter import RemotionAdapter
from vnext.storage.store import Store


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--data',default='phase2_preview_data')
    options=parser.parse_args();store=Store(Path(options.data).resolve())
    project=store.create_project('Phase 2 · 60秒诊断（全部 Mock；人工确认仅模拟）',character_pack='XIAO-Y_V1')
    pid=project.project_id;k=Knowledge(store);k.initialize(pid);runtime=Runtime(store);cache=StageCache(store)
    statements=['生产先读取规则，再使用已绑定来源的事实。',
                '脚本修改经过独立审计，确认方向后才进入导演设计。',
                '画面按主信息、次信息和辅助信息这3个层次依次展开。',
                '分镜退回责任部门，修复完成后再生成新的分镜版本。',
                '字幕保持单行白字，没有底板，沿固定基线显示。',
                '终稿确认和发布授权分别记录，完成终稿并不自动发布。']
    k.source(pid,{'source_id':'USER_PHASE2','source_type':'USER_DOCUMENT','title':'用户 Phase 2 要求的诊断摘要',
        'retrieved_at':utc_now(),'excerpt':'\n'.join(statements),'publisher':'User supplied brief'})
    facts=cache.run(pid,'RESEARCH',[store.latest(pid,'SOURCE_USER_PHASE2')['artifact_id']],lambda:k.fact_pack(pid,{'facts':[{'fact_id':f'F{i+1}','statement':s,'source_ids':['USER_PHASE2'],
        'support_status':'SUPPORTED','confidence':1,'entity':'Content OS','notes':'Diagnostic of the supplied specification, not a claim about platform news'} for i,s in enumerate(statements)]}),worker='USER_SUPPLIED_SOURCE')
    for role in (Role.SCRIPT_PRIMARY,Role.SCRIPT_EDITOR,Role.AUDIT,Role.DIRECTOR):runtime.select_worker(pid,role,'MOCK')
    def run_role(role,ids,request,config=None):
        snapshot=k.snapshot(pid,role.value,(config or {}).get('skill_layers'))
        return cache.run(pid,role.value,[*ids,snapshot['artifact_id']],lambda:runtime.run(pid,role,ids,request_id=request,config=config),
            worker='MOCK',prompt='DIAGNOSTIC_'+role.value,skills=snapshot['output_hash'],config=config)
    script=run_role(Role.SCRIPT_PRIMARY,[facts['artifact_id']],'primary')
    script=run_role(Role.SCRIPT_EDITOR,[script['artifact_id']],'editor')
    failed_audit=run_role(Role.AUDIT,[script['artifact_id']],'audit-fail',{'mock_audit_verdict':'FAIL',
        'mock_finding':'Diagnostic: independently audit every repaired script version'})
    try:runtime.approve_h2(pid,script['artifact_id'],risk_acknowledged=True)
    except Exception:pass
    else:raise RuntimeError('FAIL gate did not veto H2')
    candidate=store.latest(pid,'ERROR_CANDIDATE');gov=Governance(store);error=gov.confirm_error(pid,candidate['artifact_id'])
    repeated=gov.submit_candidate(pid,ErrorCandidate(summary=candidate['payload']['summary'],root_cause='UNKNOWN',submitted_by_role='AUDIT',artifact_id=script['artifact_id']))
    recurrence=gov.confirm_error(pid,repeated['artifact_id'])
    if recurrence['kind']!='ERROR_RECURRED' or recurrence['error_id']!=error['error_id']:raise RuntimeError('Recurrence linkage failed')
    record=RuleRecord(rule_id='DIAGNOSTIC_REAUDIT',lifecycle='CREATED',text='Every repaired script revision requires a fresh independent audit.',
        scope='SCRIPT',priority='HIGH',owner='AUDIT',reason='Mock diagnostic failure path',related_error=error['error_id'],exceptions=[])
    gov.save_rule(pid,record);gov.save_rule(pid,record.model_copy(update={'lifecycle':'ACTIVE'}))
    script=CommandBus(store).execute(pid,'SCRIPT','REPLACE_SCRIPT',{'payload':script['payload']},actor='SCRIPT_EDITOR',actor_type='AGENT',reason='Owner repairs returned script')
    passed_audit=run_role(Role.AUDIT,[script['artifact_id']],'audit-pass')
    gate=runtime.approve_h2(pid,script['artifact_id'],risk_acknowledged=True)
    cache.record(pid,'H2',[script['artifact_id'],passed_audit['artifact_id']],store.get_artifact(gate['artifact_id']))
    fonts=Fonts(store)
    font_paths=['/System/Library/Fonts/STHeiti Light.ttc','/System/Library/Fonts/Supplemental/Arial.ttf','/System/Library/Fonts/SFNS.ttf']
    if not all(Path(p).is_file() for p in font_paths):raise RuntimeError('Supply three locally available fonts for this macOS diagnostic')
    scan=fonts.scan(font_paths)
    records=fonts.list();cjk=next(f for f in records if f['family']=='Heiti SC')
    latin=next(f for f in records if f['family']=='Arial')
    variable=next(f for f in records if f['variable'])
    roles={r:{'font_id':cjk['font_id'],'weight':cjk['weight'],'size':44 if r=='SUBTITLE' else 64}
        for r in ('TITLE','BODY','SUBTITLE','KEYWORD','NUMBER','LABEL','CTA','UI')}
    roles['NUMBER']={'font_id':latin['font_id'],'weight':latin['weight'],'size':160}
    roles['UI']={'font_id':variable['font_id'],'weight':500,'size':40}
    CommandBus(store).execute(pid,'TYPOGRAPHY_PROFILE','SET_TYPOGRAPHY_PROFILE',
        {'profile':{'profile_id':'XIAOY_LOCAL_DIAGNOSTIC','roles':roles}})
    director=run_role(Role.DIRECTOR,[script['artifact_id']],'director')
    ir=director['payload']
    specs=[('CHARACTER_EXPLAIN_KEYWORD',{'keyword':'来源先行'},'来源先行','FADE'),
           ('TIMELINE_PROCESS',{'steps':['脚本','独立审计','导演设计']},'独立审计','SLIDE_UP'),
           ('NUMBER_EMPHASIS',{'number':'3'},'信息层次','FADE'),
           ('A_B_COMPARE',{'a':'退回责任部门','b':'修复后重新分镜'},'返工有归属','HOLD'),
           ('THREE_POINT_SUMMARY',{'points':['单行白字','没有底板','固定基线']},'字幕规范','SLIDE_UP'),
           ('CHARACTER_EXPLAIN_KEYWORD',{'keyword':'终稿不等于发布'},'终稿不等于发布','FADE')]
    for beat,(pattern,slots,keyword,motion) in zip(ir['beats'],specs):
        beat.update(pattern_id=pattern,slots=slots,keyword=keyword,motion_intent=motion)
    ir=CommandBus(store).execute(pid,'DIRECTOR_IR','REPLACE_IR',{'payload':ir},actor='DIRECTOR',actor_type='AGENT',reason='Diagnostic pattern selection')
    cache.record(pid,'DIRECTOR',[script['artifact_id']],ir)
    from vnext.media.resolver.service import MediaResolver
    # Register the original bundled character so MEDIA has an explicit, available source.
    pack=json.loads((ROOT/'registries/characters/XIAO-Y_V1.json').read_text())
    character=MediaLibrary(store).register(pid,ROOT/pack['master']['path'],'IMAGE','USER','LOCAL_ONLY',source='BUNDLED_CHARACTER')
    selection=CommandBus(store).execute(pid,'MEDIA_SELECTION','SELECT',{'media_need':'Diagnostic bundled character',
        'mode':'MANUAL','selected_asset_id':character.asset_id})
    cache.record(pid,'MEDIA',[ir['artifact_id']],selection)
    edt=cache.run(pid,'EDT',[ir['artifact_id'],store.latest(pid,'PROJECT_FONT_SNAPSHOT')['artifact_id']],lambda:CommandBus(store).execute(pid,'EDT','GENERATE',{}))
    print('Project',pid,'IR/EDT ready',flush=True)
    # Real stills, not placeholder thumbnails. Approval below is explicitly a test fixture.
    board=StageCache(store).run(pid,'STORYBOARD',[ir['artifact_id'],store.latest(pid,'VISUAL_EDT')['artifact_id']],
        lambda:Production(store).storyboard(pid,ROOT))
    Production(store).storyboard_gate(pid,board['artifact_id'],'REJECT','SIMULATED TESTER','Diagnostic gate veto verifies routing only')
    try:Production(store).require_storyboard(pid)
    except Exception:pass
    else:raise RuntimeError('Rejected storyboard did not veto production')
    Production(store).storyboard_gate(pid,board['artifact_id'],'APPROVE','SIMULATED TESTER','Mock acceptance fixture only')
    print('Storyboard rendered and simulated gate recorded',flush=True)
    voice_path=store.root/'projects'/pid/'voice'/'diagnostic-test-tone.wav';voice_path.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-f','lavfi','-i','sine=frequency=440:duration=60',
        '-af','volume=0.2','-ar','48000',str(voice_path)],check=True)
    media=MediaLibrary(store).register(pid,voice_path,'AUDIO','VOICE','LOCAL_ONLY',source='MOCK_60S_TEST_TONE')
    voice=store.create_artifact(pid,'VOICE',{'media_asset_id':media.asset_id,'audio_path':str(voice_path),
        'provider':'mock','status':'MOCK','duration':60,'warning':'Test tone, not TTS'},role='VOICE',
        dependencies=[store.dependency(script['artifact_id'])])
    cache.record(pid,'VOICE',[script['artifact_id'],store.latest(pid,'STORYBOARD_GATE')['artifact_id']],voice.model_dump(),worker='MOCK_TEST_TONE')
    edt=CommandBus(store).execute(pid,'EDT','ADD',{'track':'VOICE','asset_id':media.asset_id,
        'source_in':0,'source_out':60,'timeline_in':0,'timeline_out':60})
    Production(store).require_storyboard(pid)
    qa=mechanical(store,pid,edt['artifact_id'],True)
    mechanical_art=store.create_artifact(pid,'MECHANICAL_QA',qa,role='MECHANICAL_QA',dependencies=[store.dependency(edt['artifact_id'])])
    cache.record(pid,'MECHANICAL_QA',[edt['artifact_id']],mechanical_art.model_dump())
    if qa['verdict']=='FAIL': raise RuntimeError(json.dumps(qa,ensure_ascii=False))
    cache.record(pid,'EDT',[ir['artifact_id']],edt)
    preview=cache.run(pid,'RENDER',[edt['artifact_id'],store.latest(pid,'STORYBOARD_GATE')['artifact_id']],lambda:RemotionAdapter(ROOT,store).video(pid,edt['artifact_id']))
    print('60-second video rendered',flush=True)
    visual=VisualQA(store).run(pid,preview['artifact_id'])
    cache.record(pid,'VIDEO_QA',[preview['artifact_id']],visual,worker='MOCK')
    native=JianyingExporter(store).export_transfer_bundle(pid,edt['artifact_id'])
    review=Review(store).build(pid)
    cache.record(pid,'REVIEW',[d['artifact_id'] for d in review['dependencies']],review)
    Review(store).gate(pid,review['artifact_id'],'APPROVE_WITH_RISK','SIMULATED TESTER',
        [r['code'] for r in review['payload']['risks']],comments='Diagnostic only; not user production approval')
    export(ROOT)
    report={'project_id':pid,'data_root':str(store.root),'duration_seconds':60,'real_stills':12,
        'model_mode':'MOCK','voice':'TEST_TONE_NOT_TTS','human_gates':'SIMULATED_TEST_FIXTURE',
        'video':preview['payload']['preview_path'],'storyboard':board['artifact_id'],'edt':edt['artifact_id'],
        'mechanical_qa':qa,'video_qa':visual['payload'],'review_pack':review['artifact_id'],
        'font_scan':scan,'native':native,'phase2_complete':False,
        'failure_path':{'failed_audit':failed_audit['artifact_id'],'passed_audit':passed_audit['artifact_id'],'error_confirmed':error,'error_recurred':recurrence},
        'stage_states':cache.states(pid)}
    destination=ROOT/'examples'/'PHASE2_DIAGNOSTIC_REPORT.json';destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'project_id':pid,'video':report['video'],'report':str(destination)},ensure_ascii=False),flush=True)


if __name__=='__main__': main()
