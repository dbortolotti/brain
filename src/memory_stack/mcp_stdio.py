from __future__ import annotations

import os
import secrets
from typing import Any

from memory_stack.brain_store import normalize_user_id
from memory_stack.brain_models import IngestSourceRequest, RecallRequest, RememberRequest
from memory_stack.bias_context import (
    forget_bias_context,
    list_bias_context,
    remember_bias_context,
)
from memory_stack.brain_service import (
    forget as brain_forget,
    ingest_source as brain_ingest_source,
    profile_entity as brain_profile_entity,
    recall as brain_recall,
    remember as brain_remember,
    review_recent as brain_review_recent,
    undo_last as brain_undo_last,
)
from memory_stack.cognee_adapter import improve_cognee
from memory_stack.cfg import load_settings
from memory_stack.domain_constants import COGNEE_IMPROVE_DATASETS
from memory_stack.io import to_jsonable
from memory_stack.profile_context import (
    forget_profile_context,
    list_profile_context,
    remember_profile_context,
    sync_profile_context,
)
from memory_stack.session import brain_session_payload
from memory_stack.taste.models import (
    TasteDescribeRequest,
    TasteForgetRequest,
    TasteLogDecisionRequest,
    TasteQueryRequest,
    TasteRefreshRequest,
    TasteRememberRequest,
)
from memory_stack.taste.service import TasteService


def _normalize_stdio_bearer_token(value: str | None) -> str:
    token = (value or "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    return token


def _validate_stdio_launch_auth(settings: Any) -> Any:
    expected_token = _normalize_stdio_bearer_token(settings.brain_auth_token)
    if not expected_token:
        raise RuntimeError("BRAIN_AUTH_TOKEN is required for stdio MCP.")

    supplied_token = _normalize_stdio_bearer_token(os.environ.get("BRAIN_STDIO_BEARER_TOKEN"))
    if not supplied_token:
        raise RuntimeError("BRAIN_STDIO_BEARER_TOKEN is required for stdio MCP.")
    if not secrets.compare_digest(supplied_token, expected_token):
        raise RuntimeError("BRAIN_STDIO_BEARER_TOKEN does not match BRAIN_AUTH_TOKEN.")

    supplied_user_id = (os.environ.get("BRAIN_STDIO_USER_ID") or "").strip()
    if not supplied_user_id:
        raise RuntimeError("BRAIN_STDIO_USER_ID is required for stdio MCP.")
    stdio_user_id = normalize_user_id(supplied_user_id)
    configured_user_id = normalize_user_id(settings.brain_user_id)
    if stdio_user_id != configured_user_id:
        raise RuntimeError("BRAIN_STDIO_USER_ID must match BRAIN_USER_ID for stdio MCP.")

    if stdio_user_id == settings.brain_user_id:
        return settings
    return settings.model_copy(update={"brain_user_id": stdio_user_id})


def build_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:
        raise RuntimeError("Install MCP support with `uv sync --all-extras`.") from exc

    settings = _validate_stdio_launch_auth(load_settings())
    mcp = FastMCP("Brain")

    @mcp.tool(name="brain_session", structured_output=True)
    async def session() -> dict[str, Any]:
        """Resolve the active Brain user's session identity for agents."""
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

    @mcp.tool(name="brain_bias_context_remember", structured_output=True)
    async def bias_context_remember(
        statement: str,
        scope: str = "response_style",
        source: str | None = None,
    ) -> dict[str, Any]:
        """Store stable user bias/preference context returned by brain_session."""
        return remember_bias_context(
            settings,
            statement=statement,
            scope=scope,
            source=source,
        )

    @mcp.tool(name="brain_bias_context_list", structured_output=True)
    async def bias_context_list() -> dict[str, Any]:
        """List stable user bias/preference context."""
        return {"bias_context": list_bias_context(settings)}

    @mcp.tool(name="brain_bias_context_forget", structured_output=True)
    async def bias_context_forget(context_id: str) -> dict[str, Any]:
        """Remove stable user bias/preference context by id."""
        return forget_bias_context(settings, context_id=context_id)

    @mcp.tool(name="brain_remember", structured_output=True)
    async def remember(
        input: str,
        input_type: str = "auto",
        dry_run: bool = False,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Store memory. Do not use for read-only palate describe/enrich; call brain_palate_describe_item."""
        request = RememberRequest(
            input=input,
            input_type=input_type,
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
        dry_run: bool = False,
        run_in_background: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Store source material; Taste mentions are selective and never mass-written."""
        request = IngestSourceRequest(
            source=source,
            source_kind=source_kind,
            title=title,
            why_saved=why_saved,
            dry_run=dry_run,
            run_in_background=run_in_background,
            metadata=metadata or {},
        )
        receipt = brain_ingest_source(request, settings).model_dump(mode="json")
        status = receipt.get("cognee_sync_status", "pending")
        return {
            "status": "queued" if status == "queued" else "dry_run" if dry_run else "processed",
            "summary": title or why_saved or source[:500],
            "cognee_sync_status": status,
            "ingestion": receipt,
        }

    @mcp.tool(name="brain_recall", structured_output=True)
    async def recall(
        query: str,
        mode: str = "auto",
        include_superseded: bool = False,
        include_conflicts: bool = True,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Answer a user-level memory query; recommendation-style taste queries may rank Taste records."""
        request = RecallRequest(
            query=query,
            mode=mode,
            include_superseded=include_superseded,
            include_conflicts=include_conflicts,
            limit=limit,
        )
        return brain_recall(request, settings).model_dump(mode="json")

    @mcp.tool(name="brain_profile_entity", structured_output=True)
    async def profile_entity(
        name: str,
        entity_type: str = "auto",
        include_superseded: bool = False,
        include_conflicts: bool = True,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Build an entity-centric Brain profile."""
        del limit
        resolved_type = None if entity_type == "auto" else entity_type
        return brain_profile_entity(
            settings,
            name=name,
            entity_type=resolved_type,
            include_superseded=include_superseded,
            include_conflicts=include_conflicts,
        ).model_dump(mode="json")

    @mcp.tool(name="brain_forget", structured_output=True)
    async def forget(
        object_type: str,
        object_id: str,
        hard: bool = False,
        reason: str | None = None,
        confirm: bool = False,
    ) -> dict[str, Any]:
        """Forget a Cognee-backed Brain memory/source and write audit evidence."""
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
            "mode": "hard" if hard else payload.get("mode", "forget"),
            "cognee_sync_status": payload.get("cognee_sync_status", "stale"),
        }

    @mcp.tool(name="brain_review_recent", structured_output=True)
    async def review_recent(
        since: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Review recent Brain control receipts, confirmations, and context records."""
        from datetime import datetime

        parsed_since = None
        if since:
            parsed_since = datetime.fromisoformat(since.replace("Z", "+00:00"))
        return brain_review_recent(
            settings,
            since=parsed_since,
            limit=limit,
        )

    @mcp.tool(name="brain_undo_last", structured_output=True)
    async def undo_last(ingestion_run_id: str | None = None) -> dict[str, Any]:
        """Soft-delete objects created by one recent ingestion run."""
        return brain_undo_last(settings, ingestion_run_id=ingestion_run_id)

    @mcp.tool(name="cognee_improve", structured_output=True)
    async def cognee_improve(
        dataset: str = "memory",
        node_name: list[str] | None = None,
        run_in_background: bool = False,
    ) -> dict[str, Any]:
        """Run Cognee native improve on a configured dataset."""
        resolved_dataset = _configured_cognee_dataset(dataset, settings)
        result = await improve_cognee(
            dataset=resolved_dataset,
            node_name=node_name,
            run_in_background=run_in_background,
            settings=settings,
        )
        return {
            "dataset": dataset,
            "resolved_dataset": resolved_dataset,
            "node_name": node_name or [],
            "run_in_background": run_in_background,
            "result": to_jsonable(result),
        }

    @mcp.tool(name="brain_palate_describe_item", structured_output=True)
    async def taste_describe_item(
        item_text: str,
        entity_type: str,
        canonical_name: str | None = None,
        attributes: dict[str, Any] | None = None,
        attribute_intervals_iqr: dict[str, dict[str, float]] | None = None,
        metadata: dict[str, Any] | None = None,
        notes: str | None = None,
        fetch_external_ratings: bool = True,
        allow_broader_web_search: bool = False,
    ) -> dict[str, Any]:
        """Read-only palate describe/enrich. Use for 'use palate to describe Junsei restaurant in London'."""
        return TasteService(settings).describe_item(
            TasteDescribeRequest(
                item_text=item_text,
                entity_type=entity_type,
                canonical_name=canonical_name,
                attributes=attributes,
                attribute_intervals_iqr=attribute_intervals_iqr,
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
        attribute_intervals_iqr: dict[str, dict[str, float]] | None = None,
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
        store_anyway: bool = False,
        context: dict[str, Any] | None = None,
        fetch_external_ratings: bool = True,
        allow_broader_web_search: bool = False,
    ) -> dict[str, Any]:
        """Store a structured taste item and Brain projection."""
        return TasteService(settings).remember(
            TasteRememberRequest(
                id=id,
                type=type,
                canonical_name=canonical_name,
                description=description,
                attributes=attributes,
                attribute_intervals_iqr=attribute_intervals_iqr,
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
                dry_run=dry_run,
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

    @mcp.tool(name="brain_palate_forget", structured_output=True)
    async def taste_forget(
        taste_item_id: str | None = None,
        canonical_name: str | None = None,
        confirm: bool = False,
    ) -> dict[str, Any]:
        """Forget a stored Brain Palate item by palate ID, entity ID, or canonical name."""
        return TasteService(settings).forget(
            TasteForgetRequest(
                taste_item_id=taste_item_id,
                canonical_name=canonical_name,
                confirm=confirm,
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


def _configured_cognee_dataset(dataset: str, settings: Any) -> str:
    mapping = {
        "memory": settings.brain_cognee_memory_dataset,
        "data": settings.brain_cognee_data_dataset,
        "palate": settings.brain_cognee_palate_dataset,
    }
    if dataset not in mapping:
        raise ValueError(f"dataset must be one of: {', '.join(COGNEE_IMPROVE_DATASETS)}")
    return mapping[dataset]


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
