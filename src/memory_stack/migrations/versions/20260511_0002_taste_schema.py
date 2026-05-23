"""add Brain-managed taste schema

Revision ID: 20260511_0002
Revises: 20260505_0001
Create Date: 2026-05-11 00:00:00
"""
from __future__ import annotations

from alembic import op

from memory_stack import brain_schema as schema


revision = "20260511_0002"
down_revision = "20260505_0001"
branch_labels = None
depends_on = None


TASTE_TABLES = (
    schema.taste_proposals,
)


def upgrade() -> None:
    bind = op.get_bind()
    for table in TASTE_TABLES:
        table.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for table in reversed(TASTE_TABLES):
        table.drop(bind=bind, checkfirst=True)
