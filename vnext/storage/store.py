"""SQLite projections plus immutable filesystem artifacts and append-only events."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from vnext.contracts import Artifact, ArtifactDependency, Job, ProjectConfig, utc_now


SINGLE_WRITERS = {
    'STORYBOARD_MOTION': {'STORYBOARD'},
    'RESOLVED_VISUAL_COMPOSITION': {'VISUAL_RESOLVER'},
    'MODEL_EXECUTION_CONFIG': {'HUMAN'},
    'VOICE_AUTHORIZATION': {'HUMAN'},
    'AUDIO_TIMING_MAP': {'VOICE','ALIGNMENT'},
    'ALIGNED_TIMING_MAP': {'ALIGNMENT'},
    'BEAT_TIMING_BINDINGS': {'HUMAN','DIRECTOR'},
    'PROJECT_DEPENDENCY_MANIFEST': {'DEPENDENCY_RESOLVER'},
    'CLAIM_COVERAGE_REPORT': {'CLAIM_VALIDATOR'},
    'CLAIM_COVERAGE_DECISION': {'AUDIT','HUMAN'},
    'ARCHITECTURE_POLICY': {'HUMAN'},
    'WRITING_RULE_SET': {'EVOLUTION'}, 'HOOK_RULE_SET': {'EVOLUTION'},
    'RETENTION_RULE_SET': {'EVOLUTION'}, 'EDITORIAL_VOICE': {'EVOLUTION'},
    'FACT_PACK': {'RESEARCH'}, 'DIRECTOR_IR': {'DIRECTOR'},
    'TYPOGRAPHY_PROFILE': {'TYPOGRAPHY'}, 'PROJECT_FONT_SNAPSHOT': {'FONT_REGISTRY'},
    'STORYBOARD': {'STORYBOARD'}, 'STORYBOARD_GATE': {'HUMAN'},
    'MECHANICAL_QA': {'MECHANICAL_QA'}, 'REVIEW_PACK': {'REVIEW'}, 'REVIEW_GATE': {'HUMAN'},
    'EDIT_COMMAND': {'COMMAND_BUS'}, 'VISUAL_EDT': {'TIMELINE'}, 'H2_GATE': {'HUMAN'},
    'DISAGREEMENT': {'AUDIT','VIDEO_QA'},
    'DISAGREEMENT_RESOLUTION': {'RESEARCH','DIRECTOR','TIMELINE','TYPOGRAPHY','VOICE','MEDIA_RESOLVER'},
    'SCRIPT_GATE': {'GATE_ENGINE'},
    'VISUAL_CONFIG': {'HUMAN'},
    'RULE_CATALOG': {'EVOLUTION'},
    "RESEARCH": {"RESEARCH"},
    "SCRIPT": {"HUMAN", "SCRIPT_PRIMARY", "SCRIPT_EDITOR"},
    "SCRIPT_REFERENCE": {"HUMAN"},
    "AUDIT": {"AUDIT"},
    "DIRECTOR_PLAN": {"DIRECTOR"},
    "MEDIA_SELECTION": {"MEDIA_RESOLVER", "HUMAN"},
    "VOICE": {"VOICE"},
    "SUBTITLE": {"SUBTITLE", "HUMAN"},
    "EDT": {"TIMELINE"},
    "RENDER": {"RENDER"},
    "EXPORT": {"EXPORT"},
    "VIDEO_QA": {"VIDEO_QA"},
    "QA": {"VIDEO_QA"},
    "RULE": {"EVOLUTION"},
    "OBSERVATION": {"ANALYTICS"},
}


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":")).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


class Store:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.database = self.root / "content_os_vnext.sqlite3"
        self.lock = threading.RLock()
        with self.connection() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS artifacts(id TEXT PRIMARY KEY, project_id TEXT NOT NULL,
                artifact_type TEXT NOT NULL, revision INTEGER NOT NULL, data TEXT NOT NULL,
                UNIQUE(project_id, artifact_type, revision));
            CREATE TABLE IF NOT EXISTS artifact_state(id TEXT PRIMARY KEY, state TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, project_id TEXT NOT NULL,
                idempotency_key TEXT NOT NULL, data TEXT NOT NULL,
                UNIQUE(project_id, idempotency_key));
            CREATE TABLE IF NOT EXISTS media(id TEXT PRIMARY KEY, project_id TEXT NOT NULL, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS logs(id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL, at TEXT NOT NULL, level TEXT NOT NULL, message TEXT NOT NULL,
                metadata TEXT NOT NULL);
            """)

    @contextmanager
    def connection(self):
        with self.lock:
            db = sqlite3.connect(self.database)
            db.row_factory = sqlite3.Row
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

    def event(self, project_id: str, kind: str, **data) -> dict:
        from vnext.secrets.secure import redact
        data=redact(data)
        item = {"event_id": uuid.uuid4().hex, "at": utc_now(), "kind": kind, **data}
        path = self.root / "projects" / project_id / "events.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock, path.open("ab") as output:
            output.write(canonical(item) + b"\n")
        return item

    def create_project(self, name: str, **values) -> ProjectConfig:
        project = ProjectConfig(project_id="PRJ-" + uuid.uuid4().hex[:12], project_name=name,
                                created_at=utc_now(), **values)
        with self.connection() as db:
            db.execute("INSERT INTO projects VALUES (?,?)", (project.project_id, project.model_dump_json()))
        self.event(project.project_id, "PROJECT_CREATED", name=name)
        return project

    def get_project(self, project_id: str) -> ProjectConfig:
        with self.connection() as db:
            row = db.execute("SELECT data FROM projects WHERE id=?", (project_id,)).fetchone()
        if not row:
            raise KeyError("PROJECT_NOT_FOUND")
        return ProjectConfig.model_validate_json(row["data"])

    def projects(self) -> list[ProjectConfig]:
        with self.connection() as db:
            rows = db.execute("SELECT data FROM projects ORDER BY rowid DESC").fetchall()
        return [ProjectConfig.model_validate_json(row["data"]) for row in rows]

    def save_project(self, project: ProjectConfig) -> None:
        with self.connection() as db:
            db.execute("UPDATE projects SET data=? WHERE id=?", (project.model_dump_json(), project.project_id))
        self.event(project.project_id, "PROJECT_CONFIG_UPDATED", config_hash=digest(project.model_dump()))

    def create_artifact(self, project_id: str, artifact_type: str, payload: dict, *,
                        role: str, worker: str | None = None, provider: str | None = None,
                        model: str | None = None, prompt_version: str | None = None,
                        dependencies: list[ArtifactDependency] | None = None,
                        status: str = "READY", provenance: dict | None = None) -> Artifact:
        from vnext.secrets.secure import redact
        if redact(payload)!=payload:raise ValueError('SECRET_CONTENT_REJECTED')
        allowed = SINGLE_WRITERS.get(artifact_type)
        if artifact_type.startswith('MODEL_EXECUTION_CONFIG_'):allowed={'HUMAN'}
        if artifact_type.startswith('EVIDENCE_') or artifact_type.startswith('FACT_') and artifact_type!='FACT_PACK':
            allowed = {'RESEARCH'}
        if artifact_type.startswith('CLAIM_') and artifact_type not in ('CLAIM_COVERAGE_REPORT','CLAIM_COVERAGE_DECISION'):
            allowed = {'HUMAN','SCRIPT_PRIMARY','SCRIPT_EDITOR'}
        if artifact_type.startswith('SOURCE_'):
            allowed = {'RESEARCH'}
        if artifact_type.startswith('EFFECTIVE_SKILL_SNAPSHOT_'):
            allowed = {'SKILL_RESOLVER'}
        if artifact_type.startswith('STAGE_'):
            allowed = {'STAGE_CACHE'}
        if allowed and role not in allowed:
            raise PermissionError(f"SINGLE_WRITER_VIOLATION:{artifact_type}:{role}")
        self.get_project(project_id)
        dependencies = dependencies or []
        for dependency in dependencies:
            upstream = self.get_artifact(dependency.artifact_id)
            if upstream['project_id'] != project_id or upstream['output_hash'] != dependency.output_hash:
                raise ValueError('INVALID_ARTIFACT_DEPENDENCY')
        with self.connection() as db:
            row = db.execute("SELECT COALESCE(MAX(revision),0) AS revision FROM artifacts WHERE project_id=? AND artifact_type=?",
                             (project_id, artifact_type)).fetchone()
            revision = row["revision"] + 1
            artifact = Artifact(artifact_id="ART-" + uuid.uuid4().hex[:16], project_id=project_id,
                artifact_type=artifact_type, revision=revision, created_by_role=role,
                worker=worker, provider=provider, model=model, prompt_version=prompt_version, provenance=provenance or {},
                dependencies=dependencies, input_hash=digest([d.model_dump() for d in dependencies]),
                output_hash=digest(payload), status=status, created_at=utc_now(), payload=payload)
            path = self.root / "projects" / project_id / "artifacts" / artifact_type / f"v{revision:04d}-{artifact.artifact_id}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as output:
                output.write(canonical(artifact.model_dump(mode="json")) + b"\n")
            db.execute("INSERT INTO artifacts VALUES (?,?,?,?,?)", (
                artifact.artifact_id, project_id, artifact_type, revision, artifact.model_dump_json()))
            db.execute("INSERT INTO artifact_state VALUES (?,?)", (artifact.artifact_id, status))
        self.event(project_id, "ARTIFACT_CREATED", artifact_id=artifact.artifact_id,
                   artifact_type=artifact_type, revision=revision, output_hash=artifact.output_hash)
        self.invalidate_descendants(project_id, artifact_type, artifact.artifact_id)
        return artifact

    def artifacts(self, project_id: str, artifact_type: str | None = None) -> list[dict]:
        query = "SELECT a.data,s.state FROM artifacts a JOIN artifact_state s ON a.id=s.id WHERE a.project_id=?"
        params: list = [project_id]
        if artifact_type:
            query += " AND a.artifact_type=?"
            params.append(artifact_type)
        query += " ORDER BY a.rowid"
        with self.connection() as db:
            rows = db.execute(query, params).fetchall()
        return [{**json.loads(row["data"]), "current_status": row["state"]} for row in rows]

    def get_artifact(self, artifact_id: str) -> dict:
        with self.connection() as db:
            row = db.execute("SELECT a.data,s.state FROM artifacts a JOIN artifact_state s ON a.id=s.id WHERE a.id=?", (artifact_id,)).fetchone()
        if not row:
            raise KeyError("ARTIFACT_NOT_FOUND")
        return {**json.loads(row["data"]), "current_status": row["state"]}

    def set_artifact_state(self, artifact_id: str, state: str) -> None:
        """Persist a lifecycle state without rewriting immutable artifact data."""
        if state not in ('DRAFT','READY','STALE','DIRTY','BLOCKED','FAILED','APPROVED','LOCKED'):
            raise ValueError('INVALID_ARTIFACT_STATE')
        item = self.get_artifact(artifact_id)
        with self.connection() as db:
            db.execute('UPDATE artifact_state SET state=? WHERE id=?', (state, artifact_id))
        self.event(item['project_id'], 'ARTIFACT_STATE_CHANGED', artifact_id=artifact_id, state=state)

    def latest(self, project_id: str, artifact_type: str) -> dict | None:
        values = self.artifacts(project_id, artifact_type)
        return values[-1] if values else None

    def dependency(self, artifact_id: str) -> ArtifactDependency:
        item = self.get_artifact(artifact_id)
        return ArtifactDependency(artifact_id=artifact_id, output_hash=item["output_hash"])

    def invalidate_descendants(self, project_id: str, changed_type: str, new_id: str) -> None:
        """New upstream revision stales descendants still bound to older revisions."""
        stale_ids = set()
        with self.connection() as db:
            rows = db.execute("SELECT id,artifact_type,data FROM artifacts WHERE project_id=? ORDER BY rowid", (project_id,)).fetchall()
            for row in rows:
                item = json.loads(row["data"])
                for dep in item["dependencies"]:
                    old = db.execute("SELECT artifact_type FROM artifacts WHERE id=?", (dep["artifact_id"],)).fetchone()
                    if old and old["artifact_type"] == changed_type and dep["artifact_id"] != new_id:
                        stale_ids.add(row["id"])
            changed = True
            while changed:
                changed = False
                for row in rows:
                    if row["id"] not in stale_ids and any(dep["artifact_id"] in stale_ids for dep in json.loads(row["data"])["dependencies"]):
                        stale_ids.add(row["id"])
                        changed = True
            for artifact_id in stale_ids:
                db.execute("UPDATE artifact_state SET state='STALE' WHERE id=?", (artifact_id,))
        for artifact_id in sorted(stale_ids):
            self.event(project_id, "ARTIFACT_STALE", artifact_id=artifact_id,
                       changed_type=changed_type, new_artifact_id=new_id)

    def is_latest_revision(self, artifact_id: str) -> bool:
        item=self.get_artifact(artifact_id)
        latest=self.latest(item['project_id'],item['artifact_type'])
        return bool(latest and latest['artifact_id']==artifact_id)

    def dependencies_valid(self, artifact_id: str, _seen=None) -> bool:
        item=self.get_artifact(artifact_id);seen=set(_seen or ())
        if artifact_id in seen:return False
        seen.add(artifact_id)
        for dep in item['dependencies']:
            upstream=self.get_artifact(dep['artifact_id'])
            if upstream['project_id']!=item['project_id'] or upstream['output_hash']!=dep['output_hash']:
                return False
            if not self.is_latest_revision(upstream['artifact_id']):return False
            if upstream['current_status'] not in ('READY','APPROVED','LOCKED'):return False
            if not self.dependencies_valid(upstream['artifact_id'],seen):return False
        return True

    def is_usable_input(self, artifact_id: str) -> bool:
        item=self.get_artifact(artifact_id)
        return (item['current_status'] in ('READY','APPROVED','LOCKED') and
                self.is_latest_revision(artifact_id) and self.dependencies_valid(artifact_id))

    def is_current(self, artifact_id: str) -> bool:
        """Compatibility query only. Production consumers use is_usable_input."""
        return self.is_latest_revision(artifact_id) and self.dependencies_valid(artifact_id) and self.get_artifact(artifact_id)['current_status']!='STALE'

    def save_job(self, job: Job) -> Job:
        from vnext.secrets.secure import redact
        if job.error:job=job.model_copy(update={'error':redact(job.error)})
        with self.connection() as db:
            db.execute("INSERT INTO jobs VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
                       (job.job_id, job.project_id, job.idempotency_key, job.model_dump_json()))
        return job

    def job_by_key(self, project_id: str, key: str) -> Job | None:
        with self.connection() as db:
            row = db.execute("SELECT data FROM jobs WHERE project_id=? AND idempotency_key=?", (project_id, key)).fetchone()
        return Job.model_validate_json(row["data"]) if row else None

    def jobs(self, project_id: str) -> list[Job]:
        with self.connection() as db:
            rows = db.execute("SELECT data FROM jobs WHERE project_id=? ORDER BY rowid DESC", (project_id,)).fetchall()
        return [Job.model_validate_json(row["data"]) for row in rows]

    def log(self, project_id: str, level: str, message: str, **metadata) -> None:
        from vnext.secrets.secure import redact
        message,metadata=redact(message),redact(metadata)
        with self.connection() as db:
            db.execute("INSERT INTO logs(project_id,at,level,message,metadata) VALUES (?,?,?,?,?)",
                       (project_id, utc_now(), level, message, json.dumps(metadata, ensure_ascii=False)))

    def logs(self, project_id: str) -> list[dict]:
        with self.connection() as db:
            rows = db.execute("SELECT * FROM logs WHERE project_id=? ORDER BY id DESC LIMIT 200", (project_id,)).fetchall()
        return [{**dict(row), "metadata": json.loads(row["metadata"])} for row in rows]
