"""Explicit local whisper.cpp/model discovery and installation policy."""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
from pathlib import Path

from vnext.phase2.alignment.contracts import AlignmentConfig


_HASH_CACHE: dict[tuple[str, int, int], str] = {}


def file_sha(path: Path) -> str:
    stat = path.stat()
    key = (str(path.resolve()), stat.st_size, stat.st_mtime_ns)
    if key in _HASH_CACHE:
        return _HASH_CACHE[key]
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    result = value.hexdigest()
    _HASH_CACHE[key] = result
    return result


class AlignmentModelManager:
    """No implicit downloads: discovery is read-only; install is user-triggered."""
    def __init__(self, root: Path, *, executable: Path | None = None, model_path: Path | None = None):
        self.root = Path(root)
        self._executable = Path(executable) if executable else None
        self._model_path = Path(model_path) if model_path else None

    def executable(self) -> Path | None:
        configured = self._executable or (Path(os.environ["CONTENT_OS_WHISPER_CPP"]) if os.environ.get("CONTENT_OS_WHISPER_CPP") else None)
        found = configured or (Path(value) if (value := shutil.which("whisper-cli")) else None)
        return found if found and found.is_file() else None

    def model(self, config: AlignmentConfig) -> Path | None:
        configured = self._model_path or (Path(os.environ["CONTENT_OS_ALIGNMENT_MODEL"]) if os.environ.get("CONTENT_OS_ALIGNMENT_MODEL") else None)
        managed = self.root / "models/alignment" / config.model_name
        for candidate in (configured, managed):
            if candidate and candidate.is_file():
                return candidate
        return None

    def inspect(self, config: AlignmentConfig, *, verify_version: bool = False) -> dict:
        executable, model = self.executable(), self.model(config)
        result = {
            "engine": config.engine,
            "required_engine_version": config.engine_version,
            "model_name": config.model_name,
            "expected_model_sha256": config.model_sha256,
            "model_size_bytes": model.stat().st_size if model else None,
            "engine_status": "MISSING" if not executable else "DISCOVERED",
            "model_status": "MISSING" if not model else "VERIFYING",
            "ready": False,
            "silent_download": False,
            "install_strategy": "USER_TRIGGERED_COPY_OR_DOWNLOAD_TO_MANAGED_MODEL_DIRECTORY",
            "managed_model_location": "<content-os-data>/models/alignment/" + config.model_name,
        }
        if not executable or not model:
            return result
        model_hash = file_sha(model)
        result["model_sha256"] = model_hash
        result["model_status"] = "READY" if model_hash == config.model_sha256 else "CORRUPT"
        result["engine_binary_sha256"] = file_sha(executable)
        if verify_version:
            process = subprocess.run([str(executable), "--version"], capture_output=True, text=True, timeout=30)
            output = process.stdout + process.stderr
            match = re.search(r"whisper\.cpp version:\s*([^\s]+)", output)
            result["engine_version"] = match.group(1) if match else "UNKNOWN"
            result["engine_status"] = "READY" if result["engine_version"] == config.engine_version else "VERSION_MISMATCH"
        else:
            result["engine_version"] = config.engine_version
            result["engine_status"] = "READY"
        result["ready"] = result["model_status"] == "READY" and result["engine_status"] == "READY"
        return result

    def install_from_file(self, source: Path, config: AlignmentConfig) -> dict:
        """Explicit user action. Network download belongs to a future GUI adapter."""
        source = Path(source)
        if not source.is_file():
            raise ValueError("MODEL_SOURCE_MISSING")
        if file_sha(source) != config.model_sha256:
            raise ValueError("MODEL_HASH_MISMATCH")
        target = self.root / "models/alignment" / config.model_name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or file_sha(target) != config.model_sha256:
            shutil.copy2(source, target)
        return self.inspect(config)
