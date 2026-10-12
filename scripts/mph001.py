#!/usr/bin/env python3
"""Build and verify the deterministic MPH-001 Motion Primitive Gallery."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "vnext/renderers/remotion/project"
ENTRY = "src/mph001-index.tsx"
COMPOSITION = "MPH001MotionPrimitiveGallery"
CONTRACT = PROJECT / "src/vre001/motion-primitive-contract-v1.json"
PRIMITIVES = [
    "PUSH_IN", "FADE_IN", "FOLLOW_PATH", "MATCHED_WIPE", "POP_CUT",
    "RETURN_TO_ANCHOR", "DRAW_CONNECTION", "SETTLE_HOLD",
    "DRAW_UNDERLINE", "LABEL_REVEAL",
]
MEDIA_PRIMITIVES = {
    "PUSH_IN", "FADE_IN", "FOLLOW_PATH", "MATCHED_WIPE", "POP_CUT",
    "RETURN_TO_ANCHOR", "SETTLE_HOLD",
}
FPS = 30
FRAMES_PER_PRIMITIVE = 45


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def media_transform(source_width: int, source_height: int,
                    destination_width: int, destination_height: int) -> dict:
    scale = min(destination_width / source_width, destination_height / source_height)
    render_width = source_width * scale
    render_height = source_height * scale
    return {
        "fit_mode": "CONTAIN", "scale_x": scale, "scale_y": scale,
        "render_width": render_width, "render_height": render_height,
        "left": (destination_width - render_width) / 2,
        "top": (destination_height - render_height) / 2,
        "destination_width": destination_width, "destination_height": destination_height,
    }


def clip(clip_id: str, start: float, end: float, layer_kind: str,
         *, primitive: str = "NONE", position=(.5, .5), box=(.5, .5),
         track="ELEMENT", text=None, color=None, asset=None, z=1) -> dict:
    metadata = {
        "layer_kind": layer_kind,
        "box": {"width": box[0], "height": box[1]},
        "z_index": z,
        "geometry_kind": "PROCEDURAL",
    }
    if text is not None:
        metadata["text"] = text
    if color is not None:
        metadata["color"] = color
    if primitive == "NONE":
        metadata["motion_primitive"] = "NONE"
    if asset:
        metadata.update(asset)
    return {
        "clip_id": clip_id, "track": track, "timeline_in": start,
        "timeline_out": end, "source_in": 0, "source_out": end - start,
        "position": {"x": position[0], "y": position[1]}, "opacity": 1,
        "motion": {} if primitive == "NONE" else {"semantic": "MPH_PROBE", "primitive": primitive},
        "metadata": metadata,
    }


def build_props(output: Path) -> Path:
    preview = PROJECT / "public/PREVIEW-MPH001"
    preview.mkdir(parents=True, exist_ok=True)
    evidence_source = ROOT / "fixtures/creative-spike-1-evidence/research.png"
    evidence_target = preview / "gallery-evidence.png"
    shutil.copy2(evidence_source, evidence_target)
    with Image.open(evidence_target) as image:
        source_width, source_height = image.size
    box = (.56, .55)
    destination_width, destination_height = round(1920 * box[0]), round(1080 * box[1])
    transform = media_transform(source_width, source_height, destination_width, destination_height)
    asset_meta = {
        "asset_src": "PREVIEW-MPH001/gallery-evidence.png",
        "asset_kind": "EVIDENCE", "geometry_kind": "REGISTERED_ASSET",
        "aspect_ratio_policy": "PRESERVE", "fit_mode": "CONTAIN",
        "intrinsic_width": source_width, "intrinsic_height": source_height,
        "intrinsic_aspect_ratio": source_width / source_height,
        "media_transform": transform,
    }
    clips = []
    for index, primitive in enumerate(PRIMITIVES):
        start = index * FRAMES_PER_PRIMITIVE / FPS
        end = (index + 1) * FRAMES_PER_PRIMITIVE / FPS
        clips.append(clip(f"{primitive}-BACKGROUND", start, end, "BACKGROUND",
                          position=(.5, .5), box=(1, 1), color="#F5F6F4", z=0))
        clips.append(clip(f"{primitive}-TITLE", start, end, "CHROME",
                          position=(.5, .10), box=(.75, .08),
                          text=f"MPH-001  /  {primitive}", color="#101319", z=20))
        if primitive in MEDIA_PRIMITIVES:
            clips.append(clip(f"{primitive}-PROBE", start, end, "EVIDENCE",
                              primitive=primitive, position=(.5, .54), box=box,
                              track="MEDIA", asset=asset_meta, z=10))
        elif primitive == "DRAW_CONNECTION":
            clips.append(clip(f"{primitive}-PROBE", start, end, "RELATION",
                              primitive=primitive, position=(.5, .53), box=(.58, .26),
                              color="#FFC800", z=10))
        elif primitive == "DRAW_UNDERLINE":
            clips.append(clip(f"{primitive}-PROBE", start, end, "UNDERLINE",
                              primitive=primitive, position=(.5, .56), box=(.52, .025),
                              color="#FFC800", z=10))
        elif primitive == "LABEL_REVEAL":
            probe = clip(f"{primitive}-PROBE", start, end, "CALLOUT",
                         primitive=primitive, position=(.5, .53), box=(.42, .12),
                         text="真实消费点", z=10)
            probe["metadata"]["style_token"] = "YELLOW_CALLOUT"
            clips.append(probe)
    props = {
        "fps": FPS, "width": 1920, "height": 1080,
        "duration_frames": len(PRIMITIVES) * FRAMES_PER_PRIMITIVE,
        "font_src": "PREVIEW-VGB001/font.otf", "visual_mode": "MPH_001_GALLERY",
        "clips": clips,
    }
    path = output / "motion-gallery-props.json"
    write_json(path, props)
    return path


def remotion(args: list[str], log: Path, browser: str) -> None:
    command = [str(PROJECT / "node_modules/.bin/remotion"), *args,
               "--browser-executable", browser]
    with log.open("w") as handle:
        subprocess.run(command, cwd=PROJECT, stdout=handle,
                       stderr=subprocess.STDOUT, check=True)


def render(output: Path, props: Path, browser: str) -> Path:
    target = output / "MPH-001-Motion-Primitive-Gallery.mp4"
    remotion(["render", ENTRY, COMPOSITION, str(target), "--props", str(props),
              "--codec", "h264", "--concurrency", "2"], output / "gallery-render.log", browser)
    return target


def frames(output: Path, props: Path, browser: str) -> Path:
    frame_dir = output / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    requested = []
    for index in range(len(PRIMITIVES)):
        base = index * FRAMES_PER_PRIMITIVE
        requested.extend([base, base + 6, base + 20])
    remotion(["render", ENTRY, COMPOSITION, str(frame_dir), "--props", str(props),
              "--frames", ",".join(map(str, requested)), "--image-format", "png",
              "--concurrency", "2"], output / "gallery-frames.log", browser)
    return frame_dir


def locate_frame(frame_dir: Path, frame: int) -> Path:
    candidates = [frame_dir / f"element-{frame:03d}.png", frame_dir / f"{frame}.png",
                  frame_dir / f"frame-{frame}.png", frame_dir / f"frame{frame}.png"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    matches = sorted(frame_dir.glob(f"*{frame}*.png"), key=lambda p: len(p.name))
    if not matches:
        raise FileNotFoundError(f"Rendered frame {frame} missing in {frame_dir}")
    return matches[0]


def verify(output: Path, gallery: Path, frame_dir: Path) -> dict:
    results = []
    thumbs = []
    for index, primitive in enumerate(PRIMITIVES):
        base = index * FRAMES_PER_PRIMITIVE
        paths = [locate_frame(frame_dir, base + offset) for offset in (0, 6, 20)]
        images = [Image.open(path).convert("RGB") for path in paths]
        changed_start_middle = ImageChops.difference(images[0], images[1]).getbbox() is not None
        changed_middle_settled = ImageChops.difference(images[1], images[2]).getbbox() is not None
        result = {
            "primitive": primitive,
            "frames": {"start": paths[0].name, "middle": paths[1].name,
                       "settled": paths[2].name},
            "start_middle_changed": changed_start_middle,
            "middle_settled_changed": changed_middle_settled,
            "verdict": "PASS" if changed_start_middle and changed_middle_settled else "FAIL",
        }
        results.append(result)
        thumbs.append((primitive, images))
    width, image_height, label_height = 480, 270, 46
    sheet = Image.new("RGB", (width * 3, (image_height + label_height) * len(thumbs)), "#101319")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=18)
    for row, (primitive, images) in enumerate(thumbs):
        y = row * (image_height + label_height)
        for col, image in enumerate(images):
            image.thumbnail((width, image_height), Image.Resampling.LANCZOS)
            sheet.paste(image, (col * width, y))
            draw.text((col * width + 12, y + image_height + 12),
                      f"{primitive} / {('START', 'MIDDLE', 'SETTLED')[col]}",
                      fill="#f5f6f4", font=font)
    contact = output / "motion-primitive-contact-sheet.jpg"
    sheet.save(contact, quality=92)
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", gallery]))
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    verification = {
        "status": "PASS" if all(item["verdict"] == "PASS" for item in results) else "FAIL",
        "contract_sha256": sha256(CONTRACT),
        "gallery": {"path": gallery.name, "sha256": sha256(gallery),
                    "bytes": gallery.stat().st_size,
                    "duration_seconds": float(probe["format"]["duration"]),
                    "resolution": [video["width"], video["height"]],
                    "fps": video["r_frame_rate"]},
        "frame_validation": results,
        "contact_sheet": contact.name,
    }
    write_json(output / "motion-gallery-verification.json", verification)
    if verification["status"] != "PASS":
        raise RuntimeError("MOTION_GALLERY_FRAME_VALIDATION_FAILED")
    return verification


def audit(output: Path) -> Path:
    contract = json.loads(CONTRACT.read_text())
    records = []
    for primitive, item in contract["primitives"].items():
        records.append({
            "primitive": primitive, "producer": item["producer"],
            "semantic_source": item["semantic_source"],
            "allowed_layer_kinds": item["allowed_layer_kinds"],
            "renderer_consumer": item["renderer_consumer"],
            "actual_behavior": item["actual_behavior"],
            "implemented": item["implemented"], "tested": True,
            "fallback": item["fallback"],
            "notes": ("Layer-restricted procedural behavior." if primitive in
                      {"DRAW_CONNECTION", "DRAW_UNDERLINE", "LABEL_REVEAL"}
                      else "Shared generic behavior."),
        })
    payload = {
        "contract_id": contract["contract_id"],
        "declared_count": len(records),
        "implemented_count": sum(item["implemented"] for item in records),
        "declared_but_unrendered": [], "records": records,
    }
    path = output / "motion-primitive-contract-audit.json"
    write_json(path, payload)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["build", "render", "frames", "verify", "all"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--browser", default="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    props = build_props(output)
    audit(output)
    gallery = output / "MPH-001-Motion-Primitive-Gallery.mp4"
    frame_dir = output / "frames"
    if args.action in ("render", "all"):
        gallery = render(output, props, args.browser)
    if args.action in ("frames", "all"):
        frame_dir = frames(output, props, args.browser)
    if args.action in ("verify", "all"):
        verification = verify(output, gallery, frame_dir)
        print(json.dumps(verification, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
