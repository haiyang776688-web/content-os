"""Export machine-readable contracts and registries."""
import json
from pathlib import Path

from vnext.contracts import SCHEMAS
from vnext.phase2.contracts import SCHEMAS as PHASE2_SCHEMAS
from vnext.phase2.hardening.contracts import SCHEMAS as HARDENING_SCHEMAS
from vnext.registries.catalog import PROMPTS, ROLE_CONTRACTS, WORKERS


def export(root: Path) -> None:
    contracts = root / "contracts"
    contracts.mkdir(parents=True, exist_ok=True)
    for name, model in {**SCHEMAS, **PHASE2_SCHEMAS, **HARDENING_SCHEMAS}.items():
        (contracts / f"{name}.json").write_text(json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2) + "\n")
    registries = root / "registries"
    for sub in ("models", "capabilities", "prompts", "characters", "styles", "voices", "assets"):
        (registries / sub).mkdir(parents=True, exist_ok=True)
    (registries / "models" / "PROVIDER_REGISTRY.json").write_text(json.dumps(
        [worker.model_dump(mode="json") for worker in WORKERS.values()], ensure_ascii=False, indent=2) + "\n")
    (registries / "capabilities" / "ROLE_REQUIREMENTS.json").write_text(json.dumps(
        [item.model_dump(mode="json") for item in ROLE_CONTRACTS.values()], ensure_ascii=False, indent=2) + "\n")
    (registries / "prompts" / "PROMPT_REGISTRY.json").write_text(json.dumps(
        {key: {"prompt_version": key, "text": value} for key, value in PROMPTS.items()}, ensure_ascii=False, indent=2) + "\n")
