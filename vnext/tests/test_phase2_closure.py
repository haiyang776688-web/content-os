"""Closure contracts plus real browser evidence (examples/phase2_closure).
Temporary test projects never touch the existing diagnostic data.
"""
import copy
import json
import re
import subprocess
from pathlib import Path
import pytest
from vnext.tests.test_phase2 import env
from vnext.renderers.remotion.resolver import CompositionResolver
from vnext.renderers.remotion.adapter import RemotionAdapter
from vnext.phase2.production import CommandBus
from vnext.phase2.stages import StageCache
from vnext.storage.store import canonical, SINGLE_WRITERS
from vnext.contracts import Capability,Role
ROOT=Path(__file__).resolve().parents[2]
DICTS={l:json.loads((ROOT/'vnext/i18n'/f'{l}.json').read_text()) for l in ('zh-CN','en-US')}
REG=json.loads((ROOT/'vnext/i18n/registry.json').read_text())


def frozen(store,pid):
    return canonical(dict(project=store.get_project(pid).model_dump(),artifacts=store.artifacts(pid),
        stages=StageCache(store).states(pid),logs=store.logs(pid)))


def resolver(env,tmp_path):
    store,pid,*_=env
    return CompositionResolver(tmp_path/'renderer',store),pid,store.get_project(pid).timeline_artifact_id


def js(expression):
    # Execute the actual presentation module, not a test implementation.
    script=f"import {{present,brand,errorText,translate}} from {json.dumps((ROOT/'vnext/apps/workbench/i18n.js').as_uri())};const dicts={json.dumps(DICTS,ensure_ascii=False)};"+expression
    result=subprocess.run(['node','--input-type=module','-e',script],capture_output=True,text=True,check=True)
    return json.loads(result.stdout)


def test_playhead_change_updates_preview(env,tmp_path):
    r,pid,aid=resolver(env,tmp_path)
    before=r.frame(pid,aid,0);after=r.frame(pid,aid,60)
    assert before['seconds']==0 and after['seconds']==2
    assert before['fingerprint']==after['fingerprint']


def test_preview_does_not_mutate_edt(env,tmp_path):
    store,pid,*_=env;before=frozen(store,pid)
    r,_,aid=resolver(env,tmp_path);r.frame(pid,aid,120)
    assert frozen(store,pid)==before


def test_timeline_edit_updates_preview(env,tmp_path):
    store,pid,*_=env;r,_,aid=resolver(env,tmp_path);before=r.resolve(pid,aid)
    clip=before['props']['clips'][0]
    edited=CommandBus(store).execute(pid,'EDT','TRANSFORM',{'clip_id':clip['clip_id'],'position':{'x':.2,'y':.3}})
    after=r.resolve(pid,edited['artifact_id'])
    assert after['fingerprint']!=before['fingerprint']
    assert after['props']['clips'][0]['position']=={'x':.2,'y':.3}


def test_typography_edit_updates_preview(env,tmp_path):
    store,pid,*_=env;r,_,aid=resolver(env,tmp_path);before=r.resolve(pid,aid)
    CommandBus(store).execute(pid,'TYPOGRAPHY_PROFILE','SET_FONT_SIZE',{'role':'KEYWORD','value':82})
    after=r.resolve(pid,aid)
    assert after['props']['typography']['roles']['KEYWORD']['size']==82
    assert before['fingerprint']!=after['fingerprint'] and after['issues']==['STALE_EDT']
    rebound=CommandBus(store).execute(pid,'EDT','REFRESH_DEPENDENCIES',{})
    assert r.resolve(pid,rebound['artifact_id'])['issues']==[]
    assert store.get_artifact(aid)['payload']['clips']==rebound['payload']['clips']


def test_media_rebind_updates_preview(env,tmp_path):
    from vnext.media.library.service import MediaLibrary
    store,pid,*_=env;r,_,aid=resolver(env,tmp_path)
    files=[]
    for color in ('red','blue'):
        path=tmp_path/(color+'.png')
        subprocess.run(['ffmpeg','-loglevel','error','-f','lavfi','-i',f'color={color}:s=64x48','-frames:v','1',str(path)],check=True)
        files.append(MediaLibrary(store).register(pid,path,'IMAGE','USER','LOCAL_ONLY'))
    edt=CommandBus(store).execute(pid,'EDT','ADD',{'track':'MEDIA','asset_id':files[0].asset_id,'timeline_in':0,'timeline_out':3,'source_in':0,'source_out':3})
    before=r.resolve(pid,edt['artifact_id']);clip=before['props']['clips'][-1]
    edt=CommandBus(store).execute(pid,'EDT','REPLACE',{'clip_id':clip['clip_id'],'asset_id':files[1].asset_id})
    after=r.resolve(pid,edt['artifact_id'])
    assert before['fingerprint']!=after['fingerprint']
    assert files[1].asset_id in after['props']['clips'][-1]['asset_src']


def test_preview_and_render_share_composition_resolver(env,tmp_path):
    store,pid,*_=env;r,_,aid=resolver(env,tmp_path)
    resolved=r.resolve(pid,aid);prepared=RemotionAdapter(tmp_path/'renderer',store).prepare(pid,aid)
    assert prepared['props']==resolved['props']
    assert prepared['composition_fingerprint']==resolved['fingerprint']
    # Both entry points import one component. There is no duplicated clip layout.
    project=ROOT/'vnext/renderers/remotion/project/src'
    assert "from './Composition'" in (project/'index.tsx').read_text()
    assert "from './Composition'" in (project/'ProgramMonitor.tsx').read_text()


def test_preview_scrub_does_not_dirty_project(env,tmp_path):
    store,pid,*_=env;before=frozen(store,pid);r,_,aid=resolver(env,tmp_path)
    for frame in (0,1,17,150,299,10000):r.frame(pid,aid,frame)
    assert frozen(store,pid)==before


def test_selected_clip_syncs_inspector(env,tmp_path):
    r,pid,aid=resolver(env,tmp_path);clip=r.resolve(pid,aid)['props']['clips'][0]
    frame=r.frame(pid,aid,selected_clip_id=clip['clip_id'])
    assert frame['selected_clip']==clip
    assert r.frame(pid,aid,selected_clip_id='absent')['selected_clip'] is None


def test_safe_area_is_projection_only(env,tmp_path):
    store,pid,*_=env;before=frozen(store,pid);r,_,aid=resolver(env,tmp_path)
    off=r.frame(pid,aid,safe_area=False);on=r.frame(pid,aid,safe_area=True)
    assert on['safe_area'] and not off['safe_area']
    assert on['props']==off['props'] and on['fingerprint']==off['fingerprint']
    assert frozen(store,pid)==before


def test_preview_time_matches_edt_timebase(env,tmp_path):
    r,pid,aid=resolver(env,tmp_path)
    for frame in (1,29,100,299):
        value=r.frame(pid,aid,frame)
        assert value['seconds']==frame/value['props']['fps']
    assert r.frame(pid,aid,300)['frame']==299


def test_zh_cn_has_no_untranslated_known_ui_tokens():
    assert set(DICTS['zh-CN'])==set(REG['keys'])==set(DICTS['en-US'])
    for token in REG['canonical_tokens']:assert DICTS['zh-CN']['enum.'+token]!=token
    assert {c.value for c in Capability}|{r.value for r in Role}|set(SINGLE_WRITERS)<=set(REG['canonical_tokens'])


def test_en_us_has_no_chinese_ui_literals():
    assert not [k for k,v in DICTS['en-US'].items() if re.search('[\u4e00-\u9fff]',v)]


def test_locale_switch_does_not_mutate_project(env):
    store,pid,*_=env;before=frozen(store,pid)
    # This invokes only presentation code and leaves all persisted production data identical.
    js("const app={dict:dicts['zh-CN']};app.dict=dicts['en-US'];console.log(JSON.stringify(present(app,'SCRIPT_LOCKED')));")
    assert frozen(store,pid)==before


def test_locale_switch_does_not_dirty_stage(env):
    store,pid,*_=env;before=StageCache(store).states(pid)
    js("for(const locale of Object.keys(dicts)){const app={dict:dicts[locale]};for(const status of ['DIRTY','STALE','READY'])present(app,status)}console.log('true');")
    assert StageCache(store).states(pid)==before
    code=(ROOT/'vnext/apps/workbench/workbench.js').read_text().split('app.setLocale=async()=>')[1].split('function stageView')[0]
    assert "PATCH" not in code and 'patchConfig' not in code and '/api/projects/' not in code


def test_enum_values_remain_canonical():
    assert js("const app={dict:dicts['zh-CN']};const input={status:'READY',role:'RESEARCH',capability:'TEXT'};Object.values(input).map(v=>present(app,v));console.log(JSON.stringify(input));")==dict(status='READY',role='RESEARCH',capability='TEXT')


def test_dynamic_status_is_localized():
    assert js("console.log(JSON.stringify(Object.keys(dicts).map(l=>present({dict:dicts[l]},'PASS_WITH_RISK'))));")==['附风险通过','Pass with risk']


def test_inspector_is_fully_localized():
    assert js("const app={dict:dicts['zh-CN']};console.log(JSON.stringify([present(app,'RESEARCH'),translate(app,'inspector.capabilities'),present(app,'STRUCTURED_OUTPUT'),present(app,'TOOL_CALLING'),present(app,'REASONING'),present(app,'RESEARCH_V1')]));")[0:5]==['研究','能力','结构化输出','工具调用','推理']


def test_error_and_warning_are_localized():
    assert js("const app={dict:dicts['zh-CN']};console.log(JSON.stringify([errorText(app,'TIMELINE_STALE'),errorText(app,'FONT_GLYPH_MISSING'),present(app,'WARNING')]));")==['时间线依赖已过期，请先同步依赖或返回对应部门。','所选字体缺字','警告']


def test_timeline_preview_controls_are_localized():
    keys=['preview.monitor','preview.play','preview.pause','preview.previous','preview.next','preview.fit','preview.safe','preview.scrub','preview.clock']
    assert all(k in DICTS[l] for k in keys for l in DICTS)
    assert all(DICTS['zh-CN'][k]!=DICTS['en-US'][k] for k in keys)


def test_model_brand_names_are_not_translated():
    names=REG['preserved_brands']
    assert js(f"console.log(JSON.stringify({json.dumps(names)}.map(v=>brand({{dict:dicts['zh-CN']}},v))));")==names


def test_refresh_pins_cannot_accept_obsolete_script(env):
    store,pid,k,script,*_=env
    k.bound_script(pid,{'text':'Alpha has 3 items','segments':[{'segment_id':'SEG1','text':'Alpha has 3 items','claim':True,'fact_ids':['F1']}]})
    with pytest.raises(ValueError):CommandBus(store).execute(pid,'EDT','REFRESH_DEPENDENCIES',{})


def test_unified_command_http_uses_public_arguments_field(env):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from vnext.phase2.api import attach
    from vnext.core.runtime import Runtime
    store,pid,*_=env;app=FastAPI();attach(app,store,ROOT,Runtime(store));client=TestClient(app)
    result=client.post(f'/api/projects/{pid}/phase2/commands',json={'target':'TYPOGRAPHY_PROFILE','operation':'SET_FONT_SIZE','arguments':{'role':'TITLE','value':72}})
    assert result.status_code==200,result.text
    assert result.json()['payload']['roles']['TITLE']['size']==72
    refused=client.post(f'/api/projects/{pid}/phase2/commands',json={'target':'TYPOGRAPHY_PROFILE','operation':'SET_FONT_SIZE','arguments':{'role':'TITLE','value':80},'actor_type':'AGENT','actor':'DIRECTOR'})
    assert refused.status_code==403


def test_visual_pattern_rebuild_retains_audio_clock(env,tmp_path):
    store,pid,*_=env
    CommandBus(store).execute(pid,'EDT','ADD',{'track':'SFX','timeline_in':1,'timeline_out':2,'source_in':0,'source_out':1})
    old=store.latest(pid,'EDT');audio=old['payload']['clips'][-1]
    CommandBus(store).execute(pid,'DIRECTOR_IR','SET_BEAT',{'beat_id':'B1','changes':{'pattern_id':'CHARACTER_EXPLAIN_KEYWORD','slots':{'keyword':'Alpha'}}})
    with pytest.raises(ValueError,match='HUMAN_EDITS_PRESENT'):
        CommandBus(store).execute(pid,'EDT','GENERATE_PRESERVING_AUDIO',{},expected_revision=old['artifact_id'])
    rebuilt=CommandBus(store).execute(pid,'EDT','GENERATE_PRESERVING_AUDIO',
        {'discard_human_edits':True},expected_revision=old['artifact_id'])
    matching=[c for c in rebuilt['payload']['clips'] if c['track']=='SFX'][0]
    for key in ('source_in','source_out','timeline_in','timeline_out'):assert matching[key]==audio[key]
    assert rebuilt['payload']['clips'][0]['pattern_id']=='CHARACTER_EXPLAIN_KEYWORD'
