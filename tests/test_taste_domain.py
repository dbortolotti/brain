from __future__ import annotations

from typing import Any

import pytest

from memory_stack.cfg import Settings
from memory_stack.taste.media import (
    normalize_media_metadata,
    normalize_music_metadata,
    normalize_restaurant_metadata,
)
from memory_stack.taste.models import TasteLogDecisionRequest, TasteRememberRequest
from memory_stack.taste.omdb import omdb_payload_to_metadata
from memory_stack.taste.ranking import rank_candidates
from memory_stack.taste.schema import invalid_attribute_keys
from memory_stack.taste.cognee_store import CogneePalateStore, InMemoryPalateCogneeAdapter
from memory_stack.taste.service import TasteService


def test_strict_attribute_schema_rejects_cross_category_keys() -> None:
    assert invalid_attribute_keys("wine", {"oak": 0.8, "quiet": 0.5}) == ["quiet"]
    assert invalid_attribute_keys("movie", {"slow_burn": 0.7, "oak": 0.2}) == ["oak"]


def test_media_music_and_restaurant_metadata_normalization() -> None:
    media = normalize_media_metadata(
        {
            "genre": ["Science Fiction", "Rom-Com"],
            "runtime": "109 min",
            "watched": "yes",
            "external_ratings": {"imdb": {"rating": "7.2", "votes": "1,234"}},
        }
    )
    music = normalize_music_metadata(
        {"genre": ["bebop", "hiphop"], "personnel": "Miles Davis, Bill Evans"}
    )
    restaurant = normalize_restaurant_metadata(
        {
            "genre": ["Sushi", "Cocktail Bar"],
            "michelin_status": "bib",
            "google_rating": "4.6",
            "google_rating_count": "123",
            "google_url": "https://maps.google.com/example",
        }
    )

    assert media["genre"] == ["sci_fi", "comedy"]
    assert media["runtime"] == 109
    assert media["watched"] is True
    assert media["external_ratings"]["imdb"] == {"rating": 7.2, "votes": 1234}
    assert music["genre"] == ["jazz", "hip_hop"]
    assert music["personnel"] == ["Miles Davis", "Bill Evans"]
    assert set(restaurant["cuisine"]) == {"japanese", "cocktail_bar_drinks"}
    assert restaurant["michelin"]["status"] == "bib_gourmand"
    assert restaurant["google"]["rating"] == 4.6
    assert restaurant["google"]["rating_count"] == 123
    assert restaurant["google"]["source"] == "google"


def test_omdb_payload_maps_external_ids_ratings_and_genres() -> None:
    metadata = omdb_payload_to_metadata(
        {
            "Plot": "A test film.",
            "Actors": "Alice Example, Bob Example",
            "Director": "Dana Director",
            "Country": "USA, UK",
            "Language": "English",
            "Genre": "Sci-Fi, Thriller",
            "Runtime": "109 min",
            "imdbID": "tt1234567",
            "imdbRating": "7.2",
            "imdbVotes": "168,584",
            "Ratings": [{"Source": "Rotten Tomatoes", "Value": "89%"}],
        }
    )

    assert metadata["external_ids"]["imdb_id"] == "tt1234567"
    assert metadata["external_ratings"]["imdb"] == {"rating": 7.2, "votes": 168584}
    assert metadata["external_ratings"]["rotten_tomatoes"]["critic_score"] == 89
    assert metadata["ratings_source"]["provider"] == "omdb"
    assert metadata["genre"] == ["sci_fi", "thriller"]
    assert metadata["runtime"] == 109
    assert metadata["main_actors"] == ["Alice Example", "Bob Example"]


def test_ranking_uses_latest_rating_and_excludes_negative_signals() -> None:
    latest_rating = {
        "id": "taste_latest",
        "type": "wine",
        "canonical_name": "Latest Rating Wine",
        "attributes": {},
        "signals": [
            {"type": "rating", "value": 9},
            {"type": "rating", "value": 2},
        ],
    }
    avoided = {
        "id": "taste_avoid",
        "type": "wine",
        "canonical_name": "Avoid Wine",
        "attributes": {},
        "signals": [{"type": "avoid", "value": True}],
    }

    ranked = rank_candidates(
        [avoided, latest_rating],
        {
            "filters": {"min_rating": 5},
            "attributes": [],
            "context": {},
            "search_text": "",
        },
    )

    assert [result["entity"]["id"] for result in ranked] == ["taste_latest"]
    assert "rating 9/10" in ranked[0]["facts"]["signal_facts"]


def test_decision_feedback_records_chosen_and_rejected_options(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    service = make_taste_service(settings)
    alpha = remember_wine(service, "Alpha Wine", rating=7)
    beta = remember_wine(service, "Beta Wine", rating=8)
    gamma = remember_wine(service, "Gamma Wine", rating=6)

    decision_id = service.canonical_store.log_decision(
        query="Which wine should I choose?",
        context={},
        options=[],
        ranked=[
            {"id": alpha["id"], "name": "Alpha Wine", "score": 1.0},
            {"id": beta["id"], "name": "Beta Wine", "score": 0.9},
            {"id": gamma["id"], "name": "Gamma Wine", "score": 0.8},
        ],
    )
    logged = service.log_decision(
        TasteLogDecisionRequest(decision_id=decision_id, chosen_taste_item_id=beta["id"])
    )

    feedback = service.canonical_store.decision_feedback(
        "Which wine should I choose tonight?",
        [alpha["id"], beta["id"], gamma["id"]],
    )

    assert logged["logged"] is True
    assert feedback[beta["id"]]["chosen"] == 1
    assert feedback[alpha["id"]]["rejected"] == 1
    assert feedback[gamma["id"]]["rejected"] == 1


def test_soft_and_hard_delete_palate_items(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    service = make_taste_service(settings)
    record = remember_wine(service, "Delete Me Wine", rating=5)
    store = service.canonical_store

    assert store.soft_delete_item(record["id"]) is True
    assert store.get_item(record["id"]) is None
    deleted = store.get_item(record["id"], include_deleted=True)
    assert deleted is not None
    assert deleted["status"] == "deleted"

    with pytest.raises(ValueError, match="confirm=True"):
        store.hard_delete_item(record["id"])
    assert store.hard_delete_item(record["id"], confirm=True) is True
    assert store.get_item(record["id"], include_deleted=True)["status"] == "deleted"


def test_store_rejects_unknown_taste_signal_types(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    service = make_taste_service(settings)
    record = remember_wine(service, "Signal Wine", rating=5)

    with pytest.raises(ValueError, match="signal_type must be one of"):
        service.canonical_store.add_signal(record["id"], "saved", True)


def remember_wine(
    service: TasteService,
    canonical_name: str,
    *,
    rating: float,
) -> dict[str, Any]:
    return service.remember(
        TasteRememberRequest(
            type="wine",
            canonical_name=canonical_name,
            description=f"{canonical_name} is rated {rating:g}/10.",
            rating=rating,
            fetch_external_ratings=False,
        )
    )["taste_records"][0]


def brain_test_settings(tmp_path, **overrides: Any) -> Settings:
    return Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_taste_omdb_api_key=None,
        **overrides,
    )


def make_taste_service(settings: Settings) -> TasteService:
    return TasteService(
        settings,
        canonical_store=CogneePalateStore(
            settings,
            adapter=InMemoryPalateCogneeAdapter(settings.brain_cognee_palate_dataset),
        ),
    )
