from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
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
from memory_stack.brain_store import BrainStore
from memory_stack.cognee_adapter import (
    DatasourceNotFoundError,
    create_datasource as create_cognee_datasource,
    delete_datasource as delete_cognee_datasource,
    improve_cognee,
    list_datasources as list_cognee_datasources,
    recall_text,
)
from memory_stack.cfg import Settings, load_settings
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
from memory_stack.io import to_jsonable
from memory_stack.oauth import BrainOAuthProvider, parse_bearer
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


class BrainProfileContextForgetRequest(BaseModel):
    context_id: str


class MergeEntitiesRequest(BaseModel):
    primary_entity_id: str
    duplicate_entity_id: str
    reason: str | None = None
    confirm: bool = False


def memory_tool_definitions() -> list[dict[str, Any]]:
    tools = [
        {
            "name": "brain_session",
            "description": (
                "Resolve the configured Brain session identity agents should use "
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
                "High-confidence palate memories may route to Brain Palate automatically."
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
            "description": "Bridge one Cognee agent session into the dedicated, removable agent-memory dataset.",
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
            "description": "Normalize and enrich a palate item without storing it.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "item_text": {"type": "string"},
                    "entity_type": {"type": "string"},
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
            "description": "Rank canonical palate records for a recommendation or comparison query.",
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
            "description": "Rank only supplied options against canonical palate records.",
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
    return tools_with_output_schemas(tools)


def tools_with_output_schemas(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {**tool, "outputSchema": tool_output_schema(str(tool["name"]))}
        for tool in tools
    ]


def tool_output_schema(tool_name: str) -> dict[str, Any]:
    return STRUCTURED_OUTPUT_SCHEMAS.get(tool_name, ANY_OBJECT_SCHEMA)


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
            "owner": ANY_OBJECT_SCHEMA,
            "profile_context": OBJECT_ARRAY_SCHEMA,
            "agent_memory": ANY_OBJECT_SCHEMA,
            "instructions": {"type": "string"},
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
    "brain_profile_context_sync": object_schema({"synced_count": {"type": "integer"}, "results": OBJECT_ARRAY_SCHEMA}, required=["synced_count"]),
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
                "Insert operating instructions for using Cognee session memory "
                "during an agent conversation."
            ),
            "arguments": [
                {
                    "name": "session_id",
                    "description": (
                        "Cognee session ID to use consistently. Defaults to the "
                        "configured Brain agent-memory session."
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


def get_prompt(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "brain_agent_memory_protocol":
        session_id = str(arguments.get("session_id") or settings.brain_agent_memory_session_id).strip()
        if not session_id:
            raise ValueError("session_id must not be blank.")
        return prompt_response(
            description=f"Cognee session-memory protocol for session_id={session_id}.",
            text=agent_memory_protocol_prompt(session_id),
        )
    if name == "brain_bias_protocol":
        profile_name = str(arguments.get("profile_name") or settings.brain_owner_name).strip()
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
    return f"""## Memory Protocol (Cognee)

You have access to a Cognee MCP server with `remember`, `recall`, and `forget`.
Use session_id="{session_id}" consistently across all calls.

**On every conversation start:** call `recall` with a query derived from the user's first message before responding. Silently surface anything relevant.

**During conversation, call `remember` immediately when:**
- A decision is made (technical, architectural, personal)
- A preference or constraint is stated
- A project fact, name, number, or status is established
- The user says "remember", "note", "keep in mind", or similar

**At natural stopping points** (long pause, topic shift, explicit wrap-up): call `remember` with a concise summary of what was established.

**Format for remember:** one declarative sentence per fact, not transcripts.
Good: "Daniele prefers FastMCP over raw MCP SDK for Python servers."
Bad: "User said they like FastMCP because it's simpler."

**Don't narrate** the tool calls. No "I'm now storing this in memory..." — just do it and continue. If recall returns nothing useful, proceed silently.

**On ambiguous references** ("the project", "last time", "what we decided"): call `recall` before asking for clarification.

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
    return authenticated_model_response(
        authorization,
        lambda: brain_remember(payload, settings),
    )


@app.post("/memory/ingest_source")
async def brain_ingest_source_endpoint(
    payload: IngestSourceRequest | RememberRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    return authenticated_model_response(
        authorization,
        lambda: brain_ingest_source(payload, settings),
    )


@app.post("/memory/recall")
async def brain_recall_endpoint(
    payload: RecallRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    return authenticated_model_response(
        authorization,
        lambda: brain_recall(payload, settings),
    )


@app.post("/memory/profile_entity")
async def brain_profile_entity_endpoint(
    payload: ProfileEntityRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    return authenticated_model_response(
        authorization,
        lambda: brain_profile_entity(
            settings,
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
        lambda: {
            "open_loops": brain_list_open_loops(
                settings,
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
    return authenticated_dict_response(
        authorization,
        lambda: brain_forget(
            settings,
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
        lambda: brain_resolve_conflict(
            settings,
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
        lambda: brain_review_recent(
            settings,
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
        lambda: brain_undo_last(settings, ingestion_run_id=payload.ingestion_run_id),
    )


@app.post("/memory/sync_cognee")
async def brain_sync_cognee_endpoint(
    payload: SyncCogneeRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    return authenticated_dict_response(
        authorization,
        lambda: brain_sync_cognee(
            settings,
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
        lambda: brain_rebuild_cognee(
            settings,
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
        lambda: brain_merge_entities(
            settings,
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


def authenticated_model_response(authorization: str | None, factory: Any) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    return factory().model_dump(mode="json")


def authenticated_dict_response(authorization: str | None, factory: Any) -> dict[str, Any]:
    require_api_auth(authorization, settings)
    return factory()


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
                "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                "serverInfo": {"name": "brain", "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {"tools": memory_tool_definitions()}
        elif method == "prompts/list":
            result = {"prompts": prompt_definitions()}
        elif method == "prompts/get":
            result = get_prompt(
                str(params.get("name", "")),
                params.get("arguments") or {},
            )
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
    name = str(params.get("name") or "")
    arguments = params.get("arguments") or {}
    if name == "brain_session":
        payload = brain_session_payload(settings)
        return json_tool_response(
            payload,
            summary=f"Brain session resolved: {payload['session_id']}.",
        )

    if name == "brain_remember":
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

    if name == "brain_profile_context_sync":
        payload = sync_profile_context(settings)
        return json_tool_response(
            payload,
            summary=f"Profile context sync complete: {payload['synced_count']} items.",
        )

    if name == "brain_ingest_source":
        if "source" in arguments:
            request = IngestSourceRequest.model_validate(
                {
                    "source": arguments["source"],
                    "source_kind": arguments.get("source_kind", "auto"),
                    "title": arguments.get("title"),
                    "why_saved": arguments.get("why_saved"),
                    "extract_memories": bool(arguments.get("extract_memories", True)),
                    "dry_run": bool(arguments.get("dry_run", False)),
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
                    "context": arguments.get("context") or {},
                }
            )
        receipt = brain_ingest_source(request, settings).model_dump(mode="json")
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
        dataset = settings.brain_cognee_agent_memory_dataset
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
        dataset = settings.brain_cognee_agent_memory_dataset
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
        dataset = settings.brain_cognee_agent_memory_dataset
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


def configured_cognee_dataset(dataset: str, active_settings: Settings) -> str:
    mapping = {
        "memory": active_settings.brain_cognee_memory_dataset,
        "sources": active_settings.brain_cognee_sources_dataset,
        "data": active_settings.brain_cognee_data_dataset,
        "palate": active_settings.brain_cognee_palate_dataset,
        "agent_memory": active_settings.brain_cognee_agent_memory_dataset,
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
