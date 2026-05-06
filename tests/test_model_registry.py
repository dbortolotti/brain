from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


REGISTRY_PATH = Path(__file__).resolve().parents[1] / "brain_model_registry.yaml"


def test_brain_model_registry_loads() -> None:
    registry = load_registry()

    assert registry["version"] == 1
    assert registry["roles"]
    assert registry["providers"]
    assert registry["core_eval_matrix"]


def test_brain_model_registry_references_known_models() -> None:
    registry = load_registry()
    known_models = model_refs(registry)
    skipped_models = skipped_model_refs(registry)

    for role, config in registry["roles"].items():
        for model in config.get("preferred_models", []):
            assert model in known_models, f"{role} references unknown model {model}"
            assert model not in skipped_models, f"{role} references skipped model {model}"

    for role, models in registry["core_eval_matrix"].items():
        assert role in registry["roles"], f"core matrix references unknown role {role}"
        for model in models:
            assert model in known_models, f"{role} core matrix references unknown model {model}"
            assert model not in skipped_models, f"{role} core matrix references skipped model {model}"


def load_registry() -> dict[str, Any]:
    with REGISTRY_PATH.open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def model_refs(registry: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    for provider, config in registry["providers"].items():
        for model in config.get("models", []):
            if provider == "embeddings":
                model_provider = model["provider"]
            else:
                model_provider = provider

            refs.add(f"{model_provider}:{model['id']}")
            if alias := model.get("alias"):
                refs.add(f"{model_provider}:{alias}")
    return refs


def skipped_model_refs(registry: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    for provider, config in registry["providers"].items():
        for model in config.get("models", []):
            if not model.get("skip_reason"):
                continue
            if provider == "embeddings":
                model_provider = model["provider"]
            else:
                model_provider = provider

            refs.add(f"{model_provider}:{model['id']}")
            if alias := model.get("alias"):
                refs.add(f"{model_provider}:{alias}")
    return refs
