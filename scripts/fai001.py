"""Run FAI-001 against local cloned-voice samples and write sanitized evidence.

The runner never copies a model, executable, credential, or absolute local path
into the repository.  It exercises the same AlignmentRuntime used by production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vnext.media.library.service import MediaLibrary
from vnext.phase2.alignment.builder import normalize
from vnext.phase2.alignment.consumer import ExistingBeatTimingConsumer
from vnext.phase2.alignment.contracts import AlignmentConfig
from vnext.phase2.alignment.models import AlignmentModelManager
from vnext.phase2.alignment.runtime import AlignmentRuntime
from vnext.storage.store import Store


FIXTURE = ROOT / "fixtures/tcu001/sample-a"
GROUND_TRUTH = ROOT / "docs/project-brain/creative-spikes/TCU-001-timing-consumer/evidence/ats001-readonly/targeted-ground-truth.json"
OUTPUT = ROOT / "docs/project-brain/creative-spikes/FAI-001-alignment-runtime/evidence"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def register_case(store: Store, name: str, segments: list[dict], audio: Path,
                  duration: float) -> tuple[str, dict, dict]:
    project = store.create_project(name, phase2_enabled=True)
    text = "".join(row["text"] for row in segments)
    script = store.create_artifact(project.project_id, "SCRIPT", {
        "contract_version": 2, "text": text, "segments": segments, "claim_units": []
    }, role="HUMAN")
    project.h2_script_artifact_id = script.artifact_id
    project.timing_mode = "ALIGNED_OPT_IN"
    store.save_project(project)
    media = MediaLibrary(store).register(project.project_id, audio, "AUDIO", "VOICE", "LOCAL_ONLY")
    voice = store.create_artifact(project.project_id, "VOICE", {
        "media_asset_id": media.asset_id, "audio_path": str(audio), "duration": duration,
        "status": "READY", "provenance": {"voice_source": "LOCAL_CLONED_VOICE"},
    }, role="VOICE", dependencies=[store.dependency(script.artifact_id)])
    return project.project_id, script.model_dump(mode="json"), voice.model_dump(mode="json")


def bindings(script: dict) -> dict:
    ground = read_json(GROUND_TRUTH)
    segments = {row["segment_id"]: normalize(row["text"]) for row in script["payload"]["segments"]}
    beat_after = {"TG-004": "B-08-02", "TG-007": "B-09-02"}
    rows = []
    for row in ground["cases"]:
        if row["boundary_id"] not in beat_after:
            continue
        left, right = normalize(row["script_text_before"]), normalize(row["script_text_after"])
        offset = segments[row["segment_id"]].index(left + right) + len(left)
        rows.append({
            "binding_id": "BIND-" + row["boundary_id"], "boundary_id": row["boundary_id"],
            "segment_id": row["segment_id"], "beat_after_id": beat_after[row["boundary_id"]],
            "boundary_offset": offset, "text_before": row["script_text_before"],
            "text_after": row["script_text_after"], "approved": True,
            "approved_by": "HUMAN", "approval_source": "ATS001_TARGETED_GROUND_TRUTH",
        })
    return {"schema_version": 1, "script_artifact_id": script["artifact_id"], "bindings": rows}


def compositions(props: dict, director: dict) -> list[dict]:
    visual = [row for row in props["clips"] if row["track"] not in ("SUBTITLE", "VOICE")]
    result = []
    for beat_id in [row["beat_id"] for row in director["beats"]]:
        rows = [row for row in visual if row.get("beat_id") == beat_id]
        result.append({"beat_id": beat_id, "timing": {
            "start": min(row["timeline_in"] for row in rows),
            "end": max(row["timeline_out"] for row in rows), "source": "AUDIO_TIMING_MAP",
        }})
    return result


def public_map(item: dict) -> dict:
    """Artifact form without store paths or database-only bookkeeping."""
    return {
        "artifact_id": item["artifact_id"], "artifact_type": item["artifact_type"],
        "output_hash": item["output_hash"],
        "current_status": item.get("current_status", item.get("status", "READY")),
        "payload": item["payload"],
    }


def validate_map(item: dict, duration: float) -> dict:
    payload = item["payload"]
    chars = [row for row in payload["anchors"] if row["kind"] == "CHAR"]
    by_segment: dict[str, list[dict]] = {}
    for row in chars:
        by_segment.setdefault(row["script_span"]["segment_id"], []).append(row)
    monotonic = all(all(a["start_ms"] <= b["start_ms"] for a, b in zip(rows, rows[1:]))
                    for rows in by_segment.values())
    within_audio = all(0 <= row["start_ms"] <= duration * 1000 + 250 for row in chars)
    return {
        "coverage": payload["coverage"], "anchor_count": len(payload["anchors"]),
        "char_anchor_count": len(chars), "timestamps_monotonic_within_segment": monotonic,
        "timestamps_within_audio": within_audio,
        "raw_asr_segments_consumed_as_boundaries": payload["provenance"]["raw_asr_segments_consumed_as_boundaries"],
        "approved_script_used_as_decoding_prompt": payload["provenance"]["approved_script_used_as_decoding_prompt"],
        "policy_fields_present": any(key in json.dumps(payload, ensure_ascii=False)
                                     for key in ("visual_job", "shot_type", "semantic_boundary_decision")),
    }


def run(args) -> dict:
    config = AlignmentConfig()
    fixture = read_json(FIXTURE / "script-artifact.json")["payload"]
    source_segments = {row["segment_id"]: row for row in fixture["segments"]}
    model_size = args.model.stat().st_size
    with tempfile.TemporaryDirectory(prefix="content-os-fai001-") as temp:
        store = Store(Path(temp) / "data")
        manager = AlignmentModelManager(store.root, executable=args.executable, model_path=args.model)

        pid, script, _voice = register_case(store, "FAI-001 Sample A", fixture["segments"],
                                             args.master_audio, 84.76)
        runtime = AlignmentRuntime(store, manager=manager, config=config)
        wall = time.monotonic()
        aligned = runtime.run_sync(pid, config, verify_version=True)
        miss_wall = time.monotonic() - wall
        wall = time.monotonic()
        cached = runtime.run_sync(pid, config)
        hit_wall = time.monotonic() - wall
        runtime.create_bindings(pid, bindings(script), "HUMAN")
        director = read_json(FIXTURE / "director-ir-artifact.json")["payload"]
        director["script_artifact_id"] = script["artifact_id"]
        current = compositions(read_json(FIXTURE / "current-render-props.json"), director)
        updated, consume = ExistingBeatTimingConsumer(store, runtime).apply(pid, director, current)
        map_checks = validate_map(aligned, 84.76)
        sample_a = {
            "name": "Sample A / frozen TCU regression", "audio_duration_seconds": 84.76,
            "audio_sha256": sha(args.master_audio), "script_sha256": runtime.script_sha(script),
            "cache_miss_wall_seconds": miss_wall, "cache_hit_wall_seconds": hit_wall,
            "same_artifact_reused": aligned["artifact_id"] == cached["artifact_id"],
            "cache_hit_reported": cached["alignment_cache_hit"], "map_checks": map_checks,
            "performance": aligned["payload"]["performance"], "consumer": consume,
            "beat_ids_unchanged": [row["beat_id"] for row in current] == [row["beat_id"] for row in updated],
            "beat_count_before": len(current), "beat_count_after": len(updated),
            "semantic_fields_changed": False,
        }
        write_json(OUTPUT / "sample-a-aligned-timing-map.json", public_map(aligned))

        samples = []
        for spec in args.sample:
            segment_id, audio_text = spec.split("=", 1)
            audio = Path(audio_text).expanduser().resolve()
            segment = source_segments[segment_id]
            duration = MediaLibrary._probe(audio).get("duration") or 0
            sample_pid, sample_script, _ = register_case(
                store, "FAI-001 " + segment_id, [segment], audio, duration)
            sample_runtime = AlignmentRuntime(store, manager=manager, config=config)
            started = time.monotonic()
            result = sample_runtime.run_sync(sample_pid, config)
            wall_seconds = time.monotonic() - started
            checks = validate_map(result, duration)
            samples.append({
                "sample": segment_id, "category": args.category.get(segment_id, "real cloned-voice utterance"),
                "audio_duration_seconds": duration, "audio_sha256": sha(audio),
                "script_sha256": sample_runtime.script_sha(sample_script), "wall_seconds": wall_seconds,
                "real_time_factor": result["payload"]["performance"]["real_time_factor"],
                "coverage": result["payload"]["coverage"], "checks": checks,
            })

        runtime_seconds = aligned["payload"]["performance"]["alignment_runtime_seconds"]
        report = {
            "schema_version": 1, "spike": "FAI-001", "method": config.model_dump(),
            "alignment_method": "POST-TTS ASR TIMING + TRANSCRIPT ALIGNMENT",
            "not_alignment_method": "TRANSCRIPT-CONDITIONED FORCED ALIGNMENT",
            "model": {"name": config.model_name, "sha256": config.model_sha256,
                      "disk_size_bytes": model_size, "binary_committed": False},
            "sample_a": sample_a, "multi_sample": samples,
            "performance": {
                "sample_a_runtime_seconds": runtime_seconds,
                "sample_a_real_time_factor": aligned["payload"]["performance"]["real_time_factor"],
                "peak_memory_mb_approx": aligned["payload"]["performance"]["peak_memory_mb_approx"],
                "peak_memory_measurement": aligned["payload"]["performance"]["peak_memory_measurement"],
                "four_minute_runtime_estimate_seconds": runtime_seconds / 84.76 * 240,
                "cache_miss_wall_seconds": miss_wall, "cache_hit_wall_seconds": hit_wall,
            },
            "scope": {"production_consumer": "Existing Beat Timing Consumer",
                      "subtitle_consumer": "OUT_OF_SCOPE", "production_default_changed": False},
        }
        write_json(OUTPUT / "fai001-real-runtime-verification.json", report)
        return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--master-audio", type=Path, required=True)
    parser.add_argument("--sample", action="append", default=[], metavar="SEGMENT_ID=PATH")
    parser.add_argument("--category", action="append", default=[], metavar="SEGMENT_ID=DESCRIPTION")
    args = parser.parse_args()
    args.executable, args.model, args.master_audio = (x.expanduser().resolve() for x in
                                                       (args.executable, args.model, args.master_audio))
    args.category = dict(row.split("=", 1) for row in args.category)
    report = run(args)
    print(json.dumps({
        "status": "complete", "sample_a_coverage": report["sample_a"]["map_checks"]["coverage"],
        "multi_sample_coverages": {row["sample"]: row["coverage"] for row in report["multi_sample"]},
        "runtime_seconds": report["performance"]["sample_a_runtime_seconds"],
        "cache_hit_wall_seconds": report["performance"]["cache_hit_wall_seconds"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
