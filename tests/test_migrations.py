from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from memory_stack.brain_store import BrainStore
from memory_stack.config import Settings


def test_alembic_upgrade_creates_fresh_brain_schema(tmp_path) -> None:
    db_path = tmp_path / "brain.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{db_path}", future=True)
    tables = set(inspect(engine).get_table_names())
    assert {
        "memory_cards",
        "sources",
        "entities",
        "relationships",
        "open_loops",
        "cognee_sync",
        "ingestion_runs",
    } <= tables


def test_brain_store_initializes_clean_sqlite_db(tmp_path) -> None:
    db_path = tmp_path / "brain.db"

    BrainStore(Settings(brain_database_url=f"sqlite:///{db_path}"))

    assert Path(db_path).exists()
