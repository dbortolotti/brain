"""add Brain control-store tables

Revision ID: 20260521_0005
Revises: 20260516_0004
Create Date: 2026-05-21 00:00:00
"""
from __future__ import annotations

from alembic import op

from memory_stack import brain_schema as schema


revision = "20260521_0005"
down_revision = "20260516_0004"
branch_labels = None
depends_on = None


CONTROL_TABLES = (
    schema.brain_session_maps,
    schema.brain_external_receipts,
    schema.brain_pending_confirmations,
    schema.brain_context_records,
)


def upgrade() -> None:
    bind = op.get_bind()
    for table in CONTROL_TABLES:
        table.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for table in reversed(CONTROL_TABLES):
        table.drop(bind=bind, checkfirst=True)
