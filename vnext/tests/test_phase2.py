import copy
import json
from pathlib import Path
import pytest
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTCollection, TTFont
from jsonschema import Draft202012Validator
from vnext.contracts import Role, utc_now
from vnext.core.runtime import Runtime
from vnext.phase2.contracts import SCHEMAS, DirectorIR, TypographyProfile
from vnext.phase2.fonts import Fonts, sha
from vnext.phase2.knowledge import Knowledge, HARD_RULES
from vnext.phase2.production import CommandBus, Production, Review, mechanical
from vnext.phase2.stages import StageCache
from vnext.storage.store import Store


def make_font(path,weight=400,chars='ABCxyz0123456789 one two threeAlphaBetaSourcefactitems'):
    fb=FontBuilder(1000,isTTF=True)
    cmap={ord(c):f'u{ord(c):04x}' for c in set(chars)}
    order=['.notdef',*cmap.values()];fb.setupGlyphOrder(order);fb.setupCharacterMap(cmap)
    glyphs={}
    for name in order:
        pen=TTGlyphPen(None);pen.moveTo((50,0));pen.lineTo((50,700));pen.lineTo((550,700));pen.lineTo((550,0));pen.closePath();glyphs[name]=pen.glyph()
    fb.setupGlyf(glyphs);fb.setupHorizontalMetrics({n:(600,0) for n in order})
    fb.setupHorizontalHeader(ascent=800,descent=-200)
    fb.setupNameTable({'familyName':'COS Test','styleName':'Regular' if weight==400 else 'Bold',
        'uniqueFontIdentifier':f'COS Test {weight}','fullName':f'COS Test {weight}',
        'psName':f'COSTest-{weight}','version':'Version 1.0'})
    fb.setupOS2(sTypoAscender=800,sTypoDescender=-200,usWinAscent=800,usWinDescent=200,usWeightClass=weight)
    fb.setupPost();fb.setupMaxp();fb.save(path)


@pytest.fixture
def env(tmp_path):
    store=Store(tmp_path/'data');pid=store.create_project('Phase 2').project_id
    knowledge=Knowledge(store);knowledge.initialize(pid)
    knowledge.source(pid,{'source_id':'S1','source_type':'USER_DOCUMENT','title':'Test source',
        'retrieved_at':utc_now(),'excerpt':'Alpha has 3 items'})
    facts=knowledge.fact_pack(pid,{'facts':[{'fact_id':'F1','statement':'Alpha has 3 items',
        'source_ids':['S1'],'support_status':'SUPPORTED','confidence':1}]})
    script=knowledge.bound_script(pid,{'text':'Alpha has 3 items','segments':[
        {'segment_id':'SEG1','text':'Alpha has 3 items','claim':True,'fact_ids':['F1']}]})
    runtime=Runtime(store);runtime.select_worker(pid,Role.AUDIT,'MOCK')
    runtime.run(pid,Role.AUDIT,[script['artifact_id']],request_id='audit')
    runtime.approve_h2(pid,script['artifact_id'],risk_acknowledged=True)
    font_path=tmp_path/'test.ttf';make_font(font_path)
    fonts=Fonts(store);fonts.scan([str(font_path)],'USER');f=fonts.list()[0]
    profile={'profile_id':'TEST','roles':{r:{'font_id':f['font_id'],'weight':400,'size':40}
        for r in ('TITLE','BODY','SUBTITLE','KEYWORD','NUMBER','LABEL','CTA','UI')}}
    CommandBus(store).execute(pid,'TYPOGRAPHY_PROFILE','SET_TYPOGRAPHY_PROFILE',{'profile':profile})
    ir={'script_artifact_id':script['artifact_id'],'scenes':[{'scene_id':'SC1','purpose':'Explain',
        'script_range':['SEG1'],'narrative_function':'EXPLAIN','retention_goal':'VALUE','estimated_duration':10,'beat_ids':['B1']}],
        'beats':[{'beat_id':'B1','scene_id':'SC1','script_segment_id':'SEG1','purpose':'Explain',
        'visual_focus':'Alpha','visual_form':'NUMBER','pattern_id':'NUMBER_EMPHASIS','keyword':'Alpha',
        'timing_intent':10,'slots':{'number':'3'}}]}
    production=Production(store);production.ir(pid,ir);edt=production.generate_edt(pid)
    return store,pid,knowledge,script,ir,edt,fonts,font_path


def test_phase2_schemas_and_missing_fields():
    for model in SCHEMAS.values(): Draft202012Validator.check_schema(model.model_json_schema())
    with pytest.raises(ValueError): DirectorIR.model_validate({'scenes':[],'beats':[]})
    with pytest.raises(ValueError): TypographyProfile.model_validate({'profile_id':'bad','roles':{}})


def test_first_rule_activation_stales_snapshot_and_compiles_all_rule_ids(env):
    from vnext.core.governance import Governance
    from vnext.contracts import RuleRecord
    store,pid,k,script,*_=env
    old=k.snapshot(pid,'SCRIPT_PRIMARY')
    gov=Governance(store)
    def rule(rid,state='CREATED'):
        return RuleRecord(rule_id=rid,lifecycle=state,text=rid,scope='SCRIPT',priority='HIGH',owner='AUDIT',reason='Test policy epoch')
    gov.save_rule(pid,rule('FIRST'));gov.save_rule(pid,rule('FIRST','ACTIVE'))
    assert not store.is_current(old['artifact_id'])
    assert not store.is_current(script['artifact_id'])
    gov.save_rule(pid,rule('SECOND'));gov.save_rule(pid,rule('SECOND','ACTIVE'))
    snap=k.snapshot(pid,'SCRIPT_PRIMARY')
    assert {r['rule_id'] for r in snap['payload']['rule']['active_rules']}=={'FIRST','SECOND'}
    gov.save_rule(pid,rule('FIRST','DEPRECATED'))
    assert not store.is_current(snap['artifact_id'])
    assert [r['rule_id'] for r in k.snapshot(pid,'SCRIPT_PRIMARY')['payload']['rule']['active_rules']]==['SECOND']


def test_edt_v1_upgrade_preserves_ranges_and_does_not_infer_bindings():
    from vnext.migration.edt_v2 import upgrade_edt
    from vnext.contracts import EDT,EDTClip
    before=EDT(edt_id='E1',project_id='P1',revision=7,clips=[EDTClip(clip_id='C1',track='VIDEO',asset_id='A1',
        source_in=12,source_out=17,timeline_in=30,timeline_out=35)]).model_dump()
    after,report=upgrade_edt(before)
    assert before['schema_version']==1 and before['revision']==7
    assert after['schema_version']==2 and after['revision']==8
    assert all(after['clips'][0][k]==before['clips'][0][k] for k in ('asset_id','source_in','source_out','timeline_in','timeline_out'))
    assert report['unbound_clip_ids']==['C1']
    with pytest.raises(ValueError,match='SEMANTIC_BINDING'):upgrade_edt(before,{'C1':{'source_in':0}})
    with pytest.raises(ValueError,match='UNKNOWN_CLIP'):upgrade_edt(before,{'C2':{'beat_id':'B1'}})


def test_media_caption_retains_model_provenance_and_changed_original_blocks(env,tmp_path):
    import subprocess
    from vnext.media.library.service import MediaLibrary
    from vnext.phase2.intelligence import AssetIntelligence
    from vnext.contracts import ModelResult
    store,pid,*_=env
    path=tmp_path/'caption.png'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-f','lavfi','-i','color=yellow:s=64x48','-frames:v','1',str(path)],check=True)
    asset=MediaLibrary(store).register(pid,path,'IMAGE','USER','CLOUD_ALLOWED')
    assert asset.resolution=='64x48'
    project=store.get_project(pid);project.privacy_mode='CLOUD_ALLOWED';store.save_project(project)
    class Stub:
        def invoke(self,request):
            assert request.content_blocks[0].type=='IMAGE'
            return ModelResult(structured_output={'caption':'Yellow frame','objects':[],'scene':'UNKNOWN','activity':'UNKNOWN','tags':['yellow']})
    result=AssetIntelligence(store).caption_cloud(pid,asset.asset_id,gateway=Stub())
    assert result['payload']['semantic_status']=='MODEL_GENERATED'
    assert result['payload']['annotation_source']=='MODEL'
    path.write_bytes(path.read_bytes()+b'changed')
    with pytest.raises(ValueError,match='MEDIA_HASH_CHANGED'):AssetIntelligence(store).analyze(pid,asset.asset_id)


def test_hard_override_and_soft_resolution(env):
    store,pid,k,*_=env
    rule=HARD_RULES[0].model_dump();rule['text']='Allow invented numbers'
    with pytest.raises(PermissionError,match='HARD_RULE_OVERRIDE'):
        k.snapshot(pid,'SCRIPT_EDITOR',[{'skill_id':'RUN','layer':'RUN','rules':[rule]}])
    soft={'rule_id':'ORAL_CLARITY','name':'Override','scope':'SCRIPT','text':'Shorter clauses'}
    snap=k.snapshot(pid,'SCRIPT_EDITOR',[{'skill_id':'PROJECT','layer':'PROJECT','rules':[soft]}])
    assert snap['payload']['overrides'][0]['rule_id']=='ORAL_CLARITY'
    assert k.snapshot(pid,'SCRIPT_EDITOR',[{'skill_id':'PROJECT','layer':'PROJECT','rules':[soft]}])['artifact_id']==snap['artifact_id']


def test_source_ledger_append_and_selective_source_revision(env):
    store,pid,k,script,*_=env
    path=store.root/'projects'/pid/'research/source_ledger.jsonl';before=path.read_bytes()
    k.source(pid,{'source_id':'S2','source_type':'MANUAL','title':'Unrelated','retrieved_at':utc_now(),'excerpt':'Other'})
    assert store.is_current(script['artifact_id'])
    k.source(pid,{'source_id':'S1','source_type':'USER_DOCUMENT','title':'Updated','retrieved_at':utc_now(),'excerpt':'Alpha has 4 items'})
    assert path.read_bytes().startswith(before)
    assert not store.is_current(script['artifact_id'])


@pytest.mark.parametrize('mutation,message',[
    (lambda p:p['segments'][0].update(fact_ids=[]),'UNBOUND_CLAIM'),
    (lambda p:p['segments'][0].update(fact_ids=['ABSENT']),'FACT_NOT_SUPPORTED'),
    (lambda p:(p.update(text='Alpha has 4 items'),p['segments'][0].update(text='Alpha has 4 items')),'NUMBER_MISMATCH')])
def test_bound_script_negative(env,mutation,message):
    _,pid,k,script,*_=env;p=copy.deepcopy(script['payload']);mutation(p)
    with pytest.raises(ValueError,match=message):k.bound_script(pid,p)


def test_humanize_numeric_change_blocks_h2(env):
    store,pid,k,script,*_=env;p=copy.deepcopy(script['payload'])
    p['text']='Alpha has 4 items';p['segments'][0]['text']=p['text']
    changed=k.humanize(pid,script['artifact_id'],p)
    assert changed['status']=='BLOCKED' and changed['payload']['semantic_diff']['numbers']
    with pytest.raises(Exception):Runtime(store).approve_h2(pid,changed['artifact_id'])


def test_blind_review_rejects_other_opinions_and_h2_mock_risk(env):
    store,pid,_,script,*_=env;runtime=Runtime(store)
    audit=store.latest(pid,'AUDIT')
    with pytest.raises(Exception,match='BLIND_REVIEW_INPUT_FORBIDDEN'):
        runtime.run(pid,Role.AUDIT,[script['artifact_id'],audit['artifact_id']],request_id='bad')
    with pytest.raises(Exception,match='MOCK_AUDIT_RISK'):
        runtime.approve_h2(pid,script['artifact_id'])
    assert any(store.get_artifact(d['artifact_id'])['artifact_type'].startswith('SOURCE_') for d in audit['dependencies'])


@pytest.mark.parametrize('kind,role',[('FACT_PACK','ANALYTICS'),('SOURCE_X','AUDIT'),('DIRECTOR_IR','VIDEO_QA'),
    ('WRITING_RULE_SET','HUMAN'),('TYPOGRAPHY_PROFILE','DIRECTOR'),('PROJECT_FONT_SNAPSHOT','TIMELINE'),('VISUAL_EDT','DIRECTOR')])
def test_phase2_single_writers(env,kind,role):
    store,pid,*_=env
    with pytest.raises(PermissionError):store.create_artifact(pid,kind,{},role=role)


def test_director_ir_missing_slot_no_pixels_and_owner(env):
    store,pid,_,_,ir,*_=env;production=Production(store)
    p=copy.deepcopy(ir);p['beats'][0]['slots']={}
    with pytest.raises(ValueError,match='PATTERN_SLOT_MISSING'):production.ir(pid,p)
    p=copy.deepcopy(ir);p['beats'][0]['slots']['fontSize']=50
    with pytest.raises(ValueError,match='PIXEL_LAYOUT'):production.ir(pid,p)
    with pytest.raises(PermissionError):production.ir(pid,ir,actor='TIMELINE')


def test_edit_owner_revision_conflict_and_font_undo_redo(env):
    store,pid,_,_,_,edt,*_=env;bus=CommandBus(store)
    with pytest.raises(PermissionError):bus.execute(pid,'EDT','SNAPSHOT',{},actor='DIRECTOR',actor_type='AGENT')
    with pytest.raises(ValueError,match='CONFLICT'):bus.execute(pid,'EDT','SNAPSHOT',{},expected_revision='wrong')
    first=store.latest(pid,'TYPOGRAPHY_PROFILE')
    second=bus.execute(pid,'TYPOGRAPHY_PROFILE','SET_FONT_SIZE',{'role':'SUBTITLE','value':32})
    assert store.get_artifact(edt['artifact_id'])['current_status']=='STALE'
    undone=bus.execute(pid,'TYPOGRAPHY_PROFILE','UNDO',{})
    assert undone['payload']['roles']['SUBTITLE']['size']==first['payload']['roles']['SUBTITLE']['size']
    redone=bus.execute(pid,'TYPOGRAPHY_PROFILE','REDO',{})
    assert redone['payload']['roles']['SUBTITLE']['size']==second['payload']['roles']['SUBTITLE']['size']


def test_storyboard_gate_is_visual_specific_and_new_ir_invalidates(env):
    store,pid,_,_,ir,edt,*_=env;production=Production(store)
    visual=store.latest(pid,'VISUAL_EDT');director=store.latest(pid,'DIRECTOR_IR')
    board=store.create_artifact(pid,'STORYBOARD',{'ir_hash':director['output_hash'],'ir_artifact_id':director['artifact_id'],
        'entries':[{'beat_id':'B1'}]},role='STORYBOARD',dependencies=[store.dependency(visual['artifact_id']),store.dependency(director['artifact_id'])])
    production.storyboard_gate(pid,board.artifact_id,'APPROVE','Tester')
    CommandBus(store).execute(pid,'EDT','ADD',{'track':'VOICE','timeline_out':10,'source_out':10})
    assert production.require_storyboard(pid)
    production.ir(pid,{**ir,'beats':[{**ir['beats'][0],'keyword':'Beta'}]})
    with pytest.raises(ValueError,match='STORYBOARD'):production.require_storyboard(pid)
    assert store.get_artifact(board.artifact_id)['current_status']=='STALE'


def test_storyboard_rejection_routes_to_director(env):
    store,pid,_,_,_,_,*_=env;director=store.latest(pid,'DIRECTOR_IR')
    board=store.create_artifact(pid,'STORYBOARD',{'ir_hash':director['output_hash'],'ir_artifact_id':director['artifact_id'],
        'entries':[{'beat_id':'B1'}]},role='STORYBOARD',dependencies=[store.dependency(director['artifact_id'])])
    Production(store).storyboard_gate(pid,board.artifact_id,'REJECT','Tester','Please explain the number')
    assert store.latest(pid,'CHANGE_REQUEST')['payload']['owner']=='DIRECTOR'


def test_fonts_scan_cache_ttc_duplicate_faces_and_hash_changes(env,tmp_path):
    store,pid,*rest=env;fonts=rest[-2];font_path=rest[-1]
    assert fonts.scan([str(font_path)],'USER')['cached']==1
    font2=tmp_path/'bold.ttf';make_font(font2,700)
    ttc=tmp_path/'two.ttc';collection=TTCollection();collection.fonts=[TTFont(font_path),TTFont(font2)];collection.save(ttc)
    fonts.scan([str(ttc)],'USER');faces=[f for f in fonts.list() if f['file_path']==str(ttc)]
    assert len(faces)==2 and {f['face_index'] for f in faces}=={0,1}
    original=fonts.list()[0]['font_id'];fonts.face(original)
    font_path.write_bytes(font_path.read_bytes()+b'changed')
    issues=fonts.check(pid,[('BODY','Alpha')])
    assert any(x['code']=='FONT_HASH_CHANGED' for x in issues)
    assert store.get_project(pid).project_id==pid


def test_font_snapshot_glyph_strict_fallback_missing(env,tmp_path):
    store,pid,_,_,_,_,fonts,font_path=env
    assert any(x['code']=='FONT_GLYPH_MISSING' for x in fonts.check(pid,[('BODY','中')]))
    fallback=tmp_path/'chinese.ttf';make_font(fallback,chars='中ABC ')
    fonts.scan([str(fallback)],'USER');f=next(x for x in fonts.list() if x['file_path']==str(fallback))
    payload=copy.deepcopy(store.latest(pid,'TYPOGRAPHY_PROFILE')['payload'])
    payload.update(production_policy='ALLOW_FALLBACK',fallback_font_id=f['font_id'])
    Fonts(store).profile(pid,payload)
    assert any(x['code']=='FONT_FALLBACK_ACTIVE' and x['severity']=='WARNING' for x in fonts.check(pid,[('BODY','中')]))
    font_path.unlink()
    assert any(x['code']=='FONT_MISSING' for x in fonts.check(pid,[('BODY','Alpha')]))


def test_mechanical_qa_subtitle_and_voice_veto(env):
    store,pid,_,_,_,edt,*_=env
    report=mechanical(store,pid,edt['artifact_id'],True)
    assert report['verdict']=='FAIL' and any(x['code']=='MISSING_VOICE' for x in report['issues'])
    clip=next(c for c in edt['payload']['clips'] if c['track']=='SUBTITLE')
    CommandBus(store).execute(pid,'EDT','TRANSFORM',{'clip_id':clip['clip_id'],'position':{'x':.5,'y':.5}})
    report=mechanical(store,pid,store.get_project(pid).timeline_artifact_id)
    assert any(x['code']=='SUBTITLE_BASELINE' for x in report['issues'])


def test_stage_cache_late_resume_rebuild_and_input_change(env):
    store,pid,_,script,*_=env;cache=StageCache(store);count=[]
    def operation():
        count.append(1);return store.create_artifact(pid,'TEST_OUTPUT',{'ok':True},role='TEST',
            dependencies=[store.dependency(script['artifact_id'])]).model_dump()
    first=cache.run(pid,'RESEARCH',[script['artifact_id']],operation,worker='MOCK')
    assert cache.run(pid,'RESEARCH',[script['artifact_id']],operation,worker='MOCK')['stage_cache_hit']
    with pytest.raises(RuntimeError):cache.run(pid,'RENDER',[script['artifact_id']],lambda:(_ for _ in ()).throw(RuntimeError('late failure')))
    assert cache.run(pid,'RESEARCH',[script['artifact_id']],operation,worker='MOCK')['artifact_id']==first['artifact_id']
    with store.connection() as db:db.execute('DELETE FROM stage_cache')
    assert next(x for x in cache.states(pid) if x['stage']=='RESEARCH')['output_artifact']==first['artifact_id']
    assert len(count)==1


def test_phase2_http_permissions_and_font_preview_is_read_only(env,monkeypatch):
    import importlib
    from fastapi.testclient import TestClient
    store,pid,*_=env
    monkeypatch.setenv('CONTENT_OS_DATA',str(store.root))
    import vnext.apps.workbench.server as module
    module=importlib.reload(module);client=TestClient(module.app)
    assert client.get('/phase2.js').status_code==200
    forbidden=client.post(f'/api/projects/{pid}/phase2/facts',json={'actor':'ANALYTICS','payload':{'facts':[]}})
    assert forbidden.status_code==403
    font=client.get('/api/fonts').json()[0]
    before=len(store.artifacts(pid));response=client.get(f"/api/fonts/{font['font_id']}/file")
    assert response.status_code==200 and response.headers['X-Font-SHA256']==sha(Path(Fonts(store).face(font['font_id']).preview_path))
    assert len(store.artifacts(pid))==before


def test_disagreement_needs_owner_evidence_not_vote(env):
    store,pid,k,script,*_=env
    pending=k.disagreement(pid,script['artifact_id'],[{'worker':'A','claim':'3'},{'worker':'B','claim':'4'}])
    assert pending['payload']['automatic_vote'] is False
    with pytest.raises(ValueError,match='DISAGREEMENT'):Runtime(store).approve_h2(pid,script['artifact_id'],True)
    with pytest.raises(PermissionError):k.resolve_disagreement(pid,pending['artifact_id'],[script['artifact_id']],'vote','ANALYTICS')
    with pytest.raises(ValueError):k.resolve_disagreement(pid,pending['artifact_id'],[],'majority','RESEARCH')
    k.resolve_disagreement(pid,pending['artifact_id'],[store.latest(pid,'FACT_PACK')['artifact_id']],'Confirmed source evidence','RESEARCH')
    assert Runtime(store).approve_h2(pid,script['artifact_id'],True)['status']=='SCRIPT_LOCKED'


def test_minimax_gateway_maps_video_and_never_uploads_local(monkeypatch):
    from vnext.contracts import ModelMessage,ModelRequest
    from vnext.gateways.model.gateway import ModelGateway,GatewayError
    for key,value in {'MINIMAX_BASE_URL':'https://api.minimax.io/v1','MINIMAX_API_KEY':'test-key',
                      'MINIMAX_MODEL':'MiniMax-M3'}.items():monkeypatch.setenv(key,value)
    calls=[]
    def post(url,key,body):
        calls.append(body)
        return {'choices':[{'message':{'content':'{"ok":true}'},'finish_reason':'stop'}]}
    gateway=ModelGateway();monkeypatch.setattr(gateway,'_post',post)
    req=ModelRequest(role=Role.VIDEO_QA,worker_profile='MINIMAX',system_prompt='Review',prompt_version='TEST',
        messages=[ModelMessage(role='user',content='Evidence')],content_blocks=[{'type':'VIDEO',
        'uri':'data:video/mp4;base64,AAAA','mime_type':'video/mp4'}],response_schema={'type':'object','required':['ok']},config={'cloud_policy':'LOCAL_ONLY'})
    with pytest.raises(GatewayError,match='LOCAL_ONLY'):gateway.invoke(req)
    assert calls==[]
    req=req.model_copy(update={'config':{'cloud_policy':'ASK_BEFORE_UPLOAD'}})
    with pytest.raises(GatewayError,match='CONFIRMATION'):gateway.invoke(req)
    req=req.model_copy(update={'config':{'cloud_policy':'CLOUD_ALLOWED'}})
    assert gateway.invoke(req).structured_output['ok']
    assert calls[0]['messages'][-1]['content'][-1]['type']=='video_url'
    assert calls[0]['reasoning_split'] is True


def test_videoqa_veto_timestamp_privacy_and_review_freshness(env,tmp_path):
    from vnext.phase2.intelligence import VisualQA
    store,pid,_,script,_,edt,*_=env
    board=store.create_artifact(pid,'STORYBOARD',{'ir_hash':store.latest(pid,'DIRECTOR_IR')['output_hash'],
        'ir_artifact_id':store.latest(pid,'DIRECTOR_IR')['artifact_id'],'entries':[{'beat_id':'B1'}]},role='STORYBOARD',
        dependencies=[store.dependency(store.latest(pid,'VISUAL_EDT')['artifact_id'])])
    Production(store).storyboard_gate(pid,board.artifact_id,'APPROVE','Tester')
    store.create_artifact(pid,'VOICE',{'test':True},role='VOICE',dependencies=[store.dependency(script['artifact_id'])])
    qa=store.create_artifact(pid,'MECHANICAL_QA',{'verdict':'PASS','issues':[],'checked_artifact_id':edt['artifact_id']},
        role='MECHANICAL_QA',dependencies=[store.dependency(edt['artifact_id'])])
    path=tmp_path/'fixture.mp4';path.write_bytes(b'test-fixture-not-video')
    render=store.create_artifact(pid,'RENDER',{'preview_path':str(path),'media_type':'video/mp4'},role='RENDER',
        dependencies=[store.dependency(edt['artifact_id'])])
    with pytest.raises(ValueError,match='TIMESTAMP'):
        VisualQA(store).run(pid,render.artifact_id,issues=[{'code':'INVALID','severity':'BLOCKER','owner':'DIRECTOR','description':'Bad','start':9,'end':20}])
    with pytest.raises(PermissionError,match='LOCAL_ONLY'):VisualQA(store).run(pid,render.artifact_id,worker='MINIMAX')
    fail=VisualQA(store).run(pid,render.artifact_id,issues=[{'code':'BAD_LAYOUT','severity':'BLOCKER','owner':'DIRECTOR','description':'Needs director rework','start':1,'end':2}])
    assert fail['payload']['verdict']=='FAIL' and store.latest(pid,'CHANGE_REQUEST')['payload']['owner']=='DIRECTOR'
    with pytest.raises(ValueError,match='QA_VETO'):Review(store).build(pid)
    VisualQA(store).run(pid,render.artifact_id)
    pack=Review(store).build(pid)
    with pytest.raises(ValueError,match='RISK'):Review(store).gate(pid,pack['artifact_id'],'APPROVE','Tester')
    Review(store).gate(pid,pack['artifact_id'],'APPROVE_WITH_RISK','Tester',['MOCK_VISUAL_QA'])
    store.create_artifact(pid,'RENDER',{'preview_path':str(path),'media_type':'video/mp4'},role='RENDER',
        dependencies=[store.dependency(edt['artifact_id'])])
    assert not store.is_current(pack['artifact_id'])


def test_review_pack_requires_acknowledgment_only_for_actionable_qa_issues(env,tmp_path):
    from vnext.phase2.intelligence import VisualQA
    store,pid,_,script,_,edt,*_=env
    board=store.create_artifact(pid,'STORYBOARD',{'ir_hash':store.latest(pid,'DIRECTOR_IR')['output_hash'],
        'ir_artifact_id':store.latest(pid,'DIRECTOR_IR')['artifact_id'],'entries':[{'beat_id':'B1'}]},role='STORYBOARD',
        dependencies=[store.dependency(store.latest(pid,'VISUAL_EDT')['artifact_id'])])
    Production(store).storyboard_gate(pid,board.artifact_id,'APPROVE','Tester')
    store.create_artifact(pid,'VOICE',{'test':True},role='VOICE',dependencies=[store.dependency(script['artifact_id'])])
    store.create_artifact(pid,'MECHANICAL_QA',{'verdict':'PASS','issues':[],'checked_artifact_id':edt['artifact_id']},
        role='MECHANICAL_QA',dependencies=[store.dependency(edt['artifact_id'])])
    path=tmp_path/'fixture.mp4';path.write_bytes(b'test-fixture-not-video')
    render=store.create_artifact(pid,'RENDER',{'preview_path':str(path),'media_type':'video/mp4'},role='RENDER',
        dependencies=[store.dependency(edt['artifact_id'])])
    VisualQA(store).run(pid,render.artifact_id,issues=[
        {'code':'LAYOUT_RISK','severity':'WARNING','owner':'DIRECTOR','description':'Review spacing','start':1,'end':2},
        {'code':'COMPARE_LAYOUT_CLEAR','severity':'INFO','owner':'DIRECTOR','description':'Positive observation','start':3,'end':4}])
    pack=Review(store).build(pid)
    risk_codes={risk['code'] for risk in pack['payload']['risks']}
    assert 'LAYOUT_RISK' in risk_codes and 'COMPARE_LAYOUT_CLEAR' not in risk_codes
    with pytest.raises(ValueError,match='RISK_ACKNOWLEDGMENT_REQUIRED'):
        Review(store).gate(pid,pack['artifact_id'],'APPROVE_WITH_RISK','Tester',['COMPARE_LAYOUT_CLEAR'])


@pytest.mark.parametrize('asset_type,expected', [('IMAGE','LOCAL_ONLY_ASSET_IN_VIDEO'),('AUDIO','SILENT_COPY_REQUIRED')])
def test_real_videoqa_checks_media_type_and_keeps_local_asset_guard(env,tmp_path,monkeypatch,asset_type,expected):
    from vnext.contracts import MediaAsset
    from vnext.phase2.intelligence import VisualQA
    from vnext.media.library.service import MediaLibrary
    import vnext.phase2.intelligence as intelligence
    import vnext.registries.catalog as catalog
    store,pid,_,_,_,edt,*_=env
    value=copy.deepcopy(edt['payload']);value['clips'][0]['asset_id']='MED-private'
    current=store.create_artifact(pid,'EDT',value,role='TIMELINE')
    project=store.get_project(pid);project.privacy_mode='ASK_BEFORE_UPLOAD';project.timeline_artifact_id=current.artifact_id
    store.save_project(project)
    store.create_artifact(pid,'MECHANICAL_QA',{'verdict':'PASS','issues':[], 'checked_artifact_id':current.artifact_id},
        role='MECHANICAL_QA',dependencies=[store.dependency(current.artifact_id)])
    path=tmp_path/'fixture.mp4';path.write_bytes(b'guard-check')
    render=store.create_artifact(pid,'RENDER',{'preview_path':str(path),'media_type':'video/mp4'},role='RENDER',
        dependencies=[store.dependency(current.artifact_id)])
    asset=MediaAsset(asset_id='MED-private',project_id=pid,type=asset_type,original_path=str(path),hash='fixture',
        created_at=utc_now(),source='USER',owner='user',cloud_policy='LOCAL_ONLY')
    monkeypatch.setattr(MediaLibrary,'assets',lambda self,p:[asset])
    monkeypatch.setattr(catalog,'worker_options',lambda role:[{'worker_id':'MINIMAX','disabled':False}])
    def silent_copy(*args):raise ValueError('SILENT_COPY_REQUIRED')
    monkeypatch.setattr(intelligence,'visual_review_copy',silent_copy)
    with pytest.raises(PermissionError if asset_type=='IMAGE' else ValueError,match=expected):
        VisualQA(store).run(pid,render.artifact_id,worker='MINIMAX',upload_confirmed=True)
    assert store.latest(pid,'VIDEO_QA') is None


def test_rule_set_revision_is_append_only_and_next_snapshot_reads_it(env):
    from vnext.core.governance import Governance
    store,pid,k,*_=env
    path=store.root/'projects'/pid/'audit/rule_events.jsonl';before=path.read_bytes()
    first=k.snapshot(pid,'SCRIPT_PRIMARY')
    payload=copy.deepcopy(store.latest(pid,'WRITING_RULE_SET')['payload']);payload['version']='2'
    payload['rules'].append({'rule_id':'SOURCE_FIRST','name':'Source first','scope':'SCRIPT','text':'Use source-bound claims'})
    k.rules(pid,'WRITING_RULE_SET',payload,'EVOLUTION')
    assert path.read_bytes().startswith(before)
    assert 'SOURCE_FIRST' in Governance(store).current_rules(pid)
    second=k.snapshot(pid,'SCRIPT_PRIMARY')
    assert second['artifact_id']!=first['artifact_id'] and any(r['rule_id']=='SOURCE_FIRST' for r in second['payload']['rules'])
    with pytest.raises(PermissionError):k.rules(pid,'WRITING_RULE_SET',payload,'ANALYTICS')


def test_disagreement_can_be_resolved_after_source_repair(env):
    store,pid,k,script,*_=env
    disagreement=k.disagreement(pid,script['artifact_id'],[{'worker':'A','claim':'source incomplete'},{'worker':'B','claim':'source sufficient'}])
    assert store.latest(pid,'CHANGE_REQUEST')['payload']['owner']=='RESEARCH'
    k.source(pid,{'source_id':'S1','source_type':'MANUAL','title':'Repaired source','retrieved_at':utc_now(),'excerpt':'Alpha has 3 items with new evidence'})
    assert not store.is_current(disagreement['artifact_id'])
    fact=k.fact_pack(pid,{'facts':[{'fact_id':'F1','statement':'Alpha has 3 items','source_ids':['S1'],'support_status':'SUPPORTED','confidence':1}]})
    resolved=k.resolve_disagreement(pid,disagreement['artifact_id'],[fact['artifact_id']],'New evidence reviewed','RESEARCH')
    assert store.is_current(resolved['artifact_id']);k.require_no_disagreement(pid)


def test_multi_step_undo_redo_and_new_edit_clears_redo(env):
    store,pid,*_=env;bus=CommandBus(store)
    original=store.latest(pid,'TYPOGRAPHY_PROFILE')['payload']['roles']['SUBTITLE']['size']
    for size in (32,30,28):bus.execute(pid,'TYPOGRAPHY_PROFILE','SET_FONT_SIZE',{'role':'SUBTITLE','value':size})
    for size in (30,32,original):assert bus.execute(pid,'TYPOGRAPHY_PROFILE','UNDO',{})['payload']['roles']['SUBTITLE']['size']==size
    for size in (32,30,28):assert bus.execute(pid,'TYPOGRAPHY_PROFILE','REDO',{})['payload']['roles']['SUBTITLE']['size']==size
    bus.execute(pid,'TYPOGRAPHY_PROFILE','UNDO',{})
    bus.execute(pid,'TYPOGRAPHY_PROFILE','SET_FONT_SIZE',{'role':'SUBTITLE','value':29})
    with pytest.raises(ValueError,match='NOTHING_TO_REDO'):bus.execute(pid,'TYPOGRAPHY_PROFILE','REDO',{})
    events=[json.loads(x) for x in (store.root/'projects'/pid/'events.jsonl').read_text().splitlines()]
    assert any(x['kind']=='EDIT_COMMAND' and x['operation']=='UNDO' for x in events)


def test_stage_running_is_live_and_replacing_input_does_not_stale_own_stage(env):
    store,pid,k,script,*_=env;cache=StageCache(store)
    def operation():
        assert next(x for x in cache.states(pid) if x['stage']=='SCRIPT_EDITOR')['status']=='RUNNING'
        return k.bound_script(pid,script['payload'],'SCRIPT_EDITOR')
    result=cache.run(pid,'SCRIPT_EDITOR',[script['artifact_id']],operation)
    assert store.is_current(store.latest(pid,'STAGE_SCRIPT_EDITOR')['artifact_id'])
    assert store.is_current(result['artifact_id'])


def test_plain_import_cannot_bypass_bound_script_and_director_has_no_font_ids(env):
    from vnext.core.editing import Editing
    store,pid,_,script,ir,*_=env
    imported=Editing(store).script(pid,'New unsourced claim')
    assert imported['artifact_type']=='SCRIPT_REFERENCE' and imported['payload']['requires_claim_binding']
    assert store.latest(pid,'SCRIPT')['artifact_id']==script['artifact_id']
    ir=copy.deepcopy(ir);ir['beats'][0]['slots']['font_id']='FONT-any'
    with pytest.raises(ValueError,match='PIXEL_LAYOUT'):Production(store).ir(pid,ir)


def test_media_lock_and_source_range_survive_ir_generation(env,tmp_path):
    from vnext.contracts import MediaAsset
    store,pid,_,_,ir,*_=env
    asset=MediaAsset(asset_id='MED-TEST',project_id=pid,type='VIDEO',original_path=str(tmp_path/'source.mp4'),
        hash='a'*64,created_at=utc_now(),source='TEST',owner='HUMAN',cloud_policy='LOCAL_ONLY',duration=60)
    Path(asset.original_path).write_bytes(b'test fixture; no decode used in this test')
    with store.connection() as db:db.execute('INSERT INTO media VALUES (?,?,?)',(asset.asset_id,pid,asset.model_dump_json()))
    bus=CommandBus(store);bus.execute(pid,'MEDIA_SELECTION','SELECT',{'media_need':'Source','mode':'LOCKED','selected_asset_id':asset.asset_id})
    with pytest.raises(PermissionError,match='HUMAN_MEDIA_LOCK'):bus.execute(pid,'MEDIA_SELECTION','SELECT',{'media_need':'Source','mode':'AUTO'},actor='MEDIA_RESOLVER',actor_type='AGENT')
    ir=copy.deepcopy(ir);ir['beats'][0].update(pattern_id='SCREEN_DETAIL',slots={'media_asset_id':asset.asset_id,'source_in':20,'source_out':25})
    Production(store).ir(pid,ir);edt=Production(store).generate_edt(pid)
    clip=next(c for c in edt['payload']['clips'] if c['track']=='MEDIA')
    assert (clip['source_in'],clip['source_out'],clip['timeline_out'])==(20,25,10)


def test_native_canvas_preserves_foreground_gaps_and_reports_font_losses(env,monkeypatch):
    from vnext.exporters.jianying.adapter import JianyingExporter
    import vnext.phase2.production as module
    store,pid,_,_,_,edt,*_=env
    bus=CommandBus(store)
    bus.execute(pid,'EDT','ADD',{'track':'TEXT','timeline_in':20,'timeline_out':30,'source_out':10,'metadata':{'text':'Alpha'}})
    monkeypatch.setattr(module,'mechanical',lambda *a,**kw:{'verdict':'PASS','issues':[]})
    monkeypatch.delenv('JIANYING_DRAFT_ROOT',raising=False)
    director=store.latest(pid,'DIRECTOR_IR')
    board=store.create_artifact(pid,'STORYBOARD',{'ir_artifact_id':director['artifact_id'],'ir_hash':director['output_hash'],'entries':[{'beat_id':'B1'}]},role='STORYBOARD',dependencies=[store.dependency(store.latest(pid,'VISUAL_EDT')['artifact_id'])])
    Production(store).storyboard_gate(pid,board.artifact_id,'APPROVE','Tester')
    result=JianyingExporter(store).export_transfer_bundle(pid,store.get_project(pid).timeline_artifact_id)
    draft=json.loads((Path(result['native_draft_path'])/'draft_content.json').read_text())
    background=draft['tracks'][0]['segments'][0]
    assert background['target_timerange']=={'start':0,'duration':30_000_000}
    assert any(s['target_timerange']['start']==20_000_000 for t in draft['tracks'] if t['type']=='text' for s in t['segments'])
    assert result['canvas_derivation']['color']=='#ffffff'
    assert any(x['code']=='FONT_NOT_SUPPORTED' for x in result['typography_losses'])


def test_script_fail_gate_returns_owner_and_next_pass_requires_new_audit(env):
    store,pid,k,script,*_=env;runtime=Runtime(store)
    result=runtime.run(pid,Role.AUDIT,[script['artifact_id']],request_id='forced-fail',config={'mock_audit_verdict':'FAIL','mock_finding':'Diagnostic: tighten the explanation'})
    assert result['payload']['verdict']=='FAIL'
    assert store.latest(pid,'SCRIPT_GATE')['payload']['decision']=='FAIL'
    assert store.latest(pid,'CHANGE_REQUEST')['payload']['owner']=='SCRIPT_PRIMARY'
    assert store.latest(pid,'ERROR_CANDIDATE')['created_by_role']=='AUDIT'
    assert store.get_project(pid).h2_script_artifact_id is None
    with pytest.raises(Exception,match='AUDIT_FAIL'):runtime.approve_h2(pid,script['artifact_id'],True)
    fixed=CommandBus(store).execute(pid,'SCRIPT','REPLACE_SCRIPT',{'payload':script['payload']})
    with pytest.raises(Exception,match='CURRENT_INDEPENDENT_AUDIT'):runtime.approve_h2(pid,fixed['artifact_id'],True)
    runtime.run(pid,Role.AUDIT,[fixed['artifact_id']],request_id='fixed-pass')
    runtime.approve_h2(pid,fixed['artifact_id'],True)
    assert store.latest(pid,'SCRIPT_GATE')['payload']['decision']=='PASS'


def test_asset_privacy_scene_caption_transcript_and_optional_semantic_search(env,tmp_path,monkeypatch):
    import subprocess
    from vnext.media.library.service import MediaLibrary
    from vnext.phase2.intelligence import AssetIntelligence
    from vnext.phase2.embeddings import LocalEmbeddings
    store,pid,*_=env
    file=tmp_path/'sample.mp4'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-f','lavfi','-i','color=white:s=64x64:d=2','-c:v','libx264',str(file)],check=True)
    library=MediaLibrary(store);asset=library.register(pid,file,'VIDEO','HUMAN','LOCAL_ONLY')
    intelligence=AssetIntelligence(store)
    analyzed=intelligence.analyze(pid,asset.asset_id,{'caption':'MacBook 操作电脑','tags':['电脑'],'transcript':'打开应用','scene_captions':[{'start':0,'end':2,'text':'操作电脑'}]})
    assert analyzed['payload']['virtual_clips'][0]['source_out']==2
    assert intelligence.search(pid,'打开应用')['matches']
    with pytest.raises(PermissionError,match='LOCAL_ONLY'):intelligence.caption_cloud(pid,asset.asset_id,True)
    monkeypatch.setattr(LocalEmbeddings,'encode',lambda self,texts:{'method':'LOCAL_SENTENCE_TRANSFORMER','model_path':'TEST_ONLY_MODEL','vectors':[[1.,0.] for _ in texts]})
    intelligence.analyze(pid,asset.asset_id,{'caption':'MacBook 操作电脑'})
    assert intelligence.search(pid,'电脑操作')['method']=='LOCAL_SEMANTIC_EMBEDDING'
    assert intelligence.search(pid,'电脑操作')['matches'][0]['similarity']==1


def test_role_run_keeps_run_layer_snapshot_and_does_not_resolve_over_it(env):
    store,pid,k,*_=env;runtime=Runtime(store);runtime.select_worker(pid,Role.SCRIPT_PRIMARY,'MOCK')
    facts=store.latest(pid,'FACT_PACK')
    layers=[{'skill_id':'RUN_SOFT','version':'2','layer':'RUN','rules':[{'rule_id':'ORAL_CLARITY','name':'Run style','scope':'SCRIPT','text':'Use short clauses for this run'}]}]
    result=runtime.run(pid,Role.SCRIPT_PRIMARY,[facts['artifact_id']],request_id='layered',config={'skill_layers':layers})
    snapshot=store.latest(pid,'EFFECTIVE_SKILL_SNAPSHOT_SCRIPT_PRIMARY')
    assert snapshot['payload']['overrides'][0]['layer']=='RUN'
    assert snapshot['artifact_id'] in [d['artifact_id'] for d in result['dependencies']]
    assert store.is_current(result['artifact_id'])


def test_stage_resume_reuses_primary_after_editor_supersedes_canonical_script(env):
    store,pid,k,*_=env;runtime=Runtime(store);cache=StageCache(store)
    for role in (Role.SCRIPT_PRIMARY,Role.SCRIPT_EDITOR):runtime.select_worker(pid,role,'MOCK')
    fact=store.latest(pid,'FACT_PACK');calls=[]
    def primary():
        calls.append('primary');return runtime.run(pid,Role.SCRIPT_PRIMARY,[fact['artifact_id']],request_id='resume-primary')
    first=cache.run(pid,'SCRIPT_PRIMARY',[fact['artifact_id']],primary,worker='MOCK')
    def editor():
        calls.append('editor');return runtime.run(pid,Role.SCRIPT_EDITOR,[first['artifact_id']],request_id='resume-editor')
    final=cache.run(pid,'SCRIPT_EDITOR',[first['artifact_id']],editor,worker='MOCK')
    assert not store.is_current(first['artifact_id'])
    assert cache.run(pid,'SCRIPT_PRIMARY',[fact['artifact_id']],primary,worker='MOCK')['historical_stage_output']
    assert cache.run(pid,'SCRIPT_EDITOR',[first['artifact_id']],editor,worker='MOCK')['artifact_id']==final['artifact_id']
    assert calls==['primary','editor']
    with pytest.raises(Exception,match='STALE_INPUT'):
        runtime.run(pid,Role.AUDIT,[first['artifact_id']],request_id='must-not-audit-history')


def test_storyboard_partial_approval_accumulates_only_for_same_board(env):
    store,pid,_,_,ir,*_=env;production=Production(store)
    ir=copy.deepcopy(ir);ir['scenes'][0].update(beat_ids=['B1','B2'],estimated_duration=20)
    ir['beats'].append({**ir['beats'][0],'beat_id':'B2'})
    director=production.ir(pid,ir);production.generate_edt(pid)
    board=store.create_artifact(pid,'STORYBOARD',{'ir_artifact_id':director['artifact_id'],'ir_hash':director['output_hash'],
        'entries':[{'beat_id':'B1'},{'beat_id':'B2'}]},role='STORYBOARD',dependencies=[store.dependency(director['artifact_id'])])
    assert not production.storyboard_gate(pid,board.artifact_id,'APPROVE','Tester',beat_ids=['B1'])['payload']['all_beats_approved']
    with pytest.raises(ValueError,match='STORYBOARD'):production.require_storyboard(pid)
    assert production.storyboard_gate(pid,board.artifact_id,'APPROVE','Tester',beat_ids=['B2'])['payload']['all_beats_approved']
    production.require_storyboard(pid)
    production.storyboard_gate(pid,board.artifact_id,'REJECT','Tester','Fix B1',beat_ids=['B1'])
    with pytest.raises(ValueError,match='STORYBOARD'):production.require_storyboard(pid)


def test_visual_binding_change_stales_edt_but_interface_language_does_not(env):
    from vnext.phase2.configuration import visual_config
    store,pid,_,_,_,edt,*_=env
    project=store.get_project(pid);project.interface_language='en-US';store.save_project(project)
    visual_config(store,pid);assert store.is_current(edt['artifact_id'])
    project.character_pack='XIAO-Y_V1';store.save_project(project);visual_config(store,pid)
    assert not store.is_current(edt['artifact_id'])
    newer=Production(store).generate_edt(pid)
    # NUMBER pattern layout may validly include or omit a character depending
    # on the selected registered visual pattern. This test owns invalidation,
    # so assert the stable contract instead of a non-authoritative layout detail.
    assert newer['artifact_id'] != edt['artifact_id']
    assert store.is_current(newer['artifact_id'])
