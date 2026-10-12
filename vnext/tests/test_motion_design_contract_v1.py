"""MDC-001 semantic phrase, deterministic compiler, and QA tests."""
import copy
import hashlib
import json
from pathlib import Path

from PIL import Image

from vnext.phase2.experimental.director_shotplan_adapter_v1 import create_review
from vnext.phase2.experimental.motion_design_v1 import (
    MotionDesignResolver,
    mechanical_motion_design_qa,
)
from vnext.phase2.experimental.visual_language_v1 import (
    Protagonist,
    Shot,
    ShotBeat,
    ShotPlan,
    VREInput,
    VisualCompiler,
    mechanical_asset_aspect_ratio_qa,
    mechanical_motion_primitive_qa,
)

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "docs/project-brain/creative-spikes/VRE-001-f2-reproduction/evidence/input.json"


def portable_source(tmp_path):
    value = VREInput.model_validate_json(INPUT.read_text()).model_dump()
    for index, asset in enumerate(value["assets"]):
        path = tmp_path / f"asset-{index}{Path(asset['source_path']).suffix or '.bin'}"
        if asset["kind"] in ("EVIDENCE", "CHARACTER"):
            size = (1600, 900) if asset["kind"] == "EVIDENCE" else (600, 900)
            Image.new("RGBA", size, (255, 255, 255, 255)).save(path)
        else:
            path.write_bytes((asset["asset_id"] + "-mdc-fixture").encode())
        asset["source_path"] = path.name
        asset["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return VREInput.model_validate(value)


def four_shot_plan(source):
    def protagonist(primary, supporting=(), background=()):
        return Protagonist(primary=primary, supporting=list(supporting), background=list(background))
    return ShotPlan(
        plan_id="MDC-001-FOUR-SHOT", source_script_id=source.script_id,
        visual_mode="BRAND_BALANCED", beats=[
            ShotBeat(beat_id="MDC-B01", script_segment_id="SEG-02", visual_job="DEMONSTRATE",
                     visual_mode="EVIDENCE_HEAVY", shots=[Shot(
                         shot_id="MDC-S01", shot_type="EVIDENCE_FOCUS", start=0, end=4.5,
                         protagonist=protagonist("EVIDENCE"), evidence_asset_id="EV-RESEARCH",
                         evidence_treatment="FOCUS_REGION", evidence_region_id="import_control",
                         semantic_focus="本地入口", motion_semantic="FOCUS", callout="聚焦入口")]),
            ShotBeat(beat_id="MDC-B02", script_segment_id="SEG-02", visual_job="EXPLAIN",
                     visual_mode="BRAND_BALANCED", shots=[Shot(
                         shot_id="MDC-S02", shot_type="CHARACTER_EXPLAIN", start=4.5, end=9,
                         protagonist=protagonist("XIAOY"), character_role="EXPLAINER",
                         semantic_focus="人工审查边界", motion_semantic="REVEAL", callout="先看边界")]),
            ShotBeat(beat_id="MDC-B03", script_segment_id="SEG-03", visual_job="REACT",
                     visual_mode="BRAND_BALANCED", shots=[Shot(
                         shot_id="MDC-S03", shot_type="CHARACTER_REACTION", start=9, end=13.5,
                         protagonist=protagonist("XIAOY", ["EVIDENCE"]),
                         evidence_asset_id="EV-RESEARCH", evidence_treatment="DETAIL_CROP",
                         evidence_region_id="candidate_rule", character_role="REACTION",
                         semantic_focus="候选不能自动升级", motion_semantic="INTERRUPT", callout="等等。")]),
            ShotBeat(beat_id="MDC-B04", script_segment_id="SEG-04", visual_job="EXPLAIN",
                     visual_mode="BRAND_BALANCED", shots=[Shot(
                         shot_id="MDC-S04", shot_type="RELATION_EXPLAIN", start=13.5,
                         end=source.duration, protagonist=protagonist("DIAGRAM", background=["EVIDENCE"]),
                         evidence_asset_id="EV-RESEARCH", evidence_treatment="RELATION",
                         evidence_region_id="source_rule", semantic_focus="来源与事实绑定",
                         motion_semantic="CONNECT", callout="SOURCE ↔ FACT")]),
        ])


def compile_pair(tmp_path):
    source = portable_source(tmp_path)
    plan = four_shot_plan(source)
    design = MotionDesignResolver().resolve(plan)
    compiler = VisualCompiler(tmp_path, tmp_path / "public")
    old, _ = compiler.compile(source, plan, "PREVIEW-MDC-PAIR")
    new, diagnostics = compiler.compile(source, plan, "PREVIEW-MDC-PAIR", design)
    return source, plan, design, old, new, diagnostics


def test_four_motion_phrases_are_renderer_neutral(tmp_path):
    source = portable_source(tmp_path)
    plan = four_shot_plan(source)
    design = MotionDesignResolver().resolve(plan)
    assert [phrase.intent for phrase in design.phrases] == [
        "FOCUS", "EXPLAIN", "IMPACT_WARN", "CONNECT"]
    encoded = json.dumps(design.model_dump(), sort_keys=True)
    for forbidden in ("duration_ms", "duration_frames", "scale", "translate", "px",
                      "cubicBezier", "stiffness", "CSS"):
        assert forbidden not in encoded


def test_same_semantic_input_compiles_identically(tmp_path):
    source, plan, design, _, new_a, diagnostics_a = compile_pair(tmp_path)
    compiler = VisualCompiler(tmp_path, tmp_path / "public-second")
    new_b, diagnostics_b = compiler.compile(source, plan, "PREVIEW-MDC-SECOND", design)
    assert diagnostics_a["compiled_motion_artifact"]["compiled_motion_sha256"] == (
        diagnostics_b["compiled_motion_artifact"]["compiled_motion_sha256"])
    a = [(clip["clip_id"], clip["metadata"].get("motion_design")) for clip in new_a["clips"]]
    b = [(clip["clip_id"], clip["metadata"].get("motion_design")) for clip in new_b["clips"]]
    assert a == b


def test_motion_design_is_the_only_ab_variable(tmp_path):
    _, plan, _, old, new, _ = compile_pair(tmp_path)
    original_plan = plan.model_dump()
    old_clean = copy.deepcopy(old)
    new_clean = copy.deepcopy(new)
    new_clean.pop("motion_design_qa")
    new_clean.pop("compiled_motion_artifact")
    for clip in new_clean["clips"]:
        clip["metadata"].pop("motion_design", None)
    assert old_clean == new_clean
    assert plan.model_dump() == original_plan


def test_primary_dominance_and_real_secondary_offsets(tmp_path):
    _, plan, design, _, new, diagnostics = compile_pair(tmp_path)
    assert diagnostics["motion_design_qa"]["verdict"] == "PASS"
    for shot in [shot for beat in plan.beats for shot in beat.shots]:
        clips = [clip for clip in new["clips"] if clip.get("ir_node_id") == shot.shot_id and
                 clip["metadata"].get("motion_design")]
        assert sum(clip["metadata"]["motion_design"]["motion_role"] == "PRIMARY"
                   for clip in clips) == 1
        assert all(clip["metadata"]["motion_design"]["phase_offset_frames"] > 0
                   for clip in clips if
                   clip["metadata"]["motion_design"]["motion_role"] == "SECONDARY")
    assert len(design.phrases) == 4


def test_storyboard_gate_includes_motion_design_qa(tmp_path):
    _, plan, _, _, new, _ = compile_pair(tmp_path)
    review = create_review(plan, props=new)
    assert review.mechanical_qa["verdict"] == "PASS"
    assert review.mechanical_qa["checks"]["motion_design"]["verdict"] == "PASS"


def test_motion_design_mechanical_error_codes(tmp_path):
    _, plan, design, _, new, _ = compile_pair(tmp_path)
    primitive = mechanical_motion_primitive_qa(new)
    aspect = mechanical_asset_aspect_ratio_qa(new)

    missing = copy.deepcopy(new)
    for clip in missing["clips"]:
        if clip.get("ir_node_id") == "MDC-S01":
            clip["metadata"].pop("motion_design", None)
    report = mechanical_motion_design_qa(missing, design, plan, primitive, aspect)
    assert "MOTION_PRIMARY_MISSING" in {issue["code"] for issue in report["issues"]}

    conflict = copy.deepcopy(new)
    shot_clips = [clip for clip in conflict["clips"] if clip.get("ir_node_id") == "MDC-S01" and
                  clip["metadata"].get("motion_design")]
    shot_clips[1]["metadata"]["motion_design"]["motion_role"] = "PRIMARY"
    report = mechanical_motion_design_qa(conflict, design, plan, primitive, aspect)
    assert "MOTION_PRIMARY_CONFLICT" in {issue["code"] for issue in report["issues"]}

    no_offset = copy.deepcopy(new)
    secondary = next(clip for clip in no_offset["clips"] if
                     clip["metadata"].get("motion_design", {}).get("motion_role") == "SECONDARY")
    secondary["metadata"]["motion_design"]["phase_offset_frames"] = 0
    report = mechanical_motion_design_qa(no_offset, design, plan, primitive, aspect)
    assert "SECONDARY_RESPONSE_WITHOUT_OFFSET" in {issue["code"] for issue in report["issues"]}

    invalid_design = design.model_copy(deep=True)
    invalid_design.phrases[0].phases.reverse()
    report = mechanical_motion_design_qa(new, invalid_design, plan, primitive, aspect)
    assert "MOTION_PHASE_INVALID_ORDER" in {issue["code"] for issue in report["issues"]}

    report = mechanical_motion_design_qa(new, design, plan,
        {"verdict": "FAIL", "issues": [{"code": "MOTION_PRIMITIVE_UNKNOWN"}]}, aspect)
    assert "MOTION_DESIGN_UNSUPPORTED_PRIMITIVE" in {issue["code"] for issue in report["issues"]}

    report = mechanical_motion_design_qa(new, design, plan, primitive,
        {"verdict": "FAIL", "issues": [{"code": "ASSET_ASPECT_RATIO_DISTORTED"}]})
    assert "MOTION_DESIGN_ASPECT_RATIO_VIOLATION" in {issue["code"] for issue in report["issues"]}


def test_motion_design_keeps_registered_asset_scale_uniform(tmp_path):
    _, _, _, _, new, diagnostics = compile_pair(tmp_path)
    assert diagnostics["asset_aspect_ratio_qa"]["verdict"] == "PASS"
    for clip in new["clips"]:
        metadata = clip["metadata"]
        if metadata.get("geometry_kind") == "REGISTERED_ASSET":
            transform = metadata["media_transform"]
            assert transform["scale_x"] == transform["scale_y"]
            motion = metadata.get("motion_design")
            if motion:
                encoded = json.dumps(motion, sort_keys=True)
                assert "scale_x" not in encoded and "scale_y" not in encoded


def test_renderer_consumes_compiled_motion_without_semantic_policy():
    renderer = (ROOT / "vnext/renderers/remotion/project/src/vre001/Renderer.tsx").read_text()
    assert "meta.motion_design" in renderer
    assert "sampleKeyframes" in renderer
    for forbidden in ("IMPACT_WARN", "CONNECT'", "EVIDENCE_FOCUS", "CHARACTER_REACTION"):
        assert forbidden not in renderer
