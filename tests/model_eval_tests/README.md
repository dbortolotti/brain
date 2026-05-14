# Model Eval Tests

This folder stores durable model-evaluation fixtures that are larger than the
normal unit-test fixtures.

## Files

- `organic_recall_100_cases.json`: 47 service-layer seed inserts and 100 recall
  cases. Recall cases are balanced across difficulties 1 through 5, with 20
  cases per difficulty.
- `manetti_100_questions.json`: balanced 100-question Manetti question set
  generated from `manetti_document.md`, with 20 questions at each difficulty
  level from 1 through 5.
- `manetti_100_questions.md`: Markdown rendering of the balanced Manetti
  question set.
- `manetti_document.md`: local copy of the Manetti source markdown used for the
  Manetti candidate evaluation.
- `run_model_eval.py`: live Cognee eval runner. It creates a fresh dataset,
  ingests the full Manetti document followed by the ordered organic seed
  inserts, asks all 200 fixture questions, and scores every answer with a judge
  model.
- `test_fixture_integrity.py`: shape checks for the JSON fixtures and copied
  Manetti materials.

## Difficulty Scale

- 1: Direct single-fact recall.
- 2: Direct recall with simple filtering, status, or source distractors.
- 3: Multi-fact synthesis across two or more memories or sources.
- 4: Precise filtering under distractors, status conflicts, or scoped exclusions.
- 5: High-constraint synthesis across multiple domains with stale/deleted exclusions.

## Live Runner

Example:

```bash
uv run python tests/model_eval_tests/run_model_eval.py \
  --judge-model gpt-5.5 \
  --remember-model gpt-5.4-mini \
  --recall-model gpt-5.5
```

Each run writes a timestamped folder under `tests/model_eval_tests/runs/` with:

- `config.json`
- `ingestion_timings.json` and `ingestion_timings.jsonl`
- `answers.jsonl`
- `scores.jsonl`
- `scores.csv`
- `report.md`
