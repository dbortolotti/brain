from __future__ import annotations

from dataclasses import dataclass, replace
import re
import unicodedata
from typing import Any

from .media import (
    external_rating_facts,
    external_rating_tiebreak,
    is_media_type,
    is_restaurant_type,
    metadata_search_text,
    normalize_restaurant_genres,
    normalize_restaurant_metadata,
)


@dataclass(frozen=True)
class RankingWeights:
    preference: float = 1.4
    context: float = 0.5
    recommended_by_match: float = 0.6
    recommended_by_other: float = 0.25
    recommended_by_miss_penalty: float = 0.5
    saved: float = 0.15
    tried: float = 0.1
    dislike_penalty: float = 1.5
    attribute_match_cap: float = 1.5
    attribute_uncertainty_width_penalty: float = 0.5
    cuisine_match_cap: float = 1.2
    chosen_feedback: float = 0.15
    rejected_feedback: float = 0.1
    decision_feedback_cap: float = 0.45

    @classmethod
    def from_mapping(cls, values: dict[str, Any] | None = None) -> "RankingWeights":
        weights = cls()
        if not values:
            return weights
        allowed = cls.__dataclass_fields__
        updates = {
            key: float(value)
            for key, value in values.items()
            if key in allowed and value is not None
        }
        return replace(weights, **updates)


DEFAULT_WEIGHTS = RankingWeights()


def retrieve_candidates(
    store: Any,
    intent: dict[str, Any],
    extracted_entities: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    extracted_entities = extracted_entities or []

    if extracted_entities:
        option_names = [
            item.get("canonical_name") or item.get("name") or str(item)
            for item in extracted_entities
        ]
        matched = store.match_entities_by_names(option_names)
        return {
            "candidates": filter_by_type(matched["matched"], intent.get("entity_type")),
            "unmatched_options": matched["unmatched"],
            "option_matches": matched.get("matches", []),
            "needs_confirmation": matched.get("needs_confirmation", []),
            "constrained_to_options": True,
        }

    typed = filter_by_type(store.list_entities(), intent.get("entity_type"))
    searched = apply_search_text(typed, intent.get("search_text", ""))
    return {
        "candidates": searched,
        "unmatched_options": [],
        "option_matches": [],
        "needs_confirmation": [],
        "constrained_to_options": False,
    }


def rank_candidates(
    candidates: list[dict[str, Any]],
    intent: dict[str, Any],
    *,
    decision_feedback: dict[str, dict[str, Any]] | None = None,
    weights: RankingWeights | None = None,
) -> list[dict[str, Any]]:
    avoid_below = (intent.get("filters") or {}).get("min_rating")
    recommended_by = (intent.get("filters") or {}).get("recommended_by")
    cuisines = (intent.get("filters") or {}).get("cuisine") or []
    required = intent.get("attributes") or []
    context = intent.get("context") or {}
    search_text = intent.get("search_text") or ""
    decision_feedback = decision_feedback or {}
    weights = weights or DEFAULT_WEIGHTS

    results = []
    for entity in candidates:
        facts = score_entity(
            entity,
            required=required,
            context=context,
            avoid_below=avoid_below,
            recommended_by=recommended_by,
            cuisines=cuisines,
            search_text=search_text,
            decision_feedback=decision_feedback.get(entity.get("id"), {}),
            weights=weights,
        )
        if not facts["excluded"]:
            results.append({"entity": entity, "score": facts["total"], "facts": facts})

    return sorted(
        results,
        key=lambda result: (
            result["score"],
            result["facts"].get("external_rating_tiebreak", 0.0),
        ),
        reverse=True,
    )


def score_entity(
    entity: dict[str, Any],
    *,
    required: list[str],
    context: dict[str, Any],
    avoid_below: float | None,
    recommended_by: str | None,
    search_text: str,
    cuisines: list[str] | None = None,
    decision_feedback: dict[str, Any] | None = None,
    weights: RankingWeights | None = None,
) -> dict[str, Any]:
    weights = weights or DEFAULT_WEIGHTS
    decision_feedback = decision_feedback or {}
    facts: dict[str, Any] = {
        "preference": 0.0,
        "attribute_match": 0.0,
        "attribute_match_raw": 0.0,
        "attribute_uncertainty_penalty": 0.0,
        "cuisine_match": 0.0,
        "cuisine_match_raw": 0.0,
        "context_match": 0.0,
        "search_match": 0.0,
        "provenance": 0.0,
        "familiarity": 0.0,
        "decision_feedback": 0.0,
        "external_rating_tiebreak": 0.0,
        "penalties": 0.0,
        "matched_attributes": [],
        "negative_signals": [],
        "signal_facts": [],
        "excluded": False,
        "total": 0.0,
    }
    matched_recommended_by = False
    latest_rating_seen = False

    for signal in entity.get("signals") or []:
        signal_type = signal.get("type")
        value = signal.get("value")

        if signal_type == "avoid":
            facts["excluded"] = True
            facts["negative_signals"].append(str(value) if value is not True else "avoid")

        if signal_type == "rating" and not latest_rating_seen:
            try:
                rating = float(value)
            except (TypeError, ValueError):
                rating = None
            if rating is not None:
                latest_rating_seen = True
                facts["preference"] = rating_preference(rating)
                facts["signal_facts"].append(f"rating {rating:g}/10")
                if avoid_below and rating < avoid_below:
                    facts["excluded"] = True
                    facts["negative_signals"].append(f"rating below {avoid_below:g}")

        if signal_type in {"dislike", "disliked", "not_my_style", "bad_fit", "rejected_option"}:
            facts["penalties"] -= weights.dislike_penalty
            facts["negative_signals"].append(str(value))

        if signal_type == "recommended_by":
            matches_requested_person = bool(
                recommended_by and normalize(value) == normalize(recommended_by)
            )
            matched_recommended_by = matched_recommended_by or matches_requested_person
            facts["provenance"] += (
                weights.recommended_by_match
                if matches_requested_person
                else weights.recommended_by_other
            )
            facts["signal_facts"].append(f"recommended by {value}")

        if signal_type == "saved":
            facts["familiarity"] += weights.saved
            facts["signal_facts"].append("saved")

        if signal_type in {"wanted_to_try", "wanted_to_watch", "wanted_to_listen"}:
            facts["familiarity"] += weights.saved
            facts["signal_facts"].append(signal_type.replace("_", " "))

        if signal_type in {"tried", "watched", "listened"}:
            facts["familiarity"] += weights.tried
            fact = (
                "watched before"
                if signal_type == "watched" or is_media_type(entity.get("type"))
                else "listened before"
                if signal_type == "listened"
                else "tried before"
            )
            facts["signal_facts"].append(fact)

    if recommended_by and not matched_recommended_by:
        facts["provenance"] -= weights.recommended_by_miss_penalty
        facts["negative_signals"].append(f"not recommended by {recommended_by}")

    attribute_match_raw = 0.0
    for attr in required:
        value = float((entity.get("attributes") or {}).get(attr) or 0)
        if value > 0:
            adjusted = interval_adjusted_attribute_value(entity, attr, value, weights)
            attribute_match_raw += adjusted
            facts["attribute_uncertainty_penalty"] += value - adjusted
            facts["matched_attributes"].append(
                format_attribute_fact(entity, attr, value)
            )
    facts["attribute_match_raw"] = round(attribute_match_raw, 4)
    facts["attribute_match"] = min(attribute_match_raw, weights.attribute_match_cap)
    if attribute_match_raw > facts["attribute_match"]:
        facts["negative_signals"].append(
            f"attribute match capped at {weights.attribute_match_cap:g}"
        )

    cuisine_match_raw = 0.0
    cuisines = normalize_restaurant_genres(cuisines or [])
    if cuisines and is_restaurant_type(entity.get("type")):
        metadata_cuisine = (
            normalize_restaurant_metadata(entity.get("metadata") or {}).get("cuisine")
            or {}
        )
        for cuisine in cuisines:
            detail = metadata_cuisine.get(cuisine)
            value = cuisine_detail_value(detail)
            if value <= 0:
                continue
            adjusted = interval_adjusted_detail_value(detail, value, weights)
            cuisine_match_raw += adjusted
            facts["attribute_uncertainty_penalty"] += value - adjusted
            facts["matched_attributes"].append(
                format_detail_fact(cuisine, detail, value, prefix="cuisine ")
            )
    facts["cuisine_match_raw"] = round(cuisine_match_raw, 4)
    facts["cuisine_match"] = min(cuisine_match_raw, weights.cuisine_match_cap)
    if cuisine_match_raw > facts["cuisine_match"]:
        facts["negative_signals"].append(
            f"cuisine match capped at {weights.cuisine_match_cap:g}"
        )

    for key, wanted in context.items():
        value = float((entity.get("attributes") or {}).get(key) or 0)
        if wanted is True and value > 0:
            adjusted = interval_adjusted_attribute_value(entity, key, value, weights)
            facts["attribute_uncertainty_penalty"] += value - adjusted
            facts["context_match"] += adjusted * weights.context
            facts["matched_attributes"].append(
                format_attribute_fact(entity, key, value, prefix="context ")
            )

    facts["search_match"] = score_text_match(entity, search_text)
    if facts["search_match"] > 0:
        facts["signal_facts"].append(f"matched memory text: {facts['search_match']:.2f}")

    rating_facts = external_rating_facts(entity.get("metadata") or {})
    facts["signal_facts"].extend(rating_facts)
    facts["external_rating_tiebreak"] = external_rating_tiebreak(
        entity.get("metadata") or {}
    )

    chosen = float(decision_feedback.get("chosen", 0) or 0)
    rejected = float(decision_feedback.get("rejected", 0) or 0)
    chosen_boost = min(chosen * weights.chosen_feedback, weights.decision_feedback_cap)
    rejected_penalty = min(
        rejected * weights.rejected_feedback,
        weights.decision_feedback_cap,
    )
    facts["decision_feedback"] = chosen_boost - rejected_penalty
    if chosen > 0:
        facts["signal_facts"].append(f"chosen previously {chosen:g} time(s)")
    if rejected > 0:
        facts["negative_signals"].append(
            f"ranked highly but not chosen {rejected:g} time(s)"
        )

    facts["total"] = round(
        facts["preference"] * weights.preference
        + facts["attribute_match"]
        + facts["cuisine_match"]
        + facts["context_match"]
        + facts["search_match"]
        + facts["provenance"]
        + facts["familiarity"]
        + facts["decision_feedback"]
        + facts["penalties"],
        2,
    )
    return facts


def build_grounding(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": result["entity"]["id"],
            "name": result["entity"]["canonical_name"],
            "type": result["entity"]["type"],
            "score": result["score"],
            "matched_attributes": result["facts"]["matched_attributes"],
            "attribute_intervals_iqr": result["entity"].get("attribute_intervals_iqr") or {},
            "attribute_details": result["entity"].get("attribute_details") or {},
            "signal_facts": result["facts"]["signal_facts"],
            "negative_signals": result["facts"]["negative_signals"],
            "memory_status": memory_status(result["entity"]),
            "metadata": result["entity"].get("metadata") or {},
        }
        for result in results[:5]
    ]


def memory_status(entity: dict[str, Any]) -> dict[str, Any]:
    rating = None
    tried = False
    recommended_by = []
    saved = False
    wanted = False

    for signal in entity.get("signals") or []:
        signal_type = signal.get("type")
        value = signal.get("value")
        if signal_type == "rating":
            try:
                rating = max(rating or 0.0, float(value))
            except (TypeError, ValueError):
                pass
        if signal_type == "tried":
            tried = True
        if signal_type == "recommended_by":
            recommended_by.append(value)
        if signal_type == "saved":
            saved = True
        if signal_type in {"wanted_to_try", "wanted_to_watch", "wanted_to_listen"}:
            wanted = True

    metadata = entity.get("metadata") or {}
    watched = bool(metadata.get("watched")) if is_media_type(entity.get("type")) else False
    tried = tried or watched or rating is not None

    status = "want_to_watch" if is_media_type(entity.get("type")) else "want_to_try"
    if tried:
        status = "watched" if is_media_type(entity.get("type")) else "tried"
    if rating is not None and rating >= 7:
        status = "liked"
    if rating is not None and rating <= 4:
        status = "disliked"

    return {
        "status": status,
        "rating": rating,
        "tried_or_watched": tried,
        "wanted": wanted,
        "saved": saved,
        "recommended_by": recommended_by,
    }


def filter_by_type(entities: list[dict[str, Any]], entity_type: str | None) -> list[dict[str, Any]]:
    if not entity_type:
        return entities
    return [entity for entity in entities if entity["type"] == entity_type]


def apply_search_text(entities: list[dict[str, Any]], search_text: str) -> list[dict[str, Any]]:
    if not tokenize(search_text):
        return entities

    matches = [entity for entity in entities if score_text_match(entity, search_text) > 0]
    return matches or entities


def score_text_match(entity: dict[str, Any], search_text: str) -> float:
    tokens = tokenize(search_text)
    if not tokens:
        return 0.0

    attributes = " ".join(
        key
        for key, value in (entity.get("attributes") or {}).items()
        if float(value) > 0.25
    )
    signals = " ".join(
        f"{signal.get('type')} {signal.get('value')} {signal.get('provenance') or ''}"
        for signal in entity.get("signals") or []
    )
    haystack = normalize(
        " ".join(
            str(part)
            for part in [
                entity.get("canonical_name"),
                entity.get("source_text"),
                entity.get("notes"),
                metadata_search_text(entity.get("metadata") or {}),
                attributes,
                signals,
            ]
            if part
        )
    )
    haystack_terms = expanded_terms(haystack)
    matched = [
        token
        for token in tokens
        if token_variants(token) & haystack_terms or token in haystack
    ]
    return len(matched) / len(tokens)


def tokenize(value: str) -> list[str]:
    return [
        token
        for token in normalize(value).split()
        if len(token) > 2 and token not in STOP_WORDS
    ]


def normalize(value: Any) -> str:
    folded = unicodedata.normalize("NFKD", str(value or "").lower()).encode(
        "ascii",
        "ignore",
    ).decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", folded).strip()


def expanded_terms(value: str) -> set[str]:
    terms: set[str] = set()
    for token in tokenize(value):
        terms.update(token_variants(token))
    return terms


def token_variants(token: str) -> set[str]:
    variants = {token, collapse_repeated_letters(token)}
    if token.endswith("y") and len(token) > 3:
        variants.add(f"{token[:-1]}i")
    if token.endswith("ia") and len(token) > 4:
        variants.add(token[:-1])
    if token.endswith("ian") and len(token) > 5:
        variants.add(token[:-2])
    if token.endswith("ianate") and len(token) > 8:
        variants.add(token[:-3])
        variants.add(token[:-5])
    for suffix in ("ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) > len(suffix) + 3:
            variants.add(token[: -len(suffix)])
    return {variant for variant in variants if len(variant) > 2}


def collapse_repeated_letters(token: str) -> str:
    return re.sub(r"([a-z])\1+", r"\1", token)


def interval_adjusted_attribute_value(
    entity: dict[str, Any],
    key: str,
    value: float,
    weights: RankingWeights,
) -> float:
    interval = (entity.get("attribute_intervals_iqr") or {}).get(key) or {
        "lower": value,
        "upper": value,
    }
    lower = float(interval.get("lower", value))
    upper = float(interval.get("upper", value))
    width = max(0.0, min(1.0, upper) - max(0.0, lower))
    return max(0.0, value - (width * weights.attribute_uncertainty_width_penalty))


def cuisine_detail_value(detail: Any) -> float:
    if isinstance(detail, dict):
        detail = detail.get("value", 0)
    try:
        return max(0.0, min(1.0, float(detail or 0)))
    except (TypeError, ValueError):
        return 0.0


def interval_adjusted_detail_value(
    detail: Any,
    value: float,
    weights: RankingWeights,
) -> float:
    interval = detail.get("interval_iqr") if isinstance(detail, dict) else None
    if not isinstance(interval, dict):
        interval = {"lower": value, "upper": value}
    lower = float(interval.get("lower", value))
    upper = float(interval.get("upper", value))
    width = max(0.0, min(1.0, upper) - max(0.0, lower))
    return max(0.0, value - (width * weights.attribute_uncertainty_width_penalty))


def format_detail_fact(
    key: str,
    detail: Any,
    value: float,
    *,
    prefix: str = "",
) -> str:
    interval = detail.get("interval_iqr") if isinstance(detail, dict) else None
    if not isinstance(interval, dict):
        interval = {"lower": value, "upper": value}
    lower = float(interval.get("lower", value))
    upper = float(interval.get("upper", value))
    return f"{prefix}{key}: {value:.2f} (IQR {lower:.2f}-{upper:.2f})"


def format_attribute_fact(
    entity: dict[str, Any],
    key: str,
    value: float,
    *,
    prefix: str = "",
) -> str:
    interval = (entity.get("attribute_intervals_iqr") or {}).get(key) or {
        "lower": value,
        "upper": value,
    }
    lower = float(interval.get("lower", value))
    upper = float(interval.get("upper", value))
    return f"{prefix}{key}: {value:.2f} (IQR {lower:.2f}-{upper:.2f})"


def rating_preference(rating: float) -> float:
    # Preserves old 1-5 behavior after migration:
    # 2/4/6/8/10 map to -1/-0.5/0/0.5/1.
    return max(-1.0, min(1.0, (rating - 6) / 4))


STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "what",
    "which",
    "thing",
    "things",
    "place",
    "places",
    "something",
}
