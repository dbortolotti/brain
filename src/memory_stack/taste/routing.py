from __future__ import annotations

import re
from typing import Any

from memory_stack.llm.client import build_llm_client
from memory_stack.taste.schema import ENTITY_TYPES


WANTED_RE = re.compile(
    r"\b(?:(?:i|daniele)\s+)?(?:want|wants|would like|would love)\s+to\s+"
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
TASTE_HINT_TRAILING_COMMAND_RE = re.compile(
    r"^\s*(?:save|store|remember|record|add)\s+(?P<body>.+?)\s+"
    r"(?:to|in|as)\s+(?:my\s+)?(?:taste|palate)"
    r"(?:\s+(?:memory|note|record))?\s*$",
    re.IGNORECASE,
)
RESTAURANT_PHRASES = {
    "wine bar",
    "cocktail bar",
    "food fayre",
    "food hall",
}
RESTAURANT_TERMS = {
    "restaurant",
    "bar",
    "cafe",
    "café",
    "bistro",
    "brasserie",
    "grill",
    "rot",
    "food",
    "diner",
    "dining",
    "izakaya",
    "osteria",
    "pizzeria",
    "pub",
    "ramen",
    "sushi",
    "tavern",
    "trattoria",
}
WINE_PHRASES = {
    "gran reserva",
    "premier cru",
    "grand cru",
}
WINE_TERMS = {
    "barbaresco",
    "barolo",
    "bordeaux",
    "brunello",
    "burgundy",
    "cabernet",
    "champagne",
    "chardonnay",
    "chianti",
    "chateau",
    "château",
    "domaine",
    "gaja",
    "malbec",
    "merlot",
    "musar",
    "nebbiolo",
    "pinot",
    "reserva",
    "riesling",
    "rioja",
    "sancerre",
    "sangiovese",
    "sauvignon",
    "shiraz",
    "syrah",
    "tondonia",
    "wine",
}
PALATE_WEB_SEARCH_TOOL = {
    "type": "web_search",
    "user_location": {
        "type": "approximate",
        "country": "GB",
        "city": "London",
        "region": "London",
        "timezone": "Europe/London",
    },
}


def taste_domain_router(text: str, *, explicit: bool = False) -> dict[str, Any]:
    stripped = text.strip()
    lower = stripped.casefold()
    hinted, routed_text = taste_hint_body(stripped)
    explicit_command = explicit_taste_command(stripped)
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
        "explicit_taste_command": explicit_command,
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
    trailing = TASTE_HINT_TRAILING_COMMAND_RE.match(text)
    if trailing:
        return True, trailing.group("body").strip()
    return bool(TASTE_HINT_RE.search(text)), text


def explicit_taste_command(text: str) -> bool:
    return any(
        pattern.match(text)
        for pattern in (
            TASTE_HINT_PREFIX_RE,
            TASTE_HINT_COMMAND_RE,
            TASTE_HINT_TRAILING_COMMAND_RE,
        )
    )


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
    explicit_palate = explicit or bool(route.get("explicit_taste_command"))
    if not explicit_palate and float(route.get("confidence") or 0) >= 0.70:
        return route
    if not explicit_palate and not getattr(settings, "brain_taste_llm_routing_enabled", False):
        route["llm_classification_status"] = "disabled"
        return route
    active_llm_client = llm_client or (build_llm_client(settings) if settings is not None else None)
    if active_llm_client is None:
        route["llm_classification_status"] = "skipped"
        message = "LLM taste classification unavailable."
        route["ambiguity_reasons"].append(message)
        if explicit_palate:
            raise RuntimeError(
                "Explicit Palate categorization requires server-side LLM extraction; "
                f"{message}"
            )
        return route
    try:
        llm_kwargs: dict[str, Any] = {
            "model": getattr(settings, "brain_taste_llm_model", None),
            "reasoning_effort": getattr(settings, "brain_taste_llm_reasoning_effort", None),
            "temperature": 0,
            "schema_name": "brain_palate_memory_extraction" if explicit_palate else "brain_taste_routing",
        }
        if explicit_palate:
            llm_kwargs.update(
                tools=[PALATE_WEB_SEARCH_TOOL],
                tool_choice="auto",
                include=["web_search_call.action.sources"],
            )
        llm_route = normalize_llm_route(
            active_llm_client.complete_json(
                palate_memory_extraction_prompt(text, {}) if explicit_palate else taste_classification_prompt(text),
                taste_classification_schema(),
                **llm_kwargs,
            )
        )
    except Exception as exc:
        route["llm_classification_status"] = "failed"
        message = f"LLM taste classification failed: {exc}"
        route["ambiguity_reasons"].append(message)
        if explicit_palate:
            raise RuntimeError(
                "Explicit Palate categorization requires server-side LLM extraction; "
                f"{message}"
            ) from exc
        return route
    llm_route["classification_source"] = "llm_explicit_palate" if explicit_palate else "llm"
    llm_route["llm_classification_status"] = "success"
    if explicit_palate and llm_route.get("taste_intent") == "remember" and llm_route.get("domain") in {
        "taste",
        "ambiguous",
    }:
        return llm_route
    if explicit_palate:
        raise RuntimeError(
            "Explicit Palate categorization requires a remember/taste LLM extraction."
        )
    if float(llm_route.get("confidence") or 0) > float(route.get("confidence") or 0):
        return llm_route
    route["llm_classification_status"] = "success"
    return route


def classify_palate_memory_route(
    text: str,
    *,
    context: dict[str, Any] | None = None,
    settings: Any = None,
    llm_client: Any = None,
) -> dict[str, Any]:
    deterministic = taste_domain_router(text)
    deterministic["classification_source"] = "deterministic"
    deterministic["llm_classification_status"] = "not_available"
    active_llm_client = llm_client or (build_llm_client(settings) if settings is not None else None)
    if active_llm_client is None:
        raise RuntimeError(
            "Explicit Palate categorization requires server-side LLM extraction; "
            "LLM taste classification unavailable."
        )
    try:
        llm_route = normalize_llm_route(
            active_llm_client.complete_json(
                palate_memory_extraction_prompt(text, context or {}),
                taste_classification_schema(),
                model=getattr(settings, "brain_taste_llm_model", None),
                reasoning_effort=getattr(settings, "brain_taste_llm_reasoning_effort", None),
                temperature=0,
                schema_name="brain_palate_memory_extraction",
                tools=[PALATE_WEB_SEARCH_TOOL],
                tool_choice="auto",
                include=["web_search_call.action.sources"],
            )
        )
        llm_route["classification_source"] = "llm_palate_context"
        llm_route["llm_classification_status"] = "success"
        if llm_route.get("taste_intent") == "remember" and llm_route.get("domain") in {
            "taste",
            "ambiguous",
        }:
            return llm_route
        raise RuntimeError(
            "Explicit Palate categorization requires a remember/taste LLM extraction."
        )
    except Exception as exc:
        deterministic["llm_classification_status"] = "failed"
        deterministic.setdefault("ambiguity_reasons", []).append(
            f"LLM palate extraction failed: {exc}"
        )
        raise RuntimeError(
            "Explicit Palate categorization requires server-side LLM extraction; "
            f"LLM palate extraction failed: {exc}"
        ) from exc

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


def palate_memory_extraction_prompt(text: str, context: dict[str, Any]) -> str:
    context_lines = [f"{key}: {value}" for key, value in sorted(context.items())]
    return "\n".join(
        [
            "Extract a Brain Palate memory from this user note.",
            "Use Brain Palate for taste, restaurants, food/drink, wine, music, films, series, cigars, and experiences.",
            "Prefer the LLM's semantic reading over brittle phrasing, but do not invent item names.",
            "If the note is a food place or restaurant wishlist, use entity_type_hint=restaurant and wanted=true.",
            "Return a remember/taste or remember/ambiguous route. Use ambiguous when confirmation is needed.",
            f"Allowed entity types: {', '.join(ENTITY_TYPES)}.",
            "Context:",
            "\n".join(context_lines) if context_lines else "{}",
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
    if any_token(lower, {"cigar", "habanos", "robusto"}):
        return "cigar"
    if any_token(lower, {"album", "song", "track", "jazz"}):
        return "music"

    wine_term_score = phrase_score(lower, WINE_PHRASES) + token_score(lower, WINE_TERMS)
    has_vintage = re.search(r"\b(19|20)\d{2}\b", item) is not None
    wine_score = wine_term_score + (1 if has_vintage else 0)
    restaurant_score = phrase_score(lower, RESTAURANT_PHRASES) + token_score(
        lower,
        RESTAURANT_TERMS,
    )

    if wine_term_score and wine_score >= restaurant_score:
        return "wine"
    if restaurant_score:
        return "restaurant"
    if has_vintage:
        return "wine"
    return None


def entity_type_from_context(context: dict[str, Any]) -> str | None:
    text = re.sub(r"[_-]+", " ", " ".join(str(value) for value in context.values()).casefold())
    if phrase_score(text, RESTAURANT_PHRASES) or token_score(text, RESTAURANT_TERMS):
        return "restaurant"
    return mentioned_entity_type(text)


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
    text = re.split(r"\s+[-–—]\s+specifically\b", text, maxsplit=1, flags=re.IGNORECASE)[0]
    text = re.split(
        r"\s+and\s+(?:loved|liked|disliked|hated|rate|rated|would|will)\b",
        text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return text.strip().strip("\"'“”‘’").rstrip(".")


def phrase_score(lower_text: str, phrases: set[str]) -> int:
    return sum(1 for phrase in phrases if re.search(rf"\b{re.escape(phrase)}\b", lower_text))


def token_score(lower_text: str, terms: set[str]) -> int:
    return sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\b", lower_text))


def any_token(lower_text: str, terms: set[str]) -> bool:
    return token_score(lower_text, terms) > 0


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
