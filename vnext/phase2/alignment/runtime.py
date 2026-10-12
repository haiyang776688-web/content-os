"""Durable opt-in alignment lifecycle on existing Artifact/Stage/Job systems."""
from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Callable

from vnext.contracts import utc_now
from vnext.core.jobs.engine import JobControl, JobEngine
from vnext.media.library.service import MediaLibrary
from vnext.migration.legacy import sha
from vnext.phase2.alignment.builder import build_map
from vnext.phase2.alignment.contracts import (
    AlignedTimingMap, AlignmentConfig, AlignmentStatus, BeatTimingBindings,
)
from vnext.phase2.alignment.engine import WhisperCppEngine
from vnext.phase2.alignment.models import AlignmentModelManager
from vnext.phase2.stages import StageCache
from vnext.storage.store import Store, digest


class AlignmentRuntime:
    def __init__(self, store: Store, *, manager: AlignmentModelManager | None = None,
                 engine_factory: Callable[[Path, Path], WhisperCppEngine] = WhisperCppEngine,
                 config: AlignmentConfig | None = None):
        self.store = store
        self.manager = manager or AlignmentModelManager(store.root)
        self.engine_factory = engine_factory
        self.default_config = config or AlignmentConfig()

    @staticmethod
    def script_sha(script: dict) -> str:
        text = script["payload"].get("text") or "".join(row["text"] for row in script["payload"]["segments"])
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def inputs(self, pid: str, voice_id: str | None = None, script_id: str | None = None) -> dict:
        project = self.store.get_project(pid)
        script_id = script_id or project.h2_script_artifact_id
        voice = self.store.get_artifact(voice_id) if voice_id else self.store.latest(pid, "VOICE")
        if not script_id or not voice:
            raise ValueError("APPROVED_SCRIPT_AND_VOICE_REQUIRED")
        script = self.store.get_artifact(script_id)
        if script["artifact_type"] != "SCRIPT" or script_id != project.h2_script_artifact_id:
            raise ValueError("H2_APPROVED_SCRIPT_REQUIRED")
        if voice["artifact_type"] != "VOICE":
            raise ValueError("VOICE_REQUIRED")
        media = next((item for item in MediaLibrary(self.store).assets(pid)
                      if item.asset_id == voice["payload"]["media_asset_id"]), None)
        path = Path(voice["payload"].get("audio_path") or (media.original_path if media else ""))
        if not path.is_file():
            raise ValueError("VOICE_FILE_MISSING")
        audio_sha = media.hash if media else sha(path)
        if sha(path) != audio_sha:
            raise ValueError("VOICE_HASH_MISMATCH")
        return {"project": project, "voice": voice, "script": script, "audio_path": path,
                "audio_sha256": audio_sha, "script_sha256": self.script_sha(script)}

    def identity(self, pid: str, config: AlignmentConfig, *, voice_id: str | None = None,
                 script_id: str | None = None, verify_version: bool = False) -> dict:
        inputs = self.inputs(pid, voice_id, script_id)
        model = self.manager.inspect(config, verify_version=verify_version)
        if not model["ready"]:
            raise ValueError("ALIGNMENT_MODEL_NOT_AVAILABLE:" + model["model_status"] + ":" + model["engine_status"])
        config_hash = digest(config.model_dump())
        cache_key = digest({
            "audio_sha256": inputs["audio_sha256"], "script_sha256": inputs["script_sha256"],
            "engine": config.engine, "engine_version": model["engine_version"],
            "engine_binary_sha256": model["engine_binary_sha256"],
            "model_sha256": model["model_sha256"], "alignment_config_hash": config_hash,
        })
        return {**inputs, "model": model, "config_hash": config_hash, "cache_key": cache_key}

    def cached(self, pid: str, identity: dict) -> dict | None:
        for item in reversed(self.store.artifacts(pid, "ALIGNED_TIMING_MAP")):
            if item["payload"].get("cache_key") != identity["cache_key"] or not self.store.is_usable_input(item["artifact_id"]):
                continue
            try:
                value = AlignedTimingMap.model_validate(item["payload"])
                valid = (
                    item["output_hash"] == digest(item["payload"]) and
                    value.audio_artifact_id == identity["voice"]["artifact_id"] and
                    value.audio_sha256 == identity["audio_sha256"] and
                    value.script_artifact_id == identity["script"]["artifact_id"] and
                    value.script_sha256 == identity["script_sha256"] and
                    value.engine_version == identity["model"]["engine_version"] and
                    value.engine_binary_sha256 == identity["model"]["engine_binary_sha256"] and
                    value.model_sha256 == identity["model"]["model_sha256"] and
                    value.alignment_config_hash == identity["config_hash"]
                )
            except Exception:
                valid = False
            if valid:
                return item
            self.store.set_artifact_state(item["artifact_id"], "STALE")
        return None

    def run_sync(self, pid: str, config: AlignmentConfig | None = None, *,
                 voice_id: str | None = None, script_id: str | None = None,
                 control: JobControl | None = None, verify_version: bool = False) -> dict:
        config = config or self.default_config
        identity = self.identity(pid, config, voice_id=voice_id, script_id=script_id,
                                 verify_version=verify_version)
        if cached := self.cached(pid, identity):
            return {**cached, "alignment_cache_hit": True, "cache_lookup_seconds": 0.0}
        voice, script = identity["voice"], identity["script"]
        dependencies = [voice["artifact_id"], script["artifact_id"]]
        stage_config = {
            "cache_key": identity["cache_key"], "engine": config.engine,
            "engine_version": identity["model"]["engine_version"],
            "model_sha256": identity["model"]["model_sha256"],
            "alignment_config_hash": identity["config_hash"],
        }

        def operation():
            if control:
                control.update("Running post-TTS transcript alignment", .1)
            output_dir = self.store.root / "cache/alignment" / identity["cache_key"]
            engine = self.engine_factory(self.manager.executable(), self.manager.model(config))
            raw, performance, raw_path = engine.run(identity["audio_path"], output_dir, config, control)
            duration = float(voice["payload"].get("duration") or 0)
            performance.update({
                "audio_duration_seconds": duration,
                "real_time_factor": performance["alignment_runtime_seconds"] / duration if duration else None,
                "model_disk_size_bytes": identity["model"]["model_size_bytes"],
                "cache_hit": False,
            })
            value = build_map(
                raw=raw, audio_artifact_id=voice["artifact_id"],
                audio_sha256=identity["audio_sha256"], script_artifact_id=script["artifact_id"],
                script_sha256=identity["script_sha256"], segments=script["payload"]["segments"],
                identity={"engine": config.engine, "engine_version": identity["model"]["engine_version"],
                          "engine_binary_sha256": identity["model"]["engine_binary_sha256"],
                          "model_name": config.model_name, "model_sha256": identity["model"]["model_sha256"],
                          "language": config.language, "alignment_config_hash": identity["config_hash"],
                          "cache_key": identity["cache_key"]},
                raw_alignment_sha256=sha(raw_path), performance=performance,
            )
            status = "READY" if value.coverage >= config.minimum_coverage else "BLOCKED"
            artifact = self.store.create_artifact(
                pid, "ALIGNED_TIMING_MAP", value.model_dump(mode="json"), role="ALIGNMENT",
                worker="WHISPER_CPP_LOCAL", model=config.model_name,
                dependencies=[self.store.dependency(item) for item in dependencies], status=status,
                provenance={"cache_key": identity["cache_key"], "alignment_method": value.alignment_method},
            ).model_dump(mode="json")
            if control:
                control.update("Alignment artifact recorded", .95)
            if status != "READY":
                raise ValueError("ALIGNMENT_COVERAGE_INSUFFICIENT")
            return artifact

        started = time.monotonic()
        result = StageCache(self.store).run(pid, "ALIGNMENT", dependencies, operation,
            config=stage_config, worker="WHISPER_CPP_LOCAL", prompt="NO_DECODING_PROMPT",
            skills="POST_TTS_TRANSCRIPT_ALIGNMENT_V1")
        return {**result, "alignment_cache_hit": bool(result.get("stage_cache_hit")),
                "cache_lookup_seconds": time.monotonic() - started if result.get("stage_cache_hit") else 0.0}

    def enqueue(self, pid: str, config: AlignmentConfig | None = None) -> dict:
        config = config or self.default_config
        identity = self.identity(pid, config)
        if cached := self.cached(pid, identity):
            return {"cache_hit": True, "artifact": cached, "status": self.status(pid, config).model_dump()}
        def run(control: JobControl):
            return self.run_sync(pid, config, control=control)
        job = JobEngine(self.store).submit(
            pid, "P0_ALIGNMENT", identity["cache_key"], run,
            idempotency_key="P0_ALIGNMENT:" + identity["cache_key"],
            stage="Preparing local alignment", current_target=lambda: self._current_cache_key(pid, config),
            controlled=True)
        return {"cache_hit": False, "job": job.model_dump(), "status": self.status(pid, config).model_dump()}

    def _current_cache_key(self, pid: str, config: AlignmentConfig) -> str | None:
        try:
            return self.identity(pid, config)["cache_key"]
        except Exception:
            return None

    def cancel(self, pid: str, job_id: str) -> dict:
        job = JobEngine(self.store).cancel(pid, job_id)
        return {"job": job.model_dump(), "status": self.status(pid).model_dump()}

    def create_bindings(self, pid: str, payload: dict, actor: str) -> dict:
        value = BeatTimingBindings.model_validate(payload)
        script = self.store.get_artifact(value.script_artifact_id)
        if script["project_id"] != pid or script["artifact_type"] != "SCRIPT":
            raise ValueError("BINDING_SCRIPT_INVALID")
        segments = {row["segment_id"]: row["text"] for row in script["payload"]["segments"]}
        for binding in value.bindings:
            clean = __import__("vnext.phase2.alignment.builder", fromlist=["normalize"]).normalize(segments[binding.segment_id])
            if binding.boundary_offset >= len(clean):
                raise ValueError("BINDING_OFFSET_INVALID")
        return self.store.create_artifact(pid, "BEAT_TIMING_BINDINGS", value.model_dump(), role=actor,
            dependencies=[self.store.dependency(script["artifact_id"])]).model_dump()

    def status(self, pid: str, config: AlignmentConfig | None = None) -> AlignmentStatus:
        config = config or self.default_config
        project = self.store.get_project(pid)
        model = self.manager.inspect(config)
        base = dict(requested_mode=project.timing_mode, effective_state="CURRENT",
                    fallback_used=project.timing_mode == "ALIGNED_OPT_IN", model=model)
        if project.timing_mode == "CURRENT":
            return AlignmentStatus(state="NOT_REQUIRED", reason="PRODUCTION_DEFAULT_CURRENT",
                                   gui_actions=["ENQUEUE"] if model["ready"] else ["INSTALL_MODEL"], **base)
        jobs = [job for job in self.store.jobs(pid) if job.kind == "P0_ALIGNMENT"]
        latest_job = jobs[0] if jobs else None
        if latest_job and latest_job.state in ("RUNNING", "QUEUED"):
            return AlignmentStatus(state=latest_job.state, reason=None, job=latest_job.model_dump(),
                                   gui_actions=["CANCEL"], **base)
        if not model["ready"]:
            return AlignmentStatus(state="NOT_AVAILABLE", reason="MODEL_OR_ENGINE_UNAVAILABLE",
                                   job=latest_job.model_dump() if latest_job else None,
                                   gui_actions=["INSTALL_MODEL"], **base)
        try:
            identity = self.identity(pid, config)
        except Exception as error:
            return AlignmentStatus(state="FALLBACK", reason=str(error), gui_actions=["RETRY"], **base)
        if item := self.cached(pid, identity):
            bindings = self.store.latest(pid, "BEAT_TIMING_BINDINGS")
            has_bindings = bool(bindings and self.store.is_usable_input(bindings["artifact_id"]))
            return AlignmentStatus(state="READY", effective_state="ALIGNED" if has_bindings else "CURRENT",
                fallback_used=not has_bindings,
                reason=None if has_bindings else "APPROVED_BINDINGS_REQUIRED",
                alignment_artifact_id=item["artifact_id"], alignment_artifact_sha=item["output_hash"],
                cache_key=identity["cache_key"], gui_actions=["RECOMPUTE"],
                requested_mode=project.timing_mode, model=model)
        latest = self.store.latest(pid, "ALIGNED_TIMING_MAP")
        if latest and latest["current_status"] == "STALE":
            return AlignmentStatus(state="STALE", reason="ALIGNMENT_ARTIFACT_STALE_OR_INTEGRITY_MISMATCH",
                alignment_artifact_id=latest["artifact_id"], alignment_artifact_sha=latest["output_hash"],
                cache_key=identity["cache_key"], job=latest_job.model_dump() if latest_job else None,
                gui_actions=["RECOMPUTE"], **base)
        if latest and latest["payload"].get("cache_key") != identity["cache_key"]:
            if latest["current_status"] != "STALE":
                self.store.set_artifact_state(latest["artifact_id"], "STALE")
            return AlignmentStatus(state="STALE", reason="ALIGNMENT_IDENTITY_CHANGED",
                alignment_artifact_id=latest["artifact_id"], alignment_artifact_sha=latest["output_hash"],
                cache_key=identity["cache_key"], job=latest_job.model_dump() if latest_job else None,
                gui_actions=["RECOMPUTE"], **base)
        if latest_job and latest_job.state in ("FAILED", "CANCELLED", "STALE"):
            return AlignmentStatus(state=latest_job.state, reason=latest_job.error or latest_job.stage,
                cache_key=identity["cache_key"], job=latest_job.model_dump(), gui_actions=["RETRY"], **base)
        return AlignmentStatus(state="FALLBACK", reason="ALIGNMENT_NOT_RUN", cache_key=identity["cache_key"],
                               gui_actions=["ENQUEUE"], **base)
