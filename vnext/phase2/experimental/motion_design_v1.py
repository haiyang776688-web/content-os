"""MDC-001 renderer-neutral motion phrases and deterministic realization.

The semantic contract contains no frames, pixels, curves, CSS, or numeric
animation parameters.  Numeric realization belongs to the deterministic
compiler and is attached only to renderer-neutral EDT clips.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections import defaultdict
from typing import Any, Literal

from pydantic import Field, model_validator

from vnext.contracts import StrictModel

MotionPhraseIntent = Literal['EXPLAIN', 'FOCUS', 'IMPACT_WARN', 'CONNECT']
MotionRole = Literal['PRIMARY', 'SECONDARY', 'BACKGROUND']
PhaseSemantic = Literal['ANTICIPATION', 'PRIMARY_ACTION', 'IMPACT',
                        'SECONDARY_RESPONSE', 'SETTLE', 'HOLD']
RelativeOrder = Literal['BEFORE_PRIMARY', 'WITH_PRIMARY', 'AFTER_PRIMARY']
MotionStrength = Literal['SUBTLE', 'NORMAL', 'STRONG']

PHASE_ORDER = {
    'ANTICIPATION': 0, 'PRIMARY_ACTION': 1, 'IMPACT': 2,
    'SECONDARY_RESPONSE': 3, 'SETTLE': 4, 'HOLD': 5,
}


class MotionPhase(StrictModel):
    role: MotionRole
    phase_semantic: PhaseSemantic
    relative_order: RelativeOrder
    strength: MotionStrength


class MotionPhrase(StrictModel):
    phrase_id: str
    shot_id: str
    intent: MotionPhraseIntent
    motion_primary: Literal['PROTAGONIST_PRIMARY'] = 'PROTAGONIST_PRIMARY'
    motion_secondary: list[Literal['PROTAGONIST_SUPPORTING']] = Field(
        default_factory=lambda: ['PROTAGONIST_SUPPORTING'])
    motion_background: list[Literal['PROTAGONIST_BACKGROUND']] = Field(
        default_factory=lambda: ['PROTAGONIST_BACKGROUND'])
    phases: list[MotionPhase] = Field(min_length=2)

    @model_validator(mode='after')
    def coherent(self):
        primary = [phase for phase in self.phases if phase.role == 'PRIMARY' and
                   phase.phase_semantic in ('PRIMARY_ACTION', 'IMPACT')]
        if len(primary) != 1:
            raise ValueError('MOTION_PRIMARY_CONFLICT')
        ranks = [PHASE_ORDER[phase.phase_semantic] for phase in self.phases]
        # CONNECT intentionally lets restrained source context appear before
        # the primary relationship draw.  Its declared phase order still
        # follows the same monotonic vocabulary.
        if ranks != sorted(ranks):
            raise ValueError('MOTION_PHASE_INVALID_ORDER')
        return self


class MotionDesignPlan(StrictModel):
    schema_version: Literal[1] = 1
    contract_id: Literal['XIAOY_MOTION_DESIGN_V1'] = 'XIAOY_MOTION_DESIGN_V1'
    source_shot_plan_id: str
    phrases: list[MotionPhrase] = Field(min_length=1)

    @model_validator(mode='after')
    def unique_shots(self):
        shot_ids = [phrase.shot_id for phrase in self.phrases]
        if len(shot_ids) != len(set(shot_ids)):
            raise ValueError('DUPLICATE_MOTION_PHRASE_SHOT')
        return self


class MotionDesignResolver:
    """Project ShotPlan meaning into four small renderer-neutral phrases."""

    @staticmethod
    def _phrase(shot: Any) -> tuple[MotionPhraseIntent, list[MotionPhase]]:
        if shot.shot_type == 'RELATION_EXPLAIN':
            return 'CONNECT', [
                MotionPhase(role='BACKGROUND', phase_semantic='ANTICIPATION',
                            relative_order='BEFORE_PRIMARY', strength='SUBTLE'),
                MotionPhase(role='PRIMARY', phase_semantic='PRIMARY_ACTION',
                            relative_order='WITH_PRIMARY', strength='NORMAL'),
                MotionPhase(role='SECONDARY', phase_semantic='SECONDARY_RESPONSE',
                            relative_order='AFTER_PRIMARY', strength='SUBTLE'),
                MotionPhase(role='PRIMARY', phase_semantic='SETTLE',
                            relative_order='AFTER_PRIMARY', strength='SUBTLE'),
            ]
        if shot.shot_type == 'EVIDENCE_FOCUS':
            return 'FOCUS', [
                MotionPhase(role='PRIMARY', phase_semantic='ANTICIPATION',
                            relative_order='BEFORE_PRIMARY', strength='SUBTLE'),
                MotionPhase(role='PRIMARY', phase_semantic='PRIMARY_ACTION',
                            relative_order='WITH_PRIMARY', strength='NORMAL'),
                MotionPhase(role='SECONDARY', phase_semantic='SECONDARY_RESPONSE',
                            relative_order='AFTER_PRIMARY', strength='SUBTLE'),
                MotionPhase(role='PRIMARY', phase_semantic='SETTLE',
                            relative_order='AFTER_PRIMARY', strength='SUBTLE'),
            ]
        if shot.shot_type == 'CHARACTER_REACTION':
            return 'IMPACT_WARN', [
                MotionPhase(role='PRIMARY', phase_semantic='ANTICIPATION',
                            relative_order='BEFORE_PRIMARY', strength='SUBTLE'),
                MotionPhase(role='PRIMARY', phase_semantic='IMPACT',
                            relative_order='WITH_PRIMARY', strength='STRONG'),
                MotionPhase(role='SECONDARY', phase_semantic='SECONDARY_RESPONSE',
                            relative_order='AFTER_PRIMARY', strength='NORMAL'),
                MotionPhase(role='PRIMARY', phase_semantic='SETTLE',
                            relative_order='AFTER_PRIMARY', strength='SUBTLE'),
            ]
        return 'EXPLAIN', [
            MotionPhase(role='PRIMARY', phase_semantic='PRIMARY_ACTION',
                        relative_order='WITH_PRIMARY', strength='NORMAL'),
            MotionPhase(role='SECONDARY', phase_semantic='SECONDARY_RESPONSE',
                        relative_order='AFTER_PRIMARY', strength='SUBTLE'),
            MotionPhase(role='PRIMARY', phase_semantic='SETTLE',
                        relative_order='AFTER_PRIMARY', strength='SUBTLE'),
        ]

    def resolve(self, plan: Any) -> MotionDesignPlan:
        phrases = []
        for beat in plan.beats:
            for shot in beat.shots:
                intent, phases = self._phrase(shot)
                phrases.append(MotionPhrase(
                    phrase_id=f'MDC-{shot.shot_id}', shot_id=shot.shot_id,
                    intent=intent, phases=phases))
        return MotionDesignPlan(source_shot_plan_id=plan.plan_id, phrases=phrases)


# These numeric profiles are Compiler-owned.  They never appear in ShotPlan or
# the renderer-neutral MotionDesignPlan.
PRIMARY_PROFILES: dict[str, dict[str, list[dict[str, float]]]] = {
    'EXPLAIN': {
        'primitive_progress': [{'frame': 0, 'value': 0}, {'frame': 10, 'value': 1},
                               {'frame': 16, 'value': 1}],
        'uniform_scale': [{'frame': 0, 'value': 1}, {'frame': 10, 'value': 1.01},
                          {'frame': 16, 'value': 1}],
    },
    'FOCUS': {
        'primitive_progress': [{'frame': 0, 'value': 0}, {'frame': 4, 'value': 0},
                               {'frame': 12, 'value': 1}, {'frame': 18, 'value': 1}],
        'uniform_scale': [{'frame': 0, 'value': 1}, {'frame': 3, 'value': .985},
                          {'frame': 12, 'value': 1.015}, {'frame': 18, 'value': 1}],
    },
    'IMPACT_WARN': {
        'primitive_progress': [{'frame': 0, 'value': 0}, {'frame': 3, 'value': 0},
                               {'frame': 7, 'value': 1}, {'frame': 14, 'value': 1}],
        'uniform_scale': [{'frame': 0, 'value': 1}, {'frame': 3, 'value': .97},
                          {'frame': 7, 'value': 1.04}, {'frame': 14, 'value': 1}],
    },
    'CONNECT': {
        'primitive_progress': [{'frame': 0, 'value': 0}, {'frame': 5, 'value': 0},
                               {'frame': 14, 'value': 1}, {'frame': 19, 'value': 1}],
        'uniform_scale': [{'frame': 0, 'value': 1}, {'frame': 14, 'value': 1.01},
                          {'frame': 19, 'value': 1}],
    },
}


class DeterministicMotionCompiler:
    """Attach deterministic numeric phase realization to existing EDT clips."""

    EXCLUDED_LAYERS = {'BACKGROUND', 'CHROME', 'SUBTITLE'}

    @staticmethod
    def _secondary_profile(intent: str, index: int, before_primary: bool = False):
        if before_primary:
            start = 1 + index * 2
        else:
            start = {'EXPLAIN': 5, 'FOCUS': 8, 'IMPACT_WARN': 7, 'CONNECT': 15}[intent] + index * 2
        return {
            'primitive_progress': [
                {'frame': 0, 'value': 0}, {'frame': start, 'value': 0},
                {'frame': start + 8, 'value': 1}, {'frame': start + 13, 'value': 1},
            ],
            'uniform_scale': [
                {'frame': 0, 'value': 1}, {'frame': start, 'value': 1},
                {'frame': start + 8, 'value': 1.008}, {'frame': start + 13, 'value': 1},
            ],
            'opacity_multiplier': [
                {'frame': 0, 'value': 0}, {'frame': start, 'value': 0},
                {'frame': start + 8, 'value': 1}, {'frame': start + 13, 'value': 1},
            ],
            'phase_offset_frames': start,
        }

    @staticmethod
    def _sha(value: Any) -> str:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')).encode()
        return hashlib.sha256(encoded).hexdigest()

    def compile(self, props: dict[str, Any], plan: Any,
                design: MotionDesignPlan) -> tuple[dict[str, Any], dict[str, Any]]:
        if design.source_shot_plan_id != plan.plan_id:
            raise ValueError('MOTION_DESIGN_SHOT_PLAN_MISMATCH')
        result = copy.deepcopy(props)
        phrase_by_shot = {phrase.shot_id: phrase for phrase in design.phrases}
        clips_by_shot: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for clip in result['clips']:
            shot_id = clip.get('ir_node_id')
            primitive = ((clip.get('motion') or {}).get('primitive') or
                         clip.get('metadata', {}).get('motion_primitive') or 'NONE')
            if shot_id and clip.get('track') != 'VOICE' and clip['metadata'].get(
                    'layer_kind') not in self.EXCLUDED_LAYERS and primitive != 'NONE':
                clips_by_shot[shot_id].append(clip)

        compiled_rows = []
        for shot in [shot for beat in plan.beats for shot in beat.shots]:
            phrase = phrase_by_shot.get(shot.shot_id)
            if phrase is None:
                raise ValueError('MOTION_PRIMARY_MISSING:' + shot.shot_id)
            candidates = clips_by_shot[shot.shot_id]
            primary = [clip for clip in candidates if
                       clip['metadata'].get('protagonist_role') == 'PRIMARY']
            if len(primary) == 0:
                raise ValueError('MOTION_PRIMARY_MISSING:' + shot.shot_id)
            if len(primary) > 1:
                raise ValueError('MOTION_PRIMARY_CONFLICT:' + shot.shot_id)
            primary_clip = primary[0]
            primary_clip['metadata']['motion_design'] = {
                'contract_id': design.contract_id, 'phrase_id': phrase.phrase_id,
                'intent': phrase.intent, 'motion_role': 'PRIMARY',
                'phase_offset_frames': 0,
                **copy.deepcopy(PRIMARY_PROFILES[phrase.intent]),
            }
            secondaries = [clip for clip in candidates if clip is not primary_clip]
            secondary_index = 0
            for clip in secondaries:
                layer = clip['metadata'].get('layer_kind')
                before = phrase.intent == 'CONNECT' and layer == 'EVIDENCE'
                role = 'BACKGROUND' if before else 'SECONDARY'
                profile = self._secondary_profile(phrase.intent, secondary_index, before)
                if not before:
                    secondary_index += 1
                clip['metadata']['motion_design'] = {
                    'contract_id': design.contract_id, 'phrase_id': phrase.phrase_id,
                    'intent': phrase.intent, 'motion_role': role,
                    **profile,
                }
            compiled_rows.append({
                'shot_id': shot.shot_id, 'phrase_id': phrase.phrase_id,
                'intent': phrase.intent, 'primary_clip_id': primary_clip['clip_id'],
                'secondary_clip_ids': [clip['clip_id'] for clip in secondaries if
                                       clip['metadata']['motion_design']['motion_role'] == 'SECONDARY'],
                'background_context_clip_ids': [clip['clip_id'] for clip in secondaries if
                                                clip['metadata']['motion_design']['motion_role'] == 'BACKGROUND'],
            })
        artifact = {
            'schema_version': 1, 'contract_id': design.contract_id,
            'source_shot_plan_id': design.source_shot_plan_id,
            'design_sha256': self._sha(design.model_dump()),
            'shots': compiled_rows,
        }
        artifact['compiled_motion_sha256'] = self._sha({
            'artifact': artifact,
            'clips': [(clip['clip_id'], clip['metadata'].get('motion_design'))
                      for clip in result['clips'] if clip['metadata'].get('motion_design')],
        })
        return result, artifact


def mechanical_motion_design_qa(props: dict[str, Any], design: MotionDesignPlan,
                                plan: Any, primitive_qa: dict[str, Any],
                                aspect_qa: dict[str, Any]) -> dict[str, Any]:
    """Mechanical review of compiled phrase responsibility and phase offsets."""
    issues: list[dict[str, Any]] = []
    phrase_by_shot = {phrase.shot_id: phrase for phrase in design.phrases}
    for phrase in design.phrases:
        ranks = [PHASE_ORDER[phase.phase_semantic] for phase in phrase.phases]
        if ranks != sorted(ranks):
            issues.append({'code': 'MOTION_PHASE_INVALID_ORDER', 'severity': 'BLOCKER',
                           'shot_id': phrase.shot_id})
    by_shot: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for clip in props.get('clips', []):
        motion_design = clip.get('metadata', {}).get('motion_design')
        if motion_design:
            by_shot[clip.get('ir_node_id')].append(clip)
            if clip['metadata'].get('geometry_kind') == 'REGISTERED_ASSET':
                encoded = json.dumps(motion_design, sort_keys=True)
                if 'scale_x' in encoded or 'scale_y' in encoded:
                    issues.append({'code': 'MOTION_DESIGN_ASPECT_RATIO_VIOLATION',
                                   'severity': 'BLOCKER', 'clip_id': clip['clip_id']})
    for shot in [shot for beat in plan.beats for shot in beat.shots]:
        designed = by_shot.get(shot.shot_id, [])
        primaries = [clip for clip in designed if
                     clip['metadata']['motion_design']['motion_role'] == 'PRIMARY']
        if not primaries:
            issues.append({'code': 'MOTION_PRIMARY_MISSING', 'severity': 'BLOCKER',
                           'shot_id': shot.shot_id})
        elif len(primaries) > 1:
            issues.append({'code': 'MOTION_PRIMARY_CONFLICT', 'severity': 'BLOCKER',
                           'shot_id': shot.shot_id})
        phrase = phrase_by_shot.get(shot.shot_id)
        has_secondary_response = bool(phrase and any(
            phase.phase_semantic == 'SECONDARY_RESPONSE' for phase in phrase.phases))
        if has_secondary_response:
            for clip in designed:
                value = clip['metadata']['motion_design']
                if value['motion_role'] == 'SECONDARY' and value['phase_offset_frames'] <= 0:
                    issues.append({'code': 'SECONDARY_RESPONSE_WITHOUT_OFFSET',
                                   'severity': 'BLOCKER', 'clip_id': clip['clip_id']})
    if primitive_qa.get('verdict') != 'PASS':
        for issue in primitive_qa.get('issues', []):
            issues.append({'code': 'MOTION_DESIGN_UNSUPPORTED_PRIMITIVE',
                           'severity': 'BLOCKER', 'source_issue': issue})
    if aspect_qa.get('verdict') != 'PASS':
        for issue in aspect_qa.get('issues', []):
            issues.append({'code': 'MOTION_DESIGN_ASPECT_RATIO_VIOLATION',
                           'severity': 'BLOCKER', 'source_issue': issue})
    return {
        'verdict': 'FAIL' if issues else 'PASS',
        'check': 'MOTION_DESIGN_CONTRACT',
        'phrase_count': len(design.phrases),
        'compiled_shot_count': len(by_shot),
        'issues': issues,
    }
