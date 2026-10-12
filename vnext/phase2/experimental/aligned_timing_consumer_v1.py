"""TCU-001 experimental consumers for trusted post-TTS alignment.

The artifact in this module answers only WHEN an approved Script span occurs.
It never creates/removes a Beat, subtitle chunk or Shot and it never consumes
raw ASR segment boundaries as semantic policy.  Production ``AudioClock`` is
deliberately untouched; callers must opt into this experimental projection.
"""
from __future__ import annotations

import copy
import difflib
import hashlib
import json
import re
import statistics
from collections import defaultdict
from typing import Any


PUNCTUATION = re.compile(r"[\s，。！？；、,.!?;:：]")
SPECIAL_TOKEN = re.compile(r"^\[_.*_\]$")
FORBIDDEN_ARTIFACT_KEYS = {
    "shot_count", "beat_count", "semantic_boundary_decision", "layout_geometry",
    "animation_policy", "x", "y", "width", "height", "font_size", "css",
}


def canonical_sha(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def normalize(text: str) -> str:
    return PUNCTUATION.sub("", text)


def _percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = (len(ordered) - 1) * q
    lo = int(rank)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (rank - lo)


def _observed_timeline(raw: dict) -> tuple[str, list[int], list[float]]:
    chars: list[str] = []
    times: list[int] = []
    confidences: list[float] = []
    for segment in raw.get("transcription", []):
        for token in segment.get("tokens", []):
            text = token.get("text", "")
            if SPECIAL_TOKEN.match(text) or token.get("t_dtw", -1) < 0:
                continue
            clean = normalize(text)
            if not clean:
                continue
            chars.extend(clean)
            times.extend([int(token["t_dtw"]) * 10] * len(clean))
            confidences.extend([float(token.get("p") or 0.0)] * len(clean))
    return "".join(chars), times, confidences


def _tolerant_mapping(reference: str, observed: str) -> dict[int, int]:
    mapping: dict[int, int] = {}
    matcher = difflib.SequenceMatcher(a=reference, b=observed, autojunk=False)
    for tag, i1, i2, j1, _j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                mapping[i1 + offset] = j1 + offset
    return mapping


def _check_artifact_shape(value: Any) -> None:
    if isinstance(value, dict):
        conflict = set(value) & FORBIDDEN_ARTIFACT_KEYS
        if conflict:
            raise ValueError("ALIGNED_TIMING_SEMANTIC_FIELD_FORBIDDEN:" + ",".join(sorted(conflict)))
        for item in value.values():
            _check_artifact_shape(item)
    elif isinstance(value, list):
        for item in value:
            _check_artifact_shape(item)


def build_aligned_timing_map(
    manifest: dict,
    raw_alignment: dict,
    *,
    alignment_artifact_hash: str,
    source_commit: str,
) -> dict:
    """Build renderer-neutral phrase and text-span timing without semantic cuts."""
    phrases = manifest["phrases"]
    reference = "".join(normalize(item["text"]) for item in phrases)
    observed, observed_times, observed_confidence = _observed_timeline(raw_alignment)
    mapping = _tolerant_mapping(reference, observed)

    global_offsets: dict[str, tuple[int, int]] = {}
    cursor = 0
    for phrase in phrases:
        size = len(normalize(phrase["text"]))
        global_offsets[phrase["phrase_id"]] = (cursor, cursor + size)
        cursor += size

    char_anchors: list[dict] = []
    for phrase in phrases:
        phrase_start, phrase_end = global_offsets[phrase["phrase_id"]]
        local_text = normalize(phrase["text"])
        for local_index, char in enumerate(local_text):
            reference_index = phrase_start + local_index
            observed_index = mapping.get(reference_index)
            if observed_index is None:
                continue
            char_anchors.append({
                "anchor_id": f"{phrase['phrase_id']}-C{local_index:03d}",
                "phrase_id": phrase["phrase_id"],
                "segment_id": phrase["segment_id"],
                "text": char,
                "start_offset": local_index,
                "end_offset": local_index + 1,
                "start_ms": observed_times[observed_index],
                "end_ms": observed_times[observed_index],
                "confidence": observed_confidence[observed_index],
                "provenance": "TOLERANT_MATCHED_SCRIPT_CHAR_DTW",
                "alignment_method": "POST-TTS ASR TIMING + TRANSCRIPT ALIGNMENT",
                "alignment_artifact_hash": alignment_artifact_hash,
            })

    by_phrase: dict[str, list[dict]] = defaultdict(list)
    for anchor in char_anchors:
        by_phrase[anchor["phrase_id"]].append(anchor)

    phrase_anchors: list[dict] = []
    for index, phrase in enumerate(phrases):
        anchors = by_phrase[phrase["phrase_id"]]
        clean_size = len(normalize(phrase["text"]))
        coverage = len(anchors) / clean_size if clean_size else 0.0
        resolved = bool(anchors)
        start_ms = anchors[0]["start_ms"] if resolved else None
        if index + 1 < len(phrases) and by_phrase[phrases[index + 1]["phrase_id"]]:
            end_ms = by_phrase[phrases[index + 1]["phrase_id"]][0]["start_ms"]
        elif resolved:
            end_ms = min(round(manifest["audio_duration_seconds"] * 1000),
                         max(anchors[-1]["start_ms"] + 180,
                             round(float(phrase["end_seconds"]) * 1000)))
        else:
            end_ms = None
        phrase_anchors.append({
            "anchor_id": f"PHRASE-{phrase['phrase_id']}",
            "phrase_id": phrase["phrase_id"],
            "segment_id": phrase["segment_id"],
            "text": phrase["text"],
            "start_ms": start_ms,
            "end_ms": end_ms,
            "confidence": statistics.fmean(a["confidence"] for a in anchors) if anchors else 0.0,
            "coverage": coverage,
            "resolved": resolved,
            "provenance": "TOLERANT_TRANSCRIPT_ALIGNMENT_OVER_DTW_TOKENS",
            "alignment_method": "POST-TTS ASR TIMING + TRANSCRIPT ALIGNMENT",
            "alignment_artifact_hash": alignment_artifact_hash,
        })

    artifact = {
        "schema_version": 1,
        "artifact_type": "ALIGNED_TIMING_MAP_EXPERIMENT",
        "script_artifact_hash": manifest["script_sha256"],
        "audio_artifact_hash": manifest["audio_sha256"],
        "duration_ms": round(manifest["audio_duration_seconds"] * 1000),
        "phrase_anchors": phrase_anchors,
        "text_span_anchors": char_anchors,
        "coverage": len(mapping) / len(reference) if reference else 0.0,
        "provenance": {
            "alignment_method": "POST-TTS ASR TIMING + TRANSCRIPT ALIGNMENT",
            "alignment_artifact_hash": alignment_artifact_hash,
            "source_commit": source_commit,
            "approved_script_used_as_decoding_prompt": False,
            "raw_asr_segment_boundaries_consumed": False,
            "semantic_policy": "EXTERNAL_APPROVED_ANCHORS_ONLY",
        },
    }
    _check_artifact_shape(artifact)
    artifact["artifact_hash"] = canonical_sha(artifact)
    return artifact


def _char_lookup(aligned_map: dict) -> dict[tuple[str, int], dict]:
    return {(a["phrase_id"], a["start_offset"]): a for a in aligned_map["text_span_anchors"]}


def _phrase_for_time(manifest: dict, seconds: float) -> dict | None:
    phrases = manifest["phrases"]
    for index, phrase in enumerate(phrases):
        start = float(phrase["start_seconds"])
        end = float(phrase["end_seconds"])
        # Half-open ranges are important: a clip at 11.04 belongs to SEG-02,
        # not the phrase that ended at 11.04.
        if start - 0.000001 <= seconds < end - 0.000001:
            return phrase
        if index == len(phrases) - 1 and abs(seconds - end) <= 0.000001:
            return phrase
    return None


def aligned_subtitles(
    current_clips: list[dict],
    manifest: dict,
    aligned_map: dict | None,
    *,
    confidence_threshold: float = 0.65,
    coverage_threshold: float = 0.85,
    max_boundary_shift_ms: int = 250,
) -> tuple[list[dict], dict]:
    """Retime existing chunks only; unresolved phrases fall back as a unit."""
    original = copy.deepcopy(current_clips)
    if not aligned_map:
        return original, {"mode": "CURRENT_FALLBACK", "reason": "ALIGNMENT_MISSING", "fallback_phrases": len(manifest["phrases"])}
    phrase_rows = {a["phrase_id"]: a for a in aligned_map["phrase_anchors"]}
    chars = _char_lookup(aligned_map)
    grouped: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    for index, clip in enumerate(original):
        phrase = _phrase_for_time(manifest, float(clip["timeline_in"]))
        if phrase:
            grouped[phrase["phrase_id"]].append((index, clip))

    fallback: list[dict] = []
    aligned_count = 0
    for phrase in manifest["phrases"]:
        pairs = grouped.get(phrase["phrase_id"], [])
        if not pairs:
            continue
        row = phrase_rows.get(phrase["phrase_id"])
        clean_phrase = normalize(phrase["text"])
        offsets: list[int] = []
        cursor = 0
        valid = bool(row and row["resolved"] and row["coverage"] >= coverage_threshold and
                     row["confidence"] >= confidence_threshold)
        for _index, clip in pairs:
            chunk = normalize(clip["metadata"]["text"])
            found = clean_phrase.find(chunk, cursor)
            if found < 0:
                valid = False
                break
            offsets.append(found)
            cursor = found + len(chunk)
        current_boundaries = [round(float(clip["timeline_in"]) * 1000) for _index, clip in pairs]
        current_boundaries.append(round(float(pairs[-1][1]["timeline_out"]) * 1000))
        proposed: list[int | None] = []
        if valid:
            for offset in offsets:
                anchor = chars.get((phrase["phrase_id"], offset))
                if not anchor or anchor["confidence"] < confidence_threshold:
                    proposed.append(None)
                    continue
                if offset:
                    before = chars.get((phrase["phrase_id"], offset - 1))
                    if not before or before["confidence"] < confidence_threshold:
                        proposed.append(None)
                        continue
                    proposed.append(round((before["start_ms"] + anchor["start_ms"]) / 2))
                else:
                    proposed.append(int(anchor["start_ms"]))
            proposed.append(int(row["end_ms"]) if row.get("end_ms") is not None else None)
        if not valid:
            fallback.append({
                "phrase_id": phrase["phrase_id"],
                "reason": "MISSING_LOW_CONFIDENCE_OR_EXCESSIVE_SHIFT",
            })
            continue
        boundaries: list[int] = []
        fallback_positions: list[int] = []
        for position, candidate in enumerate(proposed):
            current = current_boundaries[position]
            if candidate is None or abs(candidate - current) > max_boundary_shift_ms:
                boundaries.append(current)
                fallback_positions.append(position)
            else:
                boundaries.append(candidate)
        if not all(boundaries[i + 1] - boundaries[i] >= 80 for i in range(len(boundaries) - 1)):
            boundaries = current_boundaries
            fallback_positions = list(range(len(boundaries)))
        if fallback_positions:
            fallback.append({
                "phrase_id": phrase["phrase_id"],
                "reason": "BOUNDARY_LEVEL_DETERMINISTIC_FALLBACK",
                "positions": fallback_positions,
            })
        for position, (index, clip) in enumerate(pairs):
            updated = original[index]
            changed = boundaries[position] != current_boundaries[position] or boundaries[position + 1] != current_boundaries[position + 1]
            updated["timeline_in"] = boundaries[position] / 1000
            updated["timeline_out"] = boundaries[position + 1] / 1000
            updated["source_out"] = updated["timeline_out"] - updated["timeline_in"]
            if changed:
                updated.setdefault("metadata", {})["timing_consumer"] = "ALIGNED_TIMING_CONSUMER_V1"
                updated["metadata"]["timing_source"] = "ALIGNED_TIMING_MAP_EXPERIMENT"
                updated["metadata"]["alignment_artifact_hash"] = aligned_map["artifact_hash"]
                aligned_count += 1
    return original, {
        "mode": "ALIGNED_WITH_DETERMINISTIC_FALLBACK",
        "aligned_chunks": aligned_count,
        "total_chunks": len(current_clips),
        "fallback_phrases": fallback,
        "text_and_chunk_count_preserved": [c["metadata"]["text"] for c in original] == [c["metadata"]["text"] for c in current_clips],
        "raw_asr_segments_consumed": False,
    }


def resolve_approved_anchor(aligned_map: dict, manifest: dict, binding: dict) -> dict | None:
    if not binding.get("approved"):
        return None
    phrase = next((p for p in manifest["phrases"] if p["segment_id"] == binding["segment_id"]), None)
    if not phrase:
        return None
    clean = normalize(phrase["text"])
    left = normalize(binding["text_before"])
    right = normalize(binding["text_after"])
    needle = left + right
    hits = [m.start() for m in re.finditer(re.escape(needle), clean)]
    if len(hits) != 1:
        return None
    position = hits[0] + len(left)
    lookup = _char_lookup(aligned_map)
    before = lookup.get((phrase["phrase_id"], position - 1))
    after = lookup.get((phrase["phrase_id"], position))
    if not before or not after:
        return None
    confidence = min(before["confidence"], after["confidence"])
    return {
        "boundary_id": binding["boundary_id"],
        "segment_id": binding["segment_id"],
        "beat_after_id": binding["beat_after_id"],
        "timestamp_ms": round((before["start_ms"] + after["start_ms"]) / 2),
        "confidence": confidence,
        "source": "APPROVED_SCRIPT_ANCHOR_ALIGNED_TO_DTW",
    }


def aligned_existing_beat_timing(
    current_clips: list[dict],
    manifest: dict,
    aligned_map: dict | None,
    approved_bindings: list[dict],
    *,
    confidence_threshold: float = 0.65,
) -> tuple[list[dict], dict]:
    """Move only boundaries between already-existing Beats.

    The binding is semantic policy supplied by a human-approved dataset.  The
    alignment merely supplies its timestamp.  Missing/weak anchors leave the
    original segment untouched.
    """
    result = copy.deepcopy(current_clips)
    if not aligned_map:
        return result, {"mode": "CURRENT_FALLBACK", "reason": "ALIGNMENT_MISSING", "applied": []}

    beat_ranges: dict[str, tuple[float, float]] = {}
    for beat_id in sorted({c.get("beat_id") for c in result if c.get("beat_id")}):
        selected = [c for c in result if c.get("beat_id") == beat_id]
        beat_ranges[beat_id] = (min(c["timeline_in"] for c in selected), max(c["timeline_out"] for c in selected))

    applied: list[dict] = []
    fallback: list[dict] = []
    for binding in approved_bindings:
        anchor = resolve_approved_anchor(aligned_map, manifest, binding)
        if not anchor or anchor["confidence"] < confidence_threshold:
            fallback.append({"boundary_id": binding["boundary_id"], "reason": "ANCHOR_UNRESOLVED_OR_LOW_CONFIDENCE"})
            continue
        after_id = binding["beat_after_id"]
        ordered = sorted((start, beat_id, end) for beat_id, (start, end) in beat_ranges.items())
        at = next((i for i, (_start, beat_id, _end) in enumerate(ordered) if beat_id == after_id), None)
        if at is None or at == 0:
            fallback.append({"boundary_id": binding["boundary_id"], "reason": "BEAT_NOT_FOUND"})
            continue
        prev_start, prev_id, old_boundary = ordered[at - 1]
        after_start, _after_id, after_end = ordered[at]
        new_boundary = anchor["timestamp_ms"] / 1000
        if abs(old_boundary - after_start) > 0.002 or not (prev_start + 0.25 < new_boundary < after_end - 0.25):
            fallback.append({"boundary_id": binding["boundary_id"], "reason": "BOUNDARY_RANGE_INVALID"})
            continue
        for clip in result:
            beat_id = clip.get("beat_id")
            if beat_id not in (prev_id, after_id):
                continue
            old_start, old_end = beat_ranges[beat_id]
            new_start, new_end = ((old_start, new_boundary) if beat_id == prev_id else (new_boundary, old_end))
            old_duration = old_end - old_start
            def project(value: float) -> float:
                fraction = (value - old_start) / old_duration if old_duration else 0.0
                return new_start + fraction * (new_end - new_start)
            clip["timeline_in"] = project(float(clip["timeline_in"]))
            clip["timeline_out"] = project(float(clip["timeline_out"]))
            if clip["track"] not in ("VOICE", "VIDEO"):
                clip["source_out"] = clip["timeline_out"] - clip["timeline_in"]
            clip.setdefault("metadata", {})["timing_consumer"] = "ALIGNED_TIMING_CONSUMER_V1"
            clip["metadata"]["approved_anchor_id"] = binding["boundary_id"]
        beat_ranges[prev_id] = (prev_start, new_boundary)
        beat_ranges[after_id] = (new_boundary, after_end)
        applied.append({
            **anchor,
            "beat_before_id": prev_id,
            "old_timestamp_ms": round(old_boundary * 1000),
            "new_timestamp_ms": anchor["timestamp_ms"],
        })
    return result, {
        "mode": "ALIGNED_EXISTING_BEATS_ONLY",
        "applied": applied,
        "fallback": fallback,
        "beat_count_preserved": True,
        "raw_asr_segments_consumed": False,
    }


def boundary_metrics(boundaries_ms: list[int], ground_truth: dict) -> dict:
    positive = []
    no_boundary = []
    for case in ground_truth["cases"]:
        if case["verdict"] == "BOUNDARY":
            target = int(case["correct_boundary_timestamp_ms"])
            nearest = min(boundaries_ms, key=lambda value: abs(value - target))
            positive.append({
                "case_id": case["boundary_id"], "target_ms": target,
                "nearest_ms": nearest, "absolute_error_ms": abs(nearest - target),
            })
        else:
            window = case["forbidden_boundary_range"]
            hits = [value for value in boundaries_ms if window["start_ms"] <= value <= window["end_ms"]]
            no_boundary.append({"case_id": case["boundary_id"], "new_or_existing_hits_ms": hits})
    errors = [row["absolute_error_ms"] for row in positive]
    return {
        "positive": positive,
        "positive_error": {
            "n": len(errors),
            "median_ms": statistics.median(errors) if errors else None,
            "p90_ms": _percentile(errors, 0.90),
            "max_ms": max(errors) if errors else None,
        },
        "no_boundary": no_boundary,
    }


def timeline_boundaries(clips: list[dict], *, track: str | None = None) -> list[int]:
    selected = [c for c in clips if track is None or c.get("track") == track]
    return sorted({round(float(c["timeline_in"]) * 1000) for c in selected if float(c["timeline_in"]) > 0})


def beat_boundaries(clips: list[dict]) -> list[int]:
    """Return only existing Beat starts, excluding per-element reveal timing.

    A Beat may contain several visual clips whose entrances are staggered.  Those
    entrances are animation timing, not semantic Beat boundaries, so the TCU
    evaluation keeps them out of the Beat-boundary metric.
    """
    starts: dict[str, float] = {}
    for clip in clips:
        beat_id = clip.get("beat_id")
        if not beat_id:
            continue
        starts[beat_id] = min(starts.get(beat_id, float("inf")), float(clip["timeline_in"]))
    return sorted(round(value * 1000) for value in starts.values() if value > 0)
