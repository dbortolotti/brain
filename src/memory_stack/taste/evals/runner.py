from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from memory_stack.brain_models import IngestSourceRequest, RecallRequest
from memory_stack.brain_service import ingest_source, recall
from memory_stack.config import Settings, load_settings
from memory_stack.taste.models import TasteDescribeRequest, TasteQueryRequest, TasteRememberRequest
from memory_stack.taste.routing import taste_domain_router
from memory_stack.taste.service import TasteService

from .cases import DEFAULT_TASTE_EVAL_CASES, coverage_report


def run_acceptance_evals(settings: Settings) -> dict[str, Any]:
    service = TasteService(settings)
    records = []

    def record(area: str, passed: bool, details: dict[str, Any] | None = None) -> None:
        records.append({"area": area, "passed": passed, "details": details or {}})

    route = taste_domain_router("Sam recommended Chateau Musar 2016.")
    record(
        "taste_domain_routing",
        route["domain"] == "taste"
        and route["taste_intent"] == "remember"
        and route["entity_type_hint"] == "wine",
        route,
    )

    series_route = taste_domain_router("I watched The Bear and rate it 8/10.")
    record(
        "taste_entity_classification",
        series_route["entity_type_hint"] == "series"
        and series_route["extracted"].get("item") == "The Bear",
        series_route,
    )

    described = service.describe_item(
        request=TasteDescribeRequest(
            item_text="Coherence",
            entity_type="movie",
            canonical_name="Coherence",
            metadata={"genre": ["Sci-Fi"], "runtime": "89 min"},
            fetch_external_ratings=False,
        )
    )
    record(
        "enrichment_normalization",
        described["stored"] is False
        and described["enriched"]["normalized_metadata"]["genre"] == ["sci_fi"]
        and "source_payloads" in described["enriched"]["enrichment_metadata"],
    )

    strict = service.remember(
        TasteRememberRequest(
            type="wine",
            canonical_name="Eval Strict Wine",
            description="Eval Strict Wine is rated 8/10.",
            rating=8,
            attributes={"oak": 0.8, "quiet": 0.4},
            fetch_external_ratings=False,
        )
    )
    record(
        "strict_schema_validation",
        strict["taste_records"][0]["attributes"] == {"oak": 0.8}
        and any("quiet" in warning for warning in strict["enrichment"]["warnings"]),
    )

    known = service.remember(
        TasteRememberRequest(
            type="wine",
            canonical_name="Eval Known Wine",
            description="Eval Known Wine is rated 8/10.",
            rating=8,
            fetch_external_ratings=False,
        )
    )["taste_records"][0]
    service.remember(
        TasteRememberRequest(
            type="wine",
            canonical_name="Eval Other Saved Wine",
            description="Eval Other Saved Wine is rated 10/10.",
            rating=10,
            fetch_external_ratings=False,
        )
    )
    options = service.evaluate_options(
        TasteQueryRequest(
            query="Which wine should I choose?",
            options_text="Eval Known Wine\nMystery Bottle",
            intent={
                "intent": "option_set_evaluation",
                "entity_type": "wine",
                "attributes": [],
                "context": {},
                "filters": {},
            },
        )
    )
    record(
        "option_matching",
        options["retrieval"]["unmatched_options"] == ["Mystery Bottle"]
        and [item["id"] for item in options["ranked_results"]] == [known["id"]],
    )

    ranking = service.query(
        TasteQueryRequest(
            query="Which wine should I bring?",
            explain=True,
            intent={
                "intent": "hybrid_query",
                "entity_type": "wine",
                "attributes": ["oak"],
                "context": {},
                "filters": {},
            },
        )
    )
    record("ranking_quality", bool(ranking["ranked_results"]))
    record(
        "detailed_ranking_explainability",
        bool(ranking["explanation"]["weights"])
        and bool(ranking["explanation"]["candidates"][0]["components"]),
    )

    avoided = service.remember(
        TasteRememberRequest(
            type="wine",
            canonical_name="Eval Avoid Wine",
            description="Avoid Eval Avoid Wine.",
            avoid=True,
            fetch_external_ratings=False,
        )
    )["taste_records"][0]
    negative = service.query(
        TasteQueryRequest(
            query="Which wine should I choose?",
            intent={"intent": "hybrid_query", "entity_type": "wine", "attributes": [], "context": {}, "filters": {}},
        )
    )
    record(
        "negative_signal_handling",
        avoided["id"] not in {item["id"] for item in negative["ranked_results"]},
    )

    decision_id = service.store.log_decision(
        "Which wine should I choose?",
        {},
        [],
        [{"id": known["id"], "name": known["canonical_name"], "score": 1.0}],
        chosen_taste_item_id=known["id"],
    )
    feedback = service.store.decision_feedback("Which wine should I choose tonight?", [known["id"]])
    record("decision_feedback", decision_id.startswith("tdec_") and feedback[known["id"]]["chosen"] == 1)

    projected = service.remember(
        TasteRememberRequest(
            type="restaurant",
            canonical_name="Eval Noble Rot",
            description="I want to try Eval Noble Rot.",
            wanted=True,
            fetch_external_ratings=False,
        )
    )
    projection = projected["brain_projection"]
    record("brain_entity_projection", bool(projection["entity_id"]))
    record("brain_memory_projection", bool(projection["memory_ids"]))
    record("relationship_creation", bool(projection["relationship_ids"]))
    record("open_loop_creation", bool(projection["open_loop_ids"]))

    closed = service.remember(
        TasteRememberRequest(
            type="restaurant",
            canonical_name="Eval Noble Rot",
            description="I tried Eval Noble Rot.",
            tried=True,
            fetch_external_ratings=False,
        )
    )
    record("open_loop_closure", bool(closed["brain_projection"]["closed_open_loop_ids"]))

    recall_receipt = recall(RecallRequest(query="Eval Noble Rot"), settings)
    record(
        "generic_recall_taste_evidence",
        bool((recall_receipt.taste or {}).get("linked_evidence")),
    )

    failed = service.remember(
        TasteRememberRequest(
            type="restaurant",
            canonical_name="Eval Nobble Rot",
            description="I want to try Eval Nobble Rot.",
            wanted=True,
        )
    )
    record(
        "failed_enrichment_safety",
        failed["stored"] is False and failed.get("requires_confirmation") is True,
    )

    source = ingest_source(
        IngestSourceRequest(
            source=" ".join(f"I want to try Eval Restaurant {index}." for index in range(12)),
            source_kind="markdown",
            extract_memories=True,
        ),
        settings,
    )
    record(
        "large_source_ingestion_selectivity",
        source.taste["source_ingestion_policy"] == "selection_required"
        and source.taste["mass_enrichment_skipped"] is True,
    )

    covered = coverage_report()
    required = set(covered["covered"])
    passed = {item["area"] for item in records if item["passed"]}
    missing = sorted(required - passed)
    return {
        "coverage": covered,
        "case_count": len(records),
        "pass_count": sum(1 for item in records if item["passed"]),
        "fail_count": sum(1 for item in records if not item["passed"]),
        "missing_passed_areas": missing,
        "records": records,
    }


def settings_for_eval_db(path: Path | None) -> Settings:
    if path is None:
        tmp = tempfile.NamedTemporaryFile(prefix="brain-taste-eval-", suffix=".db", delete=False)
        tmp.close()
        path = Path(tmp.name)
    return Settings(brain_database_url=f"sqlite:///{path}", brain_taste_omdb_api_key=None)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic Brain Taste acceptance evals.")
    parser.add_argument("--brain-db", help="Optional SQLite DB path. Defaults to a temporary eval DB.")
    parser.add_argument(
        "--coverage-only",
        action="store_true",
        help="Print the acceptance-case inventory without running runtime evals.",
    )
    parser.add_argument(
        "--use-runtime-db",
        action="store_true",
        help="Run against configured runtime DB. This mutates Taste eval records.",
    )
    args = parser.parse_args()

    if args.coverage_only:
        payload = {"coverage": coverage_report(), "cases": DEFAULT_TASTE_EVAL_CASES}
    elif args.use_runtime_db:
        payload = run_acceptance_evals(load_settings())
    else:
        payload = run_acceptance_evals(
            settings_for_eval_db(Path(args.brain_db) if args.brain_db else None)
        )
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
