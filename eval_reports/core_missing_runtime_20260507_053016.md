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

- Run ID: `eval_20260507_043016`
- Fixture set: `production`
- JSONL output: `eval_runs/core_missing_runtime_20260507_053016.jsonl`
- Records: `204`
- Model-role summaries: `7`
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
| `anthropic:claude-haiku-4-5` | `conflict_classifier` | 1.000 | 0.896-1.000 | 33 / 33 |
| `google:gemini-2.5-flash-lite` | `router` | 1.000 | 0.610-1.000 | 6 / 6 |
| `google:gemini-2.5-flash-lite` | `slack_intake` | 1.000 | 0.940-1.000 | 60 / 60 |
| `groq:llama-3.1-8b-instant` | `router` | 0.833 | 0.436-0.970 | 5 / 6 |
| `groq:llama-3.1-8b-instant` | `slack_intake` | 0.750 | 0.628-0.842 | 45 / 60 |
| `groq:openai/gpt-oss-120b` | `conflict_classifier` | 0.727 | 0.558-0.849 | 24 / 33 |
| `openai:gpt-5-nano` | `router` | 1.000 | 0.610-1.000 | 6 / 6 |

Operational failure classes:
- `provider_error`: 2
- `rate_limit_error`: 23

## Schema validity

| Model | Role | Schema validity | 95% CI | Valid / Operationally successful |
|---|---|---:|---:|---:|
| `anthropic:claude-haiku-4-5` | `conflict_classifier` | 1.000 | 0.896-1.000 | 33 / 33 |
| `google:gemini-2.5-flash-lite` | `router` | 0.833 | 0.436-0.970 | 5 / 6 |
| `google:gemini-2.5-flash-lite` | `slack_intake` | 0.983 | 0.911-0.997 | 59 / 60 |
| `groq:llama-3.1-8b-instant` | `router` | 1.000 | 0.566-1.000 | 5 / 5 |
| `groq:llama-3.1-8b-instant` | `slack_intake` | 1.000 | 0.921-1.000 | 45 / 45 |
| `groq:openai/gpt-oss-120b` | `conflict_classifier` | 1.000 | 0.862-1.000 | 24 / 24 |
| `openai:gpt-5-nano` | `router` | 1.000 | 0.610-1.000 | 6 / 6 |

Schema / parse failure classes:
- `json_parse_error`: 2

## Safety / zero-tolerance failures

| Model | Role | Zero-tolerance failures | Upper 95% fail rate | Eligible |
|---|---|---:|---:|---|
| `anthropic:claude-haiku-4-5` | `conflict_classifier` | 26 | 0.893 | False |
| `google:gemini-2.5-flash-lite` | `router` | 0 | 0.500 | False |
| `google:gemini-2.5-flash-lite` | `slack_intake` | 15 | 0.372 | False |
| `groq:llama-3.1-8b-instant` | `router` | 0 | 0.500 | False |
| `groq:llama-3.1-8b-instant` | `slack_intake` | 11 | 0.299 | False |
| `groq:openai/gpt-oss-120b` | `conflict_classifier` | 14 | 0.592 | False |
| `openai:gpt-5-nano` | `router` | 0 | 0.500 | False |

## Quality scores by role

| Model | Role | Category | Semantic score | 95% CI | Semantic evals | Eligible | Rejection reasons |
|---|---|---|---:|---:|---:|---|---|
| `anthropic:claude-haiku-4-5` | `conflict_classifier` | `runtime` | 0.713 | 0.657-0.765 | 33 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `google:gemini-2.5-flash-lite` | `router` | `runtime` | 0.950 | 0.875-1.000 | 5 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold |
| `google:gemini-2.5-flash-lite` | `slack_intake` | `runtime` | 0.740 | 0.697-0.782 | 59 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `groq:llama-3.1-8b-instant` | `router` | `runtime` | 0.975 | 0.917-1.000 | 5 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold |
| `groq:llama-3.1-8b-instant` | `slack_intake` | `runtime` | 0.686 | 0.632-0.741 | 45 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `groq:openai/gpt-oss-120b` | `conflict_classifier` | `runtime` | 0.747 | 0.688-0.810 | 24 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `openai:gpt-5-nano` | `router` | `runtime` | 0.917 | 0.875-0.979 | 6 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold |

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
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `groq:openai/gpt-oss-120b` | 33 | 24 | -0.023 (-0.062-0.008) | 0.273 (0.037-0.500) | 0.273 (0.037-0.500) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `router` | `google:gemini-2.5-flash-lite` | `groq:llama-3.1-8b-instant` | 6 | 5 | -0.025 (-0.125-0.062) | 0.167 (0.000-0.667) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:llama-3.1-8b-instant` if a tie-break is required. |
| `router` | `google:gemini-2.5-flash-lite` | `openai:gpt-5-nano` | 6 | 5 | 0.050 (-0.094-0.125) | 0.000 (0.000-0.000) | -0.167 (-0.667-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `router` | `groq:llama-3.1-8b-instant` | `openai:gpt-5-nano` | 6 | 5 | 0.075 (0.021-0.125) | -0.167 (-0.667-0.000) | -0.167 (-0.667-0.000) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `groq:llama-3.1-8b-instant` | 60 | 45 | 0.042 (0.020-0.064) | 0.250 (0.133-0.400) | 0.233 (0.117-0.383) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |

## Cost and latency

| Model | Role | Cost / 1k successful | p50 ms | p90 ms | p95 ms |
|---|---|---:|---:|---:|---:|
| `anthropic:claude-haiku-4-5` | `conflict_classifier` | $3.2349 | 4537 | 5460 | 5624 |
| `google:gemini-2.5-flash-lite` | `router` | $0.1249 | 1899 | 2294 | 3036 |
| `google:gemini-2.5-flash-lite` | `slack_intake` | $0.1431 | 1440 | 1906 | 1956 |
| `groq:llama-3.1-8b-instant` | `router` | $0.0433 | 1600 | 7599 | 7864 |
| `groq:llama-3.1-8b-instant` | `slack_intake` | $0.0473 | 7533 | 7900 | 7950 |
| `groq:openai/gpt-oss-120b` | `conflict_classifier` | $0.2403 | 8730 | 9530 | 9709 |
| `openai:gpt-5-nano` | `router` | $0.1645 | 4667 | 4814 | 5288 |

## Why non-deployable, if applicable

Missing mandatory roles:
- conflict_classifier
- embeddings
- memory_compiler
- recall_synthesizer
- router
- slack_intake

Observed rejection reasons:
- `conflict_classifier`: conflict_safety_below_threshold (2), operational_success_below_threshold (2), schema_validity_below_threshold (2), semantic_score_below_threshold (2), zero_tolerance_failures_present (2)
- `embeddings`: no eligible candidates were evaluated for this role.
- `memory_compiler`: no eligible candidates were evaluated for this role.
- `recall_synthesizer`: no eligible candidates were evaluated for this role.
- `router`: operational_success_below_threshold (3), schema_validity_below_threshold (3), semantic_score_below_threshold (3)
- `slack_intake`: decision_correctness_below_threshold (2), operational_success_below_threshold (2), repair_option_usefulness_below_threshold (2), schema_validity_below_threshold (2), semantic_score_below_threshold (2), zero_tolerance_failures_present (2)

## Next actions

- Restore mandatory coverage for: conflict_classifier, embeddings, memory_compiler, recall_synthesizer, router, slack_intake.
- Eliminate the largest blocking failure classes first: quality_failure (101), zero_tolerance_failure (66), rate_limit_error (23).
- Rerun after operational issues are fixed so semantic comparisons are based on overlapping evaluable variants.
- Add or refine role-specific fixtures if a mandatory role remains unevaluable after provider issues are resolved.
