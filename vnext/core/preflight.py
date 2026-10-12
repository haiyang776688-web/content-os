"""Deterministic render/export preflight."""
from __future__ import annotations

from pathlib import Path

from vnext.contracts import EDT
from vnext.migration.legacy import sha
from vnext.storage.store import Store


def check(store: Store, project_id: str, edt_artifact_id: str, *, require_audio=True) -> dict:
    project = store.get_project(project_id)
    issues = []
    if not project.h2_script_artifact_id:
        issues.append("SCRIPT_NOT_H2_APPROVED")
    if not store.is_usable_input(edt_artifact_id):
        issues.append("STALE_EDT")
    artifact = store.get_artifact(edt_artifact_id)
    if artifact["project_id"] != project_id or artifact["artifact_type"] != "EDT":
        issues.append("INVALID_EDT_ARTIFACT")
        return {"ok": False, "issues": issues}
    try:
        edt = EDT.model_validate({k: v for k, v in artifact["payload"].items() if k in EDT.model_fields})
    except Exception:
        issues.append("INVALID_EDT")
        return {"ok": False, "issues": issues}
    media = {item.asset_id: item for item in __import__("vnext.media.library.service", fromlist=["MediaLibrary"]).MediaLibrary(store).assets(project_id)}
    for clip in edt.clips:
        if clip.asset_id:
            item = media.get(clip.asset_id)
            if not item:
                issues.append(f"MISSING_MEDIA:{clip.asset_id}")
            elif not Path(item.original_path).is_file():
                issues.append(f"OFFLINE_MEDIA:{clip.asset_id}")
            elif sha(Path(item.original_path)) != item.hash:
                issues.append(f"MEDIA_HASH_CHANGED:{clip.asset_id}")
        if clip.track == "VOICE" and not clip.asset_id:
            issues.append(f"MISSING_VOICE:{clip.clip_id}")
    audit = store.latest(project_id, "AUDIT")
    if audit and audit["payload"].get("verdict") == "FAIL" and store.is_usable_input(audit["artifact_id"]):
        issues.append("UNRESOLVED_AUDIT_FAIL")
    if project.phase2_enabled:
        from vnext.phase2.production import mechanical
        from vnext.phase2.hardening.evidence import strict
        if strict(store,project_id):
            from vnext.phase2.hardening.dependencies import Dependencies
            manifest=Dependencies(store).validate(project_id)
            if not manifest['usable']:issues.append('PROJECT_DEPENDENCY_UNRESOLVED')
        report=mechanical(store,project_id,edt_artifact_id,require_voice=strict(store,project_id) and require_audio)
        issues += [x['code'] for x in report['issues'] if x['severity']=='BLOCKER']
    return {"ok": not issues, "issues": issues, "edt_revision": artifact["revision"]}
