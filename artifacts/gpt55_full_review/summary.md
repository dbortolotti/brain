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
Only no roles had eligible candidates. Treat this as a harness validation run, not a model-selection run.

Eligible partials:
- none

## Deployability status

- Run ID: `eval_20260508_125437`
- Eval mode: `fine-grained`
- Fixture set: `production`
- Canonical output: `artifacts/gpt55_full_review/results.json`
- Failed manifest JSONL: `artifacts/gpt55_full_review/failed_tests.jsonl`
- Failed manifest markdown: `artifacts/gpt55_full_review/failed_tests.md`
- HTML summary: `artifacts/gpt55_full_review/summary.html`
- Zero-tolerance detail CSV: `artifacts/gpt55_full_review/zero_tolerance_failures_detail.csv`
- Failed fixture summary CSV: `artifacts/gpt55_full_review/failed_fixture_summary.csv`
- Targeted follow-up commands: `artifacts/gpt55_full_review/targeted_followup_commands.md`
- Records: `12`
- Model-role summaries: `1`
- Deployable stack: `no`
- Eligible runtime role pairs: `0`
- Eligible embedding role pairs: `0`
- Eligible judge role pairs: `0`
- Eligible debug/admin role pairs: `0`
- Eligible support role pairs: `0`
- Eligibility states: `insufficient_sample (1)`


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
| `slack_intake` | yes | `durability_filter`: none; `memory_kind_classifier`: none; `repair_option_generator`: none; `source_classifier`: none | MISSING |

## Operational reliability

| Model | Role | Operational success | 95% CI | Successes / Total |
|---|---|---:|---:|---:|
| `openai:gpt-5.5` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |

No operational failures were recorded.

## Schema validity

| Model | Role | JSON parse success | 95% CI | Parseable / Operationally successful |
|---|---|---:|---:|---:|
| `openai:gpt-5.5` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |

| Model | Role | Schema validity | 95% CI | Valid / Parseable |
|---|---|---:|---:|---:|
| `openai:gpt-5.5` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |

No schema or parse failures were recorded.

## Semantic evaluability

| Model | Role | Semantic evaluable | 95% CI | Semantic-evaluable / Schema-valid |
|---|---|---:|---:|---:|
| `openai:gpt-5.5` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |

## Safety / zero-tolerance failures

| Model | Role | Zero-tolerance failures | Upper 95% fail rate | Eligible | Eligibility state |
|---|---|---:|---:|---|---|
| `openai:gpt-5.5` | `eval_judge` | 0 | 0.250 | False | `insufficient_sample` |

## Quality scores by role

| Model | Role | Category | Quality pass | 95% CI | Passes / Semantic evals | Semantic score | 95% CI | Eligible | Eligibility state | Rejection reasons |
|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| `openai:gpt-5.5` | `eval_judge` | `judge` | 0.417 | 0.193-0.680 | 5 / 12 | 0.879 | 0.879-0.879 | False | `insufficient_sample` | semantic_evaluable_below_minimum |

## Top failed fixtures by role/model

| Role | Model | Semantic score | Quality pass | Zero tolerance | Schema/parse fails | Eligibility state | Rejection reasons | Top failed fixtures | Top zero-tolerance reasons |
|---|---|---:|---:|---:|---:|---|---|---|---|
| `eval_judge` | `openai:gpt-5.5` | 0.879 | 0.417 | 0 | 0 | `insufficient_sample` | semantic_evaluable_below_minimum | groundedness_metadata_claims_001 (3); groundedness_absence_claims_001 (3); groundedness_section_headings_001 (1) | - |

## Runtime-role recommendations

Partial recommendations only.
- none

## Embedding recommendations

- none

## Judge/debug/support recommendations

- none

## Pairwise comparisons

| Role | Model A | Model B | Shared variants | Shared semantic variants | Semantic diff | Operational diff | Schema diff | Recommendation |
|---|---|---|---:|---:|---:|---:|---:|---|
| | | | | | | | | No pairwise comparisons available. |

## Cost and latency

| Model | Role | Cost / 1k attempted | Cost / 1k successful | Cost / 1k semantic | p50 ms | p90 ms | p95 ms |
|---|---|---:|---:|---:|---:|---:|---:|
| `openai:gpt-5.5` | `eval_judge` | $8.7379 | $8.7379 | $8.7379 | 4187 | 4777 | 4777 |

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
- `slack_intake`: missing eligible coverage for `source_classifier`, `durability_filter`, `memory_kind_classifier`, `repair_option_generator`

## Next actions

- Restore mandatory coverage for: conflict_handling, entity_resolution, memory_compiler, recall, router, slack_intake.
- Eliminate the largest blocking failure classes first: quality_failure (7).
- Rerun after operational issues are fixed so semantic comparisons are based on overlapping evaluable variants.
- Add or refine role-specific fixtures if a mandatory role remains unevaluable after provider issues are resolved.

## Rerun command

```bash
brain eval rerun-failed --source-json artifacts/gpt55_full_review/results.json --failed-manifest artifacts/gpt55_full_review/failed_tests.jsonl --endpoint-max-concurrency 3 --output-json artifacts/gpt55_full_review/results.json --overwrite
```
