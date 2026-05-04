from __future__ import annotations

import json

from memory_stack.cognee_adapter import (
    create_datasource as create_cognee_datasource,
    delete_datasource as delete_cognee_datasource,
    list_datasources as list_cognee_datasources,
    recall_text,
    remember_text,
)
from memory_stack.config import load_settings


def build_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:
        raise RuntimeError("Install MCP support with `uv sync --all-extras`.") from exc

    settings = load_settings()
    mcp = FastMCP("Brain")

    @mcp.tool()
    async def remember(text: str, dataset_name: str, temporal: bool = True) -> str:
        """Store text in Cognee memory."""
        await remember_text(text, dataset_name=dataset_name, temporal=temporal, settings=settings)
        return "remembered"

    @mcp.tool()
    async def recall(
        query: str,
        dataset: str = "property_trial",
        search_type: str = "TEMPORAL",
        top_k: int = 10,
    ) -> str:
        """Recall text from Cognee memory."""
        result = await recall_text(
            query=query,
            dataset=dataset,
            search_type=search_type,
            top_k=top_k,
            settings=settings,
        )
        return str(result)

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
    async def delete_datasource(name: str) -> str:
        """Delete a Cognee datasource by name or id."""
        datasource = await delete_cognee_datasource(name, settings=settings)
        return json.dumps({"datasource": datasource})

    return mcp


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
