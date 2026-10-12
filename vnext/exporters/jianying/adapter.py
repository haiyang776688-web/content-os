"""One-way EDT export: native editable draft plus explicit transfer sidecars."""
from __future__ import annotations

import json
import uuid
import os
import subprocess
import hashlib
from pathlib import Path

from vnext.contracts import EDT, EDTClip, MediaAsset, utc_now
from vnext.core.preflight import check
from vnext.media.library.service import MediaLibrary
from vnext.storage.store import Store
from vnext.exporters.jianying.native import native_draft


def srt_time(seconds: float) -> str:
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


class JianyingExporter:
    def __init__(self, store: Store):
        self.store = store

    def export_transfer_bundle(self, project_id: str, edt_artifact_id: str) -> dict:
        validation = check(self.store, project_id, edt_artifact_id)
        if not validation["ok"]:
            raise ValueError("PREFLIGHT_FAILED:" + ",".join(validation["issues"]))
        artifact = self.store.get_artifact(edt_artifact_id)
        edt = EDT.model_validate({k: v for k, v in artifact["payload"].items() if k in EDT.model_fields})
        assets = {x.asset_id: x for x in MediaLibrary(self.store).assets(project_id)}
        output = self.store.root / "projects" / project_id / "jianying_exports" / ("EXP-" + uuid.uuid4().hex[:10])
        output.mkdir(parents=True, exist_ok=False)
        mapped = []
        report = []
        subtitle_lines = []
        for clip in edt.clips:
            item = assets.get(clip.asset_id) if clip.asset_id else None
            source = item.original_path if item else None
            category = "EXACT" if item and clip.track in ("MEDIA", "VIDEO", "VOICE") else "APPROXIMATED" if clip.track in ("TEXT", "SUBTITLE") else "UNSUPPORTED"
            reason = "Original file and source range preserved in transfer manifest" if category == "EXACT" else "Editable text timing is represented in sidecar data" if category == "APPROXIMATED" else "No verified native mapping"
            mapped.append({"clip_id": clip.clip_id, "track": clip.track, "original_path": source,
                "source_in": clip.source_in, "source_out": clip.source_out,
                "timeline_in": clip.timeline_in, "timeline_out": clip.timeline_out,
                "text": clip.metadata.get("text"), "transform": {"position": clip.position, "scale": clip.scale, "crop": clip.crop, "opacity": clip.opacity}})
            report.append({"clip_id": clip.clip_id, "classification": category, "reason": reason})
            if clip.track == "SUBTITLE" and clip.metadata.get("text"):
                subtitle_lines += [str(len(subtitle_lines) // 4 + 1),
                    f"{srt_time(clip.timeline_in)} --> {srt_time(clip.timeline_out)}", clip.metadata["text"], ""]
        manifest = {"format": "CONTENT_OS_JIANYING_TRANSFER_BUNDLE_V1", "direction": "CONTENT_OS_TO_JIANYING",
            "native_jianying_draft": False, "edt_artifact_id": edt_artifact_id, "fps": edt.fps,
            "canvas": {"width": edt.width, "height": edt.height}, "clips": mapped}
        (output / "transfer_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        (output / "subtitles.srt").write_text("\n".join(subtitle_lines))
        configured_root = os.environ.get("JIANYING_DRAFT_ROOT")
        font_dependencies=None
        if self.store.get_project(project_id).phase2_enabled:
            from vnext.phase2.fonts import Fonts
            from vnext.phase2.production import mechanical,Production
            Production(self.store).require_storyboard(project_id)
            report_qa=mechanical(self.store,project_id,edt_artifact_id,require_voice=True)
            if report_qa['verdict']=='FAIL': raise ValueError('MECHANICAL_QA_VETO')
            font_dependencies=Fonts(self.store).render_dependencies(project_id)
        native_parent = Path(configured_root).expanduser() if configured_root else output
        if configured_root and not native_parent.is_dir():
            raise ValueError("JIANYING_DRAFT_ROOT_NOT_FOUND")
        native_edt=edt
        canvas_derivation=None
        if edt.schema_version==2:
            # A full-duration main track prevents Jianying's magnetic main track from collapsing gaps.
            # This background is derived from EDT, not a baked preview or replacement of source clips.
            canvas_path=output/'edt-canvas.png'
            subprocess.run(['ffmpeg','-y','-loglevel','error','-f','lavfi','-i',
                f'color=c={edt.canvas_color}:s={edt.width}x{edt.height}','-frames:v','1',str(canvas_path)],check=True,capture_output=True,timeout=15)
            canvas_id='DERIVED-EDT-CANVAS'
            assets[canvas_id]=MediaAsset(asset_id=canvas_id,project_id=project_id,type='IMAGE',
                original_path=str(canvas_path),hash=hashlib.sha256(canvas_path.read_bytes()).hexdigest(),
                created_at=utc_now(),source='EDT_CANVAS_DERIVATION',owner='EXPORT',cloud_policy='LOCAL_ONLY')
            end=max((c.timeline_out for c in edt.clips),default=1)
            native_edt=edt.model_copy(update={'clips':[EDTClip(clip_id='DERIVED-EDT-CANVAS',track='VIDEO',
                asset_id=canvas_id,source_out=end,timeline_out=end),*edt.clips]})
            canvas_derivation={'source':'EDT.canvas_color','color':edt.canvas_color,'path':str(canvas_path),
                'purpose':'Full-duration main background; original foreground source ranges remain on auxiliary tracks'}
        native = native_draft(native_edt, assets, native_parent / ("ContentOS-" + output.name),
                              "Content OS " + project_id + " " + output.name,
                              typography=font_dependencies['profile']['payload'] if font_dependencies else None,
                              fonts=font_dependencies['snapshot']['payload']['fonts'] if font_dependencies else None)
        result = {"path": str(output), "native_draft_path": native["path"],
            "native_jianying_draft": True, "native_project_open_verified": False,
            "mapping": native["mapping"], "transfer_mapping": report,
            "writer_validation": "Local writer POC verified on Jianying 11.5.0-beta5; each export still needs its own visual check",
            "limitation": "Default editable text styling; crop, motion, reveal and lock require review. No reverse import into Content OS."}
        if font_dependencies:
            result['canvas_derivation']=canvas_derivation
            result['font_dependencies']=[{'font_id':x['font_id'],'family':x['family'],'hash':x['preview_hash'],
                'required_path':x['preview_path'],'classification':'FONT_DEPENDENCY_REQUIRED',
                'installation_status':'LOCAL_FILE_AVAILABLE','exact_target_mapping_verified':False}
                for x in font_dependencies['snapshot']['payload']['fonts']]
            result['limitation']='Pinned font paths written; target font/weight/size mapping requires local verification. Crop/motion/reveal/lock remain approximate. No reverse import.'
            result['typography_losses']=[
                {'code':'FONT_NOT_SUPPORTED','classification':'UNSUPPORTED','target_version':'11.5.0-beta5',
                 'description':'Local diagnostic opened with system font instead of the pinned face; explicit repair in the target editor is required'},
                {'code':'SUBTITLE_SHADOW_NOT_MAPPED','classification':'UNSUPPORTED',
                 'description':'Native text shadow fields were ignored in the local diagnostic. White subtitles require manual shadow repair'},
                {'code':'FONT_SIZE_WEIGHT_SPACING_APPROXIMATED','classification':'APPROXIMATED',
                 'description':'Text timing/content are editable; exact weight, size, spacing and baseline are not verified'}]
        export = self.store.create_artifact(project_id, "EXPORT", result, role="EXPORT",
            dependencies=[self.store.dependency(edt_artifact_id)])
        result["artifact_id"] = export.artifact_id
        (output / "JIANYING_EXPORT_REPORT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        return result
