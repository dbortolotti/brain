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
Only judge had eligible candidates. Treat this as a harness validation run, not a model-selection run.

Eligible partials:
- `eval_judge`: `openai:gpt-5.4`

## Deployability status

- Run ID: `eval_20260507_043601`
- Fixture set: `production`
- JSONL output: `eval_runs/core_missing_judge_20260507_053601.jsonl`
- Records: `36`
- Model-role summaries: `3`
- Deployable stack: `no`
- Eligible runtime role pairs: `0`
- Eligible embedding role pairs: `0`
- Eligible judge role pairs: `3`
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
| `anthropic:claude-opus-4-7` | `eval_judge` | 0.000 | 0.000-0.243 | 0 / 12 |
| `anthropic:claude-sonnet-4-6` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |
| `openai:gpt-5.4` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |

Operational failure classes:
- `provider_error`: 12

## Schema validity

| Model | Role | Schema validity | 95% CI | Valid / Operationally successful |
|---|---|---:|---:|---:|
| `anthropic:claude-opus-4-7` | `eval_judge` | 0.000 | 0.000-0.000 | 0 / 0 |
| `anthropic:claude-sonnet-4-6` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |
| `openai:gpt-5.4` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |

No schema or parse failures were recorded.

## Safety / zero-tolerance failures

| Model | Role | Zero-tolerance failures | Upper 95% fail rate | Eligible |
|---|---|---:|---:|---|
| `anthropic:claude-opus-4-7` | `eval_judge` | 0 | 0.250 | True |
| `anthropic:claude-sonnet-4-6` | `eval_judge` | 0 | 0.250 | True |
| `openai:gpt-5.4` | `eval_judge` | 0 | 0.250 | True |

## Quality scores by role

| Model | Role | Category | Semantic score | 95% CI | Semantic evals | Eligible | Rejection reasons |
|---|---|---|---:|---:|---:|---|---|
| `anthropic:claude-opus-4-7` | `eval_judge` | `judge` | n/a | n/a | 0 | True | - |
| `anthropic:claude-sonnet-4-6` | `eval_judge` | `judge` | 0.807 | 0.766-0.854 | 12 | True | - |
| `openai:gpt-5.4` | `eval_judge` | `judge` | 0.802 | 0.755-0.849 | 12 | True | - |

## Runtime-role recommendations

Partial recommendations only.
- none

## Embedding recommendations

- none

## Judge/debug/support recommendations

- `eval_judge`: `openai:gpt-5.4`

## Pairwise comparisons

| Role | Model A | Model B | Shared variants | Shared semantic variants | Semantic diff | Operational diff | Schema diff | Recommendation |
|---|---|---|---:|---:|---:|---:|---:|---|
| `eval_judge` | `anthropic:claude-opus-4-7` | `anthropic:claude-sonnet-4-6` | 12 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-opus-4-7` | `openai:gpt-5.4` | 12 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.4` | 12 | 12 | 0.005 (-0.062-0.089) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4` on cost. |

## Cost and latency

| Model | Role | Cost / 1k successful | p50 ms | p90 ms | p95 ms |
|---|---|---:|---:|---:|---:|
| `anthropic:claude-opus-4-7` | `eval_judge` | n/a | 0 | 0 | 0 |
| `anthropic:claude-sonnet-4-6` | `eval_judge` | $12.1342 | 13011 | 16374 | 16374 |
| `openai:gpt-5.4` | `eval_judge` | $4.9202 | 5927 | 6854 | 6854 |

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
- `slack_intake`: no eligible candidates were evaluated for this role.

## Next actions

- Restore mandatory coverage for: conflict_classifier, embeddings, memory_compiler, recall_synthesizer, router, slack_intake.
- Eliminate the largest blocking failure classes first: quality_failure (24), provider_error (12).
- Rerun after operational issues are fixed so semantic comparisons are based on overlapping evaluable variants.
- Add or refine role-specific fixtures if a mandatory role remains unevaluable after provider issues are resolved.
