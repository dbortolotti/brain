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

- Run ID: `eval_20260507_043835`
- Fixture set: `production`
- JSONL output: `eval_runs/core_missing_embeddings_20260507_053834.jsonl`
- Records: `3`
- Model-role summaries: `3`
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
| `openai:text-embedding-3-large` | `embeddings` | 1.000 | 0.207-1.000 | 1 / 1 |
| `openai:text-embedding-3-small` | `embeddings` | 1.000 | 0.207-1.000 | 1 / 1 |
| `voyage:voyage-4-lite` | `embeddings` | 1.000 | 0.207-1.000 | 1 / 1 |

No operational failures were recorded.

## Schema validity

| Model | Role | Schema validity | 95% CI | Valid / Operationally successful |
|---|---|---:|---:|---:|
| `openai:text-embedding-3-large` | `embeddings` | 1.000 | 0.207-1.000 | 1 / 1 |
| `openai:text-embedding-3-small` | `embeddings` | 1.000 | 0.207-1.000 | 1 / 1 |
| `voyage:voyage-4-lite` | `embeddings` | 1.000 | 0.207-1.000 | 1 / 1 |

No schema or parse failures were recorded.

## Safety / zero-tolerance failures

| Model | Role | Zero-tolerance failures | Upper 95% fail rate | Eligible |
|---|---|---:|---:|---|
| `openai:text-embedding-3-large` | `embeddings` | 0 | 1.000 | False |
| `openai:text-embedding-3-small` | `embeddings` | 0 | 1.000 | False |
| `voyage:voyage-4-lite` | `embeddings` | 0 | 1.000 | False |

## Quality scores by role

| Model | Role | Category | Semantic score | 95% CI | Semantic evals | Eligible | Rejection reasons |
|---|---|---|---:|---:|---:|---|---|
| `openai:text-embedding-3-large` | `embeddings` | `embedding` | 1.000 | 1.000-1.000 | 1 | False | operational_success_below_threshold |
| `openai:text-embedding-3-small` | `embeddings` | `embedding` | 1.000 | 1.000-1.000 | 1 | False | operational_success_below_threshold |
| `voyage:voyage-4-lite` | `embeddings` | `embedding` | 1.000 | 1.000-1.000 | 1 | False | operational_success_below_threshold |

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
| `embeddings` | `openai:text-embedding-3-large` | `openai:text-embedding-3-small` | 1 | 1 | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:text-embedding-3-small` if a tie-break is required. |
| `embeddings` | `openai:text-embedding-3-large` | `voyage:voyage-4-lite` | 1 | 1 | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `voyage:voyage-4-lite` if a tie-break is required. |
| `embeddings` | `openai:text-embedding-3-small` | `voyage:voyage-4-lite` | 1 | 1 | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:text-embedding-3-small` if a tie-break is required. |

## Cost and latency

| Model | Role | Cost / 1k successful | p50 ms | p90 ms | p95 ms |
|---|---|---:|---:|---:|---:|
| `openai:text-embedding-3-large` | `embeddings` | $0.0035 | 1691 | 1691 | 1691 |
| `openai:text-embedding-3-small` | `embeddings` | $0.0005 | 860 | 860 | 860 |
| `voyage:voyage-4-lite` | `embeddings` | $0.0005 | 388 | 388 | 388 |

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
- `embeddings`: operational_success_below_threshold (3)
- `memory_compiler`: no eligible candidates were evaluated for this role.
- `recall_synthesizer`: no eligible candidates were evaluated for this role.
- `router`: no eligible candidates were evaluated for this role.
- `slack_intake`: no eligible candidates were evaluated for this role.

## Next actions

- Restore mandatory coverage for: conflict_classifier, embeddings, memory_compiler, recall_synthesizer, router, slack_intake.
- Eliminate the largest blocking failure classes first: none recorded.
- Rerun after operational issues are fixed so semantic comparisons are based on overlapping evaluable variants.
- Add or refine role-specific fixtures if a mandatory role remains unevaluable after provider issues are resolved.
