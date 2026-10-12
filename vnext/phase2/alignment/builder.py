"""Convert whisper.cpp DTW output into a policy-free AlignedTimingMap."""
from __future__ import annotations

import difflib
import re
from collections import defaultdict

from vnext.contracts import utc_now
from vnext.phase2.alignment.contracts import AlignedTimingMap, AlignmentAnchor, ScriptSpan


PUNCTUATION = re.compile(r"[\s，。！？；、,.!?;:：]")
SPECIAL_TOKEN = re.compile(r"^\[_.*_\]$")


def normalize(text: str) -> str:
    return PUNCTUATION.sub("", text)


def _observed(raw: dict) -> tuple[str, list[int], list[float]]:
    chars, times, confidence = [], [], []
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
            confidence.extend([float(token.get("p") or 0)] * len(clean))
    return "".join(chars), times, confidence


def build_map(*, raw: dict, audio_artifact_id: str, audio_sha256: str,
              script_artifact_id: str, script_sha256: str, segments: list[dict],
              identity: dict, raw_alignment_sha256: str, performance: dict) -> AlignedTimingMap:
    normalized = [(row["segment_id"], normalize(row["text"])) for row in segments]
    reference = "".join(text for _sid, text in normalized)
    observed, times, probabilities = _observed(raw)
    matcher = difflib.SequenceMatcher(a=reference, b=observed, autojunk=False)
    mapping: dict[int, int] = {}
    for tag, i1, i2, j1, _j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                mapping[i1 + offset] = j1 + offset

    segment_ranges, cursor = {}, 0
    for segment_id, text in normalized:
        segment_ranges[segment_id] = (cursor, cursor + len(text), text)
        cursor += len(text)
    char_anchors = []
    for segment_id, (start, end, text) in segment_ranges.items():
        for local_offset in range(end - start):
            observed_index = mapping.get(start + local_offset)
            if observed_index is None:
                continue
            timestamp = times[observed_index]
            char_anchors.append(AlignmentAnchor(
                anchor_id=f"{segment_id}-C{local_offset:04d}", kind="CHAR",
                script_span=ScriptSpan(segment_id=segment_id, start=local_offset,
                                       end=local_offset + 1, text=text[local_offset]),
                start_ms=timestamp, end_ms=timestamp,
                confidence=probabilities[observed_index],
                provenance={"source": "TOLERANT_MATCHED_SCRIPT_CHAR_DTW",
                            "raw_asr_segment_boundary_used": False},
            ))
    by_segment = defaultdict(list)
    for anchor in char_anchors:
        by_segment[anchor.script_span.segment_id].append(anchor)
    phrase_anchors = []
    for segment_id, text in normalized:
        rows = by_segment[segment_id]
        if not rows:
            continue
        phrase_anchors.append(AlignmentAnchor(
            anchor_id=f"PHRASE-{segment_id}", kind="PHRASE",
            script_span=ScriptSpan(segment_id=segment_id, start=0, end=len(text), text=text),
            start_ms=rows[0].start_ms, end_ms=max(rows[-1].start_ms, rows[0].start_ms),
            confidence=sum(row.confidence for row in rows) / len(rows),
            provenance={"source": "TOLERANT_TRANSCRIPT_ALIGNMENT_OVER_DTW_TOKENS",
                        "matched_chars": len(rows), "total_chars": len(text),
                        "raw_asr_segment_boundary_used": False},
        ))
    return AlignedTimingMap(
        audio_artifact_id=audio_artifact_id, audio_sha256=audio_sha256,
        script_artifact_id=script_artifact_id, script_sha256=script_sha256,
        alignment_method="POST-TTS ASR TIMING + TRANSCRIPT ALIGNMENT",
        engine=identity["engine"], engine_version=identity["engine_version"],
        engine_binary_sha256=identity["engine_binary_sha256"],
        model_name=identity["model_name"], model_sha256=identity["model_sha256"],
        language=identity["language"], created_at=utc_now(),
        coverage=len(mapping) / len(reference) if reference else 0,
        alignment_config_hash=identity["alignment_config_hash"], cache_key=identity["cache_key"],
        raw_alignment_sha256=raw_alignment_sha256,
        anchors=[*phrase_anchors, *char_anchors], performance=performance,
        provenance={
            "alignment_method": "POST-TTS ASR TIMING + TRANSCRIPT ALIGNMENT",
            "not_method": "TRANSCRIPT-CONDITIONED FORCED ALIGNMENT",
            "approved_script_used_as_decoding_prompt": False,
            "raw_asr_segments_consumed_as_boundaries": False,
            "semantic_policy_owner": "EXTERNAL_APPROVED_BEAT_BINDINGS",
        },
    )
