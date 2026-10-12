"""Local scene/keyframe index; unknown semantics stay unknown until annotated."""
import re
import base64
import json
import subprocess
from pathlib import Path
from vnext.media.library.service import MediaLibrary
from vnext.phase2.contracts import QAItem, QAReport
from vnext.phase2.knowledge import Knowledge
from vnext.storage.store import digest


class AssetIntelligence:
    def __init__(self,store): self.store=store

    def analyze(self,pid,asset_id,annotation=None,*,annotation_source='USER'):
        asset=next((a for a in MediaLibrary(self.store).assets(pid) if a.asset_id==asset_id),None)
        if not asset or not Path(asset.original_path).is_file(): raise ValueError('MEDIA_OFFLINE')
        from vnext.migration.legacy import sha
        if sha(Path(asset.original_path))!=asset.hash: raise ValueError('MEDIA_HASH_CHANGED')
        if annotation_source not in ('USER','MODEL'): raise ValueError('UNKNOWN_ANNOTATION_SOURCE')
        folder=self.store.root/'media_intelligence'/asset.hash
        folder.mkdir(parents=True,exist_ok=True)
        cuts=[0.0]
        keyframes=[]
        if asset.type=='VIDEO':
            run=subprocess.run(['ffmpeg','-hide_banner','-i',asset.original_path,
                '-vf',"select='gt(scene,0.35)',showinfo",'-an','-f','null','-'],capture_output=True,text=True,timeout=120)
            if run.returncode: raise ValueError('VIDEO_DECODE_FAILED')
            cuts+=sorted(set(float(x) for x in re.findall(r'pts_time:([\d.]+)',run.stderr)))
            cuts=[x for x in cuts if x<(asset.duration or 0)]
        if asset.type in ('VIDEO','IMAGE','SCREENSHOT'):
            for i,at in enumerate(cuts[:20]):
                path=folder/f'keyframe-{i}.jpg'
                args=['ffmpeg','-y','-loglevel','error']
                if asset.type=='VIDEO': args+=['-ss',str(at)]
                process=subprocess.run([*args,'-i',asset.original_path,'-frames:v','1','-vf','scale=480:-1',str(path)],capture_output=True,timeout=20)
                if process.returncode: raise ValueError('KEYFRAME_DECODE_FAILED')
                keyframes.append({'at':at,'path':str(path)})
        annotation=annotation or {}
        allowed={'caption','objects','scene','activity','tags','transcript','scene_captions'}
        if not set(annotation)<=allowed: raise ValueError('ANNOTATION_FIELD_UNSUPPORTED')
        for field in ('objects','tags','scene_captions'):
            if field in annotation and not isinstance(annotation[field],list):raise ValueError('ANNOTATION_LIST_REQUIRED:'+field)
        if any(not isinstance(t,str) for field in ('objects','tags') for t in annotation.get(field,[])):
            raise ValueError('ANNOTATION_TEXT_REQUIRED')
        for caption in annotation.get('scene_captions',[]):
            if not isinstance(caption,dict) or not {'start','end','text'}<=set(caption):raise ValueError('SCENE_CAPTION_FIELDS_REQUIRED')
            if not 0<=caption['start']<caption['end']<=(asset.duration or 1):raise ValueError('SCENE_CAPTION_RANGE_INVALID')
        value={'asset_id':asset_id,'source_hash':asset.hash,'cloud_policy':asset.cloud_policy,
            'semantic_status':('MODEL_GENERATED' if annotation_source=='MODEL' else 'USER_ANNOTATED') if annotation else 'UNKNOWN',
            'annotation_source':annotation_source if annotation else None,
            'caption':annotation.get('caption',''),'objects':annotation.get('objects',[]),
            'scene':annotation.get('scene',''),'activity':annotation.get('activity',''),
            'tags':annotation.get('tags',[]),'transcript':annotation.get('transcript',''),
            'scene_captions':annotation.get('scene_captions',[]),'orientation':asset.resolution or 'UNKNOWN',
            'embedding':None,'keyframes':keyframes,'keyframe_limit':20,
            'virtual_clips':[{'source_asset_id':asset_id,'source_in':a,'source_out':b}
                for a,b in zip(cuts,[*cuts[1:],asset.duration or 1]) if b>a]}
        from vnext.phase2.embeddings import LocalEmbeddings
        description=' '.join([value['caption'],value['scene'],value['activity'],value['transcript'],
            *value['tags'],*value['objects'],*[c['text'] for c in value['scene_captions']]])
        value['embedding']=LocalEmbeddings().encode([description]) if description.strip() else None
        return self.store.create_artifact(pid,'ASSET_INTELLIGENCE_'+asset_id,value,role='MEDIA_RESOLVER').model_dump()

    def caption_cloud(self,pid,asset_id,upload_confirmed=False,gateway=None):
        """Explicit optional M3 vision call; no automatic cloud fallback for local media."""
        project=self.store.get_project(pid)
        asset=next((a for a in MediaLibrary(self.store).assets(pid) if a.asset_id==asset_id),None)
        if not asset:raise ValueError('MEDIA_NOT_FOUND')
        policies=(project.privacy_mode,asset.cloud_policy)
        if 'LOCAL_ONLY' in policies:raise PermissionError('LOCAL_ONLY_UPLOAD_FORBIDDEN')
        if 'ASK_BEFORE_UPLOAD' in policies and not upload_confirmed:raise PermissionError('UPLOAD_CONFIRMATION_REQUIRED')
        local=self.store.latest(pid,'ASSET_INTELLIGENCE_'+asset_id)
        if not local or not self.store.is_usable_input(local['artifact_id']):local=self.analyze(pid,asset_id)
        frames=local['payload']['keyframes'][:3]
        if not frames:raise ValueError('IMAGE_KEYFRAMES_REQUIRED')
        from vnext.contracts import ModelRequest,ModelMessage,Role
        from vnext.gateways.model.gateway import ModelGateway
        schema={'type':'object','additionalProperties':False,'required':['caption','objects','scene','activity','tags'],
            'properties':{k:{'type':'array','items':{'type':'string'}} if k in ('objects','tags') else {'type':'string'}
                for k in ('caption','objects','scene','activity','tags')}}
        blocks=[{'type':'IMAGE','uri':'data:image/jpeg;base64,'+base64.b64encode(Path(f['path']).read_bytes()).decode(),'mime_type':'image/jpeg'} for f in frames]
        request=ModelRequest(role=Role.MEDIA_RESOLVER,worker_profile='MINIMAX',prompt_version='ASSET_CAPTION_V1',
            system_prompt='Describe only visible objects/actions in the supplied image or keyframes. Do not infer identity or facts not visible. Use UNKNOWN where uncertain.',
            messages=[ModelMessage(role='user',content='Caption these keyframes for local media search.')],content_blocks=blocks,
            response_schema=schema,config={'cloud_policy':'ASK_BEFORE_UPLOAD' if 'ASK_BEFORE_UPLOAD' in policies else 'CLOUD_ALLOWED','upload_confirmed':upload_confirmed,'cost_confirmed':upload_confirmed})
        from vnext.phase2.hardening.model_runs import governed
        response=governed(gateway or ModelGateway(cache_dir=self.store.root/'cache/models'),self.store,pid,request)
        if not response.structured_output:raise ValueError('EMPTY_CLOUD_CAPTION')
        result=self.analyze(pid,asset_id,response.structured_output,annotation_source='MODEL')
        self.store.event(pid,'CLOUD_MEDIA_CAPTION_COMPLETED',asset_id=asset_id,keyframes_sent=len(frames),provider='MINIMAX')
        return result

    def search(self,pid,query):
        tokens=[x for x in re.split(r'\s+',query.casefold()) if x]
        result=[]
        from vnext.phase2.embeddings import LocalEmbeddings
        encoded=LocalEmbeddings().encode([query]) if query.strip() else None
        for item in self.store.artifacts(pid):
            if not item['artifact_type'].startswith('ASSET_INTELLIGENCE_') or not self.store.is_usable_input(item['artifact_id']): continue
            data=item['payload']
            searchable=' '.join([data['caption'],data['scene'],data['activity'],data.get('transcript',''),*data['tags'],*data['objects'],
                *[c['text'] for c in data.get('scene_captions',[])]]).casefold()
            embedding=data.get('embedding')
            if encoded and embedding and encoded['model_path']==embedding['model_path']:
                score=sum(a*b for a,b in zip(encoded['vectors'][0],embedding['vectors'][0]))
                if score>.2:result.append({**data,'similarity':score})
            elif tokens and all(t in searchable for t in tokens):result.append(data)
        result.sort(key=lambda x:x.get('similarity',0),reverse=True)
        return {'matches':result,'method':'LOCAL_SEMANTIC_EMBEDDING' if encoded else 'LOCAL_ANNOTATION_AND_TRANSCRIPT_SEARCH',
                'embedding_available':bool(encoded),'limitation':'Automatic captions require explicit cloud permission; semantic search requires a locally installed embedding model'}


def visual_review_copy(source,folder):
    """Deterministic silent copy: generated cloned speech is never a video-model input."""
    from vnext.migration.legacy import sha
    source=Path(source);folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    target=folder/(sha(source)+'.silent.mp4')
    if not target.is_file():
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-map','0:v:0','-c:v','copy','-an','-map_metadata','-1',str(target)],check=True,capture_output=True,timeout=120)
    streams=json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-of','json',str(target)],check=True,capture_output=True,text=True,timeout=15).stdout)['streams']
    if any(x['codec_type']=='audio' for x in streams) or not any(x['codec_type']=='video' for x in streams):raise ValueError('VIDEO_REVIEW_AUDIO_REMOVAL_FAILED')
    return target,{'review_media_sha256':sha(target),'original_render_sha256':sha(source),'audio_transmitted':False,'review_scope':'VISUAL_ONLY'}


class VisualQA:
    """Mock contract is explicit; configured real video adapters must prove VIDEO_INPUT."""
    def __init__(self,store): self.store=store

    def run(self,pid,render_id,worker='MOCK',issues=None,upload_confirmed=False,gateway=None):
        render=Knowledge(self.store).require(pid,render_id,'RENDER')
        if render['payload'].get('media_type')!='video/mp4': raise ValueError('VIDEO_REQUIRED')
        if not Path(render['payload']['preview_path']).is_file(): raise ValueError('VIDEO_MISSING')
        qa=self.store.latest(pid,'MECHANICAL_QA')
        if not qa or not self.store.is_usable_input(qa['artifact_id']) or qa['payload']['verdict']=='FAIL' or qa['payload']['checked_artifact_id']!=self.store.get_project(pid).timeline_artifact_id:
            raise ValueError('MECHANICAL_QA_REQUIRED')
        inputs=[render_id,qa['artifact_id']]
        for kind in ('SCRIPT','DIRECTOR_IR','EDT'):
            item=self.store.latest(pid,kind)
            if not item: raise ValueError(kind+'_REQUIRED')
            Knowledge(self.store).require(pid,item['artifact_id'])
            inputs.append(item['artifact_id'])
        if worker!='MOCK':
            project=self.store.get_project(pid)
            if project.privacy_mode=='LOCAL_ONLY':raise PermissionError('LOCAL_ONLY_UPLOAD_FORBIDDEN')
            from vnext.registries.catalog import worker_options
            option=next((w for w in worker_options('VIDEO_QA') if w['worker_id']==worker),None)
            if not option or option['disabled']:raise ValueError('VIDEO_WORKER_UNSUPPORTED')
            from vnext.contracts import ModelMessage, ModelRequest, Role
            from vnext.gateways.model.gateway import ModelGateway
            project=self.store.get_project(pid)
            if project.privacy_mode=='LOCAL_ONLY': raise PermissionError('LOCAL_ONLY_UPLOAD_FORBIDDEN')
            if project.privacy_mode=='ASK_BEFORE_UPLOAD' and not upload_confirmed:
                raise PermissionError('UPLOAD_CONFIRMATION_REQUIRED')
            assets=MediaLibrary(self.store).assets(pid)
            used={c['asset_id'] for c in self.store.latest(pid,'EDT')['payload']['clips'] if c.get('asset_id')}
            if any(a.asset_id in used and a.cloud_policy=='LOCAL_ONLY' and a.type!='AUDIO' for a in assets):
                raise PermissionError('LOCAL_ONLY_ASSET_IN_VIDEO')
            file,review_media=visual_review_copy(render['payload']['preview_path'],self.store.root/'projects'/pid/'videoqa_inputs')
            if file.stat().st_size>45*1024*1024: raise ValueError('VIDEO_TOO_LARGE_FOR_INLINE_INPUT')
            # No font files or FontRegistry paths are included in model context.
            context={kind:self.store.latest(pid,kind)['payload'] for kind in ('SCRIPT','DIRECTOR_IR')}
            context['EDT']={'clips':[{k:c[k] for k in ('clip_id','track','timeline_in','timeline_out') if k in c} for c in self.store.latest(pid,'EDT')['payload']['clips']]}
            context['review_scope']='VISUAL_ONLY; no audio is provided; audio quality is checked locally.'
            context['checked_artifact_id']=render_id
            request=ModelRequest(role=Role.VIDEO_QA,worker_profile=worker,prompt_version='VISUAL_QA_V2',
                system_prompt='You are an independent visual reviewer. Return timestamps and owner-routed issues only. Never rewrite products.',
                messages=[ModelMessage(role='user',content=json.dumps(context,ensure_ascii=False))],
                content_blocks=[{'type':'VIDEO','uri':'data:video/mp4;base64,'+base64.b64encode(file.read_bytes()).decode(),
                    'mime_type':'video/mp4'}],response_schema=QAReport.model_json_schema(),
                config={'cloud_policy':project.privacy_mode,'upload_confirmed':upload_confirmed,'cost_confirmed':upload_confirmed})
            from vnext.phase2.hardening.model_runs import governed
            response=governed(gateway or ModelGateway(cache_dir=self.store.root/'cache/models'),self.store,pid,request)
            returned=QAReport.model_validate(response.structured_output)
            if returned.checked_artifact_id!=render_id or returned.mock:
                raise ValueError('VIDEO_QA_SOURCE_BINDING_INVALID')
            items=returned.issues
        else:
            items=[QAItem.model_validate(x) for x in (issues or [])]
        edt=self.store.latest(pid,'EDT')
        duration=max(c['timeline_out'] for c in edt['payload']['clips'])
        if any(i.end<i.start or i.end>duration for i in items): raise ValueError('QA_TIMESTAMP_INVALID')
        if worker=='MOCK':
            items.append(QAItem(code='MOCK_VISUAL_QA',severity='WARNING',owner='HUMAN',
                description='Mock contract validation; visual quality was not reviewed by MiniMax',end=duration))
        report=QAReport(verdict='FAIL' if any(i.severity=='BLOCKER' for i in items) else 'PASS_WITH_RISK' if items else 'PASS',
            issues=items,mock=worker=='MOCK',checked_artifact_id=render_id)
        result=self.store.create_artifact(pid,'VIDEO_QA',report.model_dump(),role='VIDEO_QA',worker=worker,provenance=({**response.provider_metadata,'prompt_version':'VISUAL_QA_V2','skill_snapshot':None,'timestamp':__import__('vnext.contracts',fromlist=['utc_now']).utc_now(),**review_media} if worker!='MOCK' else {}),
            dependencies=[self.store.dependency(x) for x in inputs])
        from vnext.core.runtime import Runtime
        for i in items:
            if i.severity=='BLOCKER':
                target=self.store.latest(pid,{'DIRECTOR':'DIRECTOR_IR','TIMELINE':'EDT','SCRIPT_PRIMARY':'SCRIPT',
                    'VOICE':'VOICE','TYPOGRAPHY':'TYPOGRAPHY_PROFILE'}.get(i.owner,'EDT'))
                Runtime(self.store).change_request(pid,target['artifact_id'],'VIDEO_QA',i.description)
        return result.model_dump()
