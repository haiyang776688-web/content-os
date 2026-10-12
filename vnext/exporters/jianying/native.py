"""One-way native draft writer. EDT is never reconstructed from a Jianying edit."""
from __future__ import annotations

import copy
import json
import time
import uuid
from pathlib import Path

from vnext.contracts import EDT, MediaAsset


def uid() -> str:
    return str(uuid.uuid4()).upper()


def us(seconds: float) -> int:
    return round(seconds * 1_000_000)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def native_draft(edt: EDT, assets: dict[str, MediaAsset], destination: Path, name: str, typography: dict | None = None, fonts: list[dict] | None = None) -> dict:
    """Create a new directory only, referencing originals and keeping source time ranges."""
    destination.mkdir(parents=True, exist_ok=False)
    template = json.loads(Path(__file__).with_name("templates.json").read_text())
    draft = copy.deepcopy(template["blank_draft"])
    draft_id, timeline_id, now = uid(), uid(), time.time_ns() // 1000
    draft.update(id=timeline_id, name=name, create_time=now, update_time=now,
                 fps=edt.fps, duration=max((us(c.timeline_out) for c in edt.clips), default=0),
                 canvas_config={"background": None, "height": edt.height, "width": edt.width, "ratio": "original"})
    report = []
    tracks = {}
    for index, clip in enumerate(edt.clips):
        asset = assets.get(clip.asset_id) if clip.asset_id else None
        reasons = []
        kind = None
        if asset and asset.type in ("VIDEO", "IMAGE", "SCREENSHOT", "AUDIO"):
            if not Path(asset.original_path).is_file():
                raise ValueError("ORIGINAL_MEDIA_MISSING:" + asset.asset_id)
            kind = "audio" if asset.type == "AUDIO" else "video"
            material = copy.deepcopy(template["video_material"]) if kind == "video" else {
                "type": "extract_music", "name": "", "music_id": "", "source_platform": 0,
                "check_flag": 1, "copyright_limit_type": "none", "local_material_id": ""}
            material_id = uid()
            material.update(id=material_id, path=str(Path(asset.original_path).resolve()),
                            material_name=Path(asset.original_path).name,
                            name=Path(asset.original_path).name,
                            duration=us(asset.duration or clip.source_out))
            if kind == "video":
                dimensions = (asset.resolution or f"{edt.width}x{edt.height}").split("x")
                resolution = {"width": int(dimensions[0]), "height": int(dimensions[1])}
                material.update(type="photo" if asset.type != "VIDEO" else "video",
                                width=resolution.get("width", edt.width), height=resolution.get("height", edt.height),
                                has_audio=asset.type == "VIDEO")
            draft["materials"]["audios" if kind == "audio" else "videos"].append(material)
        elif clip.track in ("TEXT", "SUBTITLE") and clip.metadata.get("text"):
            kind, material_id = "text", uid()
            text = str(clip.metadata["text"])
            material = {"id": material_id, "type": "text", "content": json.dumps({"text": text, "styles": [{
                "range": [0, len(text)], "size": 8, "fill": {"content": {"solid": {"color": [1, 1, 1], "alpha": 1}}, "type": "solid"},
                "font": {"path": "", "id": ""}}]}, ensure_ascii=False),
                "font_path": "", "font_name": "", "font_size": 8, "text_color": "#FFFFFF",
                "alignment": 1, "bold_width": 0, "italic_degree": 0, "letter_spacing": 0, "line_spacing": .02,
                "background_alpha": 0, "border_alpha": 0, "shadow_alpha": 0, "text_alpha": 1,
                "check_flag": 7, "typesetting": 0}
            draft["materials"]["texts"].append(material)
            if typography and fonts:
                role='SUBTITLE' if clip.track=='SUBTITLE' else clip.metadata.get('typography_role','BODY')
                settings=typography['roles'][role]
                font=next(x for x in fonts if x['font_id']==settings['font_id'])
                material['font_path']=font['preview_path']
                material['font_name']=font['postscript_name'] or font['family']
                content=json.loads(material['content'])
                color='#ffffff' if clip.track=='SUBTITLE' else edt.foreground_color
                rgb=[int(color[i:i+2],16)/255 for i in (1,3,5)]
                content['styles'][0]['fill']['content']['solid']['color']=rgb
                material['text_color']=color
                if clip.track=='SUBTITLE':
                    material.update(shadow_alpha=.65,shadow_color='#000000',shadow_distance=2,
                                    shadow_smoothing=.45,shadow_angle=-45)
                content['styles'][0]['font']={'path':font['preview_path'],'id':''}
                content['styles'][0]['size']=settings['size']/edt.height*100
                material['font_size']=settings['size']/edt.height*100
                material['letter_spacing']=settings['letter_spacing']
                material['content']=json.dumps(content,ensure_ascii=False)
                reasons.append('FONT_DEPENDENCY_REQUIRED: pinned local font path/name written; exact target typography mapping is unverified')
            reasons.append("Text timing/content preserved; typography uses editable default styling")
        else:
            report.append({"clip_id": clip.clip_id, "classification": "UNSUPPORTED", "reason": "No local media or supported text payload"})
            continue
        seg = copy.deepcopy(template["segment"])
        seg.update(id=uid(), material_id=material_id, extra_material_refs=[],
            source_timerange={"start": us(clip.source_in), "duration": us(clip.source_out - clip.source_in)} if kind != "text" else None,
            target_timerange={"start": us(clip.timeline_in), "duration": us(clip.timeline_out - clip.timeline_in)},
            speed=(clip.source_out - clip.source_in) / (clip.timeline_out - clip.timeline_in) if kind != "text" else 1,
            volume=0 if clip.muted else 1, visible=not clip.hidden,
            render_index=index, track_render_index=index)
        seg["clip"] = {"alpha": clip.opacity, "flip": {"horizontal": False, "vertical": False}, "rotation": 0,
            "scale": {"x": clip.scale, "y": clip.scale},
            "transform": {"x": (clip.position.get("x", .5) - .5) * 2, "y": (.5 - clip.position.get("y", .5)) * 2}}
        if clip.crop:
            reasons.append("Crop retained in EDT/transfer sidecar; native crop mapping not verified")
        if clip.motion or clip.reveal:
            reasons.append("Motion/reveal not mapped; static clip retained")
        if clip.locked:
            reasons.append("Editor track lock is not mapped")
        if clip.hidden or clip.muted:
            reasons.append("Visibility/volume flags written; verify in target editor")
        track_key = (clip.track, kind)
        if track_key not in tracks:
            tracks[track_key] = {"attribute": 0, "flag": 0, "id": uid(), "is_default_name": False,
                                  "name": clip.track, "type": kind, "segments": []}
        tracks[track_key]["segments"].append(seg)
        report.append({"clip_id": clip.clip_id, "classification": "APPROXIMATED" if reasons else "EXACT",
                       "reason": "; ".join(reasons) or "Original media/source range, target timing and normalized basic transform mapped"})
    draft["tracks"] = list(tracks.values())
    write_json(destination / "draft_content.json", draft)
    write_json(destination / "Timelines" / timeline_id / "draft_content.json", draft)
    write_json(destination / "Timelines" / "project.json", {"id": draft_id, "version": 0,
        "create_time": now, "update_time": now, "main_timeline_id": timeline_id,
        "config": {"color_space": -1, "hdr_vivid": False, "mixed_track_mode_on": False, "render_index_track_mode_on": False, "use_float_render": False},
        "timelines": [{"id": timeline_id, "name": "Content OS EDT", "create_time": now, "update_time": now, "is_marked_delete": False}]})
    write_json(destination / "timeline_layout.json", {"activeTimeline": timeline_id, "layoutOrientation": 1,
        "dockItems": [{"dockIndex": 0, "ratio": 1, "timelineIds": [timeline_id], "timelineNames": ["Content OS EDT"]}]})
    write_json(destination / "draft_meta_info.json", {"draft_id": draft_id, "draft_name": name,
        "draft_fold_path": str(destination.resolve()), "draft_root_path": str(destination.parent.resolve()),
        "draft_json_file": str((destination / "draft_content.json").resolve()), "draft_cover": "draft_cover.jpg",
        "draft_timeline_materials_size": 0, "draft_materials": [], "draft_removable_storage_device": "",
        "tm_draft_create": now, "tm_draft_modified": now, "tm_duration": draft["duration"],
        "draft_is_invisible": False, "draft_is_ai_shorts": False, "draft_type": "video", "draft_cloud_last_action_download": False})
    return {"path": str(destination), "draft_id": draft_id, "timeline_id": timeline_id,
            "native_jianying_draft": True, "native_project_open_verified": False,
            "mapping": report, "format_support": "Experimental local Jianying JSON draft; target version validation required"}
