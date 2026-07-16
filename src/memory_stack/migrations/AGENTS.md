# Purpose

- Own Alembic migration environment and versioned Brain DB schema migrations.

## Ownership

- `env.py` and `script.py.mako` own migration runtime behavior.
- `versions/` owns ordered Brain DB migrations.
- `README.md` owns the local migration contract.

## Local Contracts

- Brain DB is the source of truth for control records; migrations must preserve Brain IDs, user scope, receipts, confirmations, audit records, and lifecycle state.
- Cognee data is rebuildable from Brain tables and should not force irreversible Brain DB assumptions.
- Do not edit already-applied migration semantics casually; add a new migration for schema evolution.

## Work Guidance

- Keep migrations deterministic and compatible with the configured SQLAlchemy/Alembic stack.
- Update model/store code and migration tests with every schema change.

## Verification

- Run `uv run pytest tests/test_migrations.py` after migration changes.
- Run `uv run alembic upgrade head` when a real database verification is relevant.

## Child DOX Index

- No child AGENTS.md files. `versions/` is owned here.
