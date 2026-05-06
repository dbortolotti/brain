from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from memory_stack.config import Settings
from memory_stack.evals.model_fixtures import (
    BASE_OUTPUT_SCHEMA,
    ModelEvalFixture,
    fixture_prompt,
    select_fixtures,
)
from memory_stack.evals.model_matrix import (
    ModelCandidate,
    load_model_registry,
    select_model_candidates,
)
from memory_stack.evals.provider_client import LiveProviderClient, ModelCallResult
from memory_stack.evals.scoring import (
    aggregate_model_role_records,
    paired_model_comparisons,
    score_model_output,
)


class EvalModelClient(Protocol):
    def complete_json(
        self,
        candidate: ModelCandidate,
        *,
        prompt: str,
        schema: dict,
    ) -> ModelCallResult:
        ...

    def embed(self, candidate: ModelCandidate, *, text: str) -> ModelCallResult:
        ...


@dataclass(frozen=True)
class ModelEvalRunConfig:
    registry_path: Path
    fixture_set: str
    roles: set[str]
    model_refs: list[str] | None
    scope: str
    include_judge: bool
    repeat_runs: int
    bootstrap_samples: int
    output_path: Path
    report_md_path: Path | None = None
    raw_output_dir: Path | None = None


def run_model_evals(
    settings: Settings,
    config: ModelEvalRunConfig,
    *,
    client: EvalModelClient | None = None,
) -> dict:
    registry = load_model_registry(config.registry_path)
    candidates = select_model_candidates(
        registry,
        model_refs=config.model_refs,
        roles=config.roles,
        scope=config.scope,
        include_judge=config.include_judge,
    )
    fixtures = select_fixtures(fixture_set=config.fixture_set, roles=config.roles)
    if not candidates:
        raise ValueError("no model candidates selected")
    if not fixtures:
        raise ValueError("no fixtures selected")

    run_id = f"eval_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
    active_client = client or LiveProviderClient(settings)
    raw_output_dir = config.raw_output_dir or config.output_path.parent / "raw" / run_id
    records: list[dict] = []
    for candidate in candidates:
        candidate_roles = roles_for_candidate(candidate, config.roles, fixtures)
        for role in candidate_roles:
            role_fixtures = [fixture for fixture in fixtures if fixture.role == role]
            if candidate.kind == "embedding":
                role_fixtures = embedding_fixtures(fixtures)
            for fixture in role_fixtures:
                for repeat_idx in range(config.repeat_runs):
                    record = run_one_fixture(
                        active_client,
                        candidate=candidate,
                        fixture=fixture,
                        run_id=run_id,
                        repeat_idx=repeat_idx,
                        raw_output_dir=raw_output_dir,
                    )
                    records.append(record)

    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(config.output_path, records)
    summaries = aggregate_model_role_records(
        records,
        bootstrap_samples=config.bootstrap_samples,
    )
    comparisons = paired_model_comparisons(
        records,
        bootstrap_samples=config.bootstrap_samples,
    )
    result = {
        "run_id": run_id,
        "fixture_set": config.fixture_set,
        "models": [candidate.ref for candidate in candidates],
        "roles": sorted(config.roles) if config.roles else "candidate_roles",
        "record_count": len(records),
        "output_path": str(config.output_path),
        "report_md_path": str(config.report_md_path) if config.report_md_path else None,
        "summaries": summaries,
        "pairwise_comparisons": comparisons,
    }
    if config.report_md_path:
        config.report_md_path.parent.mkdir(parents=True, exist_ok=True)
        config.report_md_path.write_text(render_markdown_report(result, records), encoding="utf-8")
    return result


def run_one_fixture(
    client: EvalModelClient,
    *,
    candidate: ModelCandidate,
    fixture: ModelEvalFixture,
    run_id: str,
    repeat_idx: int,
    raw_output_dir: Path,
) -> dict:
    if candidate.kind == "embedding":
        call = client.embed(candidate, text=fixture.input_text)
    else:
        call = client.complete_json(
            candidate,
            prompt=fixture_prompt(fixture),
            schema=BASE_OUTPUT_SCHEMA,
        )
    scores, zero_tolerance, notes = score_model_output(
        fixture,
        call.payload,
        status=call.status,
    )
    raw_output_path = write_raw_output(
        raw_output_dir,
        run_id=run_id,
        candidate=candidate,
        fixture=fixture,
        repeat_idx=repeat_idx,
        call=call,
    )
    return {
        "run_id": run_id,
        "model": candidate.ref,
        "provider": candidate.provider,
        "role": fixture.role if candidate.kind != "embedding" else "embeddings",
        "kind": candidate.kind,
        "fixture_set_version": "brain-model-test-v2",
        "policy_version": "memory-policy-v1",
        "fixture_id": fixture.id,
        "scenario_group": fixture.scenario_group,
        "repeat_idx": repeat_idx,
        "status": call.status,
        "error": call.error,
        "input_tokens": call.input_tokens,
        "output_tokens": call.output_tokens,
        "estimated_cost_usd": call.estimated_cost_usd,
        "latency_ms": call.latency_ms,
        "schema_valid": call.status == "ok" and call.payload is not None,
        "zero_tolerance_failure": zero_tolerance,
        "scores": scores,
        "notes": notes,
        "raw_output_path": str(raw_output_path),
    }


def roles_for_candidate(
    candidate: ModelCandidate,
    requested_roles: set[str],
    fixtures: list[ModelEvalFixture],
) -> list[str]:
    fixture_roles = {fixture.role for fixture in fixtures}
    if candidate.kind == "embedding":
        return ["embeddings"]
    roles = set(candidate.roles)
    if requested_roles:
        roles &= requested_roles
    roles &= fixture_roles
    if requested_roles and not roles:
        roles = requested_roles & fixture_roles
    if not roles:
        roles = fixture_roles
    return sorted(roles)


def embedding_fixtures(fixtures: list[ModelEvalFixture]) -> list[ModelEvalFixture]:
    for fixture in fixtures:
        if fixture.role == "memory_compiler":
            return [fixture]
    return fixtures[:1]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def write_raw_output(
    raw_output_dir: Path,
    *,
    run_id: str,
    candidate: ModelCandidate,
    fixture: ModelEvalFixture,
    repeat_idx: int,
    call: ModelCallResult,
) -> Path:
    raw_output_dir.mkdir(parents=True, exist_ok=True)
    safe_model = candidate.ref.replace(":", "_").replace("/", "_")
    path = raw_output_dir / f"{safe_model}__{fixture.id}__{repeat_idx}.json"
    path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "model": candidate.ref,
                "fixture_id": fixture.id,
                "status": call.status,
                "error": call.error,
                "payload": call.payload,
                "raw_text": call.raw_text,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def render_markdown_report(result: dict, records: list[dict]) -> str:
    lines = [
        "# Brain Model Eval Report",
        "",
        f"- Run ID: `{result['run_id']}`",
        f"- Fixture set: `{result['fixture_set']}`",
        f"- JSONL output: `{result['output_path']}`",
        f"- Records: `{result['record_count']}`",
        "",
        "## Summary",
        "",
        "| Model | Role | Variants | Overall | CI 95% | Zero tolerance | Cost USD | p95 ms | Eligible | Rejection |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for summary in result["summaries"]:
        overall = summary["overall_score"]
        zero = summary["zero_tolerance"]
        cost = summary["cost"]
        latency = summary["latency_ms"]
        lines.append(
            "| "
            f"`{summary['model']}` | `{summary['role']}` | "
            f"{summary['n_fixture_variants']} | "
            f"{overall['mean']:.3f} | "
            f"{overall['ci95_low']:.3f}-{overall['ci95_high']:.3f} | "
            f"{zero['count']} | "
            f"{cost['total_usd']:.6f} | "
            f"{latency['p95']} | "
            f"{summary['eligible_for_role']} | "
            f"{summary['rejection_reason'] or ''} |"
        )
    lines.extend(
        [
            "",
            "## Pairwise Comparisons",
            "",
            "| Role | Model A | Model B | Paired fixtures | Score diff A-B | 95% CI | Cheaper | Recommendation |",
            "|---|---|---|---:|---:|---:|---|---|",
        ]
    )
    comparisons = result.get("pairwise_comparisons") or []
    if comparisons:
        for comparison in comparisons:
            diff = comparison["score_diff_a_minus_b"]
            lines.append(
                "| "
                f"`{comparison['role']}` | `{comparison['model_a']}` | `{comparison['model_b']}` | "
                f"{comparison['n_paired_fixtures']} | "
                f"{diff['mean']:.3f} | "
                f"{diff['ci95_low']:.3f}-{diff['ci95_high']:.3f} | "
                f"`{comparison['cheaper']}` | {comparison['recommendation']} |"
            )
    else:
        lines.append("| | | | | | | | No paired model comparisons. |")
    lines.extend(
        [
            "",
            "## Failures",
            "",
            "| Model | Role | Fixture | Error |",
            "|---|---|---|---|",
        ]
    )
    failures = [record for record in records if record["status"] != "ok"]
    if failures:
        for record in failures:
            error = " ".join(str(record.get("error") or "").split())
            if len(error) > 160:
                error = error[:157] + "..."
            lines.append(
                f"| `{record['model']}` | `{record['role']}` | "
                f"`{record['fixture_id']}` | {error} |"
            )
    else:
        lines.append("| | | | No provider/schema failures. |")
    lines.extend(
        [
            "",
            "## Zero-Tolerance Failures",
            "",
            "| Model | Role | Fixture | Notes |",
            "|---|---|---|---|",
        ]
    )
    zero_rows = [record for record in records if record.get("zero_tolerance_failure")]
    if zero_rows:
        for record in zero_rows:
            lines.append(
                f"| `{record['model']}` | `{record['role']}` | "
                f"`{record['fixture_id']}` | {', '.join(record.get('notes') or [])} |"
            )
    else:
        lines.append("| | | | No zero-tolerance failures. |")
    return "\n".join(lines) + "\n"
