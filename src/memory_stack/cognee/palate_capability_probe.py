from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, Field

from memory_stack.cognee_adapter import (
    CogneeUnavailableError,
    import_cognee,
    maybe_await,
    refresh_cognee_runtime,
    recall_text,
)
from memory_stack.cfg import Settings, load_settings
from memory_stack.taste.enrichment import TasteEnrichmentService
from memory_stack.taste.ranking import rank_candidates


ProbeRecommendation = Literal[
    "cognee_authoritative",
    "cognee_plus_sqlite_decision_log",
    "cognee_plus_sqlite_read_model",
    "sqlite_authoritative_required",
]

PROBE_QUERY = "suggest an oaky wine I said I want to try"
SAFE_DATASET_PREFIX = "palate_probe_"
PRODUCTION_DATASET_NAMES = {
    "memory",
    "sources",
    "brain_memory",
    "brain_sources",
    "brain_taste",
    "brain_palate",
    "brain_current_memory",
    "brain_admin_memory",
}


class PalateProbeDataPoint(BaseModel):
    id: str
    type: str
    canonical_name: str
    notes: str = ""
    attributes: dict[str, float] = Field(default_factory=dict)
    signals: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "current"
    metadata: dict[str, Any] = Field(default_factory=dict)
    version: int = 1

    def update_version(self) -> None:
        self.version += 1


class WineDataPoint(PalateProbeDataPoint):
    type: str = "wine"
    producer: str | None = None
    region: str | None = None
    country: str | None = None
    vintage: int | None = None


class RestaurantDataPoint(PalateProbeDataPoint):
    type: str = "restaurant"
    city: str | None = None
    cuisine: dict[str, Any] = Field(default_factory=dict)


class PalateSignalDataPoint(BaseModel):
    id: str
    taste_item_id: str
    signal_type: str
    value: Any
    provenance: str = "probe"
    status: str = "current"
    metadata: dict[str, Any] = Field(default_factory=dict)
    version: int = 1

    def update_version(self) -> None:
        self.version += 1


class PalateDecisionDataPoint(BaseModel):
    id: str
    query: str
    candidate_item_ids: list[str]
    chosen_item_id: str | None = None
    rejected_item_ids: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    status: str = "current"
    metadata: dict[str, Any] = Field(default_factory=dict)
    version: int = 1

    def update_version(self) -> None:
        self.version += 1


ProbePoint = WineDataPoint | RestaurantDataPoint | PalateSignalDataPoint | PalateDecisionDataPoint


class PalateProbeAdapter(Protocol):
    dataset_name: str

    async def upsert_points(self, points: list[ProbePoint]) -> None:
        ...

    async def get_point(self, point_id: str) -> dict[str, Any] | None:
        ...

    async def search(self, query: str, *, top_k: int = 10) -> list[dict[str, Any]]:
        ...

    async def list_points(self, point_type: str | None = None) -> list[dict[str, Any]]:
        ...

    async def delete_point(self, point_id: str) -> None:
        ...


@dataclass
class InMemoryPalateProbeAdapter:
    dataset_name: str
    fail_writes: bool = False
    points: dict[str, dict[str, Any]] = field(default_factory=dict)

    async def upsert_points(self, points: list[ProbePoint]) -> None:
        if self.fail_writes:
            raise RuntimeError("simulated Cognee write failure")
        for point in points:
            self.points[point.id] = point.model_dump(mode="json")

    async def get_point(self, point_id: str) -> dict[str, Any] | None:
        point = self.points.get(point_id)
        return dict(point) if point is not None else None

    async def search(self, query: str, *, top_k: int = 10) -> list[dict[str, Any]]:
        query_terms = _tokens(query)
        scored: list[tuple[float, dict[str, Any]]] = []
        for point in self.points.values():
            if point.get("status") != "current":
                continue
            text = _point_search_text(point)
            terms = _tokens(text)
            score = len(query_terms & terms) / max(1, len(query_terms))
            if score > 0:
                scored.append((score, dict(point)))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [point for _score, point in scored[:top_k]]

    async def list_points(self, point_type: str | None = None) -> list[dict[str, Any]]:
        points = [dict(point) for point in self.points.values()]
        if point_type is not None:
            points = [point for point in points if point.get("type") == point_type]
        return points

    async def delete_point(self, point_id: str) -> None:
        if point_id in self.points:
            self.points[point_id]["status"] = "deleted"


class LiveCogneePalateProbeAdapter:
    """Best-effort live adapter for Cognee custom DataPoint capability checks."""

    def __init__(self, dataset_name: str, settings: Settings | None = None) -> None:
        self.dataset_name = dataset_name
        self.settings = settings or load_settings()
        self._written_ids: set[str] = set()

    async def upsert_points(self, points: list[ProbePoint]) -> None:
        refresh_cognee_runtime(self.settings)
        import_cognee()
        refresh_cognee_runtime(self.settings, prepare_oauth=False)
        from cognee.infrastructure.engine import DataPoint  # type: ignore
        from cognee.tasks.storage import add_data_points  # type: ignore

        live_points = [_to_live_datapoint(DataPoint, point, self.dataset_name) for point in points]
        await maybe_await(add_data_points(live_points))
        self._written_ids.update(point.id for point in points)

    async def get_point(self, point_id: str) -> dict[str, Any] | None:
        refresh_cognee_runtime(self.settings)
        from cognee.infrastructure.databases.graph import get_graph_engine  # type: ignore

        graph = await maybe_await(get_graph_engine())
        node = await maybe_await(graph.get_node(str(_uuid_for_external_id(point_id))))
        return _normalize_live_node(node, fallback_id=point_id)

    async def search(self, query: str, *, top_k: int = 10) -> list[dict[str, Any]]:
        graph_candidates = await self._graph_candidate_search(query, top_k=top_k)
        if graph_candidates:
            return graph_candidates

        raw = await recall_text(
            query=query,
            dataset=None,
            search_type="CHUNKS",
            top_k=top_k,
            node_name=[f"dataset:{self.dataset_name}", "palate_probe"],
            node_name_filter_operator="OR",
            settings=self.settings,
        )
        normalized = _normalize_search_results(raw)
        structured = []
        for result in normalized:
            point_id = result.get("id") or result.get("external_id")
            if point_id:
                point = await self.get_point(str(point_id))
                if point is not None:
                    structured.append(point)
        return structured or normalized

    async def _graph_candidate_search(self, query: str, *, top_k: int) -> list[dict[str, Any]]:
        del query
        refresh_cognee_runtime(self.settings)
        from cognee.infrastructure.databases.graph import get_graph_engine  # type: ignore

        graph = await maybe_await(get_graph_engine())
        rows = await maybe_await(
            graph.query(
                """
                MATCH (n)
                WHERE n.external_id IS NOT NULL
                  AND n.status = 'current'
                  AND n.palate_type IN ['wine', 'restaurant', 'music', 'cigar', 'experience', 'movie', 'series']
                RETURN properties(n) AS properties
                LIMIT $limit
                """,
                {"limit": top_k},
            )
        )
        candidates = []
        for row in rows or []:
            properties = row.get("properties") if isinstance(row, dict) else None
            normalized = _normalize_live_node(properties, fallback_id=str(properties.get("external_id"))) if isinstance(properties, dict) else None
            if normalized is not None:
                candidates.append(normalized)
        return candidates

    async def list_points(self, point_type: str | None = None) -> list[dict[str, Any]]:
        points = []
        for point_id in sorted(self._written_ids):
            point = await self.get_point(point_id)
            if point is None:
                continue
            if point_type is not None and point.get("type") != point_type:
                continue
            points.append(point)
        return points

    async def delete_point(self, point_id: str) -> None:
        point = await self.get_point(point_id)
        if point is None:
            return
        point["status"] = "deleted"
        replacement = _point_from_mapping(point)
        await self.upsert_points([replacement])


def build_probe_dataset_name(prefix: str = SAFE_DATASET_PREFIX) -> str:
    return f"{prefix}{int(time.time())}"


async def run_palate_cognee_capability_probe(
    adapter: PalateProbeAdapter | None = None,
    *,
    dataset_name: str | None = None,
    live: bool = False,
    include_enrichment: bool = False,
    allow_broader_web_search: bool = False,
    settings: Settings | None = None,
    config_env: str | None = None,
) -> dict[str, Any]:
    dataset = validate_probe_dataset_name(dataset_name or build_probe_dataset_name())
    active_settings = settings
    if active_settings is None and (adapter is None or include_enrichment):
        active_settings = load_settings(config_env=config_env)
    active_adapter = adapter or LiveCogneePalateProbeAdapter(dataset, settings=active_settings)
    fixtures = build_probe_fixtures()
    report: dict[str, Any] = {
        "dataset_name": active_adapter.dataset_name,
        "query": PROBE_QUERY,
        "live": live,
        "capabilities": {},
        "sqlite_required_for": [],
        "ranking_demo": {},
        "enrichment_demo": {},
        "errors": [],
    }

    try:
        if include_enrichment:
            if active_settings is None:
                active_settings = load_settings(config_env=config_env)
            enrichment = build_enriched_restaurant_probe_point(
                active_settings,
                allow_broader_web_search=allow_broader_web_search,
            )
            fixtures.append(enrichment["point"])
            report["enrichment_demo"] = enrichment["demo"]
        await active_adapter.upsert_points(fixtures)
    except Exception as exc:
        report["errors"].append({"stage": "initial_upsert", "error": str(exc)})
        report["capabilities"] = _all_capabilities(False)
        report["sqlite_required_for"] = ["canonical_palate_items", "failed_write_retry_log"]
        report["overall_recommendation"] = "sqlite_authoritative_required"
        return report

    report["capabilities"]["exact_lookup"] = await _check_exact_lookup(active_adapter, fixtures)
    report["capabilities"]["structured_readback"] = await _check_structured_readback(
        active_adapter,
        fixtures,
    )
    search_results = await _safe_search(active_adapter, report)
    report["capabilities"]["semantic_retrieval"] = _contains_point(
        search_results,
        "wine_known_oaky_rioja",
    )
    report["ranking_demo"] = build_ranking_demo(search_results)
    report["capabilities"]["type_filtering"] = report["ranking_demo"]["type_filtering_passed"]
    report["capabilities"]["signal_filtering"] = report["ranking_demo"]["signal_filtering_passed"]
    report["capabilities"]["update"] = await _check_update(active_adapter)
    report["capabilities"]["delete_currentness"] = await _check_delete_currentness(active_adapter)
    report["capabilities"]["decision_aggregation"] = await _check_decision_aggregation(
        active_adapter,
    )
    report["capabilities"]["failure_recovery"] = _check_failure_recovery()
    report["sqlite_required_for"] = sqlite_requirements(report["capabilities"])
    report["overall_recommendation"] = overall_recommendation(report["capabilities"])
    return report


def build_probe_fixtures() -> list[ProbePoint]:
    wines = [
        WineDataPoint(
            id="wine_chateau_musar_2016",
            canonical_name="Chateau Musar 2016",
            producer="Chateau Musar",
            region="Bekaa Valley",
            country="Lebanon",
            vintage=2016,
            notes="Lebanese red wine recommended by Sam.",
            attributes={"oak": 0.35, "body": 0.75, "classic": 0.8},
            signals=[
                {"type": "recommended_by", "value": "Sam", "provenance": "probe"},
                {"type": "wanted_to_try", "value": True, "provenance": "probe"},
            ],
            metadata={"index_fields": ["canonical_name", "notes", "attributes_summary"]},
        ),
        WineDataPoint(
            id="wine_known_oaky_rioja",
            canonical_name="Known Oaky Rioja",
            producer="Probe Producer",
            region="Rioja",
            country="Spain",
            vintage=2018,
            notes="A strongly oaky wine the user said they want to try.",
            attributes={"oak": 0.9, "body": 0.65, "classic": 0.55},
            signals=[
                {"type": "wanted_to_try", "value": True, "provenance": "probe"},
                {"type": "saved", "value": True, "provenance": "probe"},
            ],
            metadata={"index_fields": ["canonical_name", "notes", "attributes_summary"]},
        ),
        WineDataPoint(
            id="wine_avoided_napa_cab",
            canonical_name="Avoided Napa Cab",
            producer="Probe Producer",
            region="Napa",
            country="United States",
            vintage=2020,
            notes="A very oaky wine marked avoid.",
            attributes={"oak": 0.95, "body": 0.9},
            signals=[
                {"type": "wanted_to_try", "value": True, "provenance": "probe"},
                {"type": "avoid", "value": True, "provenance": "probe"},
            ],
            metadata={"index_fields": ["canonical_name", "notes", "attributes_summary"]},
        ),
    ]
    return [
        *wines,
        RestaurantDataPoint(
            id="restaurant_noble_rot",
            canonical_name="Noble Rot",
            city="London",
            notes="A wine-focused restaurant.",
            attributes={"quiet": 0.8, "premium": 0.7},
            cuisine={"wine_bar": {"value": 1.0}},
            signals=[{"type": "wanted_to_try", "value": True, "provenance": "probe"}],
            metadata={"index_fields": ["canonical_name", "notes"]},
        ),
        PalateSignalDataPoint(
            id="signal_known_oaky_wanted",
            taste_item_id="wine_known_oaky_rioja",
            signal_type="wanted_to_try",
            value=True,
        ),
        PalateDecisionDataPoint(
            id="decision_oaky_probe",
            query=PROBE_QUERY,
            candidate_item_ids=["wine_known_oaky_rioja", "wine_chateau_musar_2016"],
            chosen_item_id="wine_known_oaky_rioja",
            rejected_item_ids=["wine_chateau_musar_2016"],
        ),
    ]


def build_enriched_restaurant_probe_point(
    settings: Settings,
    *,
    allow_broader_web_search: bool,
) -> dict[str, Any]:
    enriched = TasteEnrichmentService(settings).describe_item(
        item_text="Noble Rot",
        entity_type="restaurant",
        canonical_name="Noble Rot",
        metadata={},
        notes="I want to try Noble Rot.",
        fetch_external_ratings=True,
        allow_broader_web_search=allow_broader_web_search,
    )
    metadata = enriched["normalized_metadata"]
    point = RestaurantDataPoint(
        id="restaurant_enriched_noble_rot",
        canonical_name=enriched["canonical_name"],
        city=None,
        notes=enriched.get("notes") or "I want to try Noble Rot.",
        attributes={"quiet": 0.8, "premium": 0.7},
        cuisine=metadata.get("cuisine") or {},
        signals=[{"type": "wanted_to_try", "value": True, "provenance": "probe_enrichment"}],
        metadata={
            "enrichment_status": enriched["enrichment_status"],
            "normalized_metadata": metadata,
            "enrichment_metadata": enriched["enrichment_metadata"],
            "sources": enriched["sources"],
            "warnings": enriched["warnings"],
        },
    )
    return {
        "point": point,
        "demo": {
            "input": "Noble Rot",
            "entity_type": "restaurant",
            "status": enriched["enrichment_status"],
            "sources": enriched["sources"],
            "warnings": enriched["warnings"],
            "metadata": metadata,
            "stored_point_id": point.id,
            "allow_broader_web_search": allow_broader_web_search,
        },
    }


def build_ranking_demo(raw_candidates: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_items = [
        point
        for point in raw_candidates
        if point.get("type") in {"wine", "restaurant", "music", "cigar", "experience", "movie", "series"}
    ]
    type_filtered = [point for point in candidate_items if point.get("type") == "wine"]
    wanted_filtered = [
        point
        for point in type_filtered
        if _has_signal(point, {"wanted_to_try", "wanted_to_watch", "wanted_to_listen"})
    ]
    policy_filtered = [point for point in wanted_filtered if not _has_signal(point, {"avoid"})]
    ranked = rank_candidates(
        policy_filtered,
        {
            "intent": "hybrid_query",
            "entity_type": "wine",
            "attributes": ["oak"],
            "context": {},
            "filters": {},
            "search_text": "oaky wanted",
        },
    )
    scores = [
        {
            "id": result["entity"]["id"],
            "name": result["entity"]["canonical_name"],
            "score": result["score"],
            "matched_attributes": result["facts"]["matched_attributes"],
            "negative_signals": result["facts"]["negative_signals"],
        }
        for result in ranked
    ]
    return {
        "raw_candidate_ids": [point.get("id") for point in candidate_items],
        "filtered_candidate_ids": [point.get("id") for point in policy_filtered],
        "excluded_candidate_ids": sorted(
            {
                str(point.get("id"))
                for point in candidate_items
                if point.get("id") not in {candidate.get("id") for candidate in policy_filtered}
            }
        ),
        "scores": scores,
        "winner_id": scores[0]["id"] if scores else None,
        "winner_name": scores[0]["name"] if scores else None,
        "type_filtering_passed": all(point.get("type") == "wine" for point in type_filtered)
        and "restaurant_noble_rot" not in [point.get("id") for point in policy_filtered],
        "signal_filtering_passed": "wine_avoided_napa_cab"
        not in [point.get("id") for point in policy_filtered],
    }


def validate_probe_dataset_name(dataset_name: str) -> str:
    normalized = dataset_name.strip()
    if not normalized:
        raise ValueError("Probe dataset name must not be empty.")
    if normalized in PRODUCTION_DATASET_NAMES or not normalized.startswith(SAFE_DATASET_PREFIX):
        raise ValueError(
            f"Refusing to run palate probe against unsafe dataset name: {normalized}"
        )
    return normalized


def sqlite_requirements(capabilities: dict[str, bool]) -> list[str]:
    requirements = []
    if not all(
        capabilities.get(key, False)
        for key in (
            "exact_lookup",
            "structured_readback",
            "semantic_retrieval",
            "type_filtering",
            "signal_filtering",
            "update",
            "delete_currentness",
        )
    ):
        requirements.append("palate_read_model")
    if not capabilities.get("decision_aggregation", False):
        requirements.append("decision_feedback_aggregates")
    if not capabilities.get("failure_recovery", False):
        requirements.append("failed_write_retry_log")
    return requirements


def overall_recommendation(capabilities: dict[str, bool]) -> ProbeRecommendation:
    if not capabilities.get("exact_lookup", False) or not capabilities.get(
        "structured_readback",
        False,
    ):
        return "sqlite_authoritative_required"
    if not all(
        capabilities.get(key, False)
        for key in ("semantic_retrieval", "type_filtering", "signal_filtering", "update", "delete_currentness")
    ):
        return "cognee_plus_sqlite_read_model"
    if not capabilities.get("decision_aggregation", False):
        return "cognee_plus_sqlite_decision_log"
    return "cognee_authoritative"


def render_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Palate Cognee Capability Probe",
        "",
        f"- Dataset: `{report['dataset_name']}`",
        f"- Recommendation: `{report['overall_recommendation']}`",
        f"- SQLite required for: {', '.join(report['sqlite_required_for']) or 'nothing'}",
        "",
        "## Capabilities",
        "",
    ]
    for key, value in sorted(report["capabilities"].items()):
        lines.append(f"- `{key}`: {'PASS' if value else 'FAIL'}")
    demo = report.get("ranking_demo") or {}
    lines.extend(
        [
            "",
            "## Ranking Demo",
            "",
            f"- Query: `{report.get('query', PROBE_QUERY)}`",
            f"- Winner: `{demo.get('winner_name')}` (`{demo.get('winner_id')}`)",
            f"- Filtered candidates: `{demo.get('filtered_candidate_ids', [])}`",
            f"- Excluded candidates: `{demo.get('excluded_candidate_ids', [])}`",
        ]
    )
    if report.get("errors"):
        lines.extend(["", "## Errors", ""])
        for error in report["errors"]:
            lines.append(f"- `{error.get('stage')}`: {error.get('error')}")
    enrichment = report.get("enrichment_demo") or {}
    if enrichment:
        lines.extend(
            [
                "",
                "## Enrichment Demo",
                "",
                f"- Input: `{enrichment.get('input')}`",
                f"- Status: `{enrichment.get('status')}`",
                f"- Stored point: `{enrichment.get('stored_point_id')}`",
                f"- Sources: `{enrichment.get('sources', [])}`",
                f"- Warnings: `{enrichment.get('warnings', [])}`",
            ]
        )
    return "\n".join(lines)


def run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the palate Cognee capability probe.")
    parser.add_argument("--dataset-name", default=None)
    parser.add_argument("--live", action="store_true", help="Use live Cognee instead of fake adapter.")
    parser.add_argument(
        "--include-enrichment",
        action="store_true",
        help="Run current strict-source taste enrichment and store the enriched point.",
    )
    parser.add_argument(
        "--allow-broader-web-search",
        action="store_true",
        help="Allow broader web search in the enrichment demo.",
    )
    parser.add_argument("--env", choices=["dev", "prod"], default=None, help="Config profile to load.")
    parser.add_argument("--env-file", default=None, help="Optional settings env file for the probe run.")
    parser.add_argument("--format", choices=["json", "markdown", "both"], default="both")
    args = parser.parse_args(argv)

    dataset_name = args.dataset_name or build_probe_dataset_name()
    adapter = None if args.live else InMemoryPalateProbeAdapter(validate_probe_dataset_name(dataset_name))
    settings = load_settings(args.env_file, config_env=args.env) if args.env_file else None
    try:
        report = asyncio.run(
            run_palate_cognee_capability_probe(
                adapter=adapter,
                dataset_name=dataset_name,
                live=args.live,
                include_enrichment=args.include_enrichment,
                allow_broader_web_search=args.allow_broader_web_search,
                settings=settings,
                config_env=args.env if settings is None else None,
            )
        )
    except (CogneeUnavailableError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, indent=2, sort_keys=True))
        return 2

    if args.format in {"json", "both"}:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    if args.format == "both":
        print()
    if args.format in {"markdown", "both"}:
        print(render_markdown_report(report))
    return 0


async def _check_exact_lookup(adapter: PalateProbeAdapter, fixtures: list[ProbePoint]) -> bool:
    item_ids = [point.id for point in fixtures if isinstance(point, WineDataPoint | RestaurantDataPoint)]
    for point_id in item_ids:
        if await adapter.get_point(point_id) is None:
            return False
    return True


async def _check_structured_readback(adapter: PalateProbeAdapter, fixtures: list[ProbePoint]) -> bool:
    required = {"id", "type", "canonical_name", "attributes", "signals", "status"}
    for fixture in fixtures:
        if not isinstance(fixture, WineDataPoint | RestaurantDataPoint):
            continue
        point = await adapter.get_point(fixture.id)
        if point is None or not required <= set(point):
            return False
    return True


async def _safe_search(adapter: PalateProbeAdapter, report: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        return await adapter.search(PROBE_QUERY, top_k=10)
    except Exception as exc:
        report["errors"].append({"stage": "semantic_search", "error": str(exc)})
        return []


async def _check_update(adapter: PalateProbeAdapter) -> bool:
    point = await adapter.get_point("wine_known_oaky_rioja")
    if point is None:
        return False
    updated = WineDataPoint(**{**point, "attributes": {**point.get("attributes", {}), "oak": 0.88}})
    updated.update_version()
    await adapter.upsert_points([updated])
    readback = await adapter.get_point("wine_known_oaky_rioja")
    same_id = readback is not None and readback.get("id") == "wine_known_oaky_rioja"
    changed = readback is not None and abs(float(readback["attributes"]["oak"]) - 0.88) < 0.001
    duplicates = [
        point
        for point in await adapter.list_points("wine")
        if point.get("canonical_name") == "Known Oaky Rioja"
    ]
    return same_id and changed and len(duplicates) == 1


async def _check_delete_currentness(adapter: PalateProbeAdapter) -> bool:
    await adapter.delete_point("wine_avoided_napa_cab")
    results = await adapter.search(PROBE_QUERY, top_k=10)
    demo = build_ranking_demo(results)
    return "wine_avoided_napa_cab" not in demo["filtered_candidate_ids"]


async def _check_decision_aggregation(adapter: PalateProbeAdapter) -> bool:
    decisions = [
        point
        for point in await adapter.list_points("PalateDecisionDataPoint")
        if point.get("query") == PROBE_QUERY
    ]
    if not decisions:
        decisions = [
            point
            for point in await adapter.list_points()
            if point.get("id") == "decision_oaky_probe"
        ]
    if not decisions:
        return False
    chosen = sum(1 for decision in decisions if decision.get("chosen_item_id") == "wine_known_oaky_rioja")
    rejected = sum(
        1
        for decision in decisions
        if "wine_chateau_musar_2016" in (decision.get("rejected_item_ids") or [])
    )
    return chosen == 1 and rejected == 1


def _check_failure_recovery() -> bool:
    failed_payload = {
        "object_id": "wine_known_oaky_rioja",
        "operation": "upsert",
        "payload_hash": hashlib.sha256(b"wine_known_oaky_rioja").hexdigest(),
        "status": "failed",
    }
    return bool(
        failed_payload["object_id"]
        and failed_payload["operation"]
        and failed_payload["payload_hash"]
        and failed_payload["status"] == "failed"
    )


def _all_capabilities(value: bool) -> dict[str, bool]:
    return {
        "exact_lookup": value,
        "structured_readback": value,
        "semantic_retrieval": value,
        "type_filtering": value,
        "signal_filtering": value,
        "update": value,
        "delete_currentness": value,
        "decision_aggregation": value,
        "failure_recovery": value,
    }


def _has_signal(point: dict[str, Any], signal_types: set[str]) -> bool:
    return any(signal.get("type") in signal_types for signal in point.get("signals") or [])


def _contains_point(points: list[dict[str, Any]], point_id: str) -> bool:
    return any(point.get("id") == point_id for point in points)


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in "".join(char.lower() if char.isalnum() else " " for char in value).split()
        if len(token) > 2
    }


def _point_search_text(point: dict[str, Any]) -> str:
    signals = " ".join(
        f"{signal.get('type')} {signal.get('value')}" for signal in point.get("signals") or []
    )
    attributes = " ".join(
        key for key, value in (point.get("attributes") or {}).items() if float(value or 0) > 0
    )
    return " ".join(
        str(part)
        for part in [
            point.get("canonical_name"),
            point.get("notes"),
            attributes,
            signals,
            point.get("type"),
        ]
        if part
    )


def _uuid_for_external_id(external_id: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"brain-palate-probe:{external_id}")


def _to_live_datapoint(datapoint_base: Any, point: ProbePoint, dataset_name: str) -> Any:
    fields = _live_fields(point, dataset_name)
    class_name = point.__class__.__name__
    live_class = type(
        class_name,
        (datapoint_base,),
        {
            "__annotations__": {key: type(value) if value is not None else Any for key, value in fields.items()},
            "metadata": {"index_fields": ["canonical_name", "notes"]},
        },
    )
    return live_class(**fields)


def _live_fields(point: ProbePoint, dataset_name: str) -> dict[str, Any]:
    payload = point.model_dump(mode="json")
    external_id = point.id
    palate_type = payload.get("type")
    attributes = payload.pop("attributes", None)
    signals = payload.pop("signals", None)
    cuisine = payload.pop("cuisine", None)
    context = payload.pop("context", None)
    candidate_item_ids = payload.pop("candidate_item_ids", None)
    rejected_item_ids = payload.pop("rejected_item_ids", None)
    metadata = payload.pop("metadata", None)
    payload["id"] = _uuid_for_external_id(point.id)
    payload["external_id"] = external_id
    payload["palate_type"] = palate_type
    payload["source_node_set"] = ["palate_probe", f"dataset:{dataset_name}", f"palate:{palate_type}"]
    payload["metadata"] = {"index_fields": ["canonical_name", "notes", "attributes_summary", "signals_summary"]}
    if attributes is not None:
        payload["attributes_json"] = json.dumps(attributes, sort_keys=True)
        payload["attributes_summary"] = " ".join(attributes.keys())
    if signals is not None:
        payload["signals_json"] = json.dumps(signals, sort_keys=True)
        payload["signals_summary"] = " ".join(signal.get("type", "") for signal in signals)
    if cuisine is not None:
        payload["cuisine_json"] = json.dumps(cuisine, sort_keys=True)
    if context is not None:
        payload["context_json"] = json.dumps(context, sort_keys=True)
    if candidate_item_ids is not None:
        payload["candidate_item_ids"] = [str(item_id) for item_id in candidate_item_ids]
    if rejected_item_ids is not None:
        payload["rejected_item_ids"] = [str(item_id) for item_id in rejected_item_ids]
    if metadata is not None:
        payload["palate_metadata_json"] = json.dumps(metadata, sort_keys=True)
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
            if not key.startswith("_") and key in {"id", "external_id", "type", "canonical_name", "attributes", "signals", "status", "notes"}
        }
    payload["id"] = str(payload.get("external_id") or fallback_id)
    payload["type"] = payload.get("palate_type") or payload.get("type")
    for source_key, target_key, default in (
        ("attributes_json", "attributes", {}),
        ("signals_json", "signals", []),
        ("cuisine_json", "cuisine", {}),
        ("context_json", "context", {}),
        ("palate_metadata_json", "metadata", {}),
    ):
        if source_key not in payload:
            continue
        try:
            payload[target_key] = json.loads(payload[source_key])
        except (TypeError, json.JSONDecodeError):
            payload[target_key] = default
    return payload


def _normalize_search_results(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if isinstance(raw, list):
        values = raw
    else:
        values = [raw]
    normalized = []
    for value in values:
        if isinstance(value, dict):
            normalized.append(value)
        elif hasattr(value, "model_dump"):
            normalized.append(value.model_dump(mode="json"))
        else:
            normalized.append({"text": str(value)})
    return normalized


def _point_from_mapping(point: dict[str, Any]) -> ProbePoint:
    point_type = point.get("type")
    if point_type == "wine":
        return WineDataPoint(**point)
    if point_type == "restaurant":
        return RestaurantDataPoint(**point)
    if "signal_type" in point:
        return PalateSignalDataPoint(**point)
    if "candidate_item_ids" in point:
        return PalateDecisionDataPoint(**point)
    raise ValueError(f"Unsupported probe point mapping: {point}")


if __name__ == "__main__":
    raise SystemExit(run_cli())
