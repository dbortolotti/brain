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
- `eval_judge`: `openai:gpt-5.5-xhigh`

## Deployability status

- Run ID: `eval_20260507_041920`
- Fixture set: `production`
- JSONL output: `eval_runs/gpt55_xhigh_eval_judge_20260507_051919.jsonl`
- Records: `12`
- Model-role summaries: `1`
- Deployable stack: `no`
- Eligible runtime role pairs: `0`
- Eligible embedding role pairs: `0`
- Eligible judge role pairs: `1`
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
| `openai:gpt-5.5-xhigh` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |

No operational failures were recorded.

## Schema validity

| Model | Role | Schema validity | 95% CI | Valid / Operationally successful |
|---|---|---:|---:|---:|
| `openai:gpt-5.5-xhigh` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |

No schema or parse failures were recorded.

## Safety / zero-tolerance failures

| Model | Role | Zero-tolerance failures | Upper 95% fail rate | Eligible |
|---|---|---:|---:|---|
| `openai:gpt-5.5-xhigh` | `eval_judge` | 0 | 0.250 | True |

## Quality scores by role

| Model | Role | Category | Semantic score | 95% CI | Semantic evals | Eligible | Rejection reasons |
|---|---|---|---:|---:|---:|---|---|
| `openai:gpt-5.5-xhigh` | `eval_judge` | `judge` | 0.812 | 0.750-0.875 | 12 | True | - |

## Runtime-role recommendations

Partial recommendations only.
- none

## Embedding recommendations

- none

## Judge/debug/support recommendations

- `eval_judge`: `openai:gpt-5.5-xhigh`

## Pairwise comparisons

| Role | Model A | Model B | Shared variants | Shared semantic variants | Semantic diff | Operational diff | Schema diff | Recommendation |
|---|---|---|---:|---:|---:|---:|---:|---|
| | | | | | | | | No pairwise comparisons available. |

## Cost and latency

| Model | Role | Cost / 1k successful | p50 ms | p90 ms | p95 ms |
|---|---|---:|---:|---:|---:|
| `openai:gpt-5.5-xhigh` | `eval_judge` | $8.3029 | 11936 | 20309 | 20309 |

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
- Eliminate the largest blocking failure classes first: quality_failure (12).
- Rerun after operational issues are fixed so semantic comparisons are based on overlapping evaluable variants.
- Add or refine role-specific fixtures if a mandatory role remains unevaluable after provider issues are resolved.
