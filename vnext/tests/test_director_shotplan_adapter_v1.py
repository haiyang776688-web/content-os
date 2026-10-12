"""VLA-001 adapter, semantic review and pre-render gate tests."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import pytest
from PIL import Image

from vnext.phase2.experimental.director_shotplan_adapter_v1 import (
    DirectorShotPlanAdapter,
    DirectorShotPlanInput,
    ReviewFrame,
    ShotPlanEdit,
    apply_review_edits,
    approve_review,
    attach_compiler_review_data,
    create_review,
    reject_review,
    require_approved,
    review_summary,
    write_review_html,
)
from vnext.phase2.experimental.visual_language_v1 import (
    ShotPlan,
    VisualCompiler,
    mechanical_asset_aspect_ratio_qa,
)


def _file(tmp_path: Path, name: str) -> dict:
    path = tmp_path / name
    if path.suffix == ".png":
        size = (1600, 900) if "board" in name else (600, 900)
        Image.new("RGBA", size, (255, 255, 255, 255)).save(path)
    else:
        path.write_bytes(("fixture:" + name).encode())
    return {"source_path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def fixture(tmp_path: Path) -> DirectorShotPlanInput:
    assets = [
        {"asset_id": "EV-BOARD", "kind": "EVIDENCE", **_file(tmp_path, "board.png"), "regions": {
            "semantic_fields": {"x": .1, "y": .1, "width": .5, "height": .4,
                                "label": "semantic fields", "keywords": ["fields", "职责"]},
            "gate_controls": {"x": .2, "y": .55, "width": .55, "height": .3,
                              "label": "gate controls", "keywords": ["modify", "reject", "拒绝"]},
            "tall_panel": {"x": .72, "y": .1, "width": .18, "height": .72,
                           "label": "tall panel", "keywords": ["narrow", "panel"]},
        }},
        {"asset_id": "CH-POINT", "kind": "CHARACTER", **_file(tmp_path, "point.png")},
        {"asset_id": "CH-SERIOUS", "kind": "CHARACTER", **_file(tmp_path, "serious.png")},
        {"asset_id": "CH-SURPRISE", "kind": "CHARACTER", **_file(tmp_path, "surprise.png")},
        {"asset_id": "FONT", "kind": "FONT", **_file(tmp_path, "font.otf")},
    ]
    segments = [
        {"segment_id": "SEG1", "text": "先看职责", "fact_ids": []},
        {"segment_id": "SEG2", "text": "界面展示语义字段", "fact_ids": ["F1"]},
        {"segment_id": "SEG3", "text": "字段让判断有依据", "fact_ids": ["F1"]},
        {"segment_id": "SEG4", "text": "不能等到渲染后", "fact_ids": ["F2"]},
        {"segment_id": "SEG5", "text": "先审查再渲染", "fact_ids": ["F2"]},
    ]
    source = {"script_id": "SCRIPT-NEW", "script_sha256": "a" * 64, "segments": segments,
              "captions": [{"text": segment["text"], "start": i * 4, "end": (i + 1) * 4}
                           for i, segment in enumerate(segments)],
              "assets": assets, "duration": 20, "fps": 30, "width": 1920, "height": 1080}
    beats = [
        {"beat_id": "B1", "scene_id": "SC1", "script_segment_id": "SEG1",
         "purpose": "Transition into review", "visual_focus": "分镜职责", "visual_form": "KEYWORD",
         "pattern_id": "CHARACTER_EXPLAIN_KEYWORD", "keyword": "先看职责", "timing_intent": 4,
         "slots": {"keyword": "先看职责"}},
        {"beat_id": "B2", "scene_id": "SC1", "script_segment_id": "SEG2",
         "purpose": "Demonstrate screenshot evidence", "visual_focus": "semantic fields", "visual_form": "SCREEN",
         "pattern_id": "SCREEN_DETAIL", "keyword": "字段", "timing_intent": 4,
         "slots": {"media_asset_id": "EV-BOARD"}},
        {"beat_id": "B3", "scene_id": "SC1", "script_segment_id": "SEG3",
         "purpose": "Prove the visible responsibility boundary", "visual_focus": "职责字段", "visual_form": "SCREEN",
         "pattern_id": "SCREEN_DETAIL", "keyword": "有依据", "timing_intent": 4,
         "slots": {"media_asset_id": "EV-BOARD"}},
        {"beat_id": "B4", "scene_id": "SC1", "script_segment_id": "SEG4",
         "purpose": "Warn about expensive late correction", "visual_focus": "不能等渲染", "visual_form": "REACTION",
         "pattern_id": "CHARACTER_REACTION_MEDIA", "keyword": "别等成片", "timing_intent": 4,
         "slots": {"media_asset_id": "EV-BOARD"}},
        {"beat_id": "B5", "scene_id": "SC1", "script_segment_id": "SEG5",
         "purpose": "Summary", "visual_focus": "先审查再渲染", "visual_form": "SUMMARY",
         "pattern_id": "THREE_POINT_SUMMARY", "keyword": "先审再渲", "timing_intent": 4,
         "slots": {"points": ["看懂", "修改", "批准"]}},
    ]
    ir = {"schema_version": 2, "script_artifact_id": "SCRIPT-NEW", "scenes": [{
        "scene_id": "SC1", "purpose": "Explain storyboard review", "script_range": [s["segment_id"] for s in segments],
        "narrative_function": "EXPLAIN", "retention_goal": "VALUE", "estimated_duration": 20,
        "beat_ids": [beat["beat_id"] for beat in beats]}], "beats": beats, "transitions": []}
    return DirectorShotPlanInput.model_validate({"source": source, "director_ir": ir, "facts": [
        {"fact_id": "F1", "statement": "The board exposes semantic fields", "evidence_asset_ids": ["EV-BOARD"]},
        {"fact_id": "F2", "statement": "The board exposes gate controls", "evidence_asset_ids": ["EV-BOARD"]},
    ]})


def test_adapter_auto_decides_semantics_without_geometry(tmp_path):
    item = fixture(tmp_path)
    plan = DirectorShotPlanAdapter().adapt(item, "VLA-TEST")
    assert [beat.visual_job for beat in plan.beats] == [
        "TRANSITION", "DEMONSTRATE", "PROVE", "WARN", "SUMMARIZE"]
    assert {beat.visual_mode for beat in plan.beats} == {"BRAND_BALANCED", "EVIDENCE_HEAVY"}
    assert [beat.shots[0].protagonist.primary for beat in plan.beats] == [
        "XIAOY", "EVIDENCE", "EVIDENCE", "XIAOY", "EVIDENCE"]
    assert plan.beats[1].shots[0].evidence_region_id == "semantic_fields"
    assert plan.beats[3].shots[0].character_role == "RESPONSIBILITY"
    forbidden = {"x", "y", "width", "height", "crop", "font_size", "css", "position",
                 "scale", "scale_x", "scale_y"}
    def visit(value):
        if isinstance(value, dict):
            assert not set(value) & forbidden
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(plan.model_dump())


def test_compiler_consumes_adapter_output_and_owns_geometry(tmp_path):
    item = fixture(tmp_path)
    plan = DirectorShotPlanAdapter().adapt(item, "VLA-TEST")
    props, diagnostics = VisualCompiler(tmp_path, tmp_path / "public").compile(
        item.source, plan, "PREVIEW-VLA-TEST")
    assert diagnostics["primary_contract_pass"]
    assert diagnostics["visual_modes"] == {"BRAND_BALANCED": 3, "EVIDENCE_HEAVY": 2}
    layers = [clip for clip in props["clips"] if clip.get("ir_node_id")]
    assert all("position" in clip and "box" in clip["metadata"] for clip in layers)
    assert {clip["metadata"]["visual_mode"] for clip in layers} == {
        "BRAND_BALANCED", "EVIDENCE_HEAVY"}
    assert {clip["metadata"]["script_segment_id"] for clip in layers} == {
        "SEG1", "SEG2", "SEG3", "SEG4", "SEG5"}
    assert props["shot_plan_id"] == plan.plan_id
    assert props["shot_plan_schema_version"] == plan.schema_version
    assert props["source_script_id"] == item.source.script_id
    assert diagnostics["field_consumers"]["ShotBeat.visual_mode"].startswith("VisualCompiler")
    assert all(clip["edit_source"] == "VISUAL_COMPILER_V1" for clip in layers)


def test_storyboard_review_can_edit_reject_and_gate_render(tmp_path):
    item = fixture(tmp_path)
    plan = DirectorShotPlanAdapter().adapt(item, "VLA-TEST")
    frames = [ReviewFrame(shot_id=beat.shots[0].shot_id, path=f"frames/{beat.beat_id}.png",
                          time=(beat.shots[0].start + beat.shots[0].end) / 2) for beat in plan.beats]
    props, _ = VisualCompiler(tmp_path, tmp_path / "public-review").compile(
        item.source, plan, "PREVIEW-VLA-REVIEW")
    review = create_review(plan, frames, props)
    rejected = reject_review(plan, review, "SPIKE_REVIEWER", "Evidence treatment is semantically wrong")
    with pytest.raises(ValueError, match="STORYBOARD_APPROVAL_REQUIRED"):
        require_approved(plan, rejected)
    revised, review = apply_review_edits(plan, review, [
        ShotPlanEdit(beat_id="B3", changes={"visual_job": "DEMONSTRATE"},
                     reason="Narration demonstrates how the field works rather than proving a claim."),
        ShotPlanEdit(beat_id="B3", shot_id="VLA-TEST-S03",
                     changes={"shot_type": "EVIDENCE_FOCUS", "evidence_treatment": "FOCUS_REGION",
                              "motion_semantic": "FOLLOW"},
                     reason="Follow the named field instead of applying a proof highlight."),
    ])
    props, _ = VisualCompiler(tmp_path, tmp_path / "public-review-revised").compile(
        item.source, revised, "PREVIEW-VLA-REVIEW-REVISED")
    review = attach_compiler_review_data(review, props)
    approved = approve_review(revised, review, "SPIKE_REVIEWER")
    require_approved(revised, approved)
    summary = review_summary(item.source, revised, approved)
    assert summary["rows"][0].keys() >= {"narration", "visual_job", "visual_mode", "shot_type", "primary",
                                         "evidence_asset", "evidence_region", "evidence_treatment",
                                         "character_role", "motion_semantic", "representative_frame"}
    html_path = tmp_path / "review.html"
    write_review_html(item.source, revised, approved, html_path)
    page = html_path.read_text()
    assert "拒绝" in page and "批准" in page and "Visual Job" in page and "PRIMARY" in page


def test_renderer_does_not_reintroduce_editorial_policy():
    renderer = (Path(__file__).resolve().parents[2] /
                "vnext/renderers/remotion/project/src/vre001/Renderer.tsx").read_text()
    for hidden_policy in ("PROVE", "DEMONSTRATE", "BRAND_BALANCED", "EVIDENCE_HEAVY",
                          "visual_job", "shot_type", "evidence_treatment"):
        assert hidden_policy not in renderer


def _evidence_clip(props, shot_id):
    return next(clip for clip in props["clips"] if clip.get("ir_node_id") == shot_id and
                clip["metadata"].get("layer_kind") == "EVIDENCE")


def test_no_source_region_uses_contain_and_preserves_ratio(tmp_path):
    item = fixture(tmp_path)
    value = DirectorShotPlanAdapter().adapt(item, "VLA-ASPECT-A").model_dump()
    shot = value["beats"][1]["shots"][0]
    shot["evidence_region_id"] = None
    shot["evidence_treatment"] = "FULL_CONTEXT"
    plan = ShotPlan.model_validate(value)
    props, diagnostics = VisualCompiler(tmp_path, tmp_path / "public-a").compile(
        item.source, plan, "PREVIEW-ASPECT-A")
    clip = _evidence_clip(props, shot["shot_id"])
    transform = clip["metadata"]["media_transform"]
    assert clip["metadata"]["fit_mode"] == "CONTAIN"
    assert transform["scale_x"] == pytest.approx(transform["scale_y"])
    assert diagnostics["asset_aspect_ratio_qa"]["verdict"] == "PASS"


def test_wide_region_uses_focus_crop_with_uniform_scale(tmp_path):
    item = fixture(tmp_path)
    value = DirectorShotPlanAdapter().adapt(item, "VLA-ASPECT-B").model_dump()
    shot = value["beats"][1]["shots"][0]
    shot["evidence_region_id"] = "gate_controls"
    plan = ShotPlan.model_validate(value)
    props, _ = VisualCompiler(tmp_path, tmp_path / "public-b").compile(
        item.source, plan, "PREVIEW-ASPECT-B")
    clip = _evidence_clip(props, shot["shot_id"])
    transform = clip["metadata"]["media_transform"]
    assert clip["metadata"]["fit_mode"] == "FOCUS_CROP"
    assert transform["scale_x"] == pytest.approx(transform["scale_y"])


def test_tall_region_never_uses_vertical_stretch(tmp_path):
    item = fixture(tmp_path)
    value = DirectorShotPlanAdapter().adapt(item, "VLA-ASPECT-C").model_dump()
    shot = value["beats"][1]["shots"][0]
    shot["evidence_region_id"] = "tall_panel"
    plan = ShotPlan.model_validate(value)
    props, _ = VisualCompiler(tmp_path, tmp_path / "public-c").compile(
        item.source, plan, "PREVIEW-ASPECT-C")
    transform = _evidence_clip(props, shot["shot_id"])["metadata"]["media_transform"]
    assert transform["scale_x"] == pytest.approx(transform["scale_y"])
    assert transform["render_width"] / transform["render_height"] == pytest.approx(1600 / 900)


def test_character_asset_uses_contain_and_preserves_ratio(tmp_path):
    item = fixture(tmp_path)
    plan = DirectorShotPlanAdapter().adapt(item, "VLA-ASPECT-D")
    props, diagnostics = VisualCompiler(tmp_path, tmp_path / "public-d").compile(
        item.source, plan, "PREVIEW-ASPECT-D")
    characters = [clip for clip in props["clips"] if clip["metadata"].get("layer_kind") == "CHARACTER"]
    assert characters
    for clip in characters:
        metadata = clip["metadata"]
        assert metadata["fit_mode"] == "CONTAIN"
        assert metadata["aspect_ratio_policy"] == "PRESERVE"
        assert metadata["media_transform"]["scale_x"] == pytest.approx(
            metadata["media_transform"]["scale_y"])
    assert diagnostics["asset_aspect_ratio_qa"]["verdict"] == "PASS"


def test_non_uniform_scale_is_blocker_and_blocks_storyboard_approval(tmp_path):
    item = fixture(tmp_path)
    plan = DirectorShotPlanAdapter().adapt(item, "VLA-ASPECT-E")
    props, _ = VisualCompiler(tmp_path, tmp_path / "public-e").compile(
        item.source, plan, "PREVIEW-ASPECT-E")
    distorted = copy.deepcopy(props)
    clip = next(clip for clip in distorted["clips"] if
                clip["metadata"].get("geometry_kind") == "REGISTERED_ASSET")
    clip["metadata"]["media_transform"]["scale_x"] *= 1.02
    report = mechanical_asset_aspect_ratio_qa(distorted)
    assert report["verdict"] == "FAIL"
    assert report["issues"][0]["code"] == "ASSET_ASPECT_RATIO_DISTORTED"
    assert report["issues"][0]["severity"] == "BLOCKER"
    review = create_review(plan, props=distorted)
    with pytest.raises(ValueError, match="ASSET_ASPECT_RATIO_DISTORTED"):
        approve_review(plan, review, "SPIKE_REVIEWER")


def test_shotplan_excludes_explicit_asset_transform_fields(tmp_path):
    value = DirectorShotPlanAdapter().adapt(fixture(tmp_path), "VLA-ASPECT-F").model_dump()
    forbidden = {"x", "y", "width", "height", "scale_x", "scale_y"}
    def visit(item):
        if isinstance(item, dict):
            assert not set(item) & forbidden
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)
    visit(value)
