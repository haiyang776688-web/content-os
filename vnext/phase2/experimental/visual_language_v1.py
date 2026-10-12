"""Isolated XIAO-Y Evidence Editorial v1 contracts and deterministic compiler.

This module is the VRE-001 vertical slice. It does not write formal project
artifacts or replace DirectorIR/VisualResolver. The semantic ShotPlan contains
no pixel geometry; the compiler is the sole layout owner.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import shutil
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from PIL import Image
from pydantic import Field, model_validator

from vnext.contracts import EDTClip, StrictModel
from vnext.phase2.experimental.motion_design_v1 import (
    DeterministicMotionCompiler,
    MotionDesignPlan,
    mechanical_motion_design_qa,
)

VisualJob = Literal['PROVE', 'DEMONSTRATE', 'EXPLAIN', 'COMPARE', 'REACT',
                    'WARN', 'TRANSITION', 'SUMMARIZE']
VisualMode = Literal['BRAND_BALANCED', 'EVIDENCE_HEAVY']
ShotType = Literal['CHARACTER_INTRO', 'CHARACTER_EXPLAIN', 'CHARACTER_REACTION',
                   'CHARACTER_RESPONSIBILITY', 'EVIDENCE_CONTEXT', 'EVIDENCE_FOCUS',
                   'EVIDENCE_DETAIL', 'EVIDENCE_HIGHLIGHT', 'EVIDENCE_COMPARE',
                   'RELATION_EXPLAIN', 'KEYWORD_PUNCTUATION', 'SUMMARY', 'END_CARD']
ProtagonistKind = Literal['EVIDENCE', 'XIAOY', 'TEXT', 'NUMBER', 'COMPARISON', 'DIAGRAM']
Treatment = Literal['FULL_CONTEXT', 'FOCUS_REGION', 'DETAIL_CROP', 'HIGHLIGHT_REGION',
                    'DIM_NON_FOCUS', 'CALLOUT', 'RELATION', 'BEFORE_AFTER']
CharacterRole = Literal['GUIDE', 'EXPLAINER', 'REACTION', 'WARNING', 'RESPONSIBILITY',
                        'TRANSITION', 'SUMMARY', 'NONE']
MotionSemantic = Literal['FOCUS', 'REVEAL', 'FOLLOW', 'COMPARE', 'INTERRUPT',
                         'RETURN', 'CONNECT', 'SETTLE']
FitMode = Literal['CONTAIN', 'COVER_CROP', 'FOCUS_CROP']
VisualAssetKind = Literal['EVIDENCE', 'CHARACTER', 'IMAGE', 'VIDEO', 'LOGO',
                          'ICON', 'ELEMENT', 'SVG']

ALLOWED_SHOTS: dict[str, set[str]] = {
    'PROVE': {'EVIDENCE_CONTEXT', 'EVIDENCE_FOCUS', 'EVIDENCE_DETAIL', 'EVIDENCE_HIGHLIGHT', 'RELATION_EXPLAIN'},
    'DEMONSTRATE': {'EVIDENCE_CONTEXT', 'EVIDENCE_FOCUS', 'EVIDENCE_DETAIL', 'EVIDENCE_COMPARE'},
    'EXPLAIN': {'CHARACTER_EXPLAIN', 'EVIDENCE_CONTEXT', 'EVIDENCE_FOCUS', 'RELATION_EXPLAIN'},
    'COMPARE': {'EVIDENCE_COMPARE', 'RELATION_EXPLAIN'},
    'REACT': {'CHARACTER_REACTION', 'KEYWORD_PUNCTUATION'},
    'WARN': {'CHARACTER_REACTION', 'CHARACTER_RESPONSIBILITY', 'EVIDENCE_HIGHLIGHT', 'KEYWORD_PUNCTUATION'},
    'TRANSITION': {'CHARACTER_INTRO', 'EVIDENCE_CONTEXT', 'KEYWORD_PUNCTUATION'},
    'SUMMARIZE': {'SUMMARY', 'END_CARD', 'EVIDENCE_HIGHLIGHT'},
}
EVIDENCE_SHOTS = {'EVIDENCE_CONTEXT', 'EVIDENCE_FOCUS', 'EVIDENCE_DETAIL',
                  'EVIDENCE_HIGHLIGHT', 'EVIDENCE_COMPARE', 'RELATION_EXPLAIN'}
ROLE_ACTIONS = {
    'GUIDE': ('XACT-007', 'point.png'),
    'EXPLAINER': ('XACT-007', 'point.png'),
    'REACTION': ('XACT-030', 'surprise.png'),
    'WARNING': ('XACT-044', 'serious.png'),
    'RESPONSIBILITY': ('XACT-044', 'serious.png'),
    'TRANSITION': ('XACT-007', 'point.png'),
    'SUMMARY': ('XACT-007', 'point.png'),
}
MOTION_PRIMITIVES = {
    'FOCUS': 'PUSH_IN', 'REVEAL': 'FADE_IN', 'FOLLOW': 'FOLLOW_PATH',
    'COMPARE': 'MATCHED_WIPE', 'INTERRUPT': 'POP_CUT', 'RETURN': 'RETURN_TO_ANCHOR',
    'CONNECT': 'DRAW_CONNECTION', 'SETTLE': 'SETTLE_HOLD',
}
ASPECT_RATIO_TOLERANCE = .005
MOTION_CONTRACT_PATH = (Path(__file__).resolve().parents[2] / 'renderers' / 'remotion' /
                        'project' / 'src' / 'vre001' / 'motion-primitive-contract-v1.json')
MOTION_PRIMITIVE_CONTRACT = json.loads(MOTION_CONTRACT_PATH.read_text())


def declared_motion_primitives() -> dict[str, dict[str, Any]]:
    """Return the authoritative renderer capability contract."""
    return copy.deepcopy(MOTION_PRIMITIVE_CONTRACT['primitives'])


def validate_motion_primitive(primitive: str, layer_kind: str) -> dict[str, Any]:
    entry = MOTION_PRIMITIVE_CONTRACT['primitives'].get(primitive)
    if entry is None:
        raise ValueError(f'MOTION_PRIMITIVE_UNKNOWN:{primitive}')
    if not entry.get('implemented') or not entry.get('renderer_consumer'):
        raise ValueError(f'MOTION_PRIMITIVE_DECLARED_NOT_RENDERED:{primitive}')
    if layer_kind not in entry['allowed_layer_kinds']:
        raise ValueError(f'MOTION_PRIMITIVE_UNSUPPORTED_FOR_LAYER:{primitive}:{layer_kind}')
    return entry


def motion_frame_state(primitive: str, progress: float) -> dict[str, float]:
    """Deterministic contract probe used by tests and Gallery verification."""
    entry = MOTION_PRIMITIVE_CONTRACT['primitives'].get(primitive)
    if entry is None:
        raise ValueError(f'MOTION_PRIMITIVE_UNKNOWN:{primitive}')
    validate_motion_primitive(primitive, entry['allowed_layer_kinds'][0])
    p = min(1.0, max(0.0, progress))
    behavior = entry['behavior_class']
    if behavior == 'STATIC':
        return {'static': 1.0}
    if behavior == 'UNIFORM_SCALE_IN':
        return {'uniform_scale': .92 + .08 * p}
    if behavior == 'OPACITY_REVEAL':
        return {'opacity': p}
    if behavior == 'TRANSLATE_IN':
        return {'translate_x_percent': -5 * (1 - p)}
    if behavior == 'CLIP_WIPE':
        return {'clip_right_percent': 100 * (1 - p),
                'translate_x_percent': -3 * (1 - p)}
    if behavior == 'UNIFORM_POP_IN':
        return {'uniform_scale': .82 + .18 * p}
    if behavior == 'RETURN_SETTLE':
        return {'opacity': p, 'uniform_scale': 1.05 - .05 * p}
    if behavior == 'PATH_DRAW':
        return {'path_reveal': p}
    if behavior == 'UNIFORM_SETTLE':
        return {'uniform_scale': 1.025 - .025 * p}
    if behavior == 'WIDTH_REVEAL':
        return {'width_ratio': p}
    if behavior == 'LABEL_REVEAL':
        return {'opacity': p, 'translate_x_px': 24 * (1 - p)}
    raise ValueError(f'MOTION_PRIMITIVE_DECLARED_NOT_RENDERED:{primitive}')


def motion_primitive_for_layer(semantic: str, layer_kind: str) -> str:
    """Resolve semantic intent to an honest layer-supported primitive."""
    primitive = MOTION_PRIMITIVES[semantic]
    # CONNECT belongs to the procedural relation path. Supporting registered
    # media enters visibly but never impersonates generic path drawing.
    if primitive == 'DRAW_CONNECTION' and layer_kind in ('EVIDENCE', 'CHARACTER'):
        return 'FADE_IN'
    validate_motion_primitive(primitive, layer_kind)
    return primitive


class Region(StrictModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    width: float = Field(gt=0, le=1)
    height: float = Field(gt=0, le=1)
    label: str = ''
    keywords: list[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def inside(self):
        if self.x + self.width > 1 or self.y + self.height > 1:
            raise ValueError('EVIDENCE_REGION_OUTSIDE_SOURCE')
        return self


class RegisteredAsset(StrictModel):
    asset_id: str
    kind: VisualAssetKind | Literal['VOICE', 'FONT']
    source_path: str
    sha256: str
    intrinsic_width: int | None = Field(default=None, gt=0)
    intrinsic_height: int | None = Field(default=None, gt=0)
    intrinsic_aspect_ratio: float | None = Field(default=None, gt=0)
    regions: dict[str, Region] = Field(default_factory=dict)

    @model_validator(mode='after')
    def coherent_dimensions(self):
        supplied = (self.intrinsic_width is not None, self.intrinsic_height is not None)
        if any(supplied) and not all(supplied):
            raise ValueError('ASSET_INTRINSIC_DIMENSIONS_INCOMPLETE')
        if all(supplied):
            ratio = self.intrinsic_width / self.intrinsic_height
            if self.intrinsic_aspect_ratio is not None and abs(ratio / self.intrinsic_aspect_ratio - 1) > .005:
                raise ValueError('ASSET_INTRINSIC_RATIO_MISMATCH')
            self.intrinsic_aspect_ratio = ratio
        return self


class FrozenScriptSegment(StrictModel):
    segment_id: str
    text: str
    fact_ids: list[str] = Field(default_factory=list)


class CaptionCue(StrictModel):
    text: str
    start: float = Field(ge=0)
    end: float = Field(gt=0)


class VREInput(StrictModel):
    script_id: str
    script_sha256: str
    segments: list[FrozenScriptSegment]
    captions: list[CaptionCue]
    assets: list[RegisteredAsset]
    width: int = 1920
    height: int = 1080
    fps: int = 30
    duration: float = Field(gt=0)

    @model_validator(mode='after')
    def timeline(self):
        cursor = 0.0
        for cue in self.captions:
            if abs(cue.start - cursor) > .000001 or cue.end <= cue.start:
                raise ValueError('CAPTION_GAP_OR_OVERLAP')
            cursor = cue.end
        if abs(cursor - self.duration) > .000001:
            raise ValueError('CAPTION_DURATION_MISMATCH')
        if len({a.asset_id for a in self.assets}) != len(self.assets):
            raise ValueError('DUPLICATE_ASSET_ID')
        return self


class Protagonist(StrictModel):
    primary: ProtagonistKind
    supporting: list[ProtagonistKind] = Field(default_factory=list)
    background: list[ProtagonistKind] = Field(default_factory=list)

    @model_validator(mode='after')
    def unique(self):
        all_items = [self.primary, *self.supporting, *self.background]
        if len(all_items) != len(set(all_items)):
            raise ValueError('PROTAGONIST_ROLE_CONFLICT')
        return self


class Shot(StrictModel):
    shot_id: str
    shot_type: ShotType
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    protagonist: Protagonist
    evidence_asset_id: str | None = None
    evidence_treatment: Treatment | None = None
    evidence_region_id: str | None = None
    character_role: CharacterRole = 'NONE'
    semantic_focus: str = Field(min_length=1)
    motion_semantic: MotionSemantic
    callout: str | None = None

    @model_validator(mode='after')
    def coherent(self):
        if self.end <= self.start:
            raise ValueError('SHOT_RANGE_INVALID')
        if self.shot_type in EVIDENCE_SHOTS and not self.evidence_asset_id:
            raise ValueError('SHOT_EVIDENCE_REQUIRED')
        if self.evidence_asset_id and not self.evidence_treatment:
            raise ValueError('EVIDENCE_TREATMENT_REQUIRED')
        if self.evidence_treatment not in (None, 'FULL_CONTEXT') and not self.evidence_region_id:
            raise ValueError('EVIDENCE_REGION_REQUIRED')
        if self.protagonist.primary == 'XIAOY' and self.character_role == 'NONE':
            raise ValueError('PRIMARY_XIAOY_ROLE_REQUIRED')
        if self.character_role != 'NONE' and 'XIAOY' not in [self.protagonist.primary, *self.protagonist.supporting]:
            raise ValueError('CHARACTER_ROLE_WITHOUT_PROTAGONIST')
        if self.callout and (len(self.callout.strip()) > 16 or not self.callout.strip()):
            raise ValueError('CALLOUT_NOT_SHORT')
        return self


class ShotBeat(StrictModel):
    beat_id: str
    script_segment_id: str
    visual_job: VisualJob
    visual_mode: VisualMode = 'BRAND_BALANCED'
    shots: list[Shot] = Field(min_length=1)

    @model_validator(mode='after')
    def compatible(self):
        for shot in self.shots:
            if shot.shot_type not in ALLOWED_SHOTS[self.visual_job]:
                raise ValueError(f'SHOT_TYPE_NOT_ALLOWED:{self.visual_job}:{shot.shot_type}')
        return self


class ShotPlan(StrictModel):
    schema_version: Literal[1] = 1
    plan_id: str
    source_script_id: str
    visual_mode: VisualMode
    beats: list[ShotBeat] = Field(min_length=1)

    @model_validator(mode='after')
    def complete(self):
        shots = [shot for beat in self.beats for shot in beat.shots]
        if len({s.shot_id for s in shots}) != len(shots):
            raise ValueError('DUPLICATE_SHOT_ID')
        cursor = 0.0
        for shot in shots:
            if abs(shot.start - cursor) > .000001:
                raise ValueError('SHOT_GAP_OR_OVERLAP')
            cursor = shot.end
        return self


def build_f2_shot_plan(source: VREInput) -> ShotPlan:
    """Create the frozen semantic F2 reproduction plan without layout geometry."""
    segment_ids = [s.segment_id for s in source.segments]
    if segment_ids != ['SEG-02', 'SEG-03', 'SEG-04']:
        raise ValueError('VRE001_FROZEN_SCRIPT_REQUIRED')

    def p(primary, supporting=(), background=()):
        return Protagonist(primary=primary, supporting=list(supporting), background=list(background))

    beats = [
        ShotBeat(beat_id='VRE-B01', script_segment_id='SEG-02', visual_job='TRANSITION', shots=[
            Shot(shot_id='VRE-S01', shot_type='CHARACTER_INTRO', start=0, end=1.05,
                 protagonist=p('XIAOY', ['EVIDENCE']), evidence_asset_id='EV-RESEARCH',
                 evidence_treatment='FOCUS_REGION', evidence_region_id='import_control',
                 character_role='GUIDE', semantic_focus='研究导入入口', motion_semantic='REVEAL'),
        ]),
        ShotBeat(beat_id='VRE-B02', script_segment_id='SEG-02', visual_job='DEMONSTRATE', shots=[
            Shot(shot_id='VRE-S02', shot_type='EVIDENCE_FOCUS', start=1.05, end=2.91,
                 protagonist=p('EVIDENCE'), evidence_asset_id='EV-RESEARCH',
                 evidence_treatment='FOCUS_REGION', evidence_region_id='import_control',
                 semantic_focus='本地文件入口', motion_semantic='FOCUS', callout='本地入口'),
        ]),
        ShotBeat(beat_id='VRE-B03', script_segment_id='SEG-02', visual_job='PROVE', shots=[
            Shot(shot_id='VRE-S03', shot_type='EVIDENCE_HIGHLIGHT', start=2.91, end=6.24,
                 protagonist=p('EVIDENCE'), evidence_asset_id='EV-RESEARCH',
                 evidence_treatment='HIGHLIGHT_REGION', evidence_region_id='candidate_rule',
                 semantic_focus='候选停在人工确认边界', motion_semantic='FOLLOW', callout='待确认'),
        ]),
        ShotBeat(beat_id='VRE-B04', script_segment_id='SEG-03', visual_job='REACT', shots=[
            Shot(shot_id='VRE-S04', shot_type='CHARACTER_REACTION', start=6.24, end=7.34,
                 protagonist=p('XIAOY', ['EVIDENCE']), evidence_asset_id='EV-RESEARCH',
                 evidence_treatment='DETAIL_CROP', evidence_region_id='candidate_rule',
                 character_role='REACTION', semantic_focus='候选不能自动升级',
                 motion_semantic='INTERRUPT', callout='等等。'),
        ]),
        ShotBeat(beat_id='VRE-B05', script_segment_id='SEG-03', visual_job='WARN', shots=[
            Shot(shot_id='VRE-S05', shot_type='EVIDENCE_HIGHLIGHT', start=7.34, end=9.87,
                 protagonist=p('EVIDENCE'), evidence_asset_id='EV-RESEARCH',
                 evidence_treatment='HIGHLIGHT_REGION', evidence_region_id='not_fact_rule',
                 semantic_focus='模型总结不直接成为事实', motion_semantic='RETURN', callout='≠ FACT'),
        ]),
        ShotBeat(beat_id='VRE-B06', script_segment_id='SEG-03', visual_job='WARN', shots=[
            Shot(shot_id='VRE-S06', shot_type='CHARACTER_RESPONSIBILITY', start=9.87, end=11.88,
                 protagonist=p('XIAOY', ['EVIDENCE']), evidence_asset_id='EV-SCRIPT',
                 evidence_treatment='DETAIL_CROP', evidence_region_id='human_review',
                 character_role='RESPONSIBILITY', semantic_focus='人工审查责任',
                 motion_semantic='REVEAL', callout='人工把关'),
        ]),
        ShotBeat(beat_id='VRE-B07', script_segment_id='SEG-04', visual_job='TRANSITION', shots=[
            Shot(shot_id='VRE-S07', shot_type='CHARACTER_INTRO', start=11.88, end=12.75,
                 protagonist=p('EVIDENCE', ['XIAOY']), evidence_asset_id='EV-RESEARCH',
                 evidence_treatment='DETAIL_CROP', evidence_region_id='source_rule',
                 character_role='TRANSITION', semantic_focus='从人工审查转向来源', motion_semantic='FOLLOW'),
        ]),
        ShotBeat(beat_id='VRE-B08', script_segment_id='SEG-04', visual_job='EXPLAIN', shots=[
            Shot(shot_id='VRE-S08', shot_type='RELATION_EXPLAIN', start=12.75, end=15.42,
                 protagonist=p('DIAGRAM', background=['EVIDENCE']), evidence_asset_id='EV-RESEARCH',
                 evidence_treatment='RELATION', evidence_region_id='source_rule',
                 semantic_focus='来源与 Fact 双向绑定', motion_semantic='CONNECT', callout='SOURCE ↔ FACT'),
        ]),
        ShotBeat(beat_id='VRE-B09', script_segment_id='SEG-04', visual_job='PROVE', shots=[
            Shot(shot_id='VRE-S09', shot_type='EVIDENCE_FOCUS', start=15.42, end=17.30,
                 protagonist=p('EVIDENCE'), evidence_asset_id='EV-SCRIPT',
                 evidence_treatment='FOCUS_REGION', evidence_region_id='fact_id_rule',
                 semantic_focus='脚本引用已有 Fact ID', motion_semantic='FOCUS', callout='引用要求'),
        ]),
        ShotBeat(beat_id='VRE-B10', script_segment_id='SEG-04', visual_job='SUMMARIZE', shots=[
            Shot(shot_id='VRE-S10', shot_type='EVIDENCE_HIGHLIGHT', start=17.30, end=19.12,
                 protagonist=p('EVIDENCE', ['XIAOY']), evidence_asset_id='EV-SCRIPT',
                 evidence_treatment='HIGHLIGHT_REGION', evidence_region_id='fact_id_rule',
                 character_role='SUMMARY', semantic_focus='Fact ID 引用要求', motion_semantic='SETTLE'),
        ]),
    ]
    return ShotPlan(plan_id='VRE-001-F2-REPRODUCTION', source_script_id=source.script_id,
                    visual_mode='BRAND_BALANCED', beats=beats)


class VisualCompiler:
    """Compile semantic shots into existing EDTClip envelopes and explicit primitives."""

    def __init__(self, repo_root: Path, public_root: Path):
        self.repo_root = Path(repo_root)
        self.public_root = Path(public_root)

    @staticmethod
    def _sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _intrinsic_dimensions(asset: RegisteredAsset, path: Path) -> tuple[int, int]:
        """Resolve source dimensions once; layout code never guesses them."""
        if asset.intrinsic_width and asset.intrinsic_height:
            return asset.intrinsic_width, asset.intrinsic_height
        if asset.kind == 'VIDEO':
            payload = json.loads(subprocess.check_output([
                'ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height', '-of', 'json', str(path),
            ]))
            stream = payload['streams'][0]
            return int(stream['width']), int(stream['height'])
        if asset.kind == 'SVG' or path.suffix.lower() == '.svg':
            root = ET.parse(path).getroot()
            view_box = root.attrib.get('viewBox', '').replace(',', ' ').split()
            if len(view_box) == 4:
                return round(float(view_box[2])), round(float(view_box[3]))
            width = root.attrib.get('width', '').removesuffix('px')
            height = root.attrib.get('height', '').removesuffix('px')
            if width and height:
                return round(float(width)), round(float(height))
            raise ValueError('SVG_INTRINSIC_DIMENSIONS_MISSING:' + asset.asset_id)
        with Image.open(path) as image:
            return image.width, image.height

    @staticmethod
    def _media_transform(source_width: int, source_height: int, box: dict[str, float],
                         canvas_width: int, canvas_height: int, fit_mode: FitMode,
                         region: Region | None = None) -> dict[str, float | str]:
        """Return a uniform-scale transform in destination-box pixel coordinates."""
        destination_width = box['width'] * canvas_width
        destination_height = box['height'] * canvas_height
        if fit_mode == 'CONTAIN':
            scale = min(destination_width / source_width, destination_height / source_height)
            focus_x, focus_y = source_width / 2, source_height / 2
        elif fit_mode == 'COVER_CROP':
            scale = max(destination_width / source_width, destination_height / source_height)
            focus_x, focus_y = source_width / 2, source_height / 2
        else:
            if region is None:
                raise ValueError('FOCUS_CROP_REGION_REQUIRED')
            region_width = source_width * region.width
            region_height = source_height * region.height
            # Keep the destination covered while preserving as much of the
            # semantic focus region as its aspect ratio allows.  Using max()
            # against both region axes would crop extreme wide/tall regions
            # until their evidence meaning was no longer readable.
            source_cover_scale = max(destination_width / source_width,
                                     destination_height / source_height)
            region_contain_scale = min(destination_width / region_width,
                                       destination_height / region_height)
            scale = max(source_cover_scale, region_contain_scale)
            focus_x = source_width * (region.x + region.width / 2)
            focus_y = source_height * (region.y + region.height / 2)
        render_width = source_width * scale
        render_height = source_height * scale
        left = destination_width / 2 - focus_x * scale
        top = destination_height / 2 - focus_y * scale
        if render_width >= destination_width:
            left = min(0, max(destination_width - render_width, left))
        else:
            left = (destination_width - render_width) / 2
        if render_height >= destination_height:
            top = min(0, max(destination_height - render_height, top))
        else:
            top = (destination_height - render_height) / 2
        return {
            'fit_mode': fit_mode,
            'scale_x': scale,
            'scale_y': scale,
            'render_width': render_width,
            'render_height': render_height,
            'left': left,
            'top': top,
            'destination_width': destination_width,
            'destination_height': destination_height,
        }

    def _resolve_assets(self, source: VREInput, preview_name: str) -> dict[str, dict[str, Any]]:
        if not preview_name.startswith('PREVIEW-') or '/' in preview_name or '..' in preview_name:
            raise ValueError('PREVIEW_NAME_INVALID')
        target = self.public_root / preview_name
        target.mkdir(parents=True, exist_ok=True)
        result = {}
        for asset in source.assets:
            path = (self.repo_root / asset.source_path).resolve()
            if not path.is_file() or self._sha(path) != asset.sha256:
                raise ValueError('REGISTERED_ASSET_HASH_MISMATCH:' + asset.asset_id)
            name = path.name
            copied = target / name
            if copied.resolve() != path:
                shutil.copy2(path, copied)
            dimensions = None
            if asset.kind in ('EVIDENCE', 'CHARACTER', 'IMAGE', 'VIDEO', 'LOGO', 'ICON', 'ELEMENT', 'SVG'):
                width, height = self._intrinsic_dimensions(asset, path)
                if width <= 0 or height <= 0:
                    raise ValueError('ASSET_INTRINSIC_DIMENSIONS_INVALID:' + asset.asset_id)
                dimensions = {'width': width, 'height': height, 'aspect_ratio': width / height}
            result[asset.asset_id] = {
                'asset': asset, 'src': f'{preview_name}/{name}', 'sha256': asset.sha256,
                'dimensions': dimensions,
            }
        return result

    @staticmethod
    def _layout(shot: Shot, mode: str) -> dict[str, Any]:
        # Concrete geometry lives only here. Values are normalized canvas coordinates.
        evidence_w = .92 if mode == 'EVIDENCE_HEAVY' else .84
        recipes = {
            'CHARACTER_INTRO': {'background':'#ffffff','character':(.18,.57,.30,.70),'evidence':(.68,.50,.58,.62)},
            'CHARACTER_EXPLAIN': {'background':'#ffffff','character':(.20,.57,.32,.72),'text':(.68,.42,.48,.30)},
            'CHARACTER_REACTION': {'background':'#FFC800','character':(.74,.57,.43,.84),'evidence':(.22,.66,.34,.20)},
            'CHARACTER_RESPONSIBILITY': {'background':'#ffffff','character':(.17,.57,.28,.68),'evidence':(.67,.48,.64,.54)},
            'EVIDENCE_CONTEXT': {'background':'#0B1018','evidence':(.5,.53,evidence_w,.78)},
            'EVIDENCE_FOCUS': {'background':'#0B1018','evidence':(.5,.53,.94,.82)},
            'EVIDENCE_DETAIL': {'background':'#0B1018','evidence':(.5,.53,.94,.82)},
            'EVIDENCE_HIGHLIGHT': {'background':'#0B1018','evidence':(.5,.53,.94,.82)},
            'EVIDENCE_COMPARE': {'background':'#0B1018','evidence':(.5,.53,.94,.82)},
            'RELATION_EXPLAIN': {'background':'#ffffff','evidence':(.28,.45,.38,.23),'relation':(.55,.45,.30,.16),'node':(.78,.45,.20,.18)},
            'KEYWORD_PUNCTUATION': {'background':'#FFC800','text':(.5,.45,.68,.28)},
            'SUMMARY': {'background':'#ffffff','character':(.20,.57,.30,.70),'text':(.66,.42,.50,.30)},
            'END_CARD': {'background':'#ffffff','character':(.22,.57,.30,.70),'text':(.68,.42,.48,.30)},
        }
        if shot.shot_type not in recipes:
            raise ValueError('SHOT_RECIPE_NOT_IMPLEMENTED:' + shot.shot_type)
        return copy.deepcopy(recipes[shot.shot_type])

    @staticmethod
    def _clip(shot: Shot, beat: ShotBeat, track: str, index: str, **values) -> dict:
        duration = shot.end - shot.start
        meta = {
            'visual_language':'XIAOY_EVIDENCE_EDITORIAL_V1', 'shot_id':shot.shot_id,
            'visual_job':beat.visual_job, 'visual_mode':beat.visual_mode, 'shot_type':shot.shot_type,
            'script_segment_id':beat.script_segment_id,
            'protagonist_primary':shot.protagonist.primary,
            'protagonist_supporting':shot.protagonist.supporting,
            'protagonist_background':shot.protagonist.background,
            'semantic_focus':shot.semantic_focus, **values.pop('metadata', {}),
        }
        value = EDTClip(
            clip_id=f'{shot.shot_id}-{track}-{index}', scene_id='VRE-001', beat_id=beat.beat_id,
            ir_node_id=shot.shot_id, origin='SHOT_PLAN_V1', edit_source='VISUAL_COMPILER_V1',
            pattern_id=None, track=track, timeline_in=shot.start, timeline_out=shot.end,
            source_in=0, source_out=duration, metadata=meta, **values,
        )
        return value.model_dump()

    def compile(self, source: VREInput, plan: ShotPlan, preview_name='PREVIEW-VRE001',
                motion_design: MotionDesignPlan | None = None) -> tuple[dict, dict]:
        if plan.source_script_id != source.script_id:
            raise ValueError('SHOT_PLAN_SCRIPT_MISMATCH')
        asset_map = self._resolve_assets(source, preview_name)
        evidence_ids = {a.asset_id for a in source.assets if a.kind in ('EVIDENCE', 'IMAGE', 'VIDEO', 'SVG')}
        clips = []
        shots = [shot for beat in plan.beats for shot in beat.shots]
        if abs(shots[-1].end - source.duration) > .000001:
            raise ValueError('SHOT_PLAN_DURATION_MISMATCH')
        for beat in plan.beats:
            for shot in beat.shots:
                # A plan-wide evidence-heavy override remains compatible with
                # VRE-001; otherwise VLA-001 can vary responsibility per beat.
                effective_mode = 'EVIDENCE_HEAVY' if plan.visual_mode == 'EVIDENCE_HEAVY' else beat.visual_mode
                layout = self._layout(shot, effective_mode)
                clips.append(self._clip(shot, beat, 'ELEMENT', 'background',
                    position={'x':.5,'y':.5}, metadata={'layer_kind':'BACKGROUND','box':{'width':1,'height':1},
                    'color':layout['background'],'z_index':0,'motion_primitive':'NONE',
                    'geometry_kind':'PROCEDURAL'}))
                if shot.evidence_asset_id:
                    if shot.evidence_asset_id not in evidence_ids:
                        raise ValueError('SHOT_EVIDENCE_NOT_REGISTERED:' + shot.evidence_asset_id)
                    resolved = asset_map[shot.evidence_asset_id]
                    region = resolved['asset'].regions.get(shot.evidence_region_id) if shot.evidence_region_id else None
                    if shot.evidence_region_id and not region:
                        raise ValueError('SHOT_EVIDENCE_REGION_NOT_REGISTERED:' + shot.evidence_region_id)
                    x,y,w,h = layout['evidence']
                    dimensions = resolved['dimensions']
                    region_is_full_source = bool(region and region.x == 0 and region.y == 0 and
                                                 region.width == 1 and region.height == 1)
                    fit_mode: FitMode = ('FOCUS_CROP' if region and not region_is_full_source and
                                         shot.evidence_treatment != 'FULL_CONTEXT' else 'CONTAIN')
                    media_transform = self._media_transform(
                        dimensions['width'], dimensions['height'], {'width':w, 'height':h},
                        source.width, source.height, fit_mode, region)
                    clips.append(self._clip(shot, beat, 'MEDIA', 'evidence',
                        asset_id=shot.evidence_asset_id, position={'x':x,'y':y},
                        motion={'semantic':shot.motion_semantic,
                                'primitive':motion_primitive_for_layer(shot.motion_semantic, 'EVIDENCE')},
                        metadata={'layer_kind':'EVIDENCE','asset_src':resolved['src'],'box':{'width':w,'height':h},
                        'source_region':region.model_dump() if region else None,
                        'geometry_kind':'REGISTERED_ASSET','aspect_ratio_policy':'PRESERVE',
                        'asset_kind':resolved['asset'].kind,
                        'fit_mode':fit_mode,'intrinsic_width':dimensions['width'],
                        'intrinsic_height':dimensions['height'],
                        'intrinsic_aspect_ratio':dimensions['aspect_ratio'],
                        'media_transform':media_transform,
                        'evidence_treatment':shot.evidence_treatment,'evidence_source_sha256':resolved['sha256'],
                        'protagonist_role':'PRIMARY' if shot.protagonist.primary=='EVIDENCE' else 'SUPPORTING',
                        'z_index':10}))
                    if shot.evidence_treatment == 'HIGHLIGHT_REGION':
                        clips.append(self._clip(shot, beat, 'ELEMENT', 'highlight', position={'x':x,'y':y},
                            motion={'semantic':shot.motion_semantic,'primitive':'DRAW_UNDERLINE'},
                            metadata={'layer_kind':'UNDERLINE','box':{'width':min(w*.55,.52),'height':.012},
                            'color':'#FFC800','z_index':18,'protagonist_role':'SUPPORTING',
                            'geometry_kind':'PROCEDURAL'}))
                if shot.shot_type == 'RELATION_EXPLAIN':
                    x,y,w,h = layout['relation']
                    clips.append(self._clip(shot, beat, 'ELEMENT', 'relation', position={'x':x,'y':y},
                        motion={'semantic':'CONNECT','primitive':'DRAW_CONNECTION'},
                        metadata={'layer_kind':'RELATION','box':{'width':w,'height':h},'color':'#FFC800',
                        'z_index':20,'protagonist_role':'PRIMARY','from_label':'SOURCE','to_label':'FACT',
                        'geometry_kind':'PROCEDURAL'}))
                    nx,ny,nw,nh = layout['node']
                    clips.append(self._clip(shot, beat, 'TEXT', 'node', position={'x':nx,'y':ny},
                        metadata={'layer_kind':'FACT_NODE','text':'Fact','box':{'width':nw,'height':nh},
                        'style_token':'FACT_NODE','z_index':21,'protagonist_role':'SUPPORTING'}))
                if shot.character_role != 'NONE':
                    action_id, filename = ROLE_ACTIONS[shot.character_role]
                    character_id = {'point.png':'CH-POINT','surprise.png':'CH-SURPRISE','serious.png':'CH-SERIOUS'}[filename]
                    resolved = asset_map[character_id]
                    # Evidence-primary summary shots may add a small supporting
                    # character without changing the evidence layout recipe.
                    x,y,w,h = layout.get('character', (.13,.70,.22,.44))
                    dimensions = resolved['dimensions']
                    media_transform = self._media_transform(
                        dimensions['width'], dimensions['height'], {'width':w, 'height':h},
                        source.width, source.height, 'CONTAIN')
                    clips.append(self._clip(shot, beat, 'CHARACTER', 'character', asset_id=action_id,
                        position={'x':x,'y':y}, motion={'semantic':shot.motion_semantic,
                        'primitive':motion_primitive_for_layer(shot.motion_semantic, 'CHARACTER')},
                        metadata={'layer_kind':'CHARACTER','asset_src':resolved['src'],'box':{'width':w,'height':h},
                        'geometry_kind':'REGISTERED_ASSET','aspect_ratio_policy':'PRESERVE',
                        'asset_kind':resolved['asset'].kind,
                        'fit_mode':'CONTAIN','intrinsic_width':dimensions['width'],
                        'intrinsic_height':dimensions['height'],
                        'intrinsic_aspect_ratio':dimensions['aspect_ratio'],
                        'media_transform':media_transform,
                        'character_role':shot.character_role,'action_id':action_id,'z_index':25,
                        'protagonist_role':'PRIMARY' if shot.protagonist.primary=='XIAOY' else 'SUPPORTING'}))
                if shot.callout:
                    pos = (.18,.30) if shot.protagonist.primary=='XIAOY' else (.70,.30)
                    if shot.shot_type == 'RELATION_EXPLAIN': pos=(.50,.68)
                    if shot.shot_type in ('CHARACTER_EXPLAIN','SUMMARY','END_CARD'): pos=(.67,.40)
                    if shot.shot_type == 'KEYWORD_PUNCTUATION': pos=(.50,.45)
                    clips.append(self._clip(shot, beat, 'TEXT', 'callout', position={'x':pos[0],'y':pos[1]},
                        motion={'semantic':shot.motion_semantic,'primitive':'LABEL_REVEAL'},
                        metadata={'layer_kind':'CALLOUT','text':shot.callout,'box':{'width':.30,'height':.10},
                        'style_token':'RED_CALLOUT' if '≠' in shot.callout else 'YELLOW_CALLOUT',
                        'z_index':30,'protagonist_role':'PRIMARY' if shot.protagonist.primary in ('TEXT','NUMBER') else 'SUPPORTING'}))
                # Section chrome is explicit compiler output, not a renderer-selected policy.
                clips.append(self._clip(shot, beat, 'TEXT', 'chrome', position={'x':.18,'y':.06},
                    metadata={'layer_kind':'CHROME','text':'XIAO-Y ／ EVIDENCE EDITORIAL',
                    'box':{'width':.34,'height':.05},'style_token':'CHROME','z_index':40,
                    'color':'#101319' if layout['background']=='#ffffff' else '#dce2ea',
                    'protagonist_role':'BACKGROUND'}))

        for index, cue in enumerate(source.captions):
            clips.append(EDTClip(clip_id=f'VRE-CAP-{index+1}', track='SUBTITLE', origin='FROZEN_SCRIPT',
                edit_source='AUDIO_TIMING_MAP', timeline_in=cue.start, timeline_out=cue.end,
                source_in=0, source_out=cue.end-cue.start, position={'x':.5,'y':.925},
                metadata={'layer_kind':'SUBTITLE','text':cue.text,'box':{'width':.88,'height':.08},
                'z_index':100,'protagonist_role':'SUPPORTING'}).model_dump())
        voice = next((a for a in source.assets if a.kind == 'VOICE'), None)
        if voice:
            clips.append(EDTClip(clip_id='VRE-VOICE', track='VOICE', asset_id=voice.asset_id,
                origin='FROZEN_VOICE', edit_source='AUDIO_TIMING_MAP', timeline_in=0,
                timeline_out=source.duration, source_in=0, source_out=source.duration,
                metadata={'asset_src':asset_map[voice.asset_id]['src'],'source_sha256':voice.sha256}).model_dump())
        font = next(a for a in source.assets if a.kind == 'FONT')
        ordered = sorted(clips, key=lambda c:(c['timeline_in'], c['metadata'].get('z_index', 0), c['clip_id']))
        props = {'fps':source.fps,'width':source.width,'height':source.height,
                 'duration_frames':math.ceil(source.duration*source.fps),'clips':ordered,
                 'font_src':asset_map[font.asset_id]['src'],'visual_mode':plan.visual_mode,
                 'shot_plan_id':plan.plan_id,'shot_plan_schema_version':plan.schema_version,
                 'source_script_id':plan.source_script_id}
        compiled_motion_artifact = None
        if motion_design is not None:
            props, compiled_motion_artifact = DeterministicMotionCompiler().compile(
                props, plan, motion_design)
        changes = [s.start for s in shots]
        aspect_ratio_qa = mechanical_asset_aspect_ratio_qa(props)
        motion_primitive_qa = mechanical_motion_primitive_qa(props)
        if motion_primitive_qa['verdict'] != 'PASS':
            issue = motion_primitive_qa['issues'][0]
            raise ValueError(f"{issue['code']}:{issue.get('primitive')}:{issue.get('layer_kind')}")
        motion_design_qa = ({'verdict':'NOT_RUN','check':'MOTION_DESIGN_CONTRACT','issues':[]}
                            if motion_design is None else mechanical_motion_design_qa(
                                props, motion_design, plan, motion_primitive_qa, aspect_ratio_qa))
        if motion_design_qa['verdict'] == 'FAIL':
            issue = motion_design_qa['issues'][0]
            raise ValueError(f"{issue['code']}:{issue.get('shot_id') or issue.get('clip_id')}")
        if motion_design is not None:
            props['motion_design_qa'] = motion_design_qa
            props['compiled_motion_artifact'] = compiled_motion_artifact
        diagnostics = {
            'status':'COMPILED_NOT_HUMAN_ACCEPTED','shot_count':len(shots),
            'visual_jobs':dict(Counter(b.visual_job for b in plan.beats)),
            'visual_modes':dict(Counter(b.visual_mode for b in plan.beats)),
            'shot_types':dict(Counter(s.shot_type for s in shots)),
            'evidence_treatments':dict(Counter(s.evidence_treatment for s in shots if s.evidence_treatment)),
            'character_roles':dict(Counter(s.character_role for s in shots if s.character_role!='NONE')),
            'motion_semantics':dict(Counter(s.motion_semantic for s in shots)),
            'primary_protagonists':dict(Counter(s.protagonist.primary for s in shots)),
            'seconds_since_last_visual_change':[round(b-a,3) for a,b in zip(changes,changes[1:])],
            'shot_duration':[round(s.end-s.start,3) for s in shots],
            'evidence_hold_duration':[round(s.end-s.start,3) for s in shots if s.evidence_asset_id],
            'reaction_duration':[round(s.end-s.start,3) for s in shots if s.character_role=='REACTION'],
            'primary_contract_pass':all(sum(1 for c in ordered if c.get('ir_node_id')==s.shot_id and
                c['metadata'].get('protagonist_role')=='PRIMARY')==1 for s in shots),
            'field_consumers':{
                'ShotPlan.schema_version':'remotion_props.shot_plan_schema_version',
                'ShotPlan.plan_id':'remotion_props.shot_plan_id',
                'ShotPlan.source_script_id':'compiler_guard + remotion_props.source_script_id',
                'ShotPlan.visual_mode':'compiler plan-wide mode override',
                'ShotBeat.beat_id':'EDTClip.beat_id + Storyboard Review',
                'ShotBeat.script_segment_id':'clip metadata + narration lookup',
                'ShotBeat.visual_job':'compatibility validation + clip metadata + Storyboard Review',
                'ShotBeat.visual_mode':'VisualCompiler layout recipe + clip metadata + Storyboard Review',
                'Shot.*':'VisualCompiler layer/timing/provenance + Storyboard Review',
            },
            'script_sha256':source.script_sha256,'voice_sha256':voice.sha256 if voice else None,
            'asset_aspect_ratio_qa':aspect_ratio_qa,
            'motion_primitive_qa':motion_primitive_qa,
            'motion_design_enabled':motion_design is not None,
            'motion_design_qa':motion_design_qa,
            'compiled_motion_artifact':compiled_motion_artifact,
        }
        if not diagnostics['primary_contract_pass']:
            raise ValueError('ONE_PRIMARY_CONTRACT_FAILED')
        return props, diagnostics


def mechanical_asset_aspect_ratio_qa(props: dict[str, Any]) -> dict[str, Any]:
    """Block non-uniform transforms of registered assets before render approval."""
    issues = []
    checked = 0
    for clip in props.get('clips', []):
        metadata = clip.get('metadata', {})
        if metadata.get('geometry_kind') != 'REGISTERED_ASSET':
            continue
        checked += 1
        transform = metadata.get('media_transform') or {}
        source_width = metadata.get('intrinsic_width')
        source_height = metadata.get('intrinsic_height')
        source_ratio = metadata.get('intrinsic_aspect_ratio')
        fit_mode = metadata.get('fit_mode')
        scale_x = transform.get('scale_x')
        scale_y = transform.get('scale_y')
        render_width = transform.get('render_width')
        render_height = transform.get('render_height')
        reasons = []
        if metadata.get('aspect_ratio_policy') != 'PRESERVE':
            reasons.append('aspect_ratio_policy must be PRESERVE')
        if fit_mode not in ('CONTAIN', 'COVER_CROP', 'FOCUS_CROP'):
            reasons.append('fit_mode must be CONTAIN, COVER_CROP, or FOCUS_CROP')
        numeric = (source_width, source_height, source_ratio, scale_x, scale_y,
                   render_width, render_height)
        if any(not isinstance(value, (int, float)) or value <= 0 for value in numeric):
            reasons.append('intrinsic dimensions or final media transform missing')
        else:
            scale_error = abs(scale_x - scale_y) / max(abs(scale_x), abs(scale_y))
            rendered_ratio = render_width / render_height
            ratio_error = abs(rendered_ratio / source_ratio - 1)
            intrinsic_error = abs((source_width / source_height) / source_ratio - 1)
            if scale_error > ASPECT_RATIO_TOLERANCE:
                reasons.append(f'non-uniform scale error {scale_error:.6f}')
            if ratio_error > ASPECT_RATIO_TOLERANCE:
                reasons.append(f'rendered/source ratio error {ratio_error:.6f}')
            if intrinsic_error > ASPECT_RATIO_TOLERANCE:
                reasons.append(f'intrinsic metadata ratio error {intrinsic_error:.6f}')
        if reasons:
            issues.append({
                'code':'ASSET_ASPECT_RATIO_DISTORTED', 'severity':'BLOCKER',
                'clip_id':clip.get('clip_id'), 'asset_id':clip.get('asset_id'),
                'reasons':reasons,
            })
    return {
        'verdict':'FAIL' if issues else 'PASS',
        'check':'ASSET_ASPECT_RATIO_INVARIANT',
        'tolerance_percent':ASPECT_RATIO_TOLERANCE * 100,
        'checked_registered_assets':checked,
        'issues':issues,
    }


def mechanical_motion_primitive_qa(props: dict[str, Any]) -> dict[str, Any]:
    """Reject vocabulary drift and unsupported primitive/layer combinations."""
    issues: list[dict[str, Any]] = []
    primitives = MOTION_PRIMITIVE_CONTRACT['primitives']
    for primitive, entry in primitives.items():
        if not entry.get('implemented') or not entry.get('renderer_consumer'):
            issues.append({
                'code': 'MOTION_PRIMITIVE_DECLARED_NOT_RENDERED',
                'severity': 'BLOCKER',
                'primitive': primitive,
                'layer_kind': None,
            })
    checked = 0
    emitted: Counter[str] = Counter()
    for clip in props.get('clips', []):
        if clip.get('track') == 'VOICE':
            continue
        checked += 1
        metadata = clip.get('metadata', {})
        layer_kind = metadata.get('layer_kind')
        primitive = (clip.get('motion') or {}).get('primitive') or metadata.get(
            'motion_primitive') or 'NONE'
        emitted[primitive] += 1
        entry = primitives.get(primitive)
        if entry is None:
            issues.append({
                'code': 'MOTION_PRIMITIVE_UNKNOWN', 'severity': 'BLOCKER',
                'clip_id': clip.get('clip_id'), 'primitive': primitive,
                'layer_kind': layer_kind,
            })
        elif layer_kind not in entry['allowed_layer_kinds']:
            issues.append({
                'code': 'MOTION_PRIMITIVE_UNSUPPORTED_FOR_LAYER', 'severity': 'BLOCKER',
                'clip_id': clip.get('clip_id'), 'primitive': primitive,
                'layer_kind': layer_kind,
                'allowed_layer_kinds': entry['allowed_layer_kinds'],
            })
    return {
        'verdict': 'FAIL' if issues else 'PASS',
        'check': 'MOTION_PRIMITIVE_CAPABILITY_CONTRACT',
        'contract_id': MOTION_PRIMITIVE_CONTRACT['contract_id'],
        'declared_primitive_count': len(primitives),
        'implemented_primitive_count': sum(bool(item.get('implemented') and
                                                  item.get('renderer_consumer'))
                                           for item in primitives.values()),
        'checked_visual_clips': checked,
        'emitted_primitives': dict(emitted),
        'issues': issues,
    }


def compile_fixture(input_path: Path, repo_root: Path, public_root: Path, output_dir: Path):
    source = VREInput.model_validate_json(input_path.read_text())
    plan = build_f2_shot_plan(source)
    props, diagnostics = VisualCompiler(repo_root, public_root).compile(source, plan)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir/'shot-plan.json').write_text(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2)+'\n')
    (output_dir/'renderer-neutral-edt.json').write_text(json.dumps({'schema_version':2,'clips':props['clips']},ensure_ascii=False,indent=2)+'\n')
    (output_dir/'remotion-props.json').write_text(json.dumps(props,ensure_ascii=False,indent=2)+'\n')
    (output_dir/'compiler-diagnostics.json').write_text(json.dumps(diagnostics,ensure_ascii=False,indent=2)+'\n')
    return plan, props, diagnostics
