# Purpose

- Own Brain Palate and taste functionality: domain schemas, models, routing, enrichment, recommendations, proposal workflow, and Cognee-backed taste persistence.

## Ownership

- `service.py` owns the Palate service workflow.
- `models.py` and `schema.py` own request/response and domain schema contracts.
- `routing.py`, `enrichment.py`, and `llm_enrichment.py` own classification and enrichment behavior.
- `ranking.py`, `option_matching.py`, `media.py`, `restaurants.py`, and `omdb.py` own recommendation support.
- `store.py` and `cognee_store.py` own proposal and canonical taste storage.
- `evals/` owns taste-specific eval cases and runner.

## Local Contracts

- Palate writes are durable taste signals and must preserve confirmation thresholds, proposal expiry, enrichment status, and user scope.
- Read-only describe/enrichment paths must not store memories.
- Cognee-backed taste records are the canonical semantic store, with Brain control projections recorded where required.
- External enrichment must not require secrets in source and must make provider use explicit through settings.

## Work Guidance

- Keep routing, enrichment, and ranking deterministic where possible; isolate LLM/provider calls behind existing clients and settings.
- Update taste service tests when changing proposal, confirmation, ranking, or enrichment behavior.

## Verification

- Run `uv run pytest tests/test_taste_domain.py tests/test_taste_service.py tests/test_taste_llm_enrichment.py tests/test_cognee_palate_store.py` after taste changes.
- Run `make palate-probe` only when live Cognee capability behavior needs verification.

## Child DOX Index

- No child AGENTS.md files. `evals/` is owned here.
