from __future__ import annotations

import argparse
from collections import defaultdict, deque
from dataclasses import dataclass
import hashlib
import hmac
import json
import secrets
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from fastapi import Cookie, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

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
from memory_stack.brain_store import BrainStore, normalize_user_id
from memory_stack.cognee_adapter import (
    DatasourceNotFoundError,
    create_datasource as create_cognee_datasource,
    delete_datasource as delete_cognee_datasource,
    improve_cognee,
    list_datasources as list_cognee_datasources,
)
from memory_stack.cfg import Settings, load_settings, normalize_path
from memory_stack.domain_constants import (
    COGNEE_IMPROVE_DATASETS,
    ENTITY_TYPES,
    FORGET_OBJECT_TYPES,
    INPUT_TYPES,
    RECALL_MODES,
    SOURCE_KINDS,
)
from memory_stack.icon_assets import (
    BRAIN_FAVICON_PATH,
    BRAIN_ICON_PATH,
    brain_icon_metadata,
)
from memory_stack.io import to_jsonable
from memory_stack.oauth import (
    BrainOAuthProvider,
    auth_users_admin_payload,
    ensure_auth_password,
    load_auth_users,
    migrate_verified_password,
    parse_bearer,
    parse_scope,
    public_auth_user,
    set_user_password,
    verify_password,
    write_auth_users,
)
from memory_stack.profile_context import (
    forget_profile_context,
    list_profile_context,
    remember_profile_context,
    sync_profile_context,
)
from memory_stack.request_logging import RequestResponseLogMiddleware
from memory_stack.session import brain_session_payload
from memory_stack.taste.models import (
    TasteDescribeRequest,
    TasteLogDecisionRequest,
    TasteQueryRequest,
    TasteRefreshRequest,
    TasteRememberRequest,
)
from memory_stack.taste.service import TasteService

STARTED_AT = time.time()
settings = load_settings()


def build_oauth_provider(active_settings: Settings) -> BrainOAuthProvider | None:
    if not active_settings.brain_auth_users_file:
        return None
    try:
        return BrainOAuthProvider(active_settings)
    except (FileNotFoundError, ValueError):
        return None


oauth_provider = build_oauth_provider(settings)
SUPPORTED_MCP_PROTOCOL_VERSIONS = {"2024-11-05", "2025-11-25"}
DEFAULT_MCP_PROTOCOL_VERSION = "2024-11-05"
MCP_SURFACE_INTERNAL = "internal"
WEB_SESSION_COOKIE = "brain_web_session"
WEB_SESSION_SECONDS = 12 * 60 * 60
OAUTH_RATE_LIMITS = {
    "register": (20, 60),
    "authorize": (60, 60),
    "token": (30, 60),
    "revoke": (30, 60),
    "login": (20, 60),
}
_rate_limit_buckets: dict[str, deque[float]] = defaultdict(deque)

app = FastAPI(title="Brain MCP", version="0.1.0")
if settings.brain_request_log_enabled:
    app.add_middleware(RequestResponseLogMiddleware, settings=settings)


@app.middleware("http")
async def redirect_public_http_to_https(request: Request, call_next):
    redirect_url = public_https_redirect_url(request)
    if redirect_url is not None:
        response = RedirectResponse(redirect_url, status_code=307)
    else:
        response = await call_next(request)
    add_security_headers(response)
    return response


class CreateDatasourceRequest(BaseModel):
    name: str


class DeleteDatasourceRequest(BaseModel):
    name: str | None = None
    id: str | None = None


@dataclass(frozen=True)
class McpAuthContext:
    authenticated: bool = False
    static_token: bool = False
    web_session: bool = False
    token: str | None = None
    client_id: str | None = None
    user_id: str | None = None
    scopes: tuple[str, ...] = ()
    remote_addr: str | None = None


@dataclass(frozen=True)
class McpRequestContext:
    auth: McpAuthContext
    remote_addr: str | None = None
    json_rpc_id: Any = None


class ProfileEntityRequest(BaseModel):
    name: str
    entity_type: str | None = None
    include_superseded: bool = False
    include_conflicts: bool = True


class ForgetRequest(BaseModel):
    object_type: str
    object_id: str
    hard: bool = False
    reason: str | None = None


class ReviewRecentRequest(BaseModel):
    since: str | None = None
    limit: int = 20


class UndoLastRequest(BaseModel):
    ingestion_run_id: str | None = None


class CogneeImproveRequest(BaseModel):
    dataset: str = "memory"
    node_name: list[str] | None = None
    run_in_background: bool = False


class BrainProfileContextRememberRequest(BaseModel):
    statement: str
    scope: str = "answer_tailoring"
    source: str | None = None


class BrainProfileContextForgetRequest(BaseModel):
    context_id: str


class BrainBiasContextRememberRequest(BaseModel):
    statement: str
    scope: str = "response_style"
    source: str | None = None


class BrainBiasContextForgetRequest(BaseModel):
    context_id: str


class AuthUserCreateRequest(BaseModel):
    id: str
    password: str
    display_name: str | None = None
    email: str | None = None
    superuser: bool = False


class AuthUserUpdateRequest(BaseModel):
    password: str | None = None
    display_name: str | None = None
    email: str | None = None
    superuser: bool | None = None


class PersonalAccessTokenCreateRequest(BaseModel):
    user_id: str
    name: str
    scopes: list[str] | str | None = None
    expires_in_seconds: int | None = None


class LoginRequest(BaseModel):
    user_id: str
    password: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


def memory_tool_definitions(surface: str = MCP_SURFACE_INTERNAL) -> list[dict[str, Any]]:
    tools = [
        {
            "name": "brain_session",
            "description": (
                "Resolve the active user's Brain profile and preference context for agents."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_remember",
            "description": (
                "Store a user-level memory, fact, thought, or short note in Brain. "
                "High-confidence palate memories may route to Brain Palate automatically. "
                "Do not use this for read-only palate describe/enrich requests; use "
                "brain_palate_describe_item instead."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "input": {"type": "string"},
                    "input_type": {"type": "string", "enum": INPUT_TYPES, "default": "auto"},
                    "observed_at": {"type": "string", "format": "date-time"},
                    "dry_run": {"type": "boolean", "default": False},
                    "context": {"type": "object", "additionalProperties": True},
                },
                "required": ["input"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_profile_context_remember",
            "description": (
                "Store a stable user-profile fact that should always be returned "
                "by brain_session to tailor future answers."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "statement": {"type": "string"},
                    "scope": {
                        "type": "string",
                        "default": "answer_tailoring",
                        "description": "Why this standing context should be loaded.",
                    },
                    "source": {"type": "string"},
                    "context": {"type": "object", "additionalProperties": True},
                },
                "required": ["statement"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_profile_context_list",
            "description": "List standing user-profile context returned by brain_session.",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_profile_context_forget",
            "description": "Remove one standing user-profile context item by id.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "context_id": {"type": "string"},
                    "context": {"type": "object", "additionalProperties": True},
                },
                "required": ["context_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_bias_context_remember",
            "description": (
                "Store a durable user preference, constraint, or response-style bias "
                "in Brain's control store."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "statement": {"type": "string"},
                    "scope": {
                        "type": "string",
                        "default": "response_style",
                        "description": "Preference or bias scope, such as response_style or engineering.",
                    },
                    "source": {"type": "string"},
                    "context": {"type": "object", "additionalProperties": True},
                },
                "required": ["statement"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_bias_context_list",
            "description": "List durable user preferences, constraints, and response-style biases.",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_bias_context_forget",
            "description": "Remove one durable user bias/preference context item by id.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "context_id": {"type": "string"},
                    "context": {"type": "object", "additionalProperties": True},
                },
                "required": ["context_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_profile_context_sync",
            "description": (
                "Project all standing profile-context items into the normal Brain "
                "memory/entity graph linked to the configured owner entity."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_ingest_source",
            "description": (
                "Store source material in Brain through Cognee remember. "
                "Brain may detect palate mentions, but large source ingestion avoids "
                "mass palate enrichment/writes without confirmation."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "source_kind": {"type": "string", "enum": SOURCE_KINDS, "default": "auto"},
                    "title": {"type": "string"},
                    "why_saved": {"type": "string"},
                    "dry_run": {"type": "boolean", "default": False},
                    "run_in_background": {
                        "type": "boolean",
                        "description": (
                            "When omitted, Brain queues large non-dry-run sources "
                            "according to BRAIN_INGEST_BACKGROUND_AUTO_CHARS."
                        ),
                    },
                    "metadata": {"type": "object", "additionalProperties": True},
                },
                "required": ["source"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_recall",
            "description": (
                "Answer a user-level memory query with evidence. Recommendation-style "
                "palate queries may use Brain Palate ranking."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "mode": {"type": "string", "enum": RECALL_MODES, "default": "auto"},
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
            "name": "brain_profile_entity",
            "description": "Build an entity-centric Brain profile.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "entity_type": {"type": "string", "enum": ENTITY_TYPES, "default": "auto"},
                    "include_superseded": {"type": "boolean", "default": False},
                    "include_conflicts": {"type": "boolean", "default": True},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50},
                },
                "required": ["name"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_forget",
            "description": (
                "Forget a Cognee-backed Brain remember object via cognee.forget and "
                "write a status-event datapoint only as audit evidence. Hard delete "
                "requires confirm=true."
            ),
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
        {
            "name": "brain_review_recent",
            "description": "Review recent Brain control receipts, pending confirmations, and context records.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "since": {"type": "string", "format": "date-time"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_undo_last",
            "description": "Soft-delete objects created by one recent ingestion run.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ingestion_run_id": {"type": "string"},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "cognee_improve",
            "description": "Run Cognee native improve on a configured Brain dataset.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "dataset": {"type": "string", "enum": COGNEE_IMPROVE_DATASETS, "default": "memory"},
                    "node_name": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional Cognee node-name filter.",
                    },
                    "run_in_background": {"type": "boolean", "default": False},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_palate_describe_item",
            "description": (
                "Read-only palate describe/enrich tool. Use this when the user asks to "
                "use palate to describe, look up, normalize, or enrich a restaurant, wine, "
                "film, series, music, cigar, or other taste item without saving it. "
                "For example: 'use palate to describe Junsei restaurant in London'. "
                "This must not store palate data."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "item_text": {
                        "type": "string",
                        "description": (
                            "The item plus useful disambiguating context, e.g. "
                            "'Junsei restaurant in London'."
                        ),
                    },
                    "entity_type": {
                        "type": "string",
                        "description": (
                            "Palate item type. Use 'restaurant' for restaurant/place "
                            "lookups such as Junsei in London."
                        ),
                    },
                    "canonical_name": {"type": "string"},
                    "attributes": {"type": "object", "additionalProperties": True},
                    "attribute_intervals_95": {"type": "object", "additionalProperties": True},
                    "metadata": {"type": "object", "additionalProperties": True},
                    "notes": {"type": "string"},
                    "fetch_external_ratings": {"type": "boolean", "default": True},
                    "allow_broader_web_search": {"type": "boolean", "default": False},
                },
                "required": ["item_text", "entity_type"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_palate_remember",
            "description": "Store an approved normalized palate item in the canonical palate store and project Brain evidence.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string"},
                    "canonical_name": {"type": "string"},
                    "description": {"type": "string"},
                    "attributes": {"type": "object", "additionalProperties": True},
                    "attribute_intervals_95": {"type": "object", "additionalProperties": True},
                    "rating": {"type": "number"},
                    "tried": {"type": "boolean"},
                    "watched": {"type": "boolean"},
                    "listened": {"type": "boolean"},
                    "wanted": {"type": "boolean"},
                    "recommended_by": {"type": "string"},
                    "disliked": {"type": "boolean"},
                    "avoid": {"type": "boolean"},
                    "not_my_style": {"type": "boolean"},
                    "bad_fit": {"type": "boolean"},
                    "notes": {"type": "string"},
                    "metadata": {"type": "object", "additionalProperties": True},
                    "dry_run": {"type": "boolean", "default": False},
                    "store_anyway": {"type": "boolean", "default": False},
                    "context": {"type": "object", "additionalProperties": True},
                    "fetch_external_ratings": {"type": "boolean", "default": True},
                    "allow_broader_web_search": {"type": "boolean", "default": False},
                },
                "required": ["type", "canonical_name", "description"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_palate_query",
            "description": (
                "Rank already-saved canonical palate records for a recommendation or "
                "comparison query. Do not use this to describe, look up, enrich, or "
                "check a single named unsaved item such as Junsei; call "
                "brain_palate_describe_item for that."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "context": {"type": "object", "additionalProperties": True},
                    "options_text": {"type": "string"},
                    "explain": {"type": "boolean", "default": False},
                    "intent": {"type": "object", "additionalProperties": True},
                    "extracted_entities": {
                        "type": "array",
                        "items": {"type": "object", "additionalProperties": True},
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_palate_evaluate_options",
            "description": (
                "Rank only supplied options against already-saved canonical palate records. "
                "Do not use this to describe, look up, enrich, or check one named item; "
                "call brain_palate_describe_item for read-only item descriptions."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "options_text": {"type": "string"},
                    "context": {"type": "object", "additionalProperties": True},
                    "explain": {"type": "boolean", "default": False},
                    "intent": {"type": "object", "additionalProperties": True},
                    "extracted_entities": {
                        "type": "array",
                        "items": {"type": "object", "additionalProperties": True},
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_palate_log_decision",
            "description": "Record which palate item was chosen after a recommendation.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "chosen_taste_item_id": {"type": "string"},
                    "decision_id": {"type": "string"},
                    "query": {"type": "string"},
                    "context": {"type": "object", "additionalProperties": True},
                },
                "required": ["chosen_taste_item_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_palate_confirm",
            "description": "Confirm a pending palate proposal by proposal_id.",
            "inputSchema": {
                "type": "object",
                "properties": {"proposal_id": {"type": "string"}},
                "required": ["proposal_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_palate_cancel",
            "description": "Cancel a pending palate proposal by proposal_id.",
            "inputSchema": {
                "type": "object",
                "properties": {"proposal_id": {"type": "string"}},
                "required": ["proposal_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_palate_correct_proposal",
            "description": "Apply a free-text correction to a pending palate proposal.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "proposal_id": {"type": "string"},
                    "correction": {"type": "string"},
                },
                "required": ["proposal_id", "correction"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_palate_refresh_enrichment",
            "description": "Refresh enrichment for one canonical palate item.",
            "inputSchema": {
                "type": "object",
                "properties": {"taste_item_id": {"type": "string"}},
                "required": ["taste_item_id"],
                "additionalProperties": False,
            },
        },
    ]
    return tools_with_output_schemas(tools, surface=surface)


def tool_available_on_surface(tool_name: str, surface: str) -> bool:
    if surface == MCP_SURFACE_INTERNAL:
        return True
    return False


def tools_with_output_schemas(
    tools: list[dict[str, Any]],
    *,
    surface: str = MCP_SURFACE_INTERNAL,
) -> list[dict[str, Any]]:
    icons = brain_icon_metadata(settings.brain_public_base_url)
    return [
        tool_descriptor_with_runtime_metadata(tool, icons=icons, surface=surface)
        for tool in tools
    ]


def tool_descriptor_with_runtime_metadata(
    tool: dict[str, Any],
    *,
    icons: list[dict[str, Any]],
    surface: str,
) -> dict[str, Any]:
    tool_name = str(tool["name"])
    descriptor = {
        **tool,
        "icons": icons,
        "outputSchema": tool_output_schema(tool_name, surface=surface),
    }
    return descriptor


def security_headers() -> dict[str, str]:
    base = settings.brain_public_base_url.rstrip("/") or "'self'"
    return {
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self' "
            f"{base}; "
            "frame-ancestors 'self'"
        ),
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "X-Content-Type-Options": "nosniff",
    }


def add_security_headers(response: Response) -> None:
    for key, value in security_headers().items():
        response.headers.setdefault(key, value)


def rate_limit_oauth(request: Request, bucket: str) -> None:
    limit, window_seconds = OAUTH_RATE_LIMITS[bucket]
    forwarded_for = request.headers.get("x-forwarded-for", "").split(",", maxsplit=1)[0].strip()
    client_host = forwarded_for or (request.client.host if request.client else "unknown")
    key = f"{bucket}:{client_host}"
    now = time.monotonic()
    hits = _rate_limit_buckets[key]
    while hits and now - hits[0] > window_seconds:
        hits.popleft()
    if len(hits) >= limit:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limited",
                "error_description": "Too many authentication requests. Try again shortly.",
            },
            headers={"Retry-After": str(window_seconds)},
        )
    hits.append(now)


def tool_output_schema(
    tool_name: str,
    *,
    surface: str = MCP_SURFACE_INTERNAL,
) -> dict[str, Any]:
    del surface
    return STRUCTURED_OUTPUT_SCHEMAS.get(tool_name, ANY_OBJECT_SCHEMA)


def negotiate_mcp_protocol_version(params: Any) -> str:
    if isinstance(params, dict):
        requested = params.get("protocolVersion")
        if requested in SUPPORTED_MCP_PROTOCOL_VERSIONS:
            return str(requested)
    return DEFAULT_MCP_PROTOCOL_VERSION


def object_schema(
    properties: dict[str, Any] | None = None,
    *,
    required: list[str] | None = None,
    additional_properties: bool = True,
) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties or {},
        "additionalProperties": additional_properties,
    }
    if required:
        schema["required"] = required
    return schema


ANY_OBJECT_SCHEMA = object_schema()
STRING_ARRAY_SCHEMA = {"type": "array", "items": {"type": "string"}}
OBJECT_ARRAY_SCHEMA = {"type": "array", "items": ANY_OBJECT_SCHEMA}

RECALL_OUTPUT_SCHEMA = object_schema(
    {
        "answer": {"type": "string"},
        "facts": OBJECT_ARRAY_SCHEMA,
        "evidence": OBJECT_ARRAY_SCHEMA,
        "taste": ANY_OBJECT_SCHEMA,
    },
    required=["answer"],
)

SYNC_OUTPUT_SCHEMA = object_schema(
    {
        "status": {"type": "string"},
        "processed": {"type": "integer"},
        "succeeded": {"type": "integer"},
        "failed": {"type": "integer"},
        "skipped": {"type": "integer"},
        "results": OBJECT_ARRAY_SCHEMA,
    },
    required=["status"],
)

PALATE_QUERY_OUTPUT_SCHEMA = object_schema(
    {
        "answer": {"type": "string"},
        "ranked_results": OBJECT_ARRAY_SCHEMA,
        "decision_id": {"type": "string"},
        "intent": ANY_OBJECT_SCHEMA,
    },
)

STRUCTURED_OUTPUT_SCHEMAS: dict[str, dict[str, Any]] = {
    "brain_session": object_schema(
        {
            "user_id": {"type": "string"},
            "profile_name": {"type": "string"},
            "profile_full_name": {"type": "string"},
            "profile_context": OBJECT_ARRAY_SCHEMA,
            "profile_context_records": OBJECT_ARRAY_SCHEMA,
            "bias_context": OBJECT_ARRAY_SCHEMA,
            "bias_context_records": OBJECT_ARRAY_SCHEMA,
            "memory_tool": {"type": "string"},
            "recall_tool": {"type": "string"},
            "profile_context_remember_tool": {"type": "string"},
            "profile_context_list_tool": {"type": "string"},
            "profile_context_forget_tool": {"type": "string"},
            "bias_context_remember_tool": {"type": "string"},
            "bias_context_list_tool": {"type": "string"},
            "bias_context_forget_tool": {"type": "string"},
            "bias_prompt": {"type": "string"},
        },
        required=["user_id"],
    ),
    "brain_remember": object_schema(
        {
            "ingestion_run_id": {"type": "string"},
            "classification": {"type": "string"},
            "entities": OBJECT_ARRAY_SCHEMA,
            "conflicts": OBJECT_ARRAY_SCHEMA,
            "taste": ANY_OBJECT_SCHEMA,
            "cognee_sync_status": {"type": "string"},
            "dry_run": {"type": "boolean"},
        },
    ),
    "brain_profile_context_remember": object_schema(
        {"id": {"type": "string"}, "statement": {"type": "string"}, "scope": {"type": "string"}},
        required=["id", "statement"],
    ),
    "brain_profile_context_list": object_schema({"profile_context": OBJECT_ARRAY_SCHEMA}, required=["profile_context"]),
    "brain_profile_context_forget": object_schema({"context_id": {"type": "string"}, "status": {"type": "string"}}, required=["status"]),
    "brain_bias_context_remember": object_schema(
        {"id": {"type": "string"}, "statement": {"type": "string"}, "scope": {"type": "string"}},
        required=["id", "statement"],
    ),
    "brain_bias_context_list": object_schema({"bias_context": OBJECT_ARRAY_SCHEMA}, required=["bias_context"]),
    "brain_bias_context_forget": object_schema({"context_id": {"type": "string"}, "status": {"type": "string"}}, required=["status"]),
    "brain_profile_context_sync": object_schema(
        {
            "profile_context_count": {"type": "integer"},
            "synced_count": {"type": "integer"},
            "owner_entity_id": {"type": "string"},
            "profile_context": OBJECT_ARRAY_SCHEMA,
        },
        required=["synced_count"],
    ),
    "brain_ingest_source": object_schema(
        {
            "status": {"type": "string"},
            "summary": {"type": ["string", "null"]},
            "cognee_sync_status": {"type": "string"},
            "ingestion": ANY_OBJECT_SCHEMA,
        },
        required=["status"],
    ),
    "brain_recall": RECALL_OUTPUT_SCHEMA,
    "brain_profile_entity": RECALL_OUTPUT_SCHEMA,
    "brain_forget": object_schema({"object_type": {"type": "string"}, "object_id": {"type": "string"}, "status": {"type": "string"}, "mode": {"type": "string"}, "cognee_sync_status": {"type": "string"}}, required=["status"]),
    "brain_review_recent": object_schema(
        {
            "external_receipts": OBJECT_ARRAY_SCHEMA,
            "pending_confirmations": OBJECT_ARRAY_SCHEMA,
            "context_records": OBJECT_ARRAY_SCHEMA,
            "conflicts": OBJECT_ARRAY_SCHEMA,
        }
    ),
    "brain_undo_last": object_schema(
        {
            "status": {"type": "string"},
            "receipt_id": {"type": ["string", "null"]},
            "source_receipt_id": {"type": ["string", "null"]},
            "deleted_objects": STRING_ARRAY_SCHEMA,
            "status_events": OBJECT_ARRAY_SCHEMA,
        },
        required=["status"],
    ),
    "cognee_improve": object_schema({"dataset": {"type": "string"}, "resolved_dataset": {"type": "string"}, "node_name": STRING_ARRAY_SCHEMA, "run_in_background": {"type": "boolean"}, "result": ANY_OBJECT_SCHEMA}),
    "brain_palate_describe_item": ANY_OBJECT_SCHEMA,
    "brain_palate_remember": object_schema({"stored": {"type": "boolean"}, "taste_records": OBJECT_ARRAY_SCHEMA, "canonical_store": {"type": "string"}, "brain_projection": ANY_OBJECT_SCHEMA, "requires_confirmation": {"type": "boolean"}}),
    "brain_palate_query": PALATE_QUERY_OUTPUT_SCHEMA,
    "brain_palate_evaluate_options": PALATE_QUERY_OUTPUT_SCHEMA,
    "brain_palate_log_decision": object_schema({"logged": {"type": "boolean"}, "decision": ANY_OBJECT_SCHEMA}),
    "brain_palate_confirm": object_schema({"confirmed": {"type": "boolean"}, "proposal_id": {"type": "string"}}),
    "brain_palate_cancel": object_schema({"cancelled": {"type": "boolean"}, "proposal_id": {"type": "string"}}),
    "brain_palate_correct_proposal": ANY_OBJECT_SCHEMA,
    "brain_palate_refresh_enrichment": object_schema({"refreshed": {"type": "boolean"}, "taste_item_id": {"type": "string"}, "enrichment": ANY_OBJECT_SCHEMA}),
}


def resource_definitions(surface: str = MCP_SURFACE_INTERNAL) -> list[dict[str, str]]:
    del surface
    resources = [
        {
            "uri": "brain://schema/entity",
            "name": "Brain entity schema",
            "mimeType": "application/json",
        },
    ]
    return resources


def prompt_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "brain_bias_protocol",
            "description": (
                "Insert operating instructions for loading and updating the user's "
                "durable preferences, constraints, and response-style biases from Brain."
            ),
            "arguments": [
                {
                    "name": "profile_name",
                    "description": "Preference owner name. Defaults to the configured Brain owner.",
                    "required": False,
                }
            ],
        },
    ]


def get_prompt(name: str, arguments: dict[str, Any], active_settings: Settings | None = None) -> dict[str, Any]:
    prompt_settings = active_settings or settings
    if name == "brain_bias_protocol":
        profile_name = str(arguments.get("profile_name") or prompt_settings.brain_owner_name).strip()
        if not profile_name:
            raise ValueError("profile_name must not be blank.")
        return prompt_response(
            description=f"Brain bias/preference protocol for {profile_name}.",
            text=brain_bias_protocol_prompt(profile_name),
        )
    raise ValueError(f"Unknown Brain prompt: {name}")


def prompt_response(*, description: str, text: str) -> dict[str, Any]:
    return {
        "description": description,
        "messages": [
            {
                "role": "user",
                "content": {"type": "text", "text": text},
            }
        ],
    }


def brain_bias_protocol_prompt(profile_name: str) -> str:
    return f"""## Bias and Preference Protocol (Brain)

You have access to Brain MCP tools including `brain_bias_context_list`,
`brain_bias_context_remember`, and `brain_bias_context_forget`.
Use them to maintain durable preferences, constraints, and communication biases for {profile_name}.

**When the user says "load my preferences from Brain", "load my biases", "use Brain preferences", or similar:**
- Call `brain_bias_context_list` before responding.
- Apply relevant listed preferences silently in the rest of the conversation.
- If no bias records exist, continue without narrating that no preferences were found.

**At the start of a new chat, when this prompt is active:**
- If the first user message implies preferences, prior context, communication style, or "how I like things", call `brain_recall` before responding.
- Otherwise, wait until the user asks to load preferences or makes an ambiguous reference.

**During conversation, call `brain_bias_context_remember` immediately when the user states or revises a durable bias, preference, or constraint, including:**
- Response style, length, tone, detail level, formatting, or examples
- Engineering standards, architecture preferences, deployment constraints, tool preferences
- Personal defaults, recurring workflows, naming conventions, or "always/never" instructions
- Explicit phrases like "remember", "note", "keep in mind", "I prefer", "I don't like", "from now on"

**Format for `brain_bias_context_remember`:**
- Store one declarative sentence per fact.
- Include {profile_name}'s name when useful.
- Prefer stable, reusable statements over transcripts.
- Good: "{profile_name} prefers short answers unless a task requires implementation detail."
- Good: "{profile_name} prefers MCP tool names to use underscores rather than dots."
- Bad: "The user said maybe we should use underscores."

**When preferences conflict:**
- Use the newest explicit preference in the current conversation.
- Store the revision with `brain_remember`.
- Do not delete older memories unless the user explicitly asks to remove or forget them.

**Don't narrate memory calls.**
No "I'm saving that preference..." unless the user asks what you saved. Just apply the preference and continue."""


def resource_template_definitions() -> list[dict[str, str]]:
    return [
        {"uriTemplate": "brain://entity/{entity_id}", "name": "Brain entity", "mimeType": "application/json"},
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
        "admin_mcp_path": settings.brain_admin_mcp_path,
        "public_mcp_url": settings.public_mcp_url,
        "public_admin_mcp_url": settings.public_admin_mcp_url,
        "release_env": settings.brain_release_env,
        "release_sha": settings.brain_release_sha,
        "release_version": settings.brain_release_version,
        "uptime_seconds": round(time.time() - STARTED_AT, 3),
    }


@app.get("/icon.png", include_in_schema=False)
async def icon_png() -> FileResponse:
    return FileResponse(
        BRAIN_ICON_PATH,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/favicon.ico", include_in_schema=False)
async def favicon_ico() -> FileResponse:
    return FileResponse(
        BRAIN_FAVICON_PATH,
        media_type="image/x-icon",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/.well-known/oauth-protected-resource")
@app.get("/.well-known/oauth-protected-resource/{resource_path:path}")
async def oauth_protected_resource(resource_path: str = "") -> dict[str, Any]:
    normalized_resource_path = "/" + resource_path.strip("/")
    if normalized_resource_path == "/":
        normalized_resource_path = settings.brain_public_mcp_path
    return protected_resource_metadata_for_path(settings, normalized_resource_path)


def protected_resource_metadata_for_path(active_settings: Settings, resource_path: str) -> dict[str, Any]:
    normalized_resource_path = normalize_public_resource_path(active_settings, resource_path)
    resource_url = f"{active_settings.brain_public_base_url.rstrip('/')}{normalized_resource_path}"
    return {
        "resource": resource_url,
        "resource_name": active_settings.brain_service_name,
        "authorization_servers": [active_settings.brain_public_base_url.rstrip("/")],
        "scopes_supported": active_settings.oauth_scopes,
        "bearer_methods_supported": ["header"],
    }


def normalize_public_resource_path(active_settings: Settings, resource_path: str) -> str:
    requested = normalize_path(resource_path)
    if requested == active_settings.brain_admin_mcp_path:
        return active_settings.brain_public_admin_mcp_path
    if requested == active_settings.brain_mcp_path:
        return active_settings.brain_public_mcp_path
    return requested


@app.get("/.well-known/oauth-authorization-server")
@app.get("/.well-known/openid-configuration")
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
    rate_limit_oauth(request, "register")
    return await oauth_provider.register_client(request)


@app.api_route("/authorize", methods=["GET", "POST"])
async def authorize(request: Request) -> Response:
    if not oauth_provider:
        raise HTTPException(status_code=404, detail="OAuth is not enabled")
    rate_limit_oauth(request, "authorize")
    return await oauth_provider.authorize(request)


@app.post("/token")
async def token(request: Request) -> Response:
    if not oauth_provider:
        raise HTTPException(status_code=404, detail="OAuth is not enabled")
    rate_limit_oauth(request, "token")
    return await oauth_provider.token(request)


@app.post("/revoke")
async def revoke(request: Request) -> Response:
    if not oauth_provider:
        raise HTTPException(status_code=404, detail="OAuth is not enabled")
    rate_limit_oauth(request, "revoke")
    return await oauth_provider.revoke(request)


@app.post("/login")
async def login(payload: LoginRequest, request: Request) -> Response:
    if not settings.brain_auth_users_file:
        raise HTTPException(status_code=404, detail="Password login is not configured.")
    rate_limit_oauth(request, "login")
    user_id = normalize_user_id(payload.user_id)
    users = load_auth_users(settings, default_password=auth_admin_password())
    user = users.get(user_id)
    if user is None or not verify_password(payload.password, user):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    if migrate_verified_password(settings, users, user_id, payload.password):
        reload_oauth_users()
        user = users[user_id]
    session = create_web_session(user_id=user_id)
    response = JSONResponse(
        {
            "user": public_auth_user(user),
            "csrf_token": session["csrf_token"],
            "expires_at": session["expires_at"],
        }
    )
    set_web_session_cookie(response, session["session_id"])
    return response


@app.post("/logout")
async def logout(
    request: Request,
    brain_web_session: str | None = Cookie(default=None),
) -> Response:
    if brain_web_session:
        delete_web_session(brain_web_session)
    response = JSONResponse({"status": "logged_out"})
    response.delete_cookie(WEB_SESSION_COOKIE, path="/")
    return response


@app.get("/auth/session")
@app.get("/api/session")
async def web_session_endpoint(
    request: Request,
    brain_web_session: str | None = Cookie(default=None),
) -> dict[str, Any]:
    auth_context, session_record = require_web_session(request, brain_web_session)
    users = load_auth_users(settings, default_password=auth_admin_password())
    user_id = normalize_user_id(auth_context.user_id)
    user = users.get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Session user no longer exists.")
    return {
        "user": public_auth_user(user),
        "csrf_token": session_record["csrf_token"],
        "expires_at": session_record["expires_at"],
    }


@app.put("/account/password")
async def change_own_password(
    payload: PasswordChangeRequest,
    request: Request,
    brain_web_session: str | None = Cookie(default=None),
) -> dict[str, Any]:
    auth_context, _session_record = require_web_session(request, brain_web_session, require_csrf=True)
    user_id = normalize_user_id(auth_context.user_id)
    if not payload.new_password:
        raise HTTPException(status_code=400, detail="New password cannot be blank.")
    users = load_auth_users(settings, default_password=auth_admin_password())
    user = users.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if not verify_password(payload.current_password, user):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")
    users[user_id] = set_user_password(user, payload.new_password)
    write_auth_users(settings, users)
    reload_oauth_users()
    return {"user": public_auth_user(users[user_id])}


@app.get("/admin/users")
async def list_auth_users_endpoint(
    request: Request,
    authorization: str | None = Header(default=None),
    brain_web_session: str | None = Cookie(default=None),
) -> dict[str, Any]:
    auth_context = require_superuser_auth(authorization, request=request, session_cookie=brain_web_session)
    payload = auth_users_admin_payload(settings, default_password=auth_admin_password())
    return {
        **payload,
        "current_user_id": auth_context.user_id or settings.brain_user_id,
    }


@app.post("/admin/users", status_code=201)
async def create_auth_user_endpoint(
    payload: AuthUserCreateRequest,
    request: Request,
    authorization: str | None = Header(default=None),
    brain_web_session: str | None = Cookie(default=None),
) -> dict[str, Any]:
    require_superuser_auth(authorization, request=request, session_cookie=brain_web_session, require_csrf=True)
    user_id = normalize_user_id(payload.id)
    if not user_id:
        raise HTTPException(status_code=400, detail="User id is required.")
    if not payload.password:
        raise HTTPException(status_code=400, detail="Password is required.")
    users = load_auth_users(settings, default_password=auth_admin_password())
    if user_id in users:
        raise HTTPException(status_code=409, detail="User already exists.")
    users[user_id] = {
        "id": user_id,
        "display_name": payload.display_name or user_id,
        "email": payload.email or "",
        "superuser": str(payload.superuser).lower(),
    }
    users[user_id] = set_user_password(users[user_id], payload.password)
    write_auth_users(settings, users)
    reload_oauth_users()
    return {"user": public_auth_user(users[user_id])}


@app.put("/admin/users/{user_id}")
async def update_auth_user_endpoint(
    user_id: str,
    payload: AuthUserUpdateRequest,
    request: Request,
    authorization: str | None = Header(default=None),
    brain_web_session: str | None = Cookie(default=None),
) -> dict[str, Any]:
    auth_context = require_superuser_auth(
        authorization,
        request=request,
        session_cookie=brain_web_session,
        require_csrf=True,
    )
    normalized = normalize_user_id(user_id)
    users = load_auth_users(settings, default_password=auth_admin_password())
    if normalized not in users:
        raise HTTPException(status_code=404, detail="User not found.")
    updated = dict(users[normalized])
    if payload.password is not None:
        if not payload.password:
            raise HTTPException(status_code=400, detail="Password cannot be blank.")
        updated = set_user_password(updated, payload.password)
    if payload.display_name is not None:
        updated["display_name"] = payload.display_name or normalized
    if payload.email is not None:
        updated["email"] = payload.email
    if payload.superuser is not None:
        if not payload.superuser and normalized == auth_context.user_id:
            raise HTTPException(status_code=400, detail="Cannot remove superuser from the current user.")
        updated["superuser"] = str(payload.superuser).lower()
    users[normalized] = updated
    ensure_at_least_one_superuser(users)
    write_auth_users(settings, users)
    reload_oauth_users()
    return {"user": public_auth_user(updated)}


@app.delete("/admin/users/{user_id}")
async def delete_auth_user_endpoint(
    user_id: str,
    request: Request,
    authorization: str | None = Header(default=None),
    brain_web_session: str | None = Cookie(default=None),
) -> dict[str, Any]:
    auth_context = require_superuser_auth(
        authorization,
        request=request,
        session_cookie=brain_web_session,
        require_csrf=True,
    )
    normalized = normalize_user_id(user_id)
    if normalized == (auth_context.user_id or settings.brain_user_id):
        raise HTTPException(status_code=400, detail="Cannot delete the current user.")
    users = load_auth_users(settings, default_password=auth_admin_password())
    if normalized not in users:
        raise HTTPException(status_code=404, detail="User not found.")
    deleted = users.pop(normalized)
    ensure_at_least_one_superuser(users)
    write_auth_users(settings, users)
    reload_oauth_users()
    return {"deleted": public_auth_user(deleted)}


@app.get("/admin/tokens")
async def list_personal_access_tokens_endpoint(
    request: Request,
    user_id: str | None = None,
    authorization: str | None = Header(default=None),
    brain_web_session: str | None = Cookie(default=None),
) -> dict[str, Any]:
    require_superuser_auth(authorization, request=request, session_cookie=brain_web_session)
    if not oauth_provider:
        raise HTTPException(status_code=404, detail="Auth provider is not configured.")
    return {"personal_access_tokens": oauth_provider.list_personal_access_tokens(user_id)}


@app.post("/admin/tokens", status_code=201)
async def create_personal_access_token_endpoint(
    payload: PersonalAccessTokenCreateRequest,
    request: Request,
    authorization: str | None = Header(default=None),
    brain_web_session: str | None = Cookie(default=None),
) -> dict[str, Any]:
    require_superuser_auth(authorization, request=request, session_cookie=brain_web_session, require_csrf=True)
    if not oauth_provider:
        raise HTTPException(status_code=404, detail="Auth provider is not configured.")
    try:
        return oauth_provider.create_personal_access_token(
            user_id=payload.user_id,
            name=payload.name,
            scopes=parse_scope(payload.scopes, settings.brain_auth_scope_list),
            expires_in_seconds=payload.expires_in_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/admin/tokens/{token_id}")
async def revoke_personal_access_token_endpoint(
    token_id: str,
    request: Request,
    authorization: str | None = Header(default=None),
    brain_web_session: str | None = Cookie(default=None),
) -> dict[str, Any]:
    require_superuser_auth(authorization, request=request, session_cookie=brain_web_session, require_csrf=True)
    if not oauth_provider:
        raise HTTPException(status_code=404, detail="Auth provider is not configured.")
    revoked = oauth_provider.revoke_personal_access_token(token_id)
    if revoked is None:
        raise HTTPException(status_code=404, detail="Personal access token not found.")
    return {"revoked": revoked}


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
    return authenticated_model_response(
        authorization,
        lambda active_settings: brain_remember(payload, active_settings),
    )


@app.post("/memory/ingest_source")
async def brain_ingest_source_endpoint(
    payload: IngestSourceRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    return authenticated_model_response(
        authorization,
        lambda active_settings: brain_ingest_source(payload, active_settings),
    )


@app.post("/memory/recall")
async def brain_recall_endpoint(
    payload: RecallRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    return authenticated_model_response(
        authorization,
        lambda active_settings: brain_recall(payload, active_settings),
    )


@app.post("/memory/profile_entity")
async def brain_profile_entity_endpoint(
    payload: ProfileEntityRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    return authenticated_model_response(
        authorization,
        lambda active_settings: brain_profile_entity(
            active_settings,
            name=payload.name,
            entity_type=None if payload.entity_type == "auto" else payload.entity_type,
            include_superseded=payload.include_superseded,
            include_conflicts=payload.include_conflicts,
        ),
    )


@app.post("/memory/forget")
async def brain_forget_endpoint(
    payload: ForgetRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    return authenticated_dict_response(
        authorization,
        lambda active_settings: brain_forget(
            active_settings,
            object_type=payload.object_type,
            object_id=payload.object_id,
            hard=payload.hard,
            reason=payload.reason,
        ),
    )


@app.post("/memory/review_recent")
async def brain_review_recent_endpoint(
    payload: ReviewRecentRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    return authenticated_dict_response(
        authorization,
        lambda active_settings: brain_review_recent(
            active_settings,
            since=parse_optional_datetime(payload.since),
            limit=payload.limit,
        ),
    )


@app.post("/memory/undo_last")
async def brain_undo_last_endpoint(
    payload: UndoLastRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    return authenticated_dict_response(
        authorization,
        lambda active_settings: brain_undo_last(active_settings, ingestion_run_id=payload.ingestion_run_id),
    )


@app.api_route("/{path:path}", methods=["GET", "POST"])
async def mcp_route(
    path: str,
    request: Request,
    authorization: str | None = Header(default=None),
    brain_web_session: str | None = Cookie(default=None),
) -> Response:
    requested_path = "/" + path.strip("/")
    if requested_path == settings.brain_admin_mcp_path:
        surface = MCP_SURFACE_INTERNAL
        public_path = settings.brain_public_admin_mcp_path
        admin_surface = True
    elif requested_path == settings.brain_mcp_path:
        surface = MCP_SURFACE_INTERNAL
        public_path = settings.brain_public_mcp_path
        admin_surface = False
    else:
        raise HTTPException(status_code=404, detail="Not found")

    if request.method == "GET":
        auth_context = mcp_auth_context(authorization, settings, request=request, session_cookie=brain_web_session)
        if not auth_context.authenticated:
            return auth_challenge(settings, public_path)
        if (
            admin_surface
            and not auth_context.static_token
            and not auth_user_is_superuser(auth_context.user_id)
        ):
            raise HTTPException(status_code=403, detail="Superuser privileges are required.")
        return JSONResponse(
            {
                "service": settings.brain_service_name,
                "mcp_path": requested_path,
                "public_mcp_url": settings.public_mcp_url,
                "surface": surface,
                "status": "ready",
            }
        )

    auth_context = mcp_auth_context(authorization, settings, request=request, session_cookie=brain_web_session)
    if not auth_context.authenticated:
        return auth_challenge(settings, public_path)
    if (
        admin_surface
        and not auth_context.static_token
        and not auth_user_is_superuser(auth_context.user_id)
    ):
        raise HTTPException(status_code=403, detail="Superuser privileges are required.")
    if auth_context.web_session:
        require_web_csrf(request, brain_web_session)
    try:
        payload = await request.json()
    except ValueError:
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            },
            status_code=400,
        )
    request_context = McpRequestContext(
        auth=auth_context,
        remote_addr=request.client.host if request.client else None,
    )
    response_payload = await handle_json_rpc(
        payload,
        surface=surface,
        request_context=request_context,
    )
    return JSONResponse(response_payload)


def valid_bearer(header_value: str | None, active_settings: Settings) -> bool:
    return mcp_auth_context(
        header_value,
        active_settings,
        required_scopes=active_settings.brain_auth_scope_list,
    ).authenticated


def mcp_auth_context(
    header_value: str | None,
    active_settings: Settings,
    *,
    request: Request | None = None,
    session_cookie: str | None = None,
    remote_addr: str | None = None,
    required_scopes: list[str] | None = None,
) -> McpAuthContext:
    remote = remote_addr or (request.client.host if request and request.client else None)
    required = required_scopes or []
    if active_settings.brain_auth_token:
        expected = f"Bearer {active_settings.brain_auth_token}"
        if header_value == expected:
            return McpAuthContext(
                authenticated=True,
                static_token=True,
                user_id=active_settings.brain_user_id,
                scopes=tuple(active_settings.brain_auth_scope_list),
                remote_addr=remote,
            )
    token = parse_bearer(header_value)
    if oauth_provider and token:
        record = oauth_provider.access_token_record(token, required)
        if record is None:
            record = oauth_provider.personal_access_token_record(token, required)
        if record is not None:
            user_id = record.get("user_id")
            if not user_id:
                return McpAuthContext(remote_addr=remote)
            return McpAuthContext(
                authenticated=True,
                token=token,
                client_id=record.get("client_id"),
                user_id=user_id,
                scopes=tuple(record.get("scopes") or ()),
                remote_addr=remote,
            )
    if request is not None and session_cookie:
        session_record = web_session_record(session_cookie)
        if session_record is not None:
            return McpAuthContext(
                authenticated=True,
                web_session=True,
                user_id=session_record["user_id"],
                scopes=tuple(active_settings.brain_auth_scope_list),
                remote_addr=remote,
            )
    return McpAuthContext(remote_addr=remote)


def auth_challenge(active_settings: Settings, resource_path: str | None = None) -> Response:
    return JSONResponse(
        authentication_required_payload(active_settings),
        status_code=401,
        headers=auth_challenge_headers(active_settings, resource_path),
    )


def settings_for_request_context(request_context: McpRequestContext | None) -> Settings:
    if request_context is None or not request_context.auth.authenticated or not request_context.auth.user_id:
        raise HTTPException(status_code=401, detail=authentication_required_payload(settings))
    user_id = request_context.auth.user_id
    if user_id == settings.brain_user_id:
        return settings
    return settings.model_copy(update={"brain_user_id": user_id})


def settings_for_auth_context(active_settings: Settings, auth_context: McpAuthContext) -> Settings:
    if not auth_context.authenticated or not auth_context.user_id:
        raise HTTPException(status_code=401, detail=authentication_required_payload(active_settings))
    user_id = auth_context.user_id
    if user_id == active_settings.brain_user_id:
        return active_settings
    return active_settings.model_copy(update={"brain_user_id": user_id})


def require_api_auth(header_value: str | None, active_settings: Settings) -> Settings:
    auth_context = mcp_auth_context(
        header_value,
        active_settings,
        required_scopes=active_settings.brain_auth_scope_list,
    )
    if not auth_context.authenticated:
        raise HTTPException(
            status_code=401,
            detail=authentication_required_payload(active_settings),
            headers=auth_challenge_headers(active_settings),
        )
    return settings_for_auth_context(active_settings, auth_context)


def require_superuser_auth(
    header_value: str | None,
    *,
    request: Request | None = None,
    session_cookie: str | None = None,
    require_csrf: bool = False,
) -> McpAuthContext:
    auth_context = mcp_auth_context(
        header_value,
        settings,
        request=request,
        session_cookie=session_cookie,
        required_scopes=settings.brain_auth_scope_list,
    )
    if not auth_context.authenticated:
        raise HTTPException(
            status_code=401,
            detail=authentication_required_payload(settings),
            headers=auth_challenge_headers(settings),
        )
    if auth_context.static_token:
        return auth_context
    if require_csrf and auth_context.web_session:
        require_web_csrf(request, session_cookie)
    user_id = auth_context.user_id
    if not user_id:
        raise HTTPException(status_code=401, detail=authentication_required_payload(settings))
    users = load_auth_users(settings, default_password=auth_admin_password())
    record = users.get(normalize_user_id(user_id))
    if not record or not auth_record_is_superuser(record):
        raise HTTPException(status_code=403, detail="Superuser privileges are required.")
    return auth_context


def auth_admin_password() -> str:
    if oauth_provider:
        return oauth_provider.password
    return ensure_auth_password(settings)


def reload_oauth_users() -> None:
    if oauth_provider:
        oauth_provider.reload_users()


def ensure_at_least_one_superuser(users: dict[str, dict[str, Any]]) -> None:
    if not any(auth_record_is_superuser(record) for record in users.values()):
        raise HTTPException(status_code=400, detail="At least one superuser is required.")


def auth_user_is_superuser(user_id: str | None) -> bool:
    users = load_auth_users(settings, default_password=auth_admin_password())
    record = users.get(normalize_user_id(user_id))
    return auth_record_is_superuser(record)


def auth_record_is_superuser(record: dict[str, Any] | None) -> bool:
    return bool(record and str(record.get("superuser", "")).lower() == "true")


def public_https_redirect_url(request: Request) -> str | None:
    public_base = settings.brain_public_base_url.strip()
    public_url = urlsplit(public_base)
    if public_url.scheme != "https" or not public_url.hostname:
        return None
    request_host = request.headers.get("host", "").split(":", 1)[0].lower()
    if request_host != public_url.hostname.lower():
        return None
    forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",", 1)[0].strip().lower()
    effective_scheme = forwarded_proto or request.url.scheme
    if effective_scheme == "https":
        return None
    return str(request.url.replace(scheme="https"))


def web_sessions_path() -> Path:
    return Path(settings.brain_auth_state_path).expanduser().with_name("brain-web-sessions.json")


def session_hash(session_id: str) -> str:
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()


def load_web_sessions() -> dict[str, Any]:
    path = web_sessions_path()
    if not path.exists():
        return {"sessions": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"sessions": {}}
    if not isinstance(payload, dict) or not isinstance(payload.get("sessions"), dict):
        return {"sessions": {}}
    return payload


def save_web_sessions(payload: dict[str, Any]) -> None:
    path = web_sessions_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    temp_path = Path(temp_name)
    try:
        temp_path.chmod(0o600)
    except OSError:
        pass
    temp_path.replace(path)


def prune_web_sessions(payload: dict[str, Any]) -> None:
    now = time.time()
    sessions = payload.setdefault("sessions", {})
    for key, record in list(sessions.items()):
        expires_at = record.get("expires_at_epoch") if isinstance(record, dict) else None
        if expires_at is None or float(expires_at) <= now:
            sessions.pop(key, None)


def create_web_session(*, user_id: str) -> dict[str, str]:
    session_id = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    now = time.time()
    expires_at_epoch = now + WEB_SESSION_SECONDS
    expires_at = datetime.fromtimestamp(expires_at_epoch, UTC).isoformat()
    payload = load_web_sessions()
    prune_web_sessions(payload)
    payload["sessions"][session_hash(session_id)] = {
        "user_id": normalize_user_id(user_id),
        "csrf_token": csrf_token,
        "created_at": datetime.fromtimestamp(now, UTC).isoformat(),
        "last_seen_at": datetime.fromtimestamp(now, UTC).isoformat(),
        "expires_at": expires_at,
        "expires_at_epoch": expires_at_epoch,
    }
    save_web_sessions(payload)
    return {"session_id": session_id, "csrf_token": csrf_token, "expires_at": expires_at}


def web_session_record(session_id: str | None) -> dict[str, Any] | None:
    if not session_id:
        return None
    payload = load_web_sessions()
    prune_web_sessions(payload)
    key = session_hash(session_id)
    record = payload["sessions"].get(key)
    if not isinstance(record, dict):
        save_web_sessions(payload)
        return None
    users = load_auth_users(settings, default_password=auth_admin_password())
    if normalize_user_id(record.get("user_id")) not in users:
        payload["sessions"].pop(key, None)
        save_web_sessions(payload)
        return None
    record["last_seen_at"] = datetime.now(UTC).isoformat()
    save_web_sessions(payload)
    return record


def delete_web_session(session_id: str) -> None:
    payload = load_web_sessions()
    payload.get("sessions", {}).pop(session_hash(session_id), None)
    save_web_sessions(payload)


def set_web_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        WEB_SESSION_COOKIE,
        session_id,
        max_age=WEB_SESSION_SECONDS,
        httponly=True,
        secure=settings.brain_public_base_url.startswith("https://"),
        samesite="lax",
        path="/",
    )


def require_web_session(
    request: Request,
    session_cookie: str | None,
    *,
    require_csrf: bool = False,
) -> tuple[McpAuthContext, dict[str, Any]]:
    record = web_session_record(session_cookie)
    if record is None:
        raise HTTPException(status_code=401, detail="Login required.")
    if require_csrf:
        require_web_csrf(request, session_cookie)
    return (
        McpAuthContext(
            authenticated=True,
            web_session=True,
            user_id=record["user_id"],
            scopes=tuple(settings.brain_auth_scope_list),
            remote_addr=request.client.host if request.client else None,
        ),
        record,
    )


def require_web_csrf(request: Request | None, session_cookie: str | None) -> None:
    if request is None:
        raise HTTPException(status_code=403, detail="CSRF validation failed.")
    record = web_session_record(session_cookie)
    provided = request.headers.get("x-brain-csrf", "")
    expected = str(record.get("csrf_token") if record else "")
    if not expected or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=403, detail="CSRF validation failed.")


def authenticated_model_response(authorization: str | None, factory: Any) -> dict[str, Any]:
    active_settings = require_api_auth(authorization, settings)
    return factory(active_settings).model_dump(mode="json")


def authenticated_dict_response(authorization: str | None, factory: Any) -> dict[str, Any]:
    active_settings = require_api_auth(authorization, settings)
    return factory(active_settings)


def authentication_required_payload(active_settings: Settings) -> dict[str, str]:
    return {"error": "authentication_required", "service": active_settings.brain_service_name}


def auth_challenge_headers(
    active_settings: Settings,
    resource_path: str | None = None,
) -> dict[str, str]:
    metadata_url = (
        active_settings.protected_resource_metadata_url_for_path(resource_path)
        if resource_path
        else active_settings.protected_resource_metadata_url
    )
    return {
        "WWW-Authenticate": (
            'Bearer realm="Brain", '
            f'resource_metadata="{metadata_url}", '
            f'scope="{" ".join(active_settings.brain_auth_scope_list)}"'
        )
    }


async def delete_datasource_or_404(datasource: str) -> dict[str, Any]:
    try:
        return await delete_cognee_datasource(datasource, settings=settings)
    except DatasourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


async def handle_json_rpc(
    payload: Any,
    *,
    surface: str = MCP_SURFACE_INTERNAL,
    request_context: McpRequestContext | None = None,
) -> Any:
    if isinstance(payload, list):
        return [
            await handle_json_rpc(
                item,
                surface=surface,
                request_context=request_context,
            )
            for item in payload
        ]

    request_id = payload.get("id") if isinstance(payload, dict) else None
    method = payload.get("method") if isinstance(payload, dict) else None
    params = payload.get("params", {}) if isinstance(payload, dict) else {}

    try:
        if method == "initialize":
            result = {
                "protocolVersion": negotiate_mcp_protocol_version(params),
                "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                "serverInfo": {
                    "name": "brain",
                    "version": "0.1.0",
                    "icons": brain_icon_metadata(settings.brain_public_base_url),
                },
            }
        elif method == "tools/list":
            result = {"tools": memory_tool_definitions(surface=surface)}
        elif method == "prompts/list":
            result = {"prompts": prompt_definitions()}
        elif method == "prompts/get":
            prompt_settings = settings_for_request_context(request_context)
            result = get_prompt(
                str(params.get("name", "")),
                params.get("arguments") or {},
                prompt_settings,
            )
        elif method == "resources/list":
            result = {"resources": resource_definitions(surface=surface)}
        elif method == "resources/templates/list":
            result = {"resourceTemplates": resource_template_definitions()}
        elif method == "resources/read":
            result = read_resource(str(params.get("uri", "")), request_context=request_context)
        elif method == "tools/call":
            result = await call_tool(
                params,
                surface=surface,
                request_context=McpRequestContext(
                    auth=request_context.auth if request_context else McpAuthContext(),
                    remote_addr=request_context.remote_addr if request_context else None,
                    json_rpc_id=request_id,
                ),
            )
        elif method and method.startswith("notifications/"):
            return {"jsonrpc": "2.0", "id": request_id, "result": {}}
        else:
            return json_rpc_error(request_id, -32601, f"Unknown method: {method}")
    except Exception as exc:
        return json_rpc_error(request_id, -32000, str(exc))

    return {"jsonrpc": "2.0", "id": request_id, "result": result}


async def call_tool(
    params: dict[str, Any],
    *,
    surface: str = MCP_SURFACE_INTERNAL,
    request_context: McpRequestContext | None = None,
) -> dict[str, Any]:
    name = str(params.get("name") or "")
    arguments = params.get("arguments") or {}
    if not tool_available_on_surface(name, surface):
        raise ValueError(f"Tool is not available on the {surface} MCP surface: {name}")
    del arguments
    return await call_tool_dispatch(
        params,
        surface=surface,
        request_context=request_context,
    )


async def call_tool_dispatch(
    params: dict[str, Any],
    *,
    surface: str = MCP_SURFACE_INTERNAL,
    request_context: McpRequestContext | None = None,
) -> dict[str, Any]:
    settings = settings_for_request_context(request_context)
    name = str(params.get("name") or "")
    arguments = params.get("arguments") or {}
    if name == "brain_session":
        payload = brain_session_payload(settings)
        return json_tool_response(
            payload,
            summary=f"Brain session resolved for user {payload['user_id']}.",
        )

    if name == "brain_remember":
        arguments = normalized_arguments(arguments)
        request = RememberRequest.model_validate(
            {
                "input": arguments.get("input", ""),
                "input_type": arguments.get("input_type", "auto"),
                "observed_at": arguments.get("observed_at"),
                "dry_run": bool(arguments.get("dry_run", False)),
                "context": arguments.get("context") or {},
            }
        )
        payload = brain_remember(request, settings).model_dump(mode="json")
        return json_tool_response(payload, summary=remember_summary(payload))

    if name == "brain_profile_context_remember":
        request = BrainProfileContextRememberRequest.model_validate(arguments)
        payload = remember_profile_context(
            settings,
            statement=request.statement,
            scope=request.scope,
            source=request.source,
        )
        return json_tool_response(
            payload,
            summary=f"Profile context stored: {payload['id']}.",
        )

    if name == "brain_profile_context_list":
        payload = {"profile_context": list_profile_context(settings)}
        return json_tool_response(
            payload,
            summary=f"Found {len(payload['profile_context'])} profile context items.",
        )

    if name == "brain_profile_context_forget":
        request = BrainProfileContextForgetRequest.model_validate(arguments)
        payload = forget_profile_context(settings, context_id=request.context_id)
        return json_tool_response(
            payload,
            summary=f"Profile context forget result: {payload['status']}.",
        )

    if name == "brain_bias_context_remember":
        request = BrainBiasContextRememberRequest.model_validate(arguments)
        payload = remember_bias_context(
            settings,
            statement=request.statement,
            scope=request.scope,
            source=request.source,
        )
        return json_tool_response(
            payload,
            summary=f"Bias context stored: {payload['id']}.",
        )

    if name == "brain_bias_context_list":
        payload = {"bias_context": list_bias_context(settings)}
        return json_tool_response(
            payload,
            summary=f"Found {len(payload['bias_context'])} bias context items.",
        )

    if name == "brain_bias_context_forget":
        request = BrainBiasContextForgetRequest.model_validate(arguments)
        payload = forget_bias_context(settings, context_id=request.context_id)
        return json_tool_response(
            payload,
            summary=f"Bias context forget result: {payload['status']}.",
        )

    if name == "brain_profile_context_sync":
        payload = sync_profile_context(settings)
        return json_tool_response(
            payload,
            summary=f"Profile context sync complete: {payload['synced_count']} items.",
        )

    if name == "brain_ingest_source":
        arguments = normalized_arguments(arguments)
        request = IngestSourceRequest.model_validate(
            {
                "source": arguments.get("source"),
                "source_kind": arguments.get("source_kind", "auto"),
                "title": arguments.get("title"),
                "why_saved": arguments.get("why_saved"),
                "dry_run": bool(arguments.get("dry_run", False)),
                "run_in_background": arguments.get("run_in_background")
                if "run_in_background" in arguments
                else None,
                "metadata": arguments.get("metadata") or {},
                "context": arguments.get("context") or {},
            }
        )
        receipt = brain_ingest_source(request, settings).model_dump(mode="json")
        payload = ingest_source_tool_payload(receipt, arguments)
        return json_tool_response(
            payload,
            summary=ingest_source_tool_summary(payload),
        )

    if name == "brain_recall":
        request = RecallRequest.model_validate(
            {
                "query": arguments["query"],
                "mode": arguments.get("mode", "auto"),
                "include_superseded": bool(arguments.get("include_superseded", False)),
                "include_conflicts": bool(arguments.get("include_conflicts", True)),
                "limit": int(arguments.get("limit", 20)),
            }
        )
        payload = brain_recall(request, settings).model_dump(mode="json")
        return json_tool_response(payload, summary=payload.get("answer", "Recall complete."))

    if name == "brain_profile_entity":
        entity_type = arguments.get("entity_type")
        if entity_type == "auto":
            entity_type = None
        payload = brain_profile_entity(
            settings,
            name=str(arguments["name"]),
            entity_type=entity_type,
            include_superseded=bool(arguments.get("include_superseded", False)),
            include_conflicts=bool(arguments.get("include_conflicts", True)),
        ).model_dump(mode="json")
        return json_tool_response(payload, summary=payload.get("answer", "Profile complete."))

    if name == "brain_forget":
        hard = bool(arguments.get("hard", False))
        if hard and not bool(arguments.get("confirm", False)):
            raise ValueError("brain_forget requires confirm=true for hard deletes.")
        payload = brain_forget(
            settings,
            object_type=str(arguments["object_type"]),
            object_id=str(arguments["object_id"]),
            hard=hard,
            reason=arguments.get("reason"),
        )
        mode = "hard" if hard else str(payload.get("mode") or "forget")
        payload = {**payload, "mode": mode, "cognee_sync_status": payload.get("cognee_sync_status", "stale")}
        return json_tool_response(payload, summary=f"Forget result: {payload['status']}.")

    if name == "brain_review_recent":
        payload = brain_review_recent(
            settings,
            since=parse_optional_datetime(arguments.get("since")),
            limit=bounded_int(arguments.get("limit", 20), minimum=1, maximum=100),
        )
        return json_tool_response(
            payload,
            summary=(
                f"Found {len(payload.get('external_receipts', []))} recent receipts and "
                f"{len(payload.get('pending_confirmations', []))} pending confirmations."
            ),
        )

    if name == "brain_undo_last":
        payload = brain_undo_last(
            settings,
            ingestion_run_id=arguments.get("ingestion_run_id"),
        )
        return json_tool_response(
            payload,
            summary=f"Undo result: {payload['status']}.",
        )

    if name == "cognee_improve":
        request = CogneeImproveRequest.model_validate(arguments)
        dataset = configured_cognee_dataset(request.dataset, settings)
        result = await improve_cognee(
            dataset=dataset,
            node_name=request.node_name,
            run_in_background=request.run_in_background,
            settings=settings,
        )
        payload = {
            "dataset": request.dataset,
            "resolved_dataset": dataset,
            "node_name": request.node_name or [],
            "run_in_background": request.run_in_background,
            "result": to_jsonable(result),
        }
        return json_tool_response(payload, summary=f"Cognee improve queued for {dataset}.")

    if name == "brain_palate_describe_item":
        payload = TasteService(settings).describe_item(
            TasteDescribeRequest.model_validate(
                {
                    "item_text": arguments["item_text"],
                    "entity_type": arguments["entity_type"],
                    "canonical_name": arguments.get("canonical_name"),
                    "attributes": arguments.get("attributes"),
                    "attribute_intervals_95": arguments.get("attribute_intervals_95"),
                    "metadata": arguments.get("metadata") or {},
                    "notes": arguments.get("notes"),
                    "fetch_external_ratings": bool(
                        arguments.get("fetch_external_ratings", True)
                    ),
                    "allow_broader_web_search": bool(
                        arguments.get("allow_broader_web_search", False)
                    ),
                }
            )
        )
        return json_tool_response(payload, summary="Palate item described without storing.")

    if name == "brain_palate_remember":
        payload = TasteService(settings).remember(
            TasteRememberRequest.model_validate(
                {
                    "id": arguments.get("id"),
                    "type": arguments["type"],
                    "canonical_name": arguments["canonical_name"],
                    "description": arguments["description"],
                    "attributes": arguments.get("attributes"),
                    "attribute_intervals_95": arguments.get("attribute_intervals_95"),
                    "rating": arguments.get("rating"),
                    "tried": arguments.get("tried"),
                    "watched": arguments.get("watched"),
                    "listened": arguments.get("listened"),
                    "wanted": arguments.get("wanted"),
                    "recommended_by": arguments.get("recommended_by"),
                    "disliked": arguments.get("disliked"),
                    "avoid": arguments.get("avoid"),
                    "not_my_style": arguments.get("not_my_style"),
                    "bad_fit": arguments.get("bad_fit"),
                    "notes": arguments.get("notes"),
                    "metadata": arguments.get("metadata") or {},
                    "dry_run": bool(arguments.get("dry_run", False)),
                    "store_anyway": bool(arguments.get("store_anyway", False)),
                    "context": arguments.get("context") or {},
                    "fetch_external_ratings": bool(
                        arguments.get("fetch_external_ratings", True)
                    ),
                    "allow_broader_web_search": bool(
                        arguments.get("allow_broader_web_search", False)
                    ),
                }
            )
        )
        return json_tool_response(
            payload,
            summary=(
                f"Stored {len(payload.get('taste_records', []))} palate record(s) in "
                f"{payload.get('canonical_store', 'the canonical store')}."
                if payload.get("stored")
                else "Palate remember dry run complete."
            ),
        )

    if name == "brain_palate_query":
        payload = TasteService(settings).query(TasteQueryRequest.model_validate(arguments))
        return json_tool_response(payload, summary=payload.get("answer", "Palate query complete."))

    if name == "brain_palate_evaluate_options":
        payload = TasteService(settings).evaluate_options(
            TasteQueryRequest.model_validate(arguments)
        )
        return json_tool_response(
            payload,
            summary=payload.get("answer", "Palate option evaluation complete."),
        )

    if name == "brain_palate_log_decision":
        payload = TasteService(settings).log_decision(
            TasteLogDecisionRequest.model_validate(arguments)
        )
        return json_tool_response(
            payload,
            summary="Palate decision logged." if payload.get("logged") else "Palate decision not logged.",
        )

    if name == "brain_palate_confirm":
        payload = TasteService(settings).confirm(str(arguments["proposal_id"]))
        return json_tool_response(
            payload,
            summary="Palate proposal confirmed." if payload.get("confirmed") else "Palate proposal not confirmed.",
        )

    if name == "brain_palate_cancel":
        payload = TasteService(settings).cancel(str(arguments["proposal_id"]))
        return json_tool_response(
            payload,
            summary="Palate proposal cancelled." if payload.get("cancelled") else "Palate proposal not cancelled.",
        )

    if name == "brain_palate_correct_proposal":
        payload = TasteService(settings).correct_proposal(
            str(arguments["proposal_id"]),
            str(arguments["correction"]),
        )
        return json_tool_response(payload, summary="Palate proposal corrected.")

    if name == "brain_palate_refresh_enrichment":
        payload = TasteService(settings).refresh_enrichment(
            TasteRefreshRequest.model_validate(arguments)
        )
        return json_tool_response(
            payload,
            summary="Palate enrichment refreshed." if payload.get("refreshed") else "Palate refresh failed.",
        )

    raise ValueError(f"Unknown tool: {name}")


def normalized_arguments(arguments: Any) -> dict[str, Any]:
    if not isinstance(arguments, dict):
        return {}
    return dict(arguments)


def configured_cognee_dataset(dataset: str, active_settings: Settings) -> str:
    mapping = {
        "memory": active_settings.brain_cognee_memory_dataset,
        "data": active_settings.brain_cognee_data_dataset,
        "palate": active_settings.brain_cognee_palate_dataset,
    }
    if dataset not in mapping:
        raise ValueError(f"dataset must be one of: {', '.join(COGNEE_IMPROVE_DATASETS)}")
    return mapping[dataset]


def source_summary_from_request(arguments: dict[str, Any]) -> str | None:
    for key in ("title", "why_saved", "source", "input"):
        value = arguments.get(key)
        if value:
            return str(value)[:500]
    return None


def ingest_source_tool_payload(receipt: dict[str, Any], arguments: dict[str, Any]) -> dict[str, Any]:
    status = receipt.get("cognee_sync_status", "pending")
    if status == "queued":
        tool_status = "queued"
    elif receipt.get("dry_run"):
        tool_status = "dry_run"
    else:
        tool_status = "processed"
    return {
        "status": tool_status,
        "summary": source_summary_from_request(arguments),
        "cognee_sync_status": status,
        "ingestion": receipt,
    }


def ingest_source_tool_summary(payload: dict[str, Any]) -> str:
    if payload["status"] == "queued":
        return "Queued source ingestion in the background."
    if payload["status"] == "dry_run":
        return "Prepared source ingestion dry run; no durable write performed."
    if payload.get("cognee_sync_status") == "synced":
        return "Stored data once in Cognee; Cognee owns source handling and memory graph creation."
    return "Ingested source through Cognee."


def remember_summary(payload: dict[str, Any]) -> str:
    if payload.get("classification") == "taste_proposal":
        taste = payload.get("taste") if isinstance(payload.get("taste"), dict) else {}
        proposal_id = taste.get("proposal_id")
        warnings = taste.get("warnings") or []
        warning_text = f" Warning: {warnings[0]}" if warnings else ""
        if proposal_id:
            return (
                f"Created pending Brain Palate proposal {proposal_id}; "
                "no durable Brain memories were stored yet."
                f"{warning_text}"
            )
        return (
            "Created a pending Brain Palate proposal; no durable Brain memories "
            f"were stored yet.{warning_text}"
        )
    conflict_count = len(payload.get("conflicts", []))
    if payload.get("dry_run"):
        return "Prepared Cognee remember dry run; no durable write performed."
    if payload.get("cognee_sync_status") == "synced":
        return f"Stored data once in Cognee. {conflict_count} conflicts detected."
    return f"Stored data through Brain. {conflict_count} conflicts detected."


def bounded_int(value: Any, *, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, int(value)))


def parse_optional_datetime(value: Any) -> datetime | None:
    if value in {None, ""}:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    return datetime.fromisoformat(text)


def read_resource(uri: str, *, request_context: McpRequestContext | None = None) -> dict[str, Any]:
    payload = resource_payload(uri, request_context=request_context)
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

def resource_payload(uri: str, *, request_context: McpRequestContext | None = None) -> Any:
    store = BrainStore(settings_for_request_context(request_context))
    if uri == "brain://schema/entity":
        return {"schema": "entity", "fields": list(schema_field_names("entities"))}
    prefix_handlers = {
        "brain://entity/": store.get_entity,
    }
    for prefix, handler in prefix_handlers.items():
        if uri.startswith(prefix):
            return handler(uri.removeprefix(prefix))
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
