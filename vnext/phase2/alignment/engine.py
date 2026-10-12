"""Cancellable whisper.cpp process adapter for local post-TTS alignment."""
from __future__ import annotations

import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path

from vnext.core.jobs.engine import JobCancelled, JobControl
from vnext.phase2.alignment.contracts import AlignmentConfig


def sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


class WhisperCppEngine:
    def __init__(self, executable: Path, model: Path):
        self.executable, self.model = Path(executable), Path(model)

    def run(self, audio: Path, output_dir: Path, config: AlignmentConfig,
            control: JobControl | None = None) -> tuple[dict, dict, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        prefix = output_dir / "whisper-dtw"
        raw_path = prefix.with_suffix(".json")
        command = [str(self.executable), "-m", str(self.model), "-f", str(audio),
                   "-l", config.language, "-dtw", config.dtw_preset]
        if not config.flash_attention:
            command.append("-nfa")
        command.extend(["-ojf", "-of", str(prefix)])
        log = output_dir / "whisper.log"
        started = time.monotonic()
        before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        with log.open("w", encoding="utf-8") as handle:
            process = subprocess.Popen(command, stdout=handle, stderr=subprocess.STDOUT, text=True)
            while process.poll() is None:
                if control and control.cancelled():
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    raise JobCancelled("USER_CANCELLED")
                if time.monotonic() - started > config.timeout_seconds:
                    process.kill()
                    raise TimeoutError("ALIGNMENT_TIMEOUT")
                time.sleep(.1)
        if process.returncode:
            raise RuntimeError("ALIGNMENT_PROCESS_FAILED:" + log.read_text(encoding="utf-8", errors="replace")[-500:])
        if not raw_path.is_file():
            raise RuntimeError("ALIGNMENT_OUTPUT_MISSING")
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        elapsed = time.monotonic() - started
        after = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        # macOS reports bytes; Linux reports KiB. The platform label keeps this
        # estimate honest instead of pretending cross-platform exactness.
        import sys
        peak_mb = after / 1024 / 1024 if sys.platform == "darwin" else after / 1024
        performance = {
            "alignment_runtime_seconds": elapsed,
            "peak_memory_mb_approx": peak_mb,
            "peak_memory_measurement": "RUSAGE_CHILDREN_MAXRSS_PROCESS_GROUP_CUMULATIVE",
            "child_maxrss_before": before,
            "child_maxrss_after": after,
        }
        return raw, performance, raw_path
