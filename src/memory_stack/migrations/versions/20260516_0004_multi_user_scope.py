"""add user scope columns

Revision ID: 20260516_0004
Revises: 20260515_0003
Create Date: 2026-05-16 00:00:00
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import Column, Text, inspect, text

from memory_stack import brain_schema as schema


revision = "20260516_0004"
down_revision = "20260515_0003"
branch_labels = None
depends_on = None


USER_TABLES = (
    "sources",
    "memory_cards",
    "entities",
    "entity_aliases",
    "memory_entities",
    "relationships",
    "memory_links",
    "open_loops",
    "cognee_sync",
    "ingestion_runs",
    "recall_logs",
    "app_write_audit",
    "taste_items",
    "taste_attributes",
    "taste_signals",
    "taste_decisions",
    "taste_proposals",
)


def upgrade() -> None:
    bind = op.get_bind()
    schema.brain_users.create(bind=bind, checkfirst=True)
    if bind.dialect.name == "postgresql":
        bind.execute(
            text(
                """
                INSERT INTO brain_users
                    (id, display_name, status, metadata_json)
                VALUES
                    ('default', 'Default Brain user', 'active', '{}')
                ON CONFLICT (id) DO NOTHING
                """
            )
        )
    else:
        bind.execute(
            text(
                """
                INSERT OR IGNORE INTO brain_users
                    (id, display_name, status, metadata_json)
                VALUES
                    ('default', 'Default Brain user', 'active', '{}')
                """
            )
        )
    inspector = inspect(bind)
    for table_name in USER_TABLES:
        if table_name not in inspector.get_table_names():
            continue
        columns = {column["name"] for column in inspector.get_columns(table_name)}
        if "user_id" not in columns:
            op.add_column(
                table_name,
                Column("user_id", Text(), server_default="default", nullable=False),
            )
    _create_index_if_missing("brain_users_status_idx", "brain_users", ["status"])
    _create_index_if_missing("sources_user_created_idx", "sources", ["user_id", "created_at"])
    _create_index_if_missing("memory_cards_user_created_idx", "memory_cards", ["user_id", "created_at"])
    _create_index_if_missing("entities_user_name_idx", "entities", ["user_id", "type", "normalized_name"])
    _create_index_if_missing("entity_aliases_user_alias_idx", "entity_aliases", ["user_id", "normalized_alias"])
    _create_index_if_missing("relationships_user_status_idx", "relationships", ["user_id", "status"])
    _create_index_if_missing("memory_links_user_relation_idx", "memory_links", ["user_id", "relation"])
    _create_index_if_missing("open_loops_user_status_idx", "open_loops", ["user_id", "status"])
    _create_index_if_missing("ingestion_runs_user_started_idx", "ingestion_runs", ["user_id", "started_at"])
    _create_index_if_missing("app_write_audit_user_created_idx", "app_write_audit", ["user_id", "created_at"])
    _create_index_if_missing("taste_items_user_name_idx", "taste_items", ["user_id", "type", "normalized_name"])


def downgrade() -> None:
    # SQLite cannot reliably drop columns without table rebuilds. Keep user_id
    # columns in place on downgrade and remove only the registry table.
    schema.brain_users.drop(bind=op.get_bind(), checkfirst=True)


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str]) -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if table_name not in inspector.get_table_names():
        return
    existing = {index["name"] for index in inspector.get_indexes(table_name)}
    if index_name in existing:
        return
    table_columns = {column["name"] for column in inspector.get_columns(table_name)}
    if not set(columns) <= table_columns:
        return
    op.create_index(index_name, table_name, columns)
