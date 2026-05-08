from __future__ import annotations

import csv
import html
import hashlib
import json
import re
from collections import Counter, defaultdict, deque
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from tempfile import NamedTemporaryFile
from threading import BoundedSemaphore, Lock
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
    candidate_from_ref,
    load_model_registry,
    registry_model_index,
    select_model_candidates,
)
from memory_stack.evals.provider_client import LiveProviderClient, ModelCallResult
from memory_stack.evals.scoring import (
    EvalRecord,
    FailureClass,
    PairwiseComparison,
    Summary,
    aggregate_model_role_records,
    capability_coverage,
    classify_failure_class,
    normalized_status,
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
    mode: str = "broad"
    model_set: str | None = None
    report_md_path: Path | None = None
    raw_output_dir: Path | None = None
    endpoint_max_concurrency: int = 1
    retry_attempts: int = 2
    retry_backoff_seconds: float = 1.0


@dataclass(frozen=True)
class EvalWorkItem:
    candidate: ModelCandidate
    fixture: ModelEvalFixture
    repeat_idx: int


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
        mode=config.mode,
    )
    fixtures = select_fixtures(fixture_set=config.fixture_set, roles=config.roles, mode=config.mode)
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
    work_items = build_work_items(candidates, config.roles, fixtures, config.repeat_runs)
    total_records = len(work_items)
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

    endpoint_limit = max(1, config.endpoint_max_concurrency)
    endpoint_keys = {item.candidate.endpoint_key for item in work_items}
    max_parallel_workers = min(len(work_items), max(1, len(endpoint_keys) * endpoint_limit))
    if max_parallel_workers <= 1:
        for item in work_items:
            report_progress(
                evaluate_work_item(
                    active_client,
                    item=item,
                    run_id=run_id,
                    raw_output_dir=raw_output_dir,
                    parsed_output_dir=parsed_output_dir,
                )
            )
    else:
        endpoint_semaphores: dict[str, BoundedSemaphore] = {
            key: BoundedSemaphore(endpoint_limit) for key in {item.candidate.endpoint_key for item in work_items}
        }
        with ThreadPoolExecutor(max_workers=max_parallel_workers) as executor:
            futures = [
                executor.submit(
                    evaluate_work_item,
                    active_client,
                    item=item,
                    run_id=run_id,
                    raw_output_dir=raw_output_dir,
                    parsed_output_dir=parsed_output_dir,
                    endpoint_semaphore=endpoint_semaphores[item.candidate.endpoint_key],
                )
                for item in work_items
            ]
            for future in as_completed(futures):
                report_progress(future.result())

    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    assign_failure_numbers(records)
    write_eval_records(config.output_path, records)

    result = build_run_result(
        run_id=run_id,
        fixture_set=config.fixture_set,
        mode=config.mode,
        output_path=config.output_path,
        report_md_path=config.report_md_path,
        records=records,
        models=[candidate.ref for candidate in candidates],
        roles=sorted(config.roles) if config.roles else "candidate_roles",
        bootstrap_samples=config.bootstrap_samples,
    )
    write_run_artifacts(result, records)
    return result


def build_work_items(
    candidates: list[ModelCandidate],
    requested_roles: set[str],
    fixtures: list[ModelEvalFixture],
    repeat_runs: int,
) -> list[EvalWorkItem]:
    items: list[EvalWorkItem] = []
    for repeat_idx in range(repeat_runs):
        endpoint_buckets: dict[str, deque[EvalWorkItem]] = {}
        endpoint_order: list[str] = []
        for candidate in candidates:
            for role in roles_for_candidate(candidate, requested_roles, fixtures):
                role_fixtures = [fixture for fixture in fixtures if fixture.role == role]
                if candidate.kind == "embedding":
                    role_fixtures = embedding_fixtures(fixtures)
                for fixture in role_fixtures:
                    key = candidate.endpoint_key
                    if key not in endpoint_buckets:
                        endpoint_buckets[key] = deque()
                        endpoint_order.append(key)
                    endpoint_buckets[key].append(
                        EvalWorkItem(candidate=candidate, fixture=fixture, repeat_idx=repeat_idx)
                    )
        while endpoint_buckets:
            for key in endpoint_order:
                bucket = endpoint_buckets.get(key)
                if not bucket:
                    continue
                items.append(bucket.popleft())
                if not bucket:
                    endpoint_buckets.pop(key, None)
    return items


def evaluate_work_item(
    client: EvalModelClient,
    *,
    item: EvalWorkItem,
    run_id: str,
    raw_output_dir: Path,
    parsed_output_dir: Path,
    rerun_of_run_id: str | None = None,
    rerun_timestamp: str | None = None,
    endpoint_semaphore: BoundedSemaphore | None = None,
) -> dict[str, Any]:
    if endpoint_semaphore is None:
        return run_one_fixture(
            client,
            candidate=item.candidate,
            fixture=item.fixture,
            run_id=run_id,
            repeat_idx=item.repeat_idx,
            raw_output_dir=raw_output_dir,
            parsed_output_dir=parsed_output_dir,
            rerun_of_run_id=rerun_of_run_id,
            rerun_timestamp=rerun_timestamp,
        )
    with endpoint_semaphore:
        return run_one_fixture(
            client,
            candidate=item.candidate,
            fixture=item.fixture,
            run_id=run_id,
            repeat_idx=item.repeat_idx,
            raw_output_dir=raw_output_dir,
            parsed_output_dir=parsed_output_dir,
            rerun_of_run_id=rerun_of_run_id,
            rerun_timestamp=rerun_timestamp,
        )


def run_one_fixture(
    client: EvalModelClient,
    *,
    candidate: ModelCandidate,
    fixture: ModelEvalFixture,
    run_id: str,
    repeat_idx: int,
    raw_output_dir: Path,
    parsed_output_dir: Path,
    rerun_of_run_id: str | None = None,
    rerun_timestamp: str | None = None,
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
        rerun_of_run_id=rerun_of_run_id,
        rerun_timestamp=rerun_timestamp,
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
    rerun_of_run_id: str | None = None,
    rerun_timestamp: str | None = None,
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
        rerun_of_run_id=rerun_of_run_id,
        rerun_timestamp=rerun_timestamp,
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
    rerun_of_run_id: str | None = None,
    rerun_timestamp: str | None = None,
) -> dict[str, Any]:
    role = fixture.role if candidate.kind != "embedding" else "embeddings"
    fixture_set_version = "brain-model-test-v2"
    policy_version = "memory-policy-v1"
    fixture_id = fixture.context.get("base_fixture_id", fixture.id)
    variant_id = str(fixture.context.get("variant", "base"))
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
    json_parseable = operational_success and call.status != "schema_fail"
    schema_valid, schema_failure_message = validate_payload(candidate, call.payload)
    if not json_parseable:
        schema_valid = False
    semantic_evaluable = operational_success and json_parseable and schema_valid

    scores, zero_tolerance_failure, notes = score_model_output(
        fixture,
        call.payload,
        status="ok" if semantic_evaluable else ("parse_fail" if not json_parseable else "schema_fail" if not schema_valid else "provider_fail"),
    )
    quality_score = semantic_quality_score(scores) if semantic_evaluable else None
    quality_passed = semantic_evaluable and (not zero_tolerance_failure) and quality_score is not None and quality_score >= 1.0
    evaluation_status = normalized_status(
        status=call.status,
        operational_success=operational_success,
        json_parseable=json_parseable,
        schema_valid=schema_valid,
        zero_tolerance_failure=zero_tolerance_failure,
        quality_score=quality_score,
    )
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
    failure_reason_codes = notes if failure_class != FailureClass.NONE else []

    record = EvalRecord(
        record_id=stable_record_id(
            fixture_set_version=fixture_set_version,
            policy_version=policy_version,
            model=candidate.ref,
            role=role,
            fixture_id=str(fixture_id),
            variant_id=variant_id,
            repeat_idx=repeat_idx,
        ),
        run_id=run_id,
        rerun_of_run_id=rerun_of_run_id,
        rerun_timestamp=rerun_timestamp,
        fixture_set_version=fixture_set_version,
        policy_version=policy_version,
        model=candidate.ref,
        provider=candidate.provider,
        role=role,
        fixture_id=str(fixture_id),
        variant_id=variant_id,
        operational_success=operational_success,
        failure_class=failure_class,
        failure_message=failure_message,
        failure_reason_codes=failure_reason_codes,
        schema_valid=schema_valid,
        json_parseable=json_parseable,
        semantic_evaluable=semantic_evaluable,
        quality_passed=quality_passed,
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


def write_eval_records(path: Path, records: list[dict[str, Any]]) -> None:
    if path.suffix == ".json":
        path.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")
        return
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def read_eval_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        data = json.loads(text or "[]")
        if not isinstance(data, list):
            raise ValueError(f"expected JSON array in {path}")
        return data
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def atomic_write_eval_records(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent, suffix=path.suffix) as tmp:
        tmp_path = Path(tmp.name)
        if path.suffix == ".json":
            tmp.write(json.dumps(records, indent=2, sort_keys=True))
        else:
            tmp.write("".join(json.dumps(record, sort_keys=True) + "\n" for record in records))
    _ = read_eval_records(tmp_path)
    tmp_path.replace(path)


def stable_record_id(
    *,
    fixture_set_version: str,
    policy_version: str,
    model: str,
    role: str,
    fixture_id: str,
    variant_id: str,
    repeat_idx: int,
) -> str:
    payload = "\n".join(
        [
            fixture_set_version,
            policy_version,
            model,
            role,
            fixture_id,
            variant_id,
            str(repeat_idx),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def assign_failure_numbers(records: list[dict[str, Any]]) -> None:
    failure_number = 0
    for record in records:
        failure_class = FailureClass(record.get("failure_class", FailureClass.NONE))
        status = record.get("status")
        if failure_class == FailureClass.NONE and status != "skipped":
            record["failure_number"] = None
            continue
        failure_number += 1
        record["failure_number"] = failure_number


def failure_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for record in records:
        failure_class = FailureClass(record.get("failure_class", FailureClass.NONE))
        if failure_class != FailureClass.NONE or record.get("status") == "skipped":
            failures.append(record)
    return failures


def write_run_artifacts(result: dict[str, Any], records: list[dict[str, Any]]) -> None:
    output_path = Path(result["output_path"])
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = Path(result["report_md_path"])
    html_report_path = Path(result.get("report_html_path") or report_path.with_suffix(".html"))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_report = render_markdown_report(result, records)
    report_path.write_text(markdown_report, encoding="utf-8")
    html_report_path.write_text(
        render_html_report(markdown_report, title=f"Brain Eval Summary {result['run_id']}"),
        encoding="utf-8",
    )

    failed_path = output_dir / "failed_tests.jsonl"
    failed_md_path = output_dir / "failed_tests.md"
    failures = failure_records(records)
    write_eval_records(failed_path, [failed_manifest_row(record) for record in failures])
    failed_md_path.write_text(render_failed_tests_markdown(result["run_id"], failures), encoding="utf-8")

    summaries = [Summary.model_validate(item) for item in result.get("summaries", [])]
    write_model_role_summary_csv(output_dir / "model_role_summary.csv", summaries)
    write_cost_latency_csv(output_dir / "cost_latency.csv", summaries)
    write_zero_tolerance_csv(output_dir / "zero_tolerance_summary.csv", summaries)


def build_run_result(
    *,
    run_id: str,
    fixture_set: str,
    mode: str,
    output_path: Path,
    report_md_path: Path | None,
    records: list[dict[str, Any]],
    models: list[str],
    roles: list[str] | str,
    bootstrap_samples: int,
) -> dict[str, Any]:
    summaries = aggregate_model_role_records(records, bootstrap_samples=bootstrap_samples)
    comparisons = paired_model_comparisons(records, bootstrap_samples=bootstrap_samples)
    deployable_stack, missing_roles = is_stack_deployable(summaries, mode=mode)
    coverage = capability_coverage(summaries) if mode == "fine-grained" else {}
    recommendations = categorized_recommendations(summaries)
    report_path = report_md_path or output_path.parent / "summary.md"
    return {
        "run_id": run_id,
        "fixture_set": fixture_set,
        "mode": mode,
        "models": models,
        "roles": roles,
        "record_count": len(records),
        "output_path": str(output_path),
        "report_md_path": str(report_path),
        "report_html_path": str(report_path.with_suffix(".html")),
        "failed_manifest_jsonl_path": str(output_path.parent / "failed_tests.jsonl"),
        "failed_manifest_md_path": str(output_path.parent / "failed_tests.md"),
        "summaries": summaries,
        "pairwise_comparisons": comparisons,
        "capability_coverage": coverage,
        "deployable_stack": deployable_stack,
        "missing_roles": missing_roles,
        "eligible_counts_by_category": eligible_counts_by_category(summaries),
        "recommended_stack": recommendations["mandatory"] if deployable_stack else {},
        "partial_recommendations": recommendations["all"],
    }


def merge_rerun_records(
    original_records: list[dict[str, Any]],
    rerun_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged_by_id = {str(record["record_id"]): record for record in original_records}
    for record in rerun_records:
        merged_by_id[str(record["record_id"])] = record
    return list(merged_by_id.values())


def candidate_for_record(
    record: dict[str, Any],
    *,
    registry_index: dict[str, ModelCandidate] | None = None,
) -> ModelCandidate:
    model_ref = str(record.get("model") or "")
    role = str(record.get("role") or "")
    if registry_index and model_ref in registry_index:
        return candidate_from_ref(model_ref, registry_index, roles={role}, include_judge=True)

    kind = str(record.get("kind") or ("embedding" if role == "embeddings" else "llm"))
    provider = str(record.get("provider") or model_ref.split(":", 1)[0] or "unknown")
    return ModelCandidate(
        provider=provider,
        model=model_ref.split(":", 1)[1] if ":" in model_ref else model_ref,
        kind=kind,
        roles=(role,),
        requested_ref=model_ref or None,
    )


def raw_call_for_record(record: dict[str, Any]) -> ModelCallResult:
    raw_path_value = record.get("raw_output_path")
    if isinstance(raw_path_value, str) and raw_path_value:
        raw_path = Path(raw_path_value)
        data = json.loads(raw_path.read_text(encoding="utf-8"))
        payload = data.get("payload")
        if not isinstance(payload, dict):
            payload = None
        return ModelCallResult(
            status=str(data.get("status") or record.get("status") or "fail"),
            payload=payload,
            raw_text=str(data.get("raw_text") or ""),
            error=data.get("error"),
            latency_ms=float(record.get("latency_ms") or 0.0),
            input_tokens=int(record.get("input_tokens") or 0),
            output_tokens=int(record.get("output_tokens") or 0),
            estimated_cost_usd=float(record.get("estimated_cost_usd") or 0.0),
        )

    payload = None
    parsed_path_value = record.get("parsed_output_path")
    if isinstance(parsed_path_value, str) and parsed_path_value:
        parsed_path = Path(parsed_path_value)
        parsed = json.loads(parsed_path.read_text(encoding="utf-8"))
        if isinstance(parsed.get("payload"), dict):
            payload = parsed["payload"]
    return ModelCallResult(
        status=str(record.get("status") or "fail"),
        payload=payload,
        raw_text="",
        error=record.get("failure_message"),
        latency_ms=float(record.get("latency_ms") or 0.0),
        input_tokens=int(record.get("input_tokens") or 0),
        output_tokens=int(record.get("output_tokens") or 0),
        estimated_cost_usd=float(record.get("estimated_cost_usd") or 0.0),
    )


def rescore_record(
    record: dict[str, Any],
    *,
    registry_index: dict[str, ModelCandidate] | None = None,
) -> dict[str, Any]:
    candidate = candidate_for_record(record, registry_index=registry_index)
    role = str(record.get("role") or "")
    mode = mode_for_roles({role})
    fixture = find_fixture_for_record(
        fixture_set=str(record.get("fixture_set_version") or "brain-model-test-v2"),
        role=role,
        fixture_id=str(record.get("fixture_id") or ""),
        variant_id=str(record.get("variant_id") or "base"),
        mode=mode,
    )
    call = raw_call_for_record(record)

    operational_success = call.status != "fail"
    json_parseable = operational_success and call.status != "schema_fail"
    schema_valid, schema_failure_message = validate_payload(candidate, call.payload)
    if not json_parseable:
        schema_valid = False
    semantic_evaluable = operational_success and json_parseable and schema_valid

    scores, zero_tolerance_failure, notes = score_model_output(
        fixture,
        call.payload,
        status="ok" if semantic_evaluable else ("parse_fail" if not json_parseable else "schema_fail" if not schema_valid else "provider_fail"),
    )
    quality_score = semantic_quality_score(scores) if semantic_evaluable else None
    quality_passed = semantic_evaluable and (not zero_tolerance_failure) and quality_score is not None and quality_score >= 1.0
    evaluation_status = normalized_status(
        status=str(record.get("status") or call.status),
        operational_success=operational_success,
        json_parseable=json_parseable,
        schema_valid=schema_valid,
        zero_tolerance_failure=zero_tolerance_failure,
        quality_score=quality_score,
    )
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
    failure_reason_codes = notes if failure_class != FailureClass.NONE else []

    updated = dict(record)
    updated.update(
        {
            "provider": candidate.provider,
            "operational_success": operational_success,
            "json_parseable": json_parseable,
            "schema_valid": schema_valid,
            "semantic_evaluable": semantic_evaluable,
            "quality_passed": quality_passed,
            "status": evaluation_status,
            "failure_message": failure_message,
            "failure_class": failure_class,
            "failure_reason_codes": failure_reason_codes,
            "zero_tolerance_failure": zero_tolerance_failure,
            "zero_tolerance_failure_types": notes if zero_tolerance_failure else [],
            "quality_score": quality_score,
            "subscores": scores,
            "notes": notes,
            "kind": candidate.kind,
        }
    )
    return EvalRecord.model_validate(updated).model_dump(mode="json")


def run_rescore(
    *,
    registry_path: Path,
    source_path: Path,
    output_path: Path,
    overwrite: bool,
    bootstrap_samples: int,
) -> dict[str, Any]:
    if output_path != source_path and not overwrite:
        raise ValueError("rescore currently requires --overwrite or matching source/output path")

    records = read_eval_records(source_path)
    registry = load_model_registry(registry_path)
    index = registry_model_index(registry)
    rescored = [rescore_record(record, registry_index=index) for record in records]
    assign_failure_numbers(rescored)
    atomic_write_eval_records(output_path, rescored)

    roles = sorted({str(record.get("role") or "") for record in rescored if record.get("role")})
    mode = mode_for_roles(set(roles))
    result = build_run_result(
        run_id=f"rescore_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
        fixture_set=str(rescored[0].get("fixture_set_version") or "brain-model-test-v2") if rescored else "brain-model-test-v2",
        mode=mode,
        output_path=output_path,
        report_md_path=output_path.parent / "summary.md",
        records=rescored,
        models=sorted({str(record.get("model") or "") for record in rescored if record.get("model")}),
        roles=roles,
        bootstrap_samples=bootstrap_samples,
    )
    write_run_artifacts(result, rescored)
    return result


def run_rerun_failed(
    settings: Settings,
    *,
    registry_path: Path,
    source_path: Path,
    failed_manifest_path: Path,
    output_path: Path,
    overwrite: bool,
    bootstrap_samples: int,
    endpoint_max_concurrency: int,
    retry_attempts: int,
    retry_backoff_seconds: float,
    failure_class: str | None = None,
    role: str | None = None,
    model: str | None = None,
    client: EvalModelClient | None = None,
) -> dict[str, Any]:
    if output_path != source_path and not overwrite:
        raise ValueError("rerun-failed currently requires --overwrite or matching source/output path")

    canonical_records = read_eval_records(source_path)
    manifest_records = read_eval_records(failed_manifest_path)
    filtered_manifest = [
        record
        for record in manifest_records
        if (failure_class is None or record.get("failure_class") == failure_class)
        and (role is None or record.get("role") == role)
        and (model is None or record.get("model") == model)
    ]
    if not filtered_manifest:
        raise ValueError("no failed manifest rows matched the requested filters")

    registry = load_model_registry(registry_path)
    index = registry_model_index(registry)
    rerun_run_id = f"eval_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
    rerun_timestamp = datetime.now(UTC).isoformat()
    active_client = client or LiveProviderClient(
        settings,
        retry_attempts=retry_attempts,
        retry_backoff_seconds=retry_backoff_seconds,
    )
    raw_output_dir = output_path.parent / "raw" / rerun_run_id
    parsed_output_dir = output_path.parent / "parsed" / rerun_run_id

    work_items: list[EvalWorkItem] = []
    rerun_of_run_id = str(filtered_manifest[0].get("run_id") or "")
    selected_roles = {str(item["role"]) for item in filtered_manifest}
    mode = mode_for_roles(selected_roles)

    for item in filtered_manifest:
        candidate = candidate_from_ref(str(item["model"]), index, roles={str(item["role"])}, include_judge=True)
        fixture = find_fixture_for_record(
            fixture_set="brain-model-test-v2",
            role=str(item["role"]),
            fixture_id=str(item["fixture_id"]),
            variant_id=str(item.get("variant_id") or "base"),
            mode=mode,
        )
        work_items.append(
            EvalWorkItem(
                candidate=candidate,
                fixture=fixture,
                repeat_idx=int(item.get("repeat_idx") or 0),
            )
        )

    rerun_records: list[dict[str, Any]] = []
    endpoint_limit = max(1, endpoint_max_concurrency)
    endpoint_keys = {item.candidate.endpoint_key for item in work_items}
    max_parallel_workers = min(len(work_items), max(1, len(endpoint_keys) * endpoint_limit))
    if max_parallel_workers <= 1:
        for item in work_items:
            rerun_records.append(
                evaluate_work_item(
                    active_client,
                    item=item,
                    run_id=rerun_run_id,
                    raw_output_dir=raw_output_dir,
                    parsed_output_dir=parsed_output_dir,
                    rerun_of_run_id=rerun_of_run_id,
                    rerun_timestamp=rerun_timestamp,
                )
            )
    else:
        endpoint_semaphores: dict[str, BoundedSemaphore] = {
            key: BoundedSemaphore(endpoint_limit) for key in {item.candidate.endpoint_key for item in work_items}
        }
        with ThreadPoolExecutor(max_workers=max_parallel_workers) as executor:
            futures = [
                executor.submit(
                    evaluate_work_item,
                    active_client,
                    item=item,
                    run_id=rerun_run_id,
                    raw_output_dir=raw_output_dir,
                    parsed_output_dir=parsed_output_dir,
                    rerun_of_run_id=rerun_of_run_id,
                    rerun_timestamp=rerun_timestamp,
                    endpoint_semaphore=endpoint_semaphores[item.candidate.endpoint_key],
                )
                for item in work_items
            ]
            for future in as_completed(futures):
                rerun_records.append(future.result())

    assign_failure_numbers(rerun_records)
    merged = merge_rerun_records(canonical_records, rerun_records)
    atomic_write_eval_records(output_path, merged)

    result = build_run_result(
        run_id=rerun_run_id,
        fixture_set="brain-model-test-v2",
        mode=mode,
        output_path=output_path,
        report_md_path=output_path.parent / "summary.md",
        records=merged,
        models=sorted({record["model"] for record in merged}),
        roles=sorted({record["role"] for record in merged}),
        bootstrap_samples=bootstrap_samples,
    )
    write_run_artifacts(result, merged)
    return result


def mode_for_roles(roles: set[str]) -> str:
    fine_grained_roles = {
        "intent_router",
        "source_classifier",
        "durability_filter",
        "memory_kind_classifier",
        "atomic_card_extractor",
        "entity_mention_extractor",
        "entity_candidate_ranker",
        "relationship_extractor",
        "open_loop_detector",
        "table_policy_handler",
        "source_takeaway_extractor",
        "conflict_candidate_detector",
        "conflict_explainer",
        "repair_option_generator",
        "success_receipt_generator",
        "recall_planner",
        "recall_synthesizer",
        "groundedness_checker",
        "debug_explainer",
        "eval_judge",
    }
    return "fine-grained" if roles & fine_grained_roles else "broad"


def find_fixture_for_record(
    *,
    fixture_set: str,
    role: str,
    fixture_id: str,
    variant_id: str,
    mode: str,
) -> ModelEvalFixture:
    fixtures = select_fixtures(fixture_set=fixture_set, roles={role}, mode=mode)
    for fixture in fixtures:
        base_fixture_id = str(fixture.context.get("base_fixture_id", fixture.id))
        fixture_variant = str(fixture.context.get("variant", "base"))
        if base_fixture_id == fixture_id and fixture_variant == variant_id and fixture.role == role:
            return fixture
    raise ValueError(
        f"fixture not found for role={role!r} fixture_id={fixture_id!r} variant_id={variant_id!r} mode={mode!r}"
    )


def failed_manifest_row(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_id": record.get("record_id"),
        "failure_number": record.get("failure_number"),
        "run_id": record.get("run_id"),
        "model": record.get("model"),
        "role": record.get("role"),
        "fixture_id": record.get("fixture_id"),
        "variant_id": record.get("variant_id"),
        "repeat_idx": record.get("repeat_idx"),
        "failure_class": record.get("failure_class"),
        "failure_reason_codes": record.get("failure_reason_codes") or record.get("notes") or [],
        "failure_message": record.get("failure_message"),
        "raw_output_path": record.get("raw_output_path"),
        "parsed_output_path": record.get("parsed_output_path"),
    }


def render_failed_tests_markdown(run_id: str, failed_records_: list[dict[str, Any]]) -> str:
    lines = ["# Failed tests", "", f"Run ID: `{run_id}`", ""]
    grouped: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for record in failed_records_:
        failure_class = str(record.get("failure_class"))
        grouped[failure_class][str(record.get("role"))][str(record.get("fixture_id"))].append(record)
    for failure_class in sorted(grouped):
        lines.extend([f"## {failure_class}", ""])
        for role in sorted(grouped[failure_class]):
            for fixture_id in sorted(grouped[failure_class][role]):
                lines.extend(
                    [
                        f"### {role} / {fixture_id}",
                        "",
                        "| Failure # | Model | Variant | Repeat | Reason |",
                        "|---:|---|---|---:|---|",
                    ]
                )
                for record in sorted(grouped[failure_class][role][fixture_id], key=lambda item: item.get("failure_number") or 0):
                    reason = ", ".join(record.get("failure_reason_codes") or record.get("notes") or []) or "-"
                    lines.append(
                        f"| {record.get('failure_number') or ''} | `{record.get('model')}` | "
                        f"`{record.get('variant_id')}` | {record.get('repeat_idx') or 0} | {reason} |"
                    )
                lines.append("")
    return "\n".join(lines)


def write_model_role_summary_csv(path: Path, summaries: list[Summary]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "model",
                "provider",
                "role",
                "role_category",
                "records_total",
                "operational_success_rate",
                "json_parse_success_rate",
                "schema_validity_rate",
                "semantic_evaluable_rate",
                "quality_pass_rate",
                "semantic_score_mean",
                "cost_per_1k_attempted",
                "cost_per_1k_successful",
                "cost_per_1k_semantic",
                "zero_tolerance_failures",
                "eligible",
                "rejection_reasons",
            ]
        )
        for summary in summaries:
            writer.writerow(
                [
                    summary.model,
                    summary.provider,
                    summary.role,
                    summary.role_category,
                    summary.records_total,
                    summary.operational_success_rate,
                    summary.json_parse_success_rate,
                    summary.schema_validity_rate,
                    summary.semantic_evaluable_rate,
                    summary.quality_pass_rate,
                    summary.semantic_score_mean,
                    summary.cost_per_1k_attempted,
                    summary.cost_per_1k_successful,
                    summary.cost_per_1k_semantic,
                    summary.zero_tolerance_failures,
                    summary.eligible,
                    ";".join(summary.rejection_reasons),
                ]
            )


def write_cost_latency_csv(path: Path, summaries: list[Summary]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "model",
                "role",
                "cost_per_1k_attempted",
                "cost_per_1k_successful",
                "cost_per_1k_semantic",
                "latency_p50_ms",
                "latency_p90_ms",
                "latency_p95_ms",
            ]
        )
        for summary in summaries:
            writer.writerow(
                [
                    summary.model,
                    summary.role,
                    summary.cost_per_1k_attempted,
                    summary.cost_per_1k_successful,
                    summary.cost_per_1k_semantic,
                    summary.latency_p50_ms,
                    summary.latency_p90_ms,
                    summary.latency_p95_ms,
                ]
            )


def write_zero_tolerance_csv(path: Path, summaries: list[Summary]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["model", "role", "zero_tolerance_failures", "zero_tolerance_upper_95_fail_rate", "eligible"])
        for summary in summaries:
            writer.writerow(
                [
                    summary.model,
                    summary.role,
                    summary.zero_tolerance_failures,
                    summary.zero_tolerance_upper_95_fail_rate,
                    summary.eligible,
                ]
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
    safe_role = fixture.role.replace(":", "_").replace("/", "_")
    path = raw_output_dir / f"{safe_model}__{safe_role}__{fixture.id}__{repeat_idx}.json"
    path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "model": candidate.ref,
                "role": fixture.role,
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
    safe_role = fixture.role.replace(":", "_").replace("/", "_")
    path = parsed_output_dir / f"{safe_model}__{safe_role}__{fixture.id}__{repeat_idx}.json"
    path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "model": candidate.ref,
                "role": fixture.role,
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
    mode = str(result.get("mode", "broad"))
    coverage = result.get("capability_coverage") or {}
    eligible_counts = result.get("eligible_counts_by_category") or eligible_counts_by_category(summaries)
    recommendations = result.get("partial_recommendations") or categorized_recommendations(summaries)["all"]
    mandatory_recommendations = result.get("recommended_stack") or categorized_recommendations(summaries)["mandatory"]
    non_deployable_section = (
        non_deployable_rows(summaries, missing_roles, coverage=coverage, mode=mode)
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
            f"- Eval mode: `{mode}`",
            f"- Fixture set: `{result['fixture_set']}`",
            f"- Canonical output: `{result['output_path']}`",
            f"- Failed manifest JSONL: `{result.get('failed_manifest_jsonl_path', '')}`",
            f"- Failed manifest markdown: `{result.get('failed_manifest_md_path', '')}`",
            f"- HTML summary: `{result.get('report_html_path', '')}`",
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
            "| Target | Required | Eligible models | Status |",
            "|---|---:|---|---|",
            *mandatory_role_rows(summaries, mode=mode, coverage=coverage),
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
            "| Model | Role | JSON parse success | 95% CI | Parseable / Operationally successful |",
            "|---|---|---:|---:|---:|",
            *parse_rows(summaries),
            "",
            "| Model | Role | Schema validity | 95% CI | Valid / Parseable |",
            "|---|---|---:|---:|---:|",
            *schema_rows(summaries),
            "",
            *schema_failure_summary(eval_records),
            "",
            "## Semantic evaluability",
            "",
            "| Model | Role | Semantic evaluable | 95% CI | Semantic-evaluable / Schema-valid |",
            "|---|---|---:|---:|---:|",
            *semantic_evaluable_rows(summaries),
            "",
            "## Safety / zero-tolerance failures",
            "",
            "| Model | Role | Zero-tolerance failures | Upper 95% fail rate | Eligible |",
            "|---|---|---:|---:|---|",
            *zero_tolerance_rows(summaries),
            "",
            "## Quality scores by role",
            "",
            "| Model | Role | Category | Quality pass | 95% CI | Passes / Semantic evals | Semantic score | 95% CI | Eligible | Rejection reasons |",
            "|---|---|---|---:|---:|---:|---:|---:|---|---|",
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
            "| Model | Role | Cost / 1k attempted | Cost / 1k successful | Cost / 1k semantic | p50 ms | p90 ms | p95 ms |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
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
            "## Rerun command",
            "",
            "```bash",
            rerun_command(result),
            "```",
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


def mandatory_role_rows(
    summaries: list[Summary],
    *,
    mode: str,
    coverage: dict[str, Any],
) -> list[str]:
    if mode == "fine-grained":
        rows: list[str] = []
        for capability in sorted(coverage):
            item = coverage[capability]
            model_parts: list[str] = []
            for role, models in sorted((item.get("eligible_models_by_role") or {}).items()):
                rendered_models = ", ".join(f"`{model}`" for model in models) if models else "none"
                model_parts.append(f"`{role}`: {rendered_models}")
            required = "no" if item.get("status") == "not_tested" else "yes"
            rows.append(
                f"| `{capability}` | {required} | {'; '.join(model_parts) or 'none'} | {str(item.get('status', 'missing')).upper()} |"
            )
        return rows

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


def parse_rows(summaries: list[Summary]) -> list[str]:
    return [
        "| "
        f"`{summary.model}` | `{summary.role}` | "
        f"{summary.json_parse_success_rate:.3f} | "
        f"{summary.json_parse_success_ci_low:.3f}-{summary.json_parse_success_ci_high:.3f} | "
        f"{summary.records_json_parseable} / {summary.records_operational_success} |"
        for summary in summaries
    ]


def schema_rows(summaries: list[Summary]) -> list[str]:
    return [
        "| "
        f"`{summary.model}` | `{summary.role}` | "
        f"{summary.schema_validity_rate:.3f} | "
        f"{summary.schema_validity_ci_low:.3f}-{summary.schema_validity_ci_high:.3f} | "
        f"{summary.records_schema_valid} / {summary.records_json_parseable} |"
        for summary in summaries
    ]


def semantic_evaluable_rows(summaries: list[Summary]) -> list[str]:
    return [
        "| "
        f"`{summary.model}` | `{summary.role}` | "
        f"{summary.semantic_evaluable_rate:.3f} | "
        f"{summary.semantic_evaluable_ci_low:.3f}-{summary.semantic_evaluable_ci_high:.3f} | "
        f"{summary.records_semantic_evaluable} / {summary.records_schema_valid} |"
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
            f"{summary.quality_pass_rate:.3f} | {summary.quality_pass_ci_low:.3f}-{summary.quality_pass_ci_high:.3f} | "
            f"{summary.records_quality_passed} / {summary.records_semantic_evaluable} | "
            f"{semantic_mean} | {semantic_ci} | "
            f"{summary.eligible} | {reasons} |"
        )
    return rows


def render_html_report(markdown_report: str, *, title: str) -> str:
    body = markdown_to_html(markdown_report)
    escaped_title = html.escape(title)
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            f"  <title>{escaped_title}</title>",
            "  <style>",
            "    :root { color-scheme: light; --bg: #f5f1e8; --panel: #fffdf8; --ink: #1d1b16; --muted: #635b4f; --line: #d8cdb9; --accent: #0f766e; --accent-soft: #dff3ef; }",
            "    * { box-sizing: border-box; }",
            "    body { margin: 0; padding: 32px; background: radial-gradient(circle at top, #fff8eb 0%, var(--bg) 55%, #efe6d5 100%); color: var(--ink); font-family: Georgia, 'Iowan Old Style', serif; line-height: 1.6; }",
            "    main { max-width: 1180px; margin: 0 auto; background: color-mix(in srgb, var(--panel) 96%, white 4%); border: 1px solid var(--line); border-radius: 24px; padding: 32px; box-shadow: 0 24px 70px rgba(76, 59, 29, 0.12); }",
            "    h1, h2, h3 { font-family: 'Palatino Linotype', 'Book Antiqua', Palatino, serif; line-height: 1.2; }",
            "    h1 { margin-top: 0; font-size: 2.5rem; }",
            "    h2 { margin-top: 2.5rem; padding-top: 1.25rem; border-top: 1px solid var(--line); font-size: 1.65rem; }",
            "    h3 { margin-top: 1.5rem; font-size: 1.2rem; }",
            "    p, li { font-size: 1rem; }",
            "    ul { padding-left: 1.2rem; }",
            "    code { font-family: 'SFMono-Regular', Consolas, monospace; background: var(--accent-soft); border-radius: 6px; padding: 0.1rem 0.35rem; font-size: 0.92em; }",
            "    pre { background: #1f2937; color: #f9fafb; padding: 16px; border-radius: 14px; overflow-x: auto; }",
            "    pre code { background: transparent; padding: 0; color: inherit; }",
            "    table { width: 100%; border-collapse: collapse; margin: 1rem 0 1.4rem; font-size: 0.95rem; }",
            "    th, td { border: 1px solid var(--line); padding: 10px 12px; vertical-align: top; text-align: left; }",
            "    th { background: #f1e7d7; }",
            "    tr:nth-child(even) td { background: rgba(241, 231, 215, 0.34); }",
            "    strong { color: var(--accent); }",
            "  </style>",
            "</head>",
            "<body>",
            "  <main>",
            body,
            "  </main>",
            "</body>",
            "</html>",
        ]
    )


def markdown_to_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    html_lines: list[str] = []
    paragraph_buffer: list[str] = []
    list_buffer: list[str] = []
    table_buffer: list[str] = []
    code_buffer: list[str] = []
    in_code = False

    def flush_paragraph() -> None:
        nonlocal paragraph_buffer
        if not paragraph_buffer:
            return
        html_lines.append(f"<p>{format_inline_markdown(' '.join(paragraph_buffer))}</p>")
        paragraph_buffer = []

    def flush_list() -> None:
        nonlocal list_buffer
        if not list_buffer:
            return
        html_lines.append("<ul>")
        for item in list_buffer:
            html_lines.append(f"<li>{format_inline_markdown(item)}</li>")
        html_lines.append("</ul>")
        list_buffer = []

    def flush_table() -> None:
        nonlocal table_buffer
        if len(table_buffer) < 2:
            for line in table_buffer:
                html_lines.append(f"<p>{format_inline_markdown(line)}</p>")
            table_buffer = []
            return
        rows = [split_markdown_table_row(line) for line in table_buffer if line.strip()]
        if len(rows) < 2:
            table_buffer = []
            return
        header = rows[0]
        body_rows = rows[2:] if len(rows) > 2 else []
        html_lines.append("<table>")
        html_lines.append("<thead><tr>")
        for cell in header:
            html_lines.append(f"<th>{format_inline_markdown(cell)}</th>")
        html_lines.append("</tr></thead>")
        html_lines.append("<tbody>")
        for row in body_rows:
            html_lines.append("<tr>")
            for cell in row:
                html_lines.append(f"<td>{format_inline_markdown(cell)}</td>")
            html_lines.append("</tr>")
        html_lines.append("</tbody></table>")
        table_buffer = []

    def flush_code() -> None:
        nonlocal code_buffer
        if not code_buffer:
            return
        html_lines.append("<pre><code>")
        html_lines.append(html.escape("\n".join(code_buffer)))
        html_lines.append("</code></pre>")
        code_buffer = []

    def flush_blocks() -> None:
        flush_paragraph()
        flush_list()
        flush_table()

    for line in lines:
        if line.startswith("```"):
            if in_code:
                flush_code()
            else:
                flush_blocks()
            in_code = not in_code
            continue
        if in_code:
            code_buffer.append(line)
            continue
        if line.lstrip().startswith("|"):
            flush_paragraph()
            flush_list()
            table_buffer.append(line)
            continue
        if not line.strip():
            flush_blocks()
            continue
        if line.startswith("#"):
            flush_blocks()
            level = min(6, len(line) - len(line.lstrip("#")))
            content = line[level:].strip()
            html_lines.append(f"<h{level}>{format_inline_markdown(content)}</h{level}>")
            continue
        if line.startswith("- "):
            flush_paragraph()
            flush_table()
            list_buffer.append(line[2:].strip())
            continue
        flush_list()
        flush_table()
        paragraph_buffer.append(line.strip())

    if in_code:
        flush_code()
    flush_blocks()
    return "\n".join(html_lines)


def split_markdown_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def format_inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


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
        attempted = "n/a" if summary.cost_per_1k_attempted is None else f"${summary.cost_per_1k_attempted:.4f}"
        successful = "n/a" if summary.cost_per_1k_successful is None else f"${summary.cost_per_1k_successful:.4f}"
        semantic = "n/a" if summary.cost_per_1k_semantic is None else f"${summary.cost_per_1k_semantic:.4f}"
        p50 = "n/a" if summary.latency_p50_ms is None else f"{summary.latency_p50_ms:.0f}"
        p90 = "n/a" if summary.latency_p90_ms is None else f"{summary.latency_p90_ms:.0f}"
        p95 = "n/a" if summary.latency_p95_ms is None else f"{summary.latency_p95_ms:.0f}"
        rows.append(
            f"| `{summary.model}` | `{summary.role}` | {attempted} | {successful} | {semantic} | {p50} | {p90} | {p95} |"
        )
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


def non_deployable_rows(
    summaries: list[Summary],
    missing_roles: list[str],
    *,
    coverage: dict[str, Any],
    mode: str,
) -> list[str]:
    if not missing_roles:
        return ["Mandatory coverage is complete."]
    if mode == "fine-grained":
        rows = ["Missing mandatory capabilities:"]
        rows.extend(format_role_list(missing_roles))
        rows.append("")
        rows.append("Observed capability gaps:")
        for capability in missing_roles:
            item = coverage.get(capability) or {}
            missing_model_roles = item.get("missing_roles") or []
            if missing_model_roles:
                rows.append(
                    f"- `{capability}`: missing eligible coverage for {', '.join(f'`{role}`' for role in missing_model_roles)}"
                )
            else:
                rows.append(f"- `{capability}`: capability coverage is incomplete.")
        return rows
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


def rerun_command(result: dict[str, Any]) -> str:
    return (
        "brain eval rerun-failed "
        f"--source-json {result['output_path']} "
        f"--failed-manifest {result.get('failed_manifest_jsonl_path', '')} "
        "--endpoint-max-concurrency 3 "
        f"--output-json {result['output_path']} "
        "--overwrite"
    )
