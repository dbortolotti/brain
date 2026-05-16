from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings


def test_alembic_upgrade_creates_fresh_brain_schema(tmp_path) -> None:
    db_path = tmp_path / "brain.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{db_path}", future=True)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert {
        "memory_cards",
        "brain_users",
        "sources",
        "entities",
        "relationships",
        "open_loops",
        "cognee_sync",
        "ingestion_runs",
        "taste_items",
        "taste_attributes",
        "taste_signals",
        "taste_decisions",
        "taste_proposals",
        "app_write_audit",
    } <= tables
    proposal_columns = {
        column["name"]: column for column in inspector.get_columns("taste_proposals")
    }
    taste_item_checks = {
        constraint["name"] for constraint in inspector.get_check_constraints("taste_items")
    }
    taste_signal_checks = {
        constraint["name"] for constraint in inspector.get_check_constraints("taste_signals")
    }
    proposal_checks = {
        constraint["name"] for constraint in inspector.get_check_constraints("taste_proposals")
    }
    assert proposal_columns["expires_at"]["nullable"] is False
    assert "taste_items_type_ck" in taste_item_checks
    assert "taste_items_status_ck" in taste_item_checks
    assert "taste_signals_type_ck" in taste_signal_checks
    assert "taste_proposals_status_ck" in proposal_checks
    for table_name in ("memory_cards", "sources", "entities", "taste_items", "app_write_audit"):
        columns = {column["name"] for column in inspector.get_columns(table_name)}
        assert "user_id" in columns


def test_brain_store_initializes_clean_sqlite_db(tmp_path) -> None:
    db_path = tmp_path / "brain.db"

    BrainStore(Settings(brain_database_url=f"sqlite:///{db_path}"))

    assert Path(db_path).exists()
