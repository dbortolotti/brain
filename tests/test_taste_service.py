from __future__ import annotations

import json
from typing import Any

import pytest
from sqlalchemy import func, inspect, select

from memory_stack import brain_schema as schema
from memory_stack import brain_service
from memory_stack.brain_models import IngestSourceRequest, RecallRequest, RememberRequest
from memory_stack.brain_service import ingest_source, recall, remember
from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings
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
from memory_stack.taste.cognee_store import CogneePalateStore, InMemoryPalateCogneeAdapter
from memory_stack.taste.routing import taste_domain_router
from memory_stack.taste.service import TasteService, extract_option_entities, intent_from_query


def test_describe_item_is_read_only(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    service = make_taste_service(settings)

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
    assert service.canonical_store.list_entities() == []
    assert table_count(settings, schema.entities) == 0
    assert_table_absent(settings, "memory_cards")
    assert_table_absent(settings, "open_loops")


def test_taste_eval_case_registry_covers_acceptance_areas() -> None:
    report = coverage_report()

    assert report["complete"] is True
    assert report["case_count"] == len(DEFAULT_TASTE_EVAL_CASES)
    assert report["missing"] == []


def test_taste_acceptance_eval_runner_exercises_all_areas(tmp_path, monkeypatch) -> None:
    settings = brain_test_settings(tmp_path)
    calls: list[dict[str, Any]] = []
    patch_default_palate_store(monkeypatch, settings)
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))

    result = run_acceptance_evals(settings)

    assert result["fail_count"] == 0
    assert result["missing_passed_areas"] == []


def test_restaurant_strict_source_google_places_enrichment(tmp_path, monkeypatch) -> None:
    settings = brain_test_settings(tmp_path, brain_taste_google_places_api_key="places-key")

    def fake_json_url(url: str, *, timeout: float) -> dict[str, Any]:
        assert "key=places-key" in url
        assert "type" in url
        assert "types" not in url
        assert "website" not in url
        assert timeout > 0
        return {
            "status": "OK",
            "candidates": [
                {
                    "name": "Noble Rot",
                    "place_id": "place_123",
                    "rating": 4.6,
                    "user_ratings_total": 1200,
                    "type": ["restaurant", "wine_bar"],
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

    result = make_taste_service(settings).describe_item(
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

    service = make_taste_service(settings)
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


def test_remember_stores_taste_item_without_brain_semantic_projection(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    canonical = CogneePalateStore(settings, adapter=InMemoryPalateCogneeAdapter("palate_test"))
    service = TasteService(settings, canonical_store=canonical)

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

    assert result["stored"] is True
    assert result["canonical_store"] == "cognee"
    assert record["attributes"] == {"oak": 0.8}
    assert "quiet" not in record["attributes"]
    assert "Ignored attributes not valid for wine: quiet." in result["enrichment"]["warnings"]
    assert canonical.get_item(record["id"])["canonical_name"] == "Ridge Estate Cabernet"
    assert record["metadata"]["brain_db_semantic_rows_written"] is False
    assert "relationship_ids" not in result["brain_projection"]
    assert result["brain_projection"]["semantic_store"] == "cognee"
    assert result["brain_projection"]["brain_db_semantic_rows_written"] is False
    assert_legacy_semantic_counts(settings)


def test_evaluate_options_reports_unmatched_without_substituting_saved_items(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    service = make_taste_service(settings)
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


def test_restaurant_query_with_wine_context_keeps_restaurant_entity_type() -> None:
    query = (
        "Restaurant recommendation for Daniele in Mayfair London right now; infer from "
        "palate/taste memories including fine dining, wine, restaurants, preferred cuisines, "
        "and prior dining likes/dislikes."
    )

    assert intent_from_query(query)["entity_type"] == "restaurant"


def test_semicolon_option_text_splits_restaurant_candidates() -> None:
    options = extract_option_entities(
        "Gymkhana; Bibi; Hide; Hakkasan Mayfair; The Guinea Grill; Scott's; "
        "Roka Mayfair; Mount St. Restaurant; Umu; Jamavar; Sparrow Italia Mayfair; 34 Mayfair",
        "restaurant",
    )

    assert [option["canonical_name"] for option in options[:3]] == ["Gymkhana", "Bibi", "Hide"]
    assert options[-1] == {
        "canonical_name": "34 Mayfair",
        "type": "restaurant",
        "source_text": "34 Mayfair",
    }


def test_generic_remember_routes_high_confidence_taste_to_confirmation_then_recall_links_evidence(
    tmp_path,
    monkeypatch,
) -> None:
    settings = brain_test_settings(tmp_path)
    patch_default_palate_store(monkeypatch, settings)

    receipt = remember(
        RememberRequest(input="I want to try Ridge Estate Cabernet 2019."),
        settings,
    )
    confirmed = TasteService(settings).confirm(receipt.taste["proposal_id"])
    ranking_response = recall(RecallRequest(query="Which wine should I choose?"), settings)

    assert receipt.classification == "taste_proposal"
    assert confirmed["confirmed"] is True
    assert ranking_response.taste["ranked_results"][0]["name"] == "Ridge Estate Cabernet 2019"
    assert_legacy_semantic_counts(settings)


def test_generic_remember_creates_medium_confidence_taste_proposal(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    receipt = remember(RememberRequest(input="Alex recommended Mystery Thing."), settings)

    assert receipt.classification == "taste_proposal"
    assert receipt.dry_run is True
    assert receipt.taste["requires_confirmation"] is True
    assert_table_absent(settings, "memory_cards")
    assert table_count(settings, schema.taste_proposals) == 1


def test_failed_strict_enrichment_requires_confirmation_without_projection(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    service = make_taste_service(settings)

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
    assert_table_absent(settings, "taste_items")
    assert_table_absent(settings, "memory_cards")
    assert_table_absent(settings, "open_loops")


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


def test_taste_and_palate_keywords_strongly_hint_generic_remember_routing(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    llm = FakeLLMClient(
        [
            {
                "domain": "ambiguous",
                "taste_intent": "remember",
                "entity_type_hint": None,
                "confidence": 0.82,
                "requires_enrichment": True,
                "requires_confirmation": True,
                "ambiguity_reasons": ["Confirm explicit palate item type."],
                "extracted": {
                    "item": "Mystery Thing",
                    "recommended_by": "Alex",
                },
            },
            experience_enrichment_payload("A lightly evidenced palate item."),
        ]
    )

    receipt = remember(
        RememberRequest(input="Palate memory: Alex recommended Mystery Thing."),
        settings,
        llm_client=llm,
    )

    assert receipt.classification == "taste_proposal"
    assert receipt.taste["requires_confirmation"] is True
    assert receipt.taste["proposal"]["route"]["classification_source"] == "llm_explicit_palate"
    assert receipt.taste["proposal"]["route"]["requires_confirmation"] is True
    assert receipt.taste["proposal"]["remember_payload"]["canonical_name"] == "Mystery Thing"
    assert receipt.taste["proposal"]["remember_payload"]["recommended_by"] == "Alex"
    assert_table_absent(settings, "memory_cards")


def test_explicit_palate_command_requires_llm_when_client_unavailable(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    with pytest.raises(RuntimeError, match="requires server-side LLM extraction"):
        remember(
            RememberRequest(input="remember 2016 Gaja Barbaresco in palate"),
            settings,
        )


def test_deterministic_router_handles_barbaresco_as_wine_when_used_as_fallback() -> None:
    route = taste_domain_router("remember 2016 Gaja Barbaresco in palate")

    assert route["taste_intent"] == "remember"
    assert route["entity_type_hint"] == "wine"
    assert route["extracted"]["item"] == "2016 Gaja Barbaresco"
    assert route["routing_hints"] == ["taste_keyword"]


def test_explicit_palate_command_fails_when_llm_extraction_fails(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    llm = FakeLLMClient([])

    with pytest.raises(RuntimeError, match="requires server-side LLM extraction"):
        remember(
            RememberRequest(input="remember 2016 Gaja Barbaresco in palate"),
            settings,
            llm_client=llm,
        )


def test_explicit_palate_command_fails_when_llm_does_not_extract_taste(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    llm = FakeLLMClient(
        {
            "domain": "general",
            "taste_intent": "none",
            "entity_type_hint": None,
            "confidence": 0.8,
            "requires_enrichment": False,
            "requires_confirmation": False,
            "ambiguity_reasons": [],
            "extracted": {},
        }
    )

    with pytest.raises(RuntimeError, match="remember/taste LLM extraction"):
        remember(
            RememberRequest(input="remember 2016 Gaja Barbaresco in palate"),
            settings,
            llm_client=llm,
        )


def test_explicit_palate_command_prefers_web_enabled_llm_extraction(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    llm = FakeLLMClient(
        [
            {
                "domain": "ambiguous",
                "taste_intent": "remember",
                "entity_type_hint": "wine",
                "confidence": 0.88,
                "requires_enrichment": True,
                "requires_confirmation": True,
                "ambiguity_reasons": ["Confirm wine extraction."],
                "extracted": {
                    "item": "2016 Gaja Barbaresco",
                    "wanted": True,
                },
            },
            wine_enrichment_payload("Nebbiolo with classic Barbaresco structure."),
        ]
    )

    receipt = remember(
        RememberRequest(input="remember 2016 Gaja Barbaresco in palate"),
        settings,
        llm_client=llm,
    )

    assert receipt.classification == "taste_proposal"
    assert llm.calls
    assert llm.calls[0]["kwargs"]["schema_name"] == "brain_palate_memory_extraction"
    assert llm.calls[0]["kwargs"]["tools"][0]["type"] == "web_search"
    assert llm.calls[1]["kwargs"]["schema_name"] == "brain_wine_web_enrichment"
    assert llm.calls[1]["kwargs"]["tools"][0]["type"] == "web_search"
    route = receipt.taste["proposal"]["route"]
    payload = receipt.taste["proposal"]["remember_payload"]
    proposed = receipt.taste["proposal"]["proposed_taste_records"][0]
    assert route["classification_source"] == "llm_explicit_palate"
    assert payload["type"] == "wine"
    assert payload["canonical_name"] == "2016 Gaja Barbaresco"
    assert payload["wanted"] is True
    assert proposed["attributes"]["classic"] == 0.9
    assert proposed["enrichment_metadata_summary"]["normalized_fields_source"] == "llm"


def test_explicit_palate_wine_fails_when_enrichment_is_empty(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    llm = FakeLLMClient(
        [
            {
                "domain": "ambiguous",
                "taste_intent": "remember",
                "entity_type_hint": "wine",
                "confidence": 0.88,
                "requires_enrichment": True,
                "requires_confirmation": True,
                "ambiguity_reasons": ["Confirm wine extraction."],
                "extracted": {
                    "item": "2016 Cuvee Sasha",
                    "wanted": True,
                },
            },
            {"attributes": {}, "notes": "No usable wine evidence.", "metadata": {}},
        ]
    )

    with pytest.raises(RuntimeError, match="requires LLM/web enrichment"):
        remember(
            RememberRequest(input="remember 2016 cuvee sasha in palate"),
            settings,
            llm_client=llm,
        )

    assert llm.calls[1]["prompt"].count("2016 Cuvee Sasha") >= 1
    assert "remember 2016 cuvee sasha in palate" not in llm.calls[1]["prompt"]


def test_bar_word_inside_wine_name_does_not_force_restaurant(tmp_path) -> None:
    route = taste_domain_router("Palate memory: I want to try 2016 Gaja Barbaresco.")

    assert route["entity_type_hint"] == "wine"
    assert route["extracted"]["item"] == "2016 Gaja Barbaresco"


def test_bare_want_to_try_food_routes_to_restaurant_palate_proposal(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    llm = FakeLLMClient(
        [
            {
                "domain": "ambiguous",
                "taste_intent": "remember",
                "entity_type_hint": "restaurant",
                "confidence": 0.86,
                "requires_enrichment": True,
                "requires_confirmation": True,
                "ambiguity_reasons": ["Confirm restaurant wishlist extraction."],
                "extracted": {
                    "item": "Mayfair Food Fayre",
                    "wanted": True,
                },
            },
            restaurant_enrichment_payload("Casual food counter."),
        ]
    )

    receipt = remember(
        RememberRequest(
            input=(
                "Want to try Mayfair Food Fayre — specifically the Caesar salad wrap, "
                "spotted on Instagram. Location: Mayfair, London."
            ),
            context={
                "category": "restaurant_wishlist",
                "palate": True,
                "location": "Mayfair, London",
                "dish": "Caesar salad wrap",
                "source": "Instagram",
            },
        ),
        settings,
        llm_client=llm,
    )

    assert receipt.classification == "taste_proposal"
    payload = receipt.taste["proposal"]["remember_payload"]
    assert payload["type"] == "restaurant"
    assert payload["canonical_name"] == "Mayfair Food Fayre"
    assert payload["wanted"] is True


def test_explicit_palate_context_uses_llm_extraction_before_generic_memory(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    llm = FakeLLMClient(
        [
            {
                "domain": "ambiguous",
                "taste_intent": "remember",
                "entity_type_hint": "restaurant",
                "confidence": 0.84,
                "requires_enrichment": True,
                "requires_confirmation": True,
                "ambiguity_reasons": ["Confirm restaurant wishlist extraction."],
                "extracted": {
                    "item": "Mayfair Food Fayre",
                    "wanted": True,
                },
            },
            restaurant_enrichment_payload("Casual food counter."),
        ]
    )

    receipt = remember(
        RememberRequest(
            input="remember mayfair food fayre, want to try the cesar salad wrap .. saw on instagram",
            context={"palate": True, "category": "restaurant_wishlist"},
        ),
        settings,
        llm_client=llm,
    )

    assert receipt.classification == "taste_proposal"
    assert llm.calls
    assert llm.calls[0]["kwargs"]["schema_name"] == "brain_palate_memory_extraction"
    assert receipt.taste["proposal"]["route"]["classification_source"] == "llm_palate_context"
    assert receipt.taste["proposal"]["remember_payload"]["type"] == "restaurant"
    assert receipt.taste["proposal"]["remember_payload"]["canonical_name"] == "Mayfair Food Fayre"
    assert receipt.taste["proposal"]["remember_payload"]["wanted"] is True
    assert_table_absent(settings, "memory_cards")


def test_explicit_palate_context_never_falls_through_to_generic_memory(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    with pytest.raises(RuntimeError, match="requires server-side LLM extraction"):
        remember(
            RememberRequest(
                input="save this vague food thing for later",
                context={"palate": True, "category": "restaurant_wishlist"},
            ),
            settings,
        )
    assert_table_absent(settings, "memory_cards")


def test_taste_and_palate_keywords_do_not_replace_domain_evidence(tmp_path, monkeypatch) -> None:
    settings = brain_test_settings(tmp_path)
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))

    receipt = remember(
        RememberRequest(input="Brain owns schema and Palate is an internal service."),
        settings,
    )

    assert receipt.classification != "taste_proposal"
    assert table_count(settings, schema.taste_proposals) == 0
    assert calls
    assert_legacy_semantic_counts(settings)


def test_generic_remember_writes_routing_log_without_raw_text(tmp_path) -> None:
    settings = brain_test_settings(
        tmp_path,
        brain_routing_log_enabled=True,
        brain_routing_log_path=str(tmp_path / "routing" / "{date}.jsonl"),
        brain_routing_log_retention_days=90,
    )
    text = "Palate memory: Alex recommended Mystery Thing."
    llm = FakeLLMClient(
        [
            {
                "domain": "ambiguous",
                "taste_intent": "remember",
                "entity_type_hint": None,
                "confidence": 0.82,
                "requires_enrichment": True,
                "requires_confirmation": True,
                "ambiguity_reasons": ["Confirm explicit palate item type."],
                "extracted": {
                    "item": "Mystery Thing",
                    "recommended_by": "Alex",
                },
            },
            experience_enrichment_payload("A lightly evidenced palate item."),
        ]
    )

    remember(RememberRequest(input=text), settings, llm_client=llm)

    [log_path] = list((tmp_path / "routing").glob("*.jsonl"))
    record = json.loads(log_path.read_text(encoding="utf-8"))
    assert record["route"] == "palate_proposal"
    assert record["classification_source"] == "llm_explicit_palate"
    assert record["requires_confirmation"] is True
    assert "input_hash" in record
    assert text not in log_path.read_text(encoding="utf-8")
    assert record["extracted_keys"] == ["item", "recommended_by"]


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
    assert_table_absent(settings, "memory_cards")


def test_source_ingestion_does_not_mass_route_taste_writes(tmp_path, monkeypatch) -> None:
    settings = brain_test_settings(tmp_path)
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))

    receipt = ingest_source(
        IngestSourceRequest(
            source="I want to try Ridge Estate Cabernet 2019.",
            source_kind="markdown",
            title="Taste-looking source",
        ),
        settings,
    )

    assert receipt.classification == "markdown"
    assert_table_absent(settings, "taste_items")
    assert_table_absent(settings, "sources")
    assert [call["dataset_name"] for call in calls] == [settings.brain_cognee_memory_dataset]
    assert receipt.taste["mass_enrichment_skipped"] is True
    assert receipt.taste["candidate_count"] == 1
    assert table_count(settings, schema.taste_proposals) == 1
    assert_legacy_semantic_counts(settings)


def test_source_ingestion_four_to_ten_candidates_creates_selection_proposal(
    tmp_path,
    monkeypatch,
) -> None:
    settings = brain_test_settings(tmp_path)
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(brain_service, "_cognee_remember_text", fake_cognee(calls))

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
        ),
        settings,
    )

    assert receipt.classification == "markdown"
    assert receipt.taste["source_ingestion_policy"] == "structured_candidate_selection"
    assert receipt.taste["candidate_count"] == 4
    assert_table_absent(settings, "taste_items")
    assert_table_absent(settings, "sources")
    assert [call["dataset_name"] for call in calls] == [settings.brain_cognee_memory_dataset]
    assert table_count(settings, schema.taste_proposals) == 1
    assert_legacy_semantic_counts(settings)


def test_completion_records_control_projection_without_brain_open_loop_rows(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    canonical = CogneePalateStore(settings, adapter=InMemoryPalateCogneeAdapter("palate_test"))
    service = TasteService(settings, canonical_store=canonical)
    wanted = service.remember(
        TasteRememberRequest(
            type="restaurant",
            canonical_name="Noble Rot",
            description="I want to try Noble Rot.",
            wanted=True,
            fetch_external_ratings=False,
        )
    )
    tried = service.remember(
        TasteRememberRequest(
            type="restaurant",
            canonical_name="Noble Rot",
            description="I tried Noble Rot.",
            tried=True,
            fetch_external_ratings=False,
        )
    )

    assert "open_loop_ids" not in wanted["brain_projection"]
    assert "closed_open_loop_ids" not in tried["brain_projection"]
    assert_legacy_semantic_counts(settings)


def test_detailed_ranking_explanation_exposes_components_and_evidence(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    service = make_taste_service(settings)
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
    assert explanation["candidates"][0]["evidence_ids"] == []


def test_refresh_enrichment_reports_material_changes(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    service = make_taste_service(settings)
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
            "attribute_intervals_iqr": {"quiet": {"lower": 0.7, "upper": 0.9}},
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
        "attribute_intervals_iqr",
    }


def wine_enrichment_payload(notes: str) -> dict[str, Any]:
    return {
        "attributes": {
            "classic": {"value": 0.9, "interval_iqr": {"lower": 0.75, "upper": 0.98}},
            "body": {"value": 0.7, "interval_iqr": {"lower": 0.5, "upper": 0.85}},
            "tannin": {"value": 0.7, "interval_iqr": {"lower": 0.5, "upper": 0.85}},
        },
        "notes": notes,
        "metadata": {},
    }


def experience_enrichment_payload(notes: str) -> dict[str, Any]:
    return {
        "attributes": {
            "novelty": {"value": 0.6, "interval_iqr": {"lower": 0.3, "upper": 0.8}},
        },
        "notes": notes,
        "metadata": {},
    }


def restaurant_enrichment_payload(notes: str) -> dict[str, Any]:
    return {
        "attributes": {
            "casual": {
                "value": 0.8,
                "interval_iqr": {"lower": 0.6, "upper": 0.9},
            },
        },
        "notes": notes,
        "metadata": {
            "cuisine": {},
            "michelin": {
                "status": "unknown",
                "stars": None,
                "green_star": False,
                "source_url": None,
                "source": None,
                "checked_at": None,
            },
            "google": {
                "rating": None,
                "rating_count": None,
                "source_url": None,
                "source": None,
                "checked_at": None,
            },
        },
    }


def table_count(settings: Settings, table: Any) -> int:
    store = BrainStore(settings)
    if table.name not in set(inspect(store.engine).get_table_names()):
        return 0
    with store.engine.begin() as conn:
        return conn.execute(select(func.count()).select_from(table)).scalar_one()


def assert_table_absent(settings: Settings, table_name: str) -> None:
    store = BrainStore(settings)
    assert table_name not in set(inspect(store.engine).get_table_names())


def assert_legacy_semantic_counts(settings: Settings) -> None:
    for table_name in ("memory_cards", "relationships", "open_loops", "cognee_sync", "sources"):
        assert_table_absent(settings, table_name)
    assert table_count(settings, schema.entities) == 0


def fake_cognee(calls: list[dict[str, Any]]):
    def remember_text(
        text: str,
        *,
        dataset_name: str,
        node_set: list[str] | None = None,
        settings: Settings | None = None,
    ) -> dict[str, str]:
        del text, settings
        calls.append({"dataset_name": dataset_name, "node_set": node_set or []})
        return {"id": f"fake-{len(calls)}"}

    return remember_text


def brain_test_settings(tmp_path, **overrides: Any) -> Settings:
    values = {
        "brain_database_url": f"sqlite:///{tmp_path / 'brain.db'}",
        "brain_taste_omdb_api_key": None,
        **overrides,
    }
    return Settings(
        **values,
    )


def make_taste_service(settings: Settings) -> TasteService:
    return TasteService(
        settings,
        canonical_store=CogneePalateStore(
            settings,
            adapter=InMemoryPalateCogneeAdapter(settings.brain_cognee_palate_dataset),
        ),
    )


def patch_default_palate_store(monkeypatch: pytest.MonkeyPatch, settings: Settings) -> CogneePalateStore:
    store = CogneePalateStore(
        settings,
        adapter=InMemoryPalateCogneeAdapter(settings.brain_cognee_palate_dataset),
    )
    monkeypatch.setattr("memory_stack.taste.service.CogneePalateStore", lambda _: store)
    monkeypatch.setattr(brain_service, "CogneePalateStore", lambda _: store)
    return store
