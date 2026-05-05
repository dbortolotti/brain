from __future__ import annotations

from typing import Any

from memory_stack.brain_models import IngestSourceRequest, RecallRequest, RememberRequest
from memory_stack.brain_service import (
    forget as brain_forget,
    get_memory as brain_get_memory,
    get_source as brain_get_source,
    ingest_source as brain_ingest_source,
    list_open_loops as brain_list_open_loops,
    profile_entity as brain_profile_entity,
    recall as brain_recall,
    remember as brain_remember,
    resolve_conflict as brain_resolve_conflict,
)
from memory_stack.config import load_settings


def build_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:
        raise RuntimeError("Install MCP support with `uv sync --all-extras`.") from exc

    settings = load_settings()
    mcp = FastMCP("Brain")

    @mcp.tool(name="brain.remember", structured_output=True)
    async def remember(
        input: str,
        input_type: str = "auto",
        source_policy: str = "auto",
        dry_run: bool = False,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Store a user-level memory, fact, thought, or short note in Brain."""
        request = RememberRequest(
            input=input,
            input_type=input_type,
            source_policy=source_policy,
            dry_run=dry_run,
            context=context or {},
        )
        return brain_remember(request, settings).model_dump(mode="json")

    @mcp.tool(name="brain.ingest_source", structured_output=True)
    async def ingest_source(
        source: str,
        source_kind: str = "auto",
        title: str | None = None,
        why_saved: str | None = None,
        extract_memories: bool = True,
        dry_run: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Store source material and optionally extract durable Brain memories."""
        request = IngestSourceRequest(
            source=source,
            source_kind=source_kind,
            title=title,
            why_saved=why_saved,
            extract_memories=extract_memories,
            dry_run=dry_run,
            metadata=metadata or {},
        )
        receipt = brain_ingest_source(request, settings).model_dump(mode="json")
        return {
            "source_id": receipt.get("source", {}).get("source_id"),
            "status": "processed",
            "memory_cards_created": [
                card["id"] for card in receipt.get("memory_cards", []) if card.get("created")
            ],
            "summary": title or why_saved or source[:500],
            "cognee_sync_status": receipt.get("cognee_sync_status", "pending"),
            "ingestion": receipt,
        }

    @mcp.tool(name="brain.recall", structured_output=True)
    async def recall(
        query: str,
        mode: str = "auto",
        include_sources: bool = True,
        include_superseded: bool = False,
        include_conflicts: bool = True,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Answer a user-level memory query with evidence."""
        request = RecallRequest(
            query=query,
            mode=mode,
            include_sources=include_sources,
            include_superseded=include_superseded,
            include_conflicts=include_conflicts,
            limit=limit,
        )
        return brain_recall(request, settings).model_dump(mode="json")

    @mcp.tool(name="brain.profile_entity", structured_output=True)
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

    @mcp.tool(name="brain.list_open_loops", structured_output=True)
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

    @mcp.tool(name="brain.get_memory", structured_output=True)
    async def get_memory(
        memory_id: str,
        include_links: bool = True,
        include_entities: bool = True,
        include_source: bool = True,
    ) -> dict[str, Any]:
        """Read one Brain memory card by id."""
        del include_links, include_entities, include_source
        return {"memory": brain_get_memory(memory_id, settings)}

    @mcp.tool(name="brain.get_source", structured_output=True)
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

    @mcp.tool(name="brain.resolve_conflict", structured_output=True)
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

    @mcp.tool(name="brain.forget", structured_output=True)
    async def forget(
        object_type: str,
        object_id: str,
        hard: bool = False,
        reason: str | None = None,
        confirm: bool = False,
    ) -> dict[str, Any]:
        """Soft delete a Brain object. Hard delete requires confirm=true."""
        if hard and not confirm:
            raise ValueError("brain.forget requires confirm=true for hard deletes.")
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

    return mcp


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
