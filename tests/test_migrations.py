from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings


def test_alembic_upgrade_creates_fresh_brain_schema(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("BRAIN_DATABASE_URL", raising=False)
    db_path = tmp_path / "brain.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{db_path}", future=True)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert {
        "brain_users",
        "entities",
        "taste_proposals",
        "brain_session_maps",
        "brain_external_receipts",
        "brain_pending_confirmations",
        "brain_context_records",
    } <= tables
    assert not {
        "memory_cards",
        "sources",
        "relationships",
        "open_loops",
        "cognee_sync",
        "ingestion_runs",
        "recall_logs",
        "taste_items",
        "taste_attributes",
        "taste_signals",
        "taste_decisions",
    } & tables
    proposal_columns = {
        column["name"]: column for column in inspector.get_columns("taste_proposals")
    }
    proposal_checks = {
        constraint["name"] for constraint in inspector.get_check_constraints("taste_proposals")
    }
    assert proposal_columns["expires_at"]["nullable"] is False
    assert "taste_proposals_status_ck" in proposal_checks
    for table_name in ("entities",):
        columns = {column["name"] for column in inspector.get_columns(table_name)}
        assert "user_id" in columns
    for table_name in (
        "brain_session_maps",
        "brain_external_receipts",
        "brain_pending_confirmations",
        "brain_context_records",
    ):
        columns = {column["name"] for column in inspector.get_columns(table_name)}
        assert "user_id" in columns
    session_indexes = {
        index["name"] for index in inspector.get_indexes("brain_session_maps")
    }
    context_checks = {
        constraint["name"]
        for constraint in inspector.get_check_constraints("brain_context_records")
    }
    assert "brain_session_maps_user_last_used_idx" in session_indexes
    assert "brain_context_records_kind_ck" in context_checks


def test_brain_store_initializes_clean_sqlite_db(tmp_path) -> None:
    db_path = tmp_path / "brain.db"

    BrainStore(Settings(brain_database_url=f"sqlite:///{db_path}"))

    assert Path(db_path).exists()
