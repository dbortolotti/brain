from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


REGISTRY_PATH = Path(__file__).resolve().parents[3] / "brain_model_registry.yaml"
MODEL_TEST_INITIAL_REFS = [
    "openai:gpt-5-nano",
    "openai:gpt-5.4-nano",
    "openai:gpt-5.4-mini",
    "openai:gpt-5.4",
    "google:gemini-2.5-flash-lite",
    "google:gemini-2.5-flash",
    "google:gemini-2.5-pro",
    "aws-bedrock:mistral.ministral-3-14b-instruct",
    "aws-bedrock:nvidia.nemotron-super-3-120b",
    "aws-bedrock:nvidia.nemotron-nano-2",
    "groq:llama-3.1-8b-instant",
    "groq:llama-3.3-70b-versatile",
    "groq:openai/gpt-oss-120b",
    "anthropic:claude-haiku-4-5",
    "anthropic:claude-sonnet-4-6",
    "anthropic:claude-opus-4-7",
    "openai:text-embedding-3-small",
    "openai:text-embedding-3-large",
    "voyage:voyage-4-lite",
    "voyage:voyage-4",
]
MODEL_SETS = {
    "model-test-initial": MODEL_TEST_INITIAL_REFS,
}


@dataclass(frozen=True)
class ModelCandidate:
    provider: str
    model: str
    kind: str
    roles: tuple[str, ...] = ()
    judge_only: bool = False
    price_per_1m: dict[str, float] = field(default_factory=dict)
    skip_reason: str | None = None
    requested_ref: str | None = None

    @property
    def ref(self) -> str:
        return f"{self.provider}:{self.model}"


def load_model_registry(path: str | Path = REGISTRY_PATH) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def registry_model_index(registry: dict[str, Any]) -> dict[str, ModelCandidate]:
    index: dict[str, ModelCandidate] = {}
    for provider, config in (registry.get("providers") or {}).items():
        provider_type = str(config.get("type", "llm"))
        for model in config.get("models") or []:
            if provider == "embeddings":
                model_provider = normalize_provider(str(model["provider"]))
                kind = "embedding"
            else:
                model_provider = normalize_provider(provider)
                kind = provider_type

            price = price_config(model)
            candidate = ModelCandidate(
                provider=model_provider,
                model=str(model["id"]),
                kind=kind,
                roles=tuple(str(role) for role in model.get("roles", ())),
                judge_only=bool(model.get("judge_only", False)),
                price_per_1m=price,
                skip_reason=model_skip_reason(model),
            )
            index[candidate.ref] = candidate
            if alias := model.get("alias"):
                index[f"{model_provider}:{alias}"] = ModelCandidate(
                    provider=candidate.provider,
                    model=candidate.model,
                    kind=candidate.kind,
                    roles=candidate.roles,
                    judge_only=candidate.judge_only,
                    price_per_1m=candidate.price_per_1m,
                    skip_reason=candidate.skip_reason,
                    requested_ref=f"{model_provider}:{alias}",
                )
    return index


def select_model_candidates(
    registry: dict[str, Any],
    *,
    model_refs: list[str] | None,
    roles: set[str],
    scope: str,
    include_judge: bool,
) -> list[ModelCandidate]:
    if model_refs:
        index = registry_model_index(registry)
        return dedupe_candidates(
            [
                candidate_from_ref(ref, index, roles=set(), include_judge=include_judge)
                for ref in model_refs
            ]
        )

    if scope == "core":
        candidates = core_candidates(registry, roles=roles, include_judge=include_judge)
    elif scope in {"enabled", "all"}:
        candidates = provider_candidates(
            registry,
            enabled_only=scope == "enabled",
            roles=roles,
            include_judge=include_judge,
        )
    else:
        raise ValueError(f"unsupported model scope: {scope}")
    return dedupe_candidates(candidates)


def core_candidates(
    registry: dict[str, Any],
    *,
    roles: set[str],
    include_judge: bool,
) -> list[ModelCandidate]:
    index = registry_model_index(registry)
    candidates: list[ModelCandidate] = []
    for role, refs in (registry.get("core_eval_matrix") or {}).items():
        if roles and role not in roles:
            continue
        for ref in refs or []:
            candidate = candidate_from_ref(str(ref), index, roles={role}, include_judge=True)
            if candidate.skip_reason:
                continue
            if candidate.judge_only and not include_judge:
                continue
            candidates.append(candidate)
    return candidates


def provider_candidates(
    registry: dict[str, Any],
    *,
    enabled_only: bool,
    roles: set[str],
    include_judge: bool,
) -> list[ModelCandidate]:
    candidates: list[ModelCandidate] = []
    for provider, config in (registry.get("providers") or {}).items():
        provider_type = str(config.get("type", "llm"))
        for model in config.get("models") or []:
            if model_skip_reason(model):
                continue
            if enabled_only and not model.get("enabled_by_default", False):
                continue
            if model.get("judge_only", False) and not include_judge:
                continue
            model_roles = tuple(str(role) for role in model.get("roles", ()))
            if roles and not roles.intersection(model_roles):
                continue
            if provider == "embeddings":
                model_provider = normalize_provider(str(model["provider"]))
                kind = "embedding"
            else:
                model_provider = normalize_provider(provider)
                kind = provider_type
            candidates.append(
                ModelCandidate(
                    provider=model_provider,
                    model=str(model["id"]),
                    kind=kind,
                    roles=model_roles,
                    judge_only=bool(model.get("judge_only", False)),
                    price_per_1m=price_config(model),
                )
            )
    return candidates


def candidate_from_ref(
    ref: str,
    index: dict[str, ModelCandidate],
    *,
    roles: set[str],
    include_judge: bool,
) -> ModelCandidate:
    if ref in index:
        candidate = index[ref]
        if candidate.judge_only and not include_judge:
            raise ValueError(f"{ref} is judge_only; pass --include-judge to include it")
        return ModelCandidate(
            provider=candidate.provider,
            model=candidate.model,
            kind=candidate.kind,
            roles=tuple(dict.fromkeys((*candidate.roles, *roles))),
            judge_only=candidate.judge_only,
            price_per_1m=candidate.price_per_1m,
            skip_reason=candidate.skip_reason,
            requested_ref=ref,
        )

    provider, model = parse_model_ref(ref)
    kind = "embedding" if roles == {"embeddings"} else "llm"
    return ModelCandidate(
        provider=normalize_provider(provider),
        model=model,
        kind=kind,
        roles=tuple(sorted(roles)),
        requested_ref=ref,
    )


def dedupe_candidates(candidates: list[ModelCandidate]) -> list[ModelCandidate]:
    deduped: dict[tuple[str, str, str], ModelCandidate] = {}
    for candidate in candidates:
        key = (candidate.kind, candidate.provider, candidate.model)
        if key not in deduped:
            deduped[key] = candidate
            continue
        existing = deduped[key]
        deduped[key] = ModelCandidate(
            provider=existing.provider,
            model=existing.model,
            kind=existing.kind,
            roles=tuple(dict.fromkeys((*existing.roles, *candidate.roles))),
            judge_only=existing.judge_only or candidate.judge_only,
            price_per_1m=existing.price_per_1m or candidate.price_per_1m,
            skip_reason=existing.skip_reason or candidate.skip_reason,
            requested_ref=existing.requested_ref or candidate.requested_ref,
        )
    return list(deduped.values())


def parse_model_ref(ref: str) -> tuple[str, str]:
    if ":" not in ref:
        raise ValueError(f"model ref must be provider:model, got {ref!r}")
    provider, model = ref.split(":", maxsplit=1)
    if not provider or not model:
        raise ValueError(f"model ref must be provider:model, got {ref!r}")
    return provider, model


def normalize_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized == "gemini":
        return "google"
    if normalized == "bedrock":
        return "aws-bedrock"
    return normalized


def price_config(model: dict[str, Any]) -> dict[str, float]:
    raw = (
        model.get("price_per_1m")
        or model.get("price_per_1m_us_regions")
        or {}
    )
    return {
        str(key): float(value)
        for key, value in raw.items()
        if isinstance(value, int | float)
    }


def model_skip_reason(model: dict[str, Any]) -> str | None:
    reason = model.get("skip_reason")
    return str(reason) if reason else None
