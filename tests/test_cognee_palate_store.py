from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import inspect

from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings
from memory_stack.taste.cognee_store import (
    CogneePalateStore,
    InMemoryPalateCogneeAdapter,
    PalateItemDataPoint,
    _to_live_datapoint,
)
from memory_stack.taste.models import TasteQueryRequest, TasteRefreshRequest, TasteRememberRequest
from memory_stack.taste.ranking import rank_candidates, retrieve_candidates
from memory_stack.taste.service import TasteService


class FakeCogneeDataPoint(BaseModel):
    metadata: dict[str, Any] = Field(default_factory=dict)


def test_live_palate_datapoint_overrides_metadata_with_annotation() -> None:
    point = PalateItemDataPoint(
        id="item_1",
        type="wine",
        canonical_name="Annotated Rioja",
        normalized_name="annotated rioja",
    )

    live_point = _to_live_datapoint(FakeCogneeDataPoint, point, "palate_test")

    assert live_point.metadata == {
        "index_fields": ["canonical_name", "notes", "attributes_summary", "signals_summary"]
    }
    assert live_point.external_id == "item_1"


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
            "attribute_intervals_iqr": {"oak": {"lower": 0.8, "upper": 0.95}},
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
    assert store.get_item(alpha["id"])["attribute_intervals_iqr"]["oak"]["upper"] == 0.95
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
    assert store.prune_deleted_items() == 1
    assert store.get_item(item["id"], include_deleted=True) is None


def test_taste_service_uses_cognee_as_canonical_store_without_sqlite_items(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
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

    store = BrainStore(settings)

    assert canonical.get_item(record["id"])["canonical_name"] == "Service Rioja"
    assert "taste_items" not in set(inspect(store.engine).get_table_names())
    assert_legacy_semantic_tables_absent(store)
    assert record["metadata"]["brain_db_semantic_rows_written"] is False
    assert "evidence_memory_id" not in record
    assert result["ranked_results"][0]["id"] == record["id"]


def test_taste_service_refresh_enrichment_keeps_material_changes_in_cognee_only(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    canonical = CogneePalateStore(settings, adapter=InMemoryPalateCogneeAdapter("palate_test"))
    service = TasteService(settings, canonical_store=canonical)
    record = service.remember(
        TasteRememberRequest(
            type="wine",
            canonical_name="Refresh Rioja",
            description="I want to try Refresh Rioja.",
            wanted=True,
            metadata={"producer": "Old"},
            fetch_external_ratings=False,
        )
    )["taste_records"][0]

    refreshed = service.refresh_enrichment(TasteRefreshRequest(taste_item_id=record["id"]))

    assert refreshed["refreshed"] is True
    assert refreshed["material_memory_id"] is None
    assert refreshed["brain_db_semantic_rows_written"] is False
    assert_legacy_semantic_tables_absent(BrainStore(settings))


def assert_legacy_semantic_tables_absent(store: BrainStore) -> None:
    tables = set(inspect(store.engine).get_table_names())
    assert not {"memory_cards", "relationships", "open_loops", "cognee_sync", "sources"} & tables


def brain_test_settings(tmp_path, **overrides: Any) -> Settings:
    return Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        brain_taste_omdb_api_key=None,
        **overrides,
    )
