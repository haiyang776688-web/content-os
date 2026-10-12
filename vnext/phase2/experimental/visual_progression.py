"""VPS-001: compile manually authored visual states into ordinary EDT clips.

This module never writes project artifacts or changes DirectorIR. Screenshot crops
are pixel-preserving derivatives placed in Remotion's ignored preview directory.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Literal

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, model_validator

from vnext.contracts import EDTClip

Operation = Literal['FULL_FRAME_MEDIA', 'ZOOM_TO_REGION', 'HIGHLIGHT_RECT',
                    'CALLOUT_TEXT', 'SHOW_TEXT']
Region = tuple[float, float, float, float]
VISUAL_TRACKS = {'MEDIA', 'VIDEO', 'CHARACTER', 'ELEMENT', 'TEXT'}


class BeatRange(BaseModel):
    model_config = ConfigDict(extra='forbid')
    beat_id: str
    segment_id: str
    start: float
    end: float


class VisualState(BaseModel):
    model_config = ConfigDict(extra='forbid')
    state_id: str
    beat_id: str
    start: float
    end: float
    operation: Operation
    primary_subject: Literal['EVIDENCE', 'TEXT']
    media_asset_id: str
    region: Region | None = None
    focus: Region | None = None
    text: str | None = None

    @model_validator(mode='after')
    def required_data(self):
        if self.end <= self.start:
            raise ValueError('VISUAL_STATE_RANGE_INVALID')
        for name, value in [('region', self.region), ('focus', self.focus)]:
            if value and (len(value) != 4 or any(x < 0 or x > 1 for x in value)
                          or value[2] <= 0 or value[3] <= 0
                          or value[0] + value[2] > 1 or value[1] + value[3] > 1):
                raise ValueError('VISUAL_STATE_' + name.upper() + '_INVALID')
        if self.operation != 'FULL_FRAME_MEDIA' and not self.region:
            raise ValueError('VISUAL_STATE_REGION_REQUIRED')
        if self.operation == 'HIGHLIGHT_RECT' and not self.focus:
            raise ValueError('VISUAL_STATE_FOCUS_REQUIRED')
        if self.operation in ('CALLOUT_TEXT', 'SHOW_TEXT') and not self.text:
            raise ValueError('VISUAL_STATE_TEXT_REQUIRED')
        return self


class SubtitleRepair(BaseModel):
    model_config = ConfigDict(extra='forbid')
    start: float
    end: float
    text: str


class VisualProgression(BaseModel):
    """Spike-only contract. State times are absolute master-voice seconds."""
    model_config = ConfigDict(extra='forbid')
    source_start: float = Field(ge=0)
    source_end: float
    beats: list[BeatRange]
    states: list[VisualState]
    subtitle_repair: list[SubtitleRepair] = Field(default_factory=list)

    @model_validator(mode='after')
    def contiguous(self):
        if self.source_end <= self.source_start or not self.beats or not self.states:
            raise ValueError('VISUAL_PROGRESSION_EMPTY')
        if len({s.state_id for s in self.states}) != len(self.states):
            raise ValueError('VISUAL_STATE_ID_DUPLICATE')
        eps = .000001
        beat_map = {b.beat_id: b for b in self.beats}
        if len(beat_map) != len(self.beats):
            raise ValueError('VISUAL_BEAT_ID_DUPLICATE')
        cursor = self.source_start
        for beat in self.beats:
            if abs(beat.start - cursor) > eps or beat.end <= beat.start:
                raise ValueError('VISUAL_BEAT_GAP_OR_OVERLAP')
            cursor = beat.end
        if abs(cursor - self.source_end) > eps:
            raise ValueError('VISUAL_BEAT_END_MISMATCH')
        cursor = self.source_start
        counts = Counter()
        for state in self.states:
            beat = beat_map.get(state.beat_id)
            if not beat or abs(state.start - cursor) > eps or state.start < beat.start-eps or state.end > beat.end+eps:
                raise ValueError('VISUAL_STATE_GAP_OR_BEAT_MISMATCH')
            counts[state.beat_id] += 1
            cursor = state.end
        if abs(cursor - self.source_end) > eps or any(not 2 <= counts[b.beat_id] <= 4 for b in self.beats):
            raise ValueError('VISUAL_STATE_COUNT_OR_END_INVALID')
        return self


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def _overlap_clip(clip: dict, start: float, end: float) -> dict | None:
    left, right = max(float(clip['timeline_in']), start), min(float(clip['timeline_out']), end)
    if right <= left:
        return None
    result = copy.deepcopy(clip)
    original_duration = float(clip['timeline_out']) - float(clip['timeline_in'])
    rate = (float(clip['source_out']) - float(clip['source_in'])) / original_duration
    result['source_in'] = round(float(clip['source_in']) + (left-float(clip['timeline_in'])) * rate, 6)
    result['source_out'] = round(float(clip['source_in']) + (right-float(clip['timeline_in'])) * rate, 6)
    result['timeline_in'] = round(left-start, 6)
    result['timeline_out'] = round(right-start, 6)
    return result


def slice_props(source_props: dict, start: float, end: float) -> dict:
    result = copy.deepcopy(source_props)
    result['clips'] = [part for clip in source_props['clips']
                       if (part := _overlap_clip(clip, start, end)) is not None]
    result['duration_frames'] = math.ceil((end-start)*source_props['fps']-1e-7)
    return result


def _new_clip(state: VisualState, plan: VisualProgression, track: str, index: int, **values) -> dict:
    start, end = round(state.start-plan.source_start, 6), round(state.end-plan.source_start, 6)
    duration = round(end-start, 6)
    metadata = {'visual_state_id':state.state_id,
                'operation':state.operation, 'primary_subject':state.primary_subject,
                **values.pop('metadata',{})}
    motion = values.pop('motion',{'kind':'HOLD'})
    base = EDTClip(clip_id=f'VPS-{state.state_id}-{track}-{index}', track=track,
                   scene_id='VPS-001', beat_id=state.beat_id, ir_node_id=state.beat_id,
                   origin='VPS-001_EXPERIMENT', edit_source='HUMAN_GROUND_TRUTH',
                   timeline_in=start, timeline_out=end, source_in=0, source_out=duration,
                   motion=motion, metadata=metadata,
                   **values).model_dump()
    return base


def _crop_image(source: Path, region: Region, destination: Path):
    with Image.open(source) as image:
        width, height = image.size
        x, y, w, h = region
        box = (round(x*width), round(y*height), round((x+w)*width), round((y+h)*height))
        if box[2] <= box[0] or box[3] <= box[1]:
            raise ValueError('VISUAL_CROP_EMPTY')
        image.crop(box).save(destination)
        return box[2]-box[0], box[3]-box[1]


def _highlight_svg(destination: Path, focus: Region, source_size: tuple[int,int],
                   canvas: tuple[int,int], center_y: float, box: tuple[float,float]):
    cw, ch = canvas
    bw, bh = cw*box[0], ch*box[1]
    sw, sh = source_size
    factor = min(bw/sw, bh/sh)
    iw, ih = sw*factor, sh*factor
    left, top = (cw-iw)/2, center_y*ch-ih/2
    x, y, w, h = focus
    rect = (left+x*iw, top+y*ih, w*iw, h*ih)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{cw}" height="{ch}" viewBox="0 0 {cw} {ch}">'
           f'<rect x="{rect[0]:.1f}" y="{rect[1]:.1f}" width="{rect[2]:.1f}" height="{rect[3]:.1f}" '
           'rx="12" fill="none" stroke="#FFD51E" stroke-width="10"/>'
           '</svg>')
    destination.write_text(svg, encoding='utf-8')


def _subtitle_fix(clips: list[dict], plan: VisualProgression) -> list[dict]:
    if not plan.subtitle_repair:
        return clips
    repair_start = min(c.start for c in plan.subtitle_repair)-plan.source_start
    repair_end = max(c.end for c in plan.subtitle_repair)-plan.source_start
    prior = [c for c in clips if c['track']=='SUBTITLE' and
             c['timeline_in'] >= repair_start-.000001 and c['timeline_out'] <= repair_end+.000001]
    if not prior:
        raise ValueError('SUBTITLE_REPAIR_SOURCE_MISSING')
    original_text = ''.join(c['metadata']['text'] for c in prior)
    proposed_text = ''.join(c.text for c in plan.subtitle_repair)
    if original_text != proposed_text:
        raise ValueError('SUBTITLE_REPAIR_TEXT_CHANGED')
    repaired = [c for c in clips if c not in prior]
    template = prior[0]
    for i, cue in enumerate(plan.subtitle_repair):
        result = copy.deepcopy(template)
        result['clip_id'] = f'VPS-SUBTITLE-{i+1}'
        result['timeline_in'] = round(cue.start-plan.source_start,6)
        result['timeline_out'] = round(cue.end-plan.source_start,6)
        result['source_in'] = 0
        result['source_out'] = round(cue.end-cue.start,6)
        result['metadata']['text'] = cue.text
        result['metadata']['visual_state_id'] = 'SUBTITLE_REPAIR'
        repaired.append(result)
    return repaired


def compile_progression(source_props: dict, plan: VisualProgression,
                        public_root: Path, preview_name: str = 'PREVIEW-VPS-001') -> tuple[dict, dict, dict]:
    """Return A props, B props and diagnostics; no formal production artifact writes."""
    if not preview_name.startswith('PREVIEW-') or '/' in preview_name or '..' in preview_name:
        raise ValueError('VISUAL_PREVIEW_NAME_INVALID')
    a = slice_props(source_props, plan.source_start, plan.source_end)
    b = copy.deepcopy(a)
    b['canvas_color'] = '#101820'
    b['foreground_color'] = '#FFFFFF'
    old_media = {c['asset_id']: c for c in source_props['clips']
                 if c['track']=='MEDIA' and c.get('asset_id') and c.get('asset_src')}
    preview_dir = public_root/preview_name
    preview_dir.mkdir(parents=True, exist_ok=True)
    generated = []
    asset_hashes = {}
    for state in plan.states:
        if state.media_asset_id not in old_media:
            raise ValueError('VISUAL_STATE_EVIDENCE_NOT_IN_SOURCE')
        source_clip = old_media[state.media_asset_id]
        source = (public_root/source_clip['asset_src']).resolve()
        if not source.is_file() or not source.is_relative_to(public_root.resolve()):
            raise ValueError('VISUAL_STATE_EVIDENCE_FILE_MISSING')
        asset_hashes[state.media_asset_id] = _hash_file(source)
        center_y = .56 if state.text else .52
        box = (.92,.72)
        asset_src = source_clip['asset_src']
        size = None
        if state.region:
            crop_name = f'{state.media_asset_id}-{hashlib.sha256(str(state.region).encode()).hexdigest()[:12]}.png'
            crop_path = preview_dir/crop_name
            size = _crop_image(source, state.region, crop_path)
            asset_src = f'{preview_name}/{crop_name}'
        media = _new_clip(state,plan,'MEDIA',0,asset_id=state.media_asset_id,
                          position={'x':.5,'y':center_y},
                          motion=({'kind':'HOLD','continuous':'SLOW_ZOOM','amount':.018}
                                  if state.operation=='ZOOM_TO_REGION' else {'kind':'HOLD'}),
                          metadata={'box':{'width':box[0],'height':box[1]},
                                    'evidence_source_sha256':asset_hashes[state.media_asset_id],
                                    'evidence_region':state.region})
        media.update(asset_src=asset_src,media_kind='IMAGE')
        generated.append(media)
        if state.operation=='HIGHLIGHT_RECT':
            overlay_name = f'{state.state_id}-highlight.svg'
            overlay_path = preview_dir/overlay_name
            _highlight_svg(overlay_path,state.focus,size,(source_props['width'],source_props['height']),center_y,box)
            overlay = _new_clip(state,plan,'ELEMENT',1,position={'x':.5,'y':.5},
                                metadata={'box':{'width':1,'height':1},'visual_state_id':state.state_id})
            overlay.update(asset_src=f'{preview_name}/{overlay_name}',media_kind='IMAGE')
            generated.append(overlay)
        if state.text:
            text = _new_clip(state,plan,'TEXT',2,position={'x':.5,'y':.12},
                             metadata={'text':state.text,'typography_role':'KEYWORD',
                                       'box':{'width':.9},'visual_state_id':state.state_id})
            generated.append(text)
    # The semantic beat and its duration remain unchanged. Only visual clips
    # within the selected interval are replaced; subtitles and voice are reused.
    kept = [c for c in b['clips'] if c['track'] not in VISUAL_TRACKS]
    kept = _subtitle_fix(kept,plan)
    b['clips'] = generated + sorted(kept,key=lambda c:(c['timeline_in'],c['track']))
    for clip in b['clips']:
        EDTClip.model_validate({k:v for k,v in clip.items() if k not in ('asset_src','media_kind')})
    a_voice = [(c['asset_src'],c['source_in'],c['source_out'],c['timeline_in'],c['timeline_out'])
               for c in a['clips'] if c['track']=='VOICE']
    b_voice = [(c['asset_src'],c['source_in'],c['source_out'],c['timeline_in'],c['timeline_out'])
               for c in b['clips'] if c['track']=='VOICE']
    if not a_voice or a_voice != b_voice:
        raise ValueError('VISUAL_PROGRESSION_VOICE_CHANGED')
    voice_path = (public_root/a_voice[0][0]).resolve()
    diagnostics = {
        'source_start':plan.source_start,'source_end':plan.source_end,
        'duration':round(plan.source_end-plan.source_start,6),
        'beats':[beat.model_dump() for beat in plan.beats],
        'states':[state.model_dump() for state in plan.states],
        'states_per_beat':dict(Counter(s.beat_id for s in plan.states)),
        'max_visual_state_hold_a':max(round(beat.end-beat.start,6) for beat in plan.beats),
        'max_visual_state_hold_b':max(round(s.end-s.start,6) for s in plan.states),
        'average_visual_state_duration_b':round(sum(s.end-s.start for s in plan.states)/len(plan.states),6),
        'voice_sha256':_hash_file(voice_path),
        'evidence_sha256':asset_hashes,
        'subtitle_repair_text_preserved':bool(plan.subtitle_repair),
    }
    return a,b,diagnostics


def motion_off(props: dict) -> dict:
    result=copy.deepcopy(props)
    for clip in result['clips']:
        clip.get('motion',{}).pop('continuous',None)
        clip.get('motion',{}).pop('amount',None)
    return result


def write_experiment(source_props_path: Path, plan_path: Path,
                     public_root: Path, output_dir: Path):
    source=json.loads(source_props_path.read_text())
    plan=VisualProgression.model_validate_json(plan_path.read_text())
    a,b,diagnostics=compile_progression(source,plan,public_root)
    output_dir.mkdir(parents=True,exist_ok=True)
    for name,props in [('A',a),('B',b),('B-motion-off',motion_off(b))]:
        (output_dir/f'{name}-props.json').write_text(json.dumps(props,ensure_ascii=False,indent=2))
    (output_dir/'VPS-001-experimental-edt-clips.json').write_text(json.dumps([
        {k:v for k,v in clip.items() if k not in ('asset_src','media_kind')}
        for clip in b['clips']],ensure_ascii=False,indent=2))
    (output_dir/'diagnostics.json').write_text(json.dumps(diagnostics,ensure_ascii=False,indent=2))
    return diagnostics


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Compile a manual VisualProgression A/B experiment')
    parser.add_argument('--props',type=Path,required=True)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--public',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=write_experiment(args.props,args.plan,args.public,args.output)
    print(json.dumps({'duration':result['duration'],
                      'states_per_beat':result['states_per_beat'],
                      'output':str(args.output)},ensure_ascii=False))
