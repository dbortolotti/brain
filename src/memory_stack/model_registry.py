from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


REGISTRY_PATH = Path(__file__).resolve().parents[2] / "brain_model_registry.yaml"


def load_model_registry(path: str | Path = REGISTRY_PATH) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def capability_definitions(registry: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    data = registry or load_model_registry()
    capabilities = data.get("fine_grained_capabilities") or {}
    return {
        str(name): {
            "required_model_roles": list(config.get("required_model_roles") or []),
            "deterministic_roles": list(config.get("deterministic_roles") or []),
            "optional_if_not_tested": bool(config.get("optional_if_not_tested", False)),
            "required": bool(config.get("required", True)),
        }
        for name, config in capabilities.items()
    }


def mandatory_capabilities(registry: dict[str, Any] | None = None) -> set[str]:
    return {
        name
        for name, config in capability_definitions(registry).items()
        if bool(config.get("required", True)) and not bool(config.get("optional_if_not_tested", False))
    }


def deployment_decisions(registry: dict[str, Any] | None = None) -> dict[str, Any]:
    data = registry or load_model_registry()
    return data.get("fine_grained_deployment_decisions") or {}


def eligible_role_models(registry: dict[str, Any] | None = None) -> dict[str, str]:
    decisions = deployment_decisions(registry)
    return {
        str(role): str(config["model"])
        for role, config in (decisions.get("use") or {}).items()
        if isinstance(config, dict) and config.get("model")
    }


def role_model(role: str, registry: dict[str, Any] | None = None) -> str | None:
    return eligible_role_models(registry).get(role)


def role_enabled(role: str, registry: dict[str, Any] | None = None) -> bool:
    return role_model(role, registry) is not None


def deterministic_roles(capability: str, registry: dict[str, Any] | None = None) -> list[str]:
    capabilities = capability_definitions(registry)
    return list(capabilities.get(capability, {}).get("deterministic_roles", []))


def disabled_roles(registry: dict[str, Any] | None = None) -> set[str]:
    decisions = deployment_decisions(registry)
    return {str(role) for role in (decisions.get("do_not_use_yet") or {})}
