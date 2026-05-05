from __future__ import annotations

import json

from memory_stack.brain_models import RecallRequest, RememberRequest
from memory_stack.brain_service import (
    forget as brain_forget,
    get_memory as brain_get_memory,
    list_open_loops as brain_list_open_loops,
    profile_entity as brain_profile_entity,
    recall as brain_recall,
    remember as brain_remember,
    resolve_conflict as brain_resolve_conflict,
)
from memory_stack.cognee_adapter import (
    add_text,
    cognify_dataset,
    create_datasource as create_cognee_datasource,
    delete_datasource as delete_cognee_datasource,
    list_datasources as list_cognee_datasources,
    recall_text,
    remember_text,
)
from memory_stack.config import load_settings
from memory_stack.name_resolution import (
    load_node_set_registry,
    register_node_sets,
    resolve_dataset_name,
    resolve_node_set_names,
)


def build_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:
        raise RuntimeError("Install MCP support with `uv sync --all-extras`.") from exc

    settings = load_settings()
    mcp = FastMCP("Brain")

    @mcp.tool()
    async def remember(
        input: str | None = None,
        text: str | None = None,
        dataset_name: str | None = None,
        input_type: str = "auto",
        source_policy: str = "auto",
        dry_run: bool = False,
        context: dict | None = None,
        temporal: bool = True,
        node_set: list[str] | None = None,
    ) -> str:
        """Store durable memory in Brain, or use legacy Cognee mode with text+dataset_name."""
        if input is not None or dataset_name is None:
            request = RememberRequest(
                input=input or text or "",
                input_type=input_type,
                source_policy=source_policy,
                dry_run=dry_run,
                context=context or {},
            )
            return json.dumps(brain_remember(request, settings).model_dump(mode="json"))

        resolved_dataset = await resolve_dataset_name(
            dataset_name,
            settings=settings,
        )
        resolved_node_set = resolve_node_set_names(
            node_set,
            settings=settings,
            for_write=True,
        )
        await remember_text(
            text or "",
            dataset_name=resolved_dataset,
            temporal=temporal,
            node_set=resolved_node_set,
            settings=settings,
        )
        return "remembered"

    @mcp.tool()
    async def ingest_source(
        input: str,
        input_type: str = "auto",
        dry_run: bool = False,
        context: dict | None = None,
    ) -> str:
        """Store source material and extract durable Brain memory cards."""
        request = RememberRequest(
            input=input,
            input_type=input_type,
            source_policy="source_and_memory",
            dry_run=dry_run,
            context=context or {},
        )
        return json.dumps(brain_remember(request, settings).model_dump(mode="json"))

    @mcp.tool()
    async def add(
        text: str,
        dataset_name: str,
        node_set: list[str] | None = None,
    ) -> str:
        """Add text to a Cognee dataset without cognifying it."""
        resolved_dataset = await resolve_dataset_name(
            dataset_name,
            settings=settings,
        )
        resolved_node_set = resolve_node_set_names(
            node_set,
            settings=settings,
            for_write=True,
        )
        await add_text(
            text,
            dataset_name=resolved_dataset,
            node_set=resolved_node_set,
            settings=settings,
        )
        return "added"

    @mcp.tool()
    async def cognify(dataset_name: str, temporal: bool = True) -> str:
        """Cognify a Cognee dataset after one or more add calls."""
        resolved_dataset = await resolve_dataset_name(
            dataset_name,
            settings=settings,
        )
        await cognify_dataset(resolved_dataset, temporal=temporal, settings=settings)
        return "cognified"

    @mcp.tool()
    async def recall(
        query: str,
        mode: str = "auto",
        include_sources: bool = True,
        include_superseded: bool = False,
        limit: int = 20,
        dataset: str | None = None,
        search_type: str | None = None,
        top_k: int = 10,
        node_name: list[str] | None = None,
        node_name_filter_operator: str = "OR",
    ) -> str:
        """Recall from Brain memory, or use legacy Cognee mode with dataset/search_type."""
        if dataset is None and search_type is None and node_name is None:
            request = RecallRequest(
                query=query,
                mode=mode,
                include_sources=include_sources,
                include_superseded=include_superseded,
                limit=limit,
            )
            return json.dumps(brain_recall(request, settings).model_dump(mode="json"))

        resolved_dataset = (
            await resolve_dataset_name(
                dataset,
                settings=settings,
            )
            if dataset
            else None
        )
        resolved_node_name = resolve_node_set_names(
            node_name,
            settings=settings,
            for_write=False,
        )
        result = await recall_text(
            query=query,
            dataset=resolved_dataset,
            search_type=search_type or "TEMPORAL",
            top_k=top_k,
            node_name=resolved_node_name,
            node_name_filter_operator=node_name_filter_operator,
            settings=settings,
        )
        return str(result)

    @mcp.tool()
    async def profile_entity(
        name: str,
        entity_type: str | None = None,
        include_superseded: bool = False,
    ) -> str:
        """Build an evidence-aware profile for a Brain entity."""
        return json.dumps(
            brain_profile_entity(
                settings,
                name=name,
                entity_type=entity_type,
                include_superseded=include_superseded,
            ).model_dump(mode="json")
        )

    @mcp.tool()
    async def list_open_loops(
        topic: str | None = None,
        status: str = "open",
        limit: int = 20,
    ) -> str:
        """List Brain open questions and reminder-worthy loops."""
        return json.dumps(
            {
                "open_loops": brain_list_open_loops(
                    settings,
                    topic=topic,
                    status=status,
                    limit=limit,
                )
            },
            default=str,
        )

    @mcp.tool()
    async def get_memory(memory_id: str) -> str:
        """Fetch one Brain memory card."""
        return json.dumps({"memory": brain_get_memory(memory_id, settings)}, default=str)

    @mcp.tool()
    async def resolve_conflict(
        conflict_memory_id: str,
        target_memory_id: str,
        action: str,
        note: str | None = None,
    ) -> str:
        """Resolve a Brain memory conflict with append-only links."""
        return json.dumps(
            brain_resolve_conflict(
                settings,
                conflict_memory_id=conflict_memory_id,
                target_memory_id=target_memory_id,
                action=action,
                note=note,
            ),
            default=str,
        )

    @mcp.tool()
    async def forget(
        object_type: str,
        object_id: str,
        hard: bool = False,
        reason: str | None = None,
    ) -> str:
        """Soft-delete a Brain object."""
        return json.dumps(
            brain_forget(
                settings,
                object_type=object_type,
                object_id=object_id,
                hard=hard,
                reason=reason,
            ),
            default=str,
        )

    @mcp.tool()
    async def sync_cognee(dataset: str = "memory", limit: int = 100) -> str:
        """Placeholder for Brain-to-Cognee projection jobs."""
        del dataset, limit
        return json.dumps(
            {
                "status": "not_implemented",
                "detail": "Brain control-plane writes cognee_sync rows; projection worker is a later phase.",
            }
        )

    @mcp.tool()
    async def list_datasources() -> str:
        """List Cognee datasources."""
        datasources = await list_cognee_datasources(settings=settings)
        return json.dumps({"datasources": datasources})

    @mcp.tool()
    async def create_datasource(name: str) -> str:
        """Create a Cognee datasource."""
        datasource = await create_cognee_datasource(name, settings=settings)
        return json.dumps({"datasource": datasource})

    @mcp.tool()
    async def create_dataset(name: str) -> str:
        """Alias for create_datasource."""
        datasource = await create_cognee_datasource(name, settings=settings)
        return json.dumps({"datasource": datasource})

    @mcp.tool()
    async def list_node_sets() -> str:
        """List known Brain node-set tags."""
        return json.dumps({"node_sets": load_node_set_registry(settings)})

    @mcp.tool()
    async def create_node_set(name: str) -> str:
        """Register a Brain node-set tag."""
        register_node_sets(settings, [name])
        return json.dumps({"node_set": name})

    @mcp.tool()
    async def delete_datasource(name: str) -> str:
        """Delete a Cognee datasource by name or id."""
        datasource = await delete_cognee_datasource(name, settings=settings)
        return json.dumps({"datasource": datasource})

    return mcp


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
