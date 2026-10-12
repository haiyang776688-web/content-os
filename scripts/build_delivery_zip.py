"""Create a checked handoff archive without installed dependencies or transient render caches."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "content-os-vnext-phase2.1-h3-2026-09-28"
DATABASE = Path("phase2_preview_data/content_os_vnext.sqlite3")
SKIP_DIRS = {".venv", ".pytest_cache", "__pycache__", "node_modules"}
SKIP_FILES = {".DS_Store", ".env"}
SKIP_TREE = Path("vnext/renderers/remotion/project/public")


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def files_to_ship():
    for folder, dirs, files in os.walk(ROOT):
        relative_folder = Path(folder).relative_to(ROOT)
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS
                         and relative_folder / d != SKIP_TREE)
        for name in sorted(files):
            relative = relative_folder / name
            if name in SKIP_FILES or name.endswith((".pyc", ".pyo", ".sqlite3-wal", ".sqlite3-shm")):
                continue
            source = ROOT / relative
            if source.is_symlink():
                raise ValueError(f"Symlink requires an explicit delivery decision: {relative}")
            if source.is_file():
                yield relative, source


def build(output: Path) -> dict:
    output = output.expanduser().resolve()
    if output.exists():
        raise FileExistsError(output)
    secret_scan = json.loads((ROOT / "examples/activation/SECRET_SCAN.json").read_text())
    protected = json.loads((ROOT / "examples/activation/PROTECTED_BASELINES.json").read_text())
    if not secret_scan.get("passed") or not protected.get("all_unchanged"):
        raise ValueError("Delivery security or baseline verification has not passed")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(output.name + ".partial")
    entries = []
    try:
        with tempfile.TemporaryDirectory(prefix="content-os-delivery-") as temporary:
            stable_db = Path(temporary) / DATABASE.name
            with sqlite3.connect(ROOT / DATABASE) as source, sqlite3.connect(stable_db) as target:
                source.backup(target)
            with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=6, allowZip64=True) as archive:
                for relative, source in files_to_ship():
                    if relative == DATABASE:
                        source = stable_db
                    member = f"{PREFIX}/{relative.as_posix()}"
                    archive.write(source, member)
                    entries.append({"path": relative.as_posix(), "size": source.stat().st_size,
                                    "sha256": digest(source)})
                manifest = {"schema_version": 1,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "package_root": PREFIX,
                            "project_id": "PRJ-bba515713057",
                            "h3_review_gate_id": "ART-98b97704be3f4aa2",
                            "h4_publish_authorized": False,
                            "excluded_runtime_paths": [".venv", "node_modules",
                                                       "vnext/renderers/remotion/project/public",
                                                       "__pycache__", ".pytest_cache"],
                            "files": entries}
                archive.writestr(f"{PREFIX}/DELIVERY_MANIFEST.json",
                                 json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        with zipfile.ZipFile(partial) as archive:
            broken = archive.testzip()
            if broken:
                raise ValueError(f"ZIP CRC failed: {broken}")
            if len(archive.namelist()) != len(entries) + 1:
                raise ValueError("ZIP member count mismatch")
            for entry in entries:
                member = f"{PREFIX}/{entry['path']}"
                sha = hashlib.sha256()
                with archive.open(member) as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        sha.update(block)
                if sha.hexdigest() != entry["sha256"]:
                    raise ValueError(f"ZIP SHA-256 mismatch: {member}")
        partial.replace(output)
        checksum = digest(output)
        output.with_name(output.name + ".sha256").write_text(f"{checksum}  {output.name}\n")
        return {"output": str(output), "size_bytes": output.stat().st_size,
                "file_count": len(entries), "sha256": checksum}
    finally:
        partial.unlink(missing_ok=True)


if __name__ == "__main__":
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads" / f"{PREFIX}.zip"
    print(json.dumps(build(destination), ensure_ascii=False))
