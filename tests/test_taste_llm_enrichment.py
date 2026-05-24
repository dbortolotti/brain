from __future__ import annotations

from typing import Any

from memory_stack.cfg import Settings
from memory_stack.llm.fake import FakeLLMClient
from memory_stack.taste.llm_enrichment import enrichment_schema_for_type
from memory_stack.taste.models import TasteDescribeRequest, TasteRememberRequest
from memory_stack.taste.schema import attribute_keys_for_type
from memory_stack.taste.cognee_store import CogneePalateStore, InMemoryPalateCogneeAdapter
from memory_stack.taste.service import TasteService


def test_llm_enrichment_uses_type_specific_schema() -> None:
    schema = enrichment_schema_for_type("wine")
    wine_attributes = attribute_keys_for_type("wine")

    assert schema["properties"]["attributes"]["required"] == wine_attributes
    assert "oak" in schema["properties"]["attributes"]["properties"]
    assert "quiet" not in schema["properties"]["attributes"]["properties"]
    assert schema["properties"]["metadata"]["required"] == []


def test_taste_describe_uses_llm_enrichment_when_attributes_are_missing(tmp_path) -> None:
    llm_client = FakeLLMClient(
        {
            "attributes": {
                "oak": {"value": 0.8, "interval_iqr": {"lower": 0.7, "upper": 0.9}},
                "body": {"value": 0.7, "interval_iqr": {"lower": 0.5, "upper": 0.85}},
            },
            "notes": "Full-bodied oaky Cabernet.",
            "metadata": {},
        }
    )
    settings = brain_test_settings(tmp_path, brain_taste_web_enrichment_enabled=False)
    service = TasteService(
        settings,
        llm_client=llm_client,
        canonical_store=memory_palate_store(settings),
    )

    result = service.describe_item(
        TasteDescribeRequest(
            item_text="Ridge Estate Cabernet 2019, full-bodied and oaky",
            entity_type="wine",
            canonical_name="Ridge Estate Cabernet 2019",
            fetch_external_ratings=False,
        )
    )

    enriched = result["enriched"]
    assert result["server_llm_used"]["enrichment"] is True
    assert enriched["attributes"] == {"oak": 0.8, "body": 0.7}
    assert enriched["attribute_intervals_iqr"]["oak"] == {"lower": 0.7, "upper": 0.9}
    assert enriched["notes"] == "Full-bodied oaky Cabernet."
    assert enriched["enrichment_metadata"]["normalized_fields_source"] == "llm"
    assert llm_client.calls[0]["schema"]["properties"]["attributes"]["required"] == (
        attribute_keys_for_type("wine")
    )
    assert llm_client.calls[0]["kwargs"]["model"] == "gpt-5.5"
    assert llm_client.calls[0]["kwargs"]["reasoning_effort"] == "medium"


def test_client_attributes_skip_llm_enrichment(tmp_path) -> None:
    llm_client = FakeLLMClient(
        {
            "attributes": {
                "oak": {"value": 0.1, "interval_iqr": {"lower": 0.0, "upper": 0.2}},
            },
            "notes": "Should not be used.",
            "metadata": {},
        }
    )
    settings = brain_test_settings(tmp_path, brain_taste_web_enrichment_enabled=False)
    service = TasteService(settings, llm_client=llm_client, canonical_store=memory_palate_store(settings))

    result = service.remember(
        TasteRememberRequest(
            type="wine",
            canonical_name="Manual Wine",
            description="Manual Wine",
            attributes={"oak": 0.9},
            fetch_external_ratings=False,
        )
    )

    assert result["server_llm_used"]["enrichment"] is False
    assert result["taste_records"][0]["attributes"] == {"oak": 0.9}
    assert llm_client.calls == []


def test_llm_music_metadata_is_normalized_and_stored(tmp_path) -> None:
    llm_client = FakeLLMClient(
        {
            "attributes": {
                "intellectual": {
                    "value": 0.8,
                    "interval_iqr": {"lower": 0.6, "upper": 0.9},
                },
            },
            "notes": "Modal jazz record.",
            "metadata": {
                "artist": "Miles Davis",
                "album": "Kind of Blue",
                "personnel": ["John Coltrane"],
                "genre": ["bebop"],
            },
        }
    )
    settings = brain_test_settings(tmp_path, brain_taste_web_enrichment_enabled=False)
    service = TasteService(settings, llm_client=llm_client, canonical_store=memory_palate_store(settings))

    result = service.remember(
        TasteRememberRequest(
            type="music",
            canonical_name="Kind of Blue",
            description="Miles Davis Kind of Blue, cerebral modal jazz",
            fetch_external_ratings=False,
        )
    )

    metadata = result["taste_records"][0]["metadata"]
    assert result["server_llm_used"]["enrichment"] is True
    assert result["taste_records"][0]["attributes"] == {"intellectual": 0.8}
    assert metadata["artist"] == "Miles Davis"
    assert metadata["album"] == "Kind of Blue"
    assert metadata["personnel"] == ["John Coltrane"]
    assert metadata["genre"] == ["jazz"]


def test_restaurant_llm_enrichment_uses_web_search_schema(tmp_path) -> None:
    llm_client = FakeLLMClient(
        {
            "attributes": {
                "quiet": {
                    "value": 0.6,
                    "interval_iqr": {"lower": 0.3, "upper": 0.8},
                },
            },
            "notes": "Wine-focused restaurant.",
            "metadata": {
                "cuisine": {
                    "cocktail_bar_drinks": {
                        "value": 0.8,
                        "interval_iqr": {"lower": 0.6, "upper": 0.9},
                    }
                },
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
    )
    settings = brain_test_settings(tmp_path, brain_taste_web_enrichment_enabled=False)
    service = TasteService(settings, llm_client=llm_client, canonical_store=memory_palate_store(settings))

    result = service.describe_item(
        TasteDescribeRequest(
            item_text="Noble Rot",
            entity_type="restaurant",
            canonical_name="Noble Rot",
            fetch_external_ratings=True,
        )
    )

    call = llm_client.calls[0]
    assert result["server_llm_used"]["enrichment"] is True
    assert call["kwargs"]["model"] == "gpt-5.5"
    assert call["kwargs"]["reasoning_effort"] == "medium"
    assert call["kwargs"]["tools"][0]["type"] == "web_search"
    assert call["kwargs"]["schema_name"] == "brain_restaurant_web_enrichment"
    assert call["schema"]["properties"]["attributes"]["properties"]["quiet"]["required"] == [
        "value",
        "interval_iqr",
    ]
    assert result["enriched"]["attributes"] == {"quiet": 0.6}
    assert "cocktail_bar_drinks" in result["enriched"]["normalized_metadata"]["cuisine"]


def brain_test_settings(tmp_path, **overrides: Any) -> Settings:
    return Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_taste_omdb_api_key=None,
        **overrides,
    )


def memory_palate_store(settings: Settings) -> CogneePalateStore:
    return CogneePalateStore(
        settings,
        adapter=InMemoryPalateCogneeAdapter(settings.brain_cognee_palate_dataset),
    )
