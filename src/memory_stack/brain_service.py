from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from memory_stack.brain_models import (
    EntityReceipt,
    IngestSourceRequest,
    IngestionReceipt,
    MemoryReceipt,
    RecallRequest,
    RecallResponse,
    RememberRequest,
    SourceReceipt,
)
from memory_stack.brain_store import BrainStore, content_hash, stable_id
from memory_stack.cognee.rebuild import rebuild_cognee as rebuild_cognee_projection
from memory_stack.cognee.serializers import (
    serialize_memory_for_cognee,
    serialize_source_for_cognee,
)
from memory_stack.cognee.sync_worker import sync_one, sync_pending_cognee
from memory_stack.cfg import Settings
from memory_stack.ingestion.classifier import input_type_for_source_kind
from memory_stack.ingestion.memory_compiler import compile_memory
from memory_stack.llm.client import LLMClient
from memory_stack.recall.evidence_builder import build_evidence, build_facts
from memory_stack.recall.planner import extract_profile_name, infer_recall_mode
from memory_stack.recall.profile_builder import build_profile_response
from memory_stack.recall.retriever import retrieve_memories, retrieve_open_loops
from memory_stack.recall.synthesizer import render_memory_answer, render_open_loops
from memory_stack.resolution.conflict_detector import detect_and_apply_memory_resolution
from memory_stack.resolution.entity_resolver import EntityResolver
from memory_stack.taste.models import TasteQueryRequest
from memory_stack.taste.routing import classify_taste_route
from memory_stack.taste.service import TasteService, canonical_taste_store, remember_request_from_route
from memory_stack.taste.store import TasteStore


def remember(
    request: RememberRequest,
    settings: Settings,
    *,
    llm_client: LLMClient | None = None,
) -> IngestionReceipt:
    if settings.brain_taste_enabled and not request.context.get("taste_skip"):
        route = classify_taste_route(request.input, settings=settings, llm_client=llm_client)
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

    compiled = compile_memory(request, settings, llm_client=llm_client)
    input_hash = content_hash(request.input, request.input_type, request.context)
    run_id = stable_id("dry_ing", input_hash)
    if request.dry_run:
        return IngestionReceipt(
            ingestion_run_id=run_id,
            classification=compiled.classification,
            source=SourceReceipt(created=compiled.source is not None, source_id=None),
            memory_cards=[
                MemoryReceipt(
                    id=stable_id("dry_mem", card.kind, card.statement),
                    kind=str(card.kind),
                    statement=card.statement,
                    status=card.status,
                    confidence=card.confidence,
                    created=False,
                )
                for card in compiled.memory_cards
            ],
            dry_run=True,
        )

    store = BrainStore(settings)
    run = store.create_ingestion_run(
        input_type=compiled.classification,
        input_hash=input_hash,
        raw_input_preview=request.input,
        metadata_json={"context": request.context, "source_policy": request.source_policy},
    )
    source_id = None
    source_created = False
    try:
        if compiled.source is not None:
            raw_source_text = compiled.source.raw_text or ""
            source_metadata = {
                **compiled.source.metadata,
                "ingestion_run_id": run["id"],
                "raw_text_hash": content_hash(raw_source_text),
                "raw_text_chars": len(raw_source_text),
                "raw_text_storage": "cognee",
            }
            source, source_created = store.upsert_source(
                {
                    "kind": compiled.source.kind,
                    "title": compiled.source.title,
                    "uri": compiled.source.uri,
                    "file_path": compiled.source.file_path,
                    "raw_text": None,
                    "summary": compiled.source.summary,
                    "metadata_json": source_metadata,
                    "status": compiled.source.status,
                    "content_hash": content_hash(
                        compiled.source.kind,
                        compiled.source.uri,
                        compiled.source.title,
                        raw_source_text,
                    ),
                }
            )
            source_id = source["id"]

        receipt = IngestionReceipt(
            ingestion_run_id=run["id"],
            classification=compiled.classification,
            source=SourceReceipt(created=source_created, source_id=source_id),
        )
        entity_resolver = EntityResolver(store)
        entity_receipts: dict[str, dict[str, Any]] = {}
        for card in compiled.memory_cards:
            memory_metadata = {**card.metadata, "ingestion_run_id": run["id"]}
            if "slack" in request.context:
                memory_metadata["slack"] = request.context["slack"]
            source_quote = card.source_quote
            if card.kind == "source_record":
                source_quote = None
            memory, memory_created = store.upsert_memory_card(
                {
                    "kind": str(card.kind),
                    "statement": card.statement,
                    "summary": card.summary,
                    "confidence": card.confidence,
                    "status": card.status,
                    "observed_at": card.observed_at,
                    "source_id": source_id,
                    "source_quote": source_quote,
                    "metadata_json": memory_metadata,
                }
            )
            memory_receipt = MemoryReceipt(
                id=memory["id"],
                kind=memory["kind"],
                statement=memory["statement"],
                status=memory["status"],
                confidence=memory["confidence"],
                created=memory_created,
            )
            receipt.memory_cards.append(memory_receipt)
            entity_map: dict[str, dict[str, Any]] = {}
            for mention in card.entities:
                aliases = [mention.alias] if mention.alias else []
                resolution = entity_resolver.resolve_entity(
                    entity_type=mention.type,
                    canonical_name=mention.name,
                    aliases=aliases,
                    confidence=mention.confidence,
                    metadata_json=mention.metadata,
                )
                entity = resolution.entity
                entity_map[mention.name] = entity
                if mention.alias:
                    entity_map[mention.alias] = entity
                entity_receipts[entity["id"]] = {
                    "id": entity["id"],
                    "canonical_name": entity["canonical_name"],
                    "type": entity["type"],
                    "created": resolution.created,
                }
                store.link_memory_entity(
                    memory_id=memory["id"],
                    entity_id=entity["id"],
                    role=mention.role,
                    confidence=mention.confidence,
                )

            for relationship in card.relationships:
                subject = entity_map.get(relationship.subject)
                object_ = entity_map.get(relationship.object)
                if subject is None:
                    subject = entity_resolver.resolve_entity(
                        entity_type="concept",
                        canonical_name=relationship.subject,
                    ).entity
                if object_ is None:
                    object_ = entity_resolver.resolve_entity(
                        entity_type="concept",
                        canonical_name=relationship.object,
                    ).entity
                rel, rel_created = store.create_relationship(
                    subject_entity_id=subject["id"],
                    predicate=relationship.predicate,
                    object_entity_id=object_["id"],
                    evidence_memory_id=memory["id"],
                    confidence=relationship.confidence,
                    status=relationship.status,
                    metadata_json=relationship.metadata,
                )
                receipt.relationships.append({**rel, "created": rel_created})

            if card.open_loop is not None:
                loop, loop_created = store.create_open_loop(
                    memory_id=memory["id"],
                    status=card.open_loop.get("status", "open"),
                    priority=card.open_loop.get("priority", "normal"),
                    reminder_policy=card.open_loop.get("reminder_policy"),
                    metadata_json={k: v for k, v in card.open_loop.items() if k not in {"status", "priority", "reminder_policy"}},
                )
                receipt.open_loops.append({**loop, "created": loop_created})

            detections = detect_and_apply_memory_resolution(store, memory["id"])
            if detections:
                receipt.conflicts.extend(detections)
                for detection in detections:
                    target_memory_id = detection.get("target_memory_id")
                    if target_memory_id:
                        store.mark_cognee_stale(
                            object_type="memory",
                            object_id=str(target_memory_id),
                        )

            refreshed_memory = store.get_memory(memory["id"]) or memory
            memory_receipt.status = refreshed_memory["status"]
            projection_hash = content_hash(
                refreshed_memory["id"],
                refreshed_memory["statement"],
                refreshed_memory["status"],
            )
            store.mark_cognee_pending(
                object_type="memory",
                object_id=refreshed_memory["id"],
                dataset=settings.brain_cognee_memory_dataset,
                projection_hash=projection_hash,
            )

        receipt.entities = [
            EntityReceipt(
                id=value["id"],
                canonical_name=value["canonical_name"],
                type=value["type"],
                created=value["created"],
            )
            for value in entity_receipts.values()
        ]
        store.finish_ingestion_run(run["id"], status="processed", source_id=source_id)
        return IngestionReceipt.model_validate(receipt)
    except Exception as exc:
        store.finish_ingestion_run(run["id"], status="failed", error_message=str(exc))
        raise


def ingest_source(
    request: IngestSourceRequest | RememberRequest,
    settings: Settings,
    *,
    llm_client: LLMClient | None = None,
) -> IngestionReceipt:
    if isinstance(request, RememberRequest):
        return remember(
            request.model_copy(
                update={
                    "source_policy": "source_and_memory",
                    "context": {**request.context, "taste_skip": True, "source_ingest": True},
                }
            ),
            settings,
            llm_client=llm_client,
        )

    remember_request = RememberRequest(
        input=request.source,
        input_type=input_type_for_source_kind(request.source_kind, request.source),
        source_policy="source_and_memory" if request.extract_memories else "source_only",
        dry_run=request.dry_run,
        context={
            "title": request.title,
            "why_saved": request.why_saved,
            "metadata": request.metadata,
            "source_kind": request.source_kind,
            "taste_skip": True,
            "source_ingest": True,
        },
    )
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
                            "proposed_memory_cards": [],
                            "proposed_relationships": [],
                            "proposed_open_loops": [],
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
        profile = build_profile_response(
            name,
            settings,
            include_superseded=request.include_superseded,
            include_conflicts=request.include_conflicts,
        )
        if profile is not None:
            profile_memory_ids = [fact["memory_id"] for fact in profile.facts if "memory_id" in fact]
            profile_memories = [
                memory
                for memory_id in profile_memory_ids
                if (memory := store.get_memory(memory_id)) is not None
            ]
            taste_evidence = collect_taste_evidence(settings, profile_memories)
            store.log_recall(
                query=query,
                mode=mode,
                retrieved_memory_ids=profile_memory_ids,
                retrieved_source_ids=[],
                answer_preview=profile.answer,
            )
            if taste_evidence:
                return profile.model_copy(update={"taste": taste_evidence})
            return profile
    if mode == "open_loops":
        loops = retrieve_open_loops(store, limit=request.limit)
        answer = render_open_loops(loops)
        response = RecallResponse(answer=answer, open_loops=loops)
        store.log_recall(
            query=query,
            mode=mode,
            retrieved_memory_ids=[loop["memory_id"] for loop in loops],
            retrieved_source_ids=[],
            answer_preview=answer,
        )
        return response

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
    evidence = build_evidence(memories, include_sources=request.include_sources)
    answer = render_memory_answer(memories)
    taste_evidence = collect_taste_evidence(settings, memories)
    store.log_recall(
        query=query,
        mode=mode,
        retrieved_memory_ids=[memory["id"] for memory in memories],
        retrieved_source_ids=[memory["source_id"] for memory in memories if memory.get("source_id")],
        answer_preview=answer,
    )
    return RecallResponse(answer=answer, facts=facts, evidence=evidence, taste=taste_evidence)


def get_memory(memory_id: str, settings: Settings) -> dict[str, Any] | None:
    return BrainStore(settings).get_memory(memory_id)


def get_source(
    source_id: str,
    settings: Settings,
    *,
    include_text: bool = False,
    max_chars: int = 10_000,
) -> dict[str, Any] | None:
    return BrainStore(settings).get_source(
        source_id,
        include_text=include_text,
        max_chars=max_chars,
    )


def list_open_loops(
    settings: Settings,
    *,
    topic: str | None = None,
    status: str = "open",
    limit: int = 20,
) -> list[dict[str, Any]]:
    return BrainStore(settings).list_open_loops(topic=topic, status=status, limit=limit)


def profile_entity(
    settings: Settings,
    *,
    name: str,
    entity_type: str | None = None,
    include_superseded: bool = False,
    include_conflicts: bool = True,
) -> RecallResponse:
    response = build_profile_response(
        name,
        settings,
        entity_type=entity_type,
        include_superseded=include_superseded,
        include_conflicts=include_conflicts,
    )
    if response is None:
        return RecallResponse(answer=f"No entity found for {name}.")
    return response


def forget(
    settings: Settings,
    *,
    object_type: str,
    object_id: str,
    hard: bool = False,
    reason: str | None = None,
) -> dict[str, Any]:
    del reason
    deleted = BrainStore(settings).forget(object_type=object_type, object_id=object_id, hard=hard)
    return {"object_type": object_type, "object_id": object_id, "status": "deleted" if deleted else "not_found"}


def resolve_conflict(
    settings: Settings,
    *,
    conflict_memory_id: str,
    target_memory_id: str,
    action: str,
    note: str | None = None,
) -> dict[str, Any]:
    store = BrainStore(settings)
    if action == "supersede":
        store.update_memory_status(target_memory_id, "superseded")
        store.update_memory_status(conflict_memory_id, "current")
        link, _ = store.create_memory_link(
            from_memory_id=conflict_memory_id,
            relation="supersedes",
            to_memory_id=target_memory_id,
            metadata_json={"note": note} if note else {},
        )
        return {"action": action, "link": link}
    if action == "keep_both":
        store.update_memory_status(conflict_memory_id, "current")
        store.update_memory_status(target_memory_id, "current")
        link, _ = store.create_memory_link(
            from_memory_id=conflict_memory_id,
            relation="contradicts",
            to_memory_id=target_memory_id,
            metadata_json={"note": note} if note else {},
        )
        return {"action": action, "link": link}
    if action == "mark_contradiction":
        store.update_memory_status(conflict_memory_id, "current")
        store.update_memory_status(target_memory_id, "current")
        link, _ = store.create_memory_link(
            from_memory_id=conflict_memory_id,
            relation="contradicts",
            to_memory_id=target_memory_id,
            metadata_json={"note": note} if note else {},
        )
        return {"action": action, "link": link}
    if action == "mark_duplicate":
        store.update_memory_status(conflict_memory_id, "archived")
        link, _ = store.create_memory_link(
            from_memory_id=conflict_memory_id,
            relation="duplicates",
            to_memory_id=target_memory_id,
            metadata_json={"note": note} if note else {},
        )
        return {"action": action, "link": link}
    if action == "archive_old":
        store.update_memory_status(target_memory_id, "archived")
        return {"action": action, "target_memory_id": target_memory_id, "status": "archived"}
    if action == "reject_new":
        store.update_memory_status(conflict_memory_id, "rejected")
        return {"action": action, "conflict_memory_id": conflict_memory_id, "status": "rejected"}
    raise ValueError(
        "action must be supersede, keep_both, mark_duplicate, archive_old, "
        "reject_new, or mark_contradiction."
    )


def review_recent(
    settings: Settings,
    *,
    since: datetime | None = None,
    limit: int = 20,
    include_sources: bool = True,
) -> dict[str, Any]:
    store = BrainStore(settings)
    return {
        "ingestion_runs": store.list_ingestion_runs(since=since, limit=limit),
        "sources": store.list_sources(since=since, limit=limit) if include_sources else [],
        "memory_cards": store.list_memory_cards(since=since, limit=limit),
        "conflicts": store.list_memory_links(
            relations=("duplicates", "supersedes", "contradicts"),
            since=since,
            limit=limit,
        ),
    }


def undo_last(
    settings: Settings,
    *,
    ingestion_run_id: str | None = None,
) -> dict[str, Any]:
    store = BrainStore(settings)
    run = (
        store.get_ingestion_run(ingestion_run_id)
        if ingestion_run_id
        else (store.list_ingestion_runs(limit=1)[0] if store.list_ingestion_runs(limit=1) else None)
    )
    if run is None:
        return {"status": "not_found", "deleted_memories": [], "deleted_sources": []}

    memory_rows = store.list_memory_cards(include_deleted=True, limit=100_000)
    memory_ids = [
        memory["id"]
        for memory in memory_rows
        if (memory.get("metadata_json") or {}).get("ingestion_run_id") == run["id"]
        or (run.get("source_id") and memory.get("source_id") == run.get("source_id"))
    ]
    deleted_memories = []
    for memory_id in memory_ids:
        if store.update_memory_status(memory_id, "deleted"):
            deleted_memories.append(memory_id)

    deleted_sources = []
    if run.get("source_id") and store.update_source_status(run["source_id"], "deleted"):
        deleted_sources.append(run["source_id"])

    return {
        "status": "undone",
        "ingestion_run_id": run["id"],
        "deleted_memories": deleted_memories,
        "deleted_sources": deleted_sources,
        "mode": "soft",
        "cognee_sync_status": "stale",
    }


def sync_cognee(
    settings: Settings,
    *,
    object_type: str = "all",
    object_id: str | None = None,
    dataset: str = "all",
    force: bool = False,
    adapter: Any = None,
) -> dict[str, Any]:
    store = BrainStore(settings)
    if object_id:
        if object_type not in {"memory", "source"}:
            raise ValueError("object_type must be memory or source when object_id is provided.")
        _ensure_projection_row(
            store,
            settings,
            object_type=object_type,
            object_id=object_id,
            force=force,
        )
        rows = store.list_cognee_sync(
            statuses=("pending", "stale", "failed"),
            object_type=object_type,
            object_id=object_id,
            limit=100,
        )
        results = [
            sync_one(row["id"], settings=settings, store=store, adapter=adapter)
            for row in rows
            if row["status"] in {"pending", "stale"} or force
        ]
        return {
            "status": "complete",
            "processed": len(results),
            "succeeded": len([result for result in results if result.get("status") == "synced"]),
            "failed": len([result for result in results if result.get("status") == "failed"]),
            "results": results,
        }

    if force:
        rebuild_cognee_projection(
            settings=settings,
            store=store,
            dataset=dataset,
            confirm=True,
            sync=False,
        )
    return sync_pending_cognee(settings=settings, store=store, adapter=adapter)


def rebuild_cognee(
    settings: Settings,
    *,
    dataset: str = "all",
    prune_first: bool = False,
    confirm: bool = False,
    sync: bool = False,
    adapter: Any = None,
) -> dict[str, Any]:
    return rebuild_cognee_projection(
        settings=settings,
        dataset=dataset,
        prune_first=prune_first,
        confirm=confirm,
        sync=sync,
        adapter=adapter,
    )


def merge_entities(
    settings: Settings,
    *,
    primary_entity_id: str,
    duplicate_entity_id: str,
    reason: str | None = None,
    confirm: bool = False,
) -> dict[str, Any]:
    if not confirm:
        raise ValueError("brain_merge_entities requires confirm=true.")
    store = BrainStore(settings)
    result = store.merge_entities(
        primary_entity_id=primary_entity_id,
        duplicate_entity_id=duplicate_entity_id,
        reason=reason,
    )
    for memory in store.list_memories_by_entity(primary_entity_id, include_superseded=True, limit=100_000):
        store.mark_cognee_stale(object_type="memory", object_id=memory["id"])
    return {"status": "merged", **result}


def _ensure_projection_row(
    store: BrainStore,
    settings: Settings,
    *,
    object_type: str,
    object_id: str,
    force: bool,
) -> None:
    if object_type == "memory":
        text = serialize_memory_for_cognee(object_id, store=store)
        store.mark_cognee_pending(
            object_type="memory",
            object_id=object_id,
            dataset=settings.brain_cognee_memory_dataset,
            projection_hash=content_hash(text),
        )
    elif object_type == "source":
        text = serialize_source_for_cognee(object_id, store=store)
        store.mark_cognee_pending(
            object_type="source",
            object_id=object_id,
            dataset=settings.brain_cognee_sources_dataset,
            projection_hash=content_hash(text),
        )
    if force:
        store.mark_cognee_stale(object_type=object_type, object_id=object_id)


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
    sqlite_store = TasteStore(settings)
    store = canonical_taste_store(settings, sqlite_store)
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
    store = BrainStore(settings)
    projection = taste_result.get("brain_projection") or {}
    memory_ids = projection.get("memory_ids") or []
    records = taste_result.get("taste_records") or []
    memory_receipts = []
    for memory_id in memory_ids:
        memory = store.get_memory(memory_id)
        if memory is None:
            continue
        memory_receipts.append(
            MemoryReceipt(
                id=memory["id"],
                kind=memory["kind"],
                statement=memory["statement"],
                status=memory["status"],
                confidence=memory["confidence"],
                created=True,
            )
        )
    entity_receipts = []
    for record in records:
        entity = store.get_entity(record["brain_entity_id"])
        if entity is None:
            continue
        entity_receipts.append(
            EntityReceipt(
                id=entity["id"],
                canonical_name=entity["canonical_name"],
                type=entity["type"],
                created=bool(projection.get("entity_created")),
            )
        )
    return IngestionReceipt(
        ingestion_run_id=stable_id("taste_ing", jsonable_hashable(taste_result)),
        classification=f"taste_{route.get('taste_intent', 'remember')}",
        memory_cards=memory_receipts,
        entities=entity_receipts,
        relationships=[
            {"id": rel_id, "created": True}
            for rel_id in projection.get("relationship_ids", [])
        ],
        open_loops=[
            {"id": loop_id, "created": True}
            for loop_id in projection.get("open_loop_ids", [])
        ],
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
