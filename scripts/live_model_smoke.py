#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import httpx
import yaml
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from memory_stack.config import Settings, load_settings, normalize_provider_name
from memory_stack.evals.model_matrix import ModelCandidate
from memory_stack.evals.provider_client import LiveProviderClient, redact as redact_provider_error


REGISTRY_PATH = Path(__file__).resolve().parents[1] / "brain_model_registry.yaml"
console = Console()


@dataclass(frozen=True)
class Probe:
    provider: str
    model: str
    kind: str
    label: str
    api_model: str | None = None
    reasoning_effort: str | None = None
    quantizations: tuple[str, ...] = ()
    roles: tuple[str, ...] = ()
    judge_only: bool = False
    skip_reason: str | None = None


@dataclass(frozen=True)
class ProbeResult:
    probe: Probe
    status: str
    detail: str


def main() -> int:
    parser = build_parser()
    args = normalize_args(parser.parse_args())

    if args.scope == "none":
        console.print("[yellow][SKIP][/yellow] live model smoke disabled")
        return 0

    settings = load_settings()
    registry = load_registry(Path(args.registry))
    probes = select_probes(
        settings,
        registry,
        scope=args.scope,
        roles=set(args.role or []),
        include_judge=args.include_judge,
    )
    if not probes:
        console.print("[red][FAIL][/red] no live model probes selected")
        return 1

    with httpx.Client(timeout=args.timeout) as client:
        results = run_probes(
            settings,
            probes,
            client=client,
            skip_missing_keys=args.skip_missing_keys,
        )

    print_results(results)
    if args.json_output:
        write_json_results(Path(args.json_output), results)

    failed = [result for result in results if result.status == "fail"]
    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run low-token live model smoke checks.")
    parser.add_argument("--registry", default=str(REGISTRY_PATH))
    parser.add_argument(
        "--scope",
        choices=("none", "active", "core", "enabled", "all"),
        default=os.getenv("BRAIN_MODEL_SMOKE_SCOPE", "active"),
        help="Model set to test. Use core/enabled/all for registry-wide checks.",
    )
    parser.add_argument(
        "--all-registry",
        action="store_true",
        help=(
            "Shortcut for --scope all --include-judge. Runs one tiny live probe for "
            "every unique model declared in the registry."
        ),
    )
    parser.add_argument("--role", action="append", default=None, help="Limit registry scopes to a role.")
    parser.add_argument(
        "--skip-missing-keys",
        action="store_true",
        default=env_bool("BRAIN_MODEL_SMOKE_SKIP_MISSING_KEYS", False),
        help="Skip probes whose provider credentials are not configured.",
    )
    parser.add_argument(
        "--no-skip-missing-keys",
        dest="skip_missing_keys",
        action="store_false",
    )
    parser.add_argument(
        "--include-judge",
        action="store_true",
        default=env_bool("BRAIN_MODEL_SMOKE_INCLUDE_JUDGE", False),
        help="Include judge_only models in registry scopes.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("BRAIN_MODEL_SMOKE_TIMEOUT_SECONDS", "30")),
    )
    parser.add_argument("--json-output", default=None)
    return parser


def normalize_args(args: argparse.Namespace) -> argparse.Namespace:
    if args.all_registry:
        args.scope = "all"
        args.include_judge = True
    return args


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_registry(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def select_probes(
    settings: Settings,
    registry: dict[str, Any],
    *,
    scope: str,
    roles: set[str],
    include_judge: bool,
) -> list[Probe]:
    if scope == "active":
        return active_probes(settings)
    if scope == "core":
        return core_registry_probes(registry, roles=roles, include_judge=include_judge)
    if scope in {"enabled", "all"}:
        return provider_registry_probes(
            registry,
            enabled_only=scope == "enabled",
            roles=roles,
            include_judge=include_judge,
        )
    raise ValueError(f"unsupported smoke scope: {scope}")


def active_probes(settings: Settings) -> list[Probe]:
    probes = [
        Probe(
            provider=normalize_provider(settings.llm_provider),
            model=strip_provider_prefix(settings.llm_provider, settings.llm_model),
            kind="llm",
            label="active:llm",
        ),
        Probe(
            provider=normalize_provider(settings.embedding_provider),
            model=strip_provider_prefix(settings.embedding_provider, settings.embedding_model),
            kind="embedding",
            label="active:embedding",
        ),
    ]
    if settings.brain_llm_enabled and settings.brain_llm_provider and settings.brain_llm_model:
        probes.append(
            Probe(
                provider=normalize_provider(settings.brain_llm_provider),
                model=strip_provider_prefix(settings.brain_llm_provider, settings.brain_llm_model),
                kind="llm",
                label="active:brain_llm",
            )
        )
    return dedupe_probes(probes)


def core_registry_probes(
    registry: dict[str, Any],
    *,
    roles: set[str],
    include_judge: bool,
) -> list[Probe]:
    index = registry_model_index(registry)
    probes: list[Probe] = []
    for role, refs in (registry.get("core_eval_matrix") or {}).items():
        if roles and role not in roles:
            continue
        for ref in refs or []:
            probe = probe_from_ref(str(ref), index, role=role)
            if probe.skip_reason:
                continue
            if probe.judge_only and not include_judge:
                continue
            probes.append(probe)
    return dedupe_probes(probes)


def provider_registry_probes(
    registry: dict[str, Any],
    *,
    enabled_only: bool,
    roles: set[str],
    include_judge: bool,
) -> list[Probe]:
    probes: list[Probe] = []
    for provider, config in (registry.get("providers") or {}).items():
        provider_type = config.get("type", "llm")
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
                probe_provider = normalize_provider(str(model["provider"]))
                probe_kind = "embedding"
            else:
                probe_provider = normalize_provider(provider)
                probe_kind = str(provider_type)
            probes.append(
                Probe(
                    provider=probe_provider,
                    model=str(model["id"]),
                    kind=probe_kind,
                    label=f"{probe_provider}:{model['id']}",
                    api_model=str(model.get("api_model") or model["id"]),
                    reasoning_effort=str(model.get("reasoning_effort")) if model.get("reasoning_effort") is not None else None,
                    quantizations=tuple(str(value) for value in model.get("quantizations", ())),
                    roles=model_roles,
                    judge_only=bool(model.get("judge_only", False)),
                )
            )
    return dedupe_probes(probes)


def registry_model_index(registry: dict[str, Any]) -> dict[str, Probe]:
    index: dict[str, Probe] = {}
    for provider, config in (registry.get("providers") or {}).items():
        provider_type = config.get("type", "llm")
        for model in config.get("models") or []:
            if provider == "embeddings":
                probe_provider = normalize_provider(str(model["provider"]))
                kind = "embedding"
            else:
                probe_provider = normalize_provider(provider)
                kind = str(provider_type)
            probe = Probe(
                provider=probe_provider,
                model=str(model["id"]),
                kind=kind,
                label=f"{probe_provider}:{model['id']}",
                api_model=str(model.get("api_model") or model["id"]),
                reasoning_effort=str(model.get("reasoning_effort")) if model.get("reasoning_effort") is not None else None,
                quantizations=tuple(str(value) for value in model.get("quantizations", ())),
                roles=tuple(str(role) for role in model.get("roles", ())),
                judge_only=bool(model.get("judge_only", False)),
                skip_reason=model_skip_reason(model),
            )
            index[f"{probe_provider}:{probe.model}"] = probe
            if alias := model.get("alias"):
                index[f"{probe_provider}:{alias}"] = replace(
                    probe,
                    label=f"{probe_provider}:{alias}",
                )
    return index


def probe_from_ref(ref: str, index: dict[str, Probe], *, role: str) -> Probe:
    if ref in index:
        probe = index[ref]
        return replace(probe, roles=tuple(dict.fromkeys((*probe.roles, role))))
    provider, model = ref.split(":", maxsplit=1)
    kind = "embedding" if role == "embeddings" else "llm"
    return Probe(
        provider=normalize_provider(provider),
        model=model,
        kind=kind,
        label=ref,
        api_model=model,
        roles=(role,),
    )


def normalize_provider(provider: str | None) -> str:
    normalized = normalize_provider_name(provider)
    if normalized == "gemini":
        return "google"
    if normalized == "bedrock":
        return "aws-bedrock"
    return normalized or ""


def strip_provider_prefix(provider: str, model: str) -> str:
    normalized = normalize_provider(provider)
    for prefix in (f"{normalized}/", f"{normalized}:"):
        if model.startswith(prefix):
            return model.removeprefix(prefix)
    if normalized == "google":
        for prefix in ("gemini/", "gemini:"):
            if model.startswith(prefix):
                return model.removeprefix(prefix)
    return model


def dedupe_probes(probes: list[Probe]) -> list[Probe]:
    deduped: dict[tuple[str, str, str], Probe] = {}
    for probe in probes:
        key = (probe.kind, probe.provider, probe.model, probe.quantizations)
        if key not in deduped:
            deduped[key] = probe
            continue
        existing = deduped[key]
        deduped[key] = replace(
            existing,
            roles=tuple(dict.fromkeys((*existing.roles, *probe.roles))),
            judge_only=existing.judge_only or probe.judge_only,
            skip_reason=existing.skip_reason or probe.skip_reason,
        )
    return list(deduped.values())


def run_probes(
    settings: Settings,
    probes: list[Probe],
    *,
    client: httpx.Client,
    skip_missing_keys: bool,
) -> list[ProbeResult]:
    results: list[ProbeResult] = []
    provider_client = LiveProviderClient(settings, http_client=client)
    for probe in probes:
        missing = provider_client.missing_credential(candidate_from_probe(probe))
        if missing:
            status = "skip" if skip_missing_keys else "fail"
            results.append(ProbeResult(probe, status, missing))
            continue
        try:
            provider_client.smoke(candidate_from_probe(probe))
        except Exception as exc:
            results.append(ProbeResult(probe, "fail", redact(str(exc), settings)))
        else:
            results.append(ProbeResult(probe, "ok", "live call succeeded"))
    return results


def model_skip_reason(model: dict[str, Any]) -> str | None:
    reason = model.get("skip_reason")
    return str(reason) if reason else None


def candidate_from_probe(probe: Probe) -> ModelCandidate:
    return ModelCandidate(
        provider=probe.provider,
        model=probe.model,
        kind=probe.kind,
        api_model=probe.api_model or probe.model,
        quantizations=probe.quantizations,
        roles=probe.roles,
        judge_only=probe.judge_only,
        reasoning_effort=probe.reasoning_effort,
        skip_reason=probe.skip_reason,
        requested_ref=probe.label,
    )


def missing_credential(settings: Settings, probe: Probe) -> str | None:
    return LiveProviderClient(settings).missing_credential(candidate_from_probe(probe))


def redact(value: str, settings: Settings) -> str:
    return redact_provider_error(value, settings)


def print_results(results: list[ProbeResult]) -> None:
    table = Table(title="Live Model Smoke")
    table.add_column("Status")
    table.add_column("Kind")
    table.add_column("Provider")
    table.add_column("Model")
    table.add_column("Roles")
    table.add_column("Detail")
    for result in results:
        style = {"ok": "green", "skip": "yellow", "fail": "red"}[result.status]
        table.add_row(
            f"[{style}]{result.status.upper()}[/{style}]",
            result.probe.kind,
            result.probe.provider,
            result.probe.model,
            ",".join(result.probe.roles),
            result.detail,
        )
    console.print(table)


def write_json_results(path: Path, results: list[ProbeResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            [
                {
                    "status": result.status,
                    "detail": result.detail,
                    "kind": result.probe.kind,
                    "provider": result.probe.provider,
                    "model": result.probe.model,
                    "label": result.probe.label,
                    "roles": list(result.probe.roles),
                    "judge_only": result.probe.judge_only,
                }
                for result in results
            ],
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
