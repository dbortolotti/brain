from __future__ import annotations

from typing import Any

from sqlalchemy import func, select

from memory_stack import brain_schema as schema
from memory_stack.brain_models import IngestSourceRequest, RecallRequest, RememberRequest
from memory_stack.brain_service import ingest_source, recall, remember
from memory_stack.brain_store import BrainStore
from memory_stack.config import Settings
from memory_stack.llm.fake import FakeLLMClient
from memory_stack.taste.models import (
    TasteDescribeRequest,
    TasteQueryRequest,
    TasteRefreshRequest,
    TasteRememberRequest,
)
from memory_stack.taste.evals import DEFAULT_TASTE_EVAL_CASES, coverage_report
from memory_stack.taste.evals.runner import run_acceptance_evals
from memory_stack.taste import restaurants
from memory_stack.taste.service import TasteService
from memory_stack.taste.store import TasteStore


def test_describe_item_is_read_only(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    service = TasteService(settings)

    result = service.describe_item(
        TasteDescribeRequest(
            item_text="Coherence",
            entity_type="movie",
            canonical_name="Coherence",
            fetch_external_ratings=False,
        )
    )

    assert result["stored"] is False
    assert result["source"] == "read_only_enrichment"
    assert TasteStore(settings).list_entities() == []
    assert table_count(settings, schema.entities) == 0
    assert table_count(settings, schema.memory_cards) == 0
    assert table_count(settings, schema.open_loops) == 0


def test_taste_eval_case_registry_covers_acceptance_areas() -> None:
    report = coverage_report()

    assert report["complete"] is True
    assert report["case_count"] == len(DEFAULT_TASTE_EVAL_CASES)
    assert report["missing"] == []


def test_taste_acceptance_eval_runner_exercises_all_areas(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    result = run_acceptance_evals(settings)

    assert result["fail_count"] == 0
    assert result["missing_passed_areas"] == []


def test_restaurant_strict_source_google_places_enrichment(tmp_path, monkeypatch) -> None:
    settings = brain_test_settings(tmp_path, brain_taste_google_places_api_key="places-key")

    def fake_json_url(url: str, *, timeout: float) -> dict[str, Any]:
        assert "key=places-key" in url
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

    result = TasteService(settings).describe_item(
        TasteDescribeRequest(
            item_text="Noble Rot",
            entity_type="restaurant",
            canonical_name="Noble Rot",
        )
    )

    enriched = result["enriched"]
    assert result["stored"] is False
    assert enriched["enrichment_status"] == "success"
    assert enriched["normalized_metadata"]["google"]["rating"] == 4.6
    assert enriched["normalized_metadata"]["google"]["rating_count"] == 1200
    assert "cocktail_bar_drinks" in enriched["normalized_metadata"]["cuisine"]
    assert enriched["sources"][0]["name"] == "google_places"
    assert enriched["enrichment_metadata"]["normalized_fields_source"] == "strict_source"


def test_broader_web_search_requires_explicit_approval(tmp_path, monkeypatch) -> None:
    settings = brain_test_settings(tmp_path)

    def fake_text_url(url: str, *, timeout: float) -> str:
        assert timeout > 0
        if "duckduckgo.com" in url:
            return """
            <a class="result__a" href="https://example.com/nobble">Nobble Rot</a>
            <a class="result__snippet">A French restaurant with a wine bar menu.</a>
            """
        return "<html>No Michelin match</html>"

    monkeypatch.setattr(restaurants, "fetch_text_url", fake_text_url)

    service = TasteService(settings)
    initial = service.remember(
        TasteRememberRequest(
            type="restaurant",
            canonical_name="Nobble Rot",
            description="I want to try Nobble Rot.",
            wanted=True,
        )
    )
    corrected = service.correct_proposal(
        initial["proposal_id"],
        "search broader web and keep the category as restaurant",
    )

    payload = corrected["proposal"]["proposal_json"]
    assert initial["requires_confirmation"] is True
    assert payload["remember_payload"]["allow_broader_web_search"] is True
    assert payload["proposed_taste_records"][0]["metadata"]["cuisine"]["french"]["value"] == 1.0
    assert "controlled_web_search" in payload["proposed_taste_records"][0][
        "enrichment_metadata_summary"
    ]["source_payloads"]
    assert any(
        "Broader web search was explicitly approved" in warning
        for warning in corrected["proposal"]["warnings_json"]
    )


def test_remember_projects_taste_item_into_brain(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    service = TasteService(settings)

    result = service.remember(
        TasteRememberRequest(
            type="wine",
            canonical_name="Ridge Estate Cabernet",
            description="Mike recommended Ridge Estate Cabernet 2019.",
            attributes={"oak": 0.8, "quiet": 0.4},
            recommended_by="Mike",
            fetch_external_ratings=False,
        )
    )

    record = result["taste_records"][0]
    store = BrainStore(settings)
    memory = store.get_memory(record["evidence_memory_id"])
    relationship_id = result["brain_projection"]["relationship_ids"][0]
    with store.engine.begin() as conn:
        relationship = conn.execute(
            select(schema.relationships).where(schema.relationships.c.id == relationship_id)
        ).one()

    assert result["stored"] is True
    assert record["attributes"] == {"oak": 0.8}
    assert "quiet" not in record["attributes"]
    assert "Ignored attributes not valid for wine: quiet." in result["enrichment"]["warnings"]
    assert memory is not None
    assert memory["metadata_json"]["taste"] is True
    assert memory["metadata_json"]["taste_item_id"] == record["id"]
    assert relationship._mapping["predicate"] == "recommended"


def test_evaluate_options_reports_unmatched_without_substituting_saved_items(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    service = TasteService(settings)
    known = service.remember(
        TasteRememberRequest(
            type="wine",
            canonical_name="Known Wine",
            description="Known Wine is rated 8/10.",
            rating=8,
            fetch_external_ratings=False,
        )
    )["taste_records"][0]
    service.remember(
        TasteRememberRequest(
            type="wine",
            canonical_name="Other Saved Wine",
            description="Other Saved Wine is rated 10/10.",
            rating=10,
            fetch_external_ratings=False,
        )
    )

    result = service.evaluate_options(
        TasteQueryRequest(
            query="Which wine should I choose?",
            options_text="Known Wine\nMystery Bottle",
            intent={
                "intent": "option_set_evaluation",
                "entity_type": "wine",
                "attributes": [],
                "context": {},
                "filters": {},
            },
        )
    )

    assert result["retrieval"]["constrained_to_options"] is True
    assert result["retrieval"]["unmatched_options"] == ["Mystery Bottle"]
    assert [item["id"] for item in result["ranked_results"]] == [known["id"]]


def test_generic_remember_routes_high_confidence_taste_to_confirmation_then_recall_links_evidence(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    receipt = remember(
        RememberRequest(input="I want to try Ridge Estate Cabernet 2019."),
        settings,
    )
    confirmed = TasteService(settings).confirm(receipt.taste["proposal_id"])
    evidence_response = recall(RecallRequest(query="Ridge Estate Cabernet"), settings)
    ranking_response = recall(RecallRequest(query="Which wine should I choose?"), settings)

    assert receipt.classification == "taste_proposal"
    assert confirmed["confirmed"] is True
    assert evidence_response.taste["linked_evidence"][0]["canonical_name"] == (
        "Ridge Estate Cabernet 2019"
    )
    assert ranking_response.taste["ranked_results"][0]["name"] == "Ridge Estate Cabernet 2019"


def test_generic_remember_creates_medium_confidence_taste_proposal(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    receipt = remember(RememberRequest(input="Alex recommended Mystery Thing."), settings)

    assert receipt.classification == "taste_proposal"
    assert receipt.dry_run is True
    assert receipt.taste["requires_confirmation"] is True
    assert table_count(settings, schema.memory_cards) == 0
    assert table_count(settings, schema.taste_proposals) == 1


def test_failed_strict_enrichment_requires_confirmation_without_projection(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    service = TasteService(settings)

    result = service.remember(
        TasteRememberRequest(
            type="restaurant",
            canonical_name="Nobble Rot",
            description="I want to try Nobble Rot.",
            wanted=True,
        )
    )

    assert result["stored"] is False
    assert result["requires_confirmation"] is True
    assert result["proposal"]["broader_search_policy"].startswith("Strict-source lookup")
    assert any("Broader web search" in warning for warning in result["warnings"])
    assert table_count(settings, schema.taste_items) == 0
    assert table_count(settings, schema.memory_cards) == 0
    assert table_count(settings, schema.open_loops) == 0


def test_router_extracts_listened_and_negative_signals_into_proposals(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    listened = remember(RememberRequest(input="I listened to Kind of Blue and loved it."), settings)
    smoked = remember(
        RememberRequest(input="I smoked a Partagas Serie D No. 4 and disliked it."),
        settings,
    )

    assert listened.classification == "taste_proposal"
    assert listened.taste["proposal"]["remember_payload"]["type"] == "music"
    assert listened.taste["proposal"]["remember_payload"]["listened"] is True
    assert listened.taste["proposal"]["remember_payload"]["canonical_name"] == "Kind of Blue"
    assert smoked.classification == "taste_proposal"
    assert smoked.taste["proposal"]["remember_payload"]["type"] == "cigar"
    assert smoked.taste["proposal"]["remember_payload"]["tried"] is True
    assert smoked.taste["proposal"]["remember_payload"]["disliked"] is True


def test_optional_llm_taste_routing_creates_confirmation_proposal(tmp_path) -> None:
    settings = brain_test_settings(tmp_path, brain_taste_llm_routing_enabled=True)
    llm = FakeLLMClient(
        {
            "domain": "taste",
            "taste_intent": "remember",
            "entity_type_hint": "wine",
            "confidence": 0.82,
            "requires_enrichment": True,
            "requires_confirmation": True,
            "ambiguity_reasons": ["LLM classified as a taste recommendation."],
            "extracted": {
                "item": "Vina Tondonia",
                "recommended_by": "Mira",
            },
        }
    )

    receipt = remember(
        RememberRequest(input="Mira says Vina Tondonia would suit dinner."),
        settings,
        llm_client=llm,
    )

    assert receipt.classification == "taste_proposal"
    assert receipt.taste["proposal"]["route"]["classification_source"] == "llm"
    assert receipt.taste["proposal"]["remember_payload"]["type"] == "wine"
    assert table_count(settings, schema.memory_cards) == 0


def test_source_ingestion_does_not_mass_route_taste_writes(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    receipt = ingest_source(
        IngestSourceRequest(
            source="I want to try Ridge Estate Cabernet 2019.",
            source_kind="markdown",
            title="Taste-looking source",
            extract_memories=True,
        ),
        settings,
    )

    assert receipt.classification == "markdown"
    assert table_count(settings, schema.taste_items) == 0
    assert table_count(settings, schema.sources) == 1
    assert receipt.taste["mass_enrichment_skipped"] is True
    assert receipt.taste["candidate_count"] == 1
    assert table_count(settings, schema.taste_proposals) == 1


def test_source_ingestion_four_to_ten_candidates_creates_selection_proposal(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    receipt = ingest_source(
        IngestSourceRequest(
            source=(
                "I want to try Noble Rot. "
                "I want to try Septime. "
                "I want to try Clamato. "
                "I want to try Le Chateaubriand."
            ),
            source_kind="markdown",
            title="Paris wishlist",
            extract_memories=True,
        ),
        settings,
    )

    assert receipt.classification == "markdown"
    assert receipt.taste["source_ingestion_policy"] == "structured_candidate_selection"
    assert receipt.taste["candidate_count"] == 4
    assert table_count(settings, schema.taste_items) == 0
    assert table_count(settings, schema.taste_proposals) == 1


def test_completion_closes_matching_taste_open_loop_above_threshold(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    service = TasteService(settings)
    wanted = service.remember(
        TasteRememberRequest(
            type="restaurant",
            canonical_name="Noble Rot",
            description="I want to try Noble Rot.",
            wanted=True,
            fetch_external_ratings=False,
        )
    )
    open_loop_id = wanted["brain_projection"]["open_loop_ids"][0]

    tried = service.remember(
        TasteRememberRequest(
            type="restaurant",
            canonical_name="Noble Rot",
            description="I tried Noble Rot.",
            tried=True,
            fetch_external_ratings=False,
        )
    )

    assert tried["brain_projection"]["closed_open_loop_ids"] == [open_loop_id]
    assert BrainStore(settings).list_open_loops(topic="Noble Rot", status="open") == []


def test_detailed_ranking_explanation_exposes_components_and_evidence(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    service = TasteService(settings)
    stored = service.remember(
        TasteRememberRequest(
            type="wine",
            canonical_name="Known Wine",
            description="Known Wine is rated 8/10.",
            rating=8,
            attributes={"oak": 0.8},
            fetch_external_ratings=False,
        )
    )["taste_records"][0]

    result = service.query(
        TasteQueryRequest(
            query="Which wine should I choose?",
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

    explanation = result["explanation"]
    assert explanation["weights"]["preference"] > 0
    assert explanation["candidates"][0]["id"] == stored["id"]
    assert "preference" in explanation["candidates"][0]["components"]
    assert stored["evidence_memory_id"] in explanation["candidates"][0]["evidence_ids"]


def test_refresh_enrichment_reports_material_changes(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    service = TasteService(settings)
    record = service.remember(
        TasteRememberRequest(
            type="restaurant",
            canonical_name="Cafe Test",
            description="Cafe Test was recommended.",
            metadata={"genres": ["italian"]},
            fetch_external_ratings=False,
        )
    )["taste_records"][0]

    def fake_describe_item(**kwargs: Any) -> dict[str, Any]:
        return {
            "canonical_name": kwargs["canonical_name"],
            "entity_type": kwargs["entity_type"],
            "normalized_metadata": {"genres": ["japanese"]},
            "attributes": {"quiet": 0.8},
            "attribute_intervals_95": {"quiet": {"lower": 0.7, "upper": 0.9}},
            "enrichment_metadata": {"checked_at": "2026-05-11T10:00:00+00:00"},
            "sources": [],
            "warnings": [],
            "confidence": 1.0,
            "enrichment_status": "success",
            "notes": kwargs["item_text"],
        }

    service.enrichment.describe_item = fake_describe_item  # type: ignore[method-assign]

    refreshed = service.refresh_enrichment(TasteRefreshRequest(taste_item_id=record["id"]))

    assert refreshed["refreshed"] is True
    assert set(refreshed["changed_fields"]) == {
        "metadata",
        "attributes",
        "attribute_intervals_95",
    }


def table_count(settings: Settings, table: Any) -> int:
    with BrainStore(settings).engine.begin() as conn:
        return conn.execute(select(func.count()).select_from(table)).scalar_one()


def brain_test_settings(tmp_path, **overrides: Any) -> Settings:
    return Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_taste_omdb_api_key=None,
        **overrides,
    )
