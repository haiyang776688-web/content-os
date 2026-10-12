"""Opt-in presentation preserves ownership, time provenance and release gates."""
import copy
import re
import wave
from pathlib import Path
import pytest
from vnext.tests.test_phase2 import env
from vnext.phase2.production import CommandBus, Production
from vnext.phase2.hardening.audio import AudioClock
from vnext.phase2.hardening.visual import VisualResolver, LAYOUTS
from vnext.phase2.hardening.geometry import checks
from vnext.media.library.service import MediaLibrary
from vnext.migration.legacy import sha
from vnext.contracts import EDT
from vnext.renderers.remotion.adapter import RemotionAdapter

ROOT=Path(__file__).resolve().parents[2]

def presentation(store,pid,mode):
    profile=copy.deepcopy(store.latest(pid,'TYPOGRAPHY_PROFILE')['payload'])
    profile['presentation']=mode
    return CommandBus(store).execute(pid,'TYPOGRAPHY_PROFILE','SET_TYPOGRAPHY_PROFILE',{'profile':profile})


def test_standard_layout_unchanged_and_dynamic_scope_is_per_project(env):
    s,pid,_,_,ir,*_=env
    ir=s.latest(pid,'DIRECTOR_IR')['payload']
    first=VisualResolver(s).plan(pid,ir)
    assert first['compositions'][0]['layout']==LAYOUTS['KEYWORD_FULL_FRAME']
    presentation(s,pid,'XIAOY_EXPLAINER')
    dynamic=VisualResolver(s).plan(pid,ir)
    assert dynamic['compositions'][0]['layout']['text'][1]==.42
    presentation(s,pid,'STANDARD')
    assert VisualResolver(s).plan(pid,ir)==first


def test_short_subtitles_keep_content_contiguous_measured_time_and_honest_provenance(env,tmp_path):
    s,pid,_,script,*_=env
    audio=tmp_path/'measured.wav'
    with wave.open(str(audio),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(b'\0\0'*72000)
    asset=MediaLibrary(s).register(pid,audio,'AUDIO','VOICE','LOCAL_ONLY')
    voice=s.create_artifact(pid,'VOICE',{'media_asset_id':asset.asset_id,'audio_path':str(audio),
        'duration':3,'status':'READY'},role='VOICE',dependencies=[s.dependency(script['artifact_id'])])
    AudioClock(s).create(pid,{'audio_artifact_id':voice.artifact_id,'script_artifact_id':script['artifact_id'],
        'audio_hash':sha(audio),'duration':3,'provenance':{'method':'MANUAL_ALIGNMENT','worker':'LOCAL_FIXTURE','version':'1','reviewer':'Fixture'},
        'entries':[{'audio_id':asset.asset_id,'segment_id':'SEG1','start':0,'end':3,'duration':3,
            'phrase_ranges':[{'text':'Alpha has，3 items','start':0,'end':3}]}]},'ALIGNMENT')
    original=AudioClock(s).subtitles(pid)
    presentation(s,pid,'XIAOY_EXPLAINER')
    compact=AudioClock(s).subtitles(pid)
    assert len(compact)>len(original)
    assert all(len(c['metadata']['text'])<=18 for c in compact)
    clean=lambda t:re.sub(r'[\s，。,.]','',t)
    assert clean(''.join(c['metadata']['text'] for c in compact))==clean(script['payload']['text'])
    assert compact[0]['timeline_in']==0 and compact[-1]['timeline_out']==3
    assert all(a['timeline_out']==b['timeline_in'] for a,b in zip(compact,compact[1:]))
    assert all(c['metadata']['split_provenance']=='PROPORTIONAL_WITHIN_ALIGNED_PHRASE' for c in compact)
    assert s.is_usable_input(s.latest(pid,'AUDIO_TIMING_MAP')['artifact_id'])


@pytest.mark.parametrize('action,template',[('XACT-002','CHARACTER_LEFT_TEXT_RIGHT'),('XACT-009','CHARACTER_LEFT_TEXT_RIGHT'),('XACT-012','INFO_LEFT_CHARACTER_RIGHT'),('XACT-020','EXTREME_CLOSEUP')])
def test_wide_gestures_and_portrait_remain_in_safe_area(env,action,template):
    s,pid,_,_,ir,*_=env
    p=s.get_project(pid);p.character_pack='XIAO-Y_V1';p.style_pack='XIAO-Y_STYLE_V1';s.save_project(p)
    presentation(s,pid,'XIAOY_EXPLAINER')
    beat=ir['beats'][0];beat.update(pattern_id='CHARACTER_EXPLAIN_KEYWORD',slots={'keyword':'Alpha'},
        semantic_pattern='EXPLAIN',template_id=template,character_action_id=action)
    Production(s).ir(pid,ir)
    generated=Production(s).generate_edt(pid)
    edt=EDT.model_validate(generated['payload'])
    assert not [i for i in checks(s,pid,edt,strict=True) if i['severity']=='BLOCKER']
    assert any(c.metadata.get('treatment') for c in edt.clips if c.track=='TEXT')


@pytest.mark.parametrize('pattern,semantic,slot,labels',[
    ('TIMELINE_PROCESS','PROCESS','steps',['导出视频','片头抽帧','主体抽帧','结尾抽帧','转场补帧']),
    ('CHARACTER_ACTION_SEQUENCE','EXPLAIN','actions',['记录时间点','调整位置','重新导出','复核画面']),
])
def test_long_step_lists_fit_above_subtitle_band(env,pattern,semantic,slot,labels):
    s,pid,_,_,ir,*_=env
    p=s.get_project(pid);p.character_pack='XIAO-Y_V1';p.style_pack='XIAO-Y_STYLE_V1';s.save_project(p)
    presentation(s,pid,'XIAOY_EXPLAINER')
    beat=ir['beats'][0]
    beat.update(pattern_id=pattern,semantic_pattern=semantic,slots={slot:labels},
        character_action_id='XACT-002',character_intent='EXPLAIN')
    Production(s).ir(pid,ir)
    edt=EDT.model_validate(Production(s).generate_edt(pid)['payload'])
    text=[c for c in edt.clips if c.track=='TEXT']
    assert len(text)==len(labels)
    assert max(c.position['y'] for c in text)<=.78
    assert not [i for i in checks(s,pid,edt,strict=True)
                if i['code'] in ('safe_area_overflow','subtitle_overlap')]


def test_motion_review_never_replaces_render_or_approves_gate(env,tmp_path,monkeypatch):
    s,pid,*_=env
    adapter=RemotionAdapter(ROOT,s);edt=s.latest(pid,'EDT');before=s.latest(pid,'RENDER')
    output=tmp_path/'props.json';output.write_text('{}')
    monkeypatch.setattr('vnext.phase2.production.mechanical',lambda *a,**k:{'verdict':'PASS'})
    monkeypatch.setattr(adapter,'prepare',lambda *a,**k:{'run_id':'TEST-MOTION','props_path':str(output),'composition_fingerprint':'fixture'})
    def fake_render(args,**kw):
        Path(args[5]).write_bytes(b'test renderer fixture')
        return type('Result',(),{'returncode':0,'stderr':''})()
    monkeypatch.setattr('vnext.renderers.remotion.adapter.subprocess.run',fake_render)
    artifact=adapter.storyboard_motion(pid,edt['artifact_id'])
    assert artifact['artifact_type']=='STORYBOARD_MOTION'
    assert artifact['payload']['formal_render'] is False
    assert s.latest(pid,'RENDER')==before and not s.latest(pid,'STORYBOARD_GATE')
    with pytest.raises(ValueError,match='STORYBOARD_APPROVAL_REQUIRED'):adapter.video(pid,edt['artifact_id'])
    with pytest.raises(PermissionError):s.create_artifact(pid,'STORYBOARD_MOTION',{},role='DIRECTOR')
