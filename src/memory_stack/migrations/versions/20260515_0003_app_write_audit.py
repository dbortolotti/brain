"""add app write audit table

Revision ID: 20260515_0003
Revises: 20260511_0002
Create Date: 2026-05-15 00:00:00
"""
from __future__ import annotations

from alembic import op

from memory_stack import brain_schema as schema


revision = "20260515_0003"
down_revision = "20260511_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema.app_write_audit.create(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    schema.app_write_audit.drop(bind=op.get_bind(), checkfirst=True)
