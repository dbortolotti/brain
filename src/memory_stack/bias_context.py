from __future__ import annotations

from typing import Any

from memory_stack.context_records import (
    forget_context_record,
    list_context_records,
    remember_context_record,
)
from memory_stack.cfg import Settings


def list_bias_context(settings: Settings, *, user_id: str | None = None) -> list[dict[str, Any]]:
    return list_context_records(settings, kind="bias", user_id=user_id)


def remember_bias_context(
    settings: Settings,
    *,
    statement: str,
    scope: str = "response_style",
    source: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    return remember_context_record(
        settings,
        kind="bias",
        statement=statement,
        scope=scope,
        source=source,
        user_id=user_id,
    )


def forget_bias_context(
    settings: Settings,
    *,
    context_id: str,
    user_id: str | None = None,
) -> dict[str, Any]:
    return forget_context_record(
        settings,
        kind="bias",
        context_id=context_id,
        user_id=user_id,
    )
