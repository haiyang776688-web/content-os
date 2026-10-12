"""Durable local job state; legacy execution is synchronous, P0 submit is threaded."""
from __future__ import annotations

import time
import uuid
import threading
from typing import Callable, TypeVar

from vnext.contracts import Job, utc_now
from vnext.storage.store import Store


T = TypeVar("T")


class JobCancelled(RuntimeError):
    pass


class JobControl:
    """Cooperative durable control surface shared by P0 background jobs."""
    def __init__(self, store: Store, project_id: str, job_id: str):
        self.store, self.project_id, self.job_id = store, project_id, job_id

    def current(self) -> Job:
        job = next((item for item in self.store.jobs(self.project_id) if item.job_id == self.job_id), None)
        if not job:
            raise KeyError('JOB_NOT_FOUND')
        return job

    def cancelled(self) -> bool:
        return self.current().state == 'CANCELLED'

    def raise_if_cancelled(self) -> None:
        if self.cancelled():
            raise JobCancelled('USER_CANCELLED')

    def update(self, stage: str, progress: float | None = None) -> None:
        job = self.current()
        if job.state == 'CANCELLED':
            raise JobCancelled('USER_CANCELLED')
        self.store.save_job(job.model_copy(update={'stage': stage, 'progress': progress}))


class JobEngine:
    def __init__(self, store: Store):
        self.store = store

    def execute(self, project_id: str, kind: str, operation: Callable[[], T], *,
                idempotency_key: str | None = None, request_id: str | None = None) -> T:
        request_id = request_id or uuid.uuid4().hex
        key = idempotency_key or f"{kind}:{request_id}"
        old = self.store.job_by_key(project_id, key)
        if old and old.state == "COMPLETED" and old.artifact_id:
            return self.store.get_artifact(old.artifact_id)  # type: ignore[return-value]
        job = Job(job_id=old.job_id if old else "JOB-" + uuid.uuid4().hex[:12], request_id=request_id,
            project_id=project_id, kind=kind, state="RUNNING", idempotency_key=key,
            retries=(old.retries + 1) if old else 0, started_at=utc_now())
        self.store.save_job(job)
        start = time.monotonic()
        try:
            result = operation()
            artifact_id = result.get("artifact_id") if isinstance(result, dict) else None
            self.store.save_job(job.model_copy(update={"state": "COMPLETED", "artifact_id": artifact_id,
                "finished_at": utc_now()}))
            self.store.log(project_id, "INFO", "JOB_COMPLETED", kind=kind, job=job.job_id,
                latency_ms=round((time.monotonic() - start) * 1000))
            return result
        except Exception as error:
            self.store.save_job(job.model_copy(update={"state": "FAILED", "error": str(error), "finished_at": utc_now()}))
            self.store.log(project_id, "ERROR", "JOB_FAILED", kind=kind, job=job.job_id, error=str(error))
            raise

    def recover_orphans(self) -> int:
        """A restarted local server cannot resume an in-process P0 worker."""
        with self.store.lock:
            with self.store.connection() as db:
                rows = db.execute("SELECT data FROM jobs").fetchall()
            pending = [job for row in rows if (job := Job.model_validate_json(row['data'])).state in ('QUEUED','RUNNING')]
            for job in pending:
                if job.kind.startswith('P0_'):
                    self.store.save_job(job.model_copy(update={"state": "FAILED", "error": "SERVER_RESTARTED",
                        "finished_at": utc_now(), "stage": "Interrupted by server restart"}))
            return sum(job.kind.startswith('P0_') for job in pending)

    def submit(self, project_id: str, kind: str, target_revision: str, operation: Callable[..., T], *,
               idempotency_key: str, stage: str, current_target: Callable[[], str | None] | None = None,
               controlled: bool = False) -> Job:
        """Return immediately; one local daemon thread owns a project/kind/revision key."""
        if not kind.startswith('P0_'):
            raise ValueError('P0_JOB_KIND_REQUIRED')
        with self.store.lock:
            old = self.store.job_by_key(project_id, idempotency_key)
            if old and old.state in ('QUEUED', 'RUNNING', 'COMPLETED'):
                return old
            job = Job(job_id=old.job_id if old else 'JOB-' + uuid.uuid4().hex[:12],
                request_id=uuid.uuid4().hex, project_id=project_id, kind=kind, state='QUEUED',
                idempotency_key=idempotency_key, retries=(old.retries+1) if old else 0,
                target_revision=target_revision, stage=stage, progress=0)
            self.store.save_job(job)

            def run() -> None:
                try:
                    control = JobControl(self.store, project_id, job.job_id)
                    control.raise_if_cancelled()
                    running = control.current().model_copy(update={'state':'RUNNING','started_at':utc_now()})
                    self.store.save_job(running)
                    result = operation(control) if controlled else operation()
                    control.raise_if_cancelled()
                    artifact = result.get('artifact_id') if isinstance(result, dict) else None
                    if not artifact and isinstance(result, dict) and isinstance(result.get('voice'), dict):
                        artifact = result['voice'].get('artifact_id')
                    stale = bool(current_target and current_target() != target_revision)
                    self.store.save_job(job.model_copy(update={'state': 'STALE' if stale else 'COMPLETED',
                        'artifact_id': artifact, 'finished_at': utc_now(),
                        'stage': 'Target revision changed' if stale else 'Completed'}))
                    self.store.log(project_id, 'INFO', 'JOB_STALE' if stale else 'JOB_COMPLETED',
                        kind=kind, job=job.job_id, target_revision=target_revision)
                except JobCancelled:
                    current = control.current()
                    self.store.save_job(current.model_copy(update={'state': 'CANCELLED', 'error': 'USER_CANCELLED',
                        'finished_at': utc_now(), 'stage': 'Cancelled', 'progress': current.progress}))
                    self.store.log(project_id, 'INFO', 'JOB_CANCELLED', kind=kind, job=job.job_id)
                except Exception as error:
                    current = control.current()
                    if current.state != 'CANCELLED':
                        self.store.save_job(current.model_copy(update={'state': 'FAILED', 'error': str(error),
                            'finished_at': utc_now(), 'stage': 'Failed'}))
                    self.store.log(project_id, 'ERROR', 'JOB_FAILED', kind=kind, job=job.job_id, error=str(error))

            threading.Thread(target=run, name=f'content-os-{kind}-{job.job_id}', daemon=True).start()
            return job

    def cancel(self, project_id: str, job_id: str) -> Job:
        """Request cooperative cancellation; completed jobs remain immutable."""
        with self.store.lock:
            job = next((item for item in self.store.jobs(project_id) if item.job_id == job_id), None)
            if not job:
                raise KeyError('JOB_NOT_FOUND')
            if job.state not in ('QUEUED', 'RUNNING', 'WAITING', 'RETRYING'):
                return job
            updated = job.model_copy(update={'state': 'CANCELLED', 'error': 'USER_CANCELLED',
                'finished_at': utc_now(), 'stage': 'Cancellation requested'})
            self.store.save_job(updated)
            self.store.log(project_id, 'INFO', 'JOB_CANCEL_REQUESTED', kind=job.kind, job=job.job_id)
            return updated
