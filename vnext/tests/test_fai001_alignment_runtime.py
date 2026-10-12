"""FAI-001 lifecycle, cache, invalidation, failure and semantic regressions."""
from __future__ import annotations

import hashlib
import json
import threading
import time
import wave
from pathlib import Path

import pytest

from vnext.contracts import Job
from vnext.core.jobs.engine import JobCancelled, JobEngine
from vnext.media.library.service import MediaLibrary
from vnext.phase2.alignment.builder import normalize
from vnext.phase2.alignment.consumer import ExistingBeatTimingConsumer
from vnext.phase2.alignment.contracts import AlignmentConfig
from vnext.phase2.alignment.models import AlignmentModelManager
from vnext.phase2.alignment.runtime import AlignmentRuntime
from vnext.phase2.production import Production
from vnext.storage.store import Store


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures/tcu001/sample-a"
RAW = ROOT / "docs/project-brain/creative-spikes/TCU-001-timing-consumer/evidence/ats001-readonly/whisper-medium-dtw-raw.json"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FakeEngine:
    calls = 0
    raw = json.loads(RAW.read_text())

    def __init__(self, _executable, _model):
        pass

    def run(self, _audio, output_dir, _config, control=None):
        type(self).calls += 1
        if control:
            control.raise_if_cancelled()
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "fake-raw.json"
        path.write_text(json.dumps(type(self).raw), encoding="utf-8")
        return type(self).raw, {"alignment_runtime_seconds": .25,
                               "peak_memory_mb_approx": 12,
                               "peak_memory_measurement": "TEST"}, path


class SlowEngine(FakeEngine):
    started = threading.Event()

    def run(self, _audio, output_dir, _config, control=None):
        type(self).started.set()
        while True:
            if control and control.cancelled():
                raise JobCancelled("USER_CANCELLED")
            time.sleep(.01)


@pytest.fixture
def system(tmp_path):
    FakeEngine.calls = 0
    store = Store(tmp_path / "data")
    project = store.create_project("FAI test", phase2_enabled=True)
    script_fixture = json.loads((FIXTURE / "script-artifact.json").read_text())
    script = store.create_artifact(project.project_id, "SCRIPT", script_fixture["payload"], role="HUMAN")
    project.h2_script_artifact_id = script.artifact_id
    project.timing_mode = "ALIGNED_OPT_IN"
    store.save_project(project)
    audio = tmp_path / "voice.wav"
    with wave.open(str(audio), "wb") as output:
        output.setnchannels(1); output.setsampwidth(2); output.setframerate(16000)
        output.writeframes(b"\x00\x00" * 1600)
    media = MediaLibrary(store).register(project.project_id, audio, "AUDIO", "VOICE", "LOCAL_ONLY")
    voice = store.create_artifact(project.project_id, "VOICE", {
        "media_asset_id": media.asset_id, "audio_path": str(audio), "duration": 84.76,
        "status": "READY", "provenance": {}}, role="VOICE", dependencies=[store.dependency(script.artifact_id)])
    executable = tmp_path / "whisper-cli"; executable.write_bytes(b"fake-whisper-1.9.1")
    model = tmp_path / "ggml-medium.bin"; model.write_bytes(b"fake-model-medium")
    config = AlignmentConfig(model_sha256=file_hash(model))
    manager = AlignmentModelManager(store.root, executable=executable, model_path=model)
    runtime = AlignmentRuntime(store, manager=manager, engine_factory=FakeEngine, config=config)
    return store, project.project_id, script.model_dump(), voice.model_dump(), config, runtime, manager, audio


def wait_job(store, pid, job_id, states=("COMPLETED", "FAILED", "CANCELLED", "STALE")):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        job = next(row for row in store.jobs(pid) if row.job_id == job_id)
        if job.state in states:
            return job
        time.sleep(.01)
    raise AssertionError("job did not finish")


def test_valid_cached_artifact_avoids_expensive_rerun(system):
    store, pid, _script, _voice, config, runtime, *_ = system
    first = runtime.run_sync(pid, config)
    second = runtime.run_sync(pid, config)
    assert first["artifact_id"] == second["artifact_id"]
    assert second["alignment_cache_hit"] is True
    assert FakeEngine.calls == 1
    status = runtime.status(pid, config)
    assert status.state == "READY"
    assert status.effective_state == "CURRENT" and status.reason == "APPROVED_BINDINGS_REQUIRED"


def test_current_is_default_and_alignment_is_not_required(system):
    store, pid, script, _voice, config, runtime, *_ = system
    project = store.get_project(pid); project.timing_mode = "CURRENT"; store.save_project(project)
    assert runtime.status(pid, config).state == "NOT_REQUIRED"
    director = json.loads((FIXTURE / "director-ir-artifact.json").read_text())["payload"]
    director["script_artifact_id"] = script["artifact_id"]
    current = [{"beat_id": "B-01-01", "timing": {"start": 0, "end": 1, "source": "AUDIO_TIMING_MAP"}}]
    result, report = ExistingBeatTimingConsumer(store, runtime).apply(pid, director, current)
    assert result == current
    assert report["timing_mode"] == "CURRENT" and report["fallback_used"] is False


def test_audio_change_marks_alignment_stale(system, tmp_path):
    store, pid, script, _voice, config, runtime, *_ = system
    item = runtime.run_sync(pid, config)
    changed = tmp_path / "changed.wav"; changed.write_bytes(b"RIFF-changed-audio")
    media = MediaLibrary(store).register(pid, changed, "AUDIO", "VOICE", "LOCAL_ONLY")
    store.create_artifact(pid, "VOICE", {"media_asset_id": media.asset_id, "audio_path": str(changed),
        "duration": 84.76, "status": "READY", "provenance": {}}, role="VOICE",
        dependencies=[store.dependency(script["artifact_id"])])
    assert runtime.status(pid, config).state == "STALE"
    assert store.get_artifact(item["artifact_id"])["current_status"] == "STALE"


def test_script_change_marks_alignment_stale(system):
    store, pid, script, _voice, config, runtime, *_ = system
    item = runtime.run_sync(pid, config)
    payload = json.loads((FIXTURE / "script-artifact.json").read_text())["payload"]
    payload["text"] += "新增。"; payload["segments"][-1]["text"] += "新增。"
    changed = store.create_artifact(pid, "SCRIPT", payload, role="HUMAN")
    project = store.get_project(pid); project.h2_script_artifact_id = changed.artifact_id; store.save_project(project)
    assert runtime.status(pid, config).state == "STALE"
    assert store.get_artifact(item["artifact_id"])["current_status"] == "STALE"


def test_model_change_changes_cache_identity_and_stales(system, tmp_path):
    store, pid, *_middle, config, runtime, _manager, _audio = system
    item = runtime.run_sync(pid, config)
    model = tmp_path / "another-model.bin"; model.write_bytes(b"a-different-valid-model")
    changed_config = config.model_copy(update={"model_sha256": file_hash(model), "model_name": "another-model.bin"})
    manager = AlignmentModelManager(store.root, executable=runtime.manager.executable(), model_path=model)
    changed = AlignmentRuntime(store, manager=manager, engine_factory=FakeEngine, config=changed_config)
    assert changed.status(pid, changed_config).state == "STALE"
    assert store.get_artifact(item["artifact_id"])["current_status"] == "STALE"


def test_alignment_config_change_changes_identity_and_stales(system):
    store, pid, _script, _voice, config, runtime, *_ = system
    item = runtime.run_sync(pid, config)
    changed_config = config.model_copy(update={"anchor_confidence": .72})
    changed = AlignmentRuntime(store, manager=runtime.manager, engine_factory=FakeEngine,
                               config=changed_config)
    assert changed.status(pid, changed_config).state == "STALE"
    assert store.get_artifact(item["artifact_id"])["current_status"] == "STALE"


def test_missing_and_corrupt_model_report_not_available_and_fallback(system, tmp_path):
    store, pid, *_middle, config, runtime, manager, _audio = system
    missing = AlignmentRuntime(store, manager=AlignmentModelManager(store.root,
        executable=manager.executable(), model_path=tmp_path / "missing.bin"), engine_factory=FakeEngine, config=config)
    assert missing.status(pid, config).state == "NOT_AVAILABLE"
    corrupt = tmp_path / "corrupt.bin"; corrupt.write_bytes(b"corrupt")
    corrupt_runtime = AlignmentRuntime(store, manager=AlignmentModelManager(store.root,
        executable=manager.executable(), model_path=corrupt), engine_factory=FakeEngine, config=config)
    status = corrupt_runtime.status(pid, config)
    assert status.state == "NOT_AVAILABLE" and status.fallback_used


def test_cancel_running_alignment_is_terminal_and_safe(system):
    store, pid, _script, _voice, config, _runtime, manager, _audio = system
    SlowEngine.started.clear()
    runtime = AlignmentRuntime(store, manager=manager, engine_factory=SlowEngine, config=config)
    submitted = runtime.enqueue(pid, config)
    job_id = submitted["job"]["job_id"]
    assert SlowEngine.started.wait(1)
    runtime.cancel(pid, job_id)
    job = wait_job(store, pid, job_id)
    assert job.state == "CANCELLED"
    status = runtime.status(pid, config)
    assert status.state == "CANCELLED" and status.effective_state == "CURRENT" and status.fallback_used


def test_process_crash_recovers_to_failed_then_retry(system):
    store, pid, _script, _voice, config, runtime, *_ = system
    identity = runtime.identity(pid, config)
    orphan = Job(job_id="JOB-alignment-orphan", request_id="r", project_id=pid,
        kind="P0_ALIGNMENT", state="RUNNING", idempotency_key="P0_ALIGNMENT:" + identity["cache_key"],
        target_revision=identity["cache_key"], stage="Running alignment")
    store.save_job(orphan)
    assert JobEngine(store).recover_orphans() == 1
    assert runtime.status(pid, config).state == "FAILED"
    submission = runtime.enqueue(pid, config)
    done = wait_job(store, pid, submission["job"]["job_id"])
    assert done.state == "COMPLETED" and done.retries == 1


def test_partial_coverage_fails_closed_to_current(system):
    store, pid, _script, _voice, config, _runtime, manager, _audio = system
    class EmptyEngine(FakeEngine):
        raw = {"transcription": []}
    runtime = AlignmentRuntime(store, manager=manager, engine_factory=EmptyEngine, config=config)
    with pytest.raises(ValueError, match="COVERAGE_INSUFFICIENT"):
        runtime.run_sync(pid, config)
    status = runtime.status(pid, config)
    assert status.effective_state == "CURRENT" and status.fallback_used


def test_artifact_hash_mismatch_is_refused(system):
    store, pid, _script, _voice, config, runtime, *_ = system
    item = runtime.run_sync(pid, config)
    with store.connection() as db:
        row = db.execute("SELECT data FROM artifacts WHERE id=?", (item["artifact_id"],)).fetchone()
        value = json.loads(row["data"]); value["payload"]["audio_sha256"] = "0" * 64
        db.execute("UPDATE artifacts SET data=? WHERE id=?", (json.dumps(value), item["artifact_id"]))
    assert runtime.status(pid, config).state == "STALE"
    assert runtime.cached(pid, runtime.identity(pid, config)) is None


def _bindings(script):
    ground = json.loads((ROOT / "docs/project-brain/creative-spikes/TCU-001-timing-consumer/evidence/ats001-readonly/targeted-ground-truth.json").read_text())
    segments = {row["segment_id"]: normalize(row["text"]) for row in script["payload"]["segments"]}
    after = {"TG-004": "B-08-02", "TG-007": "B-09-02"}
    rows = []
    for case in ground["cases"]:
        if case["boundary_id"] not in after:
            continue
        left, right = normalize(case["script_text_before"]), normalize(case["script_text_after"])
        position = segments[case["segment_id"]].index(left + right) + len(left)
        rows.append({"binding_id": "BIND-" + case["boundary_id"], "boundary_id": case["boundary_id"],
            "segment_id": case["segment_id"], "beat_after_id": after[case["boundary_id"]],
            "boundary_offset": position, "text_before": case["script_text_before"],
            "text_after": case["script_text_after"], "approved": True,
            "approved_by": "HUMAN", "approval_source": "ATS001_TARGETED_GROUND_TRUTH"})
    return {"schema_version": 1, "script_artifact_id": script["artifact_id"], "bindings": rows}


def test_sample_a_existing_beats_regress_without_semantic_change(system):
    store, pid, script, _voice, config, runtime, *_ = system
    runtime.run_sync(pid, config)
    runtime.create_bindings(pid, _bindings(script), "HUMAN")
    props = json.loads((FIXTURE / "current-render-props.json").read_text())
    director = json.loads((FIXTURE / "director-ir-artifact.json").read_text())["payload"]
    director["script_artifact_id"] = script["artifact_id"]
    visual = [row for row in props["clips"] if row["track"] not in ("SUBTITLE", "VOICE")]
    compositions = []
    for beat_id in [row["beat_id"] for row in director["beats"]]:
        rows = [row for row in visual if row.get("beat_id") == beat_id]
        compositions.append({"beat_id": beat_id, "timing": {
            "start": min(row["timeline_in"] for row in rows),
            "end": max(row["timeline_out"] for row in rows), "source": "AUDIO_TIMING_MAP"}})
    result, report = ExistingBeatTimingConsumer(store, runtime).apply(pid, director, compositions)
    assert report["timing_mode"] == "ALIGNED", report.get("reason")
    assert len(result) == len(compositions) == 18
    assert [row["beat_id"] for row in result] == [row["beat_id"] for row in compositions]
    applied = {row["boundary_id"]: row for row in report["applied"]}
    assert applied["TG-004"]["new_timestamp_ms"] == 72880
    assert applied["TG-007"]["new_timestamp_ms"] == 82860
    assert report["timing_mode"] == "ALIGNED" and report["beat_count_before"] == report["beat_count_after"]
    assert runtime.status(pid, config).effective_state == "ALIGNED"


def test_edt_cache_identity_adds_only_usable_opt_in_alignment_artifacts(system):
    store, pid, *_ = system
    store.create_artifact(pid, "DIRECTOR_IR", {"test": True}, role="DIRECTOR")
    store.create_artifact(pid, "TYPOGRAPHY_PROFILE", {"test": True}, role="TYPOGRAPHY")
    store.create_artifact(pid, "PROJECT_FONT_SNAPSHOT", {"test": True}, role="FONT_REGISTRY")
    before = Production(store).edt_inputs(pid)
    aligned = store.create_artifact(pid, "ALIGNED_TIMING_MAP", {"test": True}, role="ALIGNMENT")
    binding = store.create_artifact(pid, "BEAT_TIMING_BINDINGS", {"test": True}, role="HUMAN")
    after = Production(store).edt_inputs(pid)
    assert aligned.artifact_id not in before and binding.artifact_id not in before
    assert aligned.artifact_id in after and binding.artifact_id in after
    store.set_artifact_state(aligned.artifact_id, "STALE")
    stale = Production(store).edt_inputs(pid)
    assert aligned.artifact_id not in stale and binding.artifact_id in stale


def test_alignment_writers_and_human_opt_in_api_are_enforced(system):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from vnext.core.runtime import Runtime
    from vnext.phase2.api import attach

    store, pid, *_ = system
    with pytest.raises(PermissionError, match="SINGLE_WRITER_VIOLATION"):
        store.create_artifact(pid, "ALIGNED_TIMING_MAP", {}, role="DIRECTOR")
    with pytest.raises(PermissionError, match="SINGLE_WRITER_VIOLATION"):
        store.create_artifact(pid, "BEAT_TIMING_BINDINGS", {}, role="ALIGNMENT")
    app = FastAPI(); attach(app, store, ROOT, Runtime(store)); client = TestClient(app)
    forbidden = client.post(f"/api/projects/{pid}/phase2/alignment/mode",
        json={"payload": {"mode": "CURRENT"}, "actor": "DIRECTOR"})
    assert forbidden.status_code == 403
    accepted = client.post(f"/api/projects/{pid}/phase2/alignment/mode",
        json={"payload": {"mode": "CURRENT"}, "actor": "HUMAN"})
    assert accepted.status_code == 200 and accepted.json()["state"] == "NOT_REQUIRED"
