from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from memory_stack.cfg import Settings
from memory_stack.logging_utils import append_jsonl


def log_taste_route(text: str, route: dict[str, Any], settings: Settings) -> None:
    if not settings.brain_routing_log_enabled:
        return
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "input_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "route": route_name(route),
        "domain": route.get("domain"),
        "taste_intent": route.get("taste_intent"),
        "classification_source": route.get("classification_source"),
        "llm_classification_status": route.get("llm_classification_status"),
        "confidence": route.get("confidence"),
        "routing_hints": route.get("routing_hints") or [],
        "entity_type_hint": route.get("entity_type_hint"),
        "requires_enrichment": route.get("requires_enrichment"),
        "requires_confirmation": route.get("requires_confirmation"),
        "ambiguity_reasons": route.get("ambiguity_reasons") or [],
        "extracted_keys": sorted((route.get("extracted") or {}).keys()),
    }
    append_jsonl(
        settings.brain_routing_log_path,
        record,
        retention_days=settings.brain_routing_log_retention_days,
    )


def route_name(route: dict[str, Any]) -> str:
    domain = route.get("domain")
    intent = route.get("taste_intent")
    if domain in {"taste", "ambiguous"} and intent == "remember":
        return "palate_proposal" if route.get("requires_confirmation") else "palate_write_candidate"
    if domain in {"taste", "ambiguous"} and intent == "query":
        return "palate_query"
    return "brain_memory"
