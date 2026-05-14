from __future__ import annotations

from typing import Any

from sqlalchemy import func, select

from memory_stack import brain_schema as schema
from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings
from memory_stack.taste.cognee_store import CogneePalateStore, InMemoryPalateCogneeAdapter
from memory_stack.taste.models import TasteQueryRequest, TasteRememberRequest
from memory_stack.taste.ranking import rank_candidates, retrieve_candidates
from memory_stack.taste.service import TasteService


def test_cognee_palate_store_keeps_structured_items_and_decision_feedback(tmp_path) -> None:
    store = CogneePalateStore(
        brain_test_settings(tmp_path),
        adapter=InMemoryPalateCogneeAdapter("palate_test"),
    )

    alpha, created = store.upsert_item(
        {
            "type": "wine",
            "canonical_name": "Alpha Rioja",
            "brain_entity_id": "ent_alpha",
            "attributes": {"oak": 0.9},
            "attribute_intervals_95": {"oak": {"lower": 0.8, "upper": 0.95}},
            "signals": [{"type": "wanted_to_try", "value": True}],
        }
    )
    beta, _ = store.upsert_item(
        {
            "type": "wine",
            "canonical_name": "Beta Musar",
            "brain_entity_id": "ent_beta",
            "attributes": {"oak": 0.3},
            "signals": [{"type": "wanted_to_try", "value": True}],
        }
    )

    decision_id = store.log_decision(
        query="suggest an oaky wine",
        context={},
        options=[],
        ranked=[
            {"id": alpha["id"], "name": alpha["canonical_name"], "score": 1.0},
            {"id": beta["id"], "name": beta["canonical_name"], "score": 0.5},
        ],
    )
    assert store.update_decision_choice(decision_id, alpha["id"]) == 1

    retrieval = retrieve_candidates(
        store,
        {
            "entity_type": "wine",
            "attributes": ["oak"],
            "context": {},
            "filters": {},
            "search_text": "rioja oaky",
        },
    )
    feedback = store.decision_feedback("suggest an oaky wine tonight", [alpha["id"], beta["id"]])
    ranked = rank_candidates(retrieval["candidates"], {"attributes": ["oak"], "context": {}, "filters": {}})

    assert created is True
    assert store.get_item(alpha["id"])["attribute_intervals_95"]["oak"]["upper"] == 0.95
    assert feedback[alpha["id"]]["chosen"] == 1
    assert feedback[beta["id"]]["rejected"] == 1
    assert ranked[0]["entity"]["id"] == alpha["id"]


def test_cognee_palate_store_soft_delete_removes_current_item(tmp_path) -> None:
    store = CogneePalateStore(
        brain_test_settings(tmp_path),
        adapter=InMemoryPalateCogneeAdapter("palate_test"),
    )
    item, _ = store.upsert_item(
        {
            "type": "restaurant",
            "canonical_name": "Delete Cafe",
            "brain_entity_id": "ent_delete",
            "signals": [{"type": "wanted_to_try", "value": True}],
        }
    )

    assert store.soft_delete_item(item["id"]) is True
    assert store.get_item(item["id"]) is None
    assert store.get_item(item["id"], include_deleted=True)["status"] == "deleted"
    assert store.list_entities() == []


def test_taste_service_can_use_cognee_as_canonical_store_without_sqlite_items(tmp_path) -> None:
    settings = brain_test_settings(tmp_path, brain_taste_canonical_store="cognee")
    canonical = CogneePalateStore(settings, adapter=InMemoryPalateCogneeAdapter("palate_test"))
    service = TasteService(settings, canonical_store=canonical)

    record = service.remember(
        TasteRememberRequest(
            type="wine",
            canonical_name="Service Rioja",
            description="I want to try Service Rioja.",
            wanted=True,
            attributes={"oak": 0.85},
            fetch_external_ratings=False,
        )
    )["taste_records"][0]
    result = service.query(
        TasteQueryRequest(
            query="suggest an oaky wine I said I want to try",
            intent={
                "intent": "hybrid_query",
                "entity_type": "wine",
                "attributes": ["oak"],
                "context": {},
                "filters": {},
            },
        )
    )

    with BrainStore(settings).engine.begin() as conn:
        sqlite_item_count = conn.execute(select(func.count()).select_from(schema.taste_items)).scalar_one()

    assert canonical.get_item(record["id"])["canonical_name"] == "Service Rioja"
    assert sqlite_item_count == 0
    assert result["ranked_results"][0]["id"] == record["id"]


def brain_test_settings(tmp_path, **overrides: Any) -> Settings:
    return Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_taste_omdb_api_key=None,
        **overrides,
    )
