"""Copy verified Legacy assets into a new pack; never writes to Legacy."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from vnext.contracts import CharacterPack, ElementPack, StylePack, VoiceProfile


def sha(path: Path) -> str:
    hash_value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hash_value.update(chunk)
    return hash_value.hexdigest()


def migrate(legacy: Path, destination: Path) -> dict:
    legacy = Path(legacy).resolve()
    destination = Path(destination).resolve()
    if legacy == destination or legacy in destination.parents:
        raise ValueError("Destination must be outside Legacy")
    asset_root = legacy / "data/assets/ip/xiao-y"
    revision = asset_root / "registry/revisions/AR-0004"
    action_manifest = json.loads((revision / "ACTION_MANIFEST.json").read_text())
    element_manifest = json.loads((revision / "ELEMENT_MANIFEST.json").read_text())
    actions, elements = action_manifest["actions"], element_manifest["elements"]
    if len(actions) != 48 or len(elements) != 33:
        raise ValueError("AR-0004 count mismatch")
    for entry in actions + elements:
        source = asset_root / entry["path"]
        if sha(source) != entry["sha256"]:
            raise ValueError("Legacy SHA mismatch: " + entry["path"])
    # Verify the entire source set before copying anything.
    copied = []
    for entry in actions + elements:
        source = asset_root / entry["path"]
        target = destination / "assets" / entry["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if sha(target) != entry["sha256"]:
            raise ValueError("Destination SHA mismatch: " + entry["path"])
        copied.append({"id": entry.get("asset_id", entry.get("element_id")), "path": str(target.relative_to(destination)), "sha256": entry["sha256"]})
    master_src = asset_root / "character_master/XIAO-Y_V1.png"
    master_dst = destination / "assets/character_master/XIAO-Y_V1.png"
    master_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(master_src, master_dst)
    character = CharacterPack(character_id="XIAO-Y_V1", version="AR-0004",
        master={"path": str(master_dst.relative_to(destination)), "sha256": sha(master_dst)},
        actions=actions, action_semantics={entry["id"]: entry.get("semantic_intents", []) for entry in actions},
        constraints={"no_mirroring": True},
        calibration=json.loads((revision / "PRODUCTION_ASSET_REGISTRY.json").read_text()).get("calibration", {}),
        default_style="XIAO-Y_STYLE_V1", recommended_voice_profiles=["YU_LOCAL_V1"], assets=copied[:48])
    element_pack = ElementPack(element_pack_id="XIAO-Y_ELEMENTS_V1", version="AR-0004", elements=elements)
    xvt = json.loads((legacy / "production/visual_system/XVT-0001.json").read_text())
    style = StylePack(style_id="XIAO-Y_STYLE_V1", version="XVT-0001",
        colors={key: value for key, value in xvt.get("typography", {}).items() if str(value).startswith("#")},
        typography=xvt.get("typography", {}), subtitle_style={"safe_zone": xvt.get("canvas", {}).get("caption_safe_zone_px", {})},
        motion_language={"source": "XVT-0001"}, composition_rules={"canvas": xvt.get("canvas", {})},
        template_pack="XIAO-Y_TEMPLATES_V1")
    voice_config = json.loads((legacy / "production/voice/VOICE-0001.json").read_text())
    voice = VoiceProfile(voice_profile_id="YU_LOCAL_V1", display_name="Legacy local reference voice",
        provider="LOCAL", execution_mode="LOCAL", provider_voice_id=voice_config.get("voice_id", "legacy"),
        voice_type="REFERENCE_BASED", language="zh-CN", owner="user", consent_status="PENDING",
        usage_scope="local evaluation", version=1, status="UNAVAILABLE")
    registry = destination / "registries"
    for group, name, value in [
        ("characters", "XIAO-Y_V1.json", character.model_dump(mode="json")),
        ("styles", "XIAO-Y_STYLE_V1.json", style.model_dump(mode="json")),
        ("assets", "XIAO-Y_ELEMENTS_V1.json", element_pack.model_dump(mode="json")),
        ("voices", "YU_LOCAL_V1.json", voice.model_dump(mode="json")),
        ("styles", "XIAO-Y_TEMPLATES_V1.json", {"template_pack_id": "XIAO-Y_TEMPLATES_V1", "source": "XVT-0001", "templates": xvt.get("templates", [])}),
    ]:
        path = registry / group / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    reference_dir = destination / "migration/reference"
    reference_dir.mkdir(parents=True, exist_ok=True)
    for relative in ["production/visual/VM-0003.json", "production/visual_system/XVT-0001.json",
                     "production/visual_system/VBP-0001.json", "production/av_refinement/XVT-0002_REVEAL_METADATA.json"]:
        source = legacy / relative
        if source.exists():
            shutil.copy2(source, reference_dir / source.name)
    report = {"legacy_source": str(legacy), "registry_revision": "AR-0004", "actions_verified": 48,
              "elements_verified": 33, "master_sha256": sha(master_src), "bytes_unchanged": True,
              "copied": copied, "voice_status": "UNAVAILABLE", "remotion_code_migrated": False}
    (destination / "migration").mkdir(parents=True, exist_ok=True)
    (destination / "migration/LEGACY_MIGRATION_RESULT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Copy and verify Legacy XIAO-Y AR-0004 assets")
    parser.add_argument("legacy_root", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(migrate(args.legacy_root, args.destination), ensure_ascii=False, indent=2))
