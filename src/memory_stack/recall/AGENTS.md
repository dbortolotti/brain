# Purpose

- Own recall planning, retrieval, evidence construction, and answer synthesis.

## Ownership

- `planner.py` owns recall-mode and profile inference.
- `retriever.py` owns memory retrieval orchestration.
- `evidence_builder.py` owns evidence/fact construction.
- `synthesizer.py` owns rendering recalled memory answers.

## Local Contracts

- Recall answers must be evidence-backed and respect user scope, profile context, status, superseded records, and exclusions.
- Do not synthesize unsupported claims from weak or missing evidence.
- Keep retrieval and synthesis behavior aligned with Brain tool contracts and eval fixtures.

## Work Guidance

- Prefer explicit evidence objects over free-form strings between recall stages.
- Add tests or eval cases when changing ranking, filtering, or synthesis behavior.

## Verification

- Run `uv run pytest tests/test_recall_retriever.py tests/test_brain_service.py` after recall changes.
- Use `make brain-eval` for broad recall quality changes.

## Child DOX Index

- No child AGENTS.md files. Recall modules are owned here.
