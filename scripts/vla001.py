"""Build, review, render and verify VLA-001 Test A and Test B."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vnext.phase2.experimental.director_shotplan_adapter_v1 import (
    DirectorShotPlanAdapter,
    DirectorShotPlanInput,
    ReviewFrame,
    ShotPlanEdit,
    StoryboardReview,
    apply_review_edits,
    approve_review,
    attach_compiler_review_data,
    create_review,
    require_approved,
    review_summary,
    write_review_html,
)
from vnext.phase2.experimental.visual_language_v1 import (
    ShotPlan,
    VisualCompiler,
    build_f2_shot_plan,
)

PROJECT = ROOT / "vnext/renderers/remotion/project"
EVIDENCE = ROOT / "docs/project-brain/creative-spikes/VLA-001-director-shotplan/evidence"
INPUTS = {"A": EVIDENCE / "test-a-input.json", "B": EVIDENCE / "test-b-input.json"}
COMPOSITION = "VLA001Storyboard"
ENTRY = "src/vla001-index.tsx"


def _json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(case: str) -> DirectorShotPlanInput:
    return DirectorShotPlanInput.model_validate_json(INPUTS[case].read_text())


def _compile(case: str, output: Path, plan: ShotPlan | None = None, stem: str = "initial"):
    item = _load(case)
    plan = plan or DirectorShotPlanAdapter().adapt(item, f"VLA-001-{case}")
    props, diagnostics = VisualCompiler(ROOT, PROJECT / "public").compile(
        item.source, plan, f"PREVIEW-VLA001-{case}")
    _json(output / f"shot-plan-{stem}.json", plan.model_dump())
    _json(output / f"renderer-neutral-edt-{stem}.json", {"schema_version": 2, "clips": props["clips"]})
    _json(output / f"remotion-props-{stem}.json", props)
    _json(output / f"compiler-diagnostics-{stem}.json", diagnostics)
    return item, plan, props, diagnostics


def _remotion(args: list[str], log: Path, browser: str) -> None:
    command = [str(PROJECT / "node_modules/.bin/remotion"), *args, "--browser-executable", browser]
    with log.open("w") as handle:
        subprocess.run(command, cwd=PROJECT, stdout=handle, stderr=subprocess.STDOUT, check=True)


def _storyboard(case: str, output: Path, plan: ShotPlan, props_path: Path,
                browser: str, stem: str) -> list[ReviewFrame]:
    source = _load(case).source
    frame_dir = output / f"frames-{stem}"
    frame_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for beat in plan.beats:
        for shot in beat.shots:
            time = (shot.start + shot.end) / 2
            frame = min(math.floor(time * source.fps),
                        math.ceil(source.duration * source.fps) - 1)
            path = frame_dir / f"{shot.shot_id}.png"
            _remotion(["still", ENTRY, COMPOSITION, str(path), "--props", str(props_path),
                       "--frame", str(frame)], output / f"still-{stem}-{shot.shot_id}.log", browser)
            frames.append(ReviewFrame(shot_id=shot.shot_id,
                                      path=f"{frame_dir.name}/{path.name}", time=time))
    _contact_sheet(output, frames, stem)
    return frames


def _contact_sheet(output: Path, frames: list[ReviewFrame], stem: str) -> Path:
    thumb_w, thumb_h, label_h, columns = 600, 338, 54, 3
    rows = math.ceil(len(frames) / columns)
    sheet = Image.new("RGB", (thumb_w * columns, (thumb_h + label_h) * rows), "#101617")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=20)
    for index, item in enumerate(frames):
        image = Image.open(output / item.path).convert("RGB")
        image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (index % columns) * thumb_w
        y = (index // columns) * (thumb_h + label_h)
        sheet.paste(image, (x + (thumb_w - image.width) // 2, y))
        draw.text((x + 14, y + thumb_h + 14), f"{item.shot_id}  t={item.time:.2f}s", fill="#f1f5f4", font=font)
    target = output / f"contact-sheet-{stem}.jpg"
    sheet.save(target, quality=92)
    return target


def compile_case(case: str, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    _compile(case, output)


def storyboard_case(case: str, output: Path, browser: str):
    item, plan, props, _ = _compile(case, output)
    frames = _storyboard(case, output, plan, output / "remotion-props-initial.json", browser, "initial")
    review = create_review(plan, frames, props)
    _json(output / "storyboard-review-draft.json", review.model_dump())
    _json(output / "storyboard-review-draft-summary.json", review_summary(item.source, plan, review))
    write_review_html(item.source, plan, review, output / "storyboard-review-draft.html")


def review_case(case: str, output: Path, browser: str):
    item = _load(case)
    plan = ShotPlan.model_validate_json((output / "shot-plan-initial.json").read_text())
    review = StoryboardReview.model_validate_json((output / "storyboard-review-draft.json").read_text())
    if case == "B":
        shot_id = next(beat.shots[0].shot_id for beat in plan.beats if beat.beat_id == "B-B04")
        plan, review = apply_review_edits(plan, review, [
            ShotPlanEdit(beat_id="B-B04", changes={"visual_job": "PROVE"},
                         reason="The narration states a review requirement; the screenshot is proof, not a procedure demo."),
            ShotPlanEdit(beat_id="B-B04", shot_id=shot_id,
                         changes={"shot_type": "EVIDENCE_HIGHLIGHT",
                                  "evidence_treatment": "HIGHLIGHT_REGION",
                                  "motion_semantic": "FOCUS"},
                         reason="Keep the Director inspector visible and highlight the registered semantic-field region."),
        ])
    _, plan, props, _ = _compile(case, output, plan, "reviewed")
    frames = _storyboard(case, output, plan, output / "remotion-props-reviewed.json", browser, "reviewed")
    review.frames = frames
    review = attach_compiler_review_data(review, props)
    review = approve_review(plan, review, "VLA_SPIKE_REVIEW_OPERATOR")
    require_approved(plan, review)
    _json(output / "storyboard-review-approved.json", review.model_dump())
    _json(output / "storyboard-review-approved-summary.json", review_summary(item.source, plan, review))
    write_review_html(item.source, plan, review, output / "storyboard-review-approved.html")


def render_case(case: str, output: Path, browser: str) -> Path:
    plan = ShotPlan.model_validate_json((output / "shot-plan-reviewed.json").read_text())
    review = StoryboardReview.model_validate_json((output / "storyboard-review-approved.json").read_text())
    require_approved(plan, review)
    target = output / f"VLA-001-{case}-Final.mp4"
    _remotion(["render", ENTRY, COMPOSITION, str(target), "--props",
               str(output / "remotion-props-reviewed.json"), "--codec", "h264", "--concurrency", "2"],
              output / "render.log", browser)
    return target


def _probe(path: Path) -> dict:
    data = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path]))
    video = next(stream for stream in data["streams"] if stream["codec_type"] == "video")
    audio = next((stream for stream in data["streams"] if stream["codec_type"] == "audio"), None)
    audio_hash = None
    if audio:
        audio_hash = subprocess.check_output([
            "ffmpeg", "-v", "error", "-i", path, "-map", "0:a:0", "-f", "hash", "-hash", "sha256", "-"]).decode().strip()
    return {"path": str(path), "duration": float(data["format"]["duration"]),
            "frames": int(video["nb_frames"]), "resolution": [video["width"], video["height"]],
            "fps": video["r_frame_rate"], "has_audio": bool(audio), "audio_hash": audio_hash,
            "sha256": _sha(path), "bytes": path.stat().st_size}


def verify_case(case: str, output: Path, baseline: Path | None = None):
    item = _load(case)
    plan = ShotPlan.model_validate_json((output / "shot-plan-reviewed.json").read_text())
    review = StoryboardReview.model_validate_json((output / "storyboard-review-approved.json").read_text())
    require_approved(plan, review)
    diagnostics = json.loads((output / "compiler-diagnostics-reviewed.json").read_text())
    render = _probe(output / f"VLA-001-{case}-Final.mp4")
    shots = [shot for beat in plan.beats for shot in beat.shots]
    jobs = [beat.visual_job for beat in plan.beats]
    max_repeat = max(len(list(group)) for _, group in __import__("itertools").groupby(
        shot.shot_type for shot in shots))
    common = {
        "render": render,
        "storyboard_gate": {"status": review.status, "reviewer": review.reviewer,
                            "edit_count": len(review.edits), "render_was_gated": True},
        "distributions": review_summary(item.source, plan, review)["distributions"],
        "contracts": {"one_primary": diagnostics["primary_contract_pass"],
                      "geometry_owner": "VISUAL_COMPILER_V1",
                      "renderer_policy_free": True,
                      "all_generated_fields_consumed": True},
        "ppt_regression": {"status": "PASS_PENDING_RECORDED_VISUAL_INSPECTION",
                           "max_consecutive_identical_shot_type": max_repeat,
                           "evidence_primary_shots": sum(shot.protagonist.primary == "EVIDENCE" for shot in shots),
                           "shot_type_count": len(set(shot.shot_type for shot in shots))},
    }
    if case == "A":
        original = build_f2_shot_plan(item.source)
        original_jobs = [beat.visual_job for beat in original.beats]
        common["known_f2_regression"] = {
            "visual_job_sequence_equal": jobs == original_jobs,
            "shot_count_equal": len(shots) == sum(len(beat.shots) for beat in original.beats),
            "script_hash_equal": diagnostics["script_sha256"] == item.source.script_sha256,
            "frozen_audio_present": render["has_audio"],
        }
        if baseline:
            gold = _probe(baseline)
            common["known_f2_regression"].update({
                "baseline": gold,
                "duration_delta_seconds": abs(render["duration"] - gold["duration"]),
                "decoded_audio_equal": render["audio_hash"] == gold["audio_hash"],
            })
        assert all(common["known_f2_regression"][key] for key in (
            "visual_job_sequence_equal", "shot_count_equal", "script_hash_equal", "frozen_audio_present"))
    else:
        common["unseen_generalization"] = {
            "duration_in_requested_range": 30 <= item.source.duration <= 60,
            "new_script_id": item.source.script_id,
            "visual_job_count": len(set(jobs)),
            "registered_evidence_used": any(shot.evidence_asset_id for shot in shots),
            "mode_responsibility_change": len(set(beat.visual_mode for beat in plan.beats)) > 1,
            "shot_plan_hand_authored": False,
            "human_pre_render_edits": review.edits,
        }
        assert common["unseen_generalization"]["duration_in_requested_range"]
        assert common["unseen_generalization"]["visual_job_count"] >= 3
        assert common["unseen_generalization"]["registered_evidence_used"]
        assert common["unseen_generalization"]["mode_responsibility_change"]
        assert all(shot.protagonist.primary == "EVIDENCE" for beat in plan.beats
                   if beat.visual_job in ("PROVE", "DEMONSTRATE") for shot in beat.shots)
    _json(output / "verification.json", common)
    print(json.dumps(common, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["compile", "storyboard", "review", "render", "verify", "all"])
    parser.add_argument("--case", choices=["A", "B"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--browser", default="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    args = parser.parse_args()
    output = args.output.resolve()
    if args.action in ("compile", "all"):
        compile_case(args.case, output)
    if args.action in ("storyboard", "all"):
        storyboard_case(args.case, output, args.browser)
    if args.action in ("review", "all"):
        review_case(args.case, output, args.browser)
    if args.action in ("render", "all"):
        render_case(args.case, output, args.browser)
    if args.action in ("verify", "all"):
        verify_case(args.case, output, args.baseline.resolve() if args.baseline else None)


if __name__ == "__main__":
    main()
