# Purpose

- Own Cognee-specific datapoint shaping, compatibility helpers, and capability probes.

## Ownership

- `datapoints.py` owns node-set and datapoint text construction for Brain writes.
- `oauth_compat.py` owns compatibility behavior needed for Cognee OAuth or auth integration.
- `palate_capability_probe.py` owns Palate/Cognee capability probing.

## Local Contracts

- Cognee data can be rebuilt from Brain control records; do not make Cognee-only writes the canonical source for Brain control state.
- Preserve user, profile, surface, and session scoping in datapoints.
- Probe code must avoid persisting private payloads beyond its explicit test or diagnostic purpose.

## Work Guidance

- Keep datapoint formats stable unless migrations, recall, and docs are updated together.
- Prefer explicit node-set construction over ad hoc metadata assembly in callers.

## Verification

- Run targeted Cognee tests, commonly `uv run pytest tests/test_cognee_oauth_compat.py tests/test_cognee_projection.py tests/test_cognee_palate_store.py`.
- Run `uv run pytest tests/test_palate_cognee_capability_probe.py` after capability-probe changes.

## Child DOX Index

- No child AGENTS.md files. All Cognee helpers are owned here.
