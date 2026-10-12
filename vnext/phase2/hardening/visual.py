"""Semantic IR -> existing XVT template/pack resolution -> canonical EDT clips.
Only this production resolver assigns geometry. Preview never generates layout.
"""
import json,copy
from pathlib import Path
from vnext.storage.store import digest
from vnext.migration.legacy import sha
from vnext.contracts import EDTClip
from vnext.phase2.hardening.contracts import ResolvedVisualComposition
from vnext.media.library.service import MediaLibrary

ROOT=Path(__file__).resolve().parents[3]
SEMANTICS={'CHARACTER_EXPLAIN_KEYWORD':'EXPLAIN','CHARACTER_REACTION_MEDIA':'REACTION',
 'TIMELINE_PROCESS':'PROCESS','A_B_COMPARE':'COMPARE','SCREEN_DETAIL':'EVIDENCE',
 'THREE_POINT_SUMMARY':'SUMMARY','NUMBER_EMPHASIS':'NUMBER','CHARACTER_ACTION_SEQUENCE':'EXPLAIN'}
# Only semantically compatible variants are eligible. Explicit human template edits
# remain untouched; the allocator is used for beats without a template_id.
TEMPLATES_ALLOWED={
 'EXPLAIN':['CHARACTER_LEFT_TEXT_RIGHT','INFO_LEFT_CHARACTER_RIGHT','CHARACTER_CENTER','EXTREME_CLOSEUP'],
 'REACTION':['CHARACTER_SCREEN'],
 'EVIDENCE':['SCREEN_DETAIL_ZOOM','SCREEN_FULL_FRAME'],
 'COMPARE':['COMPARE_SPLIT'],
 'PROCESS':['KEYWORD_FULL_FRAME','INFO_LEFT_CHARACTER_RIGHT'],
 'NUMBER':['KEYWORD_FULL_FRAME','CHARACTER_CENTER'],
 'SUMMARY':['THREE_POINT_SUMMARY','INFO_LEFT_CHARACTER_RIGHT'],
 'CTA':['CTA_END_CARD'],
}
MAX_RECENT_REPEAT=2


def allocate_variant(candidates, recent_ids, beat_id, project_id, max_recent_repeat=MAX_RECENT_REPEAT):
    """Select a registered variant reproducibly, preferring ones not used recently."""
    choices=sorted(set(candidates))
    if not choices:raise ValueError('NO_COMPATIBLE_VISUAL_VARIANT')
    if len(choices)==1:return choices[0]
    recent=set(recent_ids[-max_recent_repeat:]) if max_recent_repeat else set()
    available=[choice for choice in choices if choice not in recent] or choices
    return available[int(digest([project_id,beat_id])[:16],16)%len(available)]


def allocate_action(intent,recent_action_ids,beat_id,project_id,actions,max_recent_repeat=MAX_RECENT_REPEAT):
    compatible=[action['id'] for action in actions if intent in action.get('semantic_intents',[])]
    return allocate_variant(compatible,recent_action_ids,beat_id,project_id,max_recent_repeat)


def allocate_template(semantic,recent_template_ids,beat_id,project_id,registered,has_character,has_media):
    candidates=[]
    for template_id in TEMPLATES_ALLOWED[semantic]:
        template=registered.get(template_id)
        if not template or template_id not in LAYOUTS:continue
        if template['media_slots'] and not has_media:continue
        if template['allowed_character_presence']==['PRESENT'] and not has_character:continue
        candidates.append(template_id)
    if not candidates and not has_character:
        # Existing character-less projects keep a valid fallback.
        fallback='SCREEN_FULL_FRAME' if has_media else 'KEYWORD_FULL_FRAME'
        if fallback in registered:candidates=[fallback]
    return allocate_variant(candidates,recent_template_ids,beat_id,project_id)
# Layout adapters for the twelve existing templates, not new Template Packs.
LAYOUTS={
 'CHARACTER_CENTER':{'character':[.5,.49,.65],'text':[.5,.16,.8]},
 'CHARACTER_LEFT_TEXT_RIGHT':{'character':[.2,.5,.88],'text':[.67,.32,.49]},
 'INFO_LEFT_CHARACTER_RIGHT':{'character':[.8,.5,.88],'text':[.32,.3,.49]},
 'CHARACTER_LOGO':{'character':[.2,.5,.88],'text':[.66,.18,.49],'media':[.66,.52,.45],'media_height':.48},
 'CHARACTER_SCREEN':{'character':[.18,.55,.65],'text':[.65,.17,.5],'media':[.65,.49,.54]},
 'EXTREME_CLOSEUP':{'character':[.25,.48,1.65],'text':[.72,.34,.42]},
 'KEYWORD_FULL_FRAME':{'text':[.5,.3,.8]},
 'SCREEN_FULL_FRAME':{'text':[.5,.15,.8],'media':[.5,.48,.86]},
 'SCREEN_DETAIL_ZOOM':{'text':[.5,.16,.8],'media':[.5,.5,.8],'media_height':.52},
 'COMPARE_SPLIT':{'character':[.5,.65,.5],'text':[.27,.38,.38],'second':[.73,.38,.38]},
 'THREE_POINT_SUMMARY':{'text':[.55,.27,.75]},
 'CTA_END_CARD':{'character':[.23,.52,.82],'text':[.68,.3,.48]}}

class VisualResolver:
    def __init__(self,store,root=ROOT):self.store,self.root=store,Path(root)
    def registry(self,kind,pack,pid=None):
        path=self.root/'registries'/kind/(pack+'.json')
        if pid:
            from vnext.phase2.hardening.dependencies import Dependencies
            service=Dependencies(self.store,self.root);old=self.store.latest(pid,'PROJECT_DEPENDENCY_MANIFEST')
            item=next((i for i in old['payload']['items'] if i['asset_id']==pack),None) if old else None
            if item:path=service.resolved(pid,pack,path,item['expected_hash'])
        if not path.is_file():raise ValueError('PACK_REGISTRY_MISSING:'+pack)
        return json.loads(path.read_text())
    def asset(self,record,pid=None):
        path=self.root/'assets'/record['path']
        if pid:
            from vnext.phase2.hardening.dependencies import Dependencies
            path=Dependencies(self.store,self.root).resolved(pid,record.get('asset_id') or record.get('id') or record.get('element_id'),path,record['sha256'])
        if not path.is_file():raise ValueError('PACK_ASSET_MISSING')
        if sha(path)!=record['sha256']:raise ValueError('PACK_ASSET_HASH_MISMATCH')
        return {'asset_id':record.get('asset_id') or record.get('id') or record.get('element_id'),
            'registry_path':record['path'],'resolved_location':str(path),'expected_hash':record['sha256'],'calibration':record.get('remotion',{}),
            'role':record.get('semantic_role','CHARACTER')}

    def plan(self,pid,ir):
        project=self.store.get_project(pid)
        style=self.registry('styles',project.style_pack,pid) if project.style_pack else None
        templates=self.registry('styles',style.get('template_pack') if style else 'XIAO-Y_TEMPLATES_V1',pid)
        registered={x['template_id']:x for x in templates['templates']}
        pack=self.registry('characters',project.character_pack,pid) if project.character_pack else None
        elements=self.registry('assets',project.element_pack,pid) if project.element_pack else None
        element_map={x['element_id']:x for x in (elements or {}).get('elements',[])}
        profile=self.store.latest(pid,'TYPOGRAPHY_PROFILE')
        dynamic=(profile or {}).get('payload',{}).get('presentation')=='XIAOY_EXPLAINER'
        result=[];clock=0;recent_actions=[];recent_templates=[]
        beats={b['beat_id']:b for b in ir['beats']}
        for scene in ir['scenes']:
            for bid in scene['beat_ids']:
                b=beats[bid];semantic=b.get('semantic_pattern') or SEMANTICS[b['pattern_id']]
                template_id=b.get('template_id') or allocate_template(
                    semantic,recent_templates,bid,pid,registered,bool(pack),bool(b['slots'].get('media_asset_id')))
                if template_id not in registered or template_id not in LAYOUTS:raise ValueError('TEMPLATE_NOT_REGISTERED')
                recent_templates.append(template_id)
                template=registered[template_id]
                from vnext.phase2.hardening.evidence import strict
                if strict(self.store,pid):
                    if template['media_slots'] and not b['slots'].get('media_asset_id'):raise ValueError('TEMPLATE_MEDIA_BINDING_REQUIRED')
                    if 'PRESENT' in template['allowed_character_presence'] and not pack:raise ValueError('TEMPLATE_CHARACTER_PACK_REQUIRED')
                layout=copy.deepcopy(LAYOUTS[template_id]);character=None
                if dynamic:
                    # Task opt-in; frozen template registries and standard layouts stay unchanged.
                    layout.update({'text':[.68,.35,.48]} if template_id in ('CHARACTER_LEFT_TEXT_RIGHT','EXTREME_CLOSEUP','CTA_END_CARD') else {})
                    if template_id=='INFO_LEFT_CHARACTER_RIGHT':layout.update(text=[.30,.35,.48],character=[.76,.49,1])
                    elif template_id=='CHARACTER_CENTER':layout.update(text=[.5,.14,.82],character=[.47,.51,.85])
                    elif template_id=='COMPARE_SPLIT':layout.update(text=[.25,.38,.38],second=[.75,.38,.38],character=[.48,.69,.33])
                    elif template_id=='KEYWORD_FULL_FRAME':layout.update(text=[.5,.42,.84])
                    elif template_id=='THREE_POINT_SUMMARY':layout.update(text=[.68,.27,.48],character=[.22,.49,1])
                    else:layout['character']=[.22,.49,1]
                    if template_id=='KEYWORD_FULL_FRAME' and semantic=='PROCESS':layout['text']=[.5,.24,.84]

                if pack and template['allowed_character_presence']!=['NONE']:
                    actions=pack['actions'];action_id=b.get('character_action_id')
                    if not action_id:
                        action_id=allocate_action(b.get('character_intent'),recent_actions,bid,pid,actions)
                    action=next((a for a in actions if a['id']==action_id),None)
                    if not action:raise ValueError('CHARACTER_ACTION_NOT_FOUND')
                    recent_actions.append(action['id'])
                    character={**self.asset(action,pid),'character_pack':project.character_pack,'action_id':action['id']}
                resolved_elements=[]
                for eid in b.get('element_ids',[]):
                    if eid not in element_map:raise ValueError('ELEMENT_NOT_REGISTERED')
                    resolved_elements.append({**self.asset(element_map[eid],pid),'element_id':eid})
                slots=b['slots']
                required={'COMPARE':['a','b'],'PROCESS':['steps'],'SUMMARY':['points'],'NUMBER':['number']}.get(semantic,[])
                if any(k not in slots for k in required):raise ValueError('SEMANTIC_SLOTS_REQUIRED:'+semantic)
                labels=[(b.get('keyword') or str(slots.get('keyword','')),'KEYWORD')]
                if semantic=='COMPARE':labels=[(str(slots['a']),'BODY'),(str(slots['b']),'BODY')]
                elif semantic=='PROCESS':labels=[(str(x),'BODY') for x in slots['steps']]
                elif semantic=='SUMMARY':labels=[(str(x),'BODY') for x in slots['points']]
                elif semantic=='NUMBER':labels=[(str(slots['number']),'NUMBER'),(b.get('keyword',''),'KEYWORD')]
                elif b['pattern_id']=='CHARACTER_ACTION_SEQUENCE':labels=[(str(x),'LABEL') for x in slots['actions']]
                text_slots=[{'slot_id':f'text-{i}','text':text,'role':role} for i,(text,role) in enumerate(labels) if text]
                media_slots=[{'slot_id':'media-0','asset_id':slots['media_asset_id'],
                    'source_in':float(slots.get('source_in',0)),'source_out':float(slots.get('source_out',float(slots.get('source_in',0))+b['timing_intent']))}] if slots.get('media_asset_id') else []
                timing={'start':clock,'end':clock+b['timing_intent'],'source':'DIRECTOR_ESTIMATE'}
                record=ResolvedVisualComposition(beat_id=bid,pattern_id=b['pattern_id'],template_id=template_id,
                    character=character,elements=resolved_elements,media_slots=media_slots,text_slots=text_slots,
                    typography_roles=list(dict.fromkeys([x['role'] for x in text_slots]+['SUBTITLE'])),layout=layout,
                    z_order=['MEDIA','CHARACTER','ELEMENT','TEXT','SUBTITLE'],timing=timing,
                    transforms={'normalized_coordinates':True,'object_fit':'contain','character_scale':layout.get('character',[0,0,1])[2]},
                    motions={'kind':b['motion_intent'],'reveal_order':b['reveal_order']},
                    safe_area={'left':.05,'right':.05,'top':.05,'bottom':.1},
                    overlap_allowed=[['CHARACTER','CHARACTER']] if template_id=='EXTREME_CLOSEUP' else [['MEDIA','TEXT']] if template_id=='SCREEN_FULL_FRAME' else []).model_dump()
                record.update(presentation='XIAOY_EXPLAINER' if dynamic else 'STANDARD',scene_id=b['scene_id'],segment_id=b['script_segment_id'],semantic_pattern=semantic)
                result.append(record);clock=timing['end']
        from vnext.phase2.hardening.audio import AudioClock
        clock=AudioClock(self.store);result=clock.retime(pid,ir,result)
        return {'resolver_version':'VISUAL_RESOLVER_V1','compositions':result,
            'template_pack':templates['template_pack_id'],'template_registry_hash':digest(templates),
            'character_registry_hash':digest(pack) if pack else None,'element_registry_hash':digest(elements) if elements else None,
            'style_registry_hash':digest(style) if style else None,'colors':(style or {}).get('colors',{}),
            'timing_provenance':clock.last_timing_provenance}

    def resolve(self,pid,ir_artifact):
        value=self.plan(pid,ir_artifact['payload'])
        dependencies=[ir_artifact['artifact_id']]
        for kind in ['TYPOGRAPHY_PROFILE','PROJECT_FONT_SNAPSHOT','VISUAL_CONFIG','MEDIA_SELECTION','AUDIO_TIMING_MAP']:
            a=self.store.latest(pid,kind)
            if a and self.store.is_usable_input(a['artifact_id']):dependencies.append(a['artifact_id'])
        timing=value.get('timing_provenance',{})
        if timing.get('timing_mode')=='ALIGNED':
            dependencies.append(timing['alignment_artifact_id'])
            binding=self.store.latest(pid,'BEAT_TIMING_BINDINGS')
            if binding and self.store.is_usable_input(binding['artifact_id']):dependencies.append(binding['artifact_id'])
        dependencies=list(dict.fromkeys(dependencies))
        old=self.store.latest(pid,'RESOLVED_VISUAL_COMPOSITION')
        if old and old['output_hash']==digest(value) and self.store.is_usable_input(old['artifact_id']):return old
        return self.store.create_artifact(pid,'RESOLVED_VISUAL_COMPOSITION',value,role='VISUAL_RESOLVER',
            dependencies=[self.store.dependency(aid) for aid in dependencies]).model_dump()

    def clips(self,pid,resolved):
        clips=[];library=MediaLibrary(self.store)
        for composition in resolved['payload']['compositions']:
            start,end=composition['timing']['start'],composition['timing']['end'];duration=end-start
            common=dict(scene_id=composition['scene_id'],beat_id=composition['beat_id'],ir_node_id=composition['beat_id'],
                origin='DIRECTOR_IR',edit_source='VISUAL_RESOLVER',pattern_id=composition['pattern_id'],
                timeline_in=start,timeline_out=end,source_out=duration)
            def clip(track,index,metadata=None,**values):
                cid='CLP-'+digest([resolved['output_hash'],composition['beat_id'],track,index])[:16]
                meta={'template_id':composition['template_id'],'resolved_composition_id':resolved['artifact_id'],
                      'overlap_allowed':composition['overlap_allowed'],**(metadata or {})}
                value=EDTClip(clip_id=cid,track=track,**{**common,**values},metadata=meta).model_dump()
                clips.append(value)
            layout=composition['layout'];dynamic=composition.get('presentation')=='XIAOY_EXPLAINER'
            for item in composition['media_slots']:
                x,y,w=layout.get('media',[.5,.45,.8])
                clip('MEDIA',item['slot_id'],{'box':{'width':w,'height':layout.get('media_height',.64)}},asset_id=item['asset_id'],
                    source_in=item['source_in'],source_out=item['source_out'],position={'x':x,'y':y},
                    motion={**composition['motions'],'continuous':'SLOW_ZOOM' if composition['semantic_pattern']=='EVIDENCE' else 'SLOW_PAN','amount':.035})
            character=composition['character']
            if character:
                source=Path(character['resolved_location']);media=library.register(pid,source,'IMAGE','MEDIA_RESOLVER','LOCAL_ONLY',source='CHARACTER_PACK')
                x,y,scale=layout.get('character',[.2,.5,.88])
                character_meta={'box':{'width':.52,'height':.78}} if dynamic else {}
                if dynamic:
                    # Fit visible alpha bounds, including wide gestures, within the chosen column.
                    iw,ih=map(float,media.resolution.split('x'))
                    W,H=1920,1080;ratio=min(W*.52/iw,H*.78/ih);w,h=iw*ratio,ih*ratio
                    cal=character['calibration']['content_bbox']
                    center=composition['template_id']=='CHARACTER_CENTER'
                    target_x=.5 if center or composition['template_id']=='COMPARE_SPLIT' else .76 if composition['template_id']=='INFO_LEFT_CHARACTER_RIGHT' else .24
                    target_y=.53 if center else .69 if composition['template_id']=='COMPARE_SPLIT' else .5
                    scale=min(scale,(.4 if center else .34)*W/(w*cal['w']),(.62 if center else .70)*H/(h*cal['h']))
                    x=target_x-(cal['x']+cal['w']/2-.5)*w/W*scale
                    y=target_y-(cal['y']+cal['h']/2-.5)*h/H*scale
                if dynamic and composition['template_id']=='EXTREME_CLOSEUP':
                    x,y,scale=.25,.43,1
                    character_meta={'box':{'width':.40,'height':.64},'portrait_window':{'x':.24,'y':0,'w':.6,'h':.62},'calibration':{}}
                clip('CHARACTER',0,{'action_id':character['action_id'],'character_pack':character['character_pack'],
                     'calibration':character['calibration'],**character_meta},asset_id=media.asset_id,position={'x':x,'y':y},scale=scale,
                     **({'motion':{**composition['motions'],**({'continuous':'SLOW_ZOOM','amount':.018}
                         if composition['semantic_pattern'] in ('REACTION','SUMMARY') or composition['template_id']=='EXTREME_CLOSEUP' else {})}} if dynamic else {}))
            for i,item in enumerate(composition['elements']):
                media=library.register(pid,Path(item['resolved_location']),'IMAGE','MEDIA_RESOLVER','LOCAL_ONLY',source='ELEMENT_PACK')
                clip('ELEMENT',i,{'element_id':item['element_id'],'box':{'width':.12,'height':.16}},asset_id=media.asset_id,position={'x':.5+i*.15,'y':.73})
            for i,item in enumerate(composition['text_slots']):
                x,y,w=layout.get('second',layout['text']) if i==1 and composition['template_id']=='COMPARE_SPLIT' else layout['text']
                if composition['template_id']!='COMPARE_SPLIT':
                    count=len(composition['text_slots'])
                    # Keep the last label above the subtitle band, even when a
                    # director supplies more process/action steps than expected.
                    step=.18 if dynamic else .15
                    if count>1:step=min(step,max(0,(.78-y)/(count-1)))
                    y+=i*step
                treatment=None
                if dynamic:
                    template=composition['template_id']
                    treatment={'kind':'MARKER' if item['role'] in ('KEYWORD','NUMBER','CTA') else 'CHECKLIST','index':i,'accent':'#FFD51E','ink':'#111111'}
                    if template=='COMPARE_SPLIT':treatment.update(kind='COMPARE',accent='#E9EAEC' if i==0 else '#FFD51E',header='A' if i==0 else 'B')
                    if composition['semantic_pattern']=='SUMMARY':treatment.update(kind='NUMBERED')
                    if template=='CHARACTER_CENTER':treatment.update(kind='UNDERLINE')
                    if template in ('EXTREME_CLOSEUP','KEYWORD_FULL_FRAME'):treatment['ink']='#F21E2C'
                display_text=item['text']
                if dynamic and treatment['kind'] in ('CHECKLIST','NUMBERED'):display_text=f"{i+1}  {display_text}"
                if dynamic and treatment['kind']=='COMPARE':display_text=treatment['header']+'\n'+display_text
                clip('TEXT',i,{'text':display_text,'typography_role':item['role'],'box':{'width':w},
                    'semantic_level':'PRIMARY' if i==0 else 'SECONDARY',**({'treatment':treatment} if dynamic else {})},position={'x':x,'y':y},
                    reveal={'delay':min(i*(duration/max(1,len(composition['text_slots'])+1) if dynamic else .8),duration*.65 if dynamic else duration*.4),'order':i},motion=composition['motions'])
        return clips
