# Purpose

- Own non-secret Brain and Cognee configuration profiles for local dev, QA, staging, and production.

## Ownership

- `common.yaml` is the shared default profile.
- `dev.yaml`, `qa.yaml`, `staging.yaml`, and `prod.yaml` are environment-specific overlays.

## Local Contracts

- Do not commit real secrets, tokens, passwords, provider auth state, or private endpoint credentials.
- Keep config keys aligned with `src/memory_stack/cfg.py`, `scripts/render_prod_env.py`, deployment workflows, and docs.
- Config paths should be explicit about runtime data roots and must not blur tracked source with `.data/`, `secrets/`, or production shared data.

## Work Guidance

- Prefer adding new settings to `common.yaml` first, then override only where an environment genuinely differs.
- Use example or placeholder values for credentials.

## Verification

- Run `make check` for configuration sanity.
- For config schema or render changes, run `uv run pytest tests/test_cfg.py tests/test_config.py tests/test_render_prod_env.py`.

## Child DOX Index

- No child AGENTS.md files. All `cfg/` profiles are owned here.
