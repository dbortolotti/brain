#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import httpx
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from memory_stack.config import Settings, load_settings
from memory_stack.evals.model_matrix import ModelCandidate
from memory_stack.model_selection import (
    configured_embedding,
    configured_llm,
    is_embedding_ref,
    parse_csv_list,
    parse_model_ref,
)
from memory_stack.evals.provider_client import LiveProviderClient, redact as redact_provider_error


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
    probes = select_probes(
        settings,
        scope=args.scope,
        model_refs=parse_csv_list(args.models),
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
    parser.add_argument(
        "--scope",
        choices=("none", "active"),
        default=os.getenv("BRAIN_MODEL_SMOKE_SCOPE", "active"),
        help="Model set to test. Active checks the configured LLM and embedding models.",
    )
    parser.add_argument("--models", default=None, help="Comma-separated provider:model refs to probe.")
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
        "--timeout",
        type=float,
        default=float(os.getenv("BRAIN_MODEL_SMOKE_TIMEOUT_SECONDS", "30")),
    )
    parser.add_argument("--json-output", default=None)
    return parser


def normalize_args(args: argparse.Namespace) -> argparse.Namespace:
    return args


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def select_probes(
    settings: Settings,
    *,
    scope: str,
    model_refs: list[str] | None = None,
) -> list[Probe]:
    if model_refs:
        return dedupe_probes([probe_from_ref(ref) for ref in model_refs])
    if scope == "active":
        return active_probes(settings)
    raise ValueError(f"unsupported smoke scope: {scope}")


def active_probes(settings: Settings) -> list[Probe]:
    llm = configured_llm(settings)
    embedding = configured_embedding(settings)
    probes = [
        Probe(
            provider=llm.provider,
            model=llm.model,
            kind="llm",
            label="active:llm",
        ),
        Probe(
            provider=embedding.provider,
            model=embedding.model,
            kind="embedding",
            label="active:embedding",
        ),
    ]
    return dedupe_probes(probes)


def probe_from_ref(ref: str) -> Probe:
    parsed = parse_model_ref(ref)
    kind = "embedding" if is_embedding_ref(ref) else "llm"
    return Probe(
        provider=parsed.provider,
        model=parsed.model,
        kind=kind,
        label=ref,
        api_model=parsed.model,
    )


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
