from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from threading import Lock
from typing import Any, Protocol

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
    EvalRecord,
    FailureClass,
    PairwiseComparison,
    Summary,
    aggregate_model_role_records,
    classify_failure_class,
    is_stack_deployable,
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
    model_set: str | None = None
    report_md_path: Path | None = None
    raw_output_dir: Path | None = None
    max_workers: int = 1
    retry_attempts: int = 2
    retry_backoff_seconds: float = 1.0


def run_model_evals(
    settings: Settings,
    config: ModelEvalRunConfig,
    *,
    client: EvalModelClient | None = None,
    progress_callback: Callable[[int, int, dict], None] | None = None,
) -> dict:
    registry = load_model_registry(config.registry_path)
    model_refs = config.model_refs
    if config.model_set:
        from memory_stack.evals.model_matrix import MODEL_SETS

        if config.model_set not in MODEL_SETS:
            raise ValueError(f"unsupported model set: {config.model_set}")
        if model_refs:
            raise ValueError("pass either --models or --model-set, not both")
        model_refs = MODEL_SETS[config.model_set]
    candidates = select_model_candidates(
        registry,
        model_refs=model_refs,
        roles=config.roles,
        scope=config.scope,
        include_judge=config.include_judge or bool(config.model_set),
    )
    fixtures = select_fixtures(fixture_set=config.fixture_set, roles=config.roles)
    if not candidates:
        raise ValueError("no model candidates selected")
    if not fixtures:
        raise ValueError("no fixtures selected")

    run_id = f"eval_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
    active_client = client or LiveProviderClient(
        settings,
        retry_attempts=config.retry_attempts,
        retry_backoff_seconds=config.retry_backoff_seconds,
    )
    raw_output_dir = config.raw_output_dir or config.output_path.parent / "raw" / run_id
    parsed_output_dir = config.output_path.parent / "parsed" / run_id

    records: list[dict[str, Any]] = []
    candidate_task_groups = [
        (candidate, candidate_tasks(candidate, config.roles, fixtures, config.repeat_runs))
        for candidate in candidates
    ]
    total_records = sum(len(tasks) for _candidate, tasks in candidate_task_groups)
    completed = 0
    progress_lock = Lock()

    def report_progress(record: dict[str, Any]) -> None:
        nonlocal completed
        with progress_lock:
            records.append(record)
            completed += 1
            done = completed
        if progress_callback:
            progress_callback(done, total_records, record)

    work_items = [(candidate, tasks) for candidate, tasks in candidate_task_groups if tasks]
    if config.max_workers <= 1 or len(work_items) <= 1:
        for candidate, tasks in work_items:
            for record in evaluate_candidate_tasks(
                active_client,
                candidate=candidate,
                tasks=tasks,
                run_id=run_id,
                raw_output_dir=raw_output_dir,
                parsed_output_dir=parsed_output_dir,
            ):
                report_progress(record)
    else:
        with ThreadPoolExecutor(max_workers=min(config.max_workers, len(work_items))) as executor:
            futures = [
                executor.submit(
                    evaluate_candidate_tasks,
                    active_client,
                    candidate=candidate,
                    tasks=tasks,
                    run_id=run_id,
                    raw_output_dir=raw_output_dir,
                    parsed_output_dir=parsed_output_dir,
                )
                for candidate, tasks in work_items
            ]
            for future in as_completed(futures):
                for record in future.result():
                    report_progress(record)

    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(config.output_path, records)

    summaries = aggregate_model_role_records(records, bootstrap_samples=config.bootstrap_samples)
    comparisons = paired_model_comparisons(records, bootstrap_samples=config.bootstrap_samples)
    deployable_stack, missing_roles = is_stack_deployable(summaries)
    recommendations = categorized_recommendations(summaries)

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
        "deployable_stack": deployable_stack,
        "missing_roles": missing_roles,
        "eligible_counts_by_category": eligible_counts_by_category(summaries),
        "recommended_stack": recommendations["mandatory"] if deployable_stack else {},
        "partial_recommendations": recommendations["all"],
    }
    if config.report_md_path:
        config.report_md_path.parent.mkdir(parents=True, exist_ok=True)
        config.report_md_path.write_text(render_markdown_report(result, records), encoding="utf-8")
    return result


def candidate_tasks(
    candidate: ModelCandidate,
    requested_roles: set[str],
    fixtures: list[ModelEvalFixture],
    repeat_runs: int,
) -> list[tuple[ModelEvalFixture, int]]:
    tasks: list[tuple[ModelEvalFixture, int]] = []
    for role in roles_for_candidate(candidate, requested_roles, fixtures):
        role_fixtures = [fixture for fixture in fixtures if fixture.role == role]
        if candidate.kind == "embedding":
            role_fixtures = embedding_fixtures(fixtures)
        for fixture in role_fixtures:
            for repeat_idx in range(repeat_runs):
                tasks.append((fixture, repeat_idx))
    return tasks


def evaluate_candidate_tasks(
    client: EvalModelClient,
    *,
    candidate: ModelCandidate,
    tasks: list[tuple[ModelEvalFixture, int]],
    run_id: str,
    raw_output_dir: Path,
    parsed_output_dir: Path,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    first_fixture, first_repeat_idx = tasks[0]
    first_record = run_one_fixture(
        client,
        candidate=candidate,
        fixture=first_fixture,
        run_id=run_id,
        repeat_idx=first_repeat_idx,
        raw_output_dir=raw_output_dir,
        parsed_output_dir=parsed_output_dir,
    )
    records.append(first_record)

    remaining = tasks[1:]
    if first_record["status"] == "fail":
        for fixture, repeat_idx in remaining:
            records.append(
                synthetic_failure_record(
                    candidate=candidate,
                    fixture=fixture,
                    run_id=run_id,
                    repeat_idx=repeat_idx,
                    raw_output_dir=raw_output_dir,
                    parsed_output_dir=parsed_output_dir,
                    error=f"candidate preflight failed: {first_record['failure_message']}",
                )
            )
        return records

    for fixture, repeat_idx in remaining:
        records.append(
            run_one_fixture(
                client,
                candidate=candidate,
                fixture=fixture,
                run_id=run_id,
                repeat_idx=repeat_idx,
                raw_output_dir=raw_output_dir,
                parsed_output_dir=parsed_output_dir,
            )
        )
    return records


def run_one_fixture(
    client: EvalModelClient,
    *,
    candidate: ModelCandidate,
    fixture: ModelEvalFixture,
    run_id: str,
    repeat_idx: int,
    raw_output_dir: Path,
    parsed_output_dir: Path,
) -> dict[str, Any]:
    if candidate.kind == "embedding":
        call = client.embed(candidate, text=fixture.input_text)
    else:
        call = client.complete_json(candidate, prompt=fixture_prompt(fixture), schema=BASE_OUTPUT_SCHEMA)
    return build_eval_record(
        candidate=candidate,
        fixture=fixture,
        run_id=run_id,
        repeat_idx=repeat_idx,
        raw_output_dir=raw_output_dir,
        parsed_output_dir=parsed_output_dir,
        call=call,
    )


def synthetic_failure_record(
    *,
    candidate: ModelCandidate,
    fixture: ModelEvalFixture,
    run_id: str,
    repeat_idx: int,
    raw_output_dir: Path,
    parsed_output_dir: Path,
    error: str,
) -> dict[str, Any]:
    call = ModelCallResult(
        status="fail",
        payload=None,
        raw_text="",
        error=error,
        latency_ms=0,
        input_tokens=0,
        output_tokens=0,
        estimated_cost_usd=0.0,
    )
    return build_eval_record(
        candidate=candidate,
        fixture=fixture,
        run_id=run_id,
        repeat_idx=repeat_idx,
        raw_output_dir=raw_output_dir,
        parsed_output_dir=parsed_output_dir,
        call=call,
    )


def build_eval_record(
    *,
    candidate: ModelCandidate,
    fixture: ModelEvalFixture,
    run_id: str,
    repeat_idx: int,
    raw_output_dir: Path,
    parsed_output_dir: Path,
    call: ModelCallResult,
) -> dict[str, Any]:
    role = fixture.role if candidate.kind != "embedding" else "embeddings"
    raw_output_path = write_raw_output(
        raw_output_dir,
        run_id=run_id,
        candidate=candidate,
        fixture=fixture,
        repeat_idx=repeat_idx,
        call=call,
    )
    parsed_output_path = write_parsed_output(
        parsed_output_dir,
        run_id=run_id,
        candidate=candidate,
        fixture=fixture,
        repeat_idx=repeat_idx,
        payload=call.payload,
    )

    operational_success = call.status != "fail"
    json_parseable = call.status != "schema_fail"
    schema_valid, schema_failure_message = validate_payload(candidate, call.payload)
    if call.status == "schema_fail":
        schema_valid = False
    semantic_evaluable = operational_success and json_parseable and schema_valid

    evaluation_status = call.status
    if call.status == "ok" and not schema_valid:
        evaluation_status = "schema_invalid"

    scores, zero_tolerance_failure, notes = score_model_output(
        fixture,
        call.payload,
        status="ok" if semantic_evaluable else evaluation_status,
    )
    quality_score = semantic_quality_score(scores) if semantic_evaluable else None
    failure_message = schema_failure_message or call.error
    failure_class = classify_failure_class(
        operational_success=operational_success,
        json_parseable=json_parseable,
        schema_valid=schema_valid,
        semantic_evaluable=semantic_evaluable,
        zero_tolerance_failure=zero_tolerance_failure,
        quality_score=quality_score,
        failure_message=failure_message,
    )

    record = EvalRecord(
        run_id=run_id,
        model=candidate.ref,
        provider=candidate.provider,
        role=role,
        fixture_id=fixture.context.get("base_fixture_id", fixture.id),
        variant_id=str(fixture.context.get("variant", "base")),
        operational_success=operational_success,
        failure_class=failure_class,
        failure_message=failure_message,
        schema_valid=schema_valid,
        json_parseable=json_parseable,
        semantic_evaluable=semantic_evaluable,
        zero_tolerance_failure=zero_tolerance_failure,
        zero_tolerance_failure_types=notes if zero_tolerance_failure else [],
        quality_score=quality_score,
        subscores=scores,
        input_tokens=call.input_tokens,
        output_tokens=call.output_tokens,
        estimated_cost_usd=call.estimated_cost_usd,
        latency_ms=float(call.latency_ms),
        raw_output_path=str(raw_output_path),
        parsed_output_path=str(parsed_output_path) if parsed_output_path else None,
        scenario_group=fixture.scenario_group,
        repeat_idx=repeat_idx,
        status=evaluation_status,
        notes=notes,
        kind=candidate.kind,
        fixture_set_version="brain-model-test-v2",
        policy_version="memory-policy-v1",
    )
    return record.model_dump(mode="json")


def validate_payload(
    candidate: ModelCandidate,
    payload: dict[str, Any] | None,
) -> tuple[bool, str | None]:
    if payload is None:
        return False, None
    if candidate.kind == "embedding":
        size = payload.get("embedding_vector_size")
        if isinstance(size, int) and size > 0:
            return True, None
        return False, "embedding payload missing positive integer embedding_vector_size"

    errors = validate_against_schema(payload, BASE_OUTPUT_SCHEMA, path="$")
    if errors:
        return False, errors[0]
    return True, None


def validate_against_schema(value: Any, schema: dict[str, Any], *, path: str) -> list[str]:
    expected_type = schema.get("type")
    if isinstance(expected_type, list):
        branch_errors: list[str] = []
        for branch_type in expected_type:
            candidate_errors = validate_against_schema(value, {**schema, "type": branch_type}, path=path)
            if not candidate_errors:
                return []
            branch_errors.extend(candidate_errors)
        return [branch_errors[0]]

    if expected_type == "object":
        if not isinstance(value, dict):
            return [f"{path} must be an object"]
        errors: list[str] = []
        required = schema.get("required") or []
        for key in required:
            if key not in value:
                errors.append(f"{path}.{key} is required")
        properties = schema.get("properties") or {}
        for key, property_schema in properties.items():
            if key in value:
                errors.extend(validate_against_schema(value[key], property_schema, path=f"{path}.{key}"))
        return errors

    if expected_type == "array":
        if not isinstance(value, list):
            return [f"{path} must be an array"]
        item_schema = schema.get("items")
        if not isinstance(item_schema, dict):
            return []
        errors: list[str] = []
        for idx, item in enumerate(value):
            errors.extend(validate_against_schema(item, item_schema, path=f"{path}[{idx}]"))
        return errors

    if expected_type == "string":
        return [] if isinstance(value, str) else [f"{path} must be a string"]
    if expected_type == "boolean":
        return [] if isinstance(value, bool) else [f"{path} must be a boolean"]
    if expected_type == "integer":
        return [] if isinstance(value, int) and not isinstance(value, bool) else [f"{path} must be an integer"]
    if expected_type == "number":
        return [] if isinstance(value, (int, float)) and not isinstance(value, bool) else [f"{path} must be a number"]
    if expected_type == "null":
        return [] if value is None else [f"{path} must be null"]
    return []


def roles_for_candidate(
    candidate: ModelCandidate,
    requested_roles: set[str],
    fixtures: list[ModelEvalFixture],
) -> list[str]:
    fixture_roles = {fixture.role for fixture in fixtures}
    if candidate.kind == "embedding":
        return ["embeddings"] if not requested_roles or "embeddings" in requested_roles else []
    roles = set(candidate.roles)
    if requested_roles:
        roles &= requested_roles
    roles &= fixture_roles
    if requested_roles and not roles:
        return []
    if not roles:
        roles = fixture_roles
    return sorted(roles)


def embedding_fixtures(fixtures: list[ModelEvalFixture]) -> list[ModelEvalFixture]:
    for fixture in fixtures:
        if fixture.role == "embeddings":
            return [fixture]
    for fixture in fixtures:
        if fixture.role == "memory_compiler":
            return [fixture]
    return fixtures[:1]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
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


def write_parsed_output(
    parsed_output_dir: Path,
    *,
    run_id: str,
    candidate: ModelCandidate,
    fixture: ModelEvalFixture,
    repeat_idx: int,
    payload: dict[str, Any] | None,
) -> Path | None:
    if payload is None:
        return None
    parsed_output_dir.mkdir(parents=True, exist_ok=True)
    safe_model = candidate.ref.replace(":", "_").replace("/", "_")
    path = parsed_output_dir / f"{safe_model}__{fixture.id}__{repeat_idx}.json"
    path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "model": candidate.ref,
                "fixture_id": fixture.id,
                "payload": payload,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def render_markdown_report(result: dict[str, Any], records: list[dict[str, Any]]) -> str:
    summaries = [Summary.model_validate(item) for item in result.get("summaries", [])]
    comparisons = [PairwiseComparison.model_validate(item) for item in result.get("pairwise_comparisons", [])]
    eval_records = [EvalRecord.model_validate(item) for item in records]
    deployable_stack = bool(result.get("deployable_stack"))
    missing_roles = list(result.get("missing_roles") or [])
    eligible_counts = result.get("eligible_counts_by_category") or eligible_counts_by_category(summaries)
    recommendations = result.get("partial_recommendations") or categorized_recommendations(summaries)["all"]
    mandatory_recommendations = result.get("recommended_stack") or categorized_recommendations(summaries)["mandatory"]
    non_deployable_section = (
        non_deployable_rows(summaries, missing_roles)
        if not deployable_stack
        else ["Stack is deployable; this section is not applicable."]
    )

    lines = [
        "# Executive verdict",
        "",
        f"Deployable stack: **{'YES' if deployable_stack else 'NO'}**",
        "",
    ]
    if deployable_stack:
        lines.extend(
            [
                "All mandatory roles have at least one eligible model.",
                "",
                "Recommended production stack:",
                *format_recommendation_lines(mandatory_recommendations),
                "",
                "Selection basis:",
                "All mandatory roles had at least one eligible model with zero zero-tolerance failures and role-specific lower-bound confidence intervals above threshold.",
            ]
        )
    else:
        lines.extend(
            [
                "This run is not sufficient to select a full production Brain model stack.",
                "",
                "Missing mandatory roles:",
                *format_role_list(missing_roles),
                "",
                "Interpretation:",
                f"Only {eligible_summary_sentence(eligible_counts)} had eligible candidates. Treat this as a harness validation run, not a model-selection run.",
                "",
                "Eligible partials:",
                *format_recommendation_lines(recommendations),
            ]
        )

    lines.extend(
        [
            "",
            "## Deployability status",
            "",
            f"- Run ID: `{result['run_id']}`",
            f"- Fixture set: `{result['fixture_set']}`",
            f"- JSONL output: `{result['output_path']}`",
            f"- Records: `{result['record_count']}`",
            f"- Model-role summaries: `{len(summaries)}`",
            f"- Deployable stack: `{'yes' if deployable_stack else 'no'}`",
            f"- Eligible runtime role pairs: `{eligible_counts.get('runtime', 0)}`",
            f"- Eligible embedding role pairs: `{eligible_counts.get('embedding', 0)}`",
            f"- Eligible judge role pairs: `{eligible_counts.get('judge', 0)}`",
            f"- Eligible debug/admin role pairs: `{eligible_counts.get('debug_admin', 0)}`",
            f"- Eligible support role pairs: `{eligible_counts.get('support', 0) + eligible_counts.get('runtime_or_support', 0)}`",
            "",
            "## Mandatory role coverage",
            "",
            "| Role | Required | Eligible models | Status |",
            "|---|---:|---|---|",
            *mandatory_role_rows(summaries),
            "",
            "## Operational reliability",
            "",
            "| Model | Role | Operational success | 95% CI | Successes / Total |",
            "|---|---|---:|---:|---:|",
            *operational_rows(summaries),
            "",
            *operational_failure_summary(eval_records),
            "",
            "## Schema validity",
            "",
            "| Model | Role | Schema validity | 95% CI | Valid / Operationally successful |",
            "|---|---|---:|---:|---:|",
            *schema_rows(summaries),
            "",
            *schema_failure_summary(eval_records),
            "",
            "## Safety / zero-tolerance failures",
            "",
            "| Model | Role | Zero-tolerance failures | Upper 95% fail rate | Eligible |",
            "|---|---|---:|---:|---|",
            *zero_tolerance_rows(summaries),
            "",
            "## Quality scores by role",
            "",
            "| Model | Role | Category | Semantic score | 95% CI | Semantic evals | Eligible | Rejection reasons |",
            "|---|---|---|---:|---:|---:|---|---|",
            *quality_rows(summaries),
            "",
            "## Runtime-role recommendations",
            "",
        ]
    )
    if deployable_stack:
        lines.extend(format_recommendation_lines(recommendations_for_categories(summaries, {"runtime"})))
    else:
        lines.extend(["Partial recommendations only."])
        lines.extend(format_recommendation_lines(recommendations_for_categories(summaries, {"runtime"})))

    lines.extend(
        [
            "",
            "## Embedding recommendations",
            "",
            *format_recommendation_lines(recommendations_for_categories(summaries, {"embedding"})),
            "",
            "## Judge/debug/support recommendations",
            "",
            *format_recommendation_lines(recommendations_for_categories(summaries, {"judge", "debug_admin", "support", "runtime_or_support"})),
            "",
            "## Pairwise comparisons",
            "",
            "| Role | Model A | Model B | Shared variants | Shared semantic variants | Semantic diff | Operational diff | Schema diff | Recommendation |",
            "|---|---|---|---:|---:|---:|---:|---:|---|",
            *pairwise_rows(comparisons),
            "",
            "## Cost and latency",
            "",
            "| Model | Role | Cost / 1k successful | p50 ms | p90 ms | p95 ms |",
            "|---|---|---:|---:|---:|---:|",
            *cost_rows(summaries),
            "",
            "## Why non-deployable, if applicable",
            "",
            *non_deployable_section,
            "",
            "## Next actions",
            "",
            *next_action_rows(deployable_stack, missing_roles, eval_records, summaries),
            "",
        ]
    )
    return "\n".join(lines)


def render_report(
    *,
    deployable_stack: bool,
    missing_roles: list[str],
    partial_recommendations: dict[str, str],
    recommended_stack: dict[str, str] | None = None,
) -> str:
    lines = [
        "# Executive verdict",
        "",
        f"Deployable stack: **{'YES' if deployable_stack else 'NO'}**",
        "",
    ]
    if deployable_stack:
        lines.extend(
            [
                "Recommended production stack:",
                *format_recommendation_lines(recommended_stack or partial_recommendations),
            ]
        )
    else:
        lines.extend(
            [
                "Missing mandatory roles:",
                *format_role_list(missing_roles),
                "",
                "## Partial recommendations",
                "",
                *format_recommendation_lines(partial_recommendations),
            ]
        )
    return "\n".join(lines) + "\n"


def categorized_recommendations(summaries: list[Summary | dict[str, Any]]) -> dict[str, dict[str, str]]:
    normalized = [item if isinstance(item, Summary) else Summary.model_validate(item) for item in summaries]
    all_recommendations = recommendations_for_categories(
        normalized,
        {"runtime", "embedding", "judge", "debug_admin", "support", "runtime_or_support"},
    )
    mandatory = {
        role: model
        for role, model in all_recommendations.items()
        if role in {"router", "slack_intake", "memory_compiler", "conflict_classifier", "recall_synthesizer", "embeddings"}
    }
    return {"all": all_recommendations, "mandatory": mandatory}


def recommendations_for_categories(
    summaries: list[Summary | dict[str, Any]],
    categories: set[str],
) -> dict[str, str]:
    normalized = [item if isinstance(item, Summary) else Summary.model_validate(item) for item in summaries]
    by_role: dict[str, list[Summary]] = defaultdict(list)
    for summary in normalized:
        if not summary.eligible or summary.role_category not in categories:
            continue
        by_role[summary.role].append(summary)
    chosen: dict[str, str] = {}
    for role, options in sorted(by_role.items()):
        winner = min(
            options,
            key=lambda item: (
                float("inf") if item.cost_per_1k_successful is None else item.cost_per_1k_successful,
                item.model,
            ),
        )
        chosen[role] = winner.model
    return chosen


def eligible_counts_by_category(summaries: list[Summary | dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for item in summaries:
        summary = item if isinstance(item, Summary) else Summary.model_validate(item)
        if summary.eligible:
            counts[summary.role_category] += 1
    return dict(counts)


def semantic_quality_score(scores: dict[str, float | None]) -> float | None:
    numeric_values = [float(value) for value in scores.values() if value is not None]
    if not numeric_values:
        return None
    return mean(numeric_values)


def mandatory_role_rows(summaries: list[Summary]) -> list[str]:
    by_role: dict[str, list[str]] = defaultdict(list)
    for summary in summaries:
        if summary.eligible:
            by_role[summary.role].append(summary.model)
    rows: list[str] = []
    for role in sorted({"router", "slack_intake", "memory_compiler", "conflict_classifier", "recall_synthesizer", "embeddings"}):
        models = ", ".join(f"`{model}`" for model in sorted(by_role.get(role, []))) or "none"
        status = "OK" if by_role.get(role) else "MISSING"
        rows.append(f"| `{role}` | yes | {models} | {status} |")
    return rows


def operational_rows(summaries: list[Summary]) -> list[str]:
    return [
        "| "
        f"`{summary.model}` | `{summary.role}` | "
        f"{summary.operational_success_rate:.3f} | "
        f"{summary.operational_success_ci_low:.3f}-{summary.operational_success_ci_high:.3f} | "
        f"{summary.records_operational_success} / {summary.records_total} |"
        for summary in summaries
    ]


def schema_rows(summaries: list[Summary]) -> list[str]:
    return [
        "| "
        f"`{summary.model}` | `{summary.role}` | "
        f"{summary.schema_validity_rate:.3f} | "
        f"{summary.schema_validity_ci_low:.3f}-{summary.schema_validity_ci_high:.3f} | "
        f"{summary.records_schema_valid} / {summary.records_operational_success} |"
        for summary in summaries
    ]


def zero_tolerance_rows(summaries: list[Summary]) -> list[str]:
    return [
        "| "
        f"`{summary.model}` | `{summary.role}` | "
        f"{summary.zero_tolerance_failures} | "
        f"{summary.zero_tolerance_upper_95_fail_rate:.3f} | "
        f"{summary.eligible} |"
        for summary in summaries
    ]


def quality_rows(summaries: list[Summary]) -> list[str]:
    rows: list[str] = []
    for summary in summaries:
        semantic_mean = f"{summary.semantic_score_mean:.3f}" if summary.semantic_score_mean is not None else "n/a"
        semantic_ci = (
            f"{summary.semantic_score_ci_low:.3f}-{summary.semantic_score_ci_high:.3f}"
            if summary.semantic_score_ci_low is not None and summary.semantic_score_ci_high is not None
            else "n/a"
        )
        reasons = ", ".join(summary.rejection_reasons) or "-"
        rows.append(
            "| "
            f"`{summary.model}` | `{summary.role}` | `{summary.role_category}` | "
            f"{semantic_mean} | {semantic_ci} | {summary.records_semantic_evaluable} | "
            f"{summary.eligible} | {reasons} |"
        )
    return rows


def pairwise_rows(comparisons: list[PairwiseComparison]) -> list[str]:
    if not comparisons:
        return ["| | | | | | | | | No pairwise comparisons available. |"]
    rows: list[str] = []
    for comparison in comparisons:
        semantic_diff = (
            "n/a"
            if comparison.semantic_score_diff_mean is None
            else f"{comparison.semantic_score_diff_mean:.3f} ({comparison.semantic_score_diff_ci_low:.3f}-{comparison.semantic_score_diff_ci_high:.3f})"
        )
        rows.append(
            "| "
            f"`{comparison.role}` | `{comparison.model_a}` | `{comparison.model_b}` | "
            f"{comparison.shared_variants_total} | {comparison.shared_variants_semantic_evaluable} | "
            f"{semantic_diff} | "
            f"{comparison.operational_success_diff_mean:.3f} ({comparison.operational_success_diff_ci_low:.3f}-{comparison.operational_success_diff_ci_high:.3f}) | "
            f"{comparison.schema_validity_diff_mean:.3f} ({comparison.schema_validity_diff_ci_low:.3f}-{comparison.schema_validity_diff_ci_high:.3f}) | "
            f"{comparison.recommendation}: {comparison.recommendation_reason} |"
        )
    return rows


def cost_rows(summaries: list[Summary]) -> list[str]:
    rows: list[str] = []
    for summary in summaries:
        cost = "n/a" if summary.cost_per_1k_successful is None else f"${summary.cost_per_1k_successful:.4f}"
        p50 = "n/a" if summary.latency_p50_ms is None else f"{summary.latency_p50_ms:.0f}"
        p90 = "n/a" if summary.latency_p90_ms is None else f"{summary.latency_p90_ms:.0f}"
        p95 = "n/a" if summary.latency_p95_ms is None else f"{summary.latency_p95_ms:.0f}"
        rows.append(f"| `{summary.model}` | `{summary.role}` | {cost} | {p50} | {p90} | {p95} |")
    return rows


def operational_failure_summary(records: list[EvalRecord]) -> list[str]:
    failures = [record for record in records if record.operational_success is False]
    if not failures:
        return ["No operational failures were recorded."]
    counts = Counter(record.failure_class.value for record in failures)
    return [
        "Operational failure classes:",
        *[f"- `{failure_class}`: {count}" for failure_class, count in sorted(counts.items())],
    ]


def schema_failure_summary(records: list[EvalRecord]) -> list[str]:
    failures = [
        record
        for record in records
        if record.operational_success and (not record.json_parseable or not record.schema_valid)
    ]
    if not failures:
        return ["No schema or parse failures were recorded."]
    counts = Counter(record.failure_class.value for record in failures)
    return [
        "Schema / parse failure classes:",
        *[f"- `{failure_class}`: {count}" for failure_class, count in sorted(counts.items())],
    ]


def non_deployable_rows(summaries: list[Summary], missing_roles: list[str]) -> list[str]:
    if not missing_roles:
        return ["Mandatory coverage is complete."]
    by_role: dict[str, list[Summary]] = defaultdict(list)
    for summary in summaries:
        by_role[summary.role].append(summary)
    rows: list[str] = ["Missing mandatory roles:"]
    rows.extend(format_role_list(missing_roles))
    rows.append("")
    rows.append("Observed rejection reasons:")
    for role in missing_roles:
        reasons = Counter(
            reason
            for summary in by_role.get(role, [])
            for reason in summary.rejection_reasons
        )
        if not reasons:
            rows.append(f"- `{role}`: no eligible candidates were evaluated for this role.")
            continue
        formatted = ", ".join(f"{reason} ({count})" for reason, count in sorted(reasons.items()))
        rows.append(f"- `{role}`: {formatted}")
    return rows


def next_action_rows(
    deployable_stack: bool,
    missing_roles: list[str],
    records: list[EvalRecord],
    summaries: list[Summary],
) -> list[str]:
    if deployable_stack:
        return [
            "- Rerun the winning stack on the full production fixture set with more repeats to tighten confidence intervals.",
            "- Judge-audit borderline semantic failures before final promotion.",
            "- Validate production latency and cost assumptions against live traffic shape.",
        ]

    failure_counts = Counter(record.failure_class.value for record in records if record.failure_class != FailureClass.NONE)
    top_failures = ", ".join(f"{name} ({count})" for name, count in failure_counts.most_common(3))
    return [
        f"- Restore mandatory coverage for: {', '.join(missing_roles)}.",
        f"- Eliminate the largest blocking failure classes first: {top_failures or 'none recorded'}.",
        "- Rerun after operational issues are fixed so semantic comparisons are based on overlapping evaluable variants.",
        "- Add or refine role-specific fixtures if a mandatory role remains unevaluable after provider issues are resolved.",
    ]


def eligible_summary_sentence(counts: dict[str, int]) -> str:
    parts = []
    if counts.get("runtime", 0):
        parts.append("runtime")
    if counts.get("embedding", 0):
        parts.append("embedding")
    if counts.get("judge", 0):
        parts.append("judge")
    if counts.get("debug_admin", 0):
        parts.append("debug/admin")
    if counts.get("support", 0) or counts.get("runtime_or_support", 0):
        parts.append("support")
    return ", ".join(parts) if parts else "no roles"


def format_recommendation_lines(recommendations: dict[str, str] | list[str]) -> list[str]:
    if isinstance(recommendations, list):
        return recommendations or ["- none"]
    if not recommendations:
        return ["- none"]
    return [f"- `{role}`: `{model}`" for role, model in sorted(recommendations.items())]


def format_role_list(roles: list[str]) -> list[str]:
    return [f"- {role}" for role in roles] or ["- none"]
