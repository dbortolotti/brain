from __future__ import annotations

from typing import Any

from memory_stack.cfg import Settings
from memory_stack.profile_context import list_profile_context


def brain_session_payload(settings: Settings) -> dict[str, Any]:
    session_id = settings.brain_agent_memory_session_id.strip()
    if not session_id:
        raise ValueError("BRAIN_AGENT_MEMORY_SESSION_ID must not be blank.")
    profile_context_records = list_profile_context(settings)
    return {
        "session_id": session_id,
        "profile_name": settings.brain_owner_name,
        "profile_full_name": settings.brain_owner_full_name,
        "profile_context": [str(record["statement"]) for record in profile_context_records],
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
        "resolved_agent_memory_dataset": settings.brain_cognee_agent_memory_dataset,
    }
