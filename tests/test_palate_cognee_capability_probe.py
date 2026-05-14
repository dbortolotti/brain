from __future__ import annotations

import asyncio
import os

import pytest

from memory_stack.cognee.palate_capability_probe import (
    InMemoryPalateProbeAdapter,
    PRODUCTION_DATASET_NAMES,
    SAFE_DATASET_PREFIX,
    build_probe_dataset_name,
    render_markdown_report,
    run_palate_cognee_capability_probe,
    validate_probe_dataset_name,
)
from memory_stack.cfg import Settings
from memory_stack.taste import restaurants


def test_probe_report_contract_and_ranking_policy() -> None:
    dataset = "palate_probe_unit"
    report = asyncio.run(async_probe(dataset))

    assert report["dataset_name"] == dataset
    assert report["overall_recommendation"] in {
        "cognee_authoritative",
        "cognee_plus_sqlite_decision_log",
        "cognee_plus_sqlite_read_model",
        "sqlite_authoritative_required",
    }
    assert set(report["capabilities"]) == {
        "exact_lookup",
        "structured_readback",
        "semantic_retrieval",
        "type_filtering",
        "signal_filtering",
        "update",
        "delete_currentness",
        "decision_aggregation",
        "failure_recovery",
    }
    assert isinstance(report["sqlite_required_for"], list)
    assert report["ranking_demo"]["winner_id"] == "wine_known_oaky_rioja"
    assert "wine_avoided_napa_cab" in report["ranking_demo"]["excluded_candidate_ids"]
    assert "restaurant_noble_rot" in report["ranking_demo"]["excluded_candidate_ids"]


def test_probe_dataset_names_are_isolated_from_production() -> None:
    generated = build_probe_dataset_name()

    assert generated.startswith(SAFE_DATASET_PREFIX)
    assert validate_probe_dataset_name(generated) == generated
    for name in PRODUCTION_DATASET_NAMES:
        with pytest.raises(ValueError):
            validate_probe_dataset_name(name)
    with pytest.raises(ValueError):
        validate_probe_dataset_name("taste_enriched_compare")


def test_probe_can_run_repeatedly_without_duplicate_logical_records() -> None:
    dataset = "palate_probe_repeat"
    adapter = InMemoryPalateProbeAdapter(dataset)

    first = asyncio.run(run_palate_cognee_capability_probe(adapter=adapter, dataset_name=dataset))
    second = asyncio.run(run_palate_cognee_capability_probe(adapter=adapter, dataset_name=dataset))

    assert first["ranking_demo"]["winner_id"] == "wine_known_oaky_rioja"
    assert second["ranking_demo"]["winner_id"] == "wine_known_oaky_rioja"
    known = [
        point
        for point in adapter.points.values()
        if point.get("canonical_name") == "Known Oaky Rioja"
    ]
    assert len(known) == 1


def test_markdown_report_includes_recommendation_and_sqlite_requirement() -> None:
    report = asyncio.run(async_probe("palate_probe_markdown"))

    markdown = render_markdown_report(report)

    assert "# Palate Cognee Capability Probe" in markdown
    assert "Recommendation" in markdown
    assert "SQLite required for" in markdown
    assert "Known Oaky Rioja" in markdown


def test_probe_enrichment_demo_uses_strict_source_and_stores_point(monkeypatch) -> None:
    dataset = "palate_probe_enrichment"

    def fake_json_url(url: str, *, timeout: float) -> dict:
        assert "places-key" in url
        assert timeout > 0
        return {
            "status": "OK",
            "candidates": [
                {
                    "name": "Noble Rot",
                    "place_id": "place_123",
                    "rating": 4.6,
                    "user_ratings_total": 1200,
                    "types": ["restaurant", "wine_bar"],
                    "url": "https://www.google.com/maps/place/Noble+Rot",
                }
            ],
        }

    def fake_text_url(url: str, *, timeout: float) -> str:
        assert timeout > 0
        if "guide.michelin.com" in url:
            return "<html>No strict match here</html>"
        return "<html>Wine bar and restaurant</html>"

    monkeypatch.setattr(restaurants, "fetch_json_url", fake_json_url)
    monkeypatch.setattr(restaurants, "fetch_text_url", fake_text_url)

    report = asyncio.run(
        run_palate_cognee_capability_probe(
            adapter=InMemoryPalateProbeAdapter(dataset),
            dataset_name=dataset,
            include_enrichment=True,
            settings=Settings(brain_taste_google_places_api_key="places-key"),
        )
    )

    demo = report["enrichment_demo"]
    assert demo["status"] == "success"
    assert demo["stored_point_id"] == "restaurant_enriched_noble_rot"
    assert demo["metadata"]["google"]["rating"] == 4.6
    assert "cocktail_bar_drinks" in demo["metadata"]["cuisine"]
    assert report["overall_recommendation"] == "cognee_authoritative"


@pytest.mark.skipif(
    os.environ.get("BRAIN_LIVE_COGNEE_PROBE") != "1",
    reason="set BRAIN_LIVE_COGNEE_PROBE=1 to run live Cognee probe",
)
def test_live_cognee_probe_smoke() -> None:
    dataset = build_probe_dataset_name("palate_probe_live_")

    report = asyncio.run(run_palate_cognee_capability_probe(dataset_name=dataset, live=True))

    assert "overall_recommendation" in report
    assert report["dataset_name"] == dataset


async def async_probe(dataset: str) -> dict:
    return await run_palate_cognee_capability_probe(
        adapter=InMemoryPalateProbeAdapter(dataset),
        dataset_name=dataset,
    )
