from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
import inspect
import json
import logging
import re
from typing import Any
from uuid import UUID

from memory_stack.brain_models import (
    EntityReceipt,
    IngestSourceRequest,
    IngestionReceipt,
    RecallRequest,
    RecallResponse,
    RememberRequest,
)
from memory_stack.brain_store import BrainStore, content_hash, stable_id
from memory_stack.cognee.datapoints import (
    client_session_id_from_context,
    common_node_sets,
    datapoint_text,
    profile_name_from_context,
    status_event_datapoint,
    status_event_node_sets,
    surface_from_context,
)
from memory_stack.cognee_adapter import forget_cognee as _cognee_forget
from memory_stack.cognee_adapter import remember_text as _cognee_remember_text
from memory_stack.cognee_adapter import recall_text as _cognee_recall_text
from memory_stack.cognee_adapter import run_async
from memory_stack.cfg import Settings
from memory_stack.ingestion.classifier import input_type_for_source_kind
from memory_stack.llm.client import LLMClient, build_llm_client
from memory_stack.profile_context import list_profile_context
from memory_stack.recall.evidence_builder import build_evidence, build_facts
from memory_stack.recall.planner import extract_profile_name, infer_recall_mode
from memory_stack.recall.retriever import retrieve_memories
from memory_stack.recall.synthesizer import render_memory_answer
from memory_stack.route_logging import log_taste_route
from memory_stack.taste.models import TasteQueryRequest
from memory_stack.taste.routing import classify_palate_memory_route, classify_taste_route
from memory_stack.taste.cognee_store import CogneePalateStore
from memory_stack.taste.service import TasteService, remember_request_from_route


_LOGGER = logging.getLogger(__name__)
_INGEST_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="brain-ingest")


def _submit_background_ingest(
    request: IngestSourceRequest,
    settings: Settings,
    *,
    llm_client: LLMClient | None = None,
) -> Future[IngestionReceipt]:
    future = _INGEST_EXECUTOR.submit(
        ingest_source,
        request,
        settings,
        llm_client=llm_client,
    )
    future.add_done_callback(_log_background_ingest_result)
    return future


def _log_background_ingest_result(future: Future[IngestionReceipt]) -> None:
    try:
        receipt = future.result()
    except Exception:
        _LOGGER.exception("Background source ingestion failed.")
        return
    _LOGGER.info("Background source ingestion completed: %s", receipt.ingestion_run_id)


def _queued_ingestion_receipt(request: IngestSourceRequest) -> IngestionReceipt:
    source_text = request.source
    source_type = request.source_kind
    return IngestionReceipt(
        ingestion_run_id=stable_id("queued_ing", content_hash(source_text, source_type)),
        classification="queued",
        cognee_sync_status="queued",
        dry_run=request.dry_run,
    )


def _remember_request_from_ingest_source(request: IngestSourceRequest) -> RememberRequest:
    return RememberRequest(
        input=request.source,
        input_type=input_type_for_source_kind(request.source_kind, request.source),
        dry_run=request.dry_run,
        context={
            "title": request.title,
            "why_saved": request.why_saved,
            "metadata": request.metadata,
            **request.context,
            "source_kind": request.source_kind,
            "taste_skip": True,
            "source_ingest": True,
        },
    )


def _should_run_ingest_in_background(
    request: IngestSourceRequest,
    remember_request: RememberRequest,
    settings: Settings,
) -> bool:
    if request.run_in_background is not None:
        return request.run_in_background
    if remember_request.dry_run:
        return False
    threshold = settings.brain_ingest_background_auto_chars
    return threshold > 0 and len(remember_request.input) > threshold


def _raw_classification(request: RememberRequest) -> str:
    if request.context.get("source_ingest"):
        source_kind = str(request.context.get("source_kind") or "auto")
        return input_type_for_source_kind(source_kind, request.input)
    return request.input_type if request.input_type != "auto" else "direct_memory"


def _cognee_dataset_for_raw_write(settings: Settings) -> str:
    return settings.brain_cognee_memory_dataset


def _raw_dry_run_receipt(
    *,
    request: RememberRequest,
    run_id: str,
    settings: Settings,
) -> IngestionReceipt:
    classification = _raw_classification(request)
    if request.context.get("confirmation_required"):
        store = BrainStore(settings)
        action = "ingest_source" if request.context.get("source_ingest") else "remember"
        confirmation = store.create_pending_confirmation(
            surface=str(request.context.get("confirmation_surface") or surface_from_context(request.context)),
            action=action,
            original_input=request.input,
            proposed_payload_json={
                "classification": classification,
                "text_hash": content_hash(request.input),
                "cognee_operation": "remember",
            },
            reason="Explicit user confirmation is required before committing this durable write.",
            options_json=["confirm", "cancel"],
            metadata_json={
                "context": request.context,
                "semantic_compiler": "cognee",
                "brain_db_semantic_rows_written": False,
            },
        )
        run_id = confirmation["id"]
    return IngestionReceipt(
        ingestion_run_id=run_id,
        classification=classification,
        cognee_sync_status="not_applicable",
        dry_run=True,
    )


def _write_raw_to_cognee(
    *,
    request: RememberRequest,
    settings: Settings,
) -> IngestionReceipt:
    store = BrainStore(settings)
    profile_name = profile_name_from_context(request.context, settings)
    surface = surface_from_context(request.context)
    client_session_id = client_session_id_from_context(request.context)
    base_node_sets = common_node_sets(user_id=store.user_id, profile_name=profile_name)
    classification = _raw_classification(request)
    tool_name = "brain_ingest_source" if request.context.get("source_ingest") else "brain_remember"
    action = "ingest_source" if request.context.get("source_ingest") else "remember"
    primary_dataset = _cognee_dataset_for_raw_write(settings)
    session_map = store.get_or_create_session_map(
        profile_name=profile_name,
        surface=surface,
        client_session_id=client_session_id,
        cognee_dataset=primary_dataset,
        node_sets_json=base_node_sets,
        metadata_json={
            "classification": classification,
            "semantic_compiler": "cognee",
        },
    )
    cognee_results: list[dict[str, Any]] = []
    datasets: list[str] = []

    try:
        content_hash_value = content_hash("cognee_remember", request.input)
        cognee_remember_id = store.make_external_id("cog", "remember", content_hash_value)
        node_sets = common_node_sets(user_id=store.user_id, profile_name=profile_name)
        cognee_result = _call_cognee_remember_text(
            request.input,
            dataset_name=primary_dataset,
            node_set=node_sets,
            settings=settings,
        )
        datasets.append(primary_dataset)
        cognee_results.append(
            {
                "object_type": "cognee_remember",
                "external_id": cognee_remember_id,
                "content_hash": content_hash_value,
                "dataset": primary_dataset,
                "operation": "remember",
                "node_sets": node_sets,
                "cognee_result": _json_safe(cognee_result),
            }
        )
    except Exception as exc:
        failure_receipt = store.create_external_receipt(
            surface=surface,
            tool_name=tool_name,
            action=action,
            status="failed",
            summary=f"Cognee write failed for {classification}.",
            cognee_dataset=",".join(sorted(set(datasets))) if datasets else None,
            cognee_reference=_combined_cognee_reference(cognee_results),
            cognee_result_json={
                "session_map": session_map,
                "objects": cognee_results,
            },
            warnings_json=[str(exc)],
            metadata_json={
                "classification": classification,
                "context": request.context,
                "semantic_compiler": "cognee",
                "brain_db_semantic_rows_written": False,
            },
        )
        raise RuntimeError(
            "Cognee durable write failed; Brain semantic fallback is disabled "
            f"(receipt_id={failure_receipt['id']}): {exc}"
        ) from exc

    status = "synced" if cognee_results else "not_applicable"
    receipt = store.create_external_receipt(
        surface=surface,
        tool_name=tool_name,
        action=action,
        status=status,
        summary=f"Stored raw text once in Cognee dataset: {', '.join(sorted(set(datasets))) or 'none'}.",
        cognee_dataset=",".join(sorted(set(datasets))) if datasets else None,
        cognee_reference=_combined_cognee_reference(cognee_results),
        cognee_result_json={
            "session_map": session_map,
            "objects": cognee_results,
        },
        metadata_json={
            "classification": classification,
            "context": request.context,
            "semantic_compiler": "cognee",
            "brain_db_semantic_rows_written": False,
        },
    )
    return IngestionReceipt(
        ingestion_run_id=receipt["id"],
        classification=classification,
        cognee_sync_status=status,
        dry_run=False,
    )


def _call_cognee_remember_text(
    text: str,
    *,
    dataset_name: str,
    node_set: list[str],
    settings: Settings,
) -> Any:
    result = _cognee_remember_text(
        text,
        dataset_name=dataset_name,
        node_set=node_set,
        settings=settings,
    )
    if inspect.isawaitable(result):
        return run_async(result)
    return result


def _call_cognee_forget(
    *,
    data_id: str | UUID | None = None,
    dataset: str | UUID | None = None,
    everything: bool = False,
    memory_only: bool = False,
    settings: Settings,
) -> Any:
    result = _cognee_forget(
        data_id=data_id,
        dataset=dataset,
        everything=everything,
        memory_only=memory_only,
        settings=settings,
    )
    if inspect.isawaitable(result):
        return run_async(result)
    return result


def _call_cognee_recall_text(
    *,
    query: str,
    dataset: str,
    search_type: str = "CHUNKS",
    top_k: int = 10,
    settings: Settings,
) -> Any:
    result = _cognee_recall_text(
        query=query,
        dataset=dataset,
        search_type=search_type,
        top_k=top_k,
        settings=settings,
    )
    if inspect.isawaitable(result):
        return run_async(result)
    return result


def _combined_cognee_reference(results: list[dict[str, Any]]) -> str | None:
    references = [
        reference
        for result in results
        if (reference := _cognee_reference(result.get("cognee_result"))) is not None
    ]
    if not references:
        return None
    return ",".join(references)


def _cognee_reference(result: Any) -> str | None:
    if result is None:
        return None
    if isinstance(result, dict):
        for key in ("id", "data_id", "dataset_id", "pipeline_run_id", "cognee_reference", "reference", "name"):
            value = result.get(key)
            if value:
                return str(value)
        items = result.get("items")
        if isinstance(items, list) and items:
            return _cognee_reference(items[0])
    if isinstance(result, list) and result:
        return _cognee_reference(result[0])
    return str(result)[:200]


def _json_safe(value: Any) -> Any:
    def default(item: Any) -> Any:
        if hasattr(item, "to_dict"):
            return item.to_dict()
        return str(item)

    return json.loads(json.dumps(value, ensure_ascii=True, sort_keys=True, default=default))


def remember(
    request: RememberRequest,
    settings: Settings,
    *,
    llm_client: LLMClient | None = None,
) -> IngestionReceipt:
    if settings.brain_taste_enabled and not request.context.get("taste_skip"):
        if request.context.get("palate") is True:
            active_llm_client = llm_client or build_llm_client(settings)
            route = classify_palate_memory_route(
                request.input,
                context=request.context,
                settings=settings,
                llm_client=active_llm_client,
            )
            log_taste_route(request.input, route, settings)
            taste_service = TasteService(settings, llm_client=active_llm_client)
            if (
                route.get("domain") == "taste"
                and route.get("taste_intent") == "remember"
                and float(route.get("confidence") or 0) >= settings.brain_taste_auto_write_threshold
            ):
                taste_result = taste_service.remember(
                    remember_request_from_route(request.input, route).model_copy(
                        update={"dry_run": request.dry_run, "context": request.context}
                    )
                )
                return taste_result_to_ingestion_receipt(taste_result, settings, route)
            proposal = taste_service.create_proposal_from_text(
                request.input,
                route=route,
                source_metadata={"context": request.context, "forced_palate": True},
            )
            return IngestionReceipt(
                ingestion_run_id=proposal["id"],
                classification="taste_proposal",
                dry_run=True,
                taste={
                    "requires_confirmation": True,
                    "proposal_id": proposal["id"],
                    "proposal": proposal["proposal_json"],
                    "warnings": proposal["warnings_json"],
                },
            )
        route = classify_taste_route(request.input, settings=settings, llm_client=llm_client)
        log_taste_route(request.input, route, settings)
        if route.get("taste_intent") == "remember" and route.get("domain") in {"taste", "ambiguous"}:
            taste_service = TasteService(settings, llm_client=llm_client)
            if (
                route.get("domain") == "taste"
                and float(route.get("confidence") or 0) >= settings.brain_taste_auto_write_threshold
            ):
                taste_result = taste_service.remember(
                    remember_request_from_route(request.input, route).model_copy(
                        update={"dry_run": request.dry_run, "context": request.context}
                    )
                )
                return taste_result_to_ingestion_receipt(taste_result, settings, route)
            if float(route.get("confidence") or 0) >= settings.brain_taste_confirmation_threshold:
                proposal = taste_service.create_proposal_from_text(
                    request.input,
                    route=route,
                    source_metadata={"context": request.context},
                )
                return IngestionReceipt(
                    ingestion_run_id=proposal["id"],
                    classification="taste_proposal",
                    dry_run=True,
                    taste={
                        "requires_confirmation": True,
                        "proposal_id": proposal["id"],
                        "proposal": proposal["proposal_json"],
                        "warnings": proposal["warnings_json"],
                    },
                )

    input_hash = content_hash(request.input, request.input_type, request.context)
    run_id = stable_id("dry_ing", input_hash)
    if request.dry_run:
        return _raw_dry_run_receipt(
            request=request,
            run_id=run_id,
            settings=settings,
        )

    return _write_raw_to_cognee(
        request=request,
        settings=settings,
    )


def ingest_source(
    request: IngestSourceRequest,
    settings: Settings,
    *,
    llm_client: LLMClient | None = None,
) -> IngestionReceipt:
    remember_request = _remember_request_from_ingest_source(request)
    if _should_run_ingest_in_background(request, remember_request, settings):
        queued_request = request.model_copy(update={"run_in_background": False})
        _submit_background_ingest(
            queued_request,
            settings,
            llm_client=llm_client,
        )
        return _queued_ingestion_receipt(request)

    receipt = remember(remember_request, settings, llm_client=llm_client)
    if settings.brain_taste_enabled:
        candidates = taste_source_candidates(request.source, settings=settings, llm_client=llm_client)
        if candidates:
            taste_service = TasteService(settings, llm_client=llm_client)
            proposal_ids = []
            if len(candidates) <= 3 and not request.dry_run:
                for candidate in candidates:
                    proposal = taste_service.create_proposal_from_text(
                        candidate["text"],
                        route=candidate["route"],
                        source_metadata={
                            "source_ingest": True,
                            "title": request.title,
                            "source_kind": request.source_kind,
                        },
                    )
                    proposal_ids.append(proposal["id"])
                policy = "candidate_proposals"
            elif len(candidates) <= 10:
                policy = "structured_candidate_selection"
                if not request.dry_run:
                    proposal = taste_service.store.create_proposal(
                        original_text=request.source,
                        proposal={
                            "route": {
                                "domain": "taste",
                                "taste_intent": "remember",
                                "confidence": max(
                                    float(candidate.get("confidence") or 0)
                                    for candidate in candidates
                                ),
                                "requires_enrichment": True,
                                "requires_confirmation": True,
                                "ambiguity_reasons": [
                                    "Multiple taste candidates were found in one source."
                                ],
                            },
                            "source_candidates": candidates,
                            "selection_required": True,
                            "proposed_taste_records": [],
                            "proposed_brain_entities": [],
                            "allowed_actions": ["confirm", "cancel", "correct"],
                        },
                        warnings=[
                            "Select which taste candidates to enrich or store; "
                            "Brain does not mass-enrich source mentions automatically."
                        ],
                        source_metadata={
                            "source_ingest": True,
                            "title": request.title,
                            "source_kind": request.source_kind,
                            "candidate_count": len(candidates),
                        },
                    )
                    proposal_ids.append(proposal["id"])
            else:
                policy = "selection_required"
            receipt.taste = {
                "source_ingestion_policy": policy,
                "candidate_count": len(candidates),
                "candidates": candidates[:10],
                "proposal_ids": proposal_ids,
                "mass_enrichment_skipped": True,
            }
    return receipt


def recall(
    request: RecallRequest,
    settings: Settings,
    *,
    cognee_searcher: Any = None,
) -> RecallResponse:
    store = BrainStore(settings)
    query = request.query.strip()
    if settings.brain_taste_enabled and should_route_recall_to_taste(query):
        taste_result = TasteService(settings).query(TasteQueryRequest(query=query))
        return RecallResponse(
            answer=taste_result.get("answer") or "No matching taste records found.",
            facts=[
                {
                    "taste_item_id": item.get("id"),
                    "statement": item.get("name"),
                    "score": item.get("score"),
                }
                for item in taste_result.get("ranked_results", [])
            ],
            evidence=taste_result.get("ranked_results", []),
            taste=taste_result,
        )
    mode = request.mode if request.mode != "auto" else infer_recall_mode(query)
    if mode == "profile":
        name = extract_profile_name(query)
        owner_names = {
            settings.brain_owner_name.casefold(),
            settings.brain_owner_full_name.casefold(),
            "me",
            "myself",
            "the user",
            "profile owner",
        }
        if name.strip().casefold() in {value for value in owner_names if value}:
            records = list_profile_context(settings)
            if records:
                facts = [
                    {
                        "context_id": record["id"],
                        "kind": record.get("kind", "profile"),
                        "statement": record["statement"],
                        "status": record.get("status", "current"),
                        "scope": record.get("scope"),
                    }
                    for record in records
                ]
                evidence = [
                    {
                        "context_id": record["id"],
                        "quote": record["statement"],
                        "source": record.get("source"),
                        "status": record.get("status", "current"),
                    }
                    for record in records
                ]
                answer = "Profile context\n" + "\n".join(
                    f"- {record['statement']} [{record['id']}; {record.get('scope')}]"
                    for record in records
                )
                return RecallResponse(answer=answer, facts=facts, evidence=evidence)
        return RecallResponse(answer=f"No profile context found for {name}.")

    memories = retrieve_memories(
        store,
        query,
        settings=settings,
        cognee_searcher=cognee_searcher,
        include_superseded=request.include_superseded,
        include_conflicts=request.include_conflicts,
        limit=request.limit,
    )
    facts = build_facts(memories)
    evidence = build_evidence(memories)
    answer = render_memory_answer(memories)
    taste_evidence = collect_taste_evidence(settings, memories)
    return RecallResponse(answer=answer, facts=facts, evidence=evidence, taste=taste_evidence)


def profile_entity(
    settings: Settings,
    *,
    name: str,
    entity_type: str | None = None,
    include_superseded: bool = False,
    include_conflicts: bool = True,
) -> RecallResponse:
    del entity_type, include_superseded, include_conflicts
    owner_names = {
        settings.brain_owner_name.casefold(),
        settings.brain_owner_full_name.casefold(),
        "me",
        "myself",
        "the user",
        "profile owner",
    }
    if name.strip().casefold() in {value for value in owner_names if value}:
        records = list_profile_context(settings)
        if records:
            facts = [
                {
                    "context_id": record["id"],
                    "kind": record.get("kind", "profile"),
                    "statement": record["statement"],
                    "status": record.get("status", "current"),
                    "scope": record.get("scope"),
                }
                for record in records
            ]
            evidence = [
                {
                    "context_id": record["id"],
                    "quote": record["statement"],
                    "source": record.get("source"),
                    "status": record.get("status", "current"),
                }
                for record in records
            ]
            answer = "Profile context\n" + "\n".join(
                f"- {record['statement']} [{record['id']}; {record.get('scope')}]"
                for record in records
            )
            return RecallResponse(answer=answer, facts=facts, evidence=evidence)
    return RecallResponse(answer=f"No profile context found for {name}.")


def forget(
    settings: Settings,
    *,
    object_type: str,
    object_id: str,
    hard: bool = False,
    reason: str | None = None,
) -> dict[str, Any]:
    if hard:
        raise ValueError("Hard delete is intentionally not implemented at the service layer.")
    store = BrainStore(settings)
    if object_type == "cognee_remember":
        source_receipt, targets = _find_receipt_targets_for_object(
            store,
            object_type=object_type,
            object_id=object_id,
        )
        if source_receipt is None:
            return {
                "object_type": object_type,
                "object_id": object_id,
                "status": "not_found",
                "receipt_id": None,
                "source_receipt_id": None,
                "forget_results": [],
                "status_events": [],
                "mode": "receipt",
                "cognee_sync_status": "not_applicable",
            }
        forget_results, status_events, cognee_failures = _forget_targets_with_audit(
            store=store,
            settings=settings,
            source_receipt=source_receipt,
            targets=targets,
            action="brain_forget",
            reason=reason or "Forget requested through Brain admin tool.",
        )
        receipt = store.create_external_receipt(
            surface="admin",
            tool_name="brain_forget",
            action="forget",
            status="deleted" if not cognee_failures else "failed",
            summary=f"Forget requested for {object_type} {object_id}.",
            cognee_dataset=_target_dataset_summary(targets),
            cognee_reference=source_receipt.get("cognee_reference"),
            cognee_result_json={
                "source_receipt": source_receipt,
                "targets": targets,
                "forget_results": forget_results,
                "status_events": status_events,
            },
            warnings_json=cognee_failures,
            metadata_json={
                "brain_db_semantic_rows_written": False,
                "source_receipt_id": source_receipt["id"],
                "reason": reason,
            },
        )
        return {
            "object_type": object_type,
            "object_id": object_id,
            "status": "deleted" if not cognee_failures else "failed",
            "receipt_id": receipt["id"],
            "source_receipt_id": source_receipt["id"],
            "forget_results": forget_results,
            "status_events": status_events,
            "warnings": cognee_failures,
            "mode": "receipt",
            "cognee_sync_status": "synced" if not cognee_failures else "failed",
        }

    deleted = store.forget(object_type=object_type, object_id=object_id, hard=hard)
    return {
        "object_type": object_type,
        "object_id": object_id,
        "status": "deleted" if deleted else "not_found",
    }


def review_recent(
    settings: Settings,
    *,
    since: datetime | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    store = BrainStore(settings)
    receipts = store.list_external_receipts(since=since, limit=limit)
    pending_confirmations = store.list_pending_confirmations(status=None, limit=limit)
    context_records = [
        *store.list_context_records(kind="profile", limit=limit),
        *store.list_context_records(kind="bias", limit=limit),
    ][:limit]
    return {
        "external_receipts": receipts,
        "pending_confirmations": pending_confirmations,
        "context_records": context_records,
        "conflicts": [],
    }


def undo_last(
    settings: Settings,
    *,
    ingestion_run_id: str | None = None,
) -> dict[str, Any]:
    store = BrainStore(settings)
    receipt = (
        store.get_external_receipt(ingestion_run_id)
        if ingestion_run_id
        else _latest_undoable_receipt(store)
    )
    if receipt is None:
        return {
            "status": "not_found",
            "ingestion_run_id": ingestion_run_id,
            "receipt_id": None,
            "deleted_objects": [],
            "forget_results": [],
            "status_events": [],
            "mode": "receipt",
            "cognee_sync_status": "not_applicable",
        }

    targets = _receipt_cognee_objects(receipt)
    forget_results, status_events, cognee_failures = _forget_targets_with_audit(
        store=store,
        settings=settings,
        source_receipt=receipt,
        targets=targets,
        action="undo_last",
        reason="Undo requested through Brain admin tool.",
    )
    forgotten_targets = {
        result["target_external_id"]
        for result in forget_results
        if result.get("status") == "forgotten"
    }
    deleted_objects = [
        target["external_id"]
        for target in targets
        if target["external_id"] in forgotten_targets
    ]

    undo_receipt = store.create_external_receipt(
        surface="admin",
        tool_name="brain_undo_last",
        action="undo_last",
        status="undone" if not cognee_failures else "failed",
        summary=f"Undo requested for receipt {receipt['id']}.",
        cognee_dataset=_target_dataset_summary(targets),
        cognee_reference=receipt.get("cognee_reference"),
        cognee_result_json={
            "source_receipt": receipt,
            "targets": targets,
            "forget_results": forget_results,
            "status_events": status_events,
        },
        warnings_json=cognee_failures,
        metadata_json={
            "brain_db_semantic_rows_written": False,
            "source_receipt_id": receipt["id"],
        },
    )
    if cognee_failures:
        return {
            "status": "failed",
            "ingestion_run_id": receipt["id"],
            "receipt_id": undo_receipt["id"],
            "source_receipt_id": receipt["id"],
            "deleted_objects": deleted_objects,
            "forget_results": forget_results,
            "status_events": status_events,
            "warnings": cognee_failures,
            "mode": "receipt",
            "cognee_sync_status": "failed",
        }
    return {
        "status": "undone",
        "ingestion_run_id": receipt["id"],
        "receipt_id": undo_receipt["id"],
        "source_receipt_id": receipt["id"],
        "deleted_objects": deleted_objects,
        "forget_results": forget_results,
        "status_events": status_events,
        "mode": "receipt",
        "cognee_sync_status": "synced" if status_events else "not_applicable",
    }


def _forget_targets_with_audit(
    *,
    store: BrainStore,
    settings: Settings,
    source_receipt: dict[str, Any],
    targets: list[dict[str, Any]],
    action: str,
    reason: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    forget_results: list[dict[str, Any]] = []
    status_events: list[dict[str, Any]] = []
    cognee_failures: list[str] = []
    if not targets:
        return forget_results, status_events, cognee_failures

    for target in targets:
        dataset = str(target.get("dataset") or settings.brain_cognee_memory_dataset)
        target_external_id = str(target["external_id"])
        data_id = _target_cognee_data_id(target)
        if data_id is None:
            message = (
                "Cannot call cognee.forget for "
                f"{target.get('object_type')} {target_external_id}: missing Cognee data item id."
            )
            cognee_failures.append(message)
            forget_results.append(
                {
                    "target_external_id": target_external_id,
                    "object_type": target.get("object_type"),
                    "dataset": dataset,
                    "status": "skipped",
                    "reason": "missing_cognee_data_id",
                }
            )
            continue

        try:
            forget_result = _call_cognee_forget(
                data_id=data_id,
                dataset=dataset,
                settings=settings,
            )
        except Exception as exc:
            cognee_failures.append(
                f"cognee.forget failed for {target.get('object_type')} "
                f"{target_external_id}: {exc}"
            )
            forget_results.append(
                {
                    "target_external_id": target_external_id,
                    "object_type": target.get("object_type"),
                    "dataset": dataset,
                    "data_id": data_id,
                    "status": "failed",
                    "error": str(exc),
                }
            )
            continue

        forget_results.append(
            {
                "target_external_id": target_external_id,
                "object_type": target.get("object_type"),
                "dataset": dataset,
                "data_id": data_id,
                "status": "forgotten",
                "cognee_result": _json_safe(forget_result),
            }
        )
        try:
            status_events.append(
                _write_forget_status_event(
                    store=store,
                    settings=settings,
                    source_receipt=source_receipt,
                    target=target,
                    dataset=dataset,
                    action=action,
                    reason=reason,
                    data_id=data_id,
                    forget_result=forget_result,
                )
            )
        except Exception as exc:
            cognee_failures.append(
                f"status-event audit write failed after cognee.forget for "
                f"{target.get('object_type')} {target_external_id}: {exc}"
            )
    return forget_results, status_events, cognee_failures


def _write_forget_status_event(
    *,
    store: BrainStore,
    settings: Settings,
    source_receipt: dict[str, Any],
    target: dict[str, Any],
    dataset: str,
    action: str,
    reason: str,
    data_id: str,
    forget_result: Any,
) -> dict[str, Any]:
    event_id = store.make_external_id(
        "evt",
        action,
        source_receipt["id"],
        target.get("external_id"),
        datetime.now().isoformat(),
    )
    payload = status_event_datapoint(
        external_id=event_id,
        receipt_id=source_receipt["id"],
        target_external_id=str(target["external_id"]),
        action=action,
        status="deleted",
        reason=reason,
        timestamp=datetime.now().astimezone(),
        metadata={
            "source_receipt_id": source_receipt["id"],
            "source_action": source_receipt.get("action"),
            "object_type": target.get("object_type"),
            "dataset": dataset,
            "cognee_data_id": data_id,
            "cognee_forget_result": _json_safe(forget_result),
            "audit_only": True,
        },
    )
    nodes = status_event_node_sets(
        user_id=store.user_id,
        profile_name=settings.brain_owner_name,
        action=action,
        status="deleted",
    )
    result = _call_cognee_remember_text(
        datapoint_text(payload),
        dataset_name=dataset,
        node_set=nodes,
        settings=settings,
    )
    return {
        "id": event_id,
        "target_external_id": target["external_id"],
        "object_type": target.get("object_type"),
        "dataset": dataset,
        "data_id": data_id,
        "audit_only": True,
        "cognee_result": _json_safe(result),
    }


def _latest_undoable_receipt(store: BrainStore) -> dict[str, Any] | None:
    for receipt in store.list_external_receipts(limit=100):
        if receipt.get("tool_name") in {"brain_forget", "brain_undo_last"}:
            continue
        if receipt.get("status") not in {"synced", "not_applicable"}:
            continue
        if _receipt_cognee_objects(receipt):
            return receipt
    return None


def _find_receipt_targets_for_object(
    store: BrainStore,
    *,
    object_type: str,
    object_id: str,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    for receipt in store.list_external_receipts(limit=500):
        if receipt.get("tool_name") in {"brain_forget", "brain_undo_last"}:
            continue
        if receipt.get("status") not in {"synced", "not_applicable"}:
            continue
        targets = [
            target
            for target in _receipt_cognee_objects(receipt)
            if target.get("object_type") == object_type and target.get("external_id") == object_id
        ]
        if targets:
            return receipt, targets
    return None, []


def _target_dataset_summary(targets: list[dict[str, Any]]) -> str | None:
    datasets = sorted({str(target.get("dataset")) for target in targets if target.get("dataset")})
    return ",".join(datasets) if datasets else None


def _receipt_cognee_objects(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    result = receipt.get("cognee_result_json") or {}
    objects = result.get("objects") if isinstance(result, dict) else []
    if not isinstance(objects, list):
        return []
    targets: list[dict[str, Any]] = []
    for item in objects:
        if not isinstance(item, dict):
            continue
        external_id = item.get("external_id")
        object_type = item.get("object_type")
        if not external_id or object_type != "cognee_remember":
            continue
        targets.append(
            {
                "external_id": str(external_id),
                "object_type": str(object_type),
                "dataset": item.get("dataset"),
                "node_sets": item.get("node_sets") or [],
                "cognee_result": item.get("cognee_result"),
            }
        )
    return targets


def _target_cognee_data_id(target: dict[str, Any]) -> str | None:
    result = target.get("cognee_result")
    candidates: list[Any] = [target.get("data_id")]
    if isinstance(result, dict):
        candidates.extend(
            [
                result.get("data_id"),
                result.get("data_item_id"),
                result.get("id"),
            ]
        )
        items = result.get("items")
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    candidates.extend([item.get("data_id"), item.get("data_item_id"), item.get("id")])
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return str(UUID(str(candidate)))
        except (TypeError, ValueError):
            continue
    return None


def should_route_recall_to_taste(query: str) -> bool:
    lower = query.casefold()
    if "recommend" in lower and lower.startswith(("what ", "who ")):
        return False
    choice_words = ("which", "what should", "should i", "rank", "choose", "best")
    taste_words = ("wine", "restaurant", "movie", "series", "music", "cigar")
    return any(word in lower for word in choice_words) and any(
        word in lower for word in taste_words
    )


def collect_taste_evidence(settings: Settings, memories: list[dict[str, Any]]) -> dict[str, Any]:
    taste_memory_ids = [
        memory["id"]
        for memory in memories
        if (memory.get("metadata_json") or {}).get("taste_item_id")
    ]
    if not taste_memory_ids:
        return {}
    store = CogneePalateStore(settings)
    linked = []
    for memory in memories:
        taste_item_id = (memory.get("metadata_json") or {}).get("taste_item_id")
        if not taste_item_id:
            continue
        item = store.get_item(taste_item_id)
        if item is None:
            continue
        linked.append(
            {
                "memory_id": memory["id"],
                "taste_item_id": item["id"],
                "type": item["type"],
                "canonical_name": item["canonical_name"],
                "attributes": item.get("attributes") or {},
                "signals": item.get("signals") or [],
            }
        )
    return {"linked_evidence": linked} if linked else {}


def taste_result_to_ingestion_receipt(
    taste_result: dict[str, Any],
    settings: Settings,
    route: dict[str, Any],
) -> IngestionReceipt:
    if not taste_result.get("stored"):
        if taste_result.get("requires_confirmation") or taste_result.get("proposal_id"):
            return IngestionReceipt(
                ingestion_run_id=str(
                    taste_result.get("proposal_id")
                    or stable_id("taste_prop", jsonable_hashable(taste_result))
                ),
                classification="taste_proposal",
                dry_run=True,
                taste={
                    "requires_confirmation": True,
                    "proposal_id": taste_result.get("proposal_id"),
                    "proposal": taste_result.get("proposal"),
                    "warnings": taste_result.get("warnings", []),
                    "enrichment": taste_result.get("enrichment", {}),
                },
            )
        return IngestionReceipt(
            ingestion_run_id=stable_id("taste", jsonable_hashable(taste_result)),
            classification="taste",
            dry_run=bool(taste_result.get("dry_run")),
            taste=taste_result,
        )
    records = taste_result.get("taste_records") or []
    entity_receipts: list[EntityReceipt] = []
    for record in records:
        entity_id = record.get("brain_entity_id")
        if not entity_id:
            continue
        entity_receipts.append(
            EntityReceipt(
                id=str(entity_id),
                canonical_name=str(record["canonical_name"]),
                type=str(record["type"]),
                created=False,
            )
        )
    return IngestionReceipt(
        ingestion_run_id=stable_id("taste_ing", jsonable_hashable(taste_result)),
        classification=f"taste_{route.get('taste_intent', 'remember')}",
        entities=entity_receipts,
        taste=taste_result,
    )


def jsonable_hashable(value: Any) -> str:
    import json

    return json.dumps(value, sort_keys=True, default=str)


def taste_source_candidates(
    text: str,
    *,
    settings: Settings,
    llm_client: LLMClient | None = None,
) -> list[dict[str, Any]]:
    candidates = []
    chunks = [
        chunk.strip(" -*\t")
        for chunk in re.split(r"[\n.;]+", text)
        if chunk.strip(" -*\t")
    ]
    for chunk in chunks:
        route = classify_taste_route(chunk, settings=settings, llm_client=llm_client)
        if (
            route.get("taste_intent") == "remember"
            and route.get("domain") in {"taste", "ambiguous"}
            and float(route.get("confidence") or 0) >= settings.brain_taste_confirmation_threshold
        ):
            candidates.append(
                {
                    "text": chunk,
                    "route": route,
                    "confidence": route.get("confidence"),
                    "entity_type_hint": route.get("entity_type_hint"),
                }
            )
    return candidates
