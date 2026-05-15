from __future__ import annotations

from typing import Any

from memory_stack.brain_models import IngestSourceRequest, RecallRequest, RememberRequest
from memory_stack.brain_service import (
    forget as brain_forget,
    get_memory as brain_get_memory,
    get_source as brain_get_source,
    ingest_source as brain_ingest_source,
    list_open_loops as brain_list_open_loops,
    merge_entities as brain_merge_entities,
    profile_entity as brain_profile_entity,
    recall as brain_recall,
    remember as brain_remember,
    rebuild_cognee as brain_rebuild_cognee,
    resolve_conflict as brain_resolve_conflict,
    review_recent as brain_review_recent,
    sync_cognee as brain_sync_cognee,
    undo_last as brain_undo_last,
)
from memory_stack.cfg import load_settings
from memory_stack.profile_context import (
    forget_profile_context,
    list_profile_context,
    remember_profile_context,
    sync_profile_context,
)
from memory_stack.session import brain_session_payload
from memory_stack.taste.models import (
    TasteDescribeRequest,
    TasteLogDecisionRequest,
    TasteQueryRequest,
    TasteRefreshRequest,
    TasteRememberRequest,
)
from memory_stack.taste.service import TasteService


def build_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:
        raise RuntimeError("Install MCP support with `uv sync --all-extras`.") from exc

    settings = load_settings()
    mcp = FastMCP("Brain")

    @mcp.tool(name="brain_session", structured_output=True)
    async def session() -> dict[str, Any]:
        """Resolve the configured Brain session identity for agents."""
        return brain_session_payload(settings)

    @mcp.tool(name="brain_profile_context_remember", structured_output=True)
    async def profile_context_remember(
        statement: str,
        scope: str = "answer_tailoring",
        source: str | None = None,
    ) -> dict[str, Any]:
        """Store stable user-profile context returned by brain_session."""
        return remember_profile_context(
            settings,
            statement=statement,
            scope=scope,
            source=source,
        )

    @mcp.tool(name="brain_profile_context_list", structured_output=True)
    async def profile_context_list() -> dict[str, Any]:
        """List stable user-profile context returned by brain_session."""
        return {"profile_context": list_profile_context(settings)}

    @mcp.tool(name="brain_profile_context_forget", structured_output=True)
    async def profile_context_forget(context_id: str) -> dict[str, Any]:
        """Remove stable user-profile context by id."""
        return forget_profile_context(settings, context_id=context_id)

    @mcp.tool(name="brain_profile_context_sync", structured_output=True)
    async def profile_context_sync() -> dict[str, Any]:
        """Project profile context into the normal Brain memory/entity graph."""
        return sync_profile_context(settings)

    @mcp.tool(name="brain_remember", structured_output=True)
    async def remember(
        input: str,
        input_type: str = "auto",
        source_policy: str = "auto",
        dry_run: bool = False,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Store memory. Do not use for read-only palate describe/enrich; call brain_palate_describe_item."""
        request = RememberRequest(
            input=input,
            input_type=input_type,
            source_policy=source_policy,
            dry_run=dry_run,
            context=context or {},
        )
        return brain_remember(request, settings).model_dump(mode="json")

    @mcp.tool(name="brain_ingest_source", structured_output=True)
    async def ingest_source(
        source: str,
        source_kind: str = "auto",
        title: str | None = None,
        why_saved: str | None = None,
        extract_memories: bool = True,
        dry_run: bool = False,
        run_in_background: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Store source material; Taste mentions are selective and never mass-written."""
        request = IngestSourceRequest(
            source=source,
            source_kind=source_kind,
            title=title,
            why_saved=why_saved,
            extract_memories=extract_memories,
            dry_run=dry_run,
            run_in_background=run_in_background,
            metadata=metadata or {},
        )
        receipt = brain_ingest_source(request, settings).model_dump(mode="json")
        return {
            "source_id": receipt.get("source", {}).get("source_id"),
            "status": "queued" if receipt.get("cognee_sync_status") == "queued" else "processed",
            "memory_cards_created": [
                card["id"] for card in receipt.get("memory_cards", []) if card.get("created")
            ],
            "summary": title or why_saved or source[:500],
            "cognee_sync_status": receipt.get("cognee_sync_status", "pending"),
            "ingestion": receipt,
        }

    @mcp.tool(name="brain_recall", structured_output=True)
    async def recall(
        query: str,
        mode: str = "auto",
        include_sources: bool = True,
        include_superseded: bool = False,
        include_conflicts: bool = True,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Answer a user-level memory query; recommendation-style taste queries may rank Taste records."""
        request = RecallRequest(
            query=query,
            mode=mode,
            include_sources=include_sources,
            include_superseded=include_superseded,
            include_conflicts=include_conflicts,
            limit=limit,
        )
        return brain_recall(request, settings).model_dump(mode="json")

    @mcp.tool(name="brain_profile_entity", structured_output=True)
    async def profile_entity(
        name: str,
        entity_type: str = "auto",
        include_sources: bool = True,
        include_superseded: bool = False,
        include_conflicts: bool = True,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Build an entity-centric Brain profile."""
        del include_sources, limit
        resolved_type = None if entity_type == "auto" else entity_type
        return brain_profile_entity(
            settings,
            name=name,
            entity_type=resolved_type,
            include_superseded=include_superseded,
            include_conflicts=include_conflicts,
        ).model_dump(mode="json")

    @mcp.tool(name="brain_list_open_loops", structured_output=True)
    async def list_open_loops(
        topic: str | None = None,
        status: str = "open",
        include_recently_reminded: bool = False,
        limit: int = 20,
    ) -> dict[str, Any]:
        """List open questions, ideas, reminders, and parked research threads."""
        del include_recently_reminded
        return {
            "open_loops": brain_list_open_loops(
                settings,
                topic=topic,
                status=status,
                limit=limit,
            )
        }

    @mcp.tool(name="brain_get_memory", structured_output=True)
    async def get_memory(
        memory_id: str,
        include_links: bool = True,
        include_entities: bool = True,
        include_source: bool = True,
    ) -> dict[str, Any]:
        """Read one Brain memory card by id."""
        del include_links, include_entities, include_source
        return {"memory": brain_get_memory(memory_id, settings)}

    @mcp.tool(name="brain_get_source", structured_output=True)
    async def get_source(
        source_id: str,
        include_text: bool = False,
        max_chars: int = 10_000,
    ) -> dict[str, Any]:
        """Read Brain source metadata and optionally truncated source text."""
        source = brain_get_source(
            source_id,
            settings,
            include_text=include_text,
            max_chars=max(1_000, min(100_000, max_chars)),
        )
        text = source.get("text") if source and "text" in source else None
        source_without_text = (
            {key: value for key, value in source.items() if key != "text"} if source else None
        )
        return {"source": source_without_text, "text": text}

    @mcp.tool(name="brain_resolve_conflict", structured_output=True)
    async def resolve_conflict(
        conflict_memory_id: str,
        target_memory_id: str,
        action: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        """Resolve a contradiction or duplicate between two Brain memories."""
        return brain_resolve_conflict(
            settings,
            conflict_memory_id=conflict_memory_id,
            target_memory_id=target_memory_id,
            action=action,
            note=note,
        )

    @mcp.tool(name="brain_forget", structured_output=True)
    async def forget(
        object_type: str,
        object_id: str,
        hard: bool = False,
        reason: str | None = None,
        confirm: bool = False,
    ) -> dict[str, Any]:
        """Soft delete a Brain object. Hard delete requires confirm=true."""
        if hard and not confirm:
            raise ValueError("brain_forget requires confirm=true for hard deletes.")
        payload = brain_forget(
            settings,
            object_type=object_type,
            object_id=object_id,
            hard=hard,
            reason=reason,
        )
        return {
            **payload,
            "mode": "hard" if hard else "soft",
            "cognee_sync_status": "stale",
        }

    @mcp.tool(name="brain_review_recent", structured_output=True)
    async def review_recent(
        since: str | None = None,
        limit: int = 20,
        include_sources: bool = True,
    ) -> dict[str, Any]:
        """Review recent Brain ingestion runs, sources, memories, and conflict links."""
        from datetime import datetime

        parsed_since = None
        if since:
            parsed_since = datetime.fromisoformat(since.replace("Z", "+00:00"))
        return brain_review_recent(
            settings,
            since=parsed_since,
            limit=limit,
            include_sources=include_sources,
        )

    @mcp.tool(name="brain_undo_last", structured_output=True)
    async def undo_last(ingestion_run_id: str | None = None) -> dict[str, Any]:
        """Soft-delete objects created by one recent ingestion run."""
        return brain_undo_last(settings, ingestion_run_id=ingestion_run_id)

    @mcp.tool(name="brain_sync_cognee", structured_output=True)
    async def sync_cognee(
        object_type: str = "all",
        object_id: str | None = None,
        dataset: str = "all",
        force: bool = False,
    ) -> dict[str, Any]:
        """Manually sync pending Brain projections to Cognee."""
        return brain_sync_cognee(
            settings,
            object_type=object_type,
            object_id=object_id,
            dataset=dataset,
            force=force,
        )

    @mcp.tool(name="brain_rebuild_cognee", structured_output=True)
    async def rebuild_cognee(
        dataset: str = "all",
        prune_first: bool = False,
        confirm: bool = False,
    ) -> dict[str, Any]:
        """Mark Cognee projections stale so they can be rebuilt from Brain DB."""
        return brain_rebuild_cognee(
            settings,
            dataset=dataset,
            prune_first=prune_first,
            confirm=confirm,
        )

    @mcp.tool(name="brain_merge_entities", structured_output=True)
    async def merge_entities(
        primary_entity_id: str,
        duplicate_entity_id: str,
        reason: str | None = None,
        confirm: bool = False,
    ) -> dict[str, Any]:
        """Merge a duplicate entity into a primary entity after confirmation."""
        return brain_merge_entities(
            settings,
            primary_entity_id=primary_entity_id,
            duplicate_entity_id=duplicate_entity_id,
            reason=reason,
            confirm=confirm,
        )

    @mcp.tool(name="brain_palate_describe_item", structured_output=True)
    async def taste_describe_item(
        item_text: str,
        entity_type: str,
        canonical_name: str | None = None,
        attributes: dict[str, Any] | None = None,
        attribute_intervals_95: dict[str, dict[str, float]] | None = None,
        metadata: dict[str, Any] | None = None,
        notes: str | None = None,
        fetch_external_ratings: bool = True,
        allow_broader_web_search: bool = False,
    ) -> dict[str, Any]:
        """Read-only palate describe/enrich. Show enriched record and ask before saving."""
        return TasteService(settings).describe_item(
            TasteDescribeRequest(
                item_text=item_text,
                entity_type=entity_type,
                canonical_name=canonical_name,
                attributes=attributes,
                attribute_intervals_95=attribute_intervals_95,
                metadata=metadata or {},
                notes=notes,
                fetch_external_ratings=fetch_external_ratings,
                allow_broader_web_search=allow_broader_web_search,
            )
        )

    @mcp.tool(name="brain_palate_remember", structured_output=True)
    async def taste_remember(
        type: str,
        canonical_name: str,
        description: str,
        id: str | None = None,
        attributes: dict[str, Any] | None = None,
        attribute_intervals_95: dict[str, dict[str, float]] | None = None,
        rating: float | None = None,
        tried: bool | None = None,
        watched: bool | None = None,
        listened: bool | None = None,
        wanted: bool | None = None,
        recommended_by: str | None = None,
        disliked: bool | None = None,
        avoid: bool | None = None,
        not_my_style: bool | None = None,
        bad_fit: bool | None = None,
        notes: str | None = None,
        metadata: dict[str, Any] | None = None,
        dry_run: bool = False,
        confirm_save: bool = False,
        store_anyway: bool = False,
        context: dict[str, Any] | None = None,
        fetch_external_ratings: bool = True,
        allow_broader_web_search: bool = False,
    ) -> dict[str, Any]:
        """Store only after user saw the enriched record and confirmed; otherwise return a dry-run preview."""
        return TasteService(settings).remember(
            TasteRememberRequest(
                id=id,
                type=type,
                canonical_name=canonical_name,
                description=description,
                attributes=attributes,
                attribute_intervals_95=attribute_intervals_95,
                rating=rating,
                tried=tried,
                watched=watched,
                listened=listened,
                wanted=wanted,
                recommended_by=recommended_by,
                disliked=disliked,
                avoid=avoid,
                not_my_style=not_my_style,
                bad_fit=bad_fit,
                notes=notes,
                metadata=metadata or {},
                dry_run=dry_run or not confirm_save,
                store_anyway=store_anyway,
                context=context or {},
                fetch_external_ratings=fetch_external_ratings,
                allow_broader_web_search=allow_broader_web_search,
            )
        )

    @mcp.tool(name="brain_palate_query", structured_output=True)
    async def taste_query(
        query: str,
        context: dict[str, Any] | None = None,
        options_text: str | None = None,
        explain: bool = False,
        intent: dict[str, Any] | None = None,
        extracted_entities: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Rank saved taste records for recommendations. Do not use to describe one item; call brain_palate_describe_item."""
        return TasteService(settings).query(
            TasteQueryRequest(
                query=query,
                context=context or {},
                options_text=options_text,
                explain=explain,
                intent=intent,
                extracted_entities=extracted_entities,
            )
        )

    @mcp.tool(name="brain_palate_evaluate_options", structured_output=True)
    async def taste_evaluate_options(
        query: str,
        options_text: str,
        context: dict[str, Any] | None = None,
        explain: bool = False,
        intent: dict[str, Any] | None = None,
        extracted_entities: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Rank supplied options against saved taste records. Do not use to describe one item."""
        return TasteService(settings).evaluate_options(
            TasteQueryRequest(
                query=query,
                context=context or {},
                options_text=options_text,
                explain=explain,
                intent=intent,
                extracted_entities=extracted_entities,
            )
        )

    @mcp.tool(name="brain_palate_log_decision", structured_output=True)
    async def taste_log_decision(
        chosen_taste_item_id: str,
        decision_id: str | None = None,
        query: str = "",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record the selected taste item after ranking."""
        return TasteService(settings).log_decision(
            TasteLogDecisionRequest(
                chosen_taste_item_id=chosen_taste_item_id,
                decision_id=decision_id,
                query=query,
                context=context or {},
            )
        )

    @mcp.tool(name="brain_palate_confirm", structured_output=True)
    async def taste_confirm(proposal_id: str) -> dict[str, Any]:
        """Confirm a pending taste proposal."""
        return TasteService(settings).confirm(proposal_id)

    @mcp.tool(name="brain_palate_cancel", structured_output=True)
    async def taste_cancel(proposal_id: str) -> dict[str, Any]:
        """Cancel a pending taste proposal."""
        return TasteService(settings).cancel(proposal_id)

    @mcp.tool(name="brain_palate_correct_proposal", structured_output=True)
    async def taste_correct_proposal(proposal_id: str, correction: str) -> dict[str, Any]:
        """Apply a free-text correction to a pending taste proposal."""
        return TasteService(settings).correct_proposal(proposal_id, correction)

    @mcp.tool(name="brain_palate_refresh_enrichment", structured_output=True)
    async def taste_refresh_enrichment(taste_item_id: str) -> dict[str, Any]:
        """Refresh enrichment for a stored taste item."""
        return TasteService(settings).refresh_enrichment(
            TasteRefreshRequest(taste_item_id=taste_item_id)
        )

    return mcp


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
