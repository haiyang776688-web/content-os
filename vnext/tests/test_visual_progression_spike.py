"""The experimental compiler must preserve A/B content while changing pixels."""
import copy
from pathlib import Path

import pytest
from PIL import Image

from vnext.phase2.experimental.visual_progression import (
    VisualProgression, compile_progression, motion_off,
)


def _plan():
    return {
        'source_start':2,'source_end':6,
        'beats':[{'beat_id':'B1','segment_id':'S1','start':2,'end':4},
                 {'beat_id':'B2','segment_id':'S2','start':4,'end':6}],
        'states':[
            {'state_id':'a','beat_id':'B1','start':2,'end':3,'operation':'FULL_FRAME_MEDIA',
             'primary_subject':'EVIDENCE','media_asset_id':'M1'},
            {'state_id':'b','beat_id':'B1','start':3,'end':4,'operation':'ZOOM_TO_REGION',
             'primary_subject':'EVIDENCE','media_asset_id':'M1','region':[.1,.2,.6,.4]},
            {'state_id':'c','beat_id':'B2','start':4,'end':5,'operation':'HIGHLIGHT_RECT',
             'primary_subject':'EVIDENCE','media_asset_id':'M1','region':[.1,.2,.6,.4],
             'focus':[.1,.1,.5,.5]},
            {'state_id':'d','beat_id':'B2','start':5,'end':6,'operation':'CALLOUT_TEXT',
             'primary_subject':'EVIDENCE','media_asset_id':'M1','region':[.1,.2,.6,.4],
             'text':'Fact ID'},
        ],
        'subtitle_repair':[{'start':4,'end':6,'text':'Fact ID'}],
    }


def _props(public: Path):
    Image.new('RGB',(100,50),'red').save(public/'source.png')
    (public/'voice.wav').write_bytes(b'same-voice-asset')
    def clip(track,start,end,**data):
        return {'clip_id':f'{track}-{start}-{end}','track':track,'timeline_in':start,'timeline_out':end,
                'source_in':0,'source_out':end-start,'metadata':{},**data}
    return {'fps':30,'width':1920,'height':1080,'duration_frames':240,
            'clips':[clip('MEDIA',2,4,asset_id='M1',asset_src='source.png',media_kind='IMAGE'),
                     clip('CHARACTER',4,6,asset_id='C1'),
                     clip('SUBTITLE',4,5,metadata={'text':'Fact '}),
                     clip('SUBTITLE',5,6,metadata={'text':'ID'}),
                     clip('VOICE',0,8,asset_src='voice.wav',asset_id='V1')]}


def test_progression_compiles_to_edt_without_changing_voice_or_duration(tmp_path):
    plan=VisualProgression.model_validate(_plan())
    public=tmp_path/'public';public.mkdir()
    props=_props(public)
    original=copy.deepcopy(props)
    a,b,diagnostics=compile_progression(props,plan,public)
    assert props==original
    assert a['duration_frames']==b['duration_frames']==120
    a_voice=[c for c in a['clips'] if c['track']=='VOICE']
    b_voice=[c for c in b['clips'] if c['track']=='VOICE']
    assert a_voice==b_voice
    assert (a_voice[0]['source_in'],a_voice[0]['source_out'])==(2,6)
    assert any(c['track']=='CHARACTER' for c in a['clips'])
    assert all(c['track']!='CHARACTER' for c in b['clips'])
    assert len([c for c in b['clips'] if c['track']=='MEDIA'])==4
    assert ''.join(c['metadata']['text'] for c in b['clips'] if c['track']=='SUBTITLE')=='Fact ID'
    crop=public/'PREVIEW-VPS-001'/next(c['asset_src'].split('/')[-1]
                   for c in b['clips'] if c['track']=='MEDIA' and c['metadata']['visual_state_id']=='b')
    assert Image.open(crop).size==(60,20)
    assert (public/'PREVIEW-VPS-001'/'c-highlight.svg').is_file()
    assert diagnostics['max_visual_state_hold_a']==2
    assert diagnostics['max_visual_state_hold_b']==1
    assert diagnostics['voice_sha256']


def test_contract_rejects_gaps_unsupported_operations_and_unbound_media(tmp_path):
    data=_plan()
    data['states'][1]['start']=3.1
    with pytest.raises(ValueError,match='VISUAL_STATE_GAP'):
        VisualProgression.model_validate(data)
    data=_plan()
    data['states'][0]['operation']='CAMERA_GRAPH'
    with pytest.raises(ValueError):
        VisualProgression.model_validate(data)
    data=_plan()
    data['states'][0]['media_asset_id']='NOT_REGISTERED'
    plan=VisualProgression.model_validate(data)
    public=tmp_path/'public';public.mkdir()
    props=_props(public)
    with pytest.raises(ValueError,match='EVIDENCE_NOT_IN_SOURCE'):
        compile_progression(props,plan,public)


def test_subtitle_repair_cannot_rewrite_script_and_motion_off_is_pure(tmp_path):
    data=_plan();data['subtitle_repair'][0]['text']='changed words'
    plan=VisualProgression.model_validate(data)
    public=tmp_path/'public';public.mkdir()
    with pytest.raises(ValueError,match='SUBTITLE_REPAIR_TEXT_CHANGED'):
        compile_progression(_props(public),plan,public)
    props={'clips':[{'motion':{'kind':'HOLD','continuous':'SLOW_ZOOM','amount':.03}}]}
    without=motion_off(props)
    assert props['clips'][0]['motion']['continuous']=='SLOW_ZOOM'
    assert without['clips'][0]['motion']=={'kind':'HOLD'}
