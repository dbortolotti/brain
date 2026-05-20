from __future__ import annotations

import hashlib
from typing import Any

from memory_stack.brain_store import normalize_user_id
from memory_stack.cfg import Settings
from memory_stack.profile_context import list_profile_context


USER_SCOPE_HASH_LENGTH = 16


def user_scope_suffix(user_id: str | None) -> str:
    active_user_id = normalize_user_id(user_id)
    digest = hashlib.sha256(active_user_id.encode("utf-8")).hexdigest()[:USER_SCOPE_HASH_LENGTH]
    return f"u_{digest}"


def agent_memory_session_id_for_user(settings: Settings, *, user_id: str | None = None) -> str:
    base_session_id = settings.brain_agent_memory_session_id.strip()
    if not base_session_id:
        raise ValueError("BRAIN_AGENT_MEMORY_SESSION_ID must not be blank.")
    active_user_id = normalize_user_id(user_id or settings.brain_user_id)
    return f"{base_session_id}:{user_scope_suffix(active_user_id)}"


def agent_memory_dataset_for_user(settings: Settings, *, user_id: str | None = None) -> str:
    base_dataset = settings.brain_cognee_agent_memory_dataset.strip()
    if not base_dataset:
        raise ValueError("BRAIN_COGNEE_AGENT_MEMORY_DATASET must not be blank.")
    active_user_id = normalize_user_id(user_id or settings.brain_user_id)
    return f"{base_dataset}__{user_scope_suffix(active_user_id)}"


def brain_session_payload(settings: Settings, *, user_id: str | None = None) -> dict[str, Any]:
    active_user_id = normalize_user_id(user_id or settings.brain_user_id)
    session_id = agent_memory_session_id_for_user(settings, user_id=active_user_id)
    profile_context_records = list_profile_context(settings, user_id=active_user_id)
    return {
        "user_id": active_user_id,
        "session_id": session_id,
        "profile_name": settings.brain_owner_name,
        "profile_full_name": settings.brain_owner_full_name,
        "profile_context": [dict(record) for record in profile_context_records],
        "profile_context_records": profile_context_records,
        "memory_tool": "brain_remember",
        "recall_tool": "brain_recall",
        "profile_context_remember_tool": "brain_profile_context_remember",
        "profile_context_list_tool": "brain_profile_context_list",
        "profile_context_forget_tool": "brain_profile_context_forget",
        "bias_prompt": "brain_bias_protocol",
        "agent_memory_prompt": "brain_agent_memory_protocol",
        "agent_memory_workflow": "brain_agent_memory",
        "agent_memory_recall_tool": "brain_agent_memory_recall",
        "agent_memory_clear_tool": "brain_agent_memory_clear",
        "agent_memory_dataset": "agent_memory",
        "resolved_agent_memory_dataset": agent_memory_dataset_for_user(settings, user_id=active_user_id),
    }
