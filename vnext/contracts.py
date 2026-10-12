"""Canonical contracts. JSON Schema files are generated from these Pydantic models."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Capability(str, Enum):
    VISION = "VISION"
    JSON_SCHEMA = "JSON_SCHEMA"
    TEXT = "TEXT"
    IMAGE_INPUT = "IMAGE_INPUT"
    AUDIO_INPUT = "AUDIO_INPUT"
    VIDEO_INPUT = "VIDEO_INPUT"
    STRUCTURED_OUTPUT = "STRUCTURED_OUTPUT"
    TOOL_CALLING = "TOOL_CALLING"
    REASONING = "REASONING"
    STREAMING = "STREAMING"


class Role(str, Enum):
    RESEARCH = "RESEARCH"
    SCRIPT_PRIMARY = "SCRIPT_PRIMARY"
    SCRIPT_EDITOR = "SCRIPT_EDITOR"
    AUDIT = "AUDIT"
    DIRECTOR = "DIRECTOR"
    MEDIA_RESOLVER = "MEDIA_RESOLVER"
    VOICE = "VOICE"
    VIDEO_QA = "VIDEO_QA"
    ANALYTICS = "ANALYTICS"
    EVOLUTION = "EVOLUTION"


class RoleContract(StrictModel):
    role: Role
    owned_artifact_types: list[str]
    required_capabilities: list[Capability]
    default_worker: str
    prompt_id: str


class ProviderProtocol(str, Enum):
    OPENAI_RESPONSES = "OPENAI_RESPONSES"
    OPENAI_CHAT = "OPENAI_CHAT"
    ANTHROPIC_MESSAGES = "ANTHROPIC_MESSAGES"
    GEMINI_NATIVE = "GEMINI_NATIVE"
    CUSTOM_OPENAI_COMPATIBLE = "CUSTOM_OPENAI_COMPATIBLE"
    CUSTOM_REST = "CUSTOM_REST"
    MOCK = "MOCK"


class WorkerProfile(StrictModel):
    worker_id: str
    display_name: str
    provider: str
    model: str
    protocol: ProviderProtocol
    capabilities: list[Capability]
    endpoint_env: str | None = None
    api_key_env: str | None = None
    model_env: str | None = None


class ContentBlock(StrictModel):
    type: Literal["TEXT", "IMAGE", "AUDIO", "VIDEO", "FILE", "JSON"]
    text: str | None = None
    uri: str | None = None
    mime_type: str | None = None
    json_value: Any | None = None


class ModelMessage(StrictModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[ContentBlock]


class ModelRequest(StrictModel):
    role: Role
    worker_profile: str
    system_prompt: str
    messages: list[ModelMessage]
    content_blocks: list[ContentBlock] = Field(default_factory=list)
    tools: list[dict[str, Any]] = Field(default_factory=list)
    response_schema: dict[str, Any] | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    prompt_version: str


class ModelResult(StrictModel):
    text: str = ""
    structured_output: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    usage: dict[str, Any] = Field(default_factory=dict)
    finish_reason: str = "stop"
    warnings: list[str] = Field(default_factory=list)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)
    raw_response: dict[str, Any] | None = None


class VoiceProfile(StrictModel):
    voice_profile_id: str
    display_name: str
    provider: str
    execution_mode: Literal["LOCAL", "CLOUD", "MOCK"]
    provider_voice_id: str
    voice_type: Literal["BUILT_IN", "CLONED", "LOCAL_CLONED", "REFERENCE_BASED"]
    language: str
    owner: str
    consent_status: Literal["NOT_REQUIRED", "VERIFIED", "PENDING"]
    usage_scope: str
    version: int = Field(ge=1)
    status: Literal["ACTIVE", "INACTIVE", "UNAVAILABLE"]


class ProsodyProfile(StrictModel):
    rate: float = Field(default=1.0, gt=0.25, lt=4)
    pitch: float = Field(default=1.0, gt=0.25, lt=4)
    energy: float = Field(default=1.0, gt=0.0, le=2)
    pauses_ms: int = Field(default=0, ge=0, le=3000)


class VoiceRequest(StrictModel):
    text: str = Field(min_length=1)
    language: str
    voice_profile: str
    prosody: ProsodyProfile = Field(default_factory=ProsodyProfile)
    output_format: Literal["wav", "mp3"] = "wav"
    sample_rate: int = Field(default=24000, ge=8000, le=96000)
    channels: int = Field(default=1, ge=1, le=2)


class Timestamp(StrictModel):
    text: str
    start: float = Field(ge=0)
    end: float = Field(ge=0)


class VoiceArtifact(StrictModel):
    provenance: dict[str, Any] = Field(default_factory=dict)
    voice_artifact_id: str
    provider: str
    model: str
    voice_profile: str
    audio_path: str
    duration: float = Field(ge=0)
    sample_rate: int
    channels: int
    word_timestamps: list[Timestamp] | None = None
    phrase_timestamps: list[Timestamp] | None = None
    phoneme_timestamps: list[Timestamp] | None = None
    status: Literal["READY", "FAILED", "MOCK"]


class ToolRequest(StrictModel):
    tool: Literal["SEARCH", "FETCH_PAGE", "SNAPSHOT", "DOCUMENT_READ", "WEB_SEARCH", "PAGE_FETCH", "SCREENSHOT", "IMAGE_SEARCH", "FILE_READ", "PDF_READ"]
    arguments: dict[str, Any]
    request_id: str


class ToolResult(StrictModel):
    request_id: str
    tool: str
    status: Literal["COMPLETED", "BLOCKED", "FAILED"]
    output: dict[str, Any]
    provenance: dict[str, Any] = Field(default_factory=dict)


class ArtifactDependency(StrictModel):
    artifact_id: str
    output_hash: str


class Artifact(StrictModel):
    provenance: dict[str, Any] = Field(default_factory=dict)
    artifact_id: str
    project_id: str
    artifact_type: str
    revision: int = Field(ge=1)
    created_by_role: str
    worker: str | None = None
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    dependencies: list[ArtifactDependency] = Field(default_factory=list)
    input_hash: str
    output_hash: str
    status: Literal["DRAFT", "READY", "STALE", "DIRTY", "BLOCKED", "FAILED", "APPROVED", "LOCKED"]
    created_at: str
    payload: dict[str, Any]


class ProjectConfig(StrictModel):
    project_id: str
    project_name: str
    topic: str = ""
    content_type: Literal["EXPLAINER", "COMMENTARY", "TUTORIAL"] = "EXPLAINER"
    interface_language: Literal["zh-CN", "en-US"] = "zh-CN"
    content_language: str = "zh-CN"
    subtitle_language: str = "zh-CN"
    character_pack: str | None = None
    style_pack: str | None = None
    element_pack: str | None = None
    voice_profile: str | None = None
    render_profile: str = "preview-1080p"
    timing_mode: Literal["CURRENT", "ALIGNED_OPT_IN"] = "CURRENT"
    privacy_mode: Literal["LOCAL_ONLY", "CLOUD_ALLOWED", "ASK_BEFORE_UPLOAD"] = "LOCAL_ONLY"
    fallback_policy: Literal["DISABLED", "ASK", "AUTO_SAFE"] = "ASK"
    worker_assignments: dict[str, str] = Field(default_factory=dict)
    fallback_workers: list[str] = Field(default_factory=list)
    model_pricing: dict[str, dict[str, float]] = Field(default_factory=dict)
    budget: dict[str, float | None] = Field(default_factory=lambda: {"project": None, "daily": None, "single_run": None})
    @model_validator(mode='after')
    def valid_budget(self):
        if set(self.budget)-{'project','daily','single_run'} or any(v is not None and v<0 for v in self.budget.values()):raise ValueError('INVALID_BUDGET')
        for rates in self.model_pricing.values():
            if not {'input_per_million','output_per_million'}<=rates.keys() or any(v<0 for v in rates.values()):raise ValueError('INVALID_MODEL_PRICING')
        return self
    state: str = "CREATED"
    phase2_enabled: bool = False
    h2_script_artifact_id: str | None = None
    timeline_artifact_id: str | None = None
    created_at: str


class CharacterPack(StrictModel):
    character_id: str
    version: str
    master: dict[str, Any]
    actions: list[dict[str, Any]]
    action_semantics: dict[str, Any]
    constraints: dict[str, Any]
    calibration: dict[str, Any]
    default_style: str | None = None
    recommended_voice_profiles: list[str] = Field(default_factory=list)
    assets: list[dict[str, Any]]


class StylePack(StrictModel):
    style_id: str
    version: str
    colors: dict[str, Any]
    typography: dict[str, Any]
    subtitle_style: dict[str, Any]
    motion_language: dict[str, Any]
    composition_rules: dict[str, Any]
    template_pack: str | None = None


class ElementPack(StrictModel):
    element_pack_id: str
    version: str
    elements: list[dict[str, Any]]


class MediaAsset(StrictModel):
    asset_id: str
    project_id: str
    type: Literal["IMAGE", "VIDEO", "AUDIO", "SCREENSHOT", "DOCUMENT", "GENERATED"]
    original_path: str
    display_name: str | None = None
    hash: str
    duration: float | None = None
    resolution: str | None = None
    fps: float | None = None
    codec: str | None = None
    created_at: str
    source: str
    owner: str
    license: str = "UNKNOWN"
    cloud_policy: Literal["LOCAL_ONLY", "CLOUD_ALLOWED", "ASK_BEFORE_UPLOAD"] = "LOCAL_ONLY"
    status: Literal["ONLINE", "OFFLINE", "MISSING", "RELINKED"] = "ONLINE"
    proxy_path: str | None = None
    thumbnail_path: str | None = None


class MediaSelection(StrictModel):
    media_need: str
    mode: Literal["AUTO", "SUGGEST", "MANUAL", "LOCKED"] = "SUGGEST"
    candidate_asset_ids: list[str] = Field(default_factory=list)
    selected_asset_id: str | None = None
    status: Literal["SUGGESTED", "SELECTED", "ASSET_GAP", "LOCKED"]
    rationale: str


class VirtualClip(StrictModel):
    source_asset_id: str
    source_in: float = Field(ge=0)
    source_out: float = Field(gt=0)


class DirectorBeat(StrictModel):
    beat_id: str
    purpose: str
    visual_focus: str
    visual_form: str
    character_presence: str
    character_intent: str
    media_need: str
    density: str
    tempo: str
    motion_intent: str
    reveal_order: list[str]
    keyword: str


class DirectorPlan(StrictModel):
    script_artifact_id: str
    beats: list[DirectorBeat]


class EDTClip(StrictModel):
    clip_id: str
    scene_id: str | None = None
    beat_id: str | None = None
    ir_node_id: str | None = None
    origin: str = "MANUAL"
    edit_source: str = "HUMAN"
    pattern_id: str | None = None
    track: Literal["VIDEO", "MEDIA", "CHARACTER", "ELEMENT", "TEXT", "SUBTITLE", "VOICE", "BGM", "SFX"]
    asset_id: str | None = None
    source_in: float = Field(default=0, ge=0)
    source_out: float = Field(default=1, gt=0)
    timeline_in: float = Field(default=0, ge=0)
    timeline_out: float = Field(default=1, gt=0)
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0.5, "y": 0.5})
    scale: float = Field(default=1, gt=0)
    crop: dict[str, float] = Field(default_factory=dict)
    opacity: float = Field(default=1, ge=0, le=1)
    motion: dict[str, Any] = Field(default_factory=dict)
    reveal: dict[str, Any] = Field(default_factory=dict)
    locked: bool = False
    hidden: bool = False
    muted: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def valid_ranges(self):
        if self.source_out <= self.source_in or self.timeline_out <= self.timeline_in:
            raise ValueError("Clip out must exceed in")
        return self


class EDT(StrictModel):
    edt_id: str
    schema_version: int = Field(default=1, ge=1, le=2)
    canvas_color: str = Field(default='#ffffff',pattern=r'^#[0-9a-fA-F]{6}$')
    foreground_color: str = Field(default='#111111',pattern=r'^#[0-9a-fA-F]{6}$')
    typography_profile_id: str | None = None
    typography_profile_hash: str | None = None
    project_id: str
    revision: int = Field(ge=1)
    fps: int = Field(default=30, ge=1, le=120)
    width: int = Field(default=1920, gt=0)
    height: int = Field(default=1080, gt=0)
    tracks: list[str] = Field(default_factory=lambda: ["MEDIA", "CHARACTER", "TEXT", "SUBTITLE", "VOICE"])
    clips: list[EDTClip] = Field(default_factory=list)
    markers: list[dict[str, Any]] = Field(default_factory=list)
    source_artifacts: list[str] = Field(default_factory=list)
    timing_provenance: dict[str, Any] = Field(default_factory=dict)


class Job(StrictModel):
    job_id: str
    request_id: str
    project_id: str
    kind: str
    state: Literal["QUEUED", "RUNNING", "WAITING", "RETRYING", "BLOCKED", "FAILED", "COMPLETED", "CANCELLED", "STALE"]
    artifact_id: str | None = None
    idempotency_key: str
    retries: int = 0
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    target_revision: str | None = None
    stage: str | None = None
    progress: float | None = Field(default=None, ge=0, le=1)


class RuleRecord(StrictModel):
    rule_id: str
    lifecycle: Literal["CREATED", "ACTIVE", "AMENDED", "DEPRECATED"]
    text: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    owner: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    related_error: str | None = None
    exceptions: list[str] = Field(default_factory=list)


class ErrorCandidate(StrictModel):
    summary: str = Field(min_length=1)
    detail: str = ""
    root_cause: Literal["DATA", "MODEL", "TOOL", "PROCESS", "HUMAN", "UNKNOWN"] = "UNKNOWN"
    artifact_id: str | None = None
    submitted_by_role: str


SCHEMAS = {
    "EDTCLIP_SCHEMA": EDTClip,
    "MEDIAASSET_SCHEMA": MediaAsset,
    "VIRTUALCLIP_SCHEMA": VirtualClip,
    "MODELREQUEST_SCHEMA": ModelRequest,
    "CONTENTBLOCK_SCHEMA": ContentBlock,
    "ROLE_CONTRACT": RoleContract,
    "MODEL_GATEWAY_CONTRACT": ModelRequest,
    "MODEL_RESULT_SCHEMA": ModelResult,
    "VOICE_GATEWAY_CONTRACT": VoiceRequest,
    "VOICE_ARTIFACT_SCHEMA": VoiceArtifact,
    "TOOL_GATEWAY_CONTRACT": ToolRequest,
    "ARTIFACT_SCHEMA": Artifact,
    "PROJECT_CONFIG_SCHEMA": ProjectConfig,
    "CHARACTER_PACK_SCHEMA": CharacterPack,
    "STYLE_PACK_SCHEMA": StylePack,
    "ELEMENT_PACK_SCHEMA": ElementPack,
    "VOICE_PROFILE_SCHEMA": VoiceProfile,
    "MEDIA_ASSET_SCHEMA": MediaAsset,
    "MEDIA_SELECTION_SCHEMA": MediaSelection,
    "DIRECTOR_PLAN_SCHEMA": DirectorPlan,
    "EDT_SCHEMA": EDT,
    "JOB_SCHEMA": Job,
    "RULE_SCHEMA": RuleRecord,
    "ERROR_CANDIDATE_SCHEMA": ErrorCandidate,
}
