from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from memory_stack.brain_store import normalize_name, normalize_user_id
from memory_stack.cfg import Settings

class BrainContextDataPoint(BaseModel):
    datapoint_type: str = "BrainContextDataPoint"
    external_id: str
    user_id: str
    profile_name: str
    kind: str
    statement: str
    scope: str
    source: str | None = None
    status: str = "current"
    metadata: dict[str, Any] = Field(default_factory=dict)


class BrainStatusEventDataPoint(BaseModel):
    datapoint_type: str = "BrainStatusEventDataPoint"
    external_id: str
    receipt_id: str
    target_external_id: str
    action: str
    status: str
    reason: str | None = None
    timestamp: str
    metadata: dict[str, Any] = Field(default_factory=dict)


def profile_name_from_context(context: dict[str, Any], settings: Settings) -> str:
    value = context.get("profile_name") or context.get("profile")
    profile_name = str(value).strip() if value else settings.brain_owner_name
    return profile_name or "default"


def surface_from_context(context: dict[str, Any]) -> str:
    value = context.get("surface") or context.get("client") or context.get("client_id")
    surface = str(value).strip() if value else "api"
    return surface or "api"


def client_session_id_from_context(context: dict[str, Any]) -> str:
    value = context.get("client_session_id") or context.get("session_id")
    session_id = str(value).strip() if value else "default"
    return session_id or "default"


def common_node_sets(*, user_id: str, profile_name: str) -> list[str]:
    return dedupe_node_sets(
        [
            "brain",
            f"user:{normalize_user_id(user_id)}",
            f"profile:{node_label(profile_name)}",
        ]
    )

def context_node_sets(
    *,
    user_id: str,
    profile_name: str,
    kind: str,
    scope: str,
) -> list[str]:
    node_sets = common_node_sets(user_id=user_id, profile_name=profile_name)
    node_sets.extend(
        [
            "brain_context",
            f"context_kind:{node_label(kind)}",
            f"context_scope:{node_label(scope)}",
        ]
    )
    return dedupe_node_sets(node_sets)

def status_event_node_sets(
    *,
    user_id: str,
    profile_name: str,
    action: str,
    status: str,
) -> list[str]:
    node_sets = common_node_sets(user_id=user_id, profile_name=profile_name)
    node_sets.extend(
        [
            "brain_status_event",
            f"status_action:{node_label(action)}",
            f"status:{node_label(status)}",
        ]
    )
    return dedupe_node_sets(node_sets)


def palate_node_sets(
    *,
    user_id: str,
    profile_name: str,
    point_kind: str,
    palate_type: str | None = None,
    status: str = "current",
    dataset_name: str | None = None,
) -> list[str]:
    node_sets = common_node_sets(user_id=user_id, profile_name=profile_name)
    resolved_type = palate_type or point_kind
    node_sets.extend(
        [
            "brain_palate",
            f"taste:{node_label(resolved_type)}",
            f"palate_kind:{node_label(point_kind)}",
            f"palate_status:{node_label(status)}",
        ]
    )
    if dataset_name:
        node_sets.append(f"dataset:{node_label(dataset_name)}")
    return dedupe_node_sets(node_sets)

def context_datapoint(
    *,
    external_id: str,
    user_id: str,
    profile_name: str,
    kind: str,
    statement: str,
    scope: str,
    source: str | None = None,
    status: str = "current",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return BrainContextDataPoint(
        external_id=external_id,
        user_id=normalize_user_id(user_id),
        profile_name=profile_name,
        kind=kind,
        statement=statement,
        scope=scope,
        source=source,
        status=status,
        metadata=metadata or {},
    ).model_dump(mode="json")


def status_event_datapoint(
    *,
    external_id: str,
    receipt_id: str,
    target_external_id: str,
    action: str,
    status: str,
    timestamp: datetime,
    reason: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return BrainStatusEventDataPoint(
        external_id=external_id,
        receipt_id=receipt_id,
        target_external_id=target_external_id,
        action=action,
        status=status,
        reason=reason,
        timestamp=timestamp.isoformat(),
        metadata=metadata or {},
    ).model_dump(mode="json")


def datapoint_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)

def node_label(value: str) -> str:
    label = normalize_name(value).replace(" ", "_")
    return label or "default"


def dedupe_node_sets(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
