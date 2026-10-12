"""Formal research gateway operations; local adapters, remote operations blocked."""
import uuid
from pathlib import Path
from vnext.contracts import ToolRequest,utc_now
from vnext.gateways.tool.gateway import ToolGateway
from vnext.phase2.knowledge import Knowledge
from vnext.phase2.hardening.evidence import content_hash
OPERATIONS=['SEARCH','FETCH_PAGE','SNAPSHOT','SCREENSHOT','DOCUMENT_READ','IMAGE_SEARCH']
class ResearchTools:
    def __init__(self,store):self.store=store
    def invoke(self,pid,payload,actor):
        if actor!='RESEARCH':raise PermissionError('RESEARCH_TOOL_OWNER_REQUIRED')
        request=ToolRequest.model_validate(payload)
        result=ToolGateway([self.store.root/'projects'/pid]).invoke(request)
        if result.status!='COMPLETED':return result.model_dump()
        output=result.output
        # Only actual source bytes/text emitted by the adapter, never an LLM summary.
        text=output.get('text','')
        if not text:raise ValueError('SOURCE_TEXT_REQUIRED')
        sid='SRC-'+uuid.uuid4().hex[:12]
        source=Knowledge(self.store).source(pid,{'source_id':sid,'source_type':'USER_DOCUMENT',
            'title':Path(request.arguments.get('path','Tool snapshot')).name,'retrieved_at':utc_now(),
            'content':text,'excerpt':text[:2000],'pages':output.get('pages',{}),'snapshot':result.provenance.get('snapshot',''),
            'trust':'UNTRUSTED_SOURCE_DATA'},'RESEARCH')
        return {**result.model_dump(),'source_artifact_id':source['artifact_id'],'source_id':sid,
            'source_content_hash':content_hash(source['payload']),'fact_created':False,'evidence_required':True}
