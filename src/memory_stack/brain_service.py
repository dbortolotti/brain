from __future__ import annotations

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
from memory_stack.config import Settings
from memory_stack.ingestion.classifier import input_type_for_source_kind
from memory_stack.ingestion.memory_compiler import compile_memory
from memory_stack.llm.client import LLMClient
from memory_stack.recall.planner import extract_profile_name, infer_recall_mode
from memory_stack.recall.profile_builder import build_profile_response
from memory_stack.recall.retriever import retrieve_memories, retrieve_open_loops
from memory_stack.recall.synthesizer import render_memory_answer, render_open_loops
from memory_stack.resolution.entity_resolver import EntityResolver


def remember(
    request: RememberRequest,
    settings: Settings,
    *,
    llm_client: LLMClient | None = None,
) -> IngestionReceipt:
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
            source, source_created = store.upsert_source(
                {
                    "kind": compiled.source.kind,
                    "title": compiled.source.title,
                    "uri": compiled.source.uri,
                    "file_path": compiled.source.file_path,
                    "raw_text": compiled.source.raw_text,
                    "summary": compiled.source.summary,
                    "metadata_json": compiled.source.metadata,
                    "status": compiled.source.status,
                }
            )
            source_id = source["id"]
            projection_hash = content_hash(
                source["id"],
                source["kind"],
                source.get("uri"),
                source.get("summary"),
                source.get("status"),
            )
            store.mark_cognee_pending(
                object_type="source",
                object_id=source["id"],
                dataset=settings.brain_cognee_sources_dataset,
                projection_hash=projection_hash,
            )

        receipt = IngestionReceipt(
            ingestion_run_id=run["id"],
            classification=compiled.classification,
            source=SourceReceipt(created=source_created, source_id=source_id),
        )
        entity_resolver = EntityResolver(store)
        entity_receipts: dict[str, dict[str, Any]] = {}
        for card in compiled.memory_cards:
            memory, memory_created = store.upsert_memory_card(
                {
                    "kind": str(card.kind),
                    "statement": card.statement,
                    "summary": card.summary,
                    "confidence": card.confidence,
                    "status": card.status,
                    "observed_at": card.observed_at,
                    "source_id": source_id,
                    "source_quote": card.source_quote,
                    "metadata_json": card.metadata,
                }
            )
            receipt.memory_cards.append(
                MemoryReceipt(
                    id=memory["id"],
                    kind=memory["kind"],
                    statement=memory["statement"],
                    status=memory["status"],
                    created=memory_created,
                )
            )
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

            projection_hash = content_hash(memory["id"], memory["statement"], memory["status"])
            store.mark_cognee_pending(
                object_type="memory",
                object_id=memory["id"],
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
            request.model_copy(update={"source_policy": "source_and_memory"}),
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
        },
    )
    return remember(remember_request, settings, llm_client=llm_client)


def recall(request: RecallRequest, settings: Settings) -> RecallResponse:
    store = BrainStore(settings)
    query = request.query.strip()
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
            store.log_recall(
                query=query,
                mode=mode,
                retrieved_memory_ids=[fact["memory_id"] for fact in profile.facts if "memory_id" in fact],
                retrieved_source_ids=[],
                answer_preview=profile.answer,
            )
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
        include_superseded=request.include_superseded,
        include_conflicts=request.include_conflicts,
        limit=request.limit,
    )
    facts = [
        {
            "memory_id": memory["id"],
            "kind": memory["kind"],
            "statement": memory["statement"],
            "status": memory["status"],
            "confidence": memory["confidence"],
        }
        for memory in memories
    ]
    evidence = [
        {
            "memory_id": memory["id"],
            "source_id": memory.get("source_id"),
            "quote": memory.get("source_quote") or memory["statement"],
        }
        for memory in memories
    ]
    answer = render_memory_answer(memories)
    store.log_recall(
        query=query,
        mode=mode,
        retrieved_memory_ids=[memory["id"] for memory in memories],
        retrieved_source_ids=[memory["source_id"] for memory in memories if memory.get("source_id")],
        answer_preview=answer,
    )
    return RecallResponse(answer=answer, facts=facts, evidence=evidence)


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
