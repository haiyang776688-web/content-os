"""Strict renderer-neutral contracts for FAI-001.

These contracts locate approved Script spans in audio.  They intentionally do
not contain Beat/Shot creation policy, Visual Jobs, geometry, or animation.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from vnext.contracts import StrictModel


AlignmentRuntimeState = Literal[
    "NOT_REQUIRED", "NOT_AVAILABLE", "QUEUED", "RUNNING", "READY",
    "FAILED", "CANCELLED", "STALE", "FALLBACK",
]


class AlignmentConfig(StrictModel):
    language: str = "zh"
    engine: Literal["whisper.cpp"] = "whisper.cpp"
    engine_version: str = "1.9.1"
    model_name: str = "ggml-medium.bin"
    model_sha256: str = "6c14d5adee5f86394037b4e4e8b59f1673b6cee10e3cf0b11bbdbee79c156208"
    dtw_preset: str = "medium"
    flash_attention: bool = False
    vad: bool = False
    minimum_coverage: float = Field(default=0.85, ge=0, le=1)
    anchor_confidence: float = Field(default=0.65, ge=0, le=1)
    timeout_seconds: int = Field(default=900, ge=10, le=7200)


class ScriptSpan(StrictModel):
    segment_id: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered(self):
        if self.end <= self.start:
            raise ValueError("SCRIPT_SPAN_INVALID")
        return self


class AlignmentAnchor(StrictModel):
    anchor_id: str
    kind: Literal["CHAR", "PHRASE"]
    script_span: ScriptSpan
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    confidence: float = Field(ge=0, le=1)
    provenance: dict[str, Any]

    @model_validator(mode="after")
    def valid_time(self):
        if self.end_ms < self.start_ms:
            raise ValueError("ANCHOR_TIME_INVALID")
        return self


class AlignedTimingMap(StrictModel):
    schema_version: Literal[1] = 1
    audio_artifact_id: str
    audio_sha256: str
    script_artifact_id: str
    script_sha256: str
    alignment_method: Literal["POST-TTS ASR TIMING + TRANSCRIPT ALIGNMENT"]
    engine: Literal["whisper.cpp"]
    engine_version: str
    engine_binary_sha256: str
    model_name: str
    model_sha256: str
    language: str
    created_at: str
    coverage: float = Field(ge=0, le=1)
    alignment_config_hash: str
    cache_key: str
    raw_alignment_sha256: str
    anchors: list[AlignmentAnchor]
    performance: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any]

    @model_validator(mode="after")
    def policy_free(self):
        serialized = self.model_dump()
        forbidden = {
            "shot_count", "beat_count", "visual_job", "shot_type",
            "semantic_boundary_decision", "layout_geometry", "animation_policy",
        }
        def walk(value):
            if isinstance(value, dict):
                if forbidden & set(value):
                    raise ValueError("ALIGNMENT_CREATIVE_POLICY_FORBIDDEN")
                for item in value.values():
                    walk(item)
            elif isinstance(value, list):
                for item in value:
                    walk(item)
        walk(serialized)
        if self.provenance.get("raw_asr_segments_consumed_as_boundaries") is not False:
            raise ValueError("RAW_ASR_SEMANTIC_POLICY_FORBIDDEN")
        return self


class BeatTimingBinding(StrictModel):
    binding_id: str
    boundary_id: str
    segment_id: str
    beat_after_id: str
    boundary_offset: int = Field(gt=0)
    text_before: str = Field(min_length=1)
    text_after: str = Field(min_length=1)
    approved: Literal[True]
    approved_by: str = Field(min_length=1)
    approval_source: str = Field(min_length=1)


class BeatTimingBindings(StrictModel):
    schema_version: Literal[1] = 1
    script_artifact_id: str
    bindings: list[BeatTimingBinding]


class AlignmentStatus(StrictModel):
    state: AlignmentRuntimeState
    effective_state: Literal["CURRENT", "ALIGNED"]
    requested_mode: Literal["CURRENT", "ALIGNED_OPT_IN"]
    fallback_used: bool
    reason: str | None = None
    alignment_artifact_id: str | None = None
    alignment_artifact_sha: str | None = None
    cache_key: str | None = None
    job: dict[str, Any] | None = None
    model: dict[str, Any]
    gui_actions: list[Literal["INSTALL_MODEL", "ENQUEUE", "CANCEL", "RETRY", "RECOMPUTE"]] = Field(default_factory=list)
