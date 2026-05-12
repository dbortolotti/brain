from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy import and_, delete, insert, select, update
from sqlalchemy.exc import IntegrityError

from memory_stack import brain_schema as schema
from memory_stack.brain_store import (
    BrainStore,
    normalize_name,
    now_utc,
    row_dict,
    stable_id,
)
from memory_stack.config import Settings
from memory_stack.taste.schema import SIGNAL_TYPES, attribute_keys_for_type


class TasteStore:
    """Brain-owned structured store for taste records."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.brain_store = BrainStore(settings)
        self.engine = self.brain_store.engine

    def upsert_item(self, item: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        item_type = str(item["type"])
        canonical_name = str(item["canonical_name"]).strip()
        normalized = normalize_name(canonical_name)
        item_id = item.get("id") or stable_id("taste", item_type, normalized)
        payload = {
            "id": item_id,
            "brain_entity_id": item["brain_entity_id"],
            "type": item_type,
            "canonical_name": canonical_name,
            "normalized_name": normalized,
            "source_text": item.get("source_text"),
            "notes": item.get("notes"),
            "metadata_json": item.get("metadata_json") or item.get("metadata") or {},
            "enrichment_metadata_json": item.get("enrichment_metadata_json")
            or item.get("enrichment_metadata")
            or {},
            "enrichment_status": item.get("enrichment_status") or "not_attempted",
            "status": item.get("status") or "current",
        }
        with self.engine.begin() as conn:
            try:
                conn.execute(insert(schema.taste_items).values(**payload))
                created = True
            except IntegrityError:
                created = False
                conn.execute(
                    update(schema.taste_items)
                    .where(schema.taste_items.c.id == item_id)
                    .values(
                        brain_entity_id=payload["brain_entity_id"],
                        type=payload["type"],
                        canonical_name=payload["canonical_name"],
                        normalized_name=payload["normalized_name"],
                        source_text=payload["source_text"],
                        notes=payload["notes"],
                        metadata_json=payload["metadata_json"],
                        enrichment_metadata_json=payload["enrichment_metadata_json"],
                        enrichment_status=payload["enrichment_status"],
                        status=payload["status"],
                        updated_at=now_utc(),
                    )
                )
            row = conn.execute(
                select(schema.taste_items).where(schema.taste_items.c.id == item_id)
            ).one()

        for key, value in (item.get("attributes") or {}).items():
            if key not in attribute_keys_for_type(item_type):
                continue
            interval = (item.get("attribute_intervals_95") or {}).get(key)
            normalized_interval = normalize_interval_95(attribute_value(value), interval)
            self.set_attribute(
                item_id,
                key,
                attribute_value(value),
                normalized_interval["lower"],
                normalized_interval["upper"],
            )

        for signal in item.get("signals") or []:
            self.add_signal(
                item_id,
                str(signal["type"]),
                signal.get("value"),
                provenance_memory_id=signal.get("provenance_memory_id"),
                provenance_entity_id=signal.get("provenance_entity_id"),
                source=signal.get("source") or signal.get("provenance"),
            )

        return self._hydrate_item(row_dict(row)), created

    def set_attribute(
        self,
        taste_item_id: str,
        key: str,
        value: float,
        lower_95: float | None = None,
        upper_95: float | None = None,
    ) -> None:
        point = clamp01(value)
        interval = normalize_interval_95(
            point,
            {"lower": point if lower_95 is None else lower_95, "upper": point if upper_95 is None else upper_95},
        )
        payload = {
            "taste_item_id": taste_item_id,
            "key": key,
            "value": point,
            "lower_95": interval["lower"],
            "upper_95": interval["upper"],
        }
        with self.engine.begin() as conn:
            try:
                conn.execute(insert(schema.taste_attributes).values(**payload))
            except IntegrityError:
                conn.execute(
                    update(schema.taste_attributes)
                    .where(
                        and_(
                            schema.taste_attributes.c.taste_item_id == taste_item_id,
                            schema.taste_attributes.c.key == key,
                        )
                    )
                    .values(
                        value=payload["value"],
                        lower_95=payload["lower_95"],
                        upper_95=payload["upper_95"],
                        updated_at=now_utc(),
                    )
                )

    def add_signal(
        self,
        taste_item_id: str,
        signal_type: str,
        value: Any,
        *,
        provenance_memory_id: str | None = None,
        provenance_entity_id: str | None = None,
        source: str | None = None,
        signal_id: str | None = None,
    ) -> dict[str, Any]:
        validate_signal(signal_type, value)
        signal_id = signal_id or stable_id(
            "tsig",
            taste_item_id,
            signal_type,
            json.dumps(value, sort_keys=True, default=str),
            provenance_memory_id,
            provenance_entity_id,
            source,
        )
        payload = {
            "id": signal_id,
            "taste_item_id": taste_item_id,
            "signal_type": signal_type,
            "value_json": value,
            "provenance_memory_id": provenance_memory_id,
            "provenance_entity_id": provenance_entity_id,
            "source": source,
        }
        with self.engine.begin() as conn:
            try:
                conn.execute(insert(schema.taste_signals).values(**payload))
            except IntegrityError:
                pass
            row = conn.execute(
                select(schema.taste_signals).where(schema.taste_signals.c.id == signal_id)
            ).one()
        return row_dict(row)

    def get_item(self, taste_item_id: str, *, include_deleted: bool = False) -> dict[str, Any] | None:
        filters = [schema.taste_items.c.id == taste_item_id]
        if not include_deleted:
            filters.append(schema.taste_items.c.status != "deleted")
        with self.engine.begin() as conn:
            row = conn.execute(select(schema.taste_items).where(and_(*filters))).first()
        return self._hydrate_item(row_dict(row)) if row is not None else None

    def get_item_by_brain_entity(self, brain_entity_id: str) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.taste_items).where(
                    and_(
                        schema.taste_items.c.brain_entity_id == brain_entity_id,
                        schema.taste_items.c.status != "deleted",
                    )
                )
            ).first()
        return self._hydrate_item(row_dict(row)) if row is not None else None

    def list_entities(self, *, include_deleted: bool = False) -> list[dict[str, Any]]:
        filters = []
        if not include_deleted:
            filters.append(schema.taste_items.c.status != "deleted")
        where_clause = and_(*filters) if filters else True
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(schema.taste_items)
                .where(where_clause)
                .order_by(schema.taste_items.c.canonical_name)
            ).fetchall()
        return [self._hydrate_item(row_dict(row)) for row in rows]

    def match_entities_by_names(self, names: list[str]) -> dict[str, list[Any]]:
        all_entities = self.list_entities()
        matched = []
        unmatched = []
        match_details = []
        needs_confirmation = []

        for name in names:
            match = best_entity_name_match(name, all_entities)
            if match and match["confidence"] >= 0.5:
                detail = {
                    "input": name,
                    "matched_id": match["entity"]["id"],
                    "matched_name": match["entity"]["canonical_name"],
                    "confidence": round(match["confidence"], 3),
                    "needs_confirmation": match["confidence"] < 0.85,
                }
                match_details.append(detail)
                if detail["needs_confirmation"]:
                    needs_confirmation.append(detail)
                else:
                    matched.append(match["entity"])
            else:
                unmatched.append(name)

        return {
            "matched": unique_by_id(matched),
            "unmatched": unmatched,
            "matches": unique_match_details(match_details),
            "needs_confirmation": unique_match_details(needs_confirmation),
        }

    def log_decision(
        self,
        query: str,
        context: dict[str, Any] | None,
        options: list[Any] | None,
        ranked: list[Any] | None,
        chosen_entity_id: str | None = None,
        chosen_taste_item_id: str | None = None,
    ) -> str:
        chosen_id = chosen_taste_item_id or chosen_entity_id
        decision_id = stable_id("tdec", query, json.dumps(options or [], default=str), now_utc().isoformat())
        with self.engine.begin() as conn:
            conn.execute(
                insert(schema.taste_decisions).values(
                    id=decision_id,
                    query=query,
                    context_json=context or {},
                    options_json=options or [],
                    ranked_json=ranked or [],
                    chosen_taste_item_id=chosen_id,
                )
            )
        return decision_id

    def update_decision_choice(self, decision_id: str, chosen_taste_item_id: str) -> int:
        with self.engine.begin() as conn:
            result = conn.execute(
                update(schema.taste_decisions)
                .where(schema.taste_decisions.c.id == decision_id)
                .values(chosen_taste_item_id=chosen_taste_item_id)
            )
        return result.rowcount

    def decision_feedback(
        self,
        query: str,
        candidate_ids: list[str],
        *,
        limit: int = 100,
    ) -> dict[str, dict[str, int]]:
        candidate_set = set(candidate_ids)
        feedback = {entity_id: {"chosen": 0, "rejected": 0} for entity_id in candidate_ids}
        if not candidate_set:
            return feedback

        with self.engine.begin() as conn:
            rows = conn.execute(
                select(
                    schema.taste_decisions.c.query,
                    schema.taste_decisions.c.ranked_json,
                    schema.taste_decisions.c.chosen_taste_item_id,
                )
                .where(schema.taste_decisions.c.chosen_taste_item_id.is_not(None))
                .order_by(schema.taste_decisions.c.created_at.desc())
                .limit(limit)
            ).fetchall()

        for row in rows:
            payload = row._mapping
            if not query_is_similar(query, str(payload["query"])):
                continue
            chosen = payload["chosen_taste_item_id"]
            if chosen in candidate_set:
                feedback[str(chosen)]["chosen"] += 1
            ranked = payload["ranked_json"] or []
            for item in ranked[:3]:
                entity_id = item.get("id") if isinstance(item, dict) else None
                if entity_id in candidate_set and entity_id != chosen:
                    feedback[entity_id]["rejected"] += 1
        return feedback

    def create_proposal(
        self,
        *,
        original_text: str,
        proposal: dict[str, Any],
        warnings: list[Any] | None = None,
        source_metadata: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
    ) -> dict[str, Any]:
        proposal_id = stable_id("tprop", original_text, now_utc().isoformat())
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
            ).one()
        return row_dict(row)

    def get_proposal(self, proposal_id: str) -> dict[str, Any] | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(schema.taste_proposals).where(schema.taste_proposals.c.id == proposal_id)
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
                .where(schema.taste_proposals.c.id == proposal_id)
                .values(**values)
            )
            row = conn.execute(
                select(schema.taste_proposals).where(schema.taste_proposals.c.id == proposal_id)
            ).one()
        return row_dict(row)

    def soft_delete_item(self, taste_item_id: str) -> bool:
        with self.engine.begin() as conn:
            result = conn.execute(
                update(schema.taste_items)
                .where(schema.taste_items.c.id == taste_item_id)
                .values(status="deleted", updated_at=now_utc())
            )
        return result.rowcount > 0

    def hard_delete_item(self, taste_item_id: str, *, confirm: bool = False) -> bool:
        if not confirm:
            raise ValueError("hard_delete_item requires confirm=True.")
        with self.engine.begin() as conn:
            conn.execute(
                delete(schema.taste_attributes).where(
                    schema.taste_attributes.c.taste_item_id == taste_item_id
                )
            )
            conn.execute(
                delete(schema.taste_signals).where(
                    schema.taste_signals.c.taste_item_id == taste_item_id
                )
            )
            result = conn.execute(
                delete(schema.taste_items).where(schema.taste_items.c.id == taste_item_id)
            )
        return result.rowcount > 0

    def _hydrate_item(self, item: dict[str, Any]) -> dict[str, Any]:
        item_id = item["id"]
        with self.engine.begin() as conn:
            attrs = conn.execute(
                select(schema.taste_attributes).where(
                    schema.taste_attributes.c.taste_item_id == item_id
                )
            ).fetchall()
            signals = conn.execute(
                select(schema.taste_signals)
                .where(schema.taste_signals.c.taste_item_id == item_id)
                .order_by(schema.taste_signals.c.created_at.desc())
            ).fetchall()

        item["metadata"] = item.get("metadata_json") or {}
        item["enrichment_metadata"] = item.get("enrichment_metadata_json") or {}
        item["attributes"] = {row._mapping["key"]: row._mapping["value"] for row in attrs}
        item["attribute_intervals_95"] = {
            row._mapping["key"]: {
                "lower": row._mapping["lower_95"],
                "upper": row._mapping["upper_95"],
            }
            for row in attrs
        }
        item["attribute_details"] = {
            row._mapping["key"]: {
                "value": row._mapping["value"],
                "interval_95": {
                    "lower": row._mapping["lower_95"],
                    "upper": row._mapping["upper_95"],
                },
            }
            for row in attrs
        }
        item["signals"] = [
            {
                "id": row._mapping["id"],
                "type": row._mapping["signal_type"],
                "value": row._mapping["value_json"],
                "provenance": row._mapping["source"],
                "provenance_memory_id": row._mapping["provenance_memory_id"],
                "provenance_entity_id": row._mapping["provenance_entity_id"],
                "created_at": row._mapping["created_at"],
            }
            for row in signals
        ]
        return item


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


def normalize_interval_95(value: Any, interval: dict[str, Any] | None) -> dict[str, float]:
    point = clamp01(value)
    if not isinstance(interval, dict):
        return {"lower": point, "upper": point}
    lower = clamp01(interval.get("lower", interval.get("lower_95", point)))
    upper = clamp01(interval.get("upper", interval.get("upper_95", point)))
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
