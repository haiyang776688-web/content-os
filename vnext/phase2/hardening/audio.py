"""Hash-pinned audio clock; no duration estimate qualifies as alignment."""
import re,copy
from pathlib import Path
from vnext.migration.legacy import sha
from vnext.storage.store import digest
from vnext.phase2.hardening.contracts import AudioTimingMap
from vnext.contracts import EDTClip

class AudioClock:
    def __init__(self,store):
        self.store=store
        self.last_timing_provenance={
            'timing_mode':'CURRENT','alignment_artifact_id':None,'alignment_artifact_sha':None,
            'engine':None,'engine_version':None,'model':None,'model_sha':None,'coverage':None,
            'fallback_used':False,'reason':'PRODUCTION_DEFAULT_CURRENT','applied':[]}
    def create(self,pid,payload,actor):
        if actor not in ('VOICE','ALIGNMENT'):raise PermissionError('AUDIO_TIMING_OWNER_REQUIRED')
        value=AudioTimingMap.model_validate(payload)
        voice=self.store.get_artifact(value.audio_artifact_id);script=self.store.get_artifact(value.script_artifact_id)
        p=self.store.get_project(pid)
        if any(x['project_id']!=pid or not self.store.is_usable_input(x['artifact_id']) for x in (voice,script)):raise ValueError('AUDIO_INPUT_STALE')
        if voice['artifact_type']!='VOICE' or script['artifact_type']!='SCRIPT' or p.h2_script_artifact_id!=script['artifact_id']:raise ValueError('APPROVED_SCRIPT_VOICE_REQUIRED')
        from vnext.media.library.service import MediaLibrary
        media=next((a for a in MediaLibrary(self.store).assets(pid) if a.asset_id==voice['payload']['media_asset_id']),None)
        original=voice['payload'].get('audio_path') or (media.original_path if media else '')
        from vnext.phase2.hardening.dependencies import Dependencies
        try:path=Dependencies(self.store).resolved(pid,voice['artifact_id'],original,value.audio_hash)
        except ValueError:raise ValueError('AUDIO_HASH_MISMATCH')
        if not path.is_file() or sha(path)!=value.audio_hash:raise ValueError('AUDIO_HASH_MISMATCH')
        # Validate physical duration rather than trusting the JSON declaration.
        from vnext.media.library.service import MediaLibrary
        probe=MediaLibrary._probe(path);duration=float(probe.get('duration') or 0)
        if not duration or abs(value.duration-duration)>.05 or abs(value.duration-voice['payload']['duration'])>.05:raise ValueError('AUDIO_DURATION_MISMATCH')
        prov=value.provenance
        if prov.get('method') not in ('PROVIDER_TIMESTAMPS','FORCED_ALIGNMENT','MANUAL_ALIGNMENT','TEST_ALIGNMENT','MEASURED_SEGMENT_BOUNDARIES') or not prov.get('worker') or not prov.get('version'):raise ValueError('ALIGNMENT_PROVENANCE_REQUIRED')
        if prov['method']=='MEASURED_SEGMENT_BOUNDARIES':
            measurements=voice['payload'].get('provenance',{}).get('segment_measurements',[])
            if len(measurements)!=len(value.entries):raise ValueError('SEGMENT_MEASUREMENTS_REQUIRED')
            clock=0
            for m,entry in zip(measurements,value.entries):
                file=Path(m['path'])
                if not file.is_file() or sha(file)!=m['sha256']:raise ValueError('SEGMENT_AUDIO_HASH_MISMATCH')
                measured=float(MediaLibrary._probe(file).get('duration') or 0)
                if entry.segment_id!=m['segment_id'] or abs(entry.start-clock)>.001 or abs(entry.duration-measured)>.001:raise ValueError('SEGMENT_AUDIO_DURATION_MISMATCH')
                clock+=measured
            if abs(clock-duration)>.05:raise ValueError('SEGMENT_MASTER_DURATION_MISMATCH')
        if prov['method']=='MANUAL_ALIGNMENT' and not prov.get('reviewer'):raise ValueError('ALIGNMENT_REVIEWER_REQUIRED')
        if prov['method']=='PROVIDER_TIMESTAMPS':
            original=voice['payload'].get('phrase_timestamps') or voice['payload'].get('word_timestamps')
            given=[r for e in value.entries for r in (e.phrase_ranges if voice['payload'].get('phrase_timestamps') else e.word_ranges)]
            if not original or digest(original)!=digest(given):raise ValueError('PROVIDER_TIMESTAMPS_NOT_PRESERVED')
        segments=script['payload'].get('segments',[])
        if [x.segment_id for x in value.entries]!=[s['segment_id'] for s in segments]:raise ValueError('AUDIO_SEGMENT_COVERAGE_REQUIRED')
        clock=0
        for entry,segment in zip(value.entries,segments):
            if entry.audio_id!=voice['payload']['media_asset_id'] or entry.start<clock-.001 or entry.end>value.duration+.001:raise ValueError('AUDIO_TIMING_RANGE_INVALID')
            clock=entry.end
            phrases=entry.phrase_ranges
            if not phrases:raise ValueError('PHRASE_TIMING_REQUIRED')
            clean=lambda t:re.sub(r'[\s，。！？；、,.!?;:：]','',t)
            if clean(''.join(r['text'] for r in phrases))!=clean(segment['text']):raise ValueError('PHRASE_SCRIPT_MISMATCH')
            last=entry.start
            for r in [*phrases,*entry.word_ranges]:
                if not r.get('text') or not isinstance(r.get('start'),(float,int)) or not isinstance(r.get('end'),(float,int)) or r['start']<entry.start or r['end']>entry.end or r['end']<=r['start']:raise ValueError('PHRASE_TIMING_INVALID')
            for r in phrases:
                if r['start']<last-.001:raise ValueError('PHRASE_TIMING_OVERLAP')
                last=r['end']
        payload=value.model_dump();payload['production_accepted']=voice['payload'].get('status')=='READY' and prov['method']!='TEST_ALIGNMENT'
        return self.store.create_artifact(pid,'AUDIO_TIMING_MAP',payload,role=actor,
            dependencies=[self.store.dependency(voice['artifact_id']),self.store.dependency(script['artifact_id'])]).model_dump()
    def from_voice(self,pid,voice_id):
        voice=self.store.get_artifact(voice_id);p=self.store.get_project(pid)
        script=self.store.get_artifact(p.h2_script_artifact_id)
        phrases=voice['payload'].get('phrase_timestamps');words=voice['payload'].get('word_timestamps')
        ranges=phrases or words
        if not ranges:raise ValueError('VOICE_TIMING_ALIGNMENT_REQUIRED')
        clean=lambda text:re.sub(r'[\s，。！？；、,.!?;:：]','',text)
        entries=[];index=0
        for segment in script['payload']['segments']:
            selected=[];accum='';target=clean(segment['text'])
            while index<len(ranges) and accum!=target:
                current=ranges[index];selected.append(current);accum+=clean(current['text']);index+=1
                if not target.startswith(accum):raise ValueError('PROVIDER_TIMESTAMPS_SEGMENT_ALIGNMENT_REQUIRED')
            if accum!=target or not selected:raise ValueError('PROVIDER_TIMESTAMPS_SEGMENT_ALIGNMENT_REQUIRED')
            start,end=selected[0]['start'],selected[-1]['end']
            entries.append({'audio_id':voice['payload']['media_asset_id'],'segment_id':segment['segment_id'],'start':start,'end':end,'duration':end-start,
                'phrase_ranges':selected if phrases else [{'text':segment['text'],'start':start,'end':end}],
                'word_ranges':[] if phrases else selected})
        if index!=len(ranges):raise ValueError('PROVIDER_TIMESTAMPS_SEGMENT_ALIGNMENT_REQUIRED')
        from vnext.media.library.service import MediaLibrary
        asset=next(a for a in MediaLibrary(self.store).assets(pid) if a.asset_id==voice['payload']['media_asset_id'])
        return self.create(pid,{'audio_artifact_id':voice_id,'script_artifact_id':script['artifact_id'],'audio_hash':asset.hash,'duration':voice['payload']['duration'],
            'provenance':{'method':'PROVIDER_TIMESTAMPS','worker':voice['payload']['provider'],'version':'PROVIDER_TIMESTAMP_MAPPING_V1','raw_timestamps_preserved':True},'entries':entries},'VOICE')

    def retime(self,pid,ir,compositions):
        amap=self.store.latest(pid,'AUDIO_TIMING_MAP')
        if not amap:return compositions
        if not self.store.is_usable_input(amap['artifact_id']) or amap['payload']['script_artifact_id']!=ir['script_artifact_id']:raise ValueError('AUDIO_TIMING_STALE')
        entries={e['segment_id']:e for e in amap['payload']['entries']};beats={b['beat_id']:b for b in ir['beats']}
        result=copy.deepcopy(compositions)
        if {c['segment_id'] for c in result}!=set(entries):raise ValueError('BEAT_AUDIO_SEGMENT_COVERAGE_REQUIRED')
        for sid,e in entries.items():
            selected=[c for c in result if c['segment_id']==sid];total=sum(beats[c['beat_id']]['timing_intent'] for c in selected);clock=e['start']
            for i,c in enumerate(selected):
                end=e['end'] if i==len(selected)-1 else clock+(e['end']-e['start'])*beats[c['beat_id']]['timing_intent']/total
                c['timing']={'start':clock,'end':end,'source':'AUDIO_TIMING_MAP','audio_timing_hash':amap['output_hash']};clock=end
        # FAI-001 is a narrow opt-in.  The semantic system has already created
        # every Beat; alignment may only move an approved existing boundary.
        from vnext.phase2.alignment.consumer import ExistingBeatTimingConsumer
        result,self.last_timing_provenance=ExistingBeatTimingConsumer(self.store).apply(pid,ir,result)
        return result
    def subtitles(self,pid,width=1920):
        amap=self.store.latest(pid,'AUDIO_TIMING_MAP')
        if not amap or not self.store.is_usable_input(amap['artifact_id']):raise ValueError('AUDIO_TIMING_REQUIRED')
        profile=self.store.latest(pid,'TYPOGRAPHY_PROFILE');font=profile['payload']['roles']['SUBTITLE']
        from vnext.phase2.hardening.geometry import measure_text
        compact=profile['payload'].get('presentation')=='XIAOY_EXPLAINER'
        result=[]
        for entry in amap['payload']['entries']:
            for phrase in entry['phrase_ranges']:
                text=re.sub(r'[，。！？；、,.!?;:：]','',phrase['text']).strip();chunks=[];part=''
                for char in (phrase['text'].strip() if compact else text):
                    if compact and char in '，。！？；、,.!?;:：':
                        if part:chunks.append(part);part=''
                        continue
                    if part and (compact and len(part)>=18 or measure_text(self.store,part+char,font)[0]>width*.9):chunks.append(part);part=''
                    part+=char
                if part:chunks.append(part)
                # Prefer supplied word ranges; otherwise visibly recorded proportional phrase split.
                weights=sum(len(c) for c in chunks);clock=phrase['start']
                for i,c in enumerate(chunks):
                    end=phrase['end'] if i==len(chunks)-1 else clock+(phrase['end']-phrase['start'])*len(c)/weights
                    cid='CLP-'+digest([amap['output_hash'],entry['segment_id'],phrase,c,i])[:16]
                    result.append(EDTClip(clip_id=cid,track='SUBTITLE',timeline_in=clock,timeline_out=end,source_out=end-clock,
                        edit_source='AUDIO_TIMING_MAP',origin='AUDIO_TIMING_MAP',position={'x':.5,'y':.91},
                        metadata={'text':c,'typography_role':'SUBTITLE','timing_source':'AUDIO_TIMING_MAP','audio_timing_hash':amap['output_hash'],
                            'split_provenance':'PROPORTIONAL_WITHIN_ALIGNED_PHRASE' if len(chunks)>1 else 'ALIGNED_PHRASE',
                            'single_line':True,'color':'#ffffff','background':None,'box':{'width':.9}}).model_dump())
                    clock=end
        return result
