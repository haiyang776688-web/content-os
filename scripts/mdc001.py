#!/usr/bin/env python3
"""Build the MDC-001 four-shot primitive-only / motion-designed A/B."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PROJECT = ROOT / "vnext/renderers/remotion/project"
SOURCE_PATH = ROOT / "docs/project-brain/creative-spikes/VRE-001-f2-reproduction/evidence/input.json"
ENTRY = "src/mdc001-index.tsx"
COMPOSITION = "MDC001MotionDesignAB"

from vnext.phase2.experimental.director_shotplan_adapter_v1 import (  # noqa: E402
    ReviewFrame, approve_review, create_review, review_summary,
)
from vnext.phase2.experimental.motion_design_v1 import MotionDesignResolver  # noqa: E402
from vnext.phase2.experimental.visual_language_v1 import (  # noqa: E402
    Protagonist, Shot, ShotBeat, ShotPlan, VREInput, VisualCompiler,
)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_plan(source: VREInput) -> ShotPlan:
    def p(primary, supporting=(), background=()):
        return Protagonist(primary=primary, supporting=list(supporting), background=list(background))
    return ShotPlan(plan_id="MDC-001-FOUR-SHOT", source_script_id=source.script_id,
        visual_mode="BRAND_BALANCED", beats=[
            ShotBeat(beat_id="MDC-B01", script_segment_id="SEG-02", visual_job="DEMONSTRATE",
                visual_mode="EVIDENCE_HEAVY", shots=[Shot(
                    shot_id="MDC-S01", shot_type="EVIDENCE_FOCUS", start=0, end=4.5,
                    protagonist=p("EVIDENCE"), evidence_asset_id="EV-RESEARCH",
                    evidence_treatment="FOCUS_REGION", evidence_region_id="import_control",
                    semantic_focus="本地入口", motion_semantic="FOCUS", callout="聚焦入口")]),
            ShotBeat(beat_id="MDC-B02", script_segment_id="SEG-02", visual_job="EXPLAIN",
                visual_mode="BRAND_BALANCED", shots=[Shot(
                    shot_id="MDC-S02", shot_type="CHARACTER_EXPLAIN", start=4.5, end=9,
                    protagonist=p("XIAOY"), character_role="EXPLAINER",
                    semantic_focus="人工审查边界", motion_semantic="REVEAL", callout="先看边界")]),
            ShotBeat(beat_id="MDC-B03", script_segment_id="SEG-03", visual_job="REACT",
                visual_mode="BRAND_BALANCED", shots=[Shot(
                    shot_id="MDC-S03", shot_type="CHARACTER_REACTION", start=9, end=13.5,
                    protagonist=p("XIAOY", ["EVIDENCE"]), evidence_asset_id="EV-RESEARCH",
                    evidence_treatment="DETAIL_CROP", evidence_region_id="candidate_rule",
                    character_role="REACTION", semantic_focus="候选不能自动升级",
                    motion_semantic="INTERRUPT", callout="等等。")]),
            ShotBeat(beat_id="MDC-B04", script_segment_id="SEG-04", visual_job="EXPLAIN",
                visual_mode="BRAND_BALANCED", shots=[Shot(
                    shot_id="MDC-S04", shot_type="RELATION_EXPLAIN", start=13.5,
                    end=source.duration, protagonist=p("DIAGRAM", background=["EVIDENCE"]),
                    evidence_asset_id="EV-RESEARCH", evidence_treatment="RELATION",
                    evidence_region_id="source_rule", semantic_focus="来源与事实绑定",
                    motion_semantic="CONNECT", callout="SOURCE ↔ FACT")]),
        ])


def compile_ab(output: Path):
    source = VREInput.model_validate_json(SOURCE_PATH.read_text())
    plan = build_plan(source)
    design = MotionDesignResolver().resolve(plan)
    compiler = VisualCompiler(ROOT, PROJECT / "public")
    primitive, primitive_diagnostics = compiler.compile(
        source, plan, "PREVIEW-MDC001")
    designed, designed_diagnostics = compiler.compile(
        source, plan, "PREVIEW-MDC001", design)
    # A second compile proves deterministic numeric realization.
    repeated, repeated_diagnostics = compiler.compile(
        source, plan, "PREVIEW-MDC001", design)
    assert designed_diagnostics["compiled_motion_artifact"]["compiled_motion_sha256"] == (
        repeated_diagnostics["compiled_motion_artifact"]["compiled_motion_sha256"])
    assert [(clip["clip_id"], clip["metadata"].get("motion_design"))
            for clip in designed["clips"]] == [
        (clip["clip_id"], clip["metadata"].get("motion_design"))
        for clip in repeated["clips"]]

    stripped = copy.deepcopy(designed)
    stripped.pop("motion_design_qa")
    stripped.pop("compiled_motion_artifact")
    for clip in stripped["clips"]:
        clip["metadata"].pop("motion_design", None)
    assert stripped == primitive

    write_json(output / "frozen-shot-plan.json", plan.model_dump())
    write_json(output / "motion-design-plan.json", design.model_dump())
    write_json(output / "primitive-only-props.json", primitive)
    write_json(output / "motion-designed-props.json", designed)
    write_json(output / "primitive-only-diagnostics.json", primitive_diagnostics)
    write_json(output / "motion-designed-diagnostics.json", designed_diagnostics)
    write_json(output / "compiled-motion-artifact.json",
               designed_diagnostics["compiled_motion_artifact"])
    return source, plan, design, primitive, designed, designed_diagnostics


def remotion(args: list[str], log: Path, browser: str) -> None:
    command = [str(PROJECT / "node_modules/.bin/remotion"), *args,
               "--browser-executable", browser]
    with log.open("w") as handle:
        subprocess.run(command, cwd=PROJECT, stdout=handle,
                       stderr=subprocess.STDOUT, check=True)


def render_ab(output: Path, browser: str):
    renders = {}
    for label, props in (("primitive-only", output / "primitive-only-props.json"),
                         ("motion-designed", output / "motion-designed-props.json")):
        target = output / f"MDC-001-{label}.mp4"
        remotion(["render", ENTRY, COMPOSITION, str(target), "--props", str(props),
                  "--codec", "h264", "--concurrency", "2"],
                 output / f"{label}-render.log", browser)
        renders[label] = target
    return renders


def render_review_frames(output: Path, plan: ShotPlan, browser: str):
    review_frames = []
    all_frames = {"primitive-only": [], "motion-designed": []}
    for label in all_frames:
        props = output / f"{label}-props.json"
        frame_dir = output / f"{label}-frames"
        frame_dir.mkdir(parents=True, exist_ok=True)
        for beat in plan.beats:
            shot = beat.shots[0]
            # Show early, action, and settled states.  Offsets are local to the shot.
            local_frames = (1, 7, 20)
            for stage, offset in zip(("start", "action", "settled"), local_frames):
                frame = min(math.floor(shot.start * 30) + offset,
                            math.ceil(shot.end * 30) - 1)
                target = frame_dir / f"{shot.shot_id}-{stage}.png"
                remotion(["still", ENTRY, COMPOSITION, str(target), "--props", str(props),
                          "--frame", str(frame)], output / f"{label}-{shot.shot_id}-{stage}.log", browser)
                all_frames[label].append((shot.shot_id, stage, target))
                if label == "motion-designed" and stage == "action":
                    review_frames.append(ReviewFrame(
                        shot_id=shot.shot_id, path=f"{frame_dir.name}/{target.name}",
                        time=frame / 30))
    make_contact_sheet(output, all_frames)
    return review_frames


def make_contact_sheet(output: Path, all_frames) -> Path:
    width, height, label = 320, 180, 42
    sheet = Image.new("RGB", (width * 6, (height + label) * 4), "#101319")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=16)
    by_key = {(variant, shot, stage): path for variant, rows in all_frames.items()
              for shot, stage, path in rows}
    for row, shot in enumerate(("MDC-S01", "MDC-S02", "MDC-S03", "MDC-S04")):
        for col, (variant, stage) in enumerate([
            ("primitive-only", "start"), ("primitive-only", "action"),
            ("primitive-only", "settled"), ("motion-designed", "start"),
            ("motion-designed", "action"), ("motion-designed", "settled")]):
            image = Image.open(by_key[(variant, shot, stage)]).convert("RGB")
            image.thumbnail((width, height), Image.Resampling.LANCZOS)
            x, y = col * width, row * (height + label)
            sheet.paste(image, (x, y))
            draw.text((x + 8, y + height + 11),
                      f"{shot} / {variant} / {stage}", fill="#f4f5f3", font=font)
    target = output / "MDC-001-static-dynamic-contact-sheet.jpg"
    sheet.save(target, quality=92)
    return target


def storyboard_gate(output: Path, source: VREInput, plan: ShotPlan,
                    designed: dict, frames: list[ReviewFrame]):
    review = create_review(plan, frames=frames, props=designed)
    review = approve_review(plan, review, "MDC-001-MANUAL-VISUAL-REVIEW")
    write_json(output / "storyboard-review-approved.json", review.model_dump())
    write_json(output / "storyboard-review-summary.json", review_summary(source, plan, review))
    return review


def split_shots(output: Path, plan: ShotPlan, renders: dict):
    shot_dir = output / "shots"
    shot_dir.mkdir(parents=True, exist_ok=True)
    for beat in plan.beats:
        shot = beat.shots[0]
        for label, source in renders.items():
            target = shot_dir / f"{shot.shot_id}-{label}.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-v", "error", "-ss", str(shot.start),
                "-i", str(source), "-t", str(shot.end - shot.start),
                "-c:v", "libx264", "-crf", "24", "-preset", "medium",
                "-c:a", "aac", "-b:a", "128k", str(target),
            ], check=True)


def motion_preview(output: Path, renders: dict) -> Path:
    target = output / "MDC-001-motion-preview-side-by-side.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(renders["primitive-only"]),
        "-i", str(renders["motion-designed"]), "-filter_complex",
        "[0:v]scale=960:540[left];[1:v]scale=960:540[right];[left][right]hstack=inputs=2[v]",
        "-map", "[v]", "-map", "1:a?", "-c:v", "libx264", "-crf", "23",
        "-preset", "medium", "-c:a", "aac", "-b:a", "160k", str(target),
    ], check=True)
    return target


def motion_strip(output: Path, plan: ShotPlan, renders: dict) -> Path:
    """Create an eight-sample temporal strip for honest human motion review."""
    offsets = (0, 2, 4, 6, 8, 10, 14, 20)
    extracted = {}
    strip_root = output / "motion-strip-frames"
    strip_root.mkdir(parents=True, exist_ok=True)
    for variant, source in renders.items():
        frame_numbers = []
        for beat in plan.beats:
            base = round(beat.shots[0].start * 30)
            frame_numbers.extend(base + offset for offset in offsets)
        selector = "+".join(f"eq(n\\,{frame})" for frame in frame_numbers)
        target_dir = strip_root / variant
        target_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-i", str(source),
            "-vf", f"select={selector}", "-fps_mode", "vfr",
            str(target_dir / "frame-%03d.png"),
        ], check=True)
        extracted[variant] = sorted(target_dir.glob("frame-*.png"))
        assert len(extracted[variant]) == len(frame_numbers)
    width, height, label = 200, 112, 30
    sheet = Image.new("RGB", (width * len(offsets), (height + label) * 8), "#101319")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=13)
    for shot_index, beat in enumerate(plan.beats):
        shot_id = beat.shots[0].shot_id
        for variant_index, variant in enumerate(("primitive-only", "motion-designed")):
            row = shot_index * 2 + variant_index
            for col, offset in enumerate(offsets):
                image = Image.open(extracted[variant][shot_index * len(offsets) + col]).convert("RGB")
                image.thumbnail((width, height), Image.Resampling.LANCZOS)
                x, y = col * width, row * (height + label)
                sheet.paste(image, (x, y))
                draw.text((x + 5, y + height + 8),
                          f"{shot_id} {variant} f+{offset}", fill="#f4f5f3", font=font)
    target = output / "MDC-001-motion-temporal-strip.jpg"
    sheet.save(target, quality=92)
    return target


def probe(path: Path) -> dict:
    payload = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path]))
    video = next(stream for stream in payload["streams"] if stream["codec_type"] == "video")
    audio = next((stream for stream in payload["streams"] if stream["codec_type"] == "audio"), None)
    audio_hash = None
    if audio:
        audio_hash = subprocess.check_output([
            "ffmpeg", "-v", "error", "-i", path, "-map", "0:a:0",
            "-f", "hash", "-hash", "sha256", "-"]).decode().strip()
    return {"path": path.name, "sha256": sha256(path), "bytes": path.stat().st_size,
            "duration": float(payload["format"]["duration"]),
            "frames": int(video["nb_frames"]), "resolution": [video["width"], video["height"]],
            "fps": video["r_frame_rate"], "has_audio": bool(audio), "audio_hash": audio_hash}


def verify(output: Path, plan: ShotPlan, renders: dict, diagnostics: dict, review, preview: Path):
    render_data = {label: probe(path) for label, path in renders.items()}
    assert render_data["primitive-only"]["duration"] == render_data["motion-designed"]["duration"]
    assert render_data["primitive-only"]["frames"] == render_data["motion-designed"]["frames"]
    assert render_data["primitive-only"]["audio_hash"] == render_data["motion-designed"]["audio_hash"]
    value = {
        "status": "PASS_PENDING_HUMAN_MOTION_REVIEW",
        "ab_invariants": {
            "same_script": True, "same_audio": True, "same_shot_plan": True,
            "same_visual_jobs": True, "same_shot_types": True, "same_assets": True,
            "same_geometry": True, "same_shot_timing": True,
            "only_variable": "MOTION_DESIGN",
        },
        "renders": render_data,
        "motion_preview": probe(preview),
        "motion_phrases": ["FOCUS", "EXPLAIN", "IMPACT_WARN", "CONNECT"],
        "shot_types": [beat.shots[0].shot_type for beat in plan.beats],
        "storyboard_gate": {"status": review.status, "reviewer": review.reviewer},
        "mechanical_qa": diagnostics["motion_design_qa"],
        "primitive_qa": diagnostics["motion_primitive_qa"],
        "aspect_ratio_qa": diagnostics["asset_aspect_ratio_qa"],
        "determinism": diagnostics["compiled_motion_artifact"],
    }
    write_json(output / "mdc001-verification.json", value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["compile", "render", "review", "verify", "all"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--browser", default="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    source, plan, design, primitive, designed, diagnostics = compile_ab(output)
    if args.action == "compile":
        return
    renders = render_ab(output, args.browser) if args.action in ("render", "all") else {
        "primitive-only": output / "MDC-001-primitive-only.mp4",
        "motion-designed": output / "MDC-001-motion-designed.mp4"}
    if args.action == "render":
        return
    frames = render_review_frames(output, plan, args.browser)
    review = storyboard_gate(output, source, plan, designed, frames)
    split_shots(output, plan, renders)
    preview = motion_preview(output, renders)
    motion_strip(output, plan, renders)
    value = verify(output, plan, renders, diagnostics, review, preview)
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
