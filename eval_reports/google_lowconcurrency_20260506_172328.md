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

- Run ID: `eval_20260506_162328`
- Fixture set: `production`
- JSONL output: `eval_runs/google_lowconcurrency_20260506_172328.jsonl`
- Records: `357`
- Model-role summaries: `9`
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
| `google:gemini-2.5-flash` | `conflict_classifier` | 1.000 | 0.896-1.000 | 33 / 33 |
| `google:gemini-2.5-flash` | `entity_resolution` | 1.000 | 0.701-1.000 | 9 / 9 |
| `google:gemini-2.5-flash` | `memory_compiler` | 1.000 | 0.921-1.000 | 45 / 45 |
| `google:gemini-2.5-flash` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `google:gemini-2.5-flash` | `slack_intake` | 1.000 | 0.940-1.000 | 60 / 60 |
| `google:gemini-2.5-flash-lite` | `memory_compiler` | 0.978 | 0.884-0.996 | 44 / 45 |
| `google:gemini-2.5-flash-lite` | `recall_synthesizer` | 0.944 | 0.819-0.985 | 34 / 36 |
| `google:gemini-2.5-flash-lite` | `slack_intake` | 0.933 | 0.841-0.974 | 56 / 60 |
| `google:gemini-2.5-pro` | `conflict_classifier` | 0.909 | 0.764-0.969 | 30 / 33 |

Operational failure classes:
- `provider_error`: 10

## Schema validity

| Model | Role | Schema validity | 95% CI | Valid / Operationally successful |
|---|---|---:|---:|---:|
| `google:gemini-2.5-flash` | `conflict_classifier` | 0.545 | 0.380-0.702 | 18 / 33 |
| `google:gemini-2.5-flash` | `entity_resolution` | 0.889 | 0.565-0.980 | 8 / 9 |
| `google:gemini-2.5-flash` | `memory_compiler` | 0.356 | 0.232-0.502 | 16 / 45 |
| `google:gemini-2.5-flash` | `recall_synthesizer` | 0.917 | 0.782-0.971 | 33 / 36 |
| `google:gemini-2.5-flash` | `slack_intake` | 0.567 | 0.441-0.684 | 34 / 60 |
| `google:gemini-2.5-flash-lite` | `memory_compiler` | 1.000 | 0.920-1.000 | 44 / 44 |
| `google:gemini-2.5-flash-lite` | `recall_synthesizer` | 1.000 | 0.898-1.000 | 34 / 34 |
| `google:gemini-2.5-flash-lite` | `slack_intake` | 0.982 | 0.906-0.997 | 55 / 56 |
| `google:gemini-2.5-pro` | `conflict_classifier` | 0.667 | 0.488-0.808 | 20 / 30 |

Schema / parse failure classes:
- `json_parse_error`: 72
- `schema_invalid`: 13

## Safety / zero-tolerance failures

| Model | Role | Zero-tolerance failures | Upper 95% fail rate | Eligible |
|---|---|---:|---:|---|
| `google:gemini-2.5-flash` | `conflict_classifier` | 11 | 0.504 | False |
| `google:gemini-2.5-flash` | `entity_resolution` | 5 | 0.811 | False |
| `google:gemini-2.5-flash` | `memory_compiler` | 6 | 0.262 | False |
| `google:gemini-2.5-flash` | `recall_synthesizer` | 0 | 0.083 | False |
| `google:gemini-2.5-flash` | `slack_intake` | 9 | 0.261 | False |
| `google:gemini-2.5-flash-lite` | `memory_compiler` | 20 | 0.588 | False |
| `google:gemini-2.5-flash-lite` | `recall_synthesizer` | 0 | 0.083 | False |
| `google:gemini-2.5-flash-lite` | `slack_intake` | 14 | 0.354 | False |
| `google:gemini-2.5-pro` | `conflict_classifier` | 11 | 0.504 | False |

## Quality scores by role

| Model | Role | Category | Semantic score | 95% CI | Semantic evals | Eligible | Rejection reasons |
|---|---|---|---:|---:|---:|---|---|
| `google:gemini-2.5-flash` | `conflict_classifier` | `runtime` | 0.727 | 0.661-0.792 | 18 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `google:gemini-2.5-flash` | `entity_resolution` | `runtime_or_support` | 0.763 | 0.714-0.819 | 8 | False | zero_tolerance_failures_present |
| `google:gemini-2.5-flash` | `memory_compiler` | `runtime` | 0.730 | 0.688-0.795 | 16 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, memory_card_extraction_below_threshold |
| `google:gemini-2.5-flash` | `recall_synthesizer` | `runtime` | 0.951 | 0.905-0.987 | 33 | False | operational_success_below_threshold, schema_validity_below_threshold, groundedness_below_threshold |
| `google:gemini-2.5-flash` | `slack_intake` | `runtime` | 0.716 | 0.666-0.765 | 34 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `google:gemini-2.5-flash-lite` | `memory_compiler` | `runtime` | 0.709 | 0.668-0.744 | 44 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, memory_card_extraction_below_threshold |
| `google:gemini-2.5-flash-lite` | `recall_synthesizer` | `runtime` | 0.929 | 0.886-0.968 | 34 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, groundedness_below_threshold |
| `google:gemini-2.5-flash-lite` | `slack_intake` | `runtime` | 0.743 | 0.697-0.785 | 55 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `google:gemini-2.5-pro` | `conflict_classifier` | `runtime` | 0.753 | 0.684-0.835 | 20 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |

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
| `conflict_classifier` | `google:gemini-2.5-flash` | `google:gemini-2.5-pro` | 33 | 13 | 0.014 (-0.062-0.085) | 0.091 (0.000-0.250) | -0.061 (-0.405-0.282) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `memory_compiler` | `google:gemini-2.5-flash` | `google:gemini-2.5-flash-lite` | 45 | 16 | -0.005 (-0.052-0.049) | 0.022 (0.000-0.095) | -0.622 (-0.857--0.378) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `google:gemini-2.5-flash-lite` | 36 | 31 | 0.013 (-0.006-0.036) | 0.056 (0.000-0.182) | -0.028 (-0.233-0.143) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `slack_intake` | `google:gemini-2.5-flash` | `google:gemini-2.5-flash-lite` | 60 | 30 | -0.002 (-0.036-0.032) | 0.067 (0.000-0.150) | -0.350 (-0.550--0.150) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |

## Cost and latency

| Model | Role | Cost / 1k successful | p50 ms | p90 ms | p95 ms |
|---|---|---:|---:|---:|---:|
| `google:gemini-2.5-flash` | `conflict_classifier` | $0.7151 | 8016 | 10181 | 10211 |
| `google:gemini-2.5-flash` | `entity_resolution` | $0.6598 | 3812 | 8356 | 11003 |
| `google:gemini-2.5-flash` | `memory_compiler` | $0.9911 | 9177 | 10634 | 10785 |
| `google:gemini-2.5-flash` | `recall_synthesizer` | $0.7555 | 5709 | 8830 | 9179 |
| `google:gemini-2.5-flash` | `slack_intake` | $0.6396 | 7046 | 9989 | 10180 |
| `google:gemini-2.5-flash-lite` | `memory_compiler` | $0.1983 | 7478 | 15441 | 15585 |
| `google:gemini-2.5-flash-lite` | `recall_synthesizer` | $0.1407 | 5472 | 10766 | 11896 |
| `google:gemini-2.5-flash-lite` | `slack_intake` | $0.1469 | 4856 | 10015 | 10883 |
| `google:gemini-2.5-pro` | `conflict_classifier` | $3.5366 | 14631 | 16816 | 16976 |

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
- `memory_compiler`: memory_card_extraction_below_threshold (2), operational_success_below_threshold (2), schema_validity_below_threshold (2), semantic_score_below_threshold (2), zero_tolerance_failures_present (2)
- `recall_synthesizer`: groundedness_below_threshold (2), operational_success_below_threshold (2), schema_validity_below_threshold (2), semantic_score_below_threshold (1)
- `router`: no eligible candidates were evaluated for this role.
- `slack_intake`: decision_correctness_below_threshold (2), operational_success_below_threshold (2), repair_option_usefulness_below_threshold (2), schema_validity_below_threshold (2), semantic_score_below_threshold (2), zero_tolerance_failures_present (2)

## Next actions

- Restore mandatory coverage for: conflict_classifier, embeddings, memory_compiler, recall_synthesizer, router, slack_intake.
- Eliminate the largest blocking failure classes first: quality_failure (149), zero_tolerance_failure (76), json_parse_error (72).
- Rerun after operational issues are fixed so semantic comparisons are based on overlapping evaluable variants.
- Add or refine role-specific fixtures if a mandatory role remains unevaluable after provider issues are resolved.
