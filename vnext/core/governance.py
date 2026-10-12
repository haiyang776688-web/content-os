"""Evolution/08 is the sole formal error and rule ledger writer."""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from pathlib import Path

from vnext.contracts import ErrorCandidate, RuleRecord, utc_now
from vnext.storage.store import Store, canonical


class Governance:
    def __init__(self, store: Store):
        self.store = store

    def submit_candidate(self, project_id: str, value: ErrorCandidate) -> dict:
        if value.artifact_id:
            artifact = self.store.get_artifact(value.artifact_id)
            if artifact["project_id"] != project_id:
                raise ValueError("CROSS_PROJECT_ARTIFACT")
        item = self.store.create_artifact(project_id, "ERROR_CANDIDATE", value.model_dump(mode="json"),
            role=value.submitted_by_role,
            dependencies=[self.store.dependency(value.artifact_id)] if value.artifact_id else [])
        return item.model_dump(mode="json")

    def _audit_path(self, project_id: str, name: str) -> Path:
        path = self.store.root / "projects" / project_id / "audit" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _append(self, path: Path, entry: dict) -> None:
        with self.store.lock, path.open("ab") as stream:
            stream.write(canonical(entry) + b"\n")

    def events(self, project_id: str, name: str) -> list[dict]:
        path = self._audit_path(project_id, name)
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def confirm_error(self, project_id: str, candidate_artifact_id: str, actor_role: str = "EVOLUTION") -> dict:
        if actor_role != "EVOLUTION":
            raise PermissionError("EVOLUTION_ONLY")
        candidate = self.store.get_artifact(candidate_artifact_id)
        if candidate["project_id"] != project_id or candidate["artifact_type"] != "ERROR_CANDIDATE":
            raise ValueError("INVALID_ERROR_CANDIDATE")
        prior_events = self.events(project_id, "error_events.jsonl")
        already = next((event for event in prior_events if event["candidate_artifact_id"] == candidate_artifact_id), None)
        if already:
            return already
        summary = candidate["payload"]["summary"]
        fingerprint = hashlib.sha256(re.sub(r"\s+", " ", summary.strip().lower()).encode()).hexdigest()
        old = next((event for event in prior_events
                    if event["kind"] == "ERROR_CONFIRMED" and event["fingerprint"] == fingerprint), None)
        event = {"event_id": "EE-" + uuid.uuid4().hex[:12], "at": utc_now(),
                 "kind": "ERROR_RECURRED" if old else "ERROR_CONFIRMED",
                 "error_id": old["error_id"] if old else "ERR-" + uuid.uuid4().hex[:10],
                 "candidate_artifact_id": candidate_artifact_id, "fingerprint": fingerprint,
                 "summary": summary, "root_cause": candidate["payload"]["root_cause"]}
        self._append(self._audit_path(project_id, "error_events.jsonl"), event)
        return event

    def save_rule(self, project_id: str, record: RuleRecord, actor_role: str = "EVOLUTION") -> dict:
        if actor_role != "EVOLUTION":
            raise PermissionError("EVOLUTION_ONLY")
        existing = [x for x in self.store.artifacts(project_id, "RULE") if x["payload"].get("rule_id") == record.rule_id]
        previous = existing[-1]["payload"]["lifecycle"] if existing else None
        allowed = {None: {"CREATED"}, "CREATED": {"ACTIVE"}, "ACTIVE": {"AMENDED", "DEPRECATED"},
                   "AMENDED": {"AMENDED", "DEPRECATED"}, "DEPRECATED": set()}
        if record.lifecycle not in allowed[previous]:
            raise ValueError("INVALID_RULE_LIFECYCLE")
        artifact = self.store.create_artifact(project_id, "RULE", record.model_dump(mode="json"), role="EVOLUTION")
        event = {"event_id": "RE-" + uuid.uuid4().hex[:12], "at": utc_now(),
                 "kind": "RULE_" + record.lifecycle, "rule_id": record.rule_id,
                 "artifact_id": artifact.artifact_id, "revision": artifact.revision}
        self._append(self._audit_path(project_id, "rule_events.jsonl"), event)
        self._refresh_rule_catalog(project_id)
        self._write_current_rules(project_id)
        return artifact.model_dump(mode="json")

    def _write_current_rules(self, project_id: str) -> None:
        latest = {}
        for artifact in self.store.artifacts(project_id, "RULE"):
            latest[artifact["payload"]["rule_id"]] = artifact["payload"]
        lines = ["# CURRENT_RULES", ""]
        for rule_id, rule in sorted(latest.items()):
            if rule["lifecycle"] in ("ACTIVE", "AMENDED"):
                lines += [f"## {rule_id} · {rule['priority']}", "", rule["text"], "",
                          f"Scope: {rule['scope']}  ", f"Owner: {rule['owner']}  ",
                          f"Reason: {rule['reason']}  ", f"Related error: {rule.get('related_error') or '—'}", ""]
        for kind in ('WRITING_RULE_SET','HOOK_RULE_SET','RETENTION_RULE_SET','EDITORIAL_VOICE'):
            item=self.store.latest(project_id,kind)
            if item:
                lines += [f"## {kind} · v{item['revision']}", "", "```json",
                          json.dumps(item['payload'],ensure_ascii=False,indent=2), "```", ""]
        path = self._audit_path(project_id, "CURRENT_RULES.md")
        temporary = path.with_suffix(".tmp")
        temporary.write_text("\n".join(lines), encoding="utf-8")
        temporary.replace(path)

    def save_rule_set(self, project_id: str, kind: str, payload: dict, actor_role='EVOLUTION') -> dict:
        if actor_role!='EVOLUTION': raise PermissionError('EVOLUTION_ONLY')
        if kind not in ('WRITING_RULE_SET','HOOK_RULE_SET','RETENTION_RULE_SET','EDITORIAL_VOICE'):
            raise ValueError('UNKNOWN_RULE_SET')
        with self.store.lock:
            artifact=self.store.create_artifact(project_id,kind,payload,role='EVOLUTION')
            self._append(self._audit_path(project_id,'rule_events.jsonl'),{
                'event_id':'RE-'+uuid.uuid4().hex[:12],'at':utc_now(),'kind':'RULE_SET_REVISION',
                'rule_set_type':kind,'artifact_id':artifact.artifact_id,'revision':artifact.revision,
                'output_hash':artifact.output_hash})
            self._refresh_rule_catalog(project_id)
            self._write_current_rules(project_id)
        return artifact.model_dump(mode='json')

    def _refresh_rule_catalog(self,project_id):
        latest={}
        for item in self.store.artifacts(project_id,'RULE'):
            latest[item['payload']['rule_id']]=item
        active=[item for item in latest.values() if item['payload']['lifecycle'] in ('ACTIVE','AMENDED')]
        sets=[self.store.latest(project_id,k) for k in ('WRITING_RULE_SET','HOOK_RULE_SET','RETENTION_RULE_SET','EDITORIAL_VOICE')]
        sets=[item for item in sets if item]
        value={'active_rules':[item['payload'] for item in sorted(active,key=lambda x:x['payload']['rule_id'])],
            'historical_rule_references':[{'artifact_id':item['artifact_id'],'hash':item['output_hash']} for item in active],
            'rule_sets':{item['artifact_type']:item['payload'] for item in sets}}
        from vnext.storage.store import digest
        old=self.store.latest(project_id,'RULE_CATALOG')
        if old and old['output_hash']==digest(value):return old
        # Rule IDs share a historical RULE stream. These references are historical;
        # the sole-writer compiled catalog is the current policy dependency.
        return self.store.create_artifact(project_id,'RULE_CATALOG',value,role='EVOLUTION',
            dependencies=[self.store.dependency(item['artifact_id']) for item in sets]).model_dump()

    def current_rules(self, project_id: str) -> str:
        path = self._audit_path(project_id, "CURRENT_RULES.md")
        return path.read_text() if path.exists() else "# CURRENT_RULES\n"
