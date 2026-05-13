from __future__ import annotations

import asyncio
import inspect
from contextlib import asynccontextmanager
from typing import Any

from memory_stack.config import Settings, apply_runtime_environment
from memory_stack.cognee.oauth_compat import prepare_cognee_oauth_runtime


class CogneeUnavailableError(RuntimeError):
    """Raised when Cognee is not installed or cannot be imported."""


class DatasourceNotFoundError(ValueError):
    """Raised when a datasource cannot be found in Cognee's dataset table."""


SEARCH_TYPES = [
    "SUMMARIES",
    "CHUNKS",
    "RAG_COMPLETION",
    "TRIPLET_COMPLETION",
    "GRAPH_COMPLETION",
    "GRAPH_COMPLETION_DECOMPOSITION",
    "GRAPH_SUMMARY_COMPLETION",
    "CYPHER",
    "NATURAL_LANGUAGE",
    "GRAPH_COMPLETION_COT",
    "GRAPH_COMPLETION_CONTEXT_EXTENSION",
    "FEELING_LUCKY",
    "TEMPORAL",
    "CODING_RULES",
    "CHUNKS_LEXICAL",
]
NODE_NAME_FILTER_OPERATORS = {"AND", "OR"}


def import_cognee() -> Any:
    try:
        import cognee  # type: ignore
    except Exception as exc:
        raise CogneeUnavailableError(
            "Cognee is not importable. Run `uv sync --all-extras` first."
        ) from exc
    return cognee


def refresh_cognee_runtime(settings: Settings | None, *, prepare_oauth: bool = True) -> None:
    if settings is None:
        return
    apply_runtime_environment(settings)
    if prepare_oauth:
        prepare_cognee_oauth_runtime(settings)
    for module_name, function_name in (
        ("cognee.base_config", "get_base_config"),
        ("cognee.infrastructure.databases.graph.config", "get_graph_config"),
        ("cognee.infrastructure.databases.vector.config", "get_vectordb_config"),
        ("cognee.infrastructure.databases.relational.config", "get_relational_config"),
    ):
        try:
            module = __import__(module_name, fromlist=[function_name])
            function = getattr(module, function_name, None)
        except Exception:
            continue
        if hasattr(function, "cache_clear"):
            function.cache_clear()


async def maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


@asynccontextmanager
async def cognee_execution_context(settings: Settings | None):
    yield


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


def normalize_optional_string_list(value: Any, *, field_name: str) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list | tuple | set):
        items = list(value)
    else:
        raise ValueError(f"{field_name} must be a string or list of strings.")

    normalized = [str(item).strip() for item in items if str(item).strip()]
    return normalized or None


def normalize_node_name_filter_operator(value: str) -> str:
    normalized = value.strip().upper()
    if normalized not in NODE_NAME_FILTER_OPERATORS:
        raise ValueError("node_name_filter_operator must be either AND or OR.")
    return normalized


async def remember_text(
    text: str,
    *,
    dataset_name: str,
    temporal: bool = True,
    self_improvement: bool = False,
    node_set: list[str] | None = None,
    settings: Settings | None = None,
) -> Any:
    if settings is not None:
        refresh_cognee_runtime(settings)
    cognee = import_cognee()
    refresh_cognee_runtime(settings, prepare_oauth=False)
    normalized_node_set = normalize_optional_string_list(node_set, field_name="node_set")

    async with cognee_execution_context(settings):
        if hasattr(cognee, "remember"):
            kwargs: dict[str, Any] = {
                "dataset_name": dataset_name,
                "temporal_cognify": temporal,
                "self_improvement": self_improvement,
            }
            if normalized_node_set is not None:
                kwargs["node_set"] = normalized_node_set
            try:
                return await maybe_await(cognee.remember(text, **kwargs))
            except TypeError:
                return await maybe_await(cognee.remember(text, dataset_name=dataset_name))

        if hasattr(cognee, "add"):
            add_kwargs: dict[str, Any] = {"dataset_name": dataset_name}
            if normalized_node_set is not None:
                add_kwargs["node_set"] = normalized_node_set
            await maybe_await(cognee.add(text, **add_kwargs))
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


async def add_text(
    text: str,
    *,
    dataset_name: str,
    node_set: list[str] | None = None,
    settings: Settings | None = None,
) -> Any:
    if settings is not None:
        refresh_cognee_runtime(settings)
    cognee = import_cognee()
    refresh_cognee_runtime(settings, prepare_oauth=False)
    if not hasattr(cognee, "add"):
        raise RuntimeError("Installed Cognee package does not expose add().")

    kwargs: dict[str, Any] = {"dataset_name": dataset_name}
    normalized_node_set = normalize_optional_string_list(node_set, field_name="node_set")
    if normalized_node_set is not None:
        kwargs["node_set"] = normalized_node_set
    async with cognee_execution_context(settings):
        return await maybe_await(cognee.add(text, **kwargs))


async def cognify_dataset(
    dataset_name: str,
    *,
    temporal: bool = True,
    settings: Settings | None = None,
) -> Any:
    if settings is not None:
        refresh_cognee_runtime(settings)
    cognee = import_cognee()
    refresh_cognee_runtime(settings, prepare_oauth=False)
    if not hasattr(cognee, "cognify"):
        raise RuntimeError("Installed Cognee package does not expose cognify().")

    kwargs: dict[str, Any] = {"datasets": [dataset_name]}
    if temporal:
        kwargs["temporal_cognify"] = True
    async with cognee_execution_context(settings):
        try:
            return await maybe_await(cognee.cognify(**kwargs))
        except TypeError:
            return await maybe_await(cognee.cognify(datasets=[dataset_name]))


async def list_datasources(*, settings: Settings | None = None) -> list[dict[str, Any]]:
    if settings is not None:
        refresh_cognee_runtime(settings)
    cognee = import_cognee()
    refresh_cognee_runtime(settings, prepare_oauth=False)
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
        refresh_cognee_runtime(settings)
    import_cognee()
    refresh_cognee_runtime(settings, prepare_oauth=False)
    await ensure_cognee_ready()

    from cognee.modules.data.methods import create_authorized_dataset  # type: ignore

    user = await get_default_cognee_user()
    datasource = await maybe_await(create_authorized_dataset(datasource_name, user))
    return serialize_datasource(datasource)


async def ensure_datasources_ready(
    names: list[str],
    *,
    settings: Settings | None = None,
) -> list[dict[str, Any]]:
    datasource_names = sorted({validate_datasource_name(name) for name in names})
    if settings is not None:
        refresh_cognee_runtime(settings)
    import_cognee()
    refresh_cognee_runtime(settings, prepare_oauth=False)
    await ensure_cognee_ready()

    from cognee.modules.data.methods import create_authorized_dataset  # type: ignore

    user = await get_default_cognee_user()
    datasources = []
    for datasource_name in datasource_names:
        datasource = await maybe_await(create_authorized_dataset(datasource_name, user))
        datasources.append(serialize_datasource(datasource))
    return datasources


async def delete_datasource(
    datasource: str,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    datasource_ref = validate_datasource_name(datasource)
    if settings is not None:
        refresh_cognee_runtime(settings)
    cognee = import_cognee()
    refresh_cognee_runtime(settings, prepare_oauth=False)
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
    dataset: str | None,
    search_type: str,
    top_k: int = 10,
    node_name: list[str] | None = None,
    node_name_filter_operator: str = "OR",
    settings: Settings | None = None,
) -> Any:
    if settings is not None:
        refresh_cognee_runtime(settings)
    cognee = import_cognee()
    refresh_cognee_runtime(settings, prepare_oauth=False)
    query_type = resolve_search_type(search_type)
    datasets = [dataset] if dataset else None
    normalized_node_name = normalize_optional_string_list(node_name, field_name="node_name")
    normalized_operator = normalize_node_name_filter_operator(node_name_filter_operator)

    if hasattr(cognee, "recall"):
        kwargs: dict[str, Any] = {
            "query_text": query,
            "query_type": query_type,
            "datasets": datasets,
            "top_k": top_k,
        }
        if normalized_node_name is not None:
            kwargs["node_name"] = normalized_node_name
            kwargs["node_name_filter_operator"] = normalized_operator
        try:
            return await maybe_await(cognee.recall(**kwargs))
        except TypeError:
            return await maybe_await(cognee.recall(query_text=query, datasets=datasets, top_k=top_k))

    if hasattr(cognee, "search"):
        scoped_kwargs: dict[str, Any] = {}
        if normalized_node_name is not None:
            scoped_kwargs["node_name"] = normalized_node_name
            scoped_kwargs["node_name_filter_operator"] = normalized_operator
        attempts = [
            {
                "query_text": query,
                "query_type": query_type,
                "datasets": datasets,
                "top_k": top_k,
                **scoped_kwargs,
            },
            {"query_text": query, "query_type": query_type, "datasets": datasets, **scoped_kwargs},
            {"query_text": query, "query_type": query_type, "datasets": datasets, "top_k": top_k},
            {"query_text": query, "query_type": query_type, "datasets": datasets},
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
