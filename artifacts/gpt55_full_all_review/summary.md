# Executive verdict

Deployable stack: **NO**

This run is not sufficient to select a full production Brain model stack.

Missing mandatory roles:
- conflict_handling
- entity_resolution
- memory_compiler
- recall
- router
- slack_intake

Interpretation:
Only support had eligible candidates. Treat this as a harness validation run, not a model-selection run.

Eligible partials:
- `repair_option_generator`: `openai:gpt-5.5`

## Deployability status

- Run ID: `rescore_20260508_162930`
- Eval mode: `fine-grained`
- Fixture set: `brain-model-test-v2`
- Canonical output: `artifacts/gpt55_full_all_review/results_repair_iter3_rescored.json`
- Failed manifest JSONL: `artifacts/gpt55_full_all_review/failed_tests.jsonl`
- Failed manifest markdown: `artifacts/gpt55_full_all_review/failed_tests.md`
- HTML summary: `artifacts/gpt55_full_all_review/summary.html`
- Zero-tolerance detail CSV: `artifacts/gpt55_full_all_review/zero_tolerance_failures_detail.csv`
- Failed fixture summary CSV: `artifacts/gpt55_full_all_review/failed_fixture_summary.csv`
- Targeted follow-up commands: `artifacts/gpt55_full_all_review/targeted_followup_commands.md`
- Records: `123`
- Model-role summaries: `1`
- Deployable stack: `no`
- Eligible runtime role pairs: `0`
- Eligible embedding role pairs: `0`
- Eligible judge role pairs: `0`
- Eligible debug/admin role pairs: `0`
- Eligible support role pairs: `1`
- Eligibility states: `eligible (1)`

## Rescore transition audit

### Failure Class

- `none -> none`: 122
- `quality_failure -> none`: 1

### Operational Success

- `True -> True`: 123

### Status

- `ok -> ok`: 122
- `quality_fail -> ok`: 1


## Mandatory role coverage

| Target | Required | Eligible models | Status |
|---|---:|---|---|
| `conflict_handling` | yes | `conflict_candidate_detector`: none; `conflict_explainer`: none | MISSING |
| `debug` | yes | `debug_explainer`: none | MISSING |
| `embeddings` | no | none | NOT_TESTED |
| `entity_resolution` | yes | `entity_candidate_ranker`: none; `entity_mention_extractor`: none | MISSING |
| `judge` | yes | `eval_judge`: none | MISSING |
| `memory_compiler` | yes | `atomic_card_extractor`: none; `entity_mention_extractor`: none; `open_loop_detector`: none; `relationship_extractor`: none; `source_takeaway_extractor`: none; `table_policy_handler`: none | MISSING |
| `recall` | yes | `recall_planner`: none; `recall_synthesizer`: none | MISSING |
| `router` | yes | `intent_router`: none | MISSING |
| `slack_intake` | yes | `durability_filter`: none; `memory_kind_classifier`: none; `repair_option_generator`: `openai:gpt-5.5`; `source_classifier`: none | MISSING |

## Operational reliability

| Model | Role | Operational success | 95% CI | Successes / Total |
|---|---|---:|---:|---:|
| `openai:gpt-5.5` | `repair_option_generator` | 1.000 | 0.970-1.000 | 123 / 123 |

No operational failures were recorded.

## Schema validity

| Model | Role | JSON parse success | 95% CI | Parseable / Operationally successful |
|---|---|---:|---:|---:|
| `openai:gpt-5.5` | `repair_option_generator` | 1.000 | 0.970-1.000 | 123 / 123 |

| Model | Role | Schema validity | 95% CI | Valid / Parseable |
|---|---|---:|---:|---:|
| `openai:gpt-5.5` | `repair_option_generator` | 1.000 | 0.970-1.000 | 123 / 123 |

No schema or parse failures were recorded.

## Semantic evaluability

| Model | Role | Semantic evaluable | 95% CI | Semantic-evaluable / Schema-valid |
|---|---|---:|---:|---:|
| `openai:gpt-5.5` | `repair_option_generator` | 1.000 | 0.970-1.000 | 123 / 123 |

## Safety / zero-tolerance failures

| Model | Role | Zero-tolerance failures | Upper 95% fail rate | Eligible | Eligibility state |
|---|---|---:|---:|---|---|
| `openai:gpt-5.5` | `repair_option_generator` | 0 | 0.024 | True | `eligible` |

## Quality scores by role

| Model | Role | Category | Quality pass | 95% CI | Passes / Semantic evals | Semantic score | 95% CI | Eligible | Eligibility state | Rejection reasons |
|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| `openai:gpt-5.5` | `repair_option_generator` | `support` | 1.000 | 0.970-1.000 | 123 / 123 | 1.000 | 1.000-1.000 | True | `eligible` | - |

## Top failed fixtures by role/model

| Role | Model | Semantic score | Quality pass | Zero tolerance | Schema/parse fails | Eligibility state | Rejection reasons | Top failed fixtures | Top zero-tolerance reasons |
|---|---|---:|---:|---:|---:|---|---|---|---|
| `repair_option_generator` | `openai:gpt-5.5` | 1.000 | 1.000 | 0 | 0 | `eligible` | - | - | - |

## Runtime-role recommendations

Partial recommendations only.
- none

## Embedding recommendations

- none

## Judge/debug/support recommendations

- `repair_option_generator`: `openai:gpt-5.5`

## Pairwise comparisons

| Role | Model A | Model B | Shared variants | Shared semantic variants | Semantic diff | Operational diff | Schema diff | Recommendation |
|---|---|---|---:|---:|---:|---:|---:|---|
| | | | | | | | | No pairwise comparisons available. |

## Cost and latency

| Model | Role | Cost / 1k attempted | Cost / 1k successful | Cost / 1k semantic | p50 ms | p90 ms | p95 ms |
|---|---|---:|---:|---:|---:|---:|---:|
| `openai:gpt-5.5` | `repair_option_generator` | $5.2129 | $5.2129 | $5.2129 | 2771 | 4142 | 5316 |

## Why non-deployable, if applicable

Missing mandatory capabilities:
- conflict_handling
- entity_resolution
- memory_compiler
- recall
- router
- slack_intake

Observed capability gaps:
- `conflict_handling`: missing eligible coverage for `conflict_candidate_detector`, `conflict_explainer`
- `entity_resolution`: missing eligible coverage for `entity_mention_extractor`, `entity_candidate_ranker`
- `memory_compiler`: missing eligible coverage for `atomic_card_extractor`, `entity_mention_extractor`, `relationship_extractor`, `open_loop_detector`, `table_policy_handler`, `source_takeaway_extractor`
- `recall`: missing eligible coverage for `recall_planner`, `recall_synthesizer`
- `router`: missing eligible coverage for `intent_router`
- `slack_intake`: missing eligible coverage for `source_classifier`, `durability_filter`, `memory_kind_classifier`

## Next actions

- Restore mandatory coverage for: conflict_handling, entity_resolution, memory_compiler, recall, router, slack_intake.
- Eliminate the largest blocking failure classes first: none recorded.
- Rerun after operational issues are fixed so semantic comparisons are based on overlapping evaluable variants.
- Add or refine role-specific fixtures if a mandatory role remains unevaluable after provider issues are resolved.

## Rerun command

```bash
brain eval rerun-failed --source-json artifacts/gpt55_full_all_review/results_repair_iter3_rescored.json --failed-manifest artifacts/gpt55_full_all_review/failed_tests.jsonl --endpoint-max-concurrency 3 --output-json artifacts/gpt55_full_all_review/results_repair_iter3_rescored.json --overwrite
```
