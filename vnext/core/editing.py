"""Script import, H2-bound timeline revision and deterministic edits."""
from __future__ import annotations

import io
import uuid
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from vnext.contracts import EDT, EDTClip
from vnext.storage.store import Store


def import_script_text(filename: str, contents: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in (".txt", ".md"):
        return contents.decode("utf-8-sig")
    if suffix == ".docx":
        return "\n".join(paragraph.text for paragraph in Document(io.BytesIO(contents)).paragraphs)
    if suffix == ".pdf":
        return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(contents)).pages)
    raise ValueError("UNSUPPORTED_SCRIPT_FORMAT")


class Editing:
    def __init__(self, store: Store):
        self.store = store

    def script(self, project_id: str, text: str, source: str = "HUMAN_EDIT", mode: str = "USE_AS_SCRIPT") -> dict:
        if mode not in ("USE_AS_SCRIPT", "POLISH_ONLY", "AI_REWRITE", "USE_AS_REFERENCE"):
            raise ValueError("IMPORT_MODE_REQUIRED")
        if not text.strip():
            raise ValueError("EMPTY_SCRIPT")
        kind = "SCRIPT_REFERENCE" if mode == "USE_AS_REFERENCE" else "SCRIPT"
        if self.store.get_project(project_id).phase2_enabled:
            # Plain text imports cannot silently declare their factual claims unbound.
            # They remain references until the owner submits the segment/Fact-ID contract.
            kind='SCRIPT_REFERENCE'
        artifact = self.store.create_artifact(project_id, kind,
            {"text": text, "source": source, "import_mode": mode,
             **({'requires_claim_binding':True} if self.store.get_project(project_id).phase2_enabled else {})}, role="HUMAN")
        project = self.store.get_project(project_id)
        if kind == "SCRIPT":
            project.h2_script_artifact_id = None
            project.state = "SCRIPT_DRAFT"
            self.store.save_project(project)
        return artifact.model_dump(mode="json")

    def create_timeline(self, project_id: str) -> dict:
        project = self.store.get_project(project_id)
        if not project.h2_script_artifact_id:
            raise ValueError("H2_REQUIRED")
        director = self.store.latest(project_id, "DIRECTOR_PLAN")
        source_ids = [project.h2_script_artifact_id]
        if director and self.store.is_usable_input(director["artifact_id"]):
            source_ids.append(director["artifact_id"])
        edt = EDT(edt_id="EDT-" + uuid.uuid4().hex[:12], project_id=project_id, revision=1,
            source_artifacts=source_ids)
        artifact = self.store.create_artifact(project_id, "EDT", edt.model_dump(mode="json"), role="TIMELINE",
            dependencies=[self.store.dependency(x) for x in source_ids])
        project.timeline_artifact_id = artifact.artifact_id
        self.store.save_project(project)
        return artifact.model_dump(mode="json")

    def edit_timeline(self, project_id: str, operation: str, args: dict) -> dict:
        project = self.store.get_project(project_id)
        if not project.timeline_artifact_id:
            raise ValueError("TIMELINE_MISSING")
        original = self.store.get_artifact(project.timeline_artifact_id)
        if not self.store.is_usable_input(original["artifact_id"]) and operation != "REFRESH_DEPENDENCIES":
            raise ValueError("TIMELINE_STALE")
        if operation == "REFRESH_DEPENDENCIES":
            # Only rebind visual dependencies; never accept an obsolete script or Director IR.
            for dep in original['dependencies']:
                item=self.store.get_artifact(dep['artifact_id'])
                if item['artifact_type'] in ('SCRIPT','DIRECTOR_IR','DIRECTOR_PLAN') and not self.store.is_usable_input(item['artifact_id']):
                    raise ValueError('TIMELINE_STALE')
            if not project.h2_script_artifact_id or project.h2_script_artifact_id not in original['payload']['source_artifacts']:
                raise ValueError('H2_REQUIRED')
        edt = EDT.model_validate({k: v for k, v in original["payload"].items() if k in EDT.model_fields})
        clips = list(edt.clips)
        markers = list(edt.markers)
        index = next((i for i, clip in enumerate(clips) if clip.clip_id == args.get("clip_id")), None)
        if operation == "ADD":
            clip = EDTClip.model_validate({**args, "clip_id": "CLP-" + uuid.uuid4().hex[:10]})
            clips.append(clip)
        elif operation == "UNDO":
            history = self.store.artifacts(project_id, "EDT")
            if len(history) < 2:
                raise ValueError("NOTHING_TO_UNDO")
            prior = next((x for x in reversed(history[:-1]) if x["artifact_id"] != original["artifact_id"]), None)
            if not prior:
                raise ValueError("NOTHING_TO_UNDO")
            edt = EDT.model_validate({k: v for k, v in prior["payload"].items() if k in EDT.model_fields})
            clips = list(edt.clips)
            markers = list(edt.markers)
        elif operation == "REDO":
            if original["payload"].get("last_operation") != "UNDO":
                raise ValueError("NOTHING_TO_REDO")
            before_undo = self.store.get_artifact(original["payload"]["redo_artifact_id"])
            edt = EDT.model_validate({k: v for k, v in before_undo["payload"].items() if k in EDT.model_fields})
            clips = list(edt.clips)
            markers = list(edt.markers)
        elif operation == "MARKER":
            at = float(args["at"])
            if at < 0:
                raise ValueError("INVALID_MARKER")
            markers.append({"at": at, "label": str(args.get("label", ""))})
        elif operation in ("SNAPSHOT", "REFRESH_DEPENDENCIES"):
            pass
        elif index is None:
            raise ValueError("CLIP_NOT_FOUND")
        else:
            clip = clips[index]
            if clip.locked and operation != "LOCK":
                raise ValueError("CLIP_LOCKED")
            if operation == "DELETE":
                clips.pop(index)
            elif operation == "DUPLICATE":
                clips.append(clip.model_copy(update={"clip_id": "CLP-" + uuid.uuid4().hex[:10]}))
            elif operation == "SPLIT":
                at = float(args["at"])
                if not clip.timeline_in < at < clip.timeline_out:
                    raise ValueError("INVALID_SPLIT")
                source_at = clip.source_in + (at - clip.timeline_in) * (
                    clip.source_out - clip.source_in) / (clip.timeline_out - clip.timeline_in)
                clips[index] = clip.model_copy(update={"timeline_out": at, "source_out": source_at})
                clips.insert(index + 1, clip.model_copy(update={"clip_id": "CLP-" + uuid.uuid4().hex[:10],
                    "timeline_in": at, "source_in": source_at}))
            elif operation == "SNAP":
                at = float(args["at"])
                nearby = [float(x["at"]) for x in markers if abs(float(x["at"]) - at) <= 0.2]
                snapped = min(nearby, key=lambda x: abs(x-at)) if nearby else round(at * edt.fps) / edt.fps
                clips[index] = clip.model_copy(update={"timeline_in": snapped,
                    "timeline_out": snapped + clip.timeline_out - clip.timeline_in})
            else:
                fields = {"MOVE": ["timeline_in", "timeline_out"], "TRIM": ["source_in", "source_out", "timeline_in", "timeline_out"],
                    "IN_OUT": ["source_in", "source_out", "timeline_in", "timeline_out"],
                    "REPLACE": ["asset_id"], "LOCK": ["locked"], "HIDE": ["hidden"], "MUTE": ["muted"],
                    "TRANSFORM": ["position", "scale", "crop", "opacity"]}
                if operation not in fields:
                    raise ValueError("UNKNOWN_OPERATION")
                updates = {name: args[name] for name in fields[operation] if name in args}
                clips[index] = EDTClip.model_validate({**clip.model_dump(), **updates})
        updated = EDT.model_validate({**edt.model_dump(), "revision": original["revision"] + 1,
            "clips": [clip.model_dump(mode="json") for clip in clips], "markers": markers})
        payload = updated.model_dump(mode="json")
        if operation == 'REFRESH_DEPENDENCIES':
            profile=self.store.latest(project_id,'TYPOGRAPHY_PROFILE')
            if profile:
                payload['typography_profile_id']=profile['artifact_id']
                payload['typography_profile_hash']=profile['output_hash']
        payload["last_operation"] = operation
        if operation == "UNDO":
            payload["redo_artifact_id"] = original["artifact_id"]
        dependencies = self._dependencies(project_id, project.h2_script_artifact_id, clips)
        payload["source_artifacts"] = [item.artifact_id for item in dependencies]
        if project.phase2_enabled:
            from vnext.phase2.visual_state import visual_revision
            visual_revision(self.store,project_id,payload)
        artifact = self.store.create_artifact(project_id, "EDT", payload, role="TIMELINE",
            dependencies=dependencies)
        project.timeline_artifact_id = artifact.artifact_id
        self.store.save_project(project)
        return artifact.model_dump(mode="json")

    def _dependencies(self, project_id: str, script_id: str, clips: list[EDTClip]):
        ids = [script_id]
        for kind in ("DIRECTOR_PLAN", "DIRECTOR_IR", "MEDIA_SELECTION", "TYPOGRAPHY_PROFILE", "PROJECT_FONT_SNAPSHOT", "VISUAL_CONFIG"):
            latest = self.store.latest(project_id, kind)
            if latest and self.store.is_usable_input(latest["artifact_id"]):
                ids.append(latest["artifact_id"])
        voice_ids = {clip.asset_id for clip in clips if clip.track == "VOICE" and clip.asset_id}
        matched_voice_artifacts = set()
        for artifact in self.store.artifacts(project_id, "VOICE"):
            if artifact["payload"].get("media_asset_id") in voice_ids and self.store.is_usable_input(artifact["artifact_id"]):
                ids.append(artifact["artifact_id"])
                matched_voice_artifacts.add(artifact["artifact_id"])
        if self.store.get_project(project_id).phase2_enabled and matched_voice_artifacts:
            clock = self.store.latest(project_id, "AUDIO_TIMING_MAP")
            if clock and clock["payload"].get("audio_artifact_id") in matched_voice_artifacts and self.store.is_usable_input(clock["artifact_id"]):
                ids.append(clock["artifact_id"])
        return [self.store.dependency(item) for item in dict.fromkeys(ids)]
