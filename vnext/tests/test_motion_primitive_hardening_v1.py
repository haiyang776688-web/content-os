"""MPH-001 motion capability contract tests."""
import copy
from pathlib import Path

import pytest

from vnext.phase2.experimental.visual_language_v1 import (
    MOTION_PRIMITIVES,
    declared_motion_primitives,
    mechanical_asset_aspect_ratio_qa,
    mechanical_motion_primitive_qa,
    motion_frame_state,
    validate_motion_primitive,
    VREInput,
    build_f2_shot_plan,
)
from vnext.phase2.experimental.director_shotplan_adapter_v1 import create_review, approve_review

ROOT = Path(__file__).resolve().parents[2]
RENDERER = ROOT / "vnext/renderers/remotion/project/src/vre001/Renderer.tsx"


def _clip(primitive: str, layer_kind: str) -> dict:
    return {
        "clip_id": f"{primitive}-{layer_kind}", "track": "MEDIA",
        "motion": {"primitive": primitive},
        "metadata": {"layer_kind": layer_kind},
    }


def test_all_declared_primitives_have_renderer_consumer():
    contract = declared_motion_primitives()
    renderer = RENDERER.read_text()
    assert contract
    assert all(item["implemented"] and item["renderer_consumer"] for item in contract.values())
    assert {item["behavior_class"] for item in contract.values()} <= {
        "STATIC", "UNIFORM_SCALE_IN", "OPACITY_REVEAL", "TRANSLATE_IN",
        "CLIP_WIPE", "UNIFORM_POP_IN", "RETURN_SETTLE", "PATH_DRAW",
        "UNIFORM_SETTLE", "WIDTH_REVEAL", "LABEL_REVEAL",
    }
    assert "motion-primitive-contract-v1.json" in renderer
    for behavior in {item["behavior_class"] for item in contract.values()}:
        assert behavior in renderer


def test_all_emitted_primitives_are_declared():
    emitted = set(MOTION_PRIMITIVES.values()) | {"NONE", "DRAW_UNDERLINE", "LABEL_REVEAL"}
    assert emitted == set(declared_motion_primitives())


def test_unknown_primitive_rejected():
    with pytest.raises(ValueError, match="MOTION_PRIMITIVE_UNKNOWN"):
        validate_motion_primitive("MAGIC_DRIFT", "EVIDENCE")
    report = mechanical_motion_primitive_qa({"clips": [_clip("MAGIC_DRIFT", "EVIDENCE")]})
    assert report["verdict"] == "FAIL"
    assert report["issues"][0]["code"] == "MOTION_PRIMITIVE_UNKNOWN"


def test_unsupported_layer_primitive_rejected():
    with pytest.raises(ValueError, match="MOTION_PRIMITIVE_UNSUPPORTED_FOR_LAYER"):
        validate_motion_primitive("DRAW_CONNECTION", "CHARACTER")
    report = mechanical_motion_primitive_qa({"clips": [_clip("DRAW_CONNECTION", "CHARACTER")]})
    assert report["issues"][0]["code"] == "MOTION_PRIMITIVE_UNSUPPORTED_FOR_LAYER"


def test_storyboard_gate_blocks_unsupported_motion_before_render():
    source = VREInput.model_validate_json((ROOT / "docs/project-brain/creative-spikes/"
        "VRE-001-f2-reproduction/evidence/input.json").read_text())
    plan = build_f2_shot_plan(source)
    review = create_review(plan, props={"clips": [_clip("DRAW_CONNECTION", "CHARACTER")]})
    assert review.mechanical_qa["verdict"] == "FAIL"
    with pytest.raises(ValueError, match="MOTION_PRIMITIVE_UNSUPPORTED_FOR_LAYER"):
        approve_review(plan, review, "MPH-001-TEST")


def test_matched_wipe_contract():
    entry = validate_motion_primitive("MATCHED_WIPE", "EVIDENCE")
    assert entry["behavior_class"] == "CLIP_WIPE"
    assert motion_frame_state("MATCHED_WIPE", 0)["clip_right_percent"] == 100
    assert motion_frame_state("MATCHED_WIPE", 1)["clip_right_percent"] == 0
    assert "base.clipPath" in RENDERER.read_text()


def test_draw_connection_contract():
    entry = validate_motion_primitive("DRAW_CONNECTION", "RELATION")
    assert entry["allowed_layer_kinds"] == ["RELATION"]
    assert motion_frame_state("DRAW_CONNECTION", 0) == {"path_reveal": 0}
    assert motion_frame_state("DRAW_CONNECTION", 1) == {"path_reveal": 1}
    renderer = RENDERER.read_text()
    assert "state.pathReveal" in renderer
    assert "strokeDashoffset" in renderer


def test_each_primitive_changes_expected_frames():
    signatures = {}
    for primitive in declared_motion_primitives():
        states = tuple(tuple(sorted(motion_frame_state(primitive, p).items()))
                       for p in (0, .5, 1))
        signatures[primitive] = states
        if primitive == "NONE":
            assert states[0] == states[1] == states[2]
        else:
            assert states[0] != states[1] != states[2]
    # A primitive may share one numeric value, but no complete three-frame
    # behavior signature may alias another named capability.
    assert len(set(signatures.values())) == len(signatures)


def test_motion_does_not_break_asset_aspect_ratio():
    base = {
        "clip_id": "registered-media", "track": "MEDIA",
        "motion": {"primitive": "PUSH_IN"},
        "metadata": {
            "layer_kind": "EVIDENCE", "geometry_kind": "REGISTERED_ASSET",
            "aspect_ratio_policy": "PRESERVE", "fit_mode": "CONTAIN",
            "intrinsic_width": 1600, "intrinsic_height": 900,
            "intrinsic_aspect_ratio": 1600 / 900,
            "media_transform": {"scale_x": .5, "scale_y": .5,
                                "render_width": 800, "render_height": 450},
        },
    }
    for primitive in ("PUSH_IN", "FADE_IN", "FOLLOW_PATH", "MATCHED_WIPE",
                      "POP_CUT", "RETURN_TO_ANCHOR", "SETTLE_HOLD"):
        clip = copy.deepcopy(base)
        clip["motion"]["primitive"] = primitive
        assert mechanical_asset_aspect_ratio_qa({"clips": [clip]})["verdict"] == "PASS"
        state = motion_frame_state(primitive, .5)
        assert "scale_x" not in state and "scale_y" not in state


def test_declared_not_rendered_is_a_blocker(monkeypatch):
    from vnext.phase2.experimental import visual_language_v1 as module
    contract = copy.deepcopy(module.MOTION_PRIMITIVE_CONTRACT)
    contract["primitives"]["PUSH_IN"]["implemented"] = False
    monkeypatch.setattr(module, "MOTION_PRIMITIVE_CONTRACT", contract)
    report = module.mechanical_motion_primitive_qa({"clips": []})
    assert report["verdict"] == "FAIL"
    assert report["issues"][0]["code"] == "MOTION_PRIMITIVE_DECLARED_NOT_RENDERED"
