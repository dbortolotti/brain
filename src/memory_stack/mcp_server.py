from __future__ import annotations

import argparse
import json
import time
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

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
    SEARCH_TYPES,
    DatasourceNotFoundError,
    add_text,
    cognify_dataset,
    create_datasource as create_cognee_datasource,
    delete_datasource as delete_cognee_datasource,
    list_datasources as list_cognee_datasources,
    recall_text,
    remember_text,
)
from memory_stack.config import Settings, load_settings
from memory_stack.name_resolution import (
    load_node_set_registry,
    register_node_sets,
    resolve_dataset_name,
    resolve_node_set_names,
)
from memory_stack.oauth import BrainOAuthProvider, parse_bearer
from memory_stack.request_logging import RequestResponseLogMiddleware

STARTED_AT = time.time()
settings = load_settings()
oauth_provider = BrainOAuthProvider(settings) if settings.brain_auth_enabled else None

app = FastAPI(title="Brain MCP", version="0.1.0")
if settings.brain_request_log_enabled:
    app.add_middleware(RequestResponseLogMiddleware, settings=settings)


class CreateDatasourceRequest(BaseModel):
    name: str


class DeleteDatasourceRequest(BaseModel):
    name: str | None = None
    id: str | None = None


class ProfileEntityRequest(BaseModel):
    name: str
    entity_type: str | None = None
    include_superseded: bool = False
    include_sources: bool = True


class OpenLoopsRequest(BaseModel):
    topic: str | None = None
    status: str = "open"
    limit: int = 20


class ForgetRequest(BaseModel):
    object_type: str
    object_id: str
    hard: bool = False
    reason: str | None = None


class ResolveConflictRequest(BaseModel):
    conflict_memory_id: str
    target_memory_id: str
    action: str
    note: str | None = None


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    headers = dict(exc.headers or {})
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        headers.update({"Cache-Control": "no-store", "Pragma": "no-cache"})
        return JSONResponse(
            exc.detail,
            status_code=exc.status_code,
            headers=headers,
        )
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=headers)


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": settings.brain_service_name,
        "mcp_path": settings.brain_mcp_path,
        "public_mcp_url": settings.public_mcp_url,
        "uptime_seconds": round(time.time() - STARTED_AT, 3),
    }


@app.get("/.well-known/oauth-protected-resource")
@app.get("/.well-known/oauth-protected-resource/{resource_path:path}")
async def oauth_protected_resource(resource_path: str = "") -> dict[str, Any]:
    if oauth_provider:
        return oauth_provider.protected_resource_metadata()

    normalized_resource_path = "/" + resource_path.strip("/")
    resource_url = f"{settings.brain_public_base_url.rstrip('/')}{normalized_resource_path}"
    return {
        "resource": resource_url,
        "resource_name": settings.brain_service_name,
        "authorization_servers": [settings.brain_public_base_url.rstrip("/")],
        "scopes_supported": settings.oauth_scopes,
        "bearer_methods_supported": ["header"],
    }


@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server() -> dict[str, Any]:
    if oauth_provider:
        return oauth_provider.authorization_server_metadata()
    base = settings.brain_public_base_url.rstrip("/")
    return {
        "issuer": base,
        "service": settings.brain_service_name,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/token",
        "registration_endpoint": f"{base}/register",
        "scopes_supported": settings.oauth_scopes,
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
    }


@app.post("/register")
async def register_client(request: Request) -> Response:
    if not oauth_provider:
        raise HTTPException(status_code=404, detail="OAuth is not enabled")
    return await oauth_provider.register_client(request)


@app.api_route("/authorize", methods=["GET", "POST"])
async def authorize(request: Request) -> Response:
    if not oauth_provider:
        raise HTTPException(status_code=404, detail="OAuth is not enabled")
    return await oauth_provider.authorize(request)


@app.post("/token")
async def token(request: Request) -> Response:
    if not oauth_provider:
        raise HTTPException(status_code=404, detail="OAuth is not enabled")
    return await oauth_provider.token(request)


@app.post("/revoke")
async def revoke(request: Request) -> Response:
    if not oauth_provider:
        raise HTTPException(status_code=404, detail="OAuth is not enabled")
    return await oauth_provider.revoke(request)


@app.get("/datasources")
@app.get("/list_datasources")
async def list_datasources_endpoint(
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    return {"datasources": await list_cognee_datasources(settings=settings)}


@app.post("/datasources", status_code=201)
@app.post("/create_datasource", status_code=201)
async def create_datasource_endpoint(
    payload: CreateDatasourceRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    return {
        "datasource": await create_cognee_datasource(payload.name, settings=settings),
    }


@app.delete("/datasources/{datasource}")
@app.delete("/delete_datasource/{datasource}")
async def delete_datasource_path_endpoint(
    datasource: str,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    return {"datasource": await delete_datasource_or_404(datasource)}


@app.post("/delete_datasource")
async def delete_datasource_endpoint(
    payload: DeleteDatasourceRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    datasource = payload.id or payload.name
    if datasource is None:
        raise HTTPException(status_code=422, detail="Provide datasource id or name.")
    return {"datasource": await delete_datasource_or_404(datasource)}


@app.post("/memory/remember")
async def brain_remember_endpoint(
    payload: RememberRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    return brain_remember(payload, settings).model_dump(mode="json")


@app.post("/memory/ingest_source")
async def brain_ingest_source_endpoint(
    payload: RememberRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    request = payload.model_copy(update={"source_policy": "source_and_memory"})
    return brain_remember(request, settings).model_dump(mode="json")


@app.post("/memory/recall")
async def brain_recall_endpoint(
    payload: RecallRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    return brain_recall(payload, settings).model_dump(mode="json")


@app.post("/memory/profile_entity")
async def brain_profile_entity_endpoint(
    payload: ProfileEntityRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    return brain_profile_entity(
        settings,
        name=payload.name,
        entity_type=payload.entity_type,
        include_superseded=payload.include_superseded,
    ).model_dump(mode="json")


@app.get("/memory/open_loops")
async def brain_open_loops_endpoint(
    topic: str | None = None,
    status: str = "open",
    limit: int = 20,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    return {"open_loops": brain_list_open_loops(settings, topic=topic, status=status, limit=limit)}


@app.get("/memory/{memory_id}")
async def brain_get_memory_endpoint(
    memory_id: str,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    memory = brain_get_memory(memory_id, settings)
    if memory is None:
        raise HTTPException(status_code=404, detail=f"Memory not found: {memory_id}")
    return {"memory": memory}


@app.post("/memory/forget")
async def brain_forget_endpoint(
    payload: ForgetRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    return brain_forget(
        settings,
        object_type=payload.object_type,
        object_id=payload.object_id,
        hard=payload.hard,
        reason=payload.reason,
    )


@app.post("/memory/resolve_conflict")
async def brain_resolve_conflict_endpoint(
    payload: ResolveConflictRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    return brain_resolve_conflict(
        settings,
        conflict_memory_id=payload.conflict_memory_id,
        target_memory_id=payload.target_memory_id,
        action=payload.action,
        note=payload.note,
    )


@app.api_route("/{path:path}", methods=["GET", "POST"])
async def mcp_route(
    path: str,
    request: Request,
    authorization: str | None = Header(default=None),
) -> Response:
    requested_path = "/" + path.strip("/")
    if requested_path != settings.brain_mcp_path:
        raise HTTPException(status_code=404, detail="Not found")

    if settings.brain_auth_enabled and not valid_bearer(authorization, settings):
        return auth_challenge(settings)

    if request.method == "GET":
        return JSONResponse(
            {
                "service": settings.brain_service_name,
                "mcp_path": settings.brain_mcp_path,
                "public_mcp_url": settings.public_mcp_url,
                "status": "ready",
            }
        )

    payload = await request.json()
    response_payload = await handle_json_rpc(payload)
    return JSONResponse(response_payload)


def valid_bearer(header_value: str | None, active_settings: Settings) -> bool:
    if active_settings.brain_auth_token:
        expected = f"Bearer {active_settings.brain_auth_token}"
        if header_value == expected:
            return True
    token = parse_bearer(header_value)
    if oauth_provider and token:
        return oauth_provider.validate_access_token(
            token,
            active_settings.brain_auth_scope_list,
        )
    return False


def auth_challenge(active_settings: Settings) -> Response:
    return JSONResponse(
        authentication_required_payload(active_settings),
        status_code=401,
        headers=auth_challenge_headers(active_settings),
    )


def require_api_auth(header_value: str | None, active_settings: Settings) -> None:
    if active_settings.brain_auth_enabled and not valid_bearer(header_value, active_settings):
        raise HTTPException(
            status_code=401,
            detail=authentication_required_payload(active_settings),
            headers=auth_challenge_headers(active_settings),
        )


def authentication_required_payload(active_settings: Settings) -> dict[str, str]:
    return {"error": "authentication_required", "service": active_settings.brain_service_name}


def auth_challenge_headers(active_settings: Settings) -> dict[str, str]:
    return {
        "WWW-Authenticate": (
            'Bearer realm="Brain", '
            f'resource_metadata="{active_settings.protected_resource_metadata_url}", '
            f'scope="{" ".join(active_settings.brain_auth_scope_list)}"'
        )
    }


async def delete_datasource_or_404(datasource: str) -> dict[str, Any]:
    try:
        return await delete_cognee_datasource(datasource, settings=settings)
    except DatasourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


async def handle_json_rpc(payload: Any) -> Any:
    if isinstance(payload, list):
        return [await handle_json_rpc(item) for item in payload]

    request_id = payload.get("id") if isinstance(payload, dict) else None
    method = payload.get("method") if isinstance(payload, dict) else None
    params = payload.get("params", {}) if isinstance(payload, dict) else {}

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "brain", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": "remember",
                        "description": "Store durable memory in Brain. Legacy text+dataset_name calls still write directly to Cognee.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "input": {"type": "string"},
                                "input_type": {
                                    "type": "string",
                                    "default": "auto",
                                    "description": "auto, note, fact, thought, article_url, transcript, chat_summary, or table.",
                                },
                                "observed_at": {"type": "string", "format": "date-time"},
                                "source_policy": {
                                    "type": "string",
                                    "default": "auto",
                                    "enum": ["auto", "memory_only", "source_only", "source_and_memory"],
                                },
                                "dry_run": {"type": "boolean", "default": False},
                                "context": {"type": "object"},
                                "text": {"type": "string"},
                                "dataset_name": {"type": "string"},
                                "temporal": {"type": "boolean", "default": True},
                                "node_set": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Optional Cognee node-set tags for this item.",
                                },
                            },
                            "anyOf": [
                                {"required": ["input"]},
                                {"required": ["text", "dataset_name"]},
                            ],
                        },
                    },
                    {
                        "name": "ingest_source",
                        "description": "Store source material and extract durable Brain memory cards.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "input": {"type": "string"},
                                "input_type": {"type": "string", "default": "auto"},
                                "observed_at": {"type": "string", "format": "date-time"},
                                "context": {"type": "object"},
                                "dry_run": {"type": "boolean", "default": False},
                            },
                            "required": ["input"],
                        },
                    },
                    {
                        "name": "add",
                        "description": "Add text to a Cognee dataset without cognifying it.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "dataset_name": {"type": "string"},
                                "node_set": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Optional Cognee node-set tags for this item.",
                                },
                            },
                            "required": ["text", "dataset_name"],
                        },
                    },
                    {
                        "name": "cognify",
                        "description": "Cognify a Cognee dataset after one or more add calls.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "dataset_name": {"type": "string"},
                                "temporal": {"type": "boolean", "default": True},
                            },
                            "required": ["dataset_name"],
                        },
                    },
                    {
                        "name": "recall",
                        "description": "Recall from Brain memory. Legacy dataset/search_type calls still query Cognee directly.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "mode": {
                                    "type": "string",
                                    "default": "auto",
                                    "enum": ["auto", "evidence", "profile", "open_loops", "sources", "memories"],
                                },
                                "include_sources": {"type": "boolean", "default": True},
                                "include_superseded": {"type": "boolean", "default": False},
                                "limit": {"type": "integer", "default": 20},
                                "dataset": {
                                    "type": "string",
                                    "default": "property_trial",
                                    "description": "Dataset to search. Use an empty string to search all accessible datasets.",
                                },
                                "search_type": {
                                    "type": "string",
                                    "enum": SEARCH_TYPES,
                                    "default": "TEMPORAL",
                                },
                                "top_k": {"type": "integer", "default": 10},
                                "node_name": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Optional Cognee node-set names to scope supported graph search types.",
                                },
                                "node_name_filter_operator": {
                                    "type": "string",
                                    "enum": ["OR", "AND"],
                                    "default": "OR",
                                },
                            },
                            "required": ["query"],
                        },
                    },
                    {
                        "name": "profile_entity",
                        "description": "Build an evidence-aware profile for a Brain entity.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "entity_type": {"type": "string"},
                                "include_superseded": {"type": "boolean", "default": False},
                                "include_sources": {"type": "boolean", "default": True},
                            },
                            "required": ["name"],
                        },
                    },
                    {
                        "name": "list_open_loops",
                        "description": "List Brain open questions and reminder-worthy memory loops.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "topic": {"type": "string"},
                                "status": {"type": "string", "default": "open"},
                                "limit": {"type": "integer", "default": 20},
                            },
                        },
                    },
                    {
                        "name": "get_memory",
                        "description": "Fetch one Brain memory card with entities, relationships, and links.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"memory_id": {"type": "string"}},
                            "required": ["memory_id"],
                        },
                    },
                    {
                        "name": "resolve_conflict",
                        "description": "Resolve a Brain memory conflict with append-only links.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "conflict_memory_id": {"type": "string"},
                                "target_memory_id": {"type": "string"},
                                "action": {
                                    "type": "string",
                                    "enum": [
                                        "supersede",
                                        "keep_both",
                                        "mark_duplicate",
                                        "archive_old",
                                        "reject_new",
                                    ],
                                },
                                "note": {"type": "string"},
                            },
                            "required": ["conflict_memory_id", "target_memory_id", "action"],
                        },
                    },
                    {
                        "name": "forget",
                        "description": "Soft-delete a Brain object. Hard delete is intentionally blocked here.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "object_type": {"type": "string", "enum": ["memory", "source", "entity"]},
                                "object_id": {"type": "string"},
                                "hard": {"type": "boolean", "default": False},
                                "reason": {"type": "string"},
                            },
                            "required": ["object_type", "object_id"],
                        },
                    },
                    {
                        "name": "sync_cognee",
                        "description": "Placeholder for Brain-to-Cognee projection jobs.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "dataset": {"type": "string", "default": "memory"},
                                "limit": {"type": "integer", "default": 100},
                            },
                        },
                    },
                    {
                        "name": "list_datasources",
                        "description": "List Cognee datasources.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                        },
                    },
                    {
                        "name": "list_node_sets",
                        "description": "List known Brain node-set tags.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                        },
                    },
                    {
                        "name": "create_datasource",
                        "description": "Create a Cognee datasource.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                            },
                            "required": ["name"],
                        },
                    },
                    {
                        "name": "create_dataset",
                        "description": "Alias for create_datasource.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                            },
                            "required": ["name"],
                        },
                    },
                    {
                        "name": "create_node_set",
                        "description": "Register a Brain node-set tag for future writes and scoped recall.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                            },
                            "required": ["name"],
                        },
                    },
                    {
                        "name": "delete_datasource",
                        "description": "Delete a Cognee datasource by name or id.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "id": {"type": "string"},
                            },
                        },
                    },
                ]
            }
        elif method == "tools/call":
            result = await call_tool(params)
        elif method and method.startswith("notifications/"):
            return {"jsonrpc": "2.0", "id": request_id, "result": {}}
        else:
            return json_rpc_error(request_id, -32601, f"Unknown method: {method}")
    except Exception as exc:
        return json_rpc_error(request_id, -32000, str(exc))

    return {"jsonrpc": "2.0", "id": request_id, "result": result}


async def call_tool(params: dict[str, Any]) -> dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments") or {}
    if name == "remember":
        if "input" in arguments or "dataset_name" not in arguments:
            request = RememberRequest.model_validate(
                {
                    "input": arguments.get("input", arguments.get("text", "")),
                    "input_type": arguments.get("input_type", "auto"),
                    "observed_at": arguments.get("observed_at"),
                    "source_policy": arguments.get("source_policy", "auto"),
                    "dry_run": bool(arguments.get("dry_run", False)),
                    "context": arguments.get("context") or {},
                }
            )
            return json_tool_response(brain_remember(request, settings).model_dump(mode="json"))

        text = str(arguments["text"])
        dataset_name = await resolve_dataset_name(
            str(arguments["dataset_name"]),
            settings=settings,
        )
        temporal = bool(arguments.get("temporal", True))
        node_set = resolve_node_set_names(
            arguments.get("node_set"),
            settings=settings,
            for_write=True,
        )
        await remember_text(
            text,
            dataset_name=dataset_name,
            temporal=temporal,
            node_set=node_set,
            settings=settings,
        )
        return {"content": [{"type": "text", "text": "remembered"}]}

    if name == "ingest_source":
        request = RememberRequest.model_validate(
            {
                "input": arguments["input"],
                "input_type": arguments.get("input_type", "auto"),
                "observed_at": arguments.get("observed_at"),
                "source_policy": "source_and_memory",
                "dry_run": bool(arguments.get("dry_run", False)),
                "context": arguments.get("context") or {},
            }
        )
        return json_tool_response(brain_remember(request, settings).model_dump(mode="json"))

    if name == "add":
        dataset_name = await resolve_dataset_name(
            str(arguments["dataset_name"]),
            settings=settings,
        )
        node_set = resolve_node_set_names(
            arguments.get("node_set"),
            settings=settings,
            for_write=True,
        )
        await add_text(
            str(arguments["text"]),
            dataset_name=dataset_name,
            node_set=node_set,
            settings=settings,
        )
        return {"content": [{"type": "text", "text": "added"}]}

    if name == "cognify":
        dataset_name = await resolve_dataset_name(
            str(arguments["dataset_name"]),
            settings=settings,
        )
        await cognify_dataset(
            dataset_name,
            temporal=bool(arguments.get("temporal", True)),
            settings=settings,
        )
        return {"content": [{"type": "text", "text": "cognified"}]}

    if name == "recall":
        legacy_recall = any(
            key in arguments
            for key in ("dataset", "search_type", "node_name", "node_name_filter_operator")
        ) and not any(
            key in arguments
            for key in ("mode", "include_sources", "include_superseded", "limit")
        )
        if not legacy_recall:
            request = RecallRequest.model_validate(
                {
                    "query": arguments["query"],
                    "mode": arguments.get("mode", "auto"),
                    "include_sources": bool(arguments.get("include_sources", True)),
                    "include_superseded": bool(arguments.get("include_superseded", False)),
                    "limit": int(arguments.get("limit", arguments.get("top_k", 20))),
                }
            )
            return json_tool_response(brain_recall(request, settings).model_dump(mode="json"))

        raw_dataset = str(arguments.get("dataset", "property_trial")).strip()
        dataset = (
            await resolve_dataset_name(
                raw_dataset,
                settings=settings,
            )
            if raw_dataset
            else None
        )
        node_name = resolve_node_set_names(
            arguments.get("node_name"),
            settings=settings,
            for_write=False,
        )
        result = await recall_text(
            query=str(arguments["query"]),
            dataset=dataset,
            search_type=str(arguments.get("search_type", "TEMPORAL")),
            top_k=int(arguments.get("top_k", 10)),
            node_name=node_name,
            node_name_filter_operator=str(arguments.get("node_name_filter_operator", "OR")),
            settings=settings,
        )
        return {"content": [{"type": "text", "text": str(result)}]}

    if name == "profile_entity":
        return json_tool_response(
            brain_profile_entity(
                settings,
                name=str(arguments["name"]),
                entity_type=arguments.get("entity_type"),
                include_superseded=bool(arguments.get("include_superseded", False)),
            ).model_dump(mode="json")
        )

    if name == "list_open_loops":
        return json_tool_response(
            {
                "open_loops": brain_list_open_loops(
                    settings,
                    topic=arguments.get("topic"),
                    status=str(arguments.get("status", "open")),
                    limit=int(arguments.get("limit", 20)),
                )
            }
        )

    if name == "get_memory":
        memory = brain_get_memory(str(arguments["memory_id"]), settings)
        return json_tool_response({"memory": memory})

    if name == "resolve_conflict":
        return json_tool_response(
            brain_resolve_conflict(
                settings,
                conflict_memory_id=str(arguments["conflict_memory_id"]),
                target_memory_id=str(arguments["target_memory_id"]),
                action=str(arguments["action"]),
                note=arguments.get("note"),
            )
        )

    if name == "forget":
        return json_tool_response(
            brain_forget(
                settings,
                object_type=str(arguments["object_type"]),
                object_id=str(arguments["object_id"]),
                hard=bool(arguments.get("hard", False)),
                reason=arguments.get("reason"),
            )
        )

    if name == "sync_cognee":
        return json_tool_response(
            {
                "status": "not_implemented",
                "detail": "Brain control-plane writes cognee_sync rows; projection worker is a later phase.",
            }
        )

    if name == "list_datasources":
        datasources = await list_cognee_datasources(settings=settings)
        return json_tool_response({"datasources": datasources})

    if name == "list_node_sets":
        return json_tool_response({"node_sets": load_node_set_registry(settings)})

    if name in {"create_datasource", "create_dataset"}:
        datasource = await create_cognee_datasource(str(arguments["name"]), settings=settings)
        return json_tool_response({"datasource": datasource})

    if name == "create_node_set":
        register_node_sets(settings, [str(arguments["name"])])
        return json_tool_response({"node_set": str(arguments["name"])})

    if name == "delete_datasource":
        datasource = arguments.get("id") or arguments.get("name")
        if datasource is None:
            raise ValueError("delete_datasource requires name or id.")
        return json_tool_response(
            {"datasource": await delete_cognee_datasource(str(datasource), settings=settings)}
        )

    raise ValueError(f"Unknown tool: {name}")


def json_tool_response(payload: Any) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(payload, default=str)}]}


def json_rpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=settings.brain_mcp_host)
    parser.add_argument("--port", type=int, default=settings.brain_mcp_port)
    args = parser.parse_args()

    import uvicorn

    uvicorn.run(
        "memory_stack.mcp_server:app",
        host=args.host,
        port=args.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
