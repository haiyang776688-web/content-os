from __future__ import annotations

from typing import Any, Literal
from pydantic import Field, model_validator
from vnext.contracts import StrictModel


class WritingRule(StrictModel):
    rule_id: str
    name: str
    scope: str
    priority: int = 50
    severity: Literal['BLOCKER', 'WARNING', 'INFO'] = 'WARNING'
    hard_or_soft: Literal['HARD', 'SOFT'] = 'SOFT'
    applies_to: list[str] = Field(default_factory=list)
    text: str
    examples: list[str] = Field(default_factory=list)
    exceptions: list[str] = Field(default_factory=list)
    version: str = '1'
    source: str = 'SYSTEM'


class RuleSet(StrictModel):
    set_id: str
    version: str = '1'
    rules: list[WritingRule]


class HookRuleSet(StrictModel):
    hook_type: Literal['CONTRAST','SURPRISE','QUESTION','DIRECT_VALUE','PROBLEM','RESULT_FIRST','CHANGE_ALERT']
    max_duration: float = Field(default=8, gt=0)
    max_sentence_count: int = Field(default=2, ge=1)
    information_gap: str = ''
    specificity: str = 'Specific and source-bound'
    promise: str = 'Deliver in this script'
    forbidden_patterns: list[str] = Field(default_factory=lambda: ['FABRICATED_NUMBER', 'UNSUPPORTED_PROMISE'])


class RetentionRuleSet(StrictModel):
    version: str = '1'
    information_change: str = 'Change when meaning changes'
    open_loop: str = 'Only when there is a payoff'
    payoff: str = 'Close the promise'
    visual_refresh: str = 'Follow semantic beats'
    density_change: str = 'Primary before supporting details'
    question_answer: str = 'Bind questions to answers'
    pattern_interrupt: str = 'Purposeful only'
    section_transition: str = 'Narrative function'


class EditorialVoiceProfile(StrictModel):
    profile_id: str
    version: str = '1'
    tone: str = 'Clear, rational, approachable'
    formality: str = 'Conversational'
    sentence_length: str = 'Short spoken clauses'
    humor: str = 'Restrained'
    technical_density: str = 'Explain necessary jargon'
    directness: str = 'Direct'
    slang: str = 'Limited'
    emoji_policy: str = 'None in spoken script'
    rhetorical_question_frequency: str = 'Low'
    first_person_style: str = 'Companion'
    forbidden_expressions: list[str] = Field(default_factory=list)


class SkillLayer(StrictModel):
    skill_id: str
    version: str = '1'
    layer: Literal['CONSTITUTION','SYSTEM','ROLE','PROJECT','CHARACTER_STYLE','RUN']
    rules: list[WritingRule] = Field(default_factory=list)


class EffectiveSkillSnapshot(StrictModel):
    role: str
    skill_versions: list[dict]
    resolution_order: list[str]
    rules: list[WritingRule]
    overrides: list[dict] = Field(default_factory=list)
    hook_rule_set: dict | None = None
    retention_rule_set: dict | None = None
    editorial_voice: dict | None = None
    rule: dict | None = None


from vnext.phase2.hardening.contracts import ClaimUnit


class Source(StrictModel):
    source_id: str = Field(pattern=r'^[A-Za-z0-9_-]+$')
    source_type: Literal['WEB','USER_DOCUMENT','LOCAL_FILE','SCREENSHOT','MANUAL','API']
    title: str = Field(min_length=1)
    url: str | None = None
    file_id: str | None = None
    retrieved_at: str
    publisher: str = ''
    date: str = ''
    snapshot: str = ''
    excerpt: str = Field(min_length=1)
    status: Literal['AVAILABLE','UNVERIFIED','RETRACTED'] = 'AVAILABLE'
    content: str = ''
    pages: dict[str,str] = Field(default_factory=dict)
    transcript: list[dict] = Field(default_factory=list)
    duration: float | None = Field(default=None,gt=0)
    trust: Literal['UNTRUSTED_SOURCE_DATA'] = 'UNTRUSTED_SOURCE_DATA'
    entities: list[str] = Field(default_factory=list)


class Fact(StrictModel):
    evidence_ids: list[str] = Field(default_factory=list)
    fact_id: str = Field(pattern=r'^[A-Za-z0-9_-]+$')
    statement: str = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)
    support_status: Literal['SUPPORTED','PARTIAL','UNSUPPORTED']
    confidence: float = Field(ge=0, le=1)
    time_scope: str = ''
    entity: str = ''
    notes: str = ''


class FactPack(StrictModel):
    facts: list[Fact]


class ScriptSegment(StrictModel):
    segment_id: str
    text: str = Field(min_length=1)
    claim: bool = False
    fact_ids: list[str] = Field(default_factory=list)


class BoundScript(StrictModel):
    contract_version: int = Field(default=1,ge=1,le=2)
    claim_units: list[ClaimUnit] = Field(default_factory=list)
    text: str
    segments: list[ScriptSegment] = Field(min_length=1)
    semantic_status: Literal['UNCHANGED','SEMANTIC_CHANGE_DETECTED','AUDIT_REQUIRED'] = 'AUDIT_REQUIRED'
    semantic_diff: dict = Field(default_factory=dict)
    parent_script_artifact_id: str | None = None


class Scene(StrictModel):
    scene_id: str
    purpose: str
    script_range: list[str]
    narrative_function: str
    retention_goal: str
    estimated_duration: float = Field(gt=0)
    density: str = 'MEDIUM'
    entry: str = 'CUT'
    exit: str = 'CUT'
    beat_ids: list[str] = Field(min_length=1)


class Beat(StrictModel):
    semantic_pattern: Literal['EXPLAIN','REACTION','EVIDENCE','COMPARE','PROCESS','NUMBER','SUMMARY','CTA'] | None = None
    template_id: str | None = None
    character_action_id: str | None = None
    element_ids: list[str] = Field(default_factory=list)
    beat_id: str
    scene_id: str
    script_segment_id: str
    phrase_id: str = ''
    purpose: str
    visual_focus: str
    visual_form: str
    character_intent: str = 'EXPLAIN'
    media_need: str = ''
    pattern_id: str
    retention_function: str = 'INFORMATION_CHANGE'
    reveal_order: list[str] = Field(default_factory=lambda: ['PRIMARY','SECONDARY','SUPPORTING'])
    motion_intent: str = 'FADE'
    keyword: str = ''
    timing_intent: float = Field(gt=0)
    slots: dict[str, Any] = Field(default_factory=dict)


class VisualPattern(StrictModel):
    pattern_id: str
    version: str = '1'
    semantic_purpose: str
    required_slots: list[str]
    optional_slots: list[str] = Field(default_factory=list)
    layout_intent: str
    reveal_motion: list[str]
    density: str = 'MEDIUM'
    character_presence: str = 'OPTIONAL'


class DirectorIR(StrictModel):
    schema_version: int = 2
    script_artifact_id: str
    scenes: list[Scene] = Field(min_length=1)
    beats: list[Beat] = Field(min_length=1)
    transitions: list[dict] = Field(default_factory=list)

    @model_validator(mode='after')
    def graph(self):
        scenes = {s.scene_id: s for s in self.scenes}
        beats = {b.beat_id: b for b in self.beats}
        if len(scenes) != len(self.scenes) or len(beats) != len(self.beats):
            raise ValueError('DUPLICATE_NARRATIVE_ID')
        listed = [bid for s in self.scenes for bid in s.beat_ids]
        if set(listed) != set(beats) or len(listed) != len(beats):
            raise ValueError('SCENE_BEAT_BINDING_INVALID')
        for b in self.beats:
            if b.scene_id not in scenes or b.beat_id not in scenes[b.scene_id].beat_ids:
                raise ValueError('SCENE_BEAT_BINDING_INVALID')
        return self


class EditCommand(StrictModel):
    command_id: str
    project_id: str
    actor: str
    actor_type: Literal['HUMAN','AGENT','SYSTEM']
    target: str
    operation: str
    arguments: dict
    before_revision: str | None
    after_revision: str
    timestamp: str
    reason: str


class StageState(StrictModel):
    stage: str
    input_hash: str
    config_hash: str
    worker: str
    prompt: str
    skills: str
    output_artifact: str | None = None
    status: Literal['CLEAN','DIRTY','RUNNING','FAILED','BLOCKED','COMPLETED','CACHED']
    error: str | None = None


class QAItem(StrictModel):
    code: str
    severity: Literal['BLOCKER','WARNING','INFO']
    owner: Literal['RESEARCH','SCRIPT_PRIMARY','SCRIPT_EDITOR','AUDIT','DIRECTOR','TIMELINE',
        'VOICE','SUBTITLE','TYPOGRAPHY','MEDIA_RESOLVER','EXPORT','HUMAN']
    description: str
    start: float = Field(default=0, ge=0)
    end: float = Field(default=0, ge=0)


class QAReport(StrictModel):
    verdict: Literal['PASS','FAIL','PASS_WITH_RISK']
    issues: list[QAItem]
    mock: bool = False
    checked_artifact_id: str


class FontRecord(StrictModel):
    font_id: str
    family: str
    subfamily: str
    full_name: str
    postscript_name: str
    source: Literal['SYSTEM','USER','PROJECT']
    file_path: str
    file_name: str
    file_type: str
    file_hash: str
    face_index: int = 0
    version: str = ''
    weight: int = 400
    style: str = 'normal'
    stretch: int = 5
    variable: bool = False
    axes: list[dict] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    classification: list[str] = Field(default_factory=list)
    status: str = 'AVAILABLE'
    preview_path: str
    preview_hash: str


class FontRole(StrictModel):
    font_id: str
    weight: int = Field(default=400, ge=1, le=1000)
    size: float = Field(default=48, gt=0)
    letter_spacing: float = 0
    line_height: float = Field(default=1.15, gt=0)
    shadow: str = '0 2px 4px #0008'


class TypographyProfile(StrictModel):
    profile_id: str
    version: str = '1'
    roles: dict[str, FontRole]
    production_policy: Literal['STRICT_FONT','ALLOW_FALLBACK'] = 'STRICT_FONT'
    fallback_font_id: str | None = None
    presentation: Literal['STANDARD', 'XIAOY_EXPLAINER'] = 'STANDARD'

    @model_validator(mode='after')
    def complete(self):
        if set(self.roles) != {'TITLE','BODY','SUBTITLE','KEYWORD','NUMBER','LABEL','CTA','UI'}:
            raise ValueError('TYPOGRAPHY_ROLES_REQUIRED')
        return self


SCHEMAS = {cls.__name__.upper()+'_SCHEMA': cls for cls in (
    WritingRule, RuleSet, HookRuleSet, RetentionRuleSet, EditorialVoiceProfile,
    SkillLayer, EffectiveSkillSnapshot, Source, FactPack, BoundScript, Scene,
    Beat, VisualPattern, DirectorIR, EditCommand, StageState, QAReport,
    FontRecord, FontRole, TypographyProfile)}
