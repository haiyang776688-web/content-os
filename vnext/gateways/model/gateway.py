"""Canonical model gateway. Provider credentials never leave this module."""
from __future__ import annotations

from contextvars import ContextVar
TRANSPORT_TIMEOUT=ContextVar("provider_timeout",default=60)
EXECUTION_HOOKS=ContextVar("model_execution_hooks",default=(None,None))

import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from jsonschema import ValidationError, validate

from vnext.contracts import ModelRequest, ModelResult, ProviderProtocol
from vnext.registries.catalog import WORKERS
from vnext.secrets.store import SecretStore


class GatewayError(RuntimeError):
    pass


class ModelGateway:
    def __init__(self, secrets: SecretStore | None = None, cache_dir: Path | None = None):
        self.secrets = secrets or SecretStore()
        self.cache_dir = Path(cache_dir) if cache_dir else None

    def invoke(self, request: ModelRequest, *, store=None, project_id=None, _attempt=None, _synthetic=None) -> ModelResult:
        if store is not None:
            from vnext.phase2.hardening.model_runs import ModelRuns
            return ModelRuns(store,self).invoke(project_id,request)
        if _attempt is None and _synthetic is None:_attempt,_synthetic=EXECUTION_HOOKS.get()
        cache_path = None
        if self.cache_dir:
            profile = WORKERS[request.worker_profile]
            selected_model = self.secrets.get(profile.model_env or "") or profile.model
            key = hashlib.sha256(json.dumps({"request": request.model_dump(mode="json"),
                "provider_id": profile.worker_id, "adapter_version":"OPENAI_CHAT_V2", "endpoint":self.secrets.get(profile.endpoint_env or ""), "model": selected_model}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            cache_path = self.cache_dir / (key + ".json")
            if cache_path.exists():
                cached = ModelResult.model_validate_json(cache_path.read_text())
                if _synthetic:_synthetic(cached,True)
                return cached.model_copy(update={"warnings": [*cached.warnings, "CACHE_HIT"],
                    "provider_metadata": {**cached.provider_metadata, "cache_hit": True}})
        result = self._invoke_uncached(request,_attempt)
        if _synthetic and WORKERS[request.worker_profile].protocol==ProviderProtocol.MOCK:_synthetic(result,False)
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(result.model_copy(update={"raw_response": None}).model_dump_json())
        return result

    def _invoke_uncached(self, request: ModelRequest, attempt_hook=None) -> ModelResult:
        profile = WORKERS[request.worker_profile]
        if profile.protocol == ProviderProtocol.MOCK:
            return self._mock(request)
        if profile.protocol not in (ProviderProtocol.CUSTOM_OPENAI_COMPATIBLE, ProviderProtocol.OPENAI_CHAT):
            raise GatewayError(f"PROTOCOL_NOT_IMPLEMENTED:{profile.protocol.value}")
        base = self.secrets.get(profile.endpoint_env or "")
        key = self.secrets.get(profile.api_key_env or "")
        model = self.secrets.get(profile.model_env or "")
        from vnext.providers.settings import Settings,ROOT,url
        setting=Settings().get(profile.worker_id) if ROOT is not None and isinstance(self.secrets,SecretStore) and profile.worker_id in Settings().configs() else None
        if not base or not model or (not key and not (setting and setting['authentication']=='NONE')):
            raise GatewayError("PROVIDER_NOT_CONFIGURED")
        if request.tools:
            raise GatewayError("CONTENT_BLOCK_OR_TOOL_MAPPING_NOT_IMPLEMENTED")
        messages = [{"role": "system", "content": request.system_prompt}] + [m.model_dump(exclude_none=True) for m in request.messages]
        if request.content_blocks:
            if profile.worker_id!='MINIMAX' or model!='MiniMax-M3':
                raise GatewayError('MODEL_VIDEO_INPUT_UNSUPPORTED')
            if request.config.get('cloud_policy') not in ('CLOUD_ALLOWED','ASK_BEFORE_UPLOAD'):
                raise GatewayError('LOCAL_ONLY_UPLOAD_FORBIDDEN')
            if request.config.get('cloud_policy')=='ASK_BEFORE_UPLOAD' and not request.config.get('upload_confirmed'):
                raise GatewayError('UPLOAD_CONFIRMATION_REQUIRED')
            mapped=[]
            for block in request.content_blocks:
                if block.type not in ('VIDEO','IMAGE') or not block.uri or not block.uri.startswith(('data:','https://','mm_file://')):
                    raise GatewayError('CONTENT_BLOCK_UNSUPPORTED')
                kind='video_url' if block.type=='VIDEO' else 'image_url'
                value={'url':block.uri,'detail':'default'}
                if block.type=='VIDEO':value['fps']=1
                mapped.append({'type':kind,kind:value})
            messages.append({'role':'user','content':[{'type':'text','text':'Inspect the supplied video using the attached criteria.'},*mapped]})
        body = {"model": model, "messages": messages, "temperature": request.config.get("temperature", 0.2), "max_tokens": request.config.get("max_output_tokens",4096)}
        if profile.worker_id=='MINIMAX' and model=='MiniMax-M3':
            body.update(reasoning_split=True,thinking={'type':'disabled'})
        endpoint = url(base,"chat/completions") if setting else base.rstrip("/")+"/chat/completions"
        if setting and setting["provider_id"] in ("GLM","DEEPSEEK","DOUBAO"):
            body["thinking"]={"type":"disabled"}
        if request.response_schema:
            messages[0]["content"] += "\nReturn only a JSON object matching this schema: " + json.dumps(request.response_schema,ensure_ascii=False)
        last_error = None
        for attempt in range(2):
            try:
                timeout_token=TRANSPORT_TIMEOUT.set(setting["timeout"] if setting else 60)
                try:raw = attempt_hook(lambda:self._post(endpoint,key,body),attempt) if attempt_hook else self._post(endpoint,key,body)
                finally:TRANSPORT_TIMEOUT.reset(timeout_token)
                choice = raw["choices"][0]
                value = choice["message"]["content"] or ""
                parsed = self._parse(value, request.response_schema)
                return ModelResult(text=value, structured_output=parsed, usage=raw.get("usage", {}),
                    finish_reason=choice.get("finish_reason") or "stop",
                    provider_metadata={"provider": profile.provider, "provider_id":profile.worker_id,"provider_type":setting["provider_type"] if setting else "BUILTIN", "model_id":model,"adapter_version":"OPENAI_CHAT_V2", "model": model, "attempts": attempt + 1,"exercised_capabilities":["TEXT"]+(["STRUCTURED_OUTPUT"] if parsed is not None else [])+list(dict.fromkeys(b.type+"_INPUT" for b in request.content_blocks))},
                    raw_response=raw)
            except (ValueError, ValidationError, KeyError, IndexError) as error:
                last_error = str(error)
                messages.append({"role": "user", "content": "Your previous output did not match the required JSON schema. Return only valid JSON. Error: " + last_error[:300]})
                body["messages"] = messages
        raise GatewayError("SCHEMA_REPAIR_EXHAUSTED:" + str(last_error))

    @staticmethod
    def _post(url: str, key: str, body: dict[str, Any]) -> dict:
        request = urllib.request.Request(url, data=json.dumps(body).encode(),
            headers={**({"Authorization": "Bearer " + key} if key else {}), "Content-Type": "application/json"})
        try:
            from vnext.providers.settings import NoRedirect
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=TRANSPORT_TIMEOUT.get()) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            from vnext.providers.settings import error_code
            raise GatewayError(error_code(error)) from None
        except urllib.error.URLError as error:
            raise GatewayError("PROVIDER_UNREACHABLE") from error

    @staticmethod
    def _parse(value: str, schema: dict | None) -> dict | None:
        if schema is None:
            return None
        cleaned = value.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        parsed = json.loads(cleaned)
        validate(parsed, schema)
        return parsed

    def _mock(self, request: ModelRequest) -> ModelResult:
        source = "\n".join(str(m.content) for m in request.messages)
        if request.config.get('script_segments') and request.role.value=='DIRECTOR':
            segments=request.config['script_segments']
            data={'script_artifact_id':request.config['script_artifact_id'],'scenes':[],'beats':[]}
            for i,segment in enumerate(segments):
                sid,bid=f'SC{i+1}',f'B{i+1}'
                data['scenes'].append({'scene_id':sid,'purpose':'Explain evidence','script_range':[segment['segment_id']],
                    'narrative_function':'EXPLAIN','retention_goal':'INFORMATION_CHANGE','estimated_duration':10,'beat_ids':[bid]})
                data['beats'].append({'beat_id':bid,'scene_id':sid,'script_segment_id':segment['segment_id'],
                    'purpose':'Explain evidence','visual_focus':segment['text'],'visual_form':'KEYWORD',
                    'pattern_id':'CHARACTER_EXPLAIN_KEYWORD','keyword':segment['text'][:12],
                    'timing_intent':10,'slots':{'keyword':segment['text'][:12]}})
        elif request.role.value in ('SCRIPT_PRIMARY','SCRIPT_EDITOR') and request.response_schema and 'segments' in request.response_schema.get('properties',{}):
            segments=request.config.get('bound_segments') or [{'segment_id':f'SEG{i+1}', 'text':fact['statement'],
                'claim':True,'fact_ids':[fact['fact_id']]} for i,fact in enumerate(request.config.get('facts',[]))]
            data={'text':'\n'.join(s['text'] for s in segments),'segments':segments,'semantic_status':'AUDIT_REQUIRED','semantic_diff':{}}
        elif request.role.value == "DIRECTOR":
            script_id = request.config.get("script_artifact_id", "")
            data = {"script_artifact_id": script_id, "beats": [{"beat_id": "B1", "purpose": "Introduce the topic", "visual_focus": source[:80],
                "visual_form": "TITLE_CARD", "character_presence": "OPTIONAL", "character_intent": "EXPLAIN",
                "media_need": "none", "density": "LOW", "tempo": "MODERATE", "motion_intent": "HOLD",
                "reveal_order": ["title"], "keyword": source[:20]}]}
        elif request.role.value == "AUDIT":
            data = {"verdict": "PASS", "findings": [], "rationale": "Mock review for contract testing; not a factual audit."}
            if request.config.get('mock_audit_verdict')=='FAIL':
                data.update(verdict='FAIL',findings=[{'owner':'SCRIPT_PRIMARY','severity':'BLOCKER',
                    'description':request.config.get('mock_finding','Diagnostic script repair required')}])
            elif request.config.get('mock_audit_verdict')=='PASS_WITH_RISK':
                data.update(verdict='PASS_WITH_RISK',risk=request.config.get('mock_risk','Mock review is not a factual verification'))
        else:
            data = {"text": source[:2000]}
        if request.config.get('claim_integrity')==2 and request.role.value in ('SCRIPT_PRIMARY','SCRIPT_EDITOR'):
            data['contract_version']=2
            data['claim_units']=request.config.get('bound_claim_units') or [{'claim_id':f'C{i+1}','segment_id':s['segment_id'],'text_span':{'start':0,'end':len(s['text'])},'claim_text':s['text'],'claim_type':'FACTUAL','fact_ids':s['fact_ids'],'support_status':'SUPPORTED','review_status':'PENDING'} for i,s in enumerate(data['segments'])]
        if request.config.get('claim_units') and request.role.value=='AUDIT':
            data['claim_reviews']=[{'claim_id':c['claim_id'],'decision':'SUPPORTED' if c['claim_type'] in ('FACTUAL','NUMERIC','ATTRIBUTION') else 'NON_FACTUAL','reason':'Mock contract response, not semantic verification'} for c in request.config['claim_units']]
        if request.response_schema:
            validate(data, request.response_schema)
        return ModelResult(text=json.dumps(data, ensure_ascii=False), structured_output=data,
            provider_metadata={"provider": "mock", "model": WORKERS[request.worker_profile].model, "attempts": 1},
            warnings=["MOCK_OUTPUT_NOT_REAL_REVIEW"])
