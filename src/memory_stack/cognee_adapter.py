from __future__ import annotations

import asyncio
import inspect
from typing import Any

from memory_stack.config import Settings, apply_runtime_environment


class CogneeUnavailableError(RuntimeError):
    """Raised when Cognee is not installed or cannot be imported."""


def import_cognee() -> Any:
    try:
        import cognee  # type: ignore
    except Exception as exc:
        raise CogneeUnavailableError(
            "Cognee is not importable. Run `uv sync --all-extras` first."
        ) from exc
    return cognee


async def maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def resolve_search_type(search_type: str) -> Any:
    value = search_type.upper()
    try:
        from cognee.api.v1.search import SearchType  # type: ignore

        return SearchType[value]
    except Exception:
        return value


async def remember_text(
    text: str,
    *,
    dataset_name: str,
    temporal: bool = True,
    self_improvement: bool = False,
    settings: Settings | None = None,
) -> Any:
    if settings is not None:
        apply_runtime_environment(settings)
    cognee = import_cognee()

    if hasattr(cognee, "remember"):
        try:
            return await maybe_await(
                cognee.remember(
                    text,
                    dataset_name=dataset_name,
                    temporal_cognify=temporal,
                    self_improvement=self_improvement,
                )
            )
        except TypeError:
            return await maybe_await(cognee.remember(text, dataset_name=dataset_name))

    if hasattr(cognee, "add"):
        await maybe_await(cognee.add(text, dataset_name=dataset_name))
        if hasattr(cognee, "cognify"):
            kwargs: dict[str, Any] = {"datasets": [dataset_name]}
            if temporal:
                kwargs["temporal_cognify"] = True
            try:
                return await maybe_await(cognee.cognify(**kwargs))
            except TypeError:
                return await maybe_await(cognee.cognify(datasets=[dataset_name]))
        return None

    raise RuntimeError("Installed Cognee package exposes neither remember() nor add().")


async def recall_text(
    *,
    query: str,
    dataset: str,
    search_type: str,
    top_k: int = 10,
    settings: Settings | None = None,
) -> Any:
    if settings is not None:
        apply_runtime_environment(settings)
    cognee = import_cognee()
    query_type = resolve_search_type(search_type)

    if hasattr(cognee, "recall"):
        try:
            return await maybe_await(
                cognee.recall(
                    query_text=query,
                    query_type=query_type,
                    datasets=[dataset],
                    top_k=top_k,
                )
            )
        except TypeError:
            return await maybe_await(
                cognee.recall(query_text=query, datasets=[dataset], top_k=top_k)
            )

    if hasattr(cognee, "search"):
        attempts = [
            {"query_text": query, "query_type": query_type, "datasets": [dataset], "top_k": top_k},
            {"query_text": query, "query_type": query_type, "datasets": [dataset]},
            {"query_text": query, "query_type": query_type},
            {"query_text": query},
        ]
        last_error: Exception | None = None
        for kwargs in attempts:
            try:
                return await maybe_await(cognee.search(**kwargs))
            except TypeError as exc:
                last_error = exc
        if last_error is not None:
            raise last_error

    raise RuntimeError("Installed Cognee package exposes neither recall() nor search().")


def run_async(coro: Any) -> Any:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    if loop.is_running():
        raise RuntimeError("Cannot run async Cognee call from an already-running loop.")
    return loop.run_until_complete(coro)

