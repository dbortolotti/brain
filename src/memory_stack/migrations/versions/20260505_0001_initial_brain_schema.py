"""initial Brain schema

Revision ID: 20260505_0001
Revises:
Create Date: 2026-05-05 00:00:00
"""
from __future__ import annotations

from alembic import op

from memory_stack.brain_schema import metadata


revision = "20260505_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    metadata.create_all(op.get_bind())


def downgrade() -> None:
    metadata.drop_all(op.get_bind())
