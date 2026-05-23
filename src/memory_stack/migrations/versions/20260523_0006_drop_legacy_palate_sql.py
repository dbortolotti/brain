"""drop legacy SQL palate canonical tables

Revision ID: 20260523_0006
Revises: 20260521_0005
Create Date: 2026-05-23 00:00:00
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import inspect


revision = "20260523_0006"
down_revision = "20260521_0005"
branch_labels = None
depends_on = None


LEGACY_PALATE_TABLES = (
    "taste_decisions",
    "taste_signals",
    "taste_attributes",
    "taste_items",
)


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(inspect(bind).get_table_names())
    for table_name in LEGACY_PALATE_TABLES:
        if table_name in existing:
            op.drop_table(table_name)


def downgrade() -> None:
    # Approved palate items and decisions are canonical in Cognee. The old SQL
    # tables are intentionally not recreated on downgrade.
    return None
