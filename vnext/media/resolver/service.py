"""Deterministic local media candidates; external discovery is a future tool adapter."""
from __future__ import annotations

from vnext.contracts import MediaSelection
from vnext.media.library.service import MediaLibrary
from vnext.storage.store import Store


class MediaResolver:
    def __init__(self, store: Store):
        self.store = store

    def select(self, project_id: str, media_need: str, mode: str = "SUGGEST",
               selected_asset_id: str | None = None) -> dict:
        previous=self.store.latest(project_id,'MEDIA_SELECTION')
        if previous and previous['payload']['status']=='LOCKED' and mode in ('AUTO','SUGGEST'):
            raise PermissionError('HUMAN_MEDIA_LOCK_REQUIRES_EXPLICIT_MANUAL_CHANGE')
        assets = [x for x in MediaLibrary(self.store).assets(project_id) if x.status in ("ONLINE", "RELINKED")]
        words = [x.lower() for x in media_need.split() if len(x) > 1]
        ranked = sorted(assets, key=lambda x: sum(word in x.original_path.lower() for word in words), reverse=True)
        candidates = [x.asset_id for x in ranked]
        if selected_asset_id and selected_asset_id not in candidates:
            raise ValueError("SELECTED_ASSET_NOT_AVAILABLE")
        if mode == "AUTO" and not selected_asset_id and candidates:
            selected_asset_id = candidates[0]
        if mode == "LOCKED" and not selected_asset_id:
            raise ValueError("LOCKED_REQUIRES_SELECTION")
        status = "LOCKED" if mode == "LOCKED" else "SELECTED" if selected_asset_id else "SUGGESTED" if candidates else "ASSET_GAP"
        selection = MediaSelection(media_need=media_need, mode=mode, candidate_asset_ids=candidates,
            selected_asset_id=selected_asset_id, status=status,
            rationale="Local asset path match only; review the candidates before production.")
        director = self.store.latest(project_id, "DIRECTOR_IR" if self.store.get_project(project_id).phase2_enabled else "DIRECTOR_PLAN")
        artifact = self.store.create_artifact(project_id, "MEDIA_SELECTION", selection.model_dump(mode="json"),
            role="HUMAN" if mode in ("MANUAL", "LOCKED") else "MEDIA_RESOLVER",
            dependencies=[self.store.dependency(director["artifact_id"])] if director else [])
        return artifact.model_dump(mode="json")
