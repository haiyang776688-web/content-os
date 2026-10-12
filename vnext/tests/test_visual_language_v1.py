"""VRE-001 contract and compiler tests."""
import copy
import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image

from vnext.phase2.experimental.visual_language_v1 import (
    ShotPlan, VREInput, VisualCompiler, build_f2_shot_plan,
)

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT/'docs/project-brain/creative-spikes/VRE-001-f2-reproduction/evidence/input.json'


def source():
    return VREInput.model_validate_json(INPUT.read_text())


def portable_source(tmp_path):
    """Use synthetic registered files so contract tests do not commit private voice/font inputs."""
    value=source().model_dump()
    for index,asset in enumerate(value['assets']):
        path=tmp_path/f'input-{index}{Path(asset["source_path"]).suffix or ".bin"}'
        if asset['kind'] in ('EVIDENCE','CHARACTER'):
            size=(1600,900) if asset['kind']=='EVIDENCE' else (600,900)
            Image.new('RGBA',size,(255,255,255,255)).save(path)
        else:
            path.write_bytes((asset['asset_id']+'-fixture').encode())
        asset['source_path']=path.name
        asset['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    return VREInput.model_validate(value)


def test_f2_plan_is_semantic_complete_and_has_no_geometry():
    plan = build_f2_shot_plan(source())
    value = plan.model_dump()
    assert plan.visual_mode == 'BRAND_BALANCED'
    assert len([shot for beat in plan.beats for shot in beat.shots]) == 10
    assert {beat.visual_job for beat in plan.beats} == {
        'PROVE','DEMONSTRATE','EXPLAIN','REACT','WARN','TRANSITION','SUMMARIZE'}
    forbidden = {'x','y','width','height','pixels','font_size','position','scale','crop'}
    def visit(item):
        if isinstance(item, dict):
            assert not (set(item) & forbidden)
            for child in item.values(): visit(child)
        elif isinstance(item, list):
            for child in item: visit(child)
    visit(value)


def test_visual_job_and_role_are_enforced():
    value = build_f2_shot_plan(source()).model_dump()
    value['beats'][0]['visual_job'] = 'PROVE'
    with pytest.raises(ValueError, match='SHOT_TYPE_NOT_ALLOWED'):
        ShotPlan.model_validate(value)
    value = build_f2_shot_plan(source()).model_dump()
    value['beats'][3]['shots'][0]['character_role'] = 'NONE'
    with pytest.raises(ValueError, match='PRIMARY_XIAOY_ROLE_REQUIRED'):
        ShotPlan.model_validate(value)


def test_compiler_consumes_plan_fields_and_emits_one_primary(tmp_path):
    frozen = portable_source(tmp_path); plan = build_f2_shot_plan(frozen)
    compiler = VisualCompiler(tmp_path, tmp_path/'public')
    props, diagnostics = compiler.compile(frozen, plan)
    assert diagnostics['primary_contract_pass']
    assert diagnostics['shot_count'] == 10
    assert diagnostics['visual_jobs']['PROVE'] == 2
    assert diagnostics['character_roles'] == {
        'GUIDE':1,'REACTION':1,'RESPONSIBILITY':1,'TRANSITION':1,'SUMMARY':1}
    assert {c['motion']['semantic'] for c in props['clips'] if c['motion']} == {
        'FOCUS','REVEAL','FOLLOW','INTERRUPT','RETURN','CONNECT','SETTLE'}
    evidence = [c for c in props['clips'] if c['metadata'].get('layer_kind')=='EVIDENCE']
    assert all(c['metadata']['evidence_treatment'] for c in evidence)
    assert all(c['metadata']['evidence_source_sha256'] for c in evidence)
    assert all(c['edit_source']=='VISUAL_COMPILER_V1' for c in evidence)


def test_mode_changes_compiler_geometry_not_semantic_plan(tmp_path):
    frozen=portable_source(tmp_path); balanced=build_f2_shot_plan(frozen)
    heavy=ShotPlan.model_validate({**balanced.model_dump(),'plan_id':'HEAVY','visual_mode':'EVIDENCE_HEAVY'})
    compiler=VisualCompiler(tmp_path,tmp_path/'public')
    a,_=compiler.compile(frozen,balanced,'PREVIEW-A')
    b,_=compiler.compile(frozen,heavy,'PREVIEW-B')
    def evidence_width(props, shot_id):
        return next(c['metadata']['box']['width'] for c in props['clips']
                    if c.get('ir_node_id')==shot_id and c['metadata'].get('layer_kind')=='EVIDENCE')
    # Mode changes the context recipe while the semantic ShotPlan remains geometry-free.
    context = copy.deepcopy(balanced.model_dump())
    context['beats'][1]['shots'][0]['shot_type']='EVIDENCE_CONTEXT'
    context['beats'][1]['visual_job']='DEMONSTRATE'
    context_plan=ShotPlan.model_validate(context)
    context_heavy=ShotPlan.model_validate({**context_plan.model_dump(),'visual_mode':'EVIDENCE_HEAVY'})
    c,_=compiler.compile(frozen,context_plan,'PREVIEW-C')
    d,_=compiler.compile(frozen,context_heavy,'PREVIEW-D')
    assert evidence_width(c,'VRE-S02') < evidence_width(d,'VRE-S02')
    assert a['duration_frames']==b['duration_frames']==574


def test_frozen_script_voice_captions_and_renderer_policy_boundary(tmp_path):
    frozen=portable_source(tmp_path); props,diagnostics=VisualCompiler(tmp_path,tmp_path/'public').compile(
        frozen,build_f2_shot_plan(frozen))
    assert ''.join(c['metadata']['text'] for c in props['clips'] if c['track']=='SUBTITLE') == ''.join(c.text for c in frozen.captions)
    voice=next(a for a in frozen.assets if a.kind=='VOICE')
    assert hashlib.sha256((tmp_path/voice.source_path).read_bytes()).hexdigest()==diagnostics['voice_sha256']
    renderer=(ROOT/'vnext/renderers/remotion/project/src/vre001/Renderer.tsx').read_text()
    for hidden_policy in ('CHARACTER_INTRO','EVIDENCE_FOCUS','BRAND_BALANCED','visual_job'):
        assert hidden_policy not in renderer
