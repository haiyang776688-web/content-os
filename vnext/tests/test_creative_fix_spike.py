"""Creative spike contracts: reproducible variety without changing script/audio time."""
import copy
import json
from pathlib import Path

import pytest

from vnext.contracts import EDT, EDTClip
from vnext.media.library.service import MediaLibrary
from vnext.phase2.hardening.audio import AudioClock
from vnext.phase2.hardening.visual import (
    TEMPLATES_ALLOWED, VisualResolver, allocate_action, allocate_template,
)
from vnext.phase2.production import CommandBus, mechanical
from vnext.providers.director_contract import request_contract
from vnext.storage.store import Store
from vnext.tests.test_phase2_hardening import clock_env, evidence_env
from vnext.tests.test_phase2 import env

ROOT=Path(__file__).resolve().parents[2]


def test_action_allocator_is_stable_avoids_recent_and_falls_back():
    actions=[{'id':f'XACT-{index:03}', 'semantic_intents':['EXPLAIN']} for index in range(1,5)]
    first=allocate_action('EXPLAIN',[], 'B1','P1',actions)
    second=allocate_action('EXPLAIN',[first], 'B2','P1',actions)
    third=allocate_action('EXPLAIN',[first,second], 'B3','P1',actions)
    assert len({first,second,third})==3
    assert [first,second,third]==[
        allocate_action('EXPLAIN',[], 'B1','P1',actions),
        allocate_action('EXPLAIN',[first], 'B2','P1',actions),
        allocate_action('EXPLAIN',[first,second], 'B3','P1',actions)]
    single=[{'id':'ONLY','semantic_intents':['THINKING']}]
    assert allocate_action('THINKING',['ONLY'],'B9','P1',single)=='ONLY'
    assert allocate_action('EXPLAIN',[a['id'] for a in actions],'B4','P1',actions) in {a['id'] for a in actions}


def test_template_allocator_keeps_semantics_media_requirements_and_rotation():
    registered={t['template_id']:t for t in json.loads((ROOT/'registries/styles/XIAO-Y_TEMPLATES_V1.json').read_text())['templates']}
    recent=[]
    for index in range(8):
        chosen=allocate_template('EXPLAIN',recent,f'B{index}','P1',registered,True,False)
        assert chosen in TEMPLATES_ALLOWED['EXPLAIN']
        assert not registered[chosen]['media_slots']
        if recent:assert chosen!=recent[-1]
        recent.append(chosen)
    assert len(set(recent))>=3
    assert allocate_template('PROCESS',[],'B1','P1',registered,False,False)=='KEYWORD_FULL_FRAME'
    assert allocate_template('COMPARE',[],'B1','P1',registered,True,False)=='COMPARE_SPLIT'
    assert allocate_template('EVIDENCE',[],'B1','P1',registered,True,True) in ('SCREEN_FULL_FRAME','SCREEN_DETAIL_ZOOM')
    assert allocate_template('EVIDENCE',[],'B1','P1',registered,True,True)==allocate_template('EVIDENCE',[],'B1','P1',registered,True,True)


def test_resolver_rebuild_is_stable_and_media_motion_does_not_change_timing(tmp_path):
    store=Store(tmp_path/'store')
    project=store.create_project('Motion',character_pack='XIAO-Y_V1',style_pack='XIAO-Y_STYLE_V1')
    pid=project.project_id
    media=MediaLibrary(store).register(pid,ROOT/'assets/character_master/XIAO-Y_V1.png','IMAGE','HUMAN','LOCAL_ONLY')
    ir={'scenes':[{'beat_ids':['B1','B2']}], 'beats':[
        {'beat_id':'B1','scene_id':'S1','script_segment_id':'SEG1','pattern_id':'SCREEN_DETAIL','character_intent':'EXPLAIN','timing_intent':4,
         'slots':{'media_asset_id':media.asset_id},'motion_intent':'FADE','reveal_order':['PRIMARY']},
        {'beat_id':'B2','scene_id':'S1','script_segment_id':'SEG2','pattern_id':'CHARACTER_EXPLAIN_KEYWORD','character_intent':'EXPLAIN','timing_intent':5,
         'slots':{'keyword':'证据'},'motion_intent':'FADE','reveal_order':['PRIMARY']} ]}
    resolver=VisualResolver(store)
    first=resolver.plan(pid,ir)
    assert first==resolver.plan(pid,copy.deepcopy(ir))
    resolved={'payload':first,'output_hash':'fixture','artifact_id':'fixture'}
    clips=resolver.clips(pid,resolved)
    evidence=[c for c in clips if c['track']=='MEDIA'][0]
    assert evidence['motion']['continuous']=='SLOW_ZOOM'
    assert (evidence['timeline_in'],evidence['timeline_out'])==(0,4)
    assert all('continuous' not in c['motion'] for c in clips if c['track']=='TEXT')
    assert [c['timeline_in'] for c in clips if c['track']=='CHARACTER']==[4]


def test_one_segment_two_beats_uses_measured_audio_without_changing_voice(clock_env):
    store,pid,script,voice,timing=clock_env
    AudioClock(store).create(pid,timing,'ALIGNMENT')
    ir={'script_artifact_id':script['artifact_id'],'scenes':[{'beat_ids':['B1','B2']}], 'beats':[
        {'beat_id':'B1','scene_id':'S1','script_segment_id':'SEG1','pattern_id':'CHARACTER_EXPLAIN_KEYWORD','character_intent':'EXPLAIN','timing_intent':2,
         'slots':{'keyword':'Alpha'},'motion_intent':'FADE','reveal_order':['PRIMARY']},
        {'beat_id':'B2','scene_id':'S1','script_segment_id':'SEG1','pattern_id':'CHARACTER_EXPLAIN_KEYWORD','character_intent':'EXPLAIN','timing_intent':1,
         'slots':{'keyword':'Beta'},'motion_intent':'FADE','reveal_order':['PRIMARY']}]}
    before=store.get_artifact(voice['artifact_id'])['output_hash']
    result=VisualResolver(store).plan(pid,ir)['compositions']
    duration=timing['duration']
    assert result[0]['timing']['end']==pytest.approx(duration*2/3)
    assert result[1]['timing']['start']==result[0]['timing']['end']
    assert result[1]['timing']['end']==pytest.approx(duration)
    assert store.get_artifact(voice['artifact_id'])['output_hash']==before


def test_director_taste_adds_no_schema_fields(env):
    store,pid,*_=env
    schema,prompt=request_contract(store,pid)
    assert 'Avoid slide/PPT-like' in prompt and 'visible information-state changes' in prompt
    assert not {'visual_job','cognitive_change','viewer_should_notice'} & schema['$defs']['Beat']['properties'].keys()


def test_director_contract_lists_registered_image_media(env):
    store,pid,*_=env
    media=MediaLibrary(store).register(pid,ROOT/'assets/character_master/XIAO-Y_V1.png','IMAGE','HUMAN','LOCAL_ONLY')
    schema,prompt=request_contract(store,pid)
    assert media.asset_id in schema['$defs']['Beat']['properties']['slots']['properties']['media_asset_id']['enum']
    assert media.asset_id in prompt
    assert 'XIAO-Y_V1.png' in prompt


def test_mechanical_qa_warns_on_local_action_and_template_repetition(env):
    store,pid,*_=env
    project=store.get_project(pid);project.character_pack='XIAO-Y_V1';store.save_project(project)
    clips=[]
    for index,action in enumerate(('XACT-002','XACT-002','XACT-006')):
        clips.append(EDTClip(clip_id=f'C{index}',track='CHARACTER',beat_id=f'B{index}',
            timeline_in=float(index),timeline_out=float(index+1),source_out=1,
            metadata={'action_id':action,'template_id':'CHARACTER_LEFT_TEXT_RIGHT'}))
    edt=EDT(edt_id='creative-qa',project_id=pid,revision=1,clips=clips)
    artifact=store.create_artifact(pid,'EDT',edt.model_dump(),role='TIMELINE')
    codes={i['code'] for i in mechanical(store,pid,artifact.artifact_id)['issues']}
    assert {'ACTION_REPETITION','TEMPLATE_REPETITION'}<=codes


def test_gui_split_beat_keeps_scene_duration_and_segment_binding(env):
    store,pid,*_=env
    before=store.latest(pid,'DIRECTOR_IR')
    after=CommandBus(store).execute(pid,'DIRECTOR_IR','SPLIT_BEAT',{'beat_id':'B1'},
        expected_revision=before['artifact_id'],reason='Controlled 1:N visual test')
    scene=after['payload']['scenes'][0]
    beats=after['payload']['beats']
    assert len(beats)==2 and len(scene['beat_ids'])==2
    assert {b['script_segment_id'] for b in beats}=={'SEG1'}
    assert sum(b['timing_intent'] for b in beats)==pytest.approx(scene['estimated_duration'])
    assert [b['timing_intent'] for b in beats]==[5,5]
