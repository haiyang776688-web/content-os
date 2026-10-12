"""Narrative IR, owner-routed edits, storyboard approval and review references."""
from __future__ import annotations

import copy
import html
import json
import re
import subprocess
import uuid
from pathlib import Path

from vnext.contracts import EDT, EDTClip, utc_now
from vnext.core.editing import Editing
from vnext.core.runtime import Runtime
from vnext.media.library.service import MediaLibrary
from vnext.phase2.contracts import DirectorIR, EditCommand, QAItem, QAReport, TypographyProfile, VisualPattern
from vnext.phase2.fonts import Fonts
from vnext.phase2.knowledge import Knowledge, numbers
from vnext.storage.store import Store, canonical, digest


PATTERNS = [VisualPattern(pattern_id=id,semantic_purpose=purpose,required_slots=slots,
    layout_intent=layout,reveal_motion=['PRIMARY','SECONDARY','SUPPORTING'])
    for id,purpose,slots,layout in [
    ('CHARACTER_EXPLAIN_KEYWORD','Explain one idea',['keyword'],'CHARACTER_LEFT_KEYWORD_RIGHT'),
    ('CHARACTER_REACTION_MEDIA','React to evidence',['media_asset_id'],'CHARACTER_LEFT_MEDIA_RIGHT'),
    ('TIMELINE_PROCESS','Show a process',['steps'],'HORIZONTAL_SEQUENCE'),
    ('A_B_COMPARE','Compare conditions',['a','b'],'TWO_COLUMNS'),
    ('SCREEN_DETAIL','Highlight source evidence',['media_asset_id'],'MEDIA_WITH_FOCUS'),
    ('THREE_POINT_SUMMARY','Summarize three points',['points'],'THREE_ROWS'),
    ('NUMBER_EMPHASIS','Explain a source-bound number',['number'],'NUMBER_WITH_CONTEXT'),
    ('CHARACTER_ACTION_SEQUENCE','Explain actions',['actions'],'ACTION_SEQUENCE')]]
PATTERN_MAP = {x.pattern_id:x for x in PATTERNS}


def subtitle_chunks(text: str) -> list[str]:
    return [part.strip() for part in re.split(r'[，。！？；、,.!?;:：\n]+', text) if part.strip()]


def human_edits_present(store: Store, pid: str, target: str) -> bool:
    """Return whether a human edit remains after the last generated revision."""
    commands = [item['payload'] for item in store.artifacts(pid, 'EDIT_COMMAND')
                if item['payload'].get('target') == target]
    last_generation = -1
    for index, command in enumerate(commands):
        if command.get('operation') in ('GENERATE_REVISION', 'GENERATE', 'GENERATE_PRESERVING_AUDIO'):
            last_generation = index
    return any(command.get('actor_type') == 'HUMAN' and
               command.get('operation') not in ('GENERATE', 'GENERATE_PRESERVING_AUDIO')
               for command in commands[last_generation + 1:])


class Production:
    def __init__(self, store: Store):
        self.store = store
        self.knowledge = Knowledge(store)

    def ir(self, pid, payload, actor='DIRECTOR', extra_dependencies=None, run_metadata=None):
        if actor!='DIRECTOR': raise PermissionError('DIRECTOR_OWNER_REQUIRED')
        value = DirectorIR.model_validate(payload)
        self.knowledge.require_no_disagreement(pid)
        script = self.knowledge.require(pid,value.script_artifact_id,'SCRIPT')
        if self.store.get_project(pid).h2_script_artifact_id!=value.script_artifact_id:
            raise ValueError('H2_REQUIRED')
        segments = {s['segment_id'] for s in script['payload'].get('segments',[])}
        def no_pixels(obj):
            if isinstance(obj,dict):
                for key,v in obj.items():
                    if key in ('x','y','pixel_x','pixel_y','fontSize','font_family','fontFamily','font_size','font_id','fontId','font_path','font_file','absolute_asset_path','asset_path','position','scale','crop'):
                        raise ValueError('DIRECTOR_PIXEL_LAYOUT_FORBIDDEN')
                    if isinstance(v,str) and (v.startswith('/') or re.match(r'^[A-Za-z]:[\\/]',v)):raise ValueError('DIRECTOR_ABSOLUTE_PATH_FORBIDDEN')
                    no_pixels(v)
            elif isinstance(obj,list):
                for v in obj: no_pixels(v)
        no_pixels(payload)
        assets = {x.asset_id:x for x in MediaLibrary(self.store).assets(pid)}
        for beat in value.beats:
            if beat.script_segment_id not in segments: raise ValueError('SCRIPT_SEGMENT_MISSING')
            pattern = PATTERN_MAP.get(beat.pattern_id)
            if not pattern: raise ValueError('UNKNOWN_PATTERN')
            if not all(beat.slots.get(slot) for slot in pattern.required_slots):
                raise ValueError('PATTERN_SLOT_MISSING')
            if beat.slots.get('media_asset_id') and beat.slots['media_asset_id'] not in assets:
                raise ValueError('ASSET_GAP')
            if not beat.reveal_order or beat.reveal_order[0]!='PRIMARY':
                raise ValueError('REVEAL_ORDER_INVALID')
            segment = next(s for s in script['payload']['segments'] if s['segment_id']==beat.script_segment_id)
            semantic_slots={k:v for k,v in beat.slots.items() if k not in ('media_asset_id','source_in','source_out')}
            if set(numbers(str(semantic_slots)+' '+beat.keyword))-set(numbers(segment['text'])):
                raise ValueError('DIRECTOR_NUMBER_MISMATCH')
        for scene in value.scenes:
            if not set(scene.script_range)<=segments: raise ValueError('SCRIPT_SEGMENT_MISSING')
            duration = sum(b.timing_intent for b in value.beats if b.scene_id==scene.scene_id)
            if abs(duration-scene.estimated_duration)>.01: raise ValueError('SCENE_DURATION_MISMATCH')
        supplied=[d for d in (extra_dependencies or []) if self.store.get_artifact(d.artifact_id)['artifact_type']=='EFFECTIVE_SKILL_SNAPSHOT_DIRECTOR']
        snapshot=self.knowledge.require(pid,supplied[0].artifact_id) if supplied else self.knowledge.snapshot(pid,'DIRECTOR')
        deps=[self.store.dependency(value.script_artifact_id),self.store.dependency(snapshot['artifact_id']),*(extra_dependencies or [])]
        deps=list({d.artifact_id:d for d in deps}.values())
        return self.store.create_artifact(pid,'DIRECTOR_IR',value.model_dump(),role=actor,
            dependencies=deps, **(run_metadata or {})).model_dump()

    def design_table(self, pid):
        item = self.store.latest(pid,'DIRECTOR_IR')
        if not item: return {'source':None,'rows':[]}
        return {'source':item['artifact_id'],'source_hash':item['output_hash'],'read_only_projection':True,
                'rows':item['payload']['beats'],'scenes':item['payload']['scenes']}

    def edt_inputs(self, pid):
        """Include optional inputs when they first appear, not only after a prior EDT used them."""
        from vnext.phase2.configuration import visual_config
        inputs = [self.store.latest(pid, kind)['artifact_id'] for kind in
                  ('DIRECTOR_IR', 'TYPOGRAPHY_PROFILE', 'PROJECT_FONT_SNAPSHOT')]
        inputs.append(visual_config(self.store, pid)['artifact_id'])
        timing = self.store.latest(pid, 'AUDIO_TIMING_MAP')
        if timing:
            # An invalid clock must block the run rather than restore estimated timing.
            inputs.append(timing['artifact_id'])
        # Alignment is an optional timing refinement.  It participates in the
        # EDT cache only when the project explicitly opts in and the artifacts
        # are usable.  A missing, failed, stale, or blocked alignment therefore
        # keeps the deterministic CURRENT path renderable, while a newly READY
        # map/binding pair invalidates the prior CURRENT EDT cache entry.
        project = self.store.get_project(pid)
        if project.timing_mode == 'ALIGNED_OPT_IN':
            for kind in ('ALIGNED_TIMING_MAP', 'BEAT_TIMING_BINDINGS'):
                optional = self.store.latest(pid, kind)
                if optional and self.store.is_usable_input(optional['artifact_id']):
                    inputs.append(optional['artifact_id'])
        selection = self.store.latest(pid, 'MEDIA_SELECTION')
        if selection and self.store.is_usable_input(selection['artifact_id']):
            inputs.append(selection['artifact_id'])
        return inputs

    def generate_edt(self, pid):
        item = self.store.latest(pid,'DIRECTOR_IR')
        if not item: raise ValueError('DIRECTOR_IR_REQUIRED')
        self.knowledge.require(pid,item['artifact_id'],'DIRECTOR_IR')
        ir = DirectorIR.model_validate(item['payload'])
        profile = self.store.latest(pid,'TYPOGRAPHY_PROFILE')
        snapshot = self.store.latest(pid,'PROJECT_FONT_SNAPSHOT')
        if not profile or not snapshot: raise ValueError('TYPOGRAPHY_REQUIRED')
        self.knowledge.require(pid,snapshot['artifact_id'])
        script = self.store.get_artifact(ir.script_artifact_id)
        segments = {s['segment_id']:s for s in script['payload']['segments']}
        project_config=self.store.get_project(pid)
        from vnext.phase2.configuration import visual_config
        visual_config(self.store,pid)
        from vnext.phase2.hardening.visual import VisualResolver
        resolver=VisualResolver(self.store)
        resolved=resolver.resolve(pid,item)
        palette=resolved['payload']['colors']
        clips=[EDTClip.model_validate(c) for c in resolver.clips(pid,resolved)]
        # Legacy estimated captions remain available for old diagnostics. Strict
        # production replaces these exclusively from AudioTimingMap after voice.
        import re
        amap=self.store.latest(pid,'AUDIO_TIMING_MAP')
        for c in ([] if amap else resolved['payload']['compositions']):
            segment=segments[c['segment_id']]
            chunks=subtitle_chunks(segment['text'])
            start,end=c['timing']['start'],c['timing']['end'];duration=(end-start)/max(1,len(chunks))
            for i,text in enumerate(chunks):
                clips.append(EDTClip(clip_id='CLP-'+digest([resolved['output_hash'],c['beat_id'],'subtitle',i])[:16],
                    track='SUBTITLE',scene_id=c['scene_id'],beat_id=c['beat_id'],ir_node_id=c['beat_id'],
                    origin='DIRECTOR_IR',edit_source='VISUAL_RESOLVER',pattern_id=c['pattern_id'],
                    timeline_in=start+i*duration,timeline_out=start+(i+1)*duration,source_out=duration,
                    position={'x':.5,'y':.91},metadata={'text':text,'typography_role':'SUBTITLE','color':'#ffffff',
                        'background':None,'baseline':.91,'timing_source':'DIRECTOR_ESTIMATE',
                        'template_id':c['template_id'],'resolved_composition_id':resolved['artifact_id']}))
        if amap:
            from vnext.phase2.hardening.audio import AudioClock
            width=1280 if project_config.render_profile=='preview-720p' else 1920
            clips.extend(EDTClip.model_validate(c) for c in AudioClock(self.store).subtitles(pid,width))
            voice=self.store.get_artifact(amap['payload']['audio_artifact_id'])
            duration=amap['payload']['duration']
            clips.append(EDTClip(clip_id='CLP-'+digest([amap['output_hash'],'VOICE'])[:16],track='VOICE',asset_id=voice['payload']['media_asset_id'],source_out=duration,timeline_out=duration,origin='AUDIO_TIMING_MAP',edit_source='AUDIO_TIMING_MAP'))
        previous = self.store.latest(pid,'EDT')
        from vnext.phase2.configuration import visual_config
        binding=visual_config(self.store,pid)
        dependencies = [ir.script_artifact_id,item['artifact_id'],profile['artifact_id'],snapshot['artifact_id'],binding['artifact_id'],resolved['artifact_id']]
        if amap:
            # Final EDT explicitly binds both the measured clock and its voice.
            # A visual-only revision can preserve these edges without re-recording.
            dependencies.extend([voice['artifact_id'], amap['artifact_id']])
        selection=self.store.latest(pid,'MEDIA_SELECTION')
        if selection and self.store.is_usable_input(selection['artifact_id']):dependencies.append(selection['artifact_id'])
        timing_provenance=resolved['payload'].get('timing_provenance',{
            'timing_mode':'CURRENT','fallback_used':False,'reason':'PRODUCTION_DEFAULT_CURRENT'})
        if timing_provenance.get('alignment_artifact_id'):
            dependencies.append(timing_provenance['alignment_artifact_id'])
            binding=self.store.latest(pid,'BEAT_TIMING_BINDINGS')
            if binding and self.store.is_usable_input(binding['artifact_id']):dependencies.append(binding['artifact_id'])
        dependencies=list(dict.fromkeys(dependencies))
        edt = EDT(schema_version=2,edt_id='EDT-'+uuid.uuid4().hex[:12],project_id=pid,
            revision=previous['revision']+1 if previous else 1,clips=clips,source_artifacts=dependencies,
            timing_provenance=timing_provenance,
            typography_profile_id=profile['artifact_id'],typography_profile_hash=profile['output_hash'],
            canvas_color=palette.get('background','#ffffff'),foreground_color=palette.get('ink','#111111'),
            width=1280 if project_config.render_profile=='preview-720p' else 1920,
            height=720 if project_config.render_profile=='preview-720p' else 1080)
        artifact = self.store.create_artifact(pid,'EDT',edt.model_dump(),role='TIMELINE',
            dependencies=[self.store.dependency(x) for x in dependencies])
        from vnext.phase2.visual_state import visual_revision
        visual_revision(self.store,pid,edt.model_dump())
        project = self.store.get_project(pid)
        project.timeline_artifact_id = artifact.artifact_id
        self.store.save_project(project)
        return artifact.model_dump()

    def storyboard(self, pid, root: Path):
        from vnext.renderers.remotion.adapter import RemotionAdapter
        project = self.store.get_project(pid)
        ir = self.store.latest(pid,'DIRECTOR_IR')
        if not ir or not project.timeline_artifact_id: raise ValueError('DIRECTOR_EDT_REQUIRED')
        self.knowledge.require(pid,ir['artifact_id'])
        prepared = RemotionAdapter(root,self.store).prepare(pid,project.timeline_artifact_id,purpose='STORYBOARD')
        entries,clock = [],0.0
        by_id = {b['beat_id']:b for b in ir['payload']['beats']}
        for scene in ir['payload']['scenes']:
            for bid in scene['beat_ids']:
                b = by_id[bid]
                composition=next((c for c in prepared['props'].get('resolved_visual_composition',{}).get('compositions',[]) if c['beat_id']==bid),None)
                start,end=(composition['timing']['start'],composition['timing']['end']) if composition else (clock,clock+b['timing_intent'])
                frames=[round((start+min(.2,(end-start)/4))*prepared['props']['fps']),round(max(start,end-.1)*prepared['props']['fps'])]
                paths = []
                for index,frame in enumerate(frames):
                    path = self.store.root/'projects'/pid/'storyboards'/prepared['run_id']/f'{bid}-{index}.png'
                    path.parent.mkdir(parents=True,exist_ok=True)
                    process = subprocess.run(['npx','remotion','still','src/index.tsx','ContentOSPreview',str(path),
                        '--props',prepared['props_path'],'--frame',str(frame),*RemotionAdapter._browser_args()],
                        cwd=RemotionAdapter(root,self.store).project,capture_output=True,text=True,timeout=120)
                    if process.returncode: raise RuntimeError('STORYBOARD_RENDER_FAILED:'+process.stderr[-250:])
                    paths.append(str(path))
                entries.append({'scene_id':b['scene_id'],'beat_id':bid,'images':paths,
                    'pattern_id':b['pattern_id'],'character':b['character_intent'],'media':b['media_need'],
                    'keyword':b['keyword'],'warnings':[]})
                clock += b['timing_intent']
        # One read-only, offline overview makes adjacent pose/layout repetition
        # visible before any gate decision. It does not change the EDT or stills.
        contact_path=self.store.root/'projects'/pid/'storyboards'/prepared['run_id']/'contact-sheet.html'
        cards=''.join('<article><header>'+html.escape(entry['scene_id']+' / '+entry['beat_id'])+
            ' · '+html.escape(entry['pattern_id'])+'</header><div>'+''.join(
            '<figure><img src="'+html.escape(Path(image).name,quote=True)+'" alt="'+label+'"><figcaption>'+label+'</figcaption></figure>'
            for image,label in zip(entry['images'],('Start','End')))+'</div></article>' for entry in entries)
        contact_path.write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>Storyboard contact sheet</title>'
            '<style>body{font:14px system-ui;background:#151b22;color:#eee;margin:24px}h1{font-size:22px}'
            'main{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}article{background:#26313c;padding:9px}'
            'header{margin:4px 0 9px}article div{display:grid;grid-template-columns:1fr 1fr;gap:5px}'
            'figure{margin:0}img{width:100%;aspect-ratio:16/9;object-fit:contain;background:#fff}'
            'figcaption{text-align:center;color:#aebcca}@media(max-width:900px){main{grid-template-columns:1fr 1fr}}'
            '</style><h1>Storyboard · 全局分镜接触表</h1><main>'+cards+'</main></html>',encoding='utf-8')
        return self.store.create_artifact(pid,'STORYBOARD',{'ir_artifact_id':ir['artifact_id'],
            'ir_hash':ir['output_hash'],'entries':entries,'contact_sheet_path':str(contact_path)},role='STORYBOARD',
            dependencies=[self.store.dependency(self.store.latest(pid,'VISUAL_EDT')['artifact_id']),self.store.dependency(ir['artifact_id'])]).model_dump()

    def storyboard_gate(self,pid,storyboard_id,decision,reviewer,comments='',beat_ids=None):
        board = self.knowledge.require(pid,storyboard_id,'STORYBOARD')
        if decision not in ('APPROVE','REJECT','COMMENT') or not reviewer.strip():
            raise ValueError('INVALID_STORYBOARD_GATE')
        all_ids = {e['beat_id'] for e in board['payload']['entries']}
        selected = set(beat_ids or all_ids)
        if not selected<=all_ids: raise ValueError('UNKNOWN_BEAT')
        previous=self.store.latest(pid,'STORYBOARD_GATE')
        approved,rejected=set(),set()
        if previous and self.store.is_usable_input(previous['artifact_id']) and any(d['artifact_id']==storyboard_id for d in previous['dependencies']):
            approved=set(previous['payload'].get('approved_beats',previous['payload']['beat_ids'] if previous['payload']['all_beats_approved'] else []))
            rejected=set(previous['payload'].get('rejected_beats',[]))
        if decision=='APPROVE':approved|=selected;rejected-=selected
        if decision=='REJECT':
            if not comments.strip(): raise ValueError('REJECTION_REASON_REQUIRED')
            approved-=selected;rejected|=selected
            Runtime(self.store).change_request(pid,board['payload']['ir_artifact_id'],'HUMAN',comments)
        return self.store.create_artifact(pid,'STORYBOARD_GATE',{'decision':decision,'reviewer':reviewer,
            'comments':comments,'beat_ids':sorted(selected),'approved_beats':sorted(approved),'rejected_beats':sorted(rejected),
            'all_beats_approved':approved==all_ids and not rejected,
            'ir_hash':board['payload']['ir_hash'],'at':utc_now()},role='HUMAN',
            dependencies=[self.store.dependency(storyboard_id)]).model_dump()

    def require_storyboard(self,pid):
        self.knowledge.require_no_disagreement(pid)
        gate = self.store.latest(pid,'STORYBOARD_GATE')
        if not gate or not self.store.is_usable_input(gate['artifact_id']) or not gate['payload']['all_beats_approved']:
            raise ValueError('STORYBOARD_APPROVAL_REQUIRED')
        ir = self.store.latest(pid,'DIRECTOR_IR')
        if not ir or ir['output_hash']!=gate['payload']['ir_hash']: raise ValueError('STORYBOARD_APPROVAL_STALE')
        return gate


class CommandBus:
    def __init__(self,store):
        self.store=store
        with store.connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS edit_cursors(project_id TEXT,target TEXT,data TEXT,PRIMARY KEY(project_id,target))')

    def execute(self,pid,target,operation,args,actor='HUMAN',actor_type='HUMAN',reason='Manual edit',expected_revision=None):
        if actor_type not in ('HUMAN','AGENT','SYSTEM'): raise ValueError('INVALID_ACTOR_TYPE')
        if actor_type=='HUMAN' and actor!='HUMAN': raise PermissionError('ACTOR_ROLE_MISMATCH')
        owners={'EDT':'TIMELINE','DIRECTOR_IR':'DIRECTOR','TYPOGRAPHY_PROFILE':'TYPOGRAPHY',
                'SCRIPT':'SCRIPT_PRIMARY','MEDIA_SELECTION':'MEDIA_RESOLVER'}
        if target not in owners: raise ValueError('COMMAND_TARGET_UNSUPPORTED')
        if actor_type!='HUMAN' and actor!=owners[target] and not (target=='SCRIPT' and actor=='SCRIPT_EDITOR'):
            raise PermissionError('OWNER_CHANGE_REQUEST_REQUIRED')
        with self.store.lock:
            before = self.store.latest(pid,target)
            if expected_revision and (not before or before['artifact_id']!=expected_revision):
                raise ValueError('EDIT_REVISION_CONFLICT')
            regenerating = (target == 'DIRECTOR_IR' and operation == 'REPLACE_IR') or (
                target == 'EDT' and operation in ('GENERATE', 'GENERATE_PRESERVING_AUDIO'))
            if regenerating and before and human_edits_present(self.store, pid, target):
                if not args.get('discard_human_edits'):
                    raise ValueError('HUMAN_EDITS_PRESENT')
                if expected_revision != before['artifact_id']:
                    raise ValueError('EDIT_REVISION_CONFLICT')
            with self.store.connection() as db:
                row=db.execute('SELECT data FROM edit_cursors WHERE project_id=? AND target=?',(pid,target)).fetchone()
            cursor=json.loads(row['data']) if row else {'undo':[],'redo':[]}
            if operation in ('UNDO','REDO'):
                stack=cursor['undo' if operation=='UNDO' else 'redo']
                if not stack or not before: raise ValueError('NOTHING_TO_'+operation)
                restore=self.store.get_artifact(stack[-1])['payload']
                if target=='TYPOGRAPHY_PROFILE': result=Fonts(self.store).profile(pid,restore)
                elif target=='DIRECTOR_IR': result=Production(self.store).ir(pid,restore)
                elif target=='SCRIPT': result=Knowledge(self.store).bound_script(pid,restore,'HUMAN')
                elif target=='MEDIA_SELECTION':
                    from vnext.media.resolver.service import MediaResolver
                    result=MediaResolver(self.store).select(pid,restore['media_need'],restore['mode'],restore.get('selected_asset_id'))
                else:
                    if not self.store.is_usable_input(before['artifact_id']): raise ValueError('TIMELINE_STALE')
                    checked=EDT.model_validate({k:v for k,v in restore.items() if k in EDT.model_fields})
                    checked.revision=before['revision']+1
                    dependencies=Editing(self.store)._dependencies(pid,self.store.get_project(pid).h2_script_artifact_id,checked.clips)
                    payload=checked.model_dump();payload.update(last_operation=operation,source_artifacts=[d.artifact_id for d in dependencies])
                    from vnext.phase2.visual_state import visual_revision
                    visual_revision(self.store,pid,payload)
                    result=self.store.create_artifact(pid,'EDT',payload,role='TIMELINE',dependencies=dependencies).model_dump()
                    project=self.store.get_project(pid);project.timeline_artifact_id=result['artifact_id'];self.store.save_project(project)
                stack.pop();cursor['redo' if operation=='UNDO' else 'undo'].append(before['artifact_id'])
            elif target=='EDT':
                if operation in ('GENERATE','GENERATE_PRESERVING_AUDIO'):
                    audio=[c for c in (before or {}).get('payload',{}).get('clips',[]) if c['track'] in ('VOICE','BGM','SFX')] if operation=='GENERATE_PRESERVING_AUDIO' else []
                    result=Production(self.store).generate_edt(pid)
                    for clip in audio: result=Editing(self.store).edit_timeline(pid,'ADD',clip)
                else: result=Editing(self.store).edit_timeline(pid,operation,args)
            elif target=='SCRIPT':
                if operation=='REPLACE_SCRIPT':result=Knowledge(self.store).bound_script(pid,args['payload'],actor if actor_type!='HUMAN' else 'HUMAN')
                elif operation=='HUMANIZE':result=Knowledge(self.store).humanize(pid,args['original_id'],args['payload'])
                else: raise ValueError('UNKNOWN_OPERATION')
            elif target=='MEDIA_SELECTION':
                if operation!='SELECT':raise ValueError('UNKNOWN_OPERATION')
                from vnext.media.resolver.service import MediaResolver
                result=MediaResolver(self.store).select(pid,args['media_need'],args['mode'],args.get('selected_asset_id'))
            elif target=='DIRECTOR_IR':
                if operation=='REPLACE_IR':payload=args['payload']
                else:
                    if not before or not self.store.is_usable_input(before['artifact_id']): raise ValueError('STALE_INPUT')
                    payload=copy.deepcopy(before['payload'])
                    beat=next((b for b in payload['beats'] if b['beat_id']==args.get('beat_id')),None)
                    if not beat: raise ValueError('BEAT_NOT_FOUND')
                    if operation=='SET_BEAT':
                        permitted={'pattern_id','slots','character_intent','media_need','motion_intent','reveal_order','keyword',
                            'purpose','visual_focus','visual_form','retention_function','semantic_pattern','template_id','character_action_id','element_ids'}
                        if not set(args.get('changes',{}))<=permitted: raise ValueError('DIRECTOR_FIELD_FORBIDDEN')
                        beat.update(args['changes'])
                    elif operation=='SPLIT_BEAT':
                        if beat['timing_intent']<=0.4: raise ValueError('BEAT_TOO_SHORT_TO_SPLIT')
                        second=copy.deepcopy(beat)
                        second['beat_id']='BEAT-'+uuid.uuid4().hex[:12]
                        beat['timing_intent']/=2
                        second['timing_intent']=beat['timing_intent']
                        scene=next(s for s in payload['scenes'] if s['scene_id']==beat['scene_id'])
                        scene['beat_ids'].insert(scene['beat_ids'].index(beat['beat_id'])+1,second['beat_id'])
                        payload['beats'].insert(payload['beats'].index(beat)+1,second)
                    else: raise ValueError('UNKNOWN_OPERATION')
                result=Production(self.store).ir(pid,payload,extra_dependencies=[self.store.dependency(d['artifact_id'])
                    for d in before['dependencies'] if self.store.get_artifact(d['artifact_id'])['artifact_type']=='EFFECTIVE_SKILL_SNAPSHOT_DIRECTOR'] if before and operation in ('SET_BEAT','SPLIT_BEAT') else None)
            else:
                if operation=='SET_TYPOGRAPHY_PROFILE': payload=args['profile']
                else:
                    if not before: raise ValueError('TYPOGRAPHY_REQUIRED')
                    payload=copy.deepcopy(before['payload'])
                    role=args.get('role','SUBTITLE' if operation=='SET_SUBTITLE_FONT' else None)
                    if role not in payload['roles']: raise ValueError('UNKNOWN_FONT_ROLE')
                    if operation in ('SET_FONT_ROLE','SET_SUBTITLE_FONT'): payload['roles'][role].update(args['font'])
                    elif operation in ('SET_FONT_WEIGHT','SET_FONT_SIZE','SET_LETTER_SPACING'):
                        field={'SET_FONT_WEIGHT':'weight','SET_FONT_SIZE':'size','SET_LETTER_SPACING':'letter_spacing'}[operation]
                        payload['roles'][role][field]=args['value']
                    else: raise ValueError('UNKNOWN_OPERATION')
                result=Fonts(self.store).profile(pid,payload)
            if operation not in ('UNDO','REDO'):
                if before:cursor['undo'].append(before['artifact_id'])
                cursor['redo']=[]
            command=EditCommand(command_id='CMD-'+uuid.uuid4().hex[:12],project_id=pid,actor=actor,
                actor_type=actor_type,target=target,operation=operation,arguments=args,
                before_revision=before['artifact_id'] if before else None,after_revision=result['artifact_id'],
                timestamp=utc_now(),reason=reason)
            self.store.create_artifact(pid,'EDIT_COMMAND',command.model_dump(),role='COMMAND_BUS')
            with self.store.connection() as db:
                db.execute('INSERT OR REPLACE INTO edit_cursors VALUES (?,?,?)',(pid,target,json.dumps(cursor)))
            self.store.event(pid,'EDIT_COMMAND',**command.model_dump(exclude={'project_id','timestamp'}))
            return result

    def record_generated(self,pid,target,result,actor,before_id=None,reason='Role generated revision'):
        command=EditCommand(command_id='CMD-'+uuid.uuid4().hex[:12],project_id=pid,actor=actor,
            actor_type='AGENT',target=target,operation='GENERATE_REVISION',arguments={},
            before_revision=before_id,after_revision=result['artifact_id'],timestamp=utc_now(),reason=reason)
        self.store.create_artifact(pid,'EDIT_COMMAND',command.model_dump(),role='COMMAND_BUS')
        self.store.event(pid,'EDIT_COMMAND',**command.model_dump(exclude={'project_id','timestamp'}))


def mechanical(store:Store,pid,edt_id,require_voice=False):
    artifact=store.get_artifact(edt_id)
    issues=[]
    def issue(code,severity='BLOCKER',owner='TIMELINE',description=''):
        issues.append(QAItem(code=code,severity=severity,owner=owner,description=description or code))
    if artifact['project_id']!=pid or artifact['artifact_type']!='EDT': raise ValueError('INVALID_EDT')
    if not store.is_usable_input(edt_id): issue('ARTIFACT_STALE')
    for dependency in artifact['dependencies']:
        if not store.is_usable_input(dependency['artifact_id']): issue('DEPENDENCY_STALE',description=dependency['artifact_id'])
    project=store.get_project(pid)
    script=store.latest(pid,'SCRIPT');pack=store.latest(pid,'FACT_PACK')
    if project.phase2_enabled:
        if not script or not pack or not store.is_usable_input(script['artifact_id']) or not store.is_usable_input(pack['artifact_id']):
            issue('SCRIPT_FACT_NOT_CURRENT',owner='RESEARCH')
        else:
            facts={f['fact_id']:f for f in pack['payload']['facts']}
            for segment in script['payload'].get('segments',[]):
                if segment['claim'] and not segment['fact_ids']:issue('UNBOUND_CLAIM',owner='SCRIPT_PRIMARY')
                if any(fid not in facts or facts[fid]['support_status']!='SUPPORTED' for fid in segment['fact_ids']):
                    issue('FACT_NOT_SUPPORTED',owner='RESEARCH')
        if not script or project.h2_script_artifact_id!=script['artifact_id']:issue('H2_NOT_CURRENT',owner='HUMAN')
    edt=EDT.model_validate({k:v for k,v in artifact['payload'].items() if k in EDT.model_fields})
    from vnext.phase2.hardening.geometry import checks
    from vnext.phase2.hardening.evidence import strict
    issues.extend(QAItem.model_validate(x) for x in checks(store,pid,edt,strict(store,pid)))
    if strict(store,pid) and require_voice:
        amap=store.latest(pid,'AUDIO_TIMING_MAP')
        if not amap or not store.is_usable_input(amap['artifact_id']):issue('AUDIO_MASTER_CLOCK_REQUIRED',owner='ALIGNMENT')
        elif not amap['payload'].get('production_accepted'):issue('VOICE_PRODUCTION_NOT_ACCEPTED',owner='VOICE')
    assets={x.asset_id:x for x in MediaLibrary(store).assets(pid)}
    texts=[]
    profiles=store.latest(pid,'TYPOGRAPHY_PROFILE')
    for c in edt.clips:
        if c.hidden: continue
        if c.asset_id:
            a=assets.get(c.asset_id)
            if not a or not Path(a.original_path).is_file(): issue('OFFLINE_MEDIA',owner='MEDIA_RESOLVER',description=c.clip_id)
            elif a.duration and c.source_out>a.duration+.05: issue('SOURCE_RANGE_OUT_OF_BOUNDS',description=c.clip_id)
        if c.track in ('TEXT','SUBTITLE'):
            text=c.metadata.get('text','')
            role='SUBTITLE' if c.track=='SUBTITLE' else c.metadata.get('typography_role','BODY')
            if profiles and role not in profiles['payload']['roles']: issue('UNKNOWN_TYPOGRAPHY_ROLE',owner='TYPOGRAPHY')
            else: texts.append((role,text))
            if c.track=='SUBTITLE':
                if '\n' in text: issue('SUBTITLE_TWO_LINES',owner='SUBTITLE')
                if re.search(r'[，。！？；、,.!?;:：]',text): issue('SUBTITLE_PUNCTUATION',owner='SUBTITLE')
                if abs(c.position['y']-.91)>.001: issue('SUBTITLE_BASELINE',owner='SUBTITLE')
                if c.metadata.get('background'): issue('SUBTITLE_BACKGROUND',owner='SUBTITLE')
                if c.metadata.get('color','#ffffff').lower() not in ('#ffffff','white'): issue('SUBTITLE_COLOR',owner='SUBTITLE')
                if profiles:
                    font_role=profiles['payload']['roles']['SUBTITLE']
                    if not font_role.get('shadow'):issue('SUBTITLE_SHADOW_REQUIRED',owner='SUBTITLE')
                    # Glyph advances from the exact pinned font; conservative width before DOM verification.
                    snapshot=store.latest(pid,'PROJECT_FONT_SNAPSHOT')
                    font=next((x for x in snapshot['payload']['fonts'] if x['font_id']==font_role['font_id']),None) if snapshot else None
                    if font and Path(font['preview_path']).is_file():
                        from fontTools.ttLib import TTFont
                        f=TTFont(font['preview_path']); cmap=f.getBestCmap() or {}; units=f['head'].unitsPerEm
                        width=sum(f['hmtx'][cmap.get(ord(char),'.notdef')][0] for char in text)/units*font_role['size']
                        width+=max(0,len(text)-1)*font_role['letter_spacing']; f.close()
                        if width>edt.width*.9: issue('SUBTITLE_OVERFLOW',owner='SUBTITLE')
        if c.pattern_id and c.pattern_id not in PATTERN_MAP: issue('PATTERN_NOT_FOUND',owner='DIRECTOR')
        if c.track=='TEXT' and c.timeline_out-c.timeline_in>15: issue('STATIC_HOLD','WARNING','DIRECTOR')
    subtitles=sorted([c for c in edt.clips if c.track=='SUBTITLE' and not c.hidden],key=lambda c:c.timeline_in)
    if any(b.timeline_in<a.timeline_out-.001 for a,b in zip(subtitles,subtitles[1:])): issue('SUBTITLE_OVERLAP',owner='SUBTITLE')
    voices=[c for c in edt.clips if c.track=='VOICE' and c.asset_id and not c.muted and not c.hidden]
    ordered_voice=sorted(voices,key=lambda c:c.timeline_in)
    if any(b.timeline_in<a.timeline_out-.01 for a,b in zip(ordered_voice,ordered_voice[1:])):
        issue('VOICE_OVERLAP',owner='VOICE')
    if require_voice:
        if not voices: issue('MISSING_VOICE',owner='VOICE')
        elif max(c.timeline_out for c in voices)<max((c.timeline_out for c in edt.clips),default=0)-.2:
            issue('VOICE_DURATION_MISMATCH',owner='VOICE')
        if ordered_voice and (ordered_voice[0].timeline_in>.2 or any(b.timeline_in>a.timeline_out+.2 for a,b in zip(ordered_voice,ordered_voice[1:]))):
            issue('VOICE_TIMELINE_GAP',owner='VOICE')
        for c in voices:
            a=assets.get(c.asset_id)
            if not a or not Path(a.original_path).is_file(): continue
            cache=store.root/'audio_qa'/(a.hash+'.json');cache.parent.mkdir(parents=True,exist_ok=True)
            if cache.is_file(): data=json.loads(cache.read_text())
            else:
                proc=subprocess.run(['ffmpeg','-hide_banner','-i',a.original_path,'-af',
                    'volumedetect,silencedetect=n=-50dB:d=3','-f','null','-'],capture_output=True,text=True,timeout=60)
                peak=re.search(r'max_volume:\s*([\-\d.]+) dB',proc.stderr)
                data={'decode_ok':proc.returncode==0,'peak':float(peak.group(1)) if peak else None,
                      'long_silence':bool(re.search('silence_start:',proc.stderr))}
                cache.write_text(json.dumps(data))
            if not data['decode_ok']: issue('VOICE_DECODE_FAILED',owner='VOICE')
            if data['long_silence']: issue('VOICE_LONG_SILENCE',owner='VOICE')
            if data['peak'] is not None and data['peak']>-.1: issue('VOICE_CLIPPING','WARNING','VOICE')
    ir=store.latest(pid,'DIRECTOR_IR')
    primary={}
    for c in edt.clips:
        if c.metadata.get('semantic_level')=='PRIMARY' and c.beat_id and not c.hidden:
            key=(c.beat_id,c.timeline_in+float(c.reveal.get('delay',0)))
            primary[key]=primary.get(key,0)+1
    if any(count>1 for count in primary.values()):issue('SIMULTANEOUS_PRIMARY_REVEAL','WARNING','DIRECTOR')
    project_pack=project.character_pack
    if project_pack:
        registry=Path(__file__).resolve().parents[2]/'registries/characters'/(project_pack+'.json')
        supported={a['id'] for a in json.loads(registry.read_text())['actions']} if registry.is_file() else set()
        for c in edt.clips:
            if c.track=='CHARACTER' and c.metadata.get('action_id') and c.metadata['action_id'] not in supported:
                issue('UNSUPPORTED_CHARACTER_ACTION',owner='DIRECTOR',description=c.clip_id)
    if ir and len(ir['payload']['beats'])>=3:
        beats=ir['payload']['beats']
        if len({b['motion_intent'] for b in beats})==1: issue('MOTION_REPETITION','WARNING','DIRECTOR')
        if all(b['pattern_id']=='CHARACTER_EXPLAIN_KEYWORD' for b in beats): issue('KEYWORD_PATTERN_REPETITION','WARNING','DIRECTOR')
    # Inspect the actual resolved EDT, including explicit human overrides. A
    # repeated pair or three appearances within four adjacent beats is visible
    # even when the entire film does not use one pose or layout.
    def over_repeated(sequence):
        return any(a==b for a,b in zip(sequence,sequence[1:])) or any(
            len(window)==4 and max(window.count(value) for value in set(window))>=3
            for window in (sequence[i:i+4] for i in range(len(sequence)-3)))
    characters=sorted((c for c in edt.clips if c.track=='CHARACTER' and not c.hidden and c.metadata.get('action_id')),
        key=lambda c:(c.timeline_in,c.beat_id or ''))
    if over_repeated([c.metadata['action_id'] for c in characters]):
        issue('ACTION_REPETITION','WARNING','DIRECTOR')
    by_beat={}
    for c in sorted(edt.clips,key=lambda c:(c.timeline_in,c.beat_id or '')):
        if c.beat_id and not c.hidden and c.metadata.get('template_id'):
            by_beat.setdefault(c.beat_id,c.metadata['template_id'])
    if over_repeated(list(by_beat.values())):
        issue('TEMPLATE_REPETITION','WARNING','DIRECTOR')
    for c in edt.clips:
        if c.metadata.get('persistent_header'): issue('PERSISTENT_HEADER','WARNING','DIRECTOR')
    issues += [QAItem.model_validate(x) for x in Fonts(store).check(pid,texts)]
    verdict='FAIL' if any(x.severity=='BLOCKER' for x in issues) else 'PASS_WITH_RISK' if issues else 'PASS'
    return QAReport(verdict=verdict,issues=issues,checked_artifact_id=edt_id).model_dump()


class Review:
    def __init__(self,store): self.store=store

    def build(self,pid):
        kinds=['SCRIPT','FACT_PACK','AUDIT','DIRECTOR_IR','STORYBOARD','STORYBOARD_GATE','VOICE',
               'EDT','RENDER','MECHANICAL_QA','VIDEO_QA','TYPOGRAPHY_PROFILE','PROJECT_FONT_SNAPSHOT']
        references=[]
        for kind in kinds:
            item=self.store.latest(pid,kind)
            if not item: raise ValueError('REVIEW_ARTIFACT_MISSING:'+kind)
            Knowledge(self.store).require(pid,item['artifact_id'],kind)
            if kind in ('MECHANICAL_QA','VIDEO_QA') and item['payload']['verdict']=='FAIL': raise ValueError('QA_VETO')
            references.append(item)
        Production(self.store).require_storyboard(pid)
        render=next(x for x in references if x['artifact_type']=='RENDER')
        if render['payload'].get('media_type')!='video/mp4': raise ValueError('FINAL_VIDEO_REQUIRED')
        issues=[i for a in references if a['artifact_type'] in ('MECHANICAL_QA','VIDEO_QA')
                for i in a['payload']['issues'] if i.get('severity') in ('WARNING','BLOCKER')]
        sources=[a for a in self.store.artifacts(pid) if a['artifact_type'].startswith('SOURCE_') and self.store.is_usable_input(a['artifact_id'])]
        references+=sources
        exported=self.store.latest(pid,'EXPORT')
        if exported and self.store.is_usable_input(exported['artifact_id']):
            references.append(exported)
            if exported['payload'].get('font_dependencies'):
                issues.append({'code':'JIANYING_FONT_MAPPING_UNVERIFIED','severity':'WARNING','owner':'HUMAN',
                    'description':'Pinned font paths exist, but exact typography in the target editor has not been verified',
                    'start':0,'end':0})
            for loss in exported['payload'].get('typography_losses',[]):
                issues.append({'code':loss.get('code','JIANYING_TYPOGRAPHY_LOSS'),
                    'severity':'WARNING','owner':'EXPORT','description':str(loss), 'start':0,'end':0})
        for kind in ('RULE_CATALOG','VISUAL_CONFIG','MEDIA_SELECTION','EFFECTIVE_SKILL_SNAPSHOT_DIRECTOR'):
            item=self.store.latest(pid,kind)
            if item and self.store.is_usable_input(item['artifact_id']):references.append(item)
        import difflib
        versions=self.store.artifacts(pid,'SCRIPT')
        before=versions[-2] if len(versions)>1 else None
        diff='\n'.join(difflib.unified_diff(before['payload'].get('text','').splitlines(),
            self.store.latest(pid,'SCRIPT')['payload'].get('text','').splitlines())) if before else ''
        return self.store.create_artifact(pid,'REVIEW_PACK',{'references':[{'artifact_id':a['artifact_id'],
            'type':a['artifact_type'],'hash':a['output_hash']} for a in references],'risks':issues,
            'script_diff':{'before_artifact_id':before['artifact_id'] if before else None,'diff':diff},
            'h3_is_not_publish_authorization':True},role='REVIEW',
            dependencies=[self.store.dependency(a['artifact_id']) for a in references]).model_dump()

    def gate(self,pid,pack_id,decision,reviewer,accepted_risks=None,comments=''):
        pack=Knowledge(self.store).require(pid,pack_id,'REVIEW_PACK')
        if decision not in ('APPROVE','REJECT','APPROVE_WITH_RISK') or not reviewer.strip(): raise ValueError('INVALID_REVIEW_GATE')
        risks={x['code'] for x in pack['payload']['risks']}
        if decision=='APPROVE' and risks: raise ValueError('RISK_ACKNOWLEDGMENT_REQUIRED')
        if decision=='APPROVE_WITH_RISK' and (not risks or not risks<=set(accepted_risks or [])): raise ValueError('RISK_ACKNOWLEDGMENT_REQUIRED')
        if decision=='REJECT' and not comments.strip(): raise ValueError('REJECTION_REASON_REQUIRED')
        return self.store.create_artifact(pid,'REVIEW_GATE',{'decision':decision,'reviewer':reviewer,
            'accepted_risks':accepted_risks or [],'comments':comments,'at':utc_now(),'publish_authorized':False},
            role='HUMAN',dependencies=[self.store.dependency(pack_id)]).model_dump()
