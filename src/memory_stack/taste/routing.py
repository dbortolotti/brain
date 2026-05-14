from __future__ import annotations

import re
from typing import Any

from memory_stack.taste.schema import ENTITY_TYPES


WANTED_RE = re.compile(
    r"\b(?:i|daniele)\s+(?:want|wants|would like|would love)\s+to\s+"
    r"(?P<verb>try|watch|listen to)\s+(?P<item>[^.]+)",
    re.IGNORECASE,
)
RECOMMENDED_RE = re.compile(
    r"^(?P<person>[A-Z][A-Za-z0-9&' -]+?)\s+"
    r"(?:recommended|suggested|told me to try|said to try)\s+(?P<item>[^.]+)",
    re.IGNORECASE,
)
RATED_RE = re.compile(
    r"(?P<item>.+?)\s+(?:was\s+)?(?:rated|is)\s+(?P<rating>\d+(?:\.\d+)?)\s*/\s*10",
    re.IGNORECASE,
)
WATCHED_RATED_RE = re.compile(
    r"\bi\s+watched\s+(?P<item>.+?)\s+and\s+rate(?:d)?\s+(?:it\s+)?"
    r"(?P<rating>\d+(?:\.\d+)?)\s*/\s*10",
    re.IGNORECASE,
)
WATCHED_RE = re.compile(r"\bi\s+watched\s+(?P<item>[^.]+)", re.IGNORECASE)
LISTENED_RE = re.compile(r"\bi\s+listened\s+to\s+(?P<item>[^.]+)", re.IGNORECASE)
SMOKED_RE = re.compile(r"\bi\s+smoked\s+(?P<item>[^.]+)", re.IGNORECASE)
DISLIKED_RE = re.compile(
    r"\bi\s+(?:disliked|did\s+not\s+like|don't\s+like)\s+(?P<item>[^.]+)",
    re.IGNORECASE,
)
AVOID_RE = re.compile(r"\bavoid\s+(?P<item>[^.]+)", re.IGNORECASE)
TASTE_HINT_RE = re.compile(r"\b(?:taste|palate)\b", re.IGNORECASE)
TASTE_HINT_PREFIX_RE = re.compile(
    r"^\s*(?:brain\s+)?(?:taste|palate)(?:\s+(?:memory|note|record))?\s*[:\-–—]\s*(?P<body>.+)$",
    re.IGNORECASE,
)
TASTE_HINT_COMMAND_RE = re.compile(
    r"^\s*(?:save|store|remember|record|add)\s+(?:this\s+)?"
    r"(?:to|in|as)?\s*(?:my\s+)?(?:taste|palate)"
    r"(?:\s+(?:memory|note|record))?\s*[:\-–—]?\s*(?P<body>.+)$",
    re.IGNORECASE,
)


def taste_domain_router(text: str, *, explicit: bool = False) -> dict[str, Any]:
    stripped = text.strip()
    lower = stripped.casefold()
    hinted, routed_text = taste_hint_body(stripped)
    routed_lower = routed_text.casefold()
    result = {
        "domain": "general",
        "taste_intent": "none",
        "entity_type_hint": None,
        "confidence": 0.0,
        "requires_enrichment": False,
        "requires_confirmation": False,
        "ambiguity_reasons": [],
        "extracted": {},
    }
    if not stripped:
        return result

    if explicit:
        result.update(
            domain="taste",
            taste_intent="remember",
            confidence=0.98,
            requires_enrichment=True,
        )
        return result

    wanted = WANTED_RE.search(routed_text)
    if wanted:
        verb = wanted.group("verb").casefold()
        item = clean_item(wanted.group("item"))
        entity_type = type_for_item(item, verb=verb)
        result.update(
            domain="taste",
            taste_intent="remember",
            entity_type_hint=entity_type,
            confidence=0.96 if entity_type else 0.72,
            requires_enrichment=True,
            extracted={"wanted": True, "item": item},
        )
        return apply_taste_hint(result, hinted)

    recommended = RECOMMENDED_RE.search(routed_text)
    if recommended:
        item = clean_item(recommended.group("item"))
        entity_type = type_for_item(item)
        result.update(
            domain="taste",
            taste_intent="remember",
            entity_type_hint=entity_type,
            confidence=0.96 if entity_type else 0.74,
            requires_enrichment=True,
            extracted={
                "recommended_by": recommended.group("person").strip(),
                "item": item,
            },
        )
        return apply_taste_hint(result, hinted)

    watched_rated = WATCHED_RATED_RE.search(routed_text)
    if watched_rated:
        item = clean_item(watched_rated.group("item"))
        result.update(
            domain="taste",
            taste_intent="remember",
            entity_type_hint=type_for_item(item, verb="watch"),
            confidence=0.96,
            requires_enrichment=True,
            extracted={
                "item": item,
                "watched": True,
                "rating": float(watched_rated.group("rating")),
            },
        )
        return apply_taste_hint(result, hinted)

    rated = RATED_RE.search(routed_text)
    if rated and "rate limit" not in lower:
        item = clean_item(rated.group("item"))
        entity_type = type_for_item(item)
        result.update(
            domain="taste",
            taste_intent="remember",
            entity_type_hint=entity_type,
            confidence=0.95 if entity_type else 0.73,
            requires_enrichment=True,
            extracted={"item": item, "rating": float(rated.group("rating"))},
        )
        return apply_taste_hint(result, hinted)

    watched = WATCHED_RE.search(routed_text)
    if watched:
        item = clean_item(watched.group("item"))
        result.update(
            domain="taste",
            taste_intent="remember",
            entity_type_hint=type_for_item(item, verb="watch"),
            confidence=0.95,
            requires_enrichment=True,
            extracted={"item": item, "watched": True},
        )
        return apply_taste_hint(result, hinted)

    listened = LISTENED_RE.search(routed_text)
    if listened:
        item = clean_item(listened.group("item"))
        result.update(
            domain="taste",
            taste_intent="remember",
            entity_type_hint="music",
            confidence=0.95,
            requires_enrichment=True,
            extracted={"item": item, "listened": True},
        )
        return apply_taste_hint(result, hinted)

    smoked = SMOKED_RE.search(routed_text)
    if smoked:
        item = clean_item(smoked.group("item"))
        result.update(
            domain="taste",
            taste_intent="remember",
            entity_type_hint="cigar",
            confidence=0.95,
            requires_enrichment=True,
            extracted={
                "item": item,
                "tried": True,
                "disliked": any(word in lower for word in ("disliked", "did not like", "don't like")),
            },
        )
        return apply_taste_hint(result, hinted)

    disliked = DISLIKED_RE.search(routed_text)
    if disliked:
        item = clean_item(disliked.group("item"))
        entity_type = type_for_item(item)
        result.update(
            domain="taste",
            taste_intent="remember",
            entity_type_hint=entity_type,
            confidence=0.92 if entity_type else 0.74,
            requires_enrichment=True,
            requires_confirmation=entity_type is None,
            extracted={"item": item, "disliked": True},
        )
        return apply_taste_hint(result, hinted)

    avoid = AVOID_RE.search(routed_text)
    if avoid:
        item = clean_item(avoid.group("item"))
        entity_type = type_for_item(item)
        result.update(
            domain="taste",
            taste_intent="remember",
            entity_type_hint=entity_type,
            confidence=0.91 if entity_type else 0.73,
            requires_enrichment=True,
            requires_confirmation=entity_type is None,
            extracted={"item": item, "avoid": True},
        )
        return apply_taste_hint(result, hinted)

    if any(word in routed_lower for word in ("which wine", "what wine", "which restaurant", "what restaurant")):
        result.update(
            domain="taste",
            taste_intent="query",
            entity_type_hint="wine" if "wine" in routed_lower else "restaurant",
            confidence=0.92,
            requires_enrichment=False,
        )
        return apply_taste_hint(result, hinted)

    if any(word in routed_lower for word in ("wine", "restaurant", "movie", "series", "cigar")):
        result.update(
            domain="ambiguous",
            taste_intent="query",
            entity_type_hint=mentioned_entity_type(routed_lower),
            confidence=0.72,
            requires_confirmation=True,
            ambiguity_reasons=["Taste keyword present without explicit taste action."],
        )

    if hinted and result["domain"] == "general":
        item = clean_item(routed_text)
        entity_type = type_for_item(item)
        if entity_type:
            result.update(
                domain="ambiguous",
                taste_intent="remember",
                entity_type_hint=entity_type,
                confidence=0.82,
                requires_enrichment=True,
                requires_confirmation=True,
                ambiguity_reasons=[
                    "Taste/palate keyword present without an explicit taste action."
                ],
                extracted={"item": item},
            )

    return apply_taste_hint(result, hinted)


def taste_hint_body(text: str) -> tuple[bool, str]:
    prefix = TASTE_HINT_PREFIX_RE.match(text)
    if prefix:
        return True, prefix.group("body").strip()
    command = TASTE_HINT_COMMAND_RE.match(text)
    if command:
        return True, command.group("body").strip()
    return bool(TASTE_HINT_RE.search(text)), text


def apply_taste_hint(route: dict[str, Any], hinted: bool) -> dict[str, Any]:
    if not hinted or route.get("domain") == "general":
        return route
    route["routing_hints"] = ["taste_keyword"]
    route["confidence"] = max(float(route.get("confidence") or 0), 0.86)
    if route.get("domain") == "ambiguous" or (
        route.get("taste_intent") == "remember" and route.get("entity_type_hint") is None
    ):
        route["requires_confirmation"] = True
        route.setdefault("ambiguity_reasons", []).append(
            "Taste/palate keyword present but item type is not certain."
        )
    return route


def classify_taste_route(
    text: str,
    *,
    settings: Any = None,
    llm_client: Any = None,
    explicit: bool = False,
) -> dict[str, Any]:
    route = taste_domain_router(text, explicit=explicit)
    route["classification_source"] = "deterministic"
    route["llm_classification_status"] = "not_needed"
    if explicit or float(route.get("confidence") or 0) >= 0.70:
        return route
    if not getattr(settings, "brain_taste_llm_routing_enabled", False):
        route["llm_classification_status"] = "disabled"
        return route
    if llm_client is None:
        route["llm_classification_status"] = "skipped"
        route["ambiguity_reasons"].append("LLM taste classification unavailable.")
        return route
    try:
        llm_route = normalize_llm_route(
            llm_client.complete_json(
                taste_classification_prompt(text),
                taste_classification_schema(),
                model=getattr(settings, "brain_taste_llm_model", None),
                reasoning_effort=getattr(settings, "brain_taste_llm_reasoning_effort", None),
                temperature=0,
            )
        )
    except Exception as exc:
        route["llm_classification_status"] = "failed"
        route["ambiguity_reasons"].append(f"LLM taste classification failed: {exc}")
        return route
    llm_route["classification_source"] = "llm"
    llm_route["llm_classification_status"] = "success"
    if float(llm_route.get("confidence") or 0) > float(route.get("confidence") or 0):
        return llm_route
    route["llm_classification_status"] = "success"
    return route


def normalize_llm_route(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("LLM classifier returned non-object JSON.")
    domain = payload.get("domain") if payload.get("domain") in {"general", "taste", "ambiguous"} else "general"
    taste_intent = (
        payload.get("taste_intent")
        if payload.get("taste_intent") in {"remember", "query", "none"}
        else "none"
    )
    entity_type = payload.get("entity_type_hint")
    if entity_type not in ENTITY_TYPES:
        entity_type = None
    try:
        confidence = max(0.0, min(1.0, float(payload.get("confidence") or 0)))
    except (TypeError, ValueError):
        confidence = 0.0
    extracted = payload.get("extracted") if isinstance(payload.get("extracted"), dict) else {}
    item = extracted.get("item") or extracted.get("canonical_name")
    normalized_extracted = {
        key: value
        for key, value in {
            "item": clean_item(str(item)) if item else None,
            "rating": safe_float(extracted.get("rating")),
            "wanted": bool(extracted.get("wanted")) if "wanted" in extracted else None,
            "tried": bool(extracted.get("tried")) if "tried" in extracted else None,
            "watched": bool(extracted.get("watched")) if "watched" in extracted else None,
            "listened": bool(extracted.get("listened")) if "listened" in extracted else None,
            "disliked": bool(extracted.get("disliked")) if "disliked" in extracted else None,
            "avoid": bool(extracted.get("avoid")) if "avoid" in extracted else None,
            "not_my_style": bool(extracted.get("not_my_style")) if "not_my_style" in extracted else None,
            "bad_fit": bool(extracted.get("bad_fit")) if "bad_fit" in extracted else None,
            "recommended_by": extracted.get("recommended_by"),
        }.items()
        if value is not None
    }
    if taste_intent == "remember" and domain == "taste" and not normalized_extracted.get("item"):
        domain = "ambiguous"
        confidence = min(confidence, 0.69)
    return {
        "domain": domain,
        "taste_intent": taste_intent,
        "entity_type_hint": entity_type,
        "confidence": confidence,
        "requires_enrichment": bool(payload.get("requires_enrichment", taste_intent == "remember")),
        "requires_confirmation": bool(payload.get("requires_confirmation", confidence < 0.95)),
        "ambiguity_reasons": [
            str(item)
            for item in (payload.get("ambiguity_reasons") or [])
            if str(item).strip()
        ],
        "extracted": normalized_extracted,
    }


def taste_classification_prompt(text: str) -> str:
    return "\n".join(
        [
            "Classify whether this message should be handled by Brain Taste.",
            "Brain Taste stores preferences, ratings, recommendations, wanted-to-try/watch/listen items, and ranks supplied taste options.",
            "Return only JSON matching the schema. Do not invent item names or attributes.",
            f"Allowed entity types: {', '.join(ENTITY_TYPES)}.",
            "Message:",
            text[:4000],
        ]
    )


def taste_classification_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["domain", "taste_intent", "confidence"],
        "properties": {
            "domain": {"type": "string", "enum": ["general", "taste", "ambiguous"]},
            "taste_intent": {"type": "string", "enum": ["remember", "query", "none"]},
            "entity_type_hint": {"type": ["string", "null"], "enum": [*ENTITY_TYPES, None]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "requires_enrichment": {"type": "boolean"},
            "requires_confirmation": {"type": "boolean"},
            "ambiguity_reasons": {"type": "array", "items": {"type": "string"}},
            "extracted": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "item": {"type": ["string", "null"]},
                    "canonical_name": {"type": ["string", "null"]},
                    "rating": {"type": ["number", "null"]},
                    "wanted": {"type": ["boolean", "null"]},
                    "tried": {"type": ["boolean", "null"]},
                    "watched": {"type": ["boolean", "null"]},
                    "listened": {"type": ["boolean", "null"]},
                    "disliked": {"type": ["boolean", "null"]},
                    "avoid": {"type": ["boolean", "null"]},
                    "not_my_style": {"type": ["boolean", "null"]},
                    "bad_fit": {"type": ["boolean", "null"]},
                    "recommended_by": {"type": ["string", "null"]},
                },
            },
        },
    }


def type_for_item(item: str, *, verb: str | None = None) -> str | None:
    lower = item.casefold()
    if verb == "watch":
        if lower in {"the bear"}:
            return "series"
        return "series" if any(word in lower for word in ("season", "series", "show")) else "movie"
    if verb == "listen to":
        return "music"
    if any(word in lower for word in ("restaurant", "bar", "cafe", "bistro", "grill", "rot")):
        return "restaurant"
    if any(word in lower for word in ("wine", "chateau", "barolo", "riesling", "cabernet")):
        return "wine"
    if re.search(r"\b(19|20)\d{2}\b", item):
        return "wine"
    if any(word in lower for word in ("cigar", "habanos", "robusto")):
        return "cigar"
    if any(word in lower for word in ("album", "song", "track", "jazz")):
        return "music"
    return None


def mentioned_entity_type(lower_text: str) -> str | None:
    matches = [
        kind
        for kind in ENTITY_TYPES
        if re.search(rf"\b{re.escape(kind)}s?\b", lower_text)
    ]
    if not matches:
        return None
    if "restaurant" in matches:
        return "restaurant"
    return matches[0]


def clean_item(value: str) -> str:
    text = value.strip().strip("\"'“”‘’").rstrip(".")
    text = re.split(
        r"\s+and\s+(?:loved|liked|disliked|hated|rate|rated|would|will)\b",
        text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return text.strip().strip("\"'“”‘’").rstrip(".")


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
