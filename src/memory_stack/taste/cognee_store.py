from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, Field

from memory_stack.brain_store import normalize_name, now_utc, stable_id
from memory_stack.cognee_adapter import import_cognee, maybe_await, refresh_cognee_runtime, run_async
from memory_stack.cfg import Settings
from memory_stack.taste.store import (
    best_entity_name_match,
    query_is_similar,
    unique_by_id,
    unique_match_details,
    validate_signal,
)


PALATE_ITEM_TYPES = {"wine", "restaurant", "movie", "series", "music", "cigar", "experience"}


class PalateItemDataPoint(BaseModel):
    id: str
    brain_entity_id: str | None = None
    type: str
    canonical_name: str
    normalized_name: str
    source_text: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    enrichment_metadata: dict[str, Any] = Field(default_factory=dict)
    enrichment_status: str = "not_attempted"
    attributes: dict[str, float] = Field(default_factory=dict)
    attribute_intervals_95: dict[str, dict[str, float]] = Field(default_factory=dict)
    signals: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "current"
    version: int = 1


class PalateDecisionDataPoint(BaseModel):
    id: str
    query: str
    context: dict[str, Any] = Field(default_factory=dict)
    options: list[Any] = Field(default_factory=list)
    ranked: list[Any] = Field(default_factory=list)
    chosen_taste_item_id: str | None = None
    status: str = "current"
    version: int = 1


PalatePoint = PalateItemDataPoint | PalateDecisionDataPoint


class PalateCogneeAdapter(Protocol):
    dataset_name: str

    async def upsert_points(self, points: list[PalatePoint]) -> None:
        ...

    async def get_point(self, point_id: str) -> dict[str, Any] | None:
        ...

    async def list_points(self, point_kind: str | None = None) -> list[dict[str, Any]]:
        ...


@dataclass
class InMemoryPalateCogneeAdapter:
    dataset_name: str
    points: dict[str, dict[str, Any]] = field(default_factory=dict)

    async def upsert_points(self, points: list[PalatePoint]) -> None:
        for point in points:
            self.points[point.id] = point.model_dump(mode="json")

    async def get_point(self, point_id: str) -> dict[str, Any] | None:
        point = self.points.get(point_id)
        return dict(point) if point is not None else None

    async def list_points(self, point_kind: str | None = None) -> list[dict[str, Any]]:
        points = [dict(point) for point in self.points.values()]
        if point_kind == "item":
            return [point for point in points if point.get("type") in PALATE_ITEM_TYPES]
        if point_kind == "decision":
            return [point for point in points if "chosen_taste_item_id" in point]
        return points


class LivePalateCogneeAdapter:
    def __init__(self, dataset_name: str, settings: Settings) -> None:
        self.dataset_name = dataset_name
        self.settings = settings

    async def upsert_points(self, points: list[PalatePoint]) -> None:
        refresh_cognee_runtime(self.settings)
        import_cognee()
        refresh_cognee_runtime(self.settings, prepare_oauth=False)
        from cognee.infrastructure.engine import DataPoint  # type: ignore
        from cognee.tasks.storage import add_data_points  # type: ignore

        live_points = [_to_live_datapoint(DataPoint, point, self.dataset_name) for point in points]
        await maybe_await(add_data_points(live_points))

    async def get_point(self, point_id: str) -> dict[str, Any] | None:
        refresh_cognee_runtime(self.settings)
        from cognee.infrastructure.databases.graph import get_graph_engine  # type: ignore

        graph = await maybe_await(get_graph_engine())
        node = await maybe_await(graph.get_node(str(_uuid_for_external_id(point_id))))
        return _normalize_live_node(node, fallback_id=point_id)

    async def list_points(self, point_kind: str | None = None) -> list[dict[str, Any]]:
        refresh_cognee_runtime(self.settings)
        from cognee.infrastructure.databases.graph import get_graph_engine  # type: ignore

        graph = await maybe_await(get_graph_engine())
        where = "n.dataset_name = $dataset"
        if point_kind == "item":
            where += " AND n.point_kind = 'item' AND n.status <> 'deleted'"
        elif point_kind == "decision":
            where += " AND n.point_kind = 'decision' AND n.status <> 'deleted'"
        rows = await maybe_await(
            graph.query(
                f"""
                MATCH (n)
                WHERE {where}
                RETURN properties(n) AS properties
                ORDER BY n.canonical_name
                LIMIT $limit
                """,
                {"dataset": self.dataset_name, "limit": 1000},
            )
        )
        points = []
        for row in rows or []:
            properties = row.get("properties") if isinstance(row, dict) else None
            if not isinstance(properties, dict):
                continue
            point = _normalize_live_node(properties, fallback_id=str(properties.get("external_id")))
            if point is not None:
                points.append(point)
        return points


class CogneePalateStore:
    """Canonical approved palate store backed by Cognee custom DataPoints."""

    def __init__(self, settings: Settings, adapter: PalateCogneeAdapter | None = None) -> None:
        self.settings = settings
        self.adapter = adapter or LivePalateCogneeAdapter(settings.brain_cognee_palate_dataset, settings)

    def upsert_item(self, item: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        point = item_to_datapoint(item)
        existing = run_async(self.adapter.get_point(point.id))
        run_async(self.adapter.upsert_points([point]))
        stored = run_async(self.adapter.get_point(point.id)) or point.model_dump(mode="json")
        return hydrate_item(stored), existing is None

    def get_item(self, taste_item_id: str, *, include_deleted: bool = False) -> dict[str, Any] | None:
        point = run_async(self.adapter.get_point(taste_item_id))
        if point is None:
            return None
        if not include_deleted and point.get("status") == "deleted":
            return None
        return hydrate_item(point)

    def list_entities(self, *, include_deleted: bool = False) -> list[dict[str, Any]]:
        points = run_async(self.adapter.list_points("item"))
        if not include_deleted:
            points = [point for point in points if point.get("status") != "deleted"]
        return [hydrate_item(point) for point in points]

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
        item = self.get_item(taste_item_id)
        if item is None:
            raise ValueError(f"Taste item not found: {taste_item_id}")
        signal_id = signal_id or stable_id(
            "tsig",
            taste_item_id,
            signal_type,
            json.dumps(value, sort_keys=True, default=str),
            provenance_memory_id,
            provenance_entity_id,
            source,
        )
        signal = {
            "id": signal_id,
            "type": signal_type,
            "value": value,
            "provenance": source,
            "provenance_memory_id": provenance_memory_id,
            "provenance_entity_id": provenance_entity_id,
            "created_at": now_utc().isoformat(),
        }
        if not any(existing.get("id") == signal_id for existing in item.get("signals") or []):
            item["signals"] = [signal, *(item.get("signals") or [])]
            self.upsert_item(item)
        return signal

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
        point = PalateDecisionDataPoint(
            id=decision_id,
            query=query,
            context=context or {},
            options=options or [],
            ranked=ranked or [],
            chosen_taste_item_id=chosen_id,
        )
        run_async(self.adapter.upsert_points([point]))
        return decision_id

    def update_decision_choice(self, decision_id: str, chosen_taste_item_id: str) -> int:
        point = run_async(self.adapter.get_point(decision_id))
        if point is None:
            return 0
        decision = PalateDecisionDataPoint(
            id=decision_id,
            query=str(point.get("query") or ""),
            context=point.get("context") or {},
            options=point.get("options") or [],
            ranked=point.get("ranked") or [],
            chosen_taste_item_id=chosen_taste_item_id,
            status=point.get("status") or "current",
            version=int(point.get("version") or 1) + 1,
        )
        run_async(self.adapter.upsert_points([decision]))
        return 1

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
        decisions = run_async(self.adapter.list_points("decision"))
        decisions = sorted(decisions, key=lambda item: str(item.get("id")), reverse=True)[:limit]
        for decision in decisions:
            if not decision.get("chosen_taste_item_id"):
                continue
            if not query_is_similar(query, str(decision.get("query") or "")):
                continue
            chosen = decision.get("chosen_taste_item_id")
            if chosen in candidate_set:
                feedback[str(chosen)]["chosen"] += 1
            for item in (decision.get("ranked") or [])[:3]:
                entity_id = item.get("id") if isinstance(item, dict) else None
                if entity_id in candidate_set and entity_id != chosen:
                    feedback[entity_id]["rejected"] += 1
        return feedback

    def soft_delete_item(self, taste_item_id: str) -> bool:
        item = self.get_item(taste_item_id, include_deleted=True)
        if item is None:
            return False
        item["status"] = "deleted"
        self.upsert_item(item)
        return True

    def hard_delete_item(self, taste_item_id: str, *, confirm: bool = False) -> bool:
        if not confirm:
            raise ValueError("hard_delete_item requires confirm=True.")
        return self.soft_delete_item(taste_item_id)


def item_to_datapoint(item: dict[str, Any]) -> PalateItemDataPoint:
    item_type = str(item["type"])
    canonical_name = str(item["canonical_name"]).strip()
    normalized = item.get("normalized_name") or normalize_name(canonical_name)
    item_id = item.get("id") or stable_id("taste", item_type, normalized)
    return PalateItemDataPoint(
        id=item_id,
        brain_entity_id=item.get("brain_entity_id"),
        type=item_type,
        canonical_name=canonical_name,
        normalized_name=normalized,
        source_text=item.get("source_text"),
        notes=item.get("notes"),
        metadata=item.get("metadata_json") or item.get("metadata") or {},
        enrichment_metadata=item.get("enrichment_metadata_json") or item.get("enrichment_metadata") or {},
        enrichment_status=item.get("enrichment_status") or "not_attempted",
        attributes={key: float(value) for key, value in (item.get("attributes") or {}).items()},
        attribute_intervals_95=item.get("attribute_intervals_95") or {},
        signals=item.get("signals") or [],
        status=item.get("status") or "current",
        version=int(item.get("version") or 1),
    )


def hydrate_item(point: dict[str, Any]) -> dict[str, Any]:
    item = dict(point)
    item["metadata"] = item.get("metadata") or item.get("metadata_json") or {}
    item["metadata_json"] = item["metadata"]
    item["enrichment_metadata"] = item.get("enrichment_metadata") or item.get("enrichment_metadata_json") or {}
    item["enrichment_metadata_json"] = item["enrichment_metadata"]
    item["attributes"] = item.get("attributes") or {}
    item["attribute_intervals_95"] = item.get("attribute_intervals_95") or {}
    item["attribute_details"] = {
        key: {
            "value": value,
            "interval_95": item["attribute_intervals_95"].get(key, {"lower": value, "upper": value}),
        }
        for key, value in item["attributes"].items()
    }
    item["signals"] = item.get("signals") or []
    return item


def _uuid_for_external_id(external_id: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"brain-palate:{external_id}")


def _to_live_datapoint(datapoint_base: Any, point: PalatePoint, dataset_name: str) -> Any:
    fields = _live_fields(point, dataset_name)
    class_name = point.__class__.__name__
    live_class = type(
        class_name,
        (datapoint_base,),
        {
            "__annotations__": {key: type(value) if value is not None else Any for key, value in fields.items()},
            "metadata": {"index_fields": ["canonical_name", "notes", "attributes_summary", "signals_summary"]},
        },
    )
    return live_class(**fields)


def _live_fields(point: PalatePoint, dataset_name: str) -> dict[str, Any]:
    payload = point.model_dump(mode="json")
    external_id = point.id
    point_kind = "decision" if isinstance(point, PalateDecisionDataPoint) else "item"
    for key in ("metadata", "enrichment_metadata", "attributes", "attribute_intervals_95", "signals", "context", "options", "ranked"):
        if key in payload:
            payload[f"{key}_json"] = json.dumps(payload.pop(key), sort_keys=True, default=str)
    payload["id"] = _uuid_for_external_id(external_id)
    payload["external_id"] = external_id
    payload["point_kind"] = point_kind
    payload["dataset_name"] = dataset_name
    payload["palate_type"] = payload.get("type")
    payload["source_node_set"] = ["palate", f"dataset:{dataset_name}", f"palate:{point_kind}"]
    payload["attributes_summary"] = " ".join((point.model_dump(mode="json").get("attributes") or {}).keys())
    payload["signals_summary"] = " ".join(signal.get("type", "") for signal in point.model_dump(mode="json").get("signals", []))
    return payload


def _normalize_live_node(node: Any, *, fallback_id: str) -> dict[str, Any] | None:
    if node is None:
        return None
    if isinstance(node, dict):
        payload = dict(node)
    elif hasattr(node, "model_dump"):
        payload = node.model_dump(mode="json")
    else:
        payload = {
            key: getattr(node, key)
            for key in dir(node)
            if not key.startswith("_")
        }
    payload["id"] = str(payload.get("external_id") or fallback_id)
    payload["type"] = payload.get("palate_type") or payload.get("type")
    for key, default in (
        ("metadata", {}),
        ("enrichment_metadata", {}),
        ("attributes", {}),
        ("attribute_intervals_95", {}),
        ("signals", []),
        ("context", {}),
        ("options", []),
        ("ranked", []),
    ):
        source_key = f"{key}_json"
        if source_key not in payload:
            continue
        try:
            payload[key] = json.loads(payload[source_key])
        except (TypeError, json.JSONDecodeError):
            payload[key] = default
    return payload
