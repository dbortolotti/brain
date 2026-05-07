# Executive verdict

Deployable stack: **NO**

This run is not sufficient to select a full production Brain model stack.

Missing mandatory roles:
- conflict_classifier
- embeddings
- memory_compiler
- recall_synthesizer
- router
- slack_intake

Interpretation:
Only no roles had eligible candidates. Treat this as a harness validation run, not a model-selection run.

Eligible partials:
- none

## Deployability status

- Run ID: `eval_20260507_044056`
- Fixture set: `production`
- JSONL output: `eval_runs/core_missing_gptoss_slack_20260507_054056.jsonl`
- Records: `60`
- Model-role summaries: `1`
- Deployable stack: `no`
- Eligible runtime role pairs: `0`
- Eligible embedding role pairs: `0`
- Eligible judge role pairs: `0`
- Eligible debug/admin role pairs: `0`
- Eligible support role pairs: `0`

## Mandatory role coverage

| Role | Required | Eligible models | Status |
|---|---:|---|---|
| `conflict_classifier` | yes | none | MISSING |
| `embeddings` | yes | none | MISSING |
| `memory_compiler` | yes | none | MISSING |
| `recall_synthesizer` | yes | none | MISSING |
| `router` | yes | none | MISSING |
| `slack_intake` | yes | none | MISSING |

## Operational reliability

| Model | Role | Operational success | 95% CI | Successes / Total |
|---|---|---:|---:|---:|
| `groq:openai/gpt-oss-120b` | `slack_intake` | 0.750 | 0.628-0.842 | 45 / 60 |

Operational failure classes:
- `provider_error`: 1
- `rate_limit_error`: 14

## Schema validity

| Model | Role | Schema validity | 95% CI | Valid / Operationally successful |
|---|---|---:|---:|---:|
| `groq:openai/gpt-oss-120b` | `slack_intake` | 1.000 | 0.921-1.000 | 45 / 45 |

No schema or parse failures were recorded.

## Safety / zero-tolerance failures

| Model | Role | Zero-tolerance failures | Upper 95% fail rate | Eligible |
|---|---|---:|---:|---|
| `groq:openai/gpt-oss-120b` | `slack_intake` | 14 | 0.354 | False |

## Quality scores by role

| Model | Role | Category | Semantic score | 95% CI | Semantic evals | Eligible | Rejection reasons |
|---|---|---|---:|---:|---:|---|---|
| `groq:openai/gpt-oss-120b` | `slack_intake` | `runtime` | 0.694 | 0.645-0.739 | 45 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |

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

| Model | Role | Cost / 1k successful | p50 ms | p90 ms | p95 ms |
|---|---|---:|---:|---:|---:|
| `groq:openai/gpt-oss-120b` | `slack_intake` | $0.1793 | 7561 | 9132 | 9205 |

## Why non-deployable, if applicable

Missing mandatory roles:
- conflict_classifier
- embeddings
- memory_compiler
- recall_synthesizer
- router
- slack_intake

Observed rejection reasons:
- `conflict_classifier`: no eligible candidates were evaluated for this role.
- `embeddings`: no eligible candidates were evaluated for this role.
- `memory_compiler`: no eligible candidates were evaluated for this role.
- `recall_synthesizer`: no eligible candidates were evaluated for this role.
- `router`: no eligible candidates were evaluated for this role.
- `slack_intake`: decision_correctness_below_threshold (1), operational_success_below_threshold (1), repair_option_usefulness_below_threshold (1), schema_validity_below_threshold (1), semantic_score_below_threshold (1), zero_tolerance_failures_present (1)

## Next actions

- Restore mandatory coverage for: conflict_classifier, embeddings, memory_compiler, recall_synthesizer, router, slack_intake.
- Eliminate the largest blocking failure classes first: quality_failure (31), zero_tolerance_failure (14), rate_limit_error (14).
- Rerun after operational issues are fixed so semantic comparisons are based on overlapping evaluable variants.
- Add or refine role-specific fixtures if a mandatory role remains unevaluable after provider issues are resolved.
