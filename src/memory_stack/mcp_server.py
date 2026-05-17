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
from memory_stack.brain_service import (
    forget as brain_forget,
    get_memory as brain_get_memory,
    get_source as brain_get_source,
    ingest_source as brain_ingest_source,
    list_open_loops as brain_list_open_loops,
    merge_entities as brain_merge_entities,
    profile_entity as brain_profile_entity,
    recall as brain_recall,
    remember as brain_remember,
    rebuild_cognee as brain_rebuild_cognee,
    resolve_conflict as brain_resolve_conflict,
    review_recent as brain_review_recent,
    sync_cognee as brain_sync_cognee,
    undo_last as brain_undo_last,
)
from memory_stack.brain_store import BrainStore, normalize_user_id
from memory_stack.cognee_adapter import (
    DatasourceNotFoundError,
    create_datasource as create_cognee_datasource,
    delete_datasource as delete_cognee_datasource,
    improve_cognee,
    list_datasources as list_cognee_datasources,
    recall_text,
)
from memory_stack.cfg import Settings, load_settings, normalize_path
from memory_stack.domain_constants import (
    ADMIN_COGNEE_DATASETS,
    ADMIN_COGNEE_OBJECT_TYPES,
    COGNEE_IMPROVE_DATASETS,
    CONFLICT_ACTIONS,
    ENTITY_TYPES,
    FORGET_OBJECT_TYPES,
    INPUT_TYPES,
    OPEN_LOOP_STATUSES,
    RECALL_MODES,
    SOURCE_KINDS,
)
from memory_stack.icon_assets import (
    BRAIN_APPLE_TOUCH_ICON_PATH,
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
    parse_bearer,
    public_auth_user,
    write_auth_users,
)
from memory_stack.profile_context import (
    forget_profile_context,
    list_profile_context,
    remember_profile_context,
    sync_profile_context,
)
from memory_stack.request_logging import RequestResponseLogMiddleware
from memory_stack.session import (
    agent_memory_dataset_for_user,
    agent_memory_session_id_for_user,
    brain_session_payload,
)
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
oauth_provider = BrainOAuthProvider(settings) if settings.brain_auth_enabled else None
SUPPORTED_MCP_PROTOCOL_VERSIONS = {"2024-11-05", "2025-11-25"}
DEFAULT_MCP_PROTOCOL_VERSION = "2024-11-05"
MCP_SURFACE_INTERNAL = "internal"
MCP_SURFACE_CHATGPT_APP = "chatgpt_app"
CHATGPT_APP_TOOLS = {
    "brain_session",
    "brain_recall",
    "brain_remember",
    "brain_ingest_source",
    "brain_profile_entity",
    "brain_list_open_loops",
    "brain_get_memory",
    "brain_review_recent",
    "brain_undo_last",
    "brain_profile_context_list",
    "brain_profile_context_remember",
    "brain_profile_context_forget",
    "brain_app_data_controls",
    "brain_palate_describe_item",
    "brain_palate_query",
    "brain_palate_evaluate_options",
    "brain_palate_confirm",
    "brain_palate_cancel",
    "brain_palate_correct_proposal",
}
APP_READ_ONLY_TOOLS = {
    "brain_session",
    "brain_recall",
    "brain_profile_entity",
    "brain_list_open_loops",
    "brain_get_memory",
    "brain_review_recent",
    "brain_profile_context_list",
    "brain_app_data_controls",
    "brain_palate_describe_item",
    "brain_palate_query",
    "brain_palate_evaluate_options",
}
APP_MUTATING_TOOLS = {
    "brain_remember",
    "brain_ingest_source",
    "brain_profile_context_remember",
    "brain_profile_context_forget",
    "brain_undo_last",
    "brain_palate_confirm",
    "brain_palate_cancel",
    "brain_palate_correct_proposal",
}
APP_DESTRUCTIVE_TOOLS = {"brain_undo_last", "brain_profile_context_forget"}
APP_TOOL_READ_SCOPE = "brain.memory.read"
APP_TOOL_WRITE_SCOPE = "brain.memory.write"
APP_STATIC_DIR = Path(__file__).resolve().parent / "static" / "brain_app"
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
        return RedirectResponse(redirect_url, status_code=307)
    return await call_next(request)


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
    include_sources: bool = True
    include_conflicts: bool = True


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


class ReviewRecentRequest(BaseModel):
    since: str | None = None
    limit: int = 20
    include_sources: bool = True


class UndoLastRequest(BaseModel):
    ingestion_run_id: str | None = None


class SyncCogneeRequest(BaseModel):
    object_type: str = "all"
    object_id: str | None = None
    dataset: str = "all"
    force: bool = False


class RebuildCogneeRequest(BaseModel):
    dataset: str = "all"
    prune_first: bool = False
    confirm: bool = False


class CogneeImproveRequest(BaseModel):
    dataset: str = "memory"
    node_name: list[str] | None = None
    session_ids: list[str] | None = None
    run_in_background: bool = False


class BrainAgentMemoryRequest(BaseModel):
    session_id: str
    node_name: list[str] | None = None
    run_in_background: bool = False


class BrainAgentMemoryRecallRequest(BaseModel):
    query: str
    top_k: int = 10


class BrainAgentMemoryClearRequest(BaseModel):
    confirm: bool = False


class BrainProfileContextRememberRequest(BaseModel):
    statement: str
    scope: str = "answer_tailoring"
    source: str | None = None
    confirmed_by_user: bool = False


class BrainProfileContextForgetRequest(BaseModel):
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


class LoginRequest(BaseModel):
    user_id: str
    password: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class MergeEntitiesRequest(BaseModel):
    primary_entity_id: str
    duplicate_entity_id: str
    reason: str | None = None
    confirm: bool = False


def memory_tool_definitions(surface: str = MCP_SURFACE_INTERNAL) -> list[dict[str, Any]]:
    tools = [
        {
            "name": "brain_session",
            "description": (
                "Resolve the active user's Brain session identity agents should use "
                "for durable memory, bias/preferences, and portable agent-memory calls."
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
            "name": "brain_profile_context_remember",
            "description": (
                "Store a stable user-profile fact that should always be returned "
                "by brain_session to tailor future answers. On the ChatGPT App "
                "surface this requires confirmed_by_user=true."
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
                    "confirmed_by_user": {
                        "type": "boolean",
                        "default": False,
                        "description": "Required true on the ChatGPT App surface.",
                    },
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
            "description": (
                "Remove one standing user-profile context item by id. On the "
                "ChatGPT App surface this requires confirmed_by_user=true."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "context_id": {"type": "string"},
                    "confirmed_by_user": {
                        "type": "boolean",
                        "default": False,
                        "description": "Required true on the ChatGPT App surface.",
                    },
                    "context": {"type": "object", "additionalProperties": True},
                },
                "required": ["context_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_app_data_controls",
            "description": (
                "Return user-visible Brain app data controls: recent app writes, "
                "profile context, preprompt items, recent memories, and open loops."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                    "include_recent_memories": {"type": "boolean", "default": True},
                },
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
                "Store source material and optionally extract durable Brain memories. "
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
                    "extract_memories": {"type": "boolean", "default": True},
                    "dry_run": {"type": "boolean", "default": False},
                    "run_in_background": {"type": "boolean", "default": False},
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
            "name": "brain_profile_entity",
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
            "name": "brain_list_open_loops",
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
            "name": "brain_get_memory",
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
            "name": "brain_get_source",
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
            "name": "brain_resolve_conflict",
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
            "name": "brain_forget",
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
        {
            "name": "brain_review_recent",
            "description": "Review recent Brain ingestion runs, sources, memories, and conflict links.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "since": {"type": "string", "format": "date-time"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                    "include_sources": {"type": "boolean", "default": True},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_undo_last",
            "description": (
                "Soft-delete objects created by one recent ingestion run. On the "
                "ChatGPT App surface this requires confirmed_by_user=true."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ingestion_run_id": {"type": "string"},
                    "confirmed_by_user": {
                        "type": "boolean",
                        "default": False,
                        "description": "Required true on the ChatGPT App surface.",
                    },
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_sync_cognee",
            "description": "Manually sync pending Brain projections to Cognee.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "object_type": {"type": "string", "enum": ADMIN_COGNEE_OBJECT_TYPES, "default": "all"},
                    "object_id": {"type": "string"},
                    "dataset": {"type": "string", "enum": ADMIN_COGNEE_DATASETS, "default": "all"},
                    "force": {"type": "boolean", "default": False},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_rebuild_cognee",
            "description": "Mark Cognee projections stale so they can be rebuilt from Brain DB.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "dataset": {"type": "string", "enum": ADMIN_COGNEE_DATASETS, "default": "all"},
                    "prune_first": {"type": "boolean", "default": False},
                    "confirm": {
                        "type": "boolean",
                        "default": False,
                        "description": "Required true when prune_first=true.",
                    },
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "cognee_improve",
            "description": "Run Cognee native improve on a configured dataset, optionally bridging session feedback.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "dataset": {"type": "string", "enum": COGNEE_IMPROVE_DATASETS, "default": "memory"},
                    "node_name": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional Cognee node-name filter.",
                    },
                    "session_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional Cognee session IDs to bridge feedback and Q&A into the graph.",
                    },
                    "run_in_background": {"type": "boolean", "default": False},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_agent_memory",
            "description": (
                "Bridge the active user's Brain session into their dedicated, removable "
                "agent-memory dataset. Use the session_id returned by brain_session."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "node_name": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional Cognee node-name filter for the improve run.",
                    },
                    "run_in_background": {"type": "boolean", "default": False},
                },
                "required": ["session_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_agent_memory_recall",
            "description": "Recall directly from the dedicated Cognee agent-memory dataset.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_agent_memory_clear",
            "description": "Clear the dedicated Cognee agent-memory dataset after explicit confirmation.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "confirm": {
                        "type": "boolean",
                        "default": False,
                        "description": "Required true to clear agent-memory records.",
                    }
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "brain_merge_entities",
            "description": "Merge a duplicate entity into a primary entity after confirmation.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "primary_entity_id": {"type": "string"},
                    "duplicate_entity_id": {"type": "string"},
                    "reason": {"type": "string"},
                    "confirm": {
                        "type": "boolean",
                        "default": False,
                        "description": "Required true to merge entities.",
                    },
                },
                "required": ["primary_entity_id", "duplicate_entity_id"],
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
    if surface == MCP_SURFACE_CHATGPT_APP:
        tools = [tool for tool in tools if tool["name"] in CHATGPT_APP_TOOLS]
        for tool in tools:
            if tool["name"] == "brain_remember":
                tool["description"] = (
                    "Prepare or store a user-level Brain memory. On the ChatGPT App "
                    "surface this tool previews by default; save only after explicit "
                    "user confirmation by passing context.confirmed_by_user=true."
                )
            if tool["name"] == "brain_ingest_source":
                tool["description"] = (
                    "Prepare or store a user-level source such as an article, email, "
                    "transcript, markdown note, or table. On the ChatGPT App surface "
                    "this tool previews by default; save only after explicit user "
                    "confirmation by passing confirmed_by_user=true."
                )
    return tools_with_output_schemas(tools, surface=surface)


def tool_available_on_surface(tool_name: str, surface: str) -> bool:
    if surface == MCP_SURFACE_INTERNAL:
        return True
    if surface == MCP_SURFACE_CHATGPT_APP:
        return tool_name in CHATGPT_APP_TOOLS
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
        "outputSchema": tool_output_schema(tool_name),
    }
    if surface == MCP_SURFACE_CHATGPT_APP:
        descriptor.update(app_tool_metadata(tool_name))
    return descriptor


def app_tool_metadata(tool_name: str) -> dict[str, Any]:
    security_schemes = [{"type": "oauth2", "scopes": app_tool_required_scopes(tool_name)}]
    return {
        "securitySchemes": security_schemes,
        "annotations": {
            "readOnlyHint": tool_name in APP_READ_ONLY_TOOLS,
            "destructiveHint": tool_name in APP_DESTRUCTIVE_TOOLS,
            "openWorldHint": False,
        },
        "_meta": {
            "securitySchemes": security_schemes,
            "ui": {"visibility": ["model"]},
            "openai/toolInvocation/invoking": tool_invocation_status(tool_name, done=False),
            "openai/toolInvocation/invoked": tool_invocation_status(tool_name, done=True),
            "openai/visibility": "public",
            "brain/requiresUserConfirmation": tool_name in APP_MUTATING_TOOLS,
        },
    }


def app_tool_required_scopes(tool_name: str) -> list[str]:
    if tool_name in APP_MUTATING_TOOLS:
        return [APP_TOOL_READ_SCOPE, APP_TOOL_WRITE_SCOPE]
    return [APP_TOOL_READ_SCOPE]


def tool_invocation_status(tool_name: str, *, done: bool) -> str:
    statuses = {
        "brain_session": ("Loading Brain session", "Brain session loaded"),
        "brain_recall": ("Searching Brain", "Brain recall complete"),
        "brain_remember": ("Preparing memory", "Memory preview ready"),
        "brain_profile_entity": ("Building profile", "Profile ready"),
        "brain_list_open_loops": ("Loading open loops", "Open loops loaded"),
        "brain_get_memory": ("Loading memory", "Memory loaded"),
        "brain_review_recent": ("Reviewing recent memory", "Recent memory loaded"),
        "brain_undo_last": ("Checking undo", "Undo complete"),
        "brain_profile_context_list": ("Loading profile context", "Profile context loaded"),
        "brain_profile_context_remember": ("Saving profile context", "Profile context saved"),
        "brain_profile_context_forget": ("Removing profile context", "Profile context removed"),
        "brain_app_data_controls": ("Loading data controls", "Data controls loaded"),
    }
    invoking, invoked = statuses.get(tool_name, ("Calling Brain", "Brain call complete"))
    return invoked if done else invoking


def brain_app_file(filename: str, media_type: str) -> FileResponse:
    path = APP_STATIC_DIR / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(
        path,
        media_type=media_type,
        headers={"Cache-Control": "no-store"},
    )


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


def tool_output_schema(tool_name: str) -> dict[str, Any]:
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
        "open_loops": OBJECT_ARRAY_SCHEMA,
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
            "session_id": {"type": "string"},
            "user_id": {"type": "string"},
            "profile_name": {"type": "string"},
            "profile_full_name": {"type": "string"},
            "profile_context": OBJECT_ARRAY_SCHEMA,
            "profile_context_records": OBJECT_ARRAY_SCHEMA,
            "memory_tool": {"type": "string"},
            "recall_tool": {"type": "string"},
            "profile_context_remember_tool": {"type": "string"},
            "profile_context_list_tool": {"type": "string"},
            "profile_context_forget_tool": {"type": "string"},
            "bias_prompt": {"type": "string"},
            "agent_memory_prompt": {"type": "string"},
            "agent_memory_workflow": {"type": "string"},
            "agent_memory_recall_tool": {"type": "string"},
            "agent_memory_clear_tool": {"type": "string"},
            "agent_memory_dataset": {"type": "string"},
            "resolved_agent_memory_dataset": {"type": "string"},
        },
        required=["session_id"],
    ),
    "brain_remember": object_schema(
        {
            "ingestion_run_id": {"type": "string"},
            "classification": {"type": "string"},
            "memory_cards": OBJECT_ARRAY_SCHEMA,
            "entities": OBJECT_ARRAY_SCHEMA,
            "relationships": OBJECT_ARRAY_SCHEMA,
            "open_loops": OBJECT_ARRAY_SCHEMA,
            "conflicts": OBJECT_ARRAY_SCHEMA,
            "taste": ANY_OBJECT_SCHEMA,
            "dry_run": {"type": "boolean"},
        },
    ),
    "brain_profile_context_remember": object_schema(
        {"id": {"type": "string"}, "statement": {"type": "string"}, "scope": {"type": "string"}},
        required=["id", "statement"],
    ),
    "brain_profile_context_list": object_schema({"profile_context": OBJECT_ARRAY_SCHEMA}, required=["profile_context"]),
    "brain_profile_context_forget": object_schema({"context_id": {"type": "string"}, "status": {"type": "string"}}, required=["status"]),
    "brain_app_data_controls": object_schema(
        {
            "app_write_audit": OBJECT_ARRAY_SCHEMA,
            "profile_context": OBJECT_ARRAY_SCHEMA,
            "preprompt_items": OBJECT_ARRAY_SCHEMA,
            "recent_memory_cards": OBJECT_ARRAY_SCHEMA,
            "open_loops": OBJECT_ARRAY_SCHEMA,
        },
        required=["app_write_audit", "profile_context", "preprompt_items"],
    ),
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
            "source_id": {"type": ["string", "null"]},
            "status": {"type": "string"},
            "memory_cards_created": STRING_ARRAY_SCHEMA,
            "summary": {"type": ["string", "null"]},
            "cognee_sync_status": {"type": "string"},
            "ingestion": ANY_OBJECT_SCHEMA,
        },
        required=["status", "memory_cards_created"],
    ),
    "brain_recall": RECALL_OUTPUT_SCHEMA,
    "brain_profile_entity": RECALL_OUTPUT_SCHEMA,
    "brain_list_open_loops": object_schema({"open_loops": OBJECT_ARRAY_SCHEMA}, required=["open_loops"]),
    "brain_get_memory": object_schema({"memory": {"anyOf": [ANY_OBJECT_SCHEMA, {"type": "null"}]}}, required=["memory"]),
    "brain_get_source": object_schema(
        {
            "source": {"anyOf": [ANY_OBJECT_SCHEMA, {"type": "null"}]},
            "text": {"type": ["string", "null"]},
        },
        required=["source", "text"],
    ),
    "brain_resolve_conflict": object_schema({"status": {"type": "string"}, "action": {"type": "string"}, "created_links": OBJECT_ARRAY_SCHEMA, "updated_memories": OBJECT_ARRAY_SCHEMA}),
    "brain_forget": object_schema({"object_type": {"type": "string"}, "object_id": {"type": "string"}, "status": {"type": "string"}, "mode": {"type": "string"}, "cognee_sync_status": {"type": "string"}}, required=["status"]),
    "brain_review_recent": object_schema({"ingestion_runs": OBJECT_ARRAY_SCHEMA, "sources": OBJECT_ARRAY_SCHEMA, "memory_cards": OBJECT_ARRAY_SCHEMA, "conflicts": OBJECT_ARRAY_SCHEMA}),
    "brain_undo_last": object_schema({"status": {"type": "string"}, "deleted_memories": STRING_ARRAY_SCHEMA, "deleted_sources": STRING_ARRAY_SCHEMA}, required=["status"]),
    "brain_sync_cognee": SYNC_OUTPUT_SCHEMA,
    "brain_rebuild_cognee": object_schema({"status": {"type": "string"}, "dataset": {"type": "string"}, "memory_rows_marked_stale": {"type": "integer"}, "source_rows_marked_stale": {"type": "integer"}}, required=["status"]),
    "cognee_improve": object_schema({"dataset": {"type": "string"}, "resolved_dataset": {"type": "string"}, "node_name": STRING_ARRAY_SCHEMA, "session_ids": STRING_ARRAY_SCHEMA, "run_in_background": {"type": "boolean"}, "result": ANY_OBJECT_SCHEMA}),
    "brain_agent_memory": object_schema({"session_id": {"type": "string"}, "dataset": {"type": "string"}, "resolved_dataset": {"type": "string"}, "node_name": STRING_ARRAY_SCHEMA, "run_in_background": {"type": "boolean"}, "result": ANY_OBJECT_SCHEMA}),
    "brain_agent_memory_recall": object_schema({"query": {"type": "string"}, "dataset": {"type": "string"}, "resolved_dataset": {"type": "string"}, "result": ANY_OBJECT_SCHEMA}),
    "brain_agent_memory_clear": object_schema({"dataset": {"type": "string"}, "resolved_dataset": {"type": "string"}, "result": ANY_OBJECT_SCHEMA}),
    "brain_merge_entities": object_schema({"status": {"type": "string"}, "primary_entity_id": {"type": "string"}, "duplicate_entity_id": {"type": "string"}}, required=["status"]),
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


def prompt_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "brain_agent_memory_protocol",
            "description": (
                "Insert operating instructions for using Brain's portable "
                "agent-memory workflow during an agent conversation."
            ),
            "arguments": [
                {
                    "name": "session_id",
                    "description": (
                        "Brain agent-memory session ID to use consistently. Defaults to the "
                        "active user's resolved Brain agent-memory session."
                    ),
                    "required": False,
                }
            ],
        },
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
    if name == "brain_agent_memory_protocol":
        default_session_id = agent_memory_session_id_for_user(prompt_settings)
        session_id = str(arguments.get("session_id") or default_session_id).strip()
        if not session_id:
            raise ValueError("session_id must not be blank.")
        return prompt_response(
            description=f"Brain agent-memory protocol for session_id={session_id}.",
            text=agent_memory_protocol_prompt(session_id),
        )
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


def agent_memory_protocol_prompt(session_id: str) -> str:
    return f"""## Agent Memory Protocol (Brain)

You have access to Brain MCP tools for portable chat/session memory. Use session_id="{session_id}" consistently for every agent-memory workflow.

**On every conversation start:** call `brain_agent_memory_recall` with a query derived from the user's first message before responding. Silently surface anything relevant.

**During conversation, preserve chat/session context through `brain_agent_memory`, not `brain_remember`, when:**
- A decision is made (technical, architectural, personal)
- A preference or constraint is stated
- A project fact, name, number, or status is established
- The user says "remember", "note", "keep in mind", or similar

**At natural stopping points** (long pause, topic shift, explicit wrap-up): call `brain_agent_memory` with session_id="{session_id}" so the chat can be improved into the dedicated, removable agent-memory dataset.

**Format for preserved chat memory:** concise declarative facts, not transcripts.
Good: "Daniele prefers FastMCP over raw MCP SDK for Python servers."
Bad: "User said they like FastMCP because it's simpler."

**Do not use `brain_remember` for chat/session memory, handovers, conversation summaries, or agent workflow learnings.** Use `brain_remember` only for durable user facts, stable preferences, explicit constraints, durable decisions, and Palate/taste memories.

**Don't narrate** the tool calls. No "I'm now storing this in memory..." — just do it and continue. If recall returns nothing useful, proceed silently.

**On ambiguous references** ("the project", "last time", "what we decided"): call `brain_agent_memory_recall` before asking for clarification.

When the user asks to record or preserve the chat memory using Brain, use Brain's `brain_agent_memory` workflow with session_id="{session_id}" so this session can be improved into the dedicated, removable agent-memory dataset."""


def brain_bias_protocol_prompt(profile_name: str) -> str:
    return f"""## Bias and Preference Protocol (Brain)

You have access to Brain MCP tools including `brain_recall` and `brain_remember`.
Use them to maintain durable preferences, constraints, and communication biases for {profile_name}.

**When the user says "load my preferences from Brain", "load my biases", "use Brain preferences", or similar:**
- Call `brain_recall` before responding.
- Use a query such as: "{profile_name} preferences constraints communication style response format coding preferences".
- Apply relevant recalled preferences silently in the rest of the conversation.
- If recall returns nothing useful, continue without narrating that no preferences were found.

**At the start of a new chat, when this prompt is active:**
- If the first user message implies preferences, prior context, communication style, or "how I like things", call `brain_recall` before responding.
- Otherwise, wait until the user asks to load preferences or makes an ambiguous reference.

**During conversation, call `brain_remember` immediately when the user states or revises a durable bias, preference, or constraint, including:**
- Response style, length, tone, detail level, formatting, or examples
- Engineering standards, architecture preferences, deployment constraints, tool preferences
- Personal defaults, recurring workflows, naming conventions, or "always/never" instructions
- Explicit phrases like "remember", "note", "keep in mind", "I prefer", "I don't like", "from now on"

**Format for `brain_remember`:**
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
        "admin_mcp_path": settings.brain_admin_mcp_path,
        "app_mcp_path": settings.brain_app_mcp_path,
        "public_mcp_url": settings.public_mcp_url,
        "public_admin_mcp_url": settings.public_admin_mcp_url,
        "public_app_mcp_url": settings.public_app_mcp_url,
        "release_env": settings.brain_release_env,
        "release_sha": settings.brain_release_sha,
        "release_version": settings.brain_release_version,
        "uptime_seconds": round(time.time() - STARTED_AT, 3),
    }


@app.get("/", include_in_schema=False)
async def app_root() -> FileResponse:
    return brain_app_file("index.html", "text/html; charset=utf-8")


@app.get("/app", include_in_schema=False)
async def app_dashboard() -> FileResponse:
    return brain_app_file("index.html", "text/html; charset=utf-8")


@app.get("/user", include_in_schema=False)
async def user_dashboard() -> FileResponse:
    return brain_app_file("index.html", "text/html; charset=utf-8")


@app.get("/admin", include_in_schema=False)
async def admin_dashboard() -> FileResponse:
    return brain_app_file("index.html", "text/html; charset=utf-8")


@app.get("/app/oauth/callback", include_in_schema=False)
async def app_oauth_callback() -> FileResponse:
    return brain_app_file("index.html", "text/html; charset=utf-8")


@app.get("/privacy", include_in_schema=False)
async def privacy_page() -> FileResponse:
    return brain_app_file("privacy.html", "text/html; charset=utf-8")


@app.get("/terms", include_in_schema=False)
async def terms_page() -> FileResponse:
    return brain_app_file("terms.html", "text/html; charset=utf-8")


@app.get("/support", include_in_schema=False)
async def support_page() -> FileResponse:
    return brain_app_file("support.html", "text/html; charset=utf-8")


@app.get("/app-assets/{asset_name}", include_in_schema=False)
async def app_asset(asset_name: str) -> FileResponse:
    if asset_name not in {"app.css", "app.js"}:
        raise HTTPException(status_code=404, detail="Not found")
    media_type = "text/css; charset=utf-8" if asset_name.endswith(".css") else "text/javascript; charset=utf-8"
    return brain_app_file(asset_name, media_type)


@app.get("/icon.png", include_in_schema=False)
async def icon_png() -> FileResponse:
    return FileResponse(
        BRAIN_ICON_PATH,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/apple-touch-icon.png", include_in_schema=False)
async def apple_touch_icon_png() -> FileResponse:
    return FileResponse(
        BRAIN_APPLE_TOUCH_ICON_PATH,
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
    if requested == active_settings.brain_app_mcp_path:
        return active_settings.brain_public_app_mcp_path
    if requested == active_settings.brain_mcp_path:
        return active_settings.brain_public_mcp_path
    return requested


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
    if not settings.brain_auth_enabled:
        raise HTTPException(status_code=404, detail="Auth is not enabled")
    rate_limit_oauth(request, "login")
    user_id = normalize_user_id(payload.user_id)
    users = load_auth_users(settings, default_password=auth_admin_password())
    user = users.get(user_id)
    if user is None or not hmac.compare_digest(payload.password, str(user.get("password") or "")):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
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
    if not hmac.compare_digest(payload.current_password, str(user.get("password") or "")):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")
    user["password"] = payload.new_password
    users[user_id] = user
    write_auth_users(settings, users)
    reload_oauth_users()
    return {"user": public_auth_user(user)}


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
        "password": payload.password,
        "display_name": payload.display_name or user_id,
        "email": payload.email or "",
        "superuser": str(payload.superuser).lower(),
    }
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
        updated["password"] = payload.password
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
    payload: IngestSourceRequest | RememberRequest,
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


@app.get("/memory/open_loops")
async def brain_open_loops_endpoint(
    topic: str | None = None,
    status: str = "open",
    limit: int = 20,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    return authenticated_dict_response(
        authorization,
        lambda active_settings: {
            "open_loops": brain_list_open_loops(
                active_settings,
                topic=topic,
                status=status,
                limit=limit,
            )
        },
    )


@app.get("/memory/{memory_id}")
async def brain_get_memory_endpoint(
    memory_id: str,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    active_settings = require_api_auth(authorization, settings)
    memory = brain_get_memory(memory_id, active_settings)
    if memory is None:
        raise HTTPException(status_code=404, detail=f"Memory not found: {memory_id}")
    return {"memory": memory}


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


@app.post("/memory/resolve_conflict")
async def brain_resolve_conflict_endpoint(
    payload: ResolveConflictRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    return authenticated_dict_response(
        authorization,
        lambda active_settings: brain_resolve_conflict(
            active_settings,
            conflict_memory_id=payload.conflict_memory_id,
            target_memory_id=payload.target_memory_id,
            action=payload.action,
            note=payload.note,
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
            include_sources=payload.include_sources,
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


@app.post("/memory/sync_cognee")
async def brain_sync_cognee_endpoint(
    payload: SyncCogneeRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    return authenticated_dict_response(
        authorization,
        lambda active_settings: brain_sync_cognee(
            active_settings,
            object_type=payload.object_type,
            object_id=payload.object_id,
            dataset=payload.dataset,
            force=payload.force,
        ),
    )


@app.post("/memory/rebuild_cognee")
async def brain_rebuild_cognee_endpoint(
    payload: RebuildCogneeRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    return authenticated_dict_response(
        authorization,
        lambda active_settings: brain_rebuild_cognee(
            active_settings,
            dataset=payload.dataset,
            prune_first=payload.prune_first,
            confirm=payload.confirm,
        ),
    )


@app.post("/memory/merge_entities")
async def brain_merge_entities_endpoint(
    payload: MergeEntitiesRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    return authenticated_dict_response(
        authorization,
        lambda active_settings: brain_merge_entities(
            active_settings,
            primary_entity_id=payload.primary_entity_id,
            duplicate_entity_id=payload.duplicate_entity_id,
            reason=payload.reason,
            confirm=payload.confirm,
        ),
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
    elif requested_path in {settings.brain_mcp_path, settings.brain_app_mcp_path}:
        surface = MCP_SURFACE_CHATGPT_APP
        public_path = (
            settings.brain_public_mcp_path
            if requested_path == settings.brain_mcp_path
            else settings.brain_public_app_mcp_path
        )
    else:
        raise HTTPException(status_code=404, detail="Not found")

    if request.method == "GET":
        auth_context = mcp_auth_context(authorization, settings, request=request, session_cookie=brain_web_session)
        if settings.brain_auth_enabled and not auth_context.authenticated:
            return auth_challenge(settings, public_path)
        if (
            settings.brain_auth_enabled
            and surface == MCP_SURFACE_INTERNAL
            and not auth_context.static_token
            and not auth_user_is_superuser(auth_context.user_id)
        ):
            raise HTTPException(status_code=403, detail="Superuser privileges are required.")
        return JSONResponse(
            {
                "service": settings.brain_service_name,
                "mcp_path": requested_path,
                "public_mcp_url": (
                    settings.public_app_mcp_url
                    if surface == MCP_SURFACE_CHATGPT_APP
                    else settings.public_mcp_url
                ),
                "surface": surface,
                "status": "ready",
            }
        )

    payload = await request.json()
    auth_context = mcp_auth_context(authorization, settings, request=request, session_cookie=brain_web_session)
    if settings.brain_auth_enabled and not auth_context.authenticated:
        return auth_challenge(settings, public_path)
    if (
        settings.brain_auth_enabled
        and surface == MCP_SURFACE_INTERNAL
        and not auth_context.static_token
        and not auth_user_is_superuser(auth_context.user_id)
    ):
        raise HTTPException(status_code=403, detail="Superuser privileges are required.")
    if auth_context.web_session:
        require_web_csrf(request, brain_web_session)
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
        if record is not None:
            return McpAuthContext(
                authenticated=True,
                token=token,
                client_id=record.get("client_id"),
                user_id=record.get("user_id") or active_settings.brain_user_id,
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


def require_app_scopes(
    request_context: McpRequestContext | None,
    *,
    surface: str,
    scopes: list[str],
) -> None:
    if surface != MCP_SURFACE_CHATGPT_APP or not settings.brain_auth_enabled:
        return
    auth = request_context.auth if request_context else McpAuthContext()
    if auth.static_token:
        return
    missing = [scope for scope in scopes if scope not in auth.scopes]
    if missing:
        raise ValueError(f"Insufficient OAuth scope for ChatGPT App MCP call: {', '.join(missing)}")


def settings_for_request_context(request_context: McpRequestContext | None) -> Settings:
    user_id = request_context.auth.user_id if request_context and request_context.auth.user_id else settings.brain_user_id
    if user_id == settings.brain_user_id:
        return settings
    return settings.model_copy(update={"brain_user_id": user_id})


def settings_for_auth_context(active_settings: Settings, auth_context: McpAuthContext) -> Settings:
    user_id = auth_context.user_id or active_settings.brain_user_id
    if user_id == active_settings.brain_user_id:
        return active_settings
    return active_settings.model_copy(update={"brain_user_id": user_id})


def require_api_auth(header_value: str | None, active_settings: Settings) -> Settings:
    auth_context = mcp_auth_context(
        header_value,
        active_settings,
        required_scopes=active_settings.brain_auth_scope_list,
    )
    if active_settings.brain_auth_enabled and not auth_context.authenticated:
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
    if settings.brain_auth_enabled and not auth_context.authenticated:
        raise HTTPException(
            status_code=401,
            detail=authentication_required_payload(settings),
            headers=auth_challenge_headers(settings),
        )
    if require_csrf and auth_context.web_session:
        require_web_csrf(request, session_cookie)
    user_id = auth_context.user_id or settings.brain_user_id
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
            require_app_scopes(request_context, surface=surface, scopes=[APP_TOOL_READ_SCOPE])
            result = {"tools": memory_tool_definitions(surface=surface)}
        elif method == "prompts/list":
            require_app_scopes(request_context, surface=surface, scopes=[APP_TOOL_READ_SCOPE])
            result = {"prompts": prompt_definitions()}
        elif method == "prompts/get":
            require_app_scopes(request_context, surface=surface, scopes=[APP_TOOL_READ_SCOPE])
            prompt_settings = settings_for_request_context(request_context)
            result = get_prompt(
                str(params.get("name", "")),
                params.get("arguments") or {},
                prompt_settings,
            )
        elif method == "resources/list":
            require_app_scopes(request_context, surface=surface, scopes=[APP_TOOL_READ_SCOPE])
            result = {"resources": resource_definitions()}
        elif method == "resources/templates/list":
            require_app_scopes(request_context, surface=surface, scopes=[APP_TOOL_READ_SCOPE])
            result = {"resourceTemplates": resource_template_definitions()}
        elif method == "resources/read":
            require_app_scopes(request_context, surface=surface, scopes=[APP_TOOL_READ_SCOPE])
            result = read_resource(str(params.get("uri", "")), request_context=request_context)
        elif method == "tools/call":
            tool_name = str(params.get("name") or "") if isinstance(params, dict) else ""
            require_app_scopes(
                request_context,
                surface=surface,
                scopes=app_tool_required_scopes(tool_name),
            )
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
    if surface == MCP_SURFACE_CHATGPT_APP and name in APP_MUTATING_TOOLS:
        rate_limit_app_write(request_context, tool_name=name)
    try:
        result = await call_tool_dispatch(
            params,
            surface=surface,
            request_context=request_context,
        )
    except Exception as exc:
        audit_app_write(
            name,
            arguments,
            surface=surface,
            request_context=request_context,
            status="failed",
            summary=str(exc),
        )
        raise
    audit_app_write(
        name,
        arguments,
        surface=surface,
        request_context=request_context,
        status="succeeded",
        response=result,
    )
    return result


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
            summary=f"Brain session resolved: {payload['session_id']}.",
        )

    if name == "brain_remember":
        arguments = confirmation_first_arguments(arguments, surface=surface)
        request = RememberRequest.model_validate(
            {
                "input": arguments.get("input", ""),
                "input_type": arguments.get("input_type", "auto"),
                "observed_at": arguments.get("observed_at"),
                "source_policy": arguments.get("source_policy", "auto"),
                "dry_run": bool(arguments.get("dry_run", False)),
                "context": arguments.get("context") or {},
            }
        )
        payload = brain_remember(request, settings).model_dump(mode="json")
        return json_tool_response(payload, summary=remember_summary(payload))

    if name == "brain_profile_context_remember":
        require_app_confirmation(
            arguments,
            surface=surface,
            action="save profile context",
        )
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
        require_app_confirmation(
            arguments,
            surface=surface,
            action="remove profile context",
        )
        request = BrainProfileContextForgetRequest.model_validate(arguments)
        payload = forget_profile_context(settings, context_id=request.context_id)
        return json_tool_response(
            payload,
            summary=f"Profile context forget result: {payload['status']}.",
        )

    if name == "brain_app_data_controls":
        limit = bounded_int(arguments.get("limit", 20), minimum=1, maximum=100)
        store = BrainStore(settings)
        records = list_profile_context(settings)
        profile_context = [item for item in records if item.get("scope") != "brain_preprompt"]
        preprompt_items = [item for item in records if item.get("scope") == "brain_preprompt"]
        payload = {
            "app_write_audit": store.list_app_write_audit(limit=limit),
            "profile_context": profile_context,
            "preprompt_items": preprompt_items,
            "recent_memory_cards": (
                store.list_memory_cards(limit=limit)
                if bool(arguments.get("include_recent_memories", True))
                else []
            ),
            "open_loops": brain_list_open_loops(settings, limit=limit),
        }
        return json_tool_response(
            payload,
            summary=(
                f"Loaded {len(payload['app_write_audit'])} app write audit records "
                f"and {len(profile_context)} profile context items."
            ),
        )

    if name == "brain_profile_context_sync":
        payload = sync_profile_context(settings)
        return json_tool_response(
            payload,
            summary=f"Profile context sync complete: {payload['synced_count']} items.",
        )

    if name == "brain_ingest_source":
        arguments = confirmation_first_arguments(arguments, surface=surface)
        if "source" in arguments:
            request = IngestSourceRequest.model_validate(
                {
                    "source": arguments["source"],
                    "source_kind": arguments.get("source_kind", "auto"),
                    "title": arguments.get("title"),
                    "why_saved": arguments.get("why_saved"),
                    "extract_memories": bool(arguments.get("extract_memories", True)),
                    "dry_run": bool(arguments.get("dry_run", False)),
                    "run_in_background": bool(arguments.get("run_in_background", False)),
                    "metadata": arguments.get("metadata") or {},
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
                    "run_in_background": bool(arguments.get("run_in_background", False)),
                    "context": arguments.get("context") or {},
                }
            )
        receipt = brain_ingest_source(request, settings).model_dump(mode="json")
        payload = {
            "source_id": receipt.get("source", {}).get("source_id"),
            "status": "queued" if receipt.get("cognee_sync_status") == "queued" else "processed",
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
                "Queued source ingestion in the background."
                if payload["status"] == "queued"
                else f"Ingested source and created {len(payload['memory_cards_created'])} memories."
            ),
        )

    if name == "brain_recall":
        request = RecallRequest.model_validate(
            {
                "query": arguments["query"],
                "mode": arguments.get("mode", "auto"),
                "include_sources": bool(arguments.get("include_sources", True)),
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

    if name == "brain_list_open_loops":
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

    if name == "brain_get_memory":
        memory = brain_get_memory(str(arguments["memory_id"]), settings)
        return json_tool_response(
            {"memory": memory},
            summary="Memory found." if memory else "Memory not found.",
        )

    if name == "brain_get_source":
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

    if name == "brain_resolve_conflict":
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
        mode = "hard" if hard else "soft"
        payload = {**payload, "mode": mode, "cognee_sync_status": "stale"}
        return json_tool_response(payload, summary=f"{mode.title()} delete result: {payload['status']}.")

    if name == "brain_review_recent":
        payload = brain_review_recent(
            settings,
            since=parse_optional_datetime(arguments.get("since")),
            limit=bounded_int(arguments.get("limit", 20), minimum=1, maximum=100),
            include_sources=bool(arguments.get("include_sources", True)),
        )
        return json_tool_response(
            payload,
            summary=(
                f"Found {len(payload['memory_cards'])} recent memories and "
                f"{len(payload['ingestion_runs'])} ingestion runs."
            ),
        )

    if name == "brain_undo_last":
        require_app_confirmation(
            arguments,
            surface=surface,
            action="undo the latest Brain write",
        )
        payload = brain_undo_last(
            settings,
            ingestion_run_id=arguments.get("ingestion_run_id"),
        )
        return json_tool_response(
            payload,
            summary=f"Undo result: {payload['status']}.",
        )

    if name == "brain_sync_cognee":
        payload = brain_sync_cognee(
            settings,
            object_type=str(arguments.get("object_type", "all")),
            object_id=arguments.get("object_id"),
            dataset=str(arguments.get("dataset", "all")),
            force=bool(arguments.get("force", False)),
        )
        return json_tool_response(
            payload,
            summary=f"Cognee sync {payload.get('status', 'complete')}: {payload.get('processed', 0)} rows.",
        )

    if name == "brain_rebuild_cognee":
        payload = brain_rebuild_cognee(
            settings,
            dataset=str(arguments.get("dataset", "all")),
            prune_first=bool(arguments.get("prune_first", False)),
            confirm=bool(arguments.get("confirm", False)),
        )
        return json_tool_response(
            payload,
            summary=(
                "Cognee rebuild queued: "
                f"{payload.get('memory_rows_marked_stale', 0)} memories, "
                f"{payload.get('source_rows_marked_stale', 0)} sources."
            ),
        )

    if name == "cognee_improve":
        request = CogneeImproveRequest.model_validate(arguments)
        dataset = configured_cognee_dataset(request.dataset, settings)
        result = await improve_cognee(
            dataset=dataset,
            node_name=request.node_name,
            session_ids=request.session_ids,
            run_in_background=request.run_in_background,
            settings=settings,
        )
        payload = {
            "dataset": request.dataset,
            "resolved_dataset": dataset,
            "node_name": request.node_name or [],
            "session_ids": request.session_ids or [],
            "run_in_background": request.run_in_background,
            "result": to_jsonable(result),
        }
        return json_tool_response(payload, summary=f"Cognee improve queued for {dataset}.")

    if name == "brain_agent_memory":
        request = BrainAgentMemoryRequest.model_validate(arguments)
        session_id = request.session_id.strip()
        if not session_id:
            raise ValueError("session_id must not be blank.")
        expected_session_id = agent_memory_session_id_for_user(settings)
        if session_id != expected_session_id:
            raise ValueError("session_id must match the active user's session_id returned by brain_session.")
        dataset = agent_memory_dataset_for_user(settings)
        result = await improve_cognee(
            dataset=dataset,
            node_name=request.node_name,
            session_ids=[session_id],
            run_in_background=request.run_in_background,
            settings=settings,
        )
        payload = {
            "session_id": session_id,
            "dataset": "agent_memory",
            "resolved_dataset": dataset,
            "node_name": request.node_name or [],
            "run_in_background": request.run_in_background,
            "result": to_jsonable(result),
        }
        return json_tool_response(
            payload,
            summary=f"Agent session memory improved into {dataset}.",
        )

    if name == "brain_agent_memory_recall":
        request = BrainAgentMemoryRecallRequest.model_validate(arguments)
        dataset = agent_memory_dataset_for_user(settings)
        result = await recall_text(
            query=request.query,
            dataset=dataset,
            search_type="GRAPH_COMPLETION",
            top_k=bounded_int(request.top_k, minimum=1, maximum=50),
            settings=settings,
        )
        payload = {
            "query": request.query,
            "dataset": "agent_memory",
            "resolved_dataset": dataset,
            "result": to_jsonable(result),
        }
        return json_tool_response(payload, summary="Agent memory recall complete.")

    if name == "brain_agent_memory_clear":
        request = BrainAgentMemoryClearRequest.model_validate(arguments)
        if not request.confirm:
            raise ValueError("brain_agent_memory_clear requires confirm=true.")
        dataset = agent_memory_dataset_for_user(settings)
        result = await delete_cognee_datasource(dataset, settings=settings)
        payload = {
            "dataset": "agent_memory",
            "resolved_dataset": dataset,
            "result": to_jsonable(result),
        }
        return json_tool_response(payload, summary=f"Agent memory dataset cleared: {dataset}.")

    if name == "brain_merge_entities":
        payload = brain_merge_entities(
            settings,
            primary_entity_id=str(arguments["primary_entity_id"]),
            duplicate_entity_id=str(arguments["duplicate_entity_id"]),
            reason=arguments.get("reason"),
            confirm=bool(arguments.get("confirm", False)),
        )
        return json_tool_response(
            payload,
            summary=f"Merged duplicate entity {payload['duplicate_entity_id']}.",
        )

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


def confirmation_first_arguments(arguments: Any, *, surface: str) -> dict[str, Any]:
    if not isinstance(arguments, dict):
        return {}
    normalized = dict(arguments)
    if surface != MCP_SURFACE_CHATGPT_APP:
        return normalized
    context = normalized.get("context")
    if not isinstance(context, dict):
        context = {}
    confirmed = bool(
        context.get("confirmed_by_user")
        or context.get("app_confirmed")
        or normalized.get("confirmed_by_user")
    )
    if not confirmed:
        normalized["dry_run"] = True
        normalized["context"] = {
            **context,
            "confirmation_required": True,
            "confirmation_surface": MCP_SURFACE_CHATGPT_APP,
        }
    return normalized


def require_app_confirmation(arguments: Any, *, surface: str, action: str) -> None:
    if surface != MCP_SURFACE_CHATGPT_APP:
        return
    if not app_confirmed(arguments):
        raise ValueError(
            f"Explicit user confirmation is required to {action} on the "
            "chatgpt_app MCP surface. Call again with confirmed_by_user=true "
            "only after the user confirms."
        )


def app_confirmed(arguments: Any) -> bool:
    if not isinstance(arguments, dict):
        return False
    context = arguments.get("context")
    if not isinstance(context, dict):
        context = {}
    return bool(
        arguments.get("confirmed_by_user")
        or arguments.get("app_confirmed")
        or context.get("confirmed_by_user")
        or context.get("app_confirmed")
    )


def rate_limit_app_write(
    request_context: McpRequestContext | None,
    *,
    tool_name: str,
) -> None:
    auth = request_context.auth if request_context else McpAuthContext()
    identity = auth.client_id or auth.token or request_context.remote_addr if request_context else None
    key = f"app-write:{tool_name}:{identity or 'anonymous'}"
    limit = max(1, settings.brain_app_write_rate_limit_count)
    window = max(1, settings.brain_app_write_rate_limit_window_seconds)
    now = time.monotonic()
    bucket = _rate_limit_buckets[key]
    while bucket and now - bucket[0] > window:
        bucket.popleft()
    if len(bucket) >= limit:
        raise ValueError(
            f"Rate limit exceeded for ChatGPT App write calls; retry after {window} seconds."
        )
    bucket.append(now)


def audit_app_write(
    tool_name: str,
    arguments: Any,
    *,
    surface: str,
    request_context: McpRequestContext | None,
    status: str,
    response: dict[str, Any] | None = None,
    summary: str | None = None,
) -> None:
    if surface != MCP_SURFACE_CHATGPT_APP or tool_name not in APP_MUTATING_TOOLS:
        return
    try:
        structured = (response or {}).get("structuredContent") if response else None
        auth = request_context.auth if request_context else McpAuthContext()
        BrainStore(settings_for_request_context(request_context)).create_app_write_audit(
            tool_name=tool_name,
            status=status,
            confirmed_by_user=app_confirmed(arguments),
            client_id=auth.client_id,
            subject=app_write_subject(auth),
            request_id=str(request_context.json_rpc_id) if request_context else None,
            target_id=app_write_target_id(tool_name, arguments, structured),
            summary=summary or app_write_summary(tool_name, structured),
            metadata_json={
                "surface": MCP_SURFACE_CHATGPT_APP,
                "remote_addr": request_context.remote_addr if request_context else None,
            },
        )
    except Exception:
        return


def app_write_subject(auth: McpAuthContext) -> str | None:
    if auth.static_token:
        return "static_token"
    if auth.client_id:
        return f"oauth_client:{auth.client_id}"
    return None


def app_write_target_id(tool_name: str, arguments: Any, structured: Any) -> str | None:
    if isinstance(structured, dict):
        if tool_name == "brain_profile_context_remember":
            return structured.get("id")
        if tool_name == "brain_profile_context_forget":
            return structured.get("context_id") or (arguments or {}).get("context_id")
        if tool_name == "brain_undo_last":
            return structured.get("ingestion_run_id") or (arguments or {}).get("ingestion_run_id")
        if tool_name == "brain_remember":
            memory_ids = [
                str(card.get("id"))
                for card in structured.get("memory_cards", [])
                if isinstance(card, dict) and card.get("created") and card.get("id")
            ]
            return ",".join(memory_ids[:5]) if memory_ids else structured.get("ingestion_run_id")
        if tool_name == "brain_ingest_source":
            return structured.get("source_id") or (
                (structured.get("ingestion") or {}).get("ingestion_run_id")
            )
        if tool_name in {
            "brain_palate_confirm",
            "brain_palate_cancel",
            "brain_palate_correct_proposal",
        }:
            return structured.get("proposal_id") or (arguments or {}).get("proposal_id")
    if isinstance(arguments, dict):
        return arguments.get("context_id") or arguments.get("ingestion_run_id")
    return None


def app_write_summary(tool_name: str, structured: Any) -> str | None:
    if not isinstance(structured, dict):
        return tool_name
    if tool_name == "brain_remember":
        created = sum(
            1
            for card in structured.get("memory_cards", [])
            if isinstance(card, dict) and card.get("created")
        )
        return f"brain_remember dry_run={bool(structured.get('dry_run'))} created={created}"
    if tool_name == "brain_ingest_source":
        return (
            f"brain_ingest_source status={structured.get('status')} "
            f"source_id={structured.get('source_id')}"
        )
    if tool_name in {
        "brain_palate_confirm",
        "brain_palate_cancel",
        "brain_palate_correct_proposal",
    }:
        return f"{tool_name} proposal_id={structured.get('proposal_id')}"
    if tool_name == "brain_profile_context_remember":
        return f"profile_context scope={structured.get('scope')} id={structured.get('id')}"
    if tool_name == "brain_profile_context_forget":
        return f"profile_context_forget status={structured.get('status')}"
    if tool_name == "brain_undo_last":
        return f"undo_last status={structured.get('status')}"
    return tool_name


def configured_cognee_dataset(dataset: str, active_settings: Settings) -> str:
    mapping = {
        "memory": active_settings.brain_cognee_memory_dataset,
        "sources": active_settings.brain_cognee_sources_dataset,
        "data": active_settings.brain_cognee_data_dataset,
        "palate": active_settings.brain_cognee_palate_dataset,
        "agent_memory": agent_memory_dataset_for_user(active_settings),
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


def parse_optional_datetime(value: Any) -> datetime | None:
    if value in {None, ""}:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    return datetime.fromisoformat(text)


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
