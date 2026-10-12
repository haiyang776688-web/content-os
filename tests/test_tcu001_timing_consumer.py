from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from vnext.phase2.experimental.aligned_timing_consumer_v1 import (
    aligned_existing_beat_timing,
    aligned_subtitles,
    beat_boundaries,
    boundary_metrics,
    build_aligned_timing_map,
    canonical_sha,
    timeline_boundaries,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/project-brain/creative-spikes/TCU-001-timing-consumer/evidence/ats001-readonly"
FIXTURE = ROOT / "fixtures/tcu001/sample-a"


def load(name: str):
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def sample():
    manifest = load("sample-A.benchmark.json")
    raw_path = EVIDENCE / "whisper-medium-dtw-raw.json"
    aligned = build_aligned_timing_map(
        manifest,
        json.loads(raw_path.read_text(encoding="utf-8")),
        alignment_artifact_hash=hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        source_commit="e79aa07a1d06985237b177c9e65f980ad1aca3f3",
    )
    props = json.loads((FIXTURE / "current-render-props.json").read_text(encoding="utf-8"))
    return manifest, aligned, props


def bindings():
    ground_truth = load("targeted-ground-truth.json")
    beat_ids = {"TG-004": "B-08-02", "TG-007": "B-09-02"}
    result = []
    for case in ground_truth["cases"]:
        if case["boundary_id"] in beat_ids:
            result.append({
                "boundary_id": case["boundary_id"],
                "segment_id": case["segment_id"],
                "beat_after_id": beat_ids[case["boundary_id"]],
                "text_before": case["script_text_before"],
                "text_after": case["script_text_after"],
                "approved": True,
            })
    return result


def test_aligned_map_is_when_only_and_hash_pinned():
    manifest, aligned, _props = sample()
    assert aligned["script_artifact_hash"] == manifest["script_sha256"]
    assert aligned["audio_artifact_hash"] == manifest["audio_sha256"]
    assert aligned["coverage"] > 0.98
    assert len(aligned["phrase_anchors"]) == 9
    assert aligned["provenance"]["raw_asr_segment_boundaries_consumed"] is False
    assert aligned["artifact_hash"] == canonical_sha({k: v for k, v in aligned.items() if k != "artifact_hash"})
    serialized = json.dumps(aligned)
    for forbidden in ("shot_count", "beat_count", "semantic_boundary_decision", "layout_geometry", "animation_policy"):
        assert forbidden not in serialized


def test_aligned_subtitles_preserve_text_order_and_chunk_count():
    manifest, aligned, props = sample()
    current = [c for c in props["clips"] if c["track"] == "SUBTITLE"]
    result, report = aligned_subtitles(current, manifest, aligned)
    assert [c["clip_id"] for c in result] == [c["clip_id"] for c in current]
    assert [c["metadata"]["text"] for c in result] == [c["metadata"]["text"] for c in current]
    assert len(result) == len(current) == 45
    assert report["aligned_chunks"] > 0
    assert report["raw_asr_segments_consumed"] is False


def test_missing_alignment_falls_back_exactly():
    manifest, _aligned, props = sample()
    current = [c for c in props["clips"] if c["track"] == "SUBTITLE"]
    result, report = aligned_subtitles(current, manifest, None)
    assert result == current
    assert report["reason"] == "ALIGNMENT_MISSING"


def test_partial_coverage_falls_back_without_resegmentation():
    manifest, aligned, props = sample()
    partial = copy.deepcopy(aligned)
    partial["text_span_anchors"] = [
        row for row in partial["text_span_anchors"] if row["phrase_id"] != "SEG-04-P01"
    ]
    current = [c for c in props["clips"] if c["track"] == "SUBTITLE"]
    result, report = aligned_subtitles(current, manifest, partial)
    assert len(result) == len(current)
    assert [c["metadata"]["text"] for c in result] == [c["metadata"]["text"] for c in current]
    assert any(row["phrase_id"] == "SEG-04-P01" for row in report["fallback_phrases"])


def test_approved_existing_beat_boundaries_improve_without_count_change():
    manifest, aligned, props = sample()
    ground_truth = load("targeted-ground-truth.json")
    current = [c for c in props["clips"] if c["track"] != "SUBTITLE"]
    result, report = aligned_existing_beat_timing(current, manifest, aligned, bindings())
    current_beats = {c["beat_id"] for c in current if c.get("beat_id")}
    result_beats = {c["beat_id"] for c in result if c.get("beat_id")}
    assert result_beats == current_beats
    assert len(report["applied"]) == 2
    before = boundary_metrics(beat_boundaries(current), ground_truth)
    after = boundary_metrics(beat_boundaries(result), ground_truth)
    assert before["positive_error"]["median_ms"] == 1289
    assert after["positive_error"]["median_ms"] == 194


def test_no_boundary_ranges_gain_no_new_beat_cut():
    manifest, aligned, props = sample()
    ground_truth = load("targeted-ground-truth.json")
    current = [c for c in props["clips"] if c["track"] != "SUBTITLE"]
    result, _report = aligned_existing_beat_timing(current, manifest, aligned, bindings())
    current_rows = boundary_metrics(beat_boundaries(current), ground_truth)["no_boundary"]
    result_rows = boundary_metrics(beat_boundaries(result), ground_truth)["no_boundary"]
    current = {row["case_id"]: set(row["new_or_existing_hits_ms"]) for row in current_rows}
    for row in result_rows:
        assert not set(row["new_or_existing_hits_ms"]) - current[row["case_id"]]


def test_normal_controls_gain_no_new_subtitle_or_beat_boundary():
    manifest, aligned, props = sample()
    controls = load("normal-control-set.json")["controls"]
    current_sub = [c for c in props["clips"] if c["track"] == "SUBTITLE"]
    current_visual = [c for c in props["clips"] if c["track"] != "SUBTITLE"]
    aligned_sub, _ = aligned_subtitles(current_sub, manifest, aligned)
    aligned_visual, _ = aligned_existing_beat_timing(current_visual, manifest, aligned, bindings())
    for current, result in ((current_sub, aligned_sub), (current_visual, aligned_visual)):
        before = timeline_boundaries(current)
        after = timeline_boundaries(result)
        for control in controls:
            old_hits = {x for x in before if control["window_start_ms"] <= x <= control["window_end_ms"]}
            new_hits = {x for x in after if control["window_start_ms"] <= x <= control["window_end_ms"]}
            if not old_hits:
                assert not new_hits
            else:
                assert len(new_hits) <= len(old_hits)
