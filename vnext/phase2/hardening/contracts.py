"""Explicit evidence, derived visuals, clocks and provider truth contracts."""
from typing import Literal,Any
from pydantic import Field,model_validator
from vnext.contracts import StrictModel

class TextSpan(StrictModel):
    start:int=Field(ge=0)
    end:int=Field(gt=0)
    @model_validator(mode='after')
    def ordered(self):
        if self.end<=self.start:raise ValueError('INVALID_TEXT_SPAN')
        return self

class ClaimUnit(StrictModel):
    claim_id:str=Field(pattern=r'^[A-Za-z0-9_-]+$')
    segment_id:str
    text_span:TextSpan
    claim_text:str=Field(min_length=1)
    claim_type:Literal['FACTUAL','NUMERIC','ATTRIBUTION','PREDICTION','OPINION','NON_CLAIM']
    fact_ids:list[str]=Field(default_factory=list)
    support_status:Literal['SUPPORTED','PARTIAL','UNSUPPORTED','NOT_REQUIRED']='UNSUPPORTED'
    review_status:Literal['PENDING','APPROVED','REJECTED']='PENDING'
    review_reason:str=''

class EvidenceLocator(StrictModel):
    media_type:Literal['TEXT','PDF','WEB','VIDEO','AUDIO']
    character_span:TextSpan|None=None
    paragraph:int|None=Field(default=None,ge=1)
    page:int|None=Field(default=None,ge=1)
    snapshot:str|None=None
    dom_path:str|None=None
    start_time:float|None=Field(default=None,ge=0)
    end_time:float|None=Field(default=None,gt=0)
    @model_validator(mode='after')
    def required(self):
        if self.media_type=='TEXT' and not (self.character_span or self.paragraph):raise ValueError('TEXT_LOCATOR_REQUIRED')
        if self.media_type=='PDF' and (not self.page or not self.character_span):raise ValueError('PDF_LOCATOR_REQUIRED')
        if self.media_type=='WEB' and (not self.snapshot or not self.character_span):raise ValueError('WEB_LOCATOR_REQUIRED')
        if self.media_type in ('VIDEO','AUDIO') and (self.start_time is None or self.end_time is None or self.end_time<=self.start_time):raise ValueError('TIME_LOCATOR_REQUIRED')
        return self

class EvidenceRef(StrictModel):
    evidence_id:str=Field(pattern=r'^[A-Za-z0-9_-]+$')
    source_id:str=Field(pattern=r'^[A-Za-z0-9_-]+$')
    locator:EvidenceLocator
    excerpt:str=Field(min_length=1)
    excerpt_hash:str=Field(pattern=r'^[a-f0-9]{64}$')
    source_content_hash:str=Field(pattern=r'^[a-f0-9]{64}$')

class ResolvedVisualComposition(StrictModel):
    schema_version:int=1
    beat_id:str
    pattern_id:str
    template_id:str
    character:dict|None=None
    elements:list[dict]=Field(default_factory=list)
    media_slots:list[dict]=Field(default_factory=list)
    text_slots:list[dict]=Field(default_factory=list)
    typography_roles:list[str]=Field(default_factory=list)
    layout:dict
    z_order:list[str]
    transforms:dict=Field(default_factory=dict)
    timing:dict
    motions:dict=Field(default_factory=dict)
    safe_area:dict
    overlap_allowed:list[list[str]]=Field(default_factory=list)

class AudioTimingEntry(StrictModel):
    audio_id:str
    segment_id:str
    start:float=Field(ge=0)
    end:float=Field(gt=0)
    duration:float=Field(gt=0)
    phrase_ranges:list[dict]=Field(default_factory=list)
    word_ranges:list[dict]=Field(default_factory=list)
    @model_validator(mode='after')
    def span(self):
        if self.end<=self.start or abs(self.duration-(self.end-self.start))>.001:raise ValueError('INVALID_AUDIO_RANGE')
        return self

class AudioTimingMap(StrictModel):
    audio_artifact_id:str
    script_artifact_id:str
    audio_hash:str
    duration:float=Field(gt=0)
    provenance:dict
    entries:list[AudioTimingEntry]=Field(min_length=1)

class ProviderTruth(StrictModel):
    registered:bool=True
    configured:bool=False
    adapter_implemented:bool=False
    credentials_available:bool=False
    model_discovered:bool=False
    capability_verified:bool=False
    verified_capabilities:list[str]=Field(default_factory=list)
    live_verified:bool=False
    last_probe_at:str|None=None
    last_probe_result:dict|None=None

class ModelRunLedger(StrictModel):
    run_id:str
    project_id:str
    stage:str
    role:str
    provider:str
    model:str
    provider_id:str|None=None
    model_id:str|None=None
    input_tokens:int|None=None
    output_tokens:int|None=None
    cached_tokens:int|None=None
    image_inputs:int=0
    audio_inputs:int=0
    video_inputs:int=0
    estimated_cost:float|None=Field(default=None,ge=0)
    actual_cost:float|None=Field(default=None,ge=0)
    currency:str='USD'
    cost_status:Literal['ACTUAL','ESTIMATED','UNKNOWN']='UNKNOWN'
    latency:float=Field(default=0,ge=0)
    retry_count:int=Field(default=0,ge=0)
    cache_hit:bool=False
    status:Literal['RESERVED','COMPLETED','FAILED','BLOCKED']
    at:str
    fallback_from:str|None=None
    metadata:dict=Field(default_factory=dict)

class DependencyItem(StrictModel):
    kind:str
    asset_id:str
    expected_hash:str
    original_location:str
    resolved_location:str
    status:Literal['RESOLVED','MISSING','HASH_MISMATCH','RELINK_REQUIRED']

SCHEMAS={cls.__name__.upper()+'_SCHEMA':cls for cls in (ClaimUnit,EvidenceRef,EvidenceLocator,ResolvedVisualComposition,AudioTimingMap,AudioTimingEntry,ProviderTruth,ModelRunLedger,DependencyItem)}
