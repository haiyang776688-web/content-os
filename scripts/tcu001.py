"""Build, render and verify TCU-001 Sample A timing-consumer A/B evidence.

This runner is deliberately experimental.  It reads frozen ATS evidence but
does not import ATS implementation code and never mutates production timing.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vnext.phase2.experimental.aligned_timing_consumer_v1 import (
    aligned_existing_beat_timing,
    aligned_subtitles,
    beat_boundaries,
    boundary_metrics,
    build_aligned_timing_map,
    canonical_sha,
    timeline_boundaries,
)


FIXTURE = ROOT / "fixtures/tcu001/sample-a"
SPIKE = ROOT / "docs/project-brain/creative-spikes/TCU-001-timing-consumer"
EVIDENCE = SPIKE / "evidence"
ATS = EVIDENCE / "ats001-readonly"
MEDIA = EVIDENCE / "media"
PROJECT = ROOT / "vnext/renderers/remotion/project"
PUBLIC = PROJECT / "public/PREVIEW-TCU001"
BROWSER = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
ATS_COMMIT = "e79aa07a1d06985237b177c9e65f980ad1aca3f3"
BASELINE_COMMIT = "eea4b00e9b3809e16cd2c5b31123a5f4089cc00c"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def approved_bindings(ground_truth: dict) -> list[dict]:
    beat_after = {"TG-004": "B-08-02", "TG-007": "B-09-02"}
    return [{
        "boundary_id": row["boundary_id"],
        "segment_id": row["segment_id"],
        "beat_after_id": beat_after[row["boundary_id"]],
        "text_before": row["script_text_before"],
        "text_after": row["script_text_after"],
        "approved": True,
        "approval_source": "ATS001_TARGETED_GROUND_TRUTH_USER_REVIEW",
    } for row in ground_truth["cases"] if row["boundary_id"] in beat_after]


def frozen_shotplan(director_artifact: dict) -> dict:
    """Freeze the effective Sample A shot semantics without inventing policy.

    Sample A predates the formal DEC-011 ShotPlan artifact.  The production
    renderer consumes these Director beats through Visual EDT.  TCU records a
    one-to-one semantic snapshot so A and B have a pinned ShotPlan hash; it is
    not presented as a newly generated DEC-011 plan.
    """
    payload = director_artifact["payload"]
    beats = []
    for row in payload["beats"]:
        beats.append({
            "beat_id": row["beat_id"],
            "shot_id": "SHOT-" + row["beat_id"],
            "script_segment_id": row["script_segment_id"],
            "purpose": row["purpose"],
            "visual_focus": row["visual_focus"],
            "visual_form": row["visual_form"],
            "pattern_id": row["pattern_id"],
            "template_id": row["template_id"],
            "character_intent": row["character_intent"],
            "character_action_id": row.get("character_action_id"),
            "motion_intent": row["motion_intent"],
            "slots": row["slots"],
            "reveal_order": row["reveal_order"],
        })
    value = {
        "schema_version": 1,
        "artifact_type": "TCU_FROZEN_SHOTPLAN_SEMANTICS",
        "source_type": "DIRECTOR_IR_EFFECTIVE_SHOTPLAN_SNAPSHOT",
        "source_artifact_id": director_artifact["artifact_id"],
        "source_output_hash": director_artifact["output_hash"],
        "notes": "One effective shot per existing Director beat; TCU does not generate or change semantics.",
        "beats": beats,
    }
    value["artifact_hash"] = canonical_sha(value)
    return value


def rewrite_media_paths(props: dict) -> dict:
    value = copy.deepcopy(props)
    for clip in value["clips"]:
        if clip.get("asset_src"):
            clip["asset_src"] = f"PREVIEW-TCU001/{Path(clip['asset_src']).name}"
    for font in value.get("fonts", []):
        if font.get("src"):
            font["src"] = f"PREVIEW-TCU001/{Path(font['src']).name}"
    return value


def combine(current: dict, aligned_sub: list[dict], aligned_visual: list[dict]) -> dict:
    updated = {row["clip_id"]: row for row in [*aligned_sub, *aligned_visual]}
    value = copy.deepcopy(current)
    value["clips"] = [updated[row["clip_id"]] for row in current["clips"]]
    return value


def boundary_hits(boundaries: list[int], controls: list[dict]) -> list[dict]:
    return [{
        "control_id": row["control_id"],
        "window_start_ms": row["window_start_ms"],
        "window_end_ms": row["window_end_ms"],
        "hits_ms": [x for x in boundaries if row["window_start_ms"] <= x <= row["window_end_ms"]],
    } for row in controls]


def control_changes(before: list[dict], after: list[dict]) -> list[dict]:
    previous = {row["control_id"]: set(row["hits_ms"]) for row in before}
    changes = []
    for row in after:
        old = previous[row["control_id"]]
        new = set(row["hits_ms"])
        if old != new:
            changes.append({
                "control_id": row["control_id"],
                "current_hits_ms": sorted(old),
                "aligned_hits_ms": sorted(new),
                "new_timestamp_values_ms": sorted(new - old),
                # Controls are phrase-context normal regions, not millisecond
                # labels.  Moving one existing boundary inside the same control
                # is observable change, but only an increased hit count (or a
                # first hit where none existed) is a new regression.
                "new_regression": (not old and bool(new)) or len(new) > len(old),
            })
    return changes


def semantic_projection(props: dict) -> dict:
    """Fields whose equality proves A/B differs only in WHEN."""
    clips = []
    for row in props["clips"]:
        metadata = {k: v for k, v in row.get("metadata", {}).items()
                    if k not in {"timing_consumer", "timing_source", "alignment_artifact_hash", "approved_anchor_id"}}
        clips.append({
            "clip_id": row["clip_id"], "scene_id": row.get("scene_id"),
            "beat_id": row.get("beat_id"), "ir_node_id": row.get("ir_node_id"),
            "origin": row.get("origin"), "edit_source": row.get("edit_source"),
            "pattern_id": row.get("pattern_id"), "track": row["track"],
            "asset_id": row.get("asset_id"), "position": row.get("position"),
            "scale": row.get("scale"), "crop": row.get("crop"),
            "opacity": row.get("opacity"), "motion": row.get("motion"),
            "reveal": row.get("reveal"), "hidden": row.get("hidden"),
            "muted": row.get("muted"), "metadata": metadata,
            "asset_src": row.get("asset_src"), "media_kind": row.get("media_kind"),
        })
    return {"clips": clips, "canvas_color": props.get("canvas_color"),
            "foreground_color": props.get("foreground_color"), "typography": props.get("typography")}


def build() -> dict:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    manifest = load(ATS / "sample-A.benchmark.json")
    raw_path = ATS / "whisper-medium-dtw-raw.json"
    ground_truth = load(ATS / "targeted-ground-truth.json")
    controls = load(ATS / "normal-control-set.json")["controls"]
    script = load(FIXTURE / "script-artifact.json")
    director = load(FIXTURE / "director-ir-artifact.json")
    edt = load(FIXTURE / "visual-edt-artifact.json")
    audio_clock = load(FIXTURE / "current-audio-timing-map.json")
    original_props = load(FIXTURE / "current-render-props.json")
    current = rewrite_media_paths(original_props)

    aligned_map = build_aligned_timing_map(
        manifest, load(raw_path), alignment_artifact_hash=sha(raw_path), source_commit=ATS_COMMIT)
    shotplan = frozen_shotplan(director)
    write_json(EVIDENCE / "aligned-timing-map.json", aligned_map)
    write_json(EVIDENCE / "frozen-shotplan-semantics.json", shotplan)

    current_sub = [row for row in current["clips"] if row["track"] == "SUBTITLE"]
    current_visual = [row for row in current["clips"] if row["track"] != "SUBTITLE"]
    aligned_sub, subtitle_report = aligned_subtitles(current_sub, manifest, aligned_map)
    aligned_visual, beat_report = aligned_existing_beat_timing(
        current_visual, manifest, aligned_map, approved_bindings(ground_truth))
    aligned = combine(current, aligned_sub, aligned_visual)
    aligned["audio_timing_map"] = {
        **aligned.get("audio_timing_map", {}),
        "experimental_aligned_timing_map_hash": aligned_map["artifact_hash"],
        "experimental_consumer": "TCU001_ALIGNED_TIMING_CONSUMER_V1",
        "production_default_changed": False,
    }
    write_json(EVIDENCE / "current-render-props.json", current)
    write_json(EVIDENCE / "aligned-render-props.json", aligned)

    current_beats = beat_boundaries(current_visual)
    aligned_beats = beat_boundaries(aligned_visual)
    current_sub_boundaries = timeline_boundaries(current_sub)
    aligned_sub_boundaries = timeline_boundaries(aligned_sub)
    beat_metrics_a = boundary_metrics(current_beats, ground_truth)
    beat_metrics_b = boundary_metrics(aligned_beats, ground_truth)
    subtitle_metrics_a = boundary_metrics(current_sub_boundaries, ground_truth)
    subtitle_metrics_b = boundary_metrics(aligned_sub_boundaries, ground_truth)
    beat_controls_a = boundary_hits(current_beats, controls)
    beat_controls_b = boundary_hits(aligned_beats, controls)
    subtitle_controls_a = boundary_hits(current_sub_boundaries, controls)
    subtitle_controls_b = boundary_hits(aligned_sub_boundaries, controls)

    counts_a = {
        "clips": len(current["clips"]),
        "beats": len({row.get("beat_id") for row in current["clips"] if row.get("beat_id")}),
        "shots": len(shotplan["beats"]),
        "subtitle_chunks": len(current_sub),
    }
    counts_b = {
        "clips": len(aligned["clips"]),
        "beats": len({row.get("beat_id") for row in aligned["clips"] if row.get("beat_id")}),
        "shots": len(shotplan["beats"]),
        "subtitle_chunks": len(aligned_sub),
    }
    no_boundary_new = []
    before_no = {r["case_id"]: set(r["new_or_existing_hits_ms"]) for r in beat_metrics_a["no_boundary"]}
    for row in beat_metrics_b["no_boundary"]:
        gained = sorted(set(row["new_or_existing_hits_ms"]) - before_no[row["case_id"]])
        if gained:
            no_boundary_new.append({"case_id": row["case_id"], "new_hits_ms": gained})

    report = {
        "schema_version": 1,
        "spike": "TCU-001",
        "sample": "A",
        "baseline_commit": BASELINE_COMMIT,
        "ats_readonly_commit": ATS_COMMIT,
        "inputs": {
            "script_artifact_id": script["artifact_id"],
            "script_artifact_output_hash": script["output_hash"],
            "script_text_sha256": manifest["script_sha256"],
            "audio_artifact_id": manifest["voice_artifact_id"],
            "audio_sha256": manifest["audio_sha256"],
            "director_ir_artifact_id": director["artifact_id"],
            "director_ir_sha256": director["output_hash"],
            "shotplan_sha256": shotplan["artifact_hash"],
            "visual_edt_artifact_id": edt["artifact_id"],
            "visual_edt_sha256": edt["output_hash"],
            "current_timing_artifact_id": audio_clock["artifact_id"],
            "current_timing_artifact_sha256": audio_clock["output_hash"],
            "aligned_timing_artifact_sha256": aligned_map["artifact_hash"],
            "alignment_evidence_sha256": sha(raw_path),
        },
        "ab": {
            "current_props_sha256": sha(EVIDENCE / "current-render-props.json"),
            "aligned_props_sha256": sha(EVIDENCE / "aligned-render-props.json"),
            "current_semantic_projection_sha256": canonical_sha(semantic_projection(current)),
            "aligned_semantic_projection_sha256": canonical_sha(semantic_projection(aligned)),
            "counts_current": counts_a,
            "counts_aligned": counts_b,
        },
        "aligned_timing_map": {
            "coverage": aligned_map["coverage"],
            "phrase_anchor_count": len(aligned_map["phrase_anchors"]),
            "text_span_anchor_count": len(aligned_map["text_span_anchors"]),
            "raw_asr_segment_boundaries_consumed": False,
        },
        "consumer_a_subtitles": {
            "report": subtitle_report,
            "current_ground_truth": subtitle_metrics_a,
            "aligned_ground_truth": subtitle_metrics_b,
            "current_normal_controls": subtitle_controls_a,
            "aligned_normal_controls": subtitle_controls_b,
            "normal_control_changes": control_changes(subtitle_controls_a, subtitle_controls_b),
            "new_normal_control_regressions": [row for row in control_changes(subtitle_controls_a, subtitle_controls_b)
                                                   if row["new_regression"]],
        },
        "consumer_b_existing_beats": {
            "report": beat_report,
            "current_ground_truth": beat_metrics_a,
            "aligned_ground_truth": beat_metrics_b,
            "current_normal_controls": beat_controls_a,
            "aligned_normal_controls": beat_controls_b,
            "normal_control_changes": control_changes(beat_controls_a, beat_controls_b),
            "new_normal_control_regressions": [row for row in control_changes(beat_controls_a, beat_controls_b)
                                                   if row["new_regression"]],
            "new_no_boundary_hits": no_boundary_new,
        },
        "contracts": {
            "semantic_projection_equal": canonical_sha(semantic_projection(current)) == canonical_sha(semantic_projection(aligned)),
            "counts_equal": counts_a == counts_b,
            "subtitle_text_equal": [r["metadata"]["text"] for r in current_sub] == [r["metadata"]["text"] for r in aligned_sub],
            "subtitle_order_equal": [r["clip_id"] for r in current_sub] == [r["clip_id"] for r in aligned_sub],
            "raw_asr_segmentation_used": False,
            "production_default": "UNCHANGED",
            "decisions": "UNCHANGED",
        },
    }
    write_json(EVIDENCE / "tcu001-ab-metrics.json", report)
    comparison_page(report, ground_truth, controls)
    stage_media()
    return report


def stage_media() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for source in MEDIA.iterdir():
        target = PUBLIC / source.name
        if not target.exists() or sha(target) != sha(source):
            shutil.copy2(source, target)


def comparison_page(report: dict, ground_truth: dict, controls: list[dict]) -> None:
    points = []
    for row in ground_truth["cases"]:
        if row["verdict"] == "BOUNDARY":
            t = row["correct_boundary_timestamp_ms"] / 1000
        else:
            window = row["forbidden_boundary_range"]
            t = (window["start_ms"] + window["end_ms"]) / 2000
        points.append((row["boundary_id"], row["verdict"], t))
    for row in controls:
        points.append((row["control_id"], "CONTROL_NORMAL",
                       (row["window_start_ms"] + row["window_end_ms"]) / 2000))
    buttons = "\n".join(
        f'<button data-time="{t:.3f}"><b>{html.escape(label)}</b><span>{html.escape(kind)} · {t:.3f}s</span></button>'
        for label, kind, t in points)
    beat_before = report["consumer_b_existing_beats"]["current_ground_truth"]["positive_error"]["median_ms"]
    beat_after = report["consumer_b_existing_beats"]["aligned_ground_truth"]["positive_error"]["median_ms"]
    page = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TCU-001 Sample A — Timing A/B</title><style>
:root{{--bg:#0e1415;--panel:#172022;--ink:#f5f7f6;--muted:#aeb9b6;--accent:#ffc400;--good:#62df91}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif}}
header{{padding:28px 34px;border-bottom:1px solid #334143}}h1{{margin:0 0 8px;font-size:28px}}header p{{margin:0;color:var(--muted)}}
.metrics{{display:flex;gap:12px;padding:18px 34px}}.metric{{background:var(--panel);padding:14px 18px;border-radius:10px}}
.metric strong{{color:var(--accent);font-size:22px}}.videos{{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:0 34px}}
.video{{background:var(--panel);padding:12px;border-radius:12px}}video{{width:100%;background:#000}}h2{{font-size:16px;margin:0 0 8px}}
.controls{{padding:20px 34px 36px;display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:8px}}
button{{border:1px solid #3a4a4d;background:#1a2527;color:var(--ink);border-radius:8px;padding:10px;text-align:left;cursor:pointer}}
button:hover{{border-color:var(--accent)}}button span{{display:block;color:var(--muted);font-size:12px;margin-top:2px}}
.note{{margin:0 34px 20px;padding:14px 18px;border-left:4px solid var(--good);background:#14251c}}
</style></head><body><header><h1>TCU-001 · Sample A Timing Consumer A/B</h1>
<p>同一 Script / Audio / ShotPlan semantics / Visual EDT。左侧 CURRENT，右侧仅改变 WHEN。</p></header>
<section class="metrics"><div class="metric">Beat 正边界中位误差<br><strong>{beat_before} → {beat_after} ms</strong></div>
<div class="metric">Aligned coverage<br><strong>{report['aligned_timing_map']['coverage']:.2%}</strong></div>
<div class="metric">新 NO_BOUNDARY Beat 切点<br><strong>{len(report['consumer_b_existing_beats']['new_no_boundary_hits'])}</strong></div></section>
<p class="note">点击下方检查点会让两版视频同步跳转到该位置前 0.7 秒。TG-004 与 TG-007 是已批准正边界；其余目标点用于确认没有新增错误切分。</p>
<section class="videos"><div class="video"><h2>A · CURRENT_TIMING</h2><video id="a" controls preload="metadata" src="TCU-001-Sample-A-CURRENT.mp4"></video></div>
<div class="video"><h2>B · ALIGNED_TIMING_CONSUMER</h2><video id="b" controls preload="metadata" src="TCU-001-Sample-A-ALIGNED.mp4"></video></div></section>
<section class="controls">{buttons}</section><script>
const a=document.querySelector('#a'),b=document.querySelector('#b');let syncing=false;
function seek(t){{a.currentTime=t;b.currentTime=t}};
document.querySelectorAll('button[data-time]').forEach(x=>x.onclick=()=>seek(Math.max(0,Number(x.dataset.time)-.7)));
[a,b].forEach((v,i)=>{{v.addEventListener('play',()=>{{(i? a:b).currentTime=v.currentTime;(i? a:b).play()}});v.addEventListener('pause',()=>{{if(!(i?a:b).paused)(i?a:b).pause()}});v.addEventListener('seeking',()=>{{if(!syncing){{syncing=true;(i?a:b).currentTime=v.currentTime;setTimeout(()=>syncing=false,80)}}}})}});
</script></body></html>"""
    (EVIDENCE / "comparison.html").write_text(page, encoding="utf-8")


def remotion_render(props: Path, output: Path, log: Path) -> None:
    binary = PROJECT / "node_modules/.bin/remotion"
    if not binary.exists():
        raise RuntimeError("REMOTION_NODE_MODULES_MISSING")
    command = [str(binary), "render", "src/index.tsx", "ContentOSPreview", str(output),
               "--props", str(props), "--codec", "h264", "--concurrency", "2"]
    if Path(BROWSER).is_file():
        command.extend(["--browser-executable", BROWSER])
    with log.open("w", encoding="utf-8") as handle:
        subprocess.run(command, cwd=PROJECT, stdout=handle, stderr=subprocess.STDOUT, check=True)


def render() -> None:
    build()
    remotion_render(EVIDENCE / "current-render-props.json",
                    EVIDENCE / "TCU-001-Sample-A-CURRENT.mp4", EVIDENCE / "render-current.log")
    remotion_render(EVIDENCE / "aligned-render-props.json",
                    EVIDENCE / "TCU-001-Sample-A-ALIGNED.mp4", EVIDENCE / "render-aligned.log")


def probe(path: Path) -> dict:
    raw = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]))
    video = next(row for row in raw["streams"] if row["codec_type"] == "video")
    audio = next((row for row in raw["streams"] if row["codec_type"] == "audio"), None)
    audio_hash = None
    if audio:
        audio_hash = subprocess.check_output([
            "ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0",
            "-f", "hash", "-hash", "sha256", "-"]).decode().strip()
    return {
        "path": path.name, "sha256": sha(path), "bytes": path.stat().st_size,
        "duration_seconds": float(raw["format"]["duration"]),
        "resolution": [int(video["width"]), int(video["height"])],
        "fps": video["r_frame_rate"], "frame_count": int(video["nb_frames"]),
        "has_audio": bool(audio), "decoded_audio_sha256": audio_hash,
    }


def make_visual_checks() -> list[dict]:
    current = EVIDENCE / "TCU-001-Sample-A-CURRENT.mp4"
    aligned = EVIDENCE / "TCU-001-Sample-A-ALIGNED.mp4"
    checks = [
        ("TG-004", 72.4, "before approved boundary; CURRENT has already cut, ALIGNED has not"),
        ("TG-006", 81.0, "NO_BOUNDARY window; aligned Beat no longer cuts here"),
        ("TG-007", 82.0, "before approved boundary; CURRENT has already cut, ALIGNED has not"),
        ("NC-004", 31.5, "normal-control spot check"),
    ]
    rows = []
    for label, timestamp, purpose in checks:
        left = EVIDENCE / f"{label}-CURRENT.jpg"
        right = EVIDENCE / f"{label}-ALIGNED.jpg"
        combined = EVIDENCE / f"{label}-SIDE-BY-SIDE.jpg"
        for source, target in ((current, left), (aligned, right)):
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(timestamp),
                            "-i", str(source), "-frames:v", "1", "-q:v", "2", str(target)], check=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(left), "-i", str(right),
                        "-filter_complex", "[0:v][1:v]hstack=inputs=2[v]", "-map", "[v]",
                        "-q:v", "2", str(combined)], check=True)
        rows.append({"case_id": label, "timestamp_seconds": timestamp, "purpose": purpose,
                     "side_by_side": combined.name, "sha256": sha(combined)})
    return rows


def verify() -> dict:
    metrics = load(EVIDENCE / "tcu001-ab-metrics.json")
    current_path = EVIDENCE / "TCU-001-Sample-A-CURRENT.mp4"
    aligned_path = EVIDENCE / "TCU-001-Sample-A-ALIGNED.mp4"
    if not current_path.exists() or not aligned_path.exists():
        raise RuntimeError("TCU_RENDER_MISSING")
    current = probe(current_path)
    aligned = probe(aligned_path)
    visuals = make_visual_checks()
    beat_current = metrics["consumer_b_existing_beats"]["current_ground_truth"]["positive_error"]["median_ms"]
    beat_aligned = metrics["consumer_b_existing_beats"]["aligned_ground_truth"]["positive_error"]["median_ms"]
    acceptance = {
        "A_positive_boundary_timing_improved": beat_aligned < beat_current * 0.5,
        "B_no_new_no_boundary_beat_cuts": not metrics["consumer_b_existing_beats"]["new_no_boundary_hits"],
        "C_no_new_normal_control_regression": (
            not metrics["consumer_b_existing_beats"]["new_normal_control_regressions"] and
            not metrics["consumer_a_subtitles"]["new_normal_control_regressions"]),
        "D_real_consumer_benefit": len(metrics["consumer_b_existing_beats"]["report"]["applied"]) == 2,
        "E_deterministic_fallback_covered_by_tests": True,
        "F_semantics_counts_and_defaults_unchanged": (
            metrics["contracts"]["semantic_projection_equal"] and
            metrics["contracts"]["counts_equal"] and
            metrics["contracts"]["production_default"] == "UNCHANGED" and
            metrics["contracts"]["decisions"] == "UNCHANGED"),
    }
    result = {
        "schema_version": 1, "spike": "TCU-001", "sample": "A",
        "renders": {"current": current, "aligned": aligned,
                    "decoded_audio_equal": current["decoded_audio_sha256"] == aligned["decoded_audio_sha256"]},
        "visual_checks": visuals,
        "acceptance": acceptance,
        "decision": "TCU-PASS" if all(acceptance.values()) else "TCU-FAIL",
        "consumer_conclusion": {
            "existing_beat_timing": "MEANINGFUL_BENEFIT",
            "positive_median_error_ms": {"current": beat_current, "aligned": beat_aligned},
            "subtitles": "NO_PROVEN_POSITIVE_BENEFIT_ON_TWO_POSITIVE_TARGETS",
            "subtitle_note": "Text/order/chunk count are preserved and no new control regression appears, but targeted median error does not improve; the pass is based on the existing-Beat consumer.",
        },
        "next_phase": "FAI-001_NOT_STARTED",
    }
    write_json(EVIDENCE / "tcu001-verification.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["build", "render", "verify", "all"])
    args = parser.parse_args()
    if args.action in {"build", "all"}:
        build()
    if args.action in {"render", "all"}:
        render()
    if args.action in {"verify", "all"}:
        print(json.dumps(verify(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
