from typing import Any

from memory_stack.brain_store import normalize_user_id
from memory_stack.bias_context import list_bias_context
from memory_stack.cfg import Settings
from memory_stack.profile_context import list_profile_context


def brain_session_payload(settings: Settings, *, user_id: str | None = None) -> dict[str, Any]:
    active_user_id = normalize_user_id(user_id or settings.brain_user_id)
    profile_context_records = list_profile_context(settings, user_id=active_user_id)
    bias_context_records = list_bias_context(settings, user_id=active_user_id)
    return {
        "user_id": active_user_id,
        "profile_name": settings.brain_owner_name,
        "profile_full_name": settings.brain_owner_full_name,
        "profile_context": [dict(record) for record in profile_context_records],
        "profile_context_records": profile_context_records,
        "bias_context": [dict(record) for record in bias_context_records],
        "bias_context_records": bias_context_records,
        "memory_tool": "brain_remember",
        "recall_tool": "brain_recall",
        "profile_context_remember_tool": "brain_profile_context_remember",
        "profile_context_list_tool": "brain_profile_context_list",
        "profile_context_forget_tool": "brain_profile_context_forget",
        "bias_context_remember_tool": "brain_bias_context_remember",
        "bias_context_list_tool": "brain_bias_context_list",
        "bias_context_forget_tool": "brain_bias_context_forget",
        "bias_prompt": "brain_bias_protocol",
    }
