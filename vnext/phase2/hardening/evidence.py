"""Source -> explicit spans -> facts -> individual script claims.
No source text is an instruction. No automatic Fact creation or rebinding.
"""
import re,hashlib
from vnext.contracts import utc_now
from vnext.phase2.hardening.contracts import EvidenceRef,ClaimUnit
from vnext.storage.store import digest

def text_hash(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()
def content_hash(source):
    return digest({'content':source.get('content') or source['excerpt'],
        'snapshot':source.get('snapshot',''),'pages':source.get('pages',{}),
        'transcript':source.get('transcript',[]),'duration':source.get('duration'),'file_id':source.get('file_id')})

def strict(store,pid):
    item=store.latest(pid,'ARCHITECTURE_POLICY')
    return bool(item and item['payload'].get('claim_integrity')=='CLAIM_LEVEL_V2')

class EvidenceIntegrity:
    def __init__(self,store):self.store=store
    def enable(self,pid,actor='HUMAN'):
        if actor!='HUMAN':raise PermissionError('HUMAN_POLICY_REQUIRED')
        if not self.store.get_project(pid).phase2_enabled:
            from vnext.phase2.knowledge import Knowledge
            Knowledge(self.store).initialize(pid)
        old=self.store.latest(pid,'ARCHITECTURE_POLICY')
        if old:return old
        return self.store.create_artifact(pid,'ARCHITECTURE_POLICY',
            {'claim_integrity':'CLAIM_LEVEL_V2','audio_clock':'AUDIO_TIMING_MAP',
             'legacy_artifacts_readable':True,'legacy_production_accepted':False},role=actor).model_dump()

    def source(self,pid,sid):
        source=self.store.latest(pid,'SOURCE_'+sid)
        if not source or not self.store.is_usable_input(source['artifact_id']) or source['payload']['status']!='AVAILABLE':raise ValueError('EVIDENCE_SOURCE_UNAVAILABLE')
        return source

    def evidence(self,pid,payload,actor='RESEARCH'):
        if actor!='RESEARCH':raise PermissionError('RESEARCH_ONLY_EVIDENCE')
        ref=EvidenceRef.model_validate(payload);source=self.source(pid,ref.source_id);data=source['payload']
        if ref.source_content_hash!=content_hash(data):raise ValueError('SOURCE_CONTENT_HASH_MISMATCH')
        if ref.excerpt_hash!=text_hash(ref.excerpt):raise ValueError('EVIDENCE_EXCERPT_HASH_MISMATCH')
        loc=ref.locator
        content=data.get('content') or data['excerpt']
        if loc.media_type=='PDF':
            content=data.get('pages',{}).get(str(loc.page))
            if content is None:raise ValueError('EVIDENCE_PAGE_MISSING')
        if loc.media_type=='WEB' and loc.snapshot!=data.get('snapshot'):raise ValueError('EVIDENCE_SNAPSHOT_MISMATCH')
        if loc.media_type in ('TEXT','PDF','WEB'):
            if loc.paragraph:
                paragraphs=content.split('\n\n')
                if loc.paragraph>len(paragraphs):raise ValueError('EVIDENCE_PARAGRAPH_MISSING')
                content=paragraphs[loc.paragraph-1]
            excerpt=content[loc.character_span.start:loc.character_span.end] if loc.character_span else content
            if excerpt!=ref.excerpt:raise ValueError('EVIDENCE_SPAN_MISMATCH')
        else:
            if not data.get('duration') or loc.end_time>data['duration']:raise ValueError('EVIDENCE_TIME_OUTSIDE_SOURCE')
            matching=[x for x in data.get('transcript',[]) if x.get('start',-1)>=loc.start_time and x.get('end',1e99)<=loc.end_time]
            if not matching or ' '.join(x['text'] for x in matching)!=ref.excerpt:raise ValueError('EVIDENCE_TRANSCRIPT_MISMATCH')
        value={**ref.model_dump(),'source_artifact_id':source['artifact_id'],'trust':'UNTRUSTED_SOURCE_DATA'}
        return self.store.create_artifact(pid,'EVIDENCE_'+ref.evidence_id,value,role=actor,
            dependencies=[self.store.dependency(source['artifact_id'])]).model_dump()

    def validate_facts(self,pid,facts):
        dependencies=[]
        for fact in facts:
            if not fact.evidence_ids:raise ValueError('FACT_EVIDENCE_REQUIRED:'+fact.fact_id)
            for eid in fact.evidence_ids:
                item=self.store.latest(pid,'EVIDENCE_'+eid)
                if not item or not self.store.is_usable_input(item['artifact_id']):raise ValueError('FACT_EVIDENCE_STALE:'+eid)
                if item['payload']['source_id'] not in fact.source_ids:raise ValueError('FACT_EVIDENCE_SOURCE_MISMATCH')
                dependencies.append(item['artifact_id'])
        return list(dict.fromkeys(dependencies))

    def claims(self,pid,script,facts,actor):
        segments={s.segment_id:s for s in script.segments};ids=set();deps=[];validated=[]
        if not script.claim_units:raise ValueError('CLAIM_UNITS_REQUIRED')
        for claim in script.claim_units:
            if claim.claim_id in ids:raise ValueError('DUPLICATE_CLAIM_ID')
            ids.add(claim.claim_id)
            segment=segments.get(claim.segment_id)
            if not segment or segment.text[claim.text_span.start:claim.text_span.end]!=claim.claim_text:raise ValueError('CLAIM_SPAN_MISMATCH')
            factual=claim.claim_type in ('FACTUAL','NUMERIC','ATTRIBUTION')
            if factual and (not claim.fact_ids or claim.support_status!='SUPPORTED'):raise ValueError('UNSUPPORTED_CLAIM:'+claim.claim_id)
            if claim.claim_type in ('OPINION','NON_CLAIM') and claim.fact_ids:raise ValueError('NON_FACTUAL_CLAIM_BINDING')
            if claim.claim_type=='PREDICTION' and claim.support_status=='SUPPORTED':raise ValueError('PREDICTION_NOT_ESTABLISHED_FACT')
            if claim.review_status!='PENDING':raise ValueError('PRODUCER_CANNOT_APPROVE_CLAIM')
            for fid in claim.fact_ids:
                if fid not in facts or facts[fid]['support_status']!='SUPPORTED':raise ValueError('CLAIM_FACT_NOT_SUPPORTED')
            evidence=' '.join(facts[fid]['statement'] for fid in claim.fact_ids)
            if factual and set(re.findall(r'\d+(?:\.\d+)?%?',claim.claim_text))-set(re.findall(r'\d+(?:\.\d+)?%?',evidence)):raise ValueError('CLAIM_NUMBER_MISMATCH')
            fact_artifacts=[self.store.latest(pid,'FACT_'+fid) for fid in claim.fact_ids]
            if any(not x or not self.store.is_usable_input(x['artifact_id']) for x in fact_artifacts):raise ValueError('CLAIM_FACT_STALE')
            validated.append((claim,fact_artifacts))
        # Validate the entire submission before producing any revisions.
        for claim,fact_artifacts in validated:
            old=self.store.latest(pid,'CLAIM_'+claim.claim_id);value=claim.model_dump()
            if old and old['output_hash']==digest(value) and self.store.is_usable_input(old['artifact_id']):item=old
            else:item=self.store.create_artifact(pid,'CLAIM_'+claim.claim_id,value,role=actor,
                dependencies=[self.store.dependency(x['artifact_id']) for x in fact_artifacts]).model_dump()
            deps.append(item['artifact_id'])
        return deps

    def coverage(self,pid,script_artifact):
        payload=script_artifact['payload'];source_entities=set()
        for s in self.store.artifacts(pid):
            if s['artifact_type'].startswith('SOURCE_') and self.store.is_usable_input(s['artifact_id']):source_entities.update(s['payload'].get('entities',[]))
        report=detect_claims(payload['segments'],payload.get('claim_units',[]),source_entities)
        report.update(script_artifact_id=script_artifact['artifact_id'],contract_version=payload.get('contract_version',1),
            semantic_review_required=True,detector='DETERMINISTIC_HEURISTIC_V1')
        if payload.get('contract_version',1)<2:report['issues'].append({'code':'LEGACY_SEGMENT_EVIDENCE','owner':'SCRIPT_PRIMARY'})
        report['verdict']='FAIL' if report['issues'] else 'PASS_WITH_RISK' if report['candidates'] else 'PASS'
        return self.store.create_artifact(pid,'CLAIM_COVERAGE_REPORT',report,role='CLAIM_VALIDATOR',
            dependencies=[self.store.dependency(script_artifact['artifact_id'])]).model_dump()

    def decide(self,pid,report_id,decisions,actor,reviewer):
        report=self.store.get_artifact(report_id)
        if actor not in ('AUDIT','HUMAN') or not reviewer.strip():raise PermissionError('COVERAGE_REVIEWER_REQUIRED')
        if report['project_id']!=pid or report['artifact_type']!='CLAIM_COVERAGE_REPORT' or not self.store.is_usable_input(report_id):raise ValueError('INVALID_COVERAGE_REPORT')
        ids={x['candidate_id'] for x in report['payload']['candidates']}
        if {x.get('candidate_id') for x in decisions}!=ids or len(decisions)!=len(ids):raise ValueError('ALL_CANDIDATES_REQUIRE_DECISION')
        if any(x.get('decision') not in ('NON_CLAIM','REGISTER_CLAIM') or not x.get('reason','').strip() for x in decisions):raise ValueError('INVALID_COVERAGE_DECISION')
        return self.store.create_artifact(pid,'CLAIM_COVERAGE_DECISION',{'report_id':report_id,'decisions':decisions,'reviewer':reviewer},role=actor,
            dependencies=[self.store.dependency(report_id)]).model_dump()

    def require_script(self,pid,script_id):
        script=self.store.get_artifact(script_id)
        if not strict(self.store,pid) and script['payload'].get('contract_version',1)<2:return []
        if script['payload'].get('contract_version',1)!=2:raise ValueError('CLAIM_LEVEL_SCRIPT_REQUIRED')
        report=self.store.latest(pid,'CLAIM_COVERAGE_REPORT')
        if not report or report['payload']['script_artifact_id']!=script_id or not self.store.is_usable_input(report['artifact_id']):raise ValueError('CURRENT_CLAIM_COVERAGE_REQUIRED')
        if report['payload']['issues']:raise ValueError('CLAIM_INTEGRITY_FAILED')
        deps=[report['artifact_id']]
        if report['payload']['candidates']:
            decision=self.store.latest(pid,'CLAIM_COVERAGE_DECISION')
            if not decision or not self.store.is_usable_input(decision['artifact_id']) or decision['payload']['report_id']!=report['artifact_id']:raise ValueError('UNREGISTERED_CLAIM_REVIEW_REQUIRED')
            if any(x['decision']!='NON_CLAIM' for x in decision['payload']['decisions']):raise ValueError('REGISTER_CLAIM_REQUIRED')
            deps.append(decision['artifact_id'])
        return deps

PATTERNS=[('NUMERIC',r'\d+(?:\.\d+)?(?:\s*%)?|[零一二三四五六七八九十百千万亿]+(?:个|项|人|元|倍|%|百分之)'),
 ('DATE',r'\d{4}[-/年]\d{1,2}(?:[-/月]\d{1,2}日?)?|今天|昨日|本周|本月|今年|最新|目前|截至'),
 ('ATTRIBUTION',r'官方(?:表示|称|宣布)|数据显示|研究发现|据.{1,12}(?:报道|称)|according to|study (?:found|shows)|data shows'),
 ('RANK',r'第[一二三四五六七八九十\d]+|排名|领先|最高|最大|最多|top\s*\d+'),
 ('ENTITY',r'[A-Z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,12}(?:公司|集团|大学|研究所|协会|委员会)|(?:先生|女士)|[《「][^》」]{1,30}[》」]')]
def detect_claims(segments,claims,entities=()):
    candidates=[];issues=[]
    for segment in segments:
        text=segment['text'];cover=[c for c in claims if c['segment_id']==segment['segment_id']]
        matches=[]
        for kind,pattern in PATTERNS:
            matches.extend((kind,m.start(),m.end()) for m in re.finditer(pattern,text,re.I if kind=='ATTRIBUTION' else 0))
        for entity in entities:
            matches.extend(('ENTITY',m.start(),m.end()) for m in re.finditer(re.escape(entity),text))
        # Explicit person / product context plus declared source entities supplement heuristics.
        for m in re.finditer(r'(?:创始人|CEO|董事长|教授|产品|平台|手机|软件|模型|应用)([\u4e00-\u9fffA-Za-z0-9_-]{2,12})',text):matches.append(('ENTITY',m.start(),m.end()))
        for m in re.finditer(r'[\u4e00-\u9fff]{2,4}(?:表示|宣布|指出|称)',text):matches.append(('ENTITY',m.start(),m.end()))
        for kind,start,end in sorted(set(matches)):
            if any(c['text_span']['start']<=start and c['text_span']['end']>=end for c in cover):continue
            cid='CC-'+digest([segment['segment_id'],kind,start,end,text[start:end]])[:16]
            candidates.append({'candidate_id':cid,'code':'UNREGISTERED_CLAIM_CANDIDATE','segment_id':segment['segment_id'],'text_span':{'start':start,'end':end},'text':text[start:end],'kind':kind,'owner':'AUDIT','status':'PENDING'})
    # Marked non-claims are declarations, not a way to hide suspicious factual text.
    for c in claims:
        if c['claim_type'] in ('NON_CLAIM','OPINION') and any(re.search(pattern,c['claim_text']) for kind,pattern in PATTERNS if kind in ('NUMERIC','DATE','ATTRIBUTION','RANK')):
            candidates.append({'candidate_id':'CC-'+digest(c)[:16],'code':'UNREGISTERED_CLAIM_CANDIDATE','claim_id':c['claim_id'],'segment_id':c['segment_id'],'text_span':c['text_span'],'text':c['claim_text'],'kind':'DECLARED_NON_FACTUAL','owner':'AUDIT','status':'PENDING'})
    return {'candidates':candidates,'issues':issues,'verdict':'PASS' if not candidates else 'PASS_WITH_RISK'}
