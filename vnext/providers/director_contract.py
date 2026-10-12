"""Supply only registered resources to a real narrative director; no output rewriting."""
import json,copy
from pathlib import Path
from vnext.phase2.contracts import DirectorIR
from vnext.phase2.production import PATTERNS
from vnext.media.library.service import MediaLibrary

def request_contract(store,pid):
    project=store.get_project(pid);root=Path(__file__).resolve().parents[2]
    def registry(folder,name):
        return json.loads((root/'registries'/folder/(name+'.json')).read_text()) if name else {}
    pack=registry('characters',project.character_pack);elements=registry('assets',project.element_pack)
    action_ids=[a['id'] for a in pack.get('actions',[])];intents=sorted({i for a in pack.get('actions',[]) for i in a.get('semantic_intents',[])}) or ['EXPLAIN','GENERAL']
    element_ids=[e['element_id'] for e in elements.get('elements',[])]
    media=[a for a in MediaLibrary(store).assets(pid) if a.type in ('IMAGE','VIDEO','SCREENSHOT') and a.status=='ONLINE']
    media_ids=[a.asset_id for a in media]
    patterns=[p for p in PATTERNS if media_ids or 'media_asset_id' not in p.required_slots]
    schema=copy.deepcopy(DirectorIR.model_json_schema());schema['properties']['script_artifact_id']={'const':project.h2_script_artifact_id}
    props=schema['$defs']['Beat']['properties'];props['pattern_id']['enum']=[p.pattern_id for p in patterns]
    props['semantic_pattern']={'const':None};props['motion_intent']['enum']=['HOLD','FADE','SLIDE_UP'];props['template_id']={'const':None};props['character_action_id']={'enum':[None,*action_ids]};props['character_intent']['enum']=intents
    props['element_ids']['items']={'enum':element_ids} if element_ids else {'type':'string'}
    if not element_ids:props['element_ids']['maxItems']=0
    props['slots']['properties']={'media_asset_id':{'enum':media_ids} if media_ids else {'type':'null'}}
    for slot in ('keyword','a','b','number'):props['slots']['properties'][slot]={'type':'string','minLength':1}
    schema['$defs']['Beat']['allOf']=[{'if':{'properties':{'pattern_id':{'const':p.pattern_id}},'required':['pattern_id']},'then':{'properties':{'slots':{'required':p.required_slots}},'required':['slots']}} for p in patterns]
    props['reveal_order'].update(minItems=1,prefixItems=[{'const':'PRIMARY'}])
    for slot in ('steps','points','actions'):props['slots']['properties'][slot]={'type':'array','minItems':1,'items':{'type':'string'}}
    description={'locked_script_artifact_id':project.h2_script_artifact_id,'available_media_asset_ids':media_ids,
        'available_media':[{'asset_id':a.asset_id,'display_name':a.display_name,'type':a.type} for a in media],
        'available_character_action_ids':action_ids,'allowed_character_intents':intents,'available_element_ids':element_ids,'allowed_patterns':[p.model_dump() for p in patterns]}
    instructions='\nDIRECTOR INPUT CONTRACT: '+json.dumps(description,ensure_ascii=False)+'. Use the exact locked script ID and approved segment IDs. Never invent media/action/element IDs. Omit unavailable resources. Leave semantic_pattern and template_id null so the existing resolver selects its registered layout. Scene estimated_duration equals the sum of its beat timing_intent values. Keep display keywords and labels brief; steps, points and actions slots are lists of short strings. Semantic slot text and keywords must not add numbers absent from that approved segment. Timing seconds are only estimates and exempt from this content rule. CHARACTER_EXPLAIN_KEYWORD requires a nonempty slots.keyword even when beat.keyword is present; provide both. Every pattern required_slots entry must appear as a nonempty value inside slots. Specify narrative intent without pixel geometry.\nCREATIVE TASTE: Avoid slide/PPT-like visual sequencing and repeated character + headline + white-background beats. Prefer real evidence, screenshots, comparisons, process demonstrations and visible information-state changes when the approved material supports them. XIAO-Y need not lead every beat: when evidence, data or UI carries the information, let it take visual priority. Avoid repeating the same pose, pattern or composition structure. Never replace real evidence with generic whiteboard decoration. Each beat must reveal new information, not merely restate narration as text. When one approved segment contains two distinct visible information states, use two short beats for that same segment instead of one long static beat. Do not split a segment without a new information state.'
    return schema,instructions
