"""Linked-folder media index. Originals stay at their original paths."""
from __future__ import annotations

import json
import mimetypes
import subprocess
import uuid
from pathlib import Path

from vnext.contracts import MediaAsset, utc_now
from vnext.migration.legacy import sha
from vnext.storage.store import Store


EXTENSIONS = {".png": "IMAGE", ".jpg": "IMAGE", ".jpeg": "IMAGE", ".webp": "IMAGE",
              ".mp4": "VIDEO", ".mov": "VIDEO", ".mkv": "VIDEO", ".wav": "AUDIO", ".mp3": "AUDIO",
              ".pdf": "DOCUMENT", ".txt": "DOCUMENT", ".md": "DOCUMENT"}


class MediaLibrary:
    def __init__(self, store: Store):
        self.store = store

    def add_folder(self, project_id: str, folder: Path, owner: str = "user") -> list[MediaAsset]:
        folder = folder.expanduser().resolve()
        if not folder.is_dir():
            raise ValueError("FOLDER_NOT_FOUND")
        project = self.store.get_project(project_id)
        found = []
        for path in sorted(folder.rglob("*")):
            kind = EXTENSIONS.get(path.suffix.lower())
            if not kind or not path.is_file():
                continue
            item = self.register(project_id, path, kind, owner, project.privacy_mode)
            found.append(item)
        self.store.event(project_id, "MEDIA_FOLDER_LINKED", folder=str(folder), count=len(found))
        return found

    def register(self, project_id: str, path: Path, kind: str, owner: str, cloud_policy: str,
                 source: str = "LINKED_FOLDER", display_name: str | None = None) -> MediaAsset:
        path = path.resolve()
        hash_value = sha(path)
        with self.store.connection() as db:
            rows = db.execute("SELECT data FROM media WHERE project_id=?", (project_id,)).fetchall()
        for row in rows:
            old = MediaAsset.model_validate_json(row["data"])
            if old.hash == hash_value and (source != "PROJECT_UPLOAD" or
                    (old.source == "PROJECT_UPLOAD" and Path(old.original_path).is_file())):
                return old
        metadata = self._probe(path) if kind in ("VIDEO", "AUDIO", "IMAGE", "SCREENSHOT") else {}
        asset = MediaAsset(asset_id="MED-" + uuid.uuid4().hex[:12], project_id=project_id,
            type=kind, original_path=str(path), hash=hash_value, created_at=utc_now(),
            display_name=display_name or path.name, source=source, owner=owner, cloud_policy=cloud_policy,
            duration=metadata.get("duration"), resolution=metadata.get("resolution"),
            fps=metadata.get("fps"), codec=metadata.get("codec"))
        thumbnail = self.store.root / "media_cache" / (asset.asset_id + ".jpg")
        thumbnail.parent.mkdir(parents=True, exist_ok=True)
        if kind in ("IMAGE", "VIDEO"):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-frames:v", "1",
                "-vf", "scale=360:-1", str(thumbnail)], capture_output=True, timeout=20)
            if thumbnail.exists():
                asset.thumbnail_path = str(thumbnail)
        if kind == "VIDEO":
            proxy = self.store.root / "media_cache" / (asset.asset_id + "-proxy.mp4")
            try:
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-t", "30",
                    "-vf", "scale=640:-2", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "32",
                    "-an", "-movflags", "+faststart", str(proxy)], capture_output=True, timeout=90)
                if proxy.exists():
                    asset.proxy_path = str(proxy)
            except subprocess.TimeoutExpired:
                pass
        with self.store.connection() as db:
            db.execute("INSERT INTO media VALUES (?,?,?)", (asset.asset_id, project_id, asset.model_dump_json()))
        return asset

    def assets(self, project_id: str) -> list[MediaAsset]:
        with self.store.connection() as db:
            rows = db.execute("SELECT data FROM media WHERE project_id=? ORDER BY rowid DESC", (project_id,)).fetchall()
        values = [MediaAsset.model_validate_json(row["data"]) for row in rows]
        result = []
        for value in values:
            if not Path(value.original_path).exists():
                value = value.model_copy(update={"status": "MISSING"})
            result.append(value)
        return result

    def relink(self, project_id: str, asset_id: str, candidate: Path) -> MediaAsset:
        candidate = candidate.expanduser().resolve()
        with self.store.connection() as db:
            row = db.execute("SELECT data FROM media WHERE id=? AND project_id=?", (asset_id, project_id)).fetchone()
        if not row:
            raise KeyError("MEDIA_NOT_FOUND")
        asset = MediaAsset.model_validate_json(row["data"])
        if sha(candidate) != asset.hash:
            raise ValueError("RELINK_HASH_MISMATCH")
        asset = asset.model_copy(update={"original_path": str(candidate), "status": "RELINKED"})
        with self.store.connection() as db:
            db.execute("UPDATE media SET data=? WHERE id=?", (asset.model_dump_json(), asset_id))
        self.store.event(project_id, "MEDIA_RELINKED", asset_id=asset_id)
        return asset

    def relink_folder(self, project_id: str, folder: Path) -> list[MediaAsset]:
        folder = folder.expanduser().resolve()
        if not folder.is_dir():
            raise ValueError("FOLDER_NOT_FOUND")
        missing = {x.hash: x for x in self.assets(project_id) if x.status == "MISSING"}
        found = []
        for path in folder.rglob("*"):
            if path.is_file() and path.suffix.lower() in EXTENSIONS:
                hash_value = sha(path)
                if hash_value in missing:
                    found.append(self.relink(project_id, missing.pop(hash_value).asset_id, path))
        return found

    def cloud_policy(self, project_id:str,asset_id:str,policy:str):
        if policy not in ('LOCAL_ONLY','CLOUD_ALLOWED','ASK_BEFORE_UPLOAD'):raise ValueError('INVALID_CLOUD_POLICY')
        with self.store.connection() as db:
            row=db.execute('SELECT data FROM media WHERE id=? AND project_id=?',(asset_id,project_id)).fetchone()
            if not row:raise KeyError('MEDIA_NOT_FOUND')
            asset=MediaAsset.model_validate_json(row['data'])
            asset.cloud_policy=policy
            db.execute('UPDATE media SET data=? WHERE id=? AND project_id=?',(asset.model_dump_json(),asset_id,project_id))
        self.store.event(project_id,'MEDIA_CLOUD_POLICY_CHANGED',asset_id=asset_id,policy=policy,actor='HUMAN')
        return asset.model_dump(mode='json')

    @staticmethod
    def _probe(path: Path) -> dict:
        try:
            process = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
                                     capture_output=True, text=True, timeout=15, check=True)
            value = json.loads(process.stdout)
            stream = next((s for s in value.get("streams", []) if s.get("codec_type") == "video"), None)
            fps = None
            if stream and stream.get("r_frame_rate"):
                numerator, denominator = stream["r_frame_rate"].split("/")
                fps = float(numerator) / float(denominator) if float(denominator) else None
            return {"duration": float(value.get("format", {}).get("duration", 0)) or None,
                "resolution": f"{stream['width']}x{stream['height']}" if stream else None,
                "fps": fps, "codec": stream.get("codec_name") if stream else None}
        except Exception:
            return {}
