from vnext.storage.store import digest


def visual_revision(store, pid, edt_payload):
    old=store.latest(pid,'VISUAL_EDT')
    gate=store.latest(pid,'STORYBOARD_GATE')
    director=store.latest(pid,'DIRECTOR_IR')
    # Once a human approved the storyboard, final audio retiming and downstream
    # timeline edits must not silently turn that upstream approval into a new
    # visual draft. Director changes still invalidate the gate through its IR edge.
    if (old and gate and director and gate['payload'].get('all_beats_approved')
            and gate['payload'].get('ir_hash')==director['output_hash']
            and store.is_usable_input(gate['artifact_id']) and store.is_usable_input(old['artifact_id'])):
        return old
    value={k:edt_payload[k] for k in ('fps','width','height','canvas_color','foreground_color','typography_profile_id','typography_profile_hash') if k in edt_payload}
    value['clips']=[c for c in edt_payload['clips'] if c['track'] not in ('VOICE','BGM','SFX')]
    if old and {**old['payload'],'canvas_color':old['payload'].get('canvas_color','#ffffff'),'foreground_color':old['payload'].get('foreground_color','#111111')}==value and store.is_usable_input(old['artifact_id']): return old
    dependencies=[]
    for kind in ('DIRECTOR_IR','TYPOGRAPHY_PROFILE','PROJECT_FONT_SNAPSHOT','MEDIA_SELECTION','VISUAL_CONFIG'):
        item=store.latest(pid,kind)
        if item: dependencies.append(store.dependency(item['artifact_id']))
    return store.create_artifact(pid,'VISUAL_EDT',value,role='TIMELINE',dependencies=dependencies).model_dump()
