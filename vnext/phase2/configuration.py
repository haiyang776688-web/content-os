"""Separate visual configuration from audio and UI settings."""
import json
from pathlib import Path
from vnext.storage.store import digest


def visual_payload(project):
    root=Path(__file__).resolve().parents[2]
    payload={key:getattr(project,key) for key in ('character_pack','style_pack','element_pack','render_profile')}
    for field,folder in (('character_pack','characters'),('style_pack','styles'),('element_pack','assets')):
        name=payload[field]
        if name:
            file=root/'registries'/folder/(name+'.json')
            if not file.is_file():raise ValueError('CONFIG_PACK_NOT_FOUND:'+name)
            payload[field+'_hash']=digest(json.loads(file.read_text()))
    return payload


def visual_config(store,pid):
    payload=visual_payload(store.get_project(pid))
    existing=store.latest(pid,'VISUAL_CONFIG')
    if existing and existing['output_hash']==digest(payload):return existing
    return store.create_artifact(pid,'VISUAL_CONFIG',payload,role='HUMAN').model_dump()
