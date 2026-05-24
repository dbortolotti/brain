from __future__ import annotations

import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy import and_, insert, select, update

from memory_stack import brain_schema as schema
from memory_stack.brain_store import (
    BrainStore,
    now_utc,
    row_dict,
    stable_id,
)
from memory_stack.cfg import Settings
from memory_stack.taste.schema import SIGNAL_TYPES


class TasteProposalStore:
    """Brain-owned SQL store for pending palate proposal workflow state."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.brain_store = BrainStore(settings)
        self.user_id = self.brain_store.user_id
        self.engine = self.brain_store.engine

    def create_proposal(
        self,
        *,
        original_text: str,
        proposal: dict[str, Any],
        warnings: list[Any] | None = None,
        source_metadata: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
    ) -> dict[str, Any]:
        proposal_id = stable_id("tprop", self.user_id, original_text, now_utc().isoformat())
        expires = expires_at or now_utc() + timedelta(hours=self.settings.brain_taste_proposal_expiry_hours)
        proposal = {
            "proposal_id": proposal_id,
            "original_text": original_text,
            **proposal,
        }
        with self.engine.begin() as conn:
            conn.execute(
                insert(schema.taste_proposals).values(
                    id=proposal_id,
                    user_id=self.user_id,
                    original_text=original_text,
                    proposal_json=proposal,
                    warnings_json=warnings or [],
                    source_metadata_json=source_metadata or {},
                    status="pending",
                    expires_at=expires,
                )
            )
            row = conn.execute(
                select(schema.taste_proposals).where(schema.taste_proposals.c.id == proposal_id)
                .where(schema.taste_proposals.c.user_id == self.user_id)
            ).one()
        return row_dict(row)

    def get_proposal(self, proposal_id: str) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.taste_proposals).where(schema.taste_proposals.c.id == proposal_id)
                .where(schema.taste_proposals.c.user_id == self.user_id)
            ).first()
        return row_dict(row) if row is not None else None

    def update_proposal(
        self,
        proposal_id: str,
        *,
        status: str | None = None,
        proposal: dict[str, Any] | None = None,
        warnings: list[Any] | None = None,
        correction_text: str | None = None,
    ) -> dict[str, Any] | None:
        current = self.get_proposal(proposal_id)
        if current is None:
            return None
        values: dict[str, Any] = {}
        if status is not None:
            values["status"] = status
        if proposal is not None:
            values["proposal_json"] = proposal
        if warnings is not None:
            values["warnings_json"] = warnings
        if correction_text is not None:
            values["last_correction_text"] = correction_text
            values["last_corrected_at"] = now_utc()
            values["correction_count"] = int(current.get("correction_count") or 0) + 1
        if not values:
            return current
        with self.engine.begin() as conn:
            conn.execute(
                update(schema.taste_proposals)
                .where(and_(schema.taste_proposals.c.id == proposal_id, schema.taste_proposals.c.user_id == self.user_id))
                .values(**values)
            )
            row = conn.execute(
                select(schema.taste_proposals).where(schema.taste_proposals.c.id == proposal_id)
                .where(schema.taste_proposals.c.user_id == self.user_id)
            ).one()
        return row_dict(row)


def normalize(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def best_entity_name_match(
    name: str,
    candidates: list[dict[str, Any]],
) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    for candidate in candidates:
        confidence = name_match_confidence(name, candidate["canonical_name"])
        if best is None or confidence > best["confidence"]:
            best = {"entity": candidate, "confidence": confidence}
    return best


def name_match_confidence(left: str, right: str) -> float:
    left_norm = normalize_name_for_match(left)
    right_norm = normalize_name_for_match(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm == right_norm:
        return 1.0
    if left_norm in right_norm or right_norm in left_norm:
        return 1.0

    left_tokens = left_norm.split()
    right_tokens = right_norm.split()
    overlap_tokens = set(left_tokens) & set(right_tokens)
    token_score = token_overlap_score(left_tokens, right_tokens)
    sequence_score = SequenceMatcher(None, left_norm, right_norm).ratio()
    if overlap_tokens and overlap_tokens <= GENERIC_WINE_NAME_TOKENS:
        return min(max(token_score, sequence_score), 0.49)
    return max(token_score, sequence_score)


def normalize_name_for_match(value: str) -> str:
    tokens = [
        normalize_wine_token(token)
        for token in normalize(value).split()
        if token not in NAME_MATCH_STOP_WORDS and not is_vintage_token(token)
    ]
    return " ".join(token for token in tokens if token)


def normalize_wine_token(token: str) -> str:
    aliases = {
        "cab": "cabernet",
        "cabs": "cabernet",
        "sauv": "sauvignon",
        "sauvignon": "sauvignon",
        "syra": "syrah",
        "est": "estate",
        "ch": "chateau",
    }
    return aliases.get(token, token)


def is_vintage_token(token: str) -> bool:
    return bool(re.fullmatch(r"(19|20)\d{2}", token))


def token_overlap_score(left_tokens: list[str], right_tokens: list[str]) -> float:
    left = set(left_tokens)
    right = set(right_tokens)
    if not left or not right:
        return 0.0
    overlap = len(left & right)
    precision = overlap / len(left)
    recall = overlap / len(right)
    if precision == 0 or recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def unique_match_details(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    unique = []
    for match in matches:
        key = (match["input"], match["matched_id"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(match)
    return unique


NAME_MATCH_STOP_WORDS = {
    "the",
    "a",
    "an",
    "and",
    "of",
    "de",
    "di",
    "da",
    "la",
    "le",
    "il",
    "lo",
    "s",
}


GENERIC_WINE_NAME_TOKENS = {
    "barolo",
    "cabernet",
    "chardonnay",
    "grenache",
    "malbec",
    "merlot",
    "nebbiolo",
    "pinot",
    "riesling",
    "sangiovese",
    "sauvignon",
    "syrah",
    "tempranillo",
    "zinfandel",
}


def query_is_similar(current: str, historical: str) -> bool:
    current_tokens = query_tokens(current)
    historical_tokens = query_tokens(historical)
    if not current_tokens or not historical_tokens:
        return True
    return bool(current_tokens & historical_tokens)


def query_tokens(value: str) -> set[str]:
    stop_words = {
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
    return {
        token
        for token in normalize(value).split()
        if len(token) > 2 and token not in stop_words
    }


def clamp01(value: Any) -> float:
    return max(0.0, min(1.0, float(value)))


def validate_signal(signal_type: str, value: Any) -> None:
    if signal_type not in SIGNAL_TYPES:
        raise ValueError(f"signal_type must be one of: {', '.join(SIGNAL_TYPES)}")
    if signal_type == "rating":
        try:
            rating = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("rating signal value must be numeric.") from exc
        if not 1 <= rating <= 10:
            raise ValueError("rating signal value must be between 1 and 10.")


def attribute_value(value: Any) -> Any:
    if isinstance(value, dict):
        return value.get("value", 0)
    return value


def normalize_interval_iqr(value: Any, interval: dict[str, Any] | None) -> dict[str, float]:
    point = clamp01(value)
    if not isinstance(interval, dict):
        return {"lower": point, "upper": point}
    lower = clamp01(interval.get("lower", interval.get("p25", interval.get("q1", point))))
    upper = clamp01(interval.get("upper", interval.get("p75", interval.get("q3", point))))
    if lower > upper:
        lower, upper = upper, lower
    return {"lower": min(lower, point), "upper": max(upper, point)}


def unique_by_id(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    unique = []
    for entity in entities:
        if entity["id"] in seen:
            continue
        seen.add(entity["id"])
        unique.append(entity)
    return unique
