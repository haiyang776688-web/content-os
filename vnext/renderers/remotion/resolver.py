"""Rebuildable EDT projection. Shared by the Player and formal Remotion export.
No artifact, project, gate or stage writes are permitted here.
"""
from __future__ import annotations
import json
import shutil
from pathlib import Path
from vnext.contracts import EDT
from vnext.storage.store import digest
from vnext.media.library.service import MediaLibrary
from vnext.migration.legacy import sha

RESOLVER_VERSION = "EDT_COMPOSITION_V1"

class CompositionResolver:
    def __init__(self, root, store):
        self.root, self.store = Path(root), store
        self.public = self.root / "vnext/renderers/remotion/project/public"

    def resolve(self, pid, edt_id):
        project = self.store.get_project(pid)
        artifact = self.store.get_artifact(edt_id)
        if artifact['project_id'] != pid or artifact['artifact_type'] != 'EDT':
            raise ValueError('INVALID_EDT_ARTIFACT')
        edt = EDT.model_validate({k:v for k,v in artifact['payload'].items() if k in EDT.model_fields})
        media = {a.asset_id:a for a in MediaLibrary(self.store).assets(pid)}
        dependencies = [self.store.latest(pid,k) for k in ('TYPOGRAPHY_PROFILE','PROJECT_FONT_SNAPSHOT','DIRECTOR_IR','MEDIA_SELECTION','VISUAL_CONFIG')]
        dependencies = [a for a in dependencies if a]
        files = {}
        clips = []
        for clip in edt.clips:
            value = clip.model_dump(mode='json')
            if clip.asset_id:
                asset = media.get(clip.asset_id)
                if not asset: raise ValueError('MISSING_MEDIA:'+clip.asset_id)
                path = Path(asset.original_path)
                if not path.is_file(): raise ValueError('OFFLINE_MEDIA:'+clip.asset_id)
                if sha(path) != asset.hash: raise ValueError('MEDIA_HASH_CHANGED:'+clip.asset_id)
                name = clip.asset_id+path.suffix.lower()
                files[name] = path
                value.update(asset_src=name, media_kind=asset.type)
            clips.append(value)
        derived={}
        for dependency in artifact['dependencies']:
            pinned=self.store.get_artifact(dependency['artifact_id'])
            if pinned['artifact_type'] in ('RESOLVED_VISUAL_COMPOSITION','AUDIO_TIMING_MAP'):
                derived[pinned['artifact_type'].lower()]=pinned['payload']
        script = self.store.get_artifact(project.h2_script_artifact_id) if project.h2_script_artifact_id else None
        props = dict(clips=clips,fallback_title=script['payload'].get('text','')[:50] if script else '',
            canvas_color=edt.canvas_color,foreground_color=edt.foreground_color,character_src=None,
            fps=edt.fps,width=edt.width,height=edt.height,
            duration_frames=max(1,round(max((c.timeline_out for c in edt.clips),default=5)*edt.fps)),phase2=project.phase2_enabled,
            timing_provenance=edt.timing_provenance or {'timing_mode':'CURRENT','fallback_used':False})
        if project.character_pack and not project.phase2_enabled:
            pack = self.root/'registries/characters'/(project.character_pack+'.json')
            if pack.is_file():
                path = self.root/'assets'/json.loads(pack.read_text())['actions'][0]['path']
                files['character.png']=path
                props['character_src']='character.png'
        if project.phase2_enabled:
            from vnext.phase2.fonts import Fonts
            fonts = Fonts(self.store).render_dependencies(pid)
            if not fonts: raise ValueError('TYPOGRAPHY_REQUIRED')
            font_items=[]
            for font in fonts['snapshot']['payload']['fonts']:
                path=Path(font['preview_path'])
                if not path.is_file(): raise ValueError('FONT_MISSING')
                if sha(path)!=font['preview_hash']: raise ValueError('FONT_RENDER_MISMATCH')
                name=font['preview_hash']+'.otf'
                files[name]=path
                font_items.append({**font,'src':name})
            props.update(typography=fonts['profile']['payload'],fonts=font_items)
        props.update(derived)
        fingerprint=digest(dict(resolver=RESOLVER_VERSION,edt=artifact['output_hash'],
            renderer_source=sha(Path(__file__).parent/'project/src/Composition.tsx'),
            dependencies=[(a['artifact_id'],a['output_hash']) for a in dependencies],
            files={name:sha(path) for name,path in files.items()},props=props))
        cache_key='PREVIEW-'+fingerprint[:32]
        public=self.public/cache_key
        public.mkdir(parents=True,exist_ok=True)
        for name,path in files.items():
            destination=public/name
            if not destination.is_file() or sha(destination)!=sha(path): shutil.copy2(path,destination)
        for c in props['clips']:
            if c.get('asset_src'): c['asset_src']=cache_key+'/'+c['asset_src']
        if props['character_src']: props['character_src']=cache_key+'/'+props['character_src']
        for f in props.get('fonts',[]): f['src']=cache_key+'/'+f['src']
        issues=[] if self.store.is_usable_input(edt_id) else ['STALE_EDT']
        state_semantics={'is_latest_revision':self.store.is_latest_revision(edt_id),'dependencies_valid':self.store.dependencies_valid(edt_id),'is_usable_input':self.store.is_usable_input(edt_id)}
        return dict(projection='PREVIEW_FRAME',canonical=False,resolver=RESOLVER_VERSION,
            edt_artifact_id=edt_id,edt_hash=artifact['output_hash'],cache_key=cache_key,
            fingerprint=fingerprint,props=props,issues=issues,state_semantics=state_semantics,
            dependencies=[dict(artifact_id=a['artifact_id'],output_hash=a['output_hash']) for a in dependencies])

    def frame(self,pid,edt_id,frame=0,selected_clip_id=None,safe_area=False):
        resolved=self.resolve(pid,edt_id)
        frame=max(0,min(int(frame),resolved['props']['duration_frames']-1))
        clips=resolved['props']['clips']
        selected=next((c for c in clips if c['clip_id']==selected_clip_id),None)
        return {**resolved,'frame':frame,'seconds':frame/resolved['props']['fps'],
            'visible_clip_ids':[c['clip_id'] for c in clips if not c['hidden'] and round(c['timeline_in']*resolved['props']['fps'])<=frame<round(c['timeline_out']*resolved['props']['fps'])],
            'selected_clip':selected,'safe_area':bool(safe_area)}
