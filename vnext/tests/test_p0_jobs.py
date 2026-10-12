"""Minimal durable local job contract: one flight, retry, stale result, restart."""
import threading
import time

from vnext.contracts import Job
from vnext.core.jobs.engine import JobEngine
from vnext.storage.store import Store


def done(store, pid, key, expected):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        job = store.job_by_key(pid, key)
        if job and job.state == expected:
            return job
        time.sleep(.01)
    raise AssertionError(f'{key} did not reach {expected}')


def test_local_job_single_flight_and_refresh_visibility(tmp_path):
    store = Store(tmp_path)
    pid = store.create_project('job test').project_id
    engine = JobEngine(store)
    started, release = threading.Event(), threading.Event()
    calls = []

    def operation():
        calls.append(1)
        started.set()
        assert release.wait(2)
        return {'artifact_id': 'ART-test'}

    key = 'P0_RENDER_VIDEO:EDT-v1'
    first = engine.submit(pid, 'P0_RENDER_VIDEO', 'EDT-v1', operation,
        idempotency_key=key, stage='Rendering video')
    assert started.wait(1)
    duplicate = engine.submit(pid, 'P0_RENDER_VIDEO', 'EDT-v1', operation,
        idempotency_key=key, stage='Rendering video')
    assert duplicate.job_id == first.job_id
    assert Store(tmp_path).job_by_key(pid, key).state == 'RUNNING'
    release.set()
    completed = done(store, pid, key, 'COMPLETED')
    assert completed.artifact_id == 'ART-test'
    assert engine.submit(pid, 'P0_RENDER_VIDEO', 'EDT-v1', operation,
        idempotency_key=key, stage='Rendering video').job_id == first.job_id
    assert calls == [1]


def test_stale_target_and_failed_retry_and_orphan_recovery(tmp_path):
    store = Store(tmp_path)
    pid = store.create_project('job recovery').project_id
    engine = JobEngine(store)
    release = threading.Event()
    target = ['EDT-v1']
    key = 'P0_RENDER_VIDEO:EDT-v1'
    engine.submit(pid, 'P0_RENDER_VIDEO', 'EDT-v1', lambda: (release.wait(2), {'artifact_id': 'ART-old'})[1],
        idempotency_key=key, stage='Rendering video', current_target=lambda: target[0])
    target[0] = 'EDT-v2'
    release.set()
    assert done(store, pid, key, 'STALE').artifact_id == 'ART-old'

    attempts = []
    def failing():
        attempts.append(1)
        if len(attempts) == 1:
            raise RuntimeError('transient')
        return {'artifact_id': 'ART-retried'}

    retry_key = 'P0_VOICE:SCRIPT-v1'
    engine.submit(pid, 'P0_VOICE', 'SCRIPT-v1', failing, idempotency_key=retry_key,
        stage='Synthesizing audio')
    assert done(store, pid, retry_key, 'FAILED').error == 'transient'
    engine.submit(pid, 'P0_VOICE', 'SCRIPT-v1', failing, idempotency_key=retry_key,
        stage='Synthesizing audio')
    assert done(store, pid, retry_key, 'COMPLETED').retries == 1

    orphan = Job(job_id='JOB-orphan', request_id='request', project_id=pid,
        kind='P0_STORYBOARD', state='RUNNING', idempotency_key='P0_STORYBOARD:IR-v1',
        target_revision='IR-v1', stage='Rendering stills')
    store.save_job(orphan)
    assert engine.recover_orphans() == 1
    recovered = store.job_by_key(pid, orphan.idempotency_key)
    assert recovered.state == 'FAILED' and recovered.error == 'SERVER_RESTARTED'
