"""Production opt-in consumer: retime existing approved Beats only."""
from __future__ import annotations

import copy

from vnext.phase2.alignment.contracts import AlignedTimingMap, BeatTimingBindings


class ExistingBeatTimingConsumer:
    def __init__(self, store, runtime=None):
        self.store = store
        if runtime is None:
            from vnext.phase2.alignment.runtime import AlignmentRuntime
            runtime = AlignmentRuntime(store)
        self.runtime = runtime

    @staticmethod
    def _anchor_time(aligned: AlignedTimingMap, segment_id: str, offset: int,
                     confidence_threshold: float) -> tuple[int, float] | None:
        chars = {(a.script_span.segment_id, a.script_span.start): a for a in aligned.anchors if a.kind == "CHAR"}
        before, after = chars.get((segment_id, offset - 1)), chars.get((segment_id, offset))
        if not before or not after:
            return None
        confidence = min(before.confidence, after.confidence)
        if confidence < confidence_threshold:
            return None
        return round((before.start_ms + after.start_ms) / 2), confidence

    def apply(self, pid: str, ir: dict, current: list[dict], *, confidence_threshold: float = .65,
              minimum_coverage: float = .85) -> tuple[list[dict], dict]:
        result = copy.deepcopy(current)
        project = self.store.get_project(pid)
        fallback = {"timing_mode": "CURRENT", "fallback_used": project.timing_mode == "ALIGNED_OPT_IN",
                    "alignment_artifact_id": None, "alignment_artifact_sha": None,
                    "engine": None, "engine_version": None, "model": None, "model_sha": None,
                    "coverage": None, "applied": []}
        if project.timing_mode != "ALIGNED_OPT_IN":
            return result, {**fallback, "fallback_used": False, "reason": "PRODUCTION_DEFAULT_CURRENT"}
        runtime_status = self.runtime.status(pid)
        if runtime_status.state != "READY" or not runtime_status.alignment_artifact_id:
            return result, {**fallback, "reason": "ALIGNMENT_RUNTIME_" + runtime_status.state}
        aligned_item = self.store.get_artifact(runtime_status.alignment_artifact_id)
        bindings_item = self.store.latest(pid, "BEAT_TIMING_BINDINGS")
        if not aligned_item or not bindings_item:
            return result, {**fallback, "reason": "ALIGNMENT_OR_BINDINGS_MISSING"}
        if not self.store.is_usable_input(aligned_item["artifact_id"]) or not self.store.is_usable_input(bindings_item["artifact_id"]):
            return result, {**fallback, "reason": "ALIGNMENT_OR_BINDINGS_STALE"}
        try:
            aligned = AlignedTimingMap.model_validate(aligned_item["payload"])
            bindings = BeatTimingBindings.model_validate(bindings_item["payload"])
        except Exception:
            return result, {**fallback, "reason": "ALIGNMENT_OR_BINDINGS_CORRUPT"}
        if aligned.coverage < minimum_coverage or aligned.script_artifact_id != ir["script_artifact_id"]:
            return result, {**fallback, "reason": "COVERAGE_OR_SCRIPT_MISMATCH"}
        beat_ranges = {row["beat_id"]: (row["timing"]["start"], row["timing"]["end"]) for row in result}
        ordered = sorted((start, beat_id, end) for beat_id, (start, end) in beat_ranges.items())
        applied = []
        for binding in bindings.bindings:
            resolved = self._anchor_time(aligned, binding.segment_id, binding.boundary_offset, confidence_threshold)
            at = next((index for index, (_start, beat, _end) in enumerate(ordered)
                       if beat == binding.beat_after_id), None)
            if not resolved or at is None or at == 0:
                continue
            timestamp_ms, confidence = resolved
            prev_start, prev_id, old_end = ordered[at - 1]
            old_start, after_id, after_end = ordered[at]
            new = timestamp_ms / 1000
            if abs(old_end - old_start) > .002 or not (prev_start + .25 < new < after_end - .25):
                continue
            previous = next(row for row in result if row["beat_id"] == prev_id)
            following = next(row for row in result if row["beat_id"] == after_id)
            previous["timing"] = {**previous["timing"], "end": new, "source": "ALIGNED_TIMING_MAP",
                                  "alignment_artifact_id": aligned_item["artifact_id"]}
            following["timing"] = {**following["timing"], "start": new, "source": "ALIGNED_TIMING_MAP",
                                   "alignment_artifact_id": aligned_item["artifact_id"]}
            ordered[at - 1] = (prev_start, prev_id, new)
            ordered[at] = (new, after_id, after_end)
            applied.append({"binding_id": binding.binding_id, "boundary_id": binding.boundary_id,
                            "beat_before_id": prev_id, "beat_after_id": after_id,
                            "old_timestamp_ms": round(old_end * 1000), "new_timestamp_ms": timestamp_ms,
                            "confidence": confidence})
        if not applied:
            return result, {**fallback, "reason": "NO_APPROVED_ANCHOR_RESOLVED"}
        return result, {
            "timing_mode": "ALIGNED", "fallback_used": False,
            "alignment_artifact_id": aligned_item["artifact_id"],
            "alignment_artifact_sha": aligned_item["output_hash"],
            "engine": aligned.engine, "engine_version": aligned.engine_version,
            "model": aligned.model_name, "model_sha": aligned.model_sha256,
            "coverage": aligned.coverage, "alignment_method": aligned.alignment_method,
            "raw_asr_segments_used_as_boundaries": False, "applied": applied,
            "beat_count_before": len(current), "beat_count_after": len(result),
        }
