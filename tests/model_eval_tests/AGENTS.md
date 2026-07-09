# Purpose

- Own durable model-evaluation fixtures that are larger than normal unit-test fixtures, plus the live Cognee eval runner for those fixtures.

## Ownership

- `organic_recall_100_cases.json` owns the organic recall case fixture set.
- `manetti_100_questions.json`, `manetti_100_questions.md`, and `manetti_document.md` own the Manetti fixture materials.
- `run_model_eval.py` owns the live Cognee evaluation runner.
- `test_fixture_integrity.py` owns fixture shape checks.

## Local Contracts

- Keep fixture difficulty definitions aligned with `README.md`.
- Do not track live run outputs; `runs/` is ignored runtime output.
- Live runs must write inspectable config, timing, answer, score, CSV, and report artifacts under the run output directory.

## Work Guidance

- Preserve balanced difficulty coverage when editing question sets.
- Update JSON and Markdown renderings together for Manetti question changes.

## Verification

- Run `uv run pytest tests/model_eval_tests/test_fixture_integrity.py` after fixture edits.
- Run `uv run python tests/model_eval_tests/run_model_eval.py --help` after runner interface edits.

## Child DOX Index

- No child AGENTS.md files. All model-eval fixture files are owned here.
