from __future__ import annotations

import asyncio
import inspect
from typing import Any

from memory_stack.config import Settings, apply_runtime_environment


class CogneeUnavailableError(RuntimeError):
    """Raised when Cognee is not installed or cannot be imported."""


class DatasourceNotFoundError(ValueError):
    """Raised when a datasource cannot be found in Cognee's dataset table."""


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


async def ensure_cognee_ready() -> None:
    try:
        from cognee.low_level import setup as setup_cognee  # type: ignore
    except Exception:
        from cognee.modules.engine.operations.setup import setup as setup_cognee  # type: ignore

    await maybe_await(setup_cognee())


def serialize_datasource(datasource: Any) -> dict[str, Any]:
    created_at = getattr(datasource, "created_at", None)
    updated_at = getattr(datasource, "updated_at", None)
    owner_id = getattr(datasource, "owner_id", None)
    tenant_id = getattr(datasource, "tenant_id", None)

    return {
        "id": str(getattr(datasource, "id")),
        "name": getattr(datasource, "name", None),
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
        "owner_id": str(owner_id) if owner_id else None,
        "tenant_id": str(tenant_id) if tenant_id else None,
    }


def validate_datasource_name(name: str) -> str:
    normalized = name.strip()
    if not normalized:
        raise ValueError("Datasource name must not be empty.")
    return normalized


async def get_default_cognee_user() -> Any:
    from cognee.modules.users.methods import get_default_user  # type: ignore

    return await maybe_await(get_default_user())


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


async def list_datasources(*, settings: Settings | None = None) -> list[dict[str, Any]]:
    if settings is not None:
        apply_runtime_environment(settings)
    cognee = import_cognee()
    await ensure_cognee_ready()

    if not hasattr(cognee, "datasets") or not hasattr(cognee.datasets, "list_datasets"):
        raise RuntimeError("Installed Cognee package does not expose datasets.list_datasets().")

    datasources = await maybe_await(cognee.datasets.list_datasets())
    return [serialize_datasource(datasource) for datasource in datasources]


async def create_datasource(
    name: str,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    datasource_name = validate_datasource_name(name)
    if settings is not None:
        apply_runtime_environment(settings)
    import_cognee()
    await ensure_cognee_ready()

    from cognee.modules.data.methods import create_authorized_dataset  # type: ignore

    user = await get_default_cognee_user()
    datasource = await maybe_await(create_authorized_dataset(datasource_name, user))
    return serialize_datasource(datasource)


async def delete_datasource(
    datasource: str,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    datasource_ref = validate_datasource_name(datasource)
    if settings is not None:
        apply_runtime_environment(settings)
    cognee = import_cognee()
    await ensure_cognee_ready()

    if not hasattr(cognee, "datasets") or not hasattr(cognee.datasets, "empty_dataset"):
        raise RuntimeError("Installed Cognee package does not expose datasets.empty_dataset().")

    user = await get_default_cognee_user()
    datasources = await maybe_await(cognee.datasets.list_datasets(user=user))
    datasource_record = next(
        (
            candidate
            for candidate in datasources
            if str(getattr(candidate, "id")) == datasource_ref
            or getattr(candidate, "name", None) == datasource_ref
        ),
        None,
    )

    if datasource_record is None:
        raise DatasourceNotFoundError(f"Datasource not found: {datasource_ref}")

    await maybe_await(cognee.datasets.empty_dataset(datasource_record.id, user=user))
    return {
        "id": str(datasource_record.id),
        "name": getattr(datasource_record, "name", None),
        "status": "deleted",
    }


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
