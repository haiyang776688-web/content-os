"""Role runtime, human gates and idempotent jobs."""
from __future__ import annotations

import time
import json
import copy
import uuid

from vnext.contracts import ArtifactDependency, DirectorPlan, Job, ModelMessage, ModelRequest, Role, utc_now
from vnext.core.governance import Governance
from vnext.gateways.model.gateway import GatewayError, ModelGateway
from vnext.registries.catalog import PROMPTS, ROLE_CONTRACTS, WORKERS, worker_options
from vnext.storage.store import Store, digest


AUDIT_SCHEMA = {"type": "object", "additionalProperties":False,"required": ["verdict", "findings", "rationale"],
    "properties": {"verdict": {"enum": ["PASS", "FAIL", "PASS_WITH_RISK"]},
    "findings": {"type": "array","items":{"type":"object","required":["owner","severity","description"],
        "properties":{"owner":{"type":"string"},"severity":{"enum":["BLOCKER","WARNING","INFO"]},
            "description":{"type":"string","minLength":1},"fact_ids":{"type":"array","items":{"type":"string"}}}}},
    "rationale": {"type": "string"}, "risk": {"type": "string","minLength":1}},
    "allOf":[{"if": {"properties": {"verdict": {"const": "PASS_WITH_RISK"}}}, "then": {"required": ["risk"]}},
        {"if":{"properties":{"verdict":{"const":"FAIL"}}},"then":{"properties":{"findings":{"minItems":1}}}}]}
SCRIPT_SCHEMA = {"type": "object", "required": ["text"], "properties": {"text": {"type": "string"}}}


class WorkflowError(RuntimeError):
    pass


class Runtime:
    def __init__(self, store: Store, gateway: ModelGateway | None = None):
        self.store = store
        self.gateway = gateway or ModelGateway(cache_dir=store.root / "cache" / "models")

    def select_worker(self, project_id: str, role: Role, worker_id: str) -> dict:
        if worker_id not in WORKERS:
            raise WorkflowError("UNKNOWN_WORKER")
        choice = next(x for x in worker_options(role) if x["worker_id"] == worker_id)
        if choice["disabled"]:
            raise WorkflowError("WORKER_UNAVAILABLE:" + ",".join(choice["missing_capabilities"]))
        project = self.store.get_project(project_id)
        previous = project.worker_assignments.get(role.value, ROLE_CONTRACTS[role].default_worker)
        project.worker_assignments[role.value] = worker_id
        self.store.save_project(project)
        self.store.event(project_id, "WORKER_SELECTED", role=role.value, previous=previous, worker=worker_id)
        assignment = self.store.create_artifact(project_id, "ROLE_ASSIGNMENT_" + role.value,
            {"role": role.value, "previous_worker": previous, "worker": worker_id}, role="HUMAN")
        return {"previous": previous, "worker": worker_id, "assignment_artifact_id": assignment.artifact_id,
                "revision": assignment.revision}

    def run(self, project_id: str, role: Role, source_artifact_ids: list[str], *, request_id: str, config: dict | None = None) -> dict:
        config = config or {}
        project = self.store.get_project(project_id)
        contract = ROLE_CONTRACTS[role]
        worker_id = project.worker_assignments.get(role.value, contract.default_worker)
        choice = next(x for x in worker_options(role) if x["worker_id"] == worker_id)
        if choice["disabled"]:
            raise WorkflowError("WORKER_UNAVAILABLE")
        if role == Role.DIRECTOR and not project.h2_script_artifact_id:
            raise WorkflowError("H2_REQUIRED")
        if role == Role.DIRECTOR and project.h2_script_artifact_id not in source_artifact_ids:
            raise WorkflowError("DIRECTOR_REQUIRES_LOCKED_SCRIPT")
        if project.phase2_enabled and role==Role.DIRECTOR:
            from vnext.phase2.knowledge import Knowledge
            from vnext.phase2.production import human_edits_present
            current_ir = self.store.latest(project_id, 'DIRECTOR_IR')
            expected = config.get('expected_revision')
            if expected and (not current_ir or current_ir['artifact_id'] != expected):
                raise WorkflowError('EDIT_REVISION_CONFLICT')
            if current_ir and human_edits_present(self.store, project_id, 'DIRECTOR_IR'):
                if not config.get('discard_human_edits'):
                    raise WorkflowError('HUMAN_EDITS_PRESENT')
                if expected != current_ir['artifact_id']:
                    raise WorkflowError('EDIT_REVISION_CONFLICT')
            Knowledge(self.store).require_no_disagreement(project_id)
        sources = [self.store.get_artifact(x) for x in source_artifact_ids]
        if any(x['project_id'] != project_id for x in sources):
            raise WorkflowError('CROSS_PROJECT_ARTIFACT')
        from vnext.phase2.knowledge import reusable_script
        if any(not self.store.is_usable_input(x["artifact_id"]) and not
            (project.phase2_enabled and role==Role.SCRIPT_EDITOR and x['artifact_type']=='SCRIPT' and reusable_script(self.store,x['artifact_id'])) for x in sources):
            raise WorkflowError("STALE_INPUT")
        snapshot = None
        if project.phase2_enabled:
            from vnext.phase2.knowledge import Knowledge
            knowledge = Knowledge(self.store)
            if role == Role.AUDIT:
                if not any(x['artifact_type']=='SCRIPT' for x in sources):raise WorkflowError('AUDIT_SCRIPT_REQUIRED')
                # Blind audit only receives source evidence and the product, never another audit/rationale.
                if any(x['artifact_type'] not in ('SCRIPT','FACT_PACK') and not x['artifact_type'].startswith('SOURCE_') for x in sources):
                    raise WorkflowError('BLIND_REVIEW_INPUT_FORBIDDEN')
                facts = self.store.latest(project_id, 'FACT_PACK')
                if not facts: raise WorkflowError('FACT_PACK_REQUIRED')
                knowledge.require(project_id, facts['artifact_id'])
                evidence_ids=[facts['artifact_id']];queue=[facts]
                while queue:
                    current=queue.pop()
                    for d in current['dependencies']:
                        child=knowledge.require(project_id,d['artifact_id'])
                        if child['artifact_id'] not in evidence_ids:
                            evidence_ids.append(child['artifact_id']);queue.append(child)
                for aid in evidence_ids:
                    item = knowledge.require(project_id, aid)
                    if aid not in [x['artifact_id'] for x in sources]: sources.append(item)
            snapshot = knowledge.snapshot(project_id,role.value,config.get('skill_layers'))
        from vnext.phase2.hardening.dependencies import Dependencies
        execution_config=Dependencies(self.store).pin_config(project_id,role.value)
        key = digest({"role": role.value, "worker": worker_id, "sources": [(x["artifact_id"], x["output_hash"]) for x in sources], "skills": snapshot['output_hash'] if snapshot else None, "execution_config":execution_config['output_hash'], "config": config, "request_id": request_id})
        previous = self.store.job_by_key(project_id, key)
        if previous and previous.state == "COMPLETED" and previous.artifact_id and self.store.is_usable_input(previous.artifact_id):
            return self.store.get_artifact(previous.artifact_id)
        job = Job(job_id=previous.job_id if previous else "JOB-" + uuid.uuid4().hex[:12], request_id=request_id, project_id=project_id,
            kind=role.value, state="RUNNING", idempotency_key=key, started_at=utc_now(),
            retries=(previous.retries + 1) if previous else 0)
        self.store.save_job(job)
        start = time.monotonic()
        before=self.store.latest(project_id,'DIRECTOR_IR' if role==Role.DIRECTOR else 'SCRIPT')
        try:
            def blind_payload(item):
                if role==Role.AUDIT and item['artifact_type']=='SCRIPT':
                    return {k:v for k,v in item['payload'].items() if k in ('text','segments','contract_version','claim_units')}
                return item['payload']
            content = 'UNTRUSTED_SOURCE_DATA\n' + json.dumps([{'artifact_id':x['artifact_id'],'artifact_type':x['artifact_type'],'payload':blind_payload(x)} for x in sources],ensure_ascii=False)
            schema = DirectorPlan.model_json_schema() if role == Role.DIRECTOR else AUDIT_SCHEMA if role == Role.AUDIT else SCRIPT_SCHEMA
            extra_config = {}
            if project.phase2_enabled:
                from vnext.phase2.contracts import BoundScript, DirectorIR
                if role in (Role.SCRIPT_PRIMARY, Role.SCRIPT_EDITOR):
                    schema = BoundScript.model_json_schema()
                    fact_pack = self.store.latest(project_id, 'FACT_PACK')
                    if not fact_pack: raise WorkflowError('FACT_PACK_REQUIRED')
                    knowledge.require(project_id, fact_pack['artifact_id'])
                    extra_config['facts'] = fact_pack['payload']['facts']
                    from vnext.phase2.hardening.evidence import strict
                    if strict(self.store,project_id):
                        schema=copy.deepcopy(schema);schema['properties']['contract_version']={'const':2};schema['required']+=['contract_version','claim_units'];schema['properties']['claim_units']['minItems']=1;extra_config['claim_integrity']=2
                    if role == Role.SCRIPT_EDITOR:
                        source_script = next((x for x in sources if x['artifact_type']=='SCRIPT'), None)
                        if not source_script: raise WorkflowError('SCRIPT_EDITOR_SOURCE_REQUIRED')
                        extra_config['bound_segments'] = source_script['payload']['segments']
                        extra_config['bound_claim_units']=source_script['payload'].get('claim_units',[])
                if role == Role.DIRECTOR:
                    schema = DirectorIR.model_json_schema()
                    schema['properties']['script_artifact_id']={'const':project.h2_script_artifact_id}
                    extra_config['script_segments'] = self.store.get_artifact(project.h2_script_artifact_id)['payload']['segments']
            if role==Role.SCRIPT_PRIMARY and config.get('min_script_characters'):
                minimum=int(config['min_script_characters'])
                if not 1<=minimum<=10000:raise WorkflowError('SCRIPT_LENGTH_SETTING_INVALID')
                schema=copy.deepcopy(schema);schema['properties']['text']['minLength']=minimum
            domain_instructions=''
            if role in (Role.SCRIPT_PRIMARY,Role.SCRIPT_EDITOR):
                domain_instructions='\nSCRIPT CONTRACT: text equals segments joined by newline. Each claim_text is an exact contiguous substring of its own segment text, with segment-local character offsets. Preserve source Fact IDs. Do not summarize the claim separately. An editor must preserve segment and claim IDs, fact bindings, contract_version, meaning and approximate length; only polish wording. All claims require matching source evidence. Return the complete producer-owned JSON.'
            if role==Role.DIRECTOR and project.phase2_enabled:
                from vnext.providers.director_contract import request_contract
                schema,domain_instructions=request_contract(self.store,project_id)
            strict_claims=role==Role.AUDIT and any(x['artifact_type']=='SCRIPT' and x['payload'].get('contract_version')==2 for x in sources)
            if strict_claims:
                schema=copy.deepcopy(schema)
                schema['properties']['claim_reviews']={'type':'array','items':{'type':'object','required':['claim_id','decision','reason'],
                    'properties':{'claim_id':{'type':'string'},'decision':{'enum':['SUPPORTED','UNSUPPORTED','NON_FACTUAL']},'reason':{'type':'string','minLength':1}}}}
                schema['required'].append('claim_reviews')
                target=next(x for x in sources if x['artifact_type']=='SCRIPT')
                extra_config['claim_units']=target['payload']['claim_units']
            sources.append(execution_config)
            active_rules = Governance(self.store).current_rules(project_id)
            request = ModelRequest(role=role, worker_profile=worker_id,
                system_prompt=PROMPTS[contract.prompt_id] + domain_instructions + ("\nUSER EDITORIAL BRIEF: "+str(config["editorial_brief"]) if config.get("editorial_brief") else "") + "\n\n" + active_rules + ('\n'+str(snapshot['payload']) if snapshot else ''),
                messages=[ModelMessage(role="user", content=content)],
                response_schema=schema, config={**config, **extra_config, "script_artifact_id": project.h2_script_artifact_id},
                prompt_version=contract.prompt_id)
            from vnext.phase2.hardening.model_runs import governed
            result = governed(self.gateway,self.store,project_id,request)
            provenance={k:result.provider_metadata.get(k) for k in ('provider_id','provider_type','model_id','adapter_version','run_id')}
            provenance.update(prompt_version=contract.prompt_id,skill_snapshot=snapshot['artifact_id'] if snapshot else None,timestamp=utc_now())
            payload = result.structured_output or {"text": result.text}
            if role in (Role.SCRIPT_PRIMARY,Role.SCRIPT_EDITOR) and WORKERS[worker_id].protocol.value!="MOCK":
                from vnext.providers.script_contract import prepare
                payload,repairs=prepare(payload)
                if repairs:provenance["deterministic_derived_fields"]=repairs
            if strict_claims:
                expected={c['claim_id'] for c in extra_config['claim_units']};reviews=payload.get('claim_reviews',[])
                if len(reviews)!=len(expected) or {c['claim_id'] for c in reviews}!=expected:raise WorkflowError('CLAIM_REVIEW_INCOMPLETE')
                claim_types={c['claim_id']:c['claim_type'] for c in extra_config['claim_units']}
                if any(c['decision']=='NON_FACTUAL' and claim_types[c['claim_id']] in ('FACTUAL','NUMERIC','ATTRIBUTION') for c in reviews):raise WorkflowError('CLAIM_REVIEW_TYPE_CONFLICT')
                if any(c['decision']=='UNSUPPORTED' for c in reviews) and payload['verdict']!='FAIL':raise WorkflowError('CLAIM_REVIEW_VERDICT_CONFLICT')
            if role == Role.DIRECTOR and not project.phase2_enabled:
                if any(k in str(payload) for k in ('"fontSize"', '"pixel_x"', '"pixel_y"')):
                    raise WorkflowError("DIRECTOR_PIXEL_LAYOUT_FORBIDDEN")
                DirectorPlan.model_validate(payload)
            if project.phase2_enabled and role in (Role.SCRIPT_PRIMARY,Role.SCRIPT_EDITOR,Role.DIRECTOR):
                from vnext.contracts import Artifact
                metadata={'worker':result.provider_metadata.get('selected_worker',worker_id),'provider':result.provider_metadata.get('provider',WORKERS[worker_id].provider),
                    'model':result.provider_metadata.get('model'),'prompt_version':contract.prompt_id,'provenance':provenance}
                if role==Role.DIRECTOR:
                    from vnext.phase2.production import Production
                    latest_ir = self.store.latest(project_id, 'DIRECTOR_IR')
                    if (latest_ir or {}).get('artifact_id') != (before or {}).get('artifact_id'):
                        raise WorkflowError('EDIT_REVISION_CONFLICT')
                    owned = Production(self.store).ir(project_id, payload, extra_dependencies=[self.store.dependency(snapshot['artifact_id']),self.store.dependency(execution_config['artifact_id'])], run_metadata=metadata)
                elif role==Role.SCRIPT_EDITOR:
                    owned = knowledge.humanize(project_id, source_script['artifact_id'], payload,
                        [self.store.dependency(snapshot['artifact_id']),self.store.dependency(execution_config['artifact_id'])], metadata)
                else:
                    owned = knowledge.bound_script(project_id, payload, role.value,
                        [self.store.dependency(snapshot['artifact_id']),self.store.dependency(execution_config['artifact_id'])], metadata)
                artifact = Artifact.model_validate(owned)
                from vnext.phase2.production import CommandBus
                CommandBus(self.store).record_generated(project_id,artifact.artifact_type,owned,role.value,
                    before['artifact_id'] if before else None)
            else:
                artifact = self.store.create_artifact(project_id, contract.owned_artifact_types[0], payload,
                    role=role.value, worker=result.provider_metadata.get("selected_worker",worker_id), provider=result.provider_metadata.get("provider",WORKERS[worker_id].provider),
                    model=result.provider_metadata.get("model"), prompt_version=contract.prompt_id,provenance=provenance,
                    dependencies=[ArtifactDependency(artifact_id=x["artifact_id"], output_hash=x["output_hash"]) for x in [*sources, *([snapshot] if snapshot else [])]])
            if project.phase2_enabled and role==Role.AUDIT:
                script_target=next((x for x in sources if x['artifact_type']=='SCRIPT'),None)
                if not script_target:raise WorkflowError('AUDIT_SCRIPT_REQUIRED')
                self.store.create_artifact(project_id,'SCRIPT_GATE',{'decision':payload['verdict'],
                    'risk':payload.get('risk'),'human_confirmation_required':payload['verdict']=='PASS_WITH_RISK',
                    'script_artifact_id':script_target['artifact_id'],'audit_artifact_id':artifact.artifact_id},role='GATE_ENGINE',
                    dependencies=[self.store.dependency(script_target['artifact_id']),self.store.dependency(artifact.artifact_id)])
                if payload['verdict']=='FAIL':
                    from vnext.contracts import ErrorCandidate
                    reason='; '.join(f['description'] for f in payload['findings'])
                    for finding in payload['findings']:
                        target=self.store.latest(project_id,'FACT_PACK') if finding['owner']=='RESEARCH' else script_target
                        self.change_request(project_id,target['artifact_id'],'AUDIT',finding['description'])
                    Governance(self.store).submit_candidate(project_id,ErrorCandidate(summary=reason,
                        root_cause='UNKNOWN',submitted_by_role='AUDIT',artifact_id=script_target['artifact_id']))
                    project=self.store.get_project(project_id);project.h2_script_artifact_id=None
                    project.state='RETURNED_TO_SCRIPT';self.store.save_project(project)
            job = job.model_copy(update={"state": "COMPLETED", "artifact_id": artifact.artifact_id, "finished_at": utc_now()})
            self.store.save_job(job)
            self.store.log(project_id, "INFO", "ROLE_RUN_COMPLETED", job=job.job_id, role=role.value,
                worker=worker_id, latency_ms=round((time.monotonic()-start)*1000),
                usage={} if result.provider_metadata.get("cache_hit") else result.usage,
                cache_hit=bool(result.provider_metadata.get("cache_hit")),
                retries=int(result.provider_metadata.get("attempts", 1))-1)
            return artifact.model_dump(mode="json")
        except Exception as error:
            job = job.model_copy(update={"state": "FAILED", "error": str(error), "finished_at": utc_now()})
            self.store.save_job(job)
            self.store.log(project_id, "ERROR", "ROLE_RUN_FAILED", job=job.job_id, error=str(error))
            raise

    def approve_h2(self, project_id: str, script_artifact_id: str, risk_acknowledged: bool = False) -> dict:
        artifact = self.store.get_artifact(script_artifact_id)
        if artifact["project_id"] != project_id or artifact["artifact_type"] != "SCRIPT" or not self.store.is_usable_input(script_artifact_id):
            raise WorkflowError("INVALID_H2_SCRIPT")
        latest_audit = self.store.latest(project_id, "AUDIT")
        project = self.store.get_project(project_id)
        if project.phase2_enabled:
            from vnext.phase2.knowledge import Knowledge
            Knowledge(self.store).require_no_disagreement(project_id)
            from vnext.phase2.hardening.evidence import EvidenceIntegrity
            coverage_dependencies=EvidenceIntegrity(self.store).require_script(project_id,script_artifact_id)
            if coverage_dependencies:
                expected={c['claim_id'] for c in artifact['payload']['claim_units']}
                reviews=latest_audit['payload'].get('claim_reviews',[]) if latest_audit else []
                if {c['claim_id'] for c in reviews}!=expected or any(c['decision']=='UNSUPPORTED' for c in reviews):raise WorkflowError('CLAIM_REVIEW_REQUIRED')
                types={c['claim_id']:c['claim_type'] for c in artifact['payload']['claim_units']}
                if any(c['decision']=='NON_FACTUAL' and types[c['claim_id']] in ('FACTUAL','NUMERIC','ATTRIBUTION') for c in reviews):raise WorkflowError('CLAIM_REVIEW_TYPE_CONFLICT')
            if artifact['current_status'] in ('BLOCKED','FAILED') or 'segments' not in artifact['payload']:
                raise WorkflowError('BOUND_SCRIPT_REQUIRED')
            if not latest_audit or not self.store.is_usable_input(latest_audit['artifact_id']) or not any(
                d['artifact_id']==script_artifact_id for d in latest_audit['dependencies']):
                raise WorkflowError('CURRENT_INDEPENDENT_AUDIT_REQUIRED')
            if str(latest_audit.get('provider','')).lower() == 'mock' and not risk_acknowledged:
                raise WorkflowError('MOCK_AUDIT_RISK_ACKNOWLEDGMENT_REQUIRED')
        if latest_audit and any(x["artifact_id"] == script_artifact_id for x in latest_audit["dependencies"]):
            if latest_audit["payload"].get("verdict") == "FAIL":
                raise WorkflowError("AUDIT_FAIL")
            if latest_audit["payload"].get("verdict") == "PASS_WITH_RISK" and not risk_acknowledged:
                raise WorkflowError("RISK_ACKNOWLEDGMENT_REQUIRED")
        project = self.store.get_project(project_id)
        project.h2_script_artifact_id = script_artifact_id
        project.state = "SCRIPT_LOCKED"
        self.store.save_project(project)
        self.store.event(project_id, "H2_SCRIPT_APPROVED", artifact_id=script_artifact_id,
                         risk_acknowledged=risk_acknowledged)
        if project.phase2_enabled:
            gate=self.store.create_artifact(project_id,'H2_GATE',{'script_artifact_id':script_artifact_id,
                'risk_acknowledged':risk_acknowledged,'decision':'APPROVE','at':utc_now()},role='HUMAN',
                dependencies=[self.store.dependency(script_artifact_id),self.store.dependency(latest_audit['artifact_id']),
                    *[self.store.dependency(aid) for aid in coverage_dependencies]])
            return {'status':'SCRIPT_LOCKED','script_artifact_id':script_artifact_id,'artifact_id':gate.artifact_id}
        return {"status": "SCRIPT_LOCKED", "script_artifact_id": script_artifact_id}

    def change_request(self, project_id: str, target_artifact_id: str, from_role: str, reason: str) -> dict:
        target = self.store.get_artifact(target_artifact_id)
        if target["project_id"] != project_id:
            raise WorkflowError("CROSS_PROJECT_ARTIFACT")
        artifact = self.store.create_artifact(project_id, "CHANGE_REQUEST",
            {"target_artifact_id": target_artifact_id, "owner": target["created_by_role"], "reason": reason},
            role=from_role, dependencies=[self.store.dependency(target_artifact_id)])
        return artifact.model_dump(mode="json")
