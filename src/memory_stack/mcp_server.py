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
    get_source as brain_get_source,
    list_open_loops as brain_list_open_loops,
    profile_entity as brain_profile_entity,
    recall as brain_recall,
    remember as brain_remember,
    resolve_conflict as brain_resolve_conflict,
)
from memory_stack.brain_store import BrainStore
from memory_stack.cognee_adapter import (
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
from memory_stack.io import to_jsonable
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


MEMORY_TOOL_NAMES = [
    "brain.remember",
    "brain.ingest_source",
    "brain.recall",
    "brain.profile_entity",
    "brain.list_open_loops",
    "brain.get_memory",
    "brain.get_source",
    "brain.resolve_conflict",
    "brain.forget",
]

TOOL_ALIASES = {
    "remember": "brain.remember",
    "ingest_source": "brain.ingest_source",
    "recall": "brain.recall",
    "profile_entity": "brain.profile_entity",
    "list_open_loops": "brain.list_open_loops",
    "get_memory": "brain.get_memory",
    "get_source": "brain.get_source",
    "resolve_conflict": "brain.resolve_conflict",
    "forget": "brain.forget",
    "sync_cognee": "brain.sync_cognee",
}

INPUT_TYPES = [
    "auto",
    "note",
    "fact",
    "thought",
    "person_interaction",
    "open_question",
    "research_question",
    "chat_conclusion",
    "table",
]
SOURCE_KINDS = [
    "auto",
    "article",
    "transcript",
    "markdown",
    "pdf",
    "email",
    "table",
    "chat_log",
    "other",
]
RECALL_MODES = ["auto", "evidence", "profile", "open_loops", "sources", "memories", "debug"]
ENTITY_TYPES = ["auto", "person", "organization", "place", "concept", "project", "artifact"]
OPEN_LOOP_STATUSES = ["open", "parked", "in_progress", "closed", "archived", "any"]
CONFLICT_ACTIONS = [
    "supersede",
    "keep_both",
    "mark_duplicate",
    "archive_old",
    "reject_new",
    "mark_contradiction",
]
FORGET_OBJECT_TYPES = ["memory", "source", "entity", "relationship", "open_loop"]


def memory_tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "brain.remember",
            "description": "Store a user-level memory, fact, thought, or short note in Brain.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "input": {"type": "string"},
                    "input_type": {"type": "string", "enum": INPUT_TYPES, "default": "auto"},
                    "observed_at": {"type": "string", "format": "date-time"},
                    "source_policy": {
                        "type": "string",
                        "enum": ["auto", "memory_only", "source_only", "source_and_memory"],
                        "default": "auto",
                    },
                    "dry_run": {"type": "boolean", "default": False},
                    "context": {"type": "object", "additionalProperties": True},
                },
                "required": ["input"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain.ingest_source",
            "description": "Store source material and optionally extract durable Brain memories.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "source_kind": {"type": "string", "enum": SOURCE_KINDS, "default": "auto"},
                    "title": {"type": "string"},
                    "why_saved": {"type": "string"},
                    "extract_memories": {"type": "boolean", "default": True},
                    "dry_run": {"type": "boolean", "default": False},
                    "metadata": {"type": "object", "additionalProperties": True},
                },
                "required": ["source"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain.recall",
            "description": "Answer a user-level memory query with evidence.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "mode": {"type": "string", "enum": RECALL_MODES, "default": "auto"},
                    "include_sources": {"type": "boolean", "default": True},
                    "include_superseded": {"type": "boolean", "default": False},
                    "include_conflicts": {"type": "boolean", "default": True},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                    "time_range": {
                        "type": "object",
                        "properties": {
                            "from": {"type": "string", "format": "date-time"},
                            "to": {"type": "string", "format": "date-time"},
                        },
                        "additionalProperties": False,
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain.profile_entity",
            "description": "Build an entity-centric Brain profile.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "entity_type": {"type": "string", "enum": ENTITY_TYPES, "default": "auto"},
                    "include_sources": {"type": "boolean", "default": True},
                    "include_superseded": {"type": "boolean", "default": False},
                    "include_conflicts": {"type": "boolean", "default": True},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50},
                },
                "required": ["name"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain.list_open_loops",
            "description": "List open questions, ideas, reminders, and parked research threads.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "status": {"type": "string", "enum": OPEN_LOOP_STATUSES, "default": "open"},
                    "due_before": {"type": "string", "format": "date-time"},
                    "include_recently_reminded": {"type": "boolean", "default": False},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "brain.get_memory",
            "description": "Read one Brain memory card by id.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string"},
                    "include_links": {"type": "boolean", "default": True},
                    "include_entities": {"type": "boolean", "default": True},
                    "include_source": {"type": "boolean", "default": True},
                },
                "required": ["memory_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain.get_source",
            "description": "Read Brain source metadata and optionally truncated source text.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "source_id": {"type": "string"},
                    "include_text": {"type": "boolean", "default": False},
                    "max_chars": {"type": "integer", "minimum": 1000, "maximum": 100000, "default": 10000},
                },
                "required": ["source_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain.resolve_conflict",
            "description": "Resolve a contradiction or duplicate between two Brain memories.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "conflict_memory_id": {"type": "string"},
                    "target_memory_id": {"type": "string"},
                    "action": {"type": "string", "enum": CONFLICT_ACTIONS},
                    "note": {"type": "string"},
                },
                "required": ["conflict_memory_id", "target_memory_id", "action"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain.forget",
            "description": "Soft delete a Brain object. Hard delete requires confirm=true.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "object_type": {"type": "string", "enum": FORGET_OBJECT_TYPES},
                    "object_id": {"type": "string"},
                    "hard": {"type": "boolean", "default": False},
                    "reason": {"type": "string"},
                    "confirm": {
                        "type": "boolean",
                        "default": False,
                        "description": "Required true for hard deletes.",
                    },
                },
                "required": ["object_type", "object_id"],
                "additionalProperties": False,
            },
        },
    ]


def resource_definitions() -> list[dict[str, str]]:
    return [
        {
            "uri": "brain://schema/memory-card",
            "name": "Brain memory-card schema",
            "mimeType": "application/json",
        },
        {
            "uri": "brain://schema/source",
            "name": "Brain source schema",
            "mimeType": "application/json",
        },
        {
            "uri": "brain://schema/entity",
            "name": "Brain entity schema",
            "mimeType": "application/json",
        },
    ]


def resource_template_definitions() -> list[dict[str, str]]:
    return [
        {"uriTemplate": "brain://memory/{memory_id}", "name": "Brain memory", "mimeType": "application/json"},
        {"uriTemplate": "brain://source/{source_id}", "name": "Brain source", "mimeType": "application/json"},
        {"uriTemplate": "brain://entity/{entity_id}", "name": "Brain entity", "mimeType": "application/json"},
        {"uriTemplate": "brain://open-loop/{loop_id}", "name": "Brain open loop", "mimeType": "application/json"},
        {
            "uriTemplate": "brain://ingestion-run/{run_id}",
            "name": "Brain ingestion run",
            "mimeType": "application/json",
        },
        {
            "uriTemplate": "brain://debug/cognee-sync/{object_id}",
            "name": "Brain Cognee sync debug record",
            "mimeType": "application/json",
        },
        {"uriTemplate": "brain://schema/{schema_name}", "name": "Brain schema", "mimeType": "application/json"},
    ]


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
                "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {"name": "brain", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {"tools": memory_tool_definitions()}
        elif method == "resources/list":
            result = {"resources": resource_definitions()}
        elif method == "resources/templates/list":
            result = {"resourceTemplates": resource_template_definitions()}
        elif method == "resources/read":
            result = read_resource(str(params.get("uri", "")))
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
    raw_name = str(params.get("name") or "")
    name = TOOL_ALIASES.get(raw_name, raw_name)
    arguments = params.get("arguments") or {}
    if name == "brain.remember":
        if raw_name == "remember" and "dataset_name" in arguments and "input" not in arguments:
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
            return json_tool_response(
                {"status": "remembered"},
                summary="Remembered legacy Cognee text.",
            )

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
        payload = brain_remember(request, settings).model_dump(mode="json")
        return json_tool_response(payload, summary=remember_summary(payload))

    if name == "brain.ingest_source":
        if "source" in arguments:
            request = RememberRequest.model_validate(
                {
                    "input": arguments["source"],
                    "input_type": input_type_for_source_kind(
                        str(arguments.get("source_kind", "auto")),
                        str(arguments["source"]),
                    ),
                    "source_policy": (
                        "source_and_memory"
                        if bool(arguments.get("extract_memories", True))
                        else "source_only"
                    ),
                    "dry_run": bool(arguments.get("dry_run", False)),
                    "context": {
                        "title": arguments.get("title"),
                        "why_saved": arguments.get("why_saved"),
                        "metadata": arguments.get("metadata") or {},
                        "source_kind": arguments.get("source_kind", "auto"),
                    },
                }
            )
        else:
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
        receipt = brain_remember(request, settings).model_dump(mode="json")
        payload = {
            "source_id": receipt.get("source", {}).get("source_id"),
            "status": "processed",
            "memory_cards_created": [
                card["id"] for card in receipt.get("memory_cards", []) if card.get("created")
            ],
            "summary": source_summary_from_request(arguments),
            "cognee_sync_status": receipt.get("cognee_sync_status", "pending"),
            "ingestion": receipt,
        }
        return json_tool_response(
            payload,
            summary=(
                f"Ingested source and created {len(payload['memory_cards_created'])} memories."
            ),
        )

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

    if name == "brain.recall":
        legacy_recall = raw_name == "recall" and any(
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
            payload = brain_recall(request, settings).model_dump(mode="json")
            return json_tool_response(payload, summary=payload.get("answer", "Recall complete."))

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
        return json_tool_response({"result": result}, summary="Legacy Cognee recall complete.")

    if name == "brain.profile_entity":
        entity_type = arguments.get("entity_type")
        if entity_type == "auto":
            entity_type = None
        payload = brain_profile_entity(
            settings,
            name=str(arguments["name"]),
            entity_type=entity_type,
            include_superseded=bool(arguments.get("include_superseded", False)),
        ).model_dump(mode="json")
        return json_tool_response(payload, summary=payload.get("answer", "Profile complete."))

    if name == "brain.list_open_loops":
        payload = {
            "open_loops": brain_list_open_loops(
                settings,
                topic=arguments.get("topic"),
                status=str(arguments.get("status", "open")),
                limit=int(arguments.get("limit", 20)),
            )
        }
        return json_tool_response(
            payload,
            summary=f"Found {len(payload['open_loops'])} open loops.",
        )

    if name == "brain.get_memory":
        memory = brain_get_memory(str(arguments["memory_id"]), settings)
        return json_tool_response(
            {"memory": memory},
            summary="Memory found." if memory else "Memory not found.",
        )

    if name == "brain.get_source":
        max_chars = bounded_int(arguments.get("max_chars", 10_000), minimum=1_000, maximum=100_000)
        source = brain_get_source(
            str(arguments["source_id"]),
            settings,
            include_text=bool(arguments.get("include_text", False)),
            max_chars=max_chars,
        )
        payload = {
            "source": source_without_text(source),
            "text": source.get("text") if source and "text" in source else None,
        }
        return json_tool_response(
            payload,
            summary="Source found." if source else "Source not found.",
        )

    if name == "brain.resolve_conflict":
        payload = brain_resolve_conflict(
            settings,
            conflict_memory_id=str(arguments["conflict_memory_id"]),
            target_memory_id=str(arguments["target_memory_id"]),
            action=str(arguments["action"]),
            note=arguments.get("note"),
        )
        return json_tool_response(
            normalize_conflict_resolution(payload),
            summary=f"Conflict action applied: {payload.get('action')}.",
        )

    if name == "brain.forget":
        hard = bool(arguments.get("hard", False))
        if hard and not bool(arguments.get("confirm", False)):
            raise ValueError("brain.forget requires confirm=true for hard deletes.")
        payload = brain_forget(
            settings,
            object_type=str(arguments["object_type"]),
            object_id=str(arguments["object_id"]),
            hard=hard,
            reason=arguments.get("reason"),
        )
        mode = "hard" if hard else "soft"
        payload = {**payload, "mode": mode, "cognee_sync_status": "stale"}
        return json_tool_response(payload, summary=f"{mode.title()} delete result: {payload['status']}.")

    if name == "brain.sync_cognee":
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

    raise ValueError(f"Unknown tool: {raw_name}")


def input_type_for_source_kind(source_kind: str, source: str) -> str:
    normalized = source_kind.strip().lower()
    if normalized == "auto":
        if source.startswith(("http://", "https://")):
            return "article_url"
        return "source_text"
    mapping = {
        "article": "article_url" if source.startswith(("http://", "https://")) else "article",
        "transcript": "transcript",
        "markdown": "markdown",
        "table": "table",
        "chat_log": "transcript",
        "pdf": "source_text",
        "email": "source_text",
        "other": "source_text",
    }
    return mapping.get(normalized, "source_text")


def source_summary_from_request(arguments: dict[str, Any]) -> str | None:
    for key in ("title", "why_saved", "source", "input"):
        value = arguments.get(key)
        if value:
            return str(value)[:500]
    return None


def remember_summary(payload: dict[str, Any]) -> str:
    memory_count = len(payload.get("memory_cards", []))
    entity_count = len(payload.get("entities", []))
    conflict_count = len(payload.get("conflicts", []))
    return (
        f"Stored {memory_count} memories and created or matched {entity_count} entities. "
        f"{conflict_count} conflicts detected."
    )


def bounded_int(value: Any, *, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, int(value)))


def source_without_text(source: dict[str, Any] | None) -> dict[str, Any] | None:
    if source is None:
        return None
    return {key: value for key, value in source.items() if key != "text"}


def normalize_conflict_resolution(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "status": "resolved",
        "action": payload.get("action"),
        "created_links": [],
        "updated_memories": [],
        **payload,
    }
    link = payload.get("link")
    if link:
        normalized["created_links"] = [
            {
                "from_memory_id": link.get("from_memory_id"),
                "relation": link.get("relation"),
                "to_memory_id": link.get("to_memory_id"),
            }
        ]
    return normalized


def read_resource(uri: str) -> dict[str, Any]:
    payload = resource_payload(uri)
    if payload is None:
        raise ValueError(f"Unknown Brain resource: {uri}")
    return {
        "contents": [
            {
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(payload, default=str),
            }
        ]
    }


def resource_payload(uri: str) -> Any:
    store = BrainStore(settings)
    if uri == "brain://schema/memory-card":
        return {"schema": "memory-card", "fields": list(schema_field_names("memory_cards"))}
    if uri == "brain://schema/source":
        return {"schema": "source", "fields": list(schema_field_names("sources"))}
    if uri == "brain://schema/entity":
        return {"schema": "entity", "fields": list(schema_field_names("entities"))}
    prefix_handlers = {
        "brain://memory/": store.get_memory,
        "brain://entity/": store.get_entity,
        "brain://open-loop/": store.get_open_loop,
        "brain://ingestion-run/": store.get_ingestion_run,
        "brain://debug/cognee-sync/": store.get_cognee_sync,
    }
    for prefix, handler in prefix_handlers.items():
        if uri.startswith(prefix):
            return handler(uri.removeprefix(prefix))
    if uri.startswith("brain://source/"):
        return store.get_source(uri.removeprefix("brain://source/"), include_text=False)
    if uri.startswith("brain://schema/"):
        schema_name = uri.removeprefix("brain://schema/")
        return {"schema": schema_name, "error": "unknown schema"}
    return None


def schema_field_names(name: str) -> list[str]:
    from memory_stack import brain_schema

    table = getattr(brain_schema, name)
    return [column.name for column in table.columns]


def json_tool_response(payload: Any, *, summary: str | None = None) -> dict[str, Any]:
    structured = to_jsonable(payload)
    json_text = json.dumps(structured, default=str)
    return {
        "content": [
            {"type": "text", "text": summary or "Brain tool call complete."},
            {"type": "text", "text": json_text},
        ],
        "structuredContent": structured,
        "isError": False,
    }


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
