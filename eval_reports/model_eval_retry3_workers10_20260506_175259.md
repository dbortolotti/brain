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

- Run ID: `eval_20260506_165259`
- Fixture set: `production`
- JSONL output: `eval_runs/prod_retry3_workers10_20260506_175259.jsonl`
- Records: `1395`
- Model-role summaries: `35`
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
| `anthropic:claude-haiku-4-5-20251001` | `conflict_classifier` | 1.000 | 0.896-1.000 | 33 / 33 |
| `anthropic:claude-haiku-4-5-20251001` | `entity_resolution` | 1.000 | 0.701-1.000 | 9 / 9 |
| `anthropic:claude-haiku-4-5-20251001` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `anthropic:claude-sonnet-4-6` | `conflict_classifier` | 1.000 | 0.896-1.000 | 33 / 33 |
| `aws-bedrock:mistral.ministral-3-14b-instruct` | `memory_compiler` | 1.000 | 0.921-1.000 | 45 / 45 |
| `aws-bedrock:mistral.ministral-3-14b-instruct` | `slack_intake` | 1.000 | 0.940-1.000 | 60 / 60 |
| `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `slack_intake` | 1.000 | 0.940-1.000 | 60 / 60 |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `conflict_classifier` | 0.000 | 0.000-0.104 | 0 / 33 |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `memory_compiler` | 0.000 | 0.000-0.079 | 0 / 45 |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `recall_synthesizer` | 0.000 | 0.000-0.096 | 0 / 36 |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `slack_intake` | 0.000 | 0.000-0.060 | 0 / 60 |
| `google:gemini-2.5-flash` | `conflict_classifier` | 1.000 | 0.896-1.000 | 33 / 33 |
| `google:gemini-2.5-flash` | `entity_resolution` | 1.000 | 0.701-1.000 | 9 / 9 |
| `google:gemini-2.5-flash` | `memory_compiler` | 1.000 | 0.921-1.000 | 45 / 45 |
| `google:gemini-2.5-flash` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `google:gemini-2.5-flash` | `slack_intake` | 1.000 | 0.940-1.000 | 60 / 60 |
| `google:gemini-2.5-flash-lite` | `memory_compiler` | 1.000 | 0.921-1.000 | 45 / 45 |
| `google:gemini-2.5-flash-lite` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `google:gemini-2.5-flash-lite` | `slack_intake` | 1.000 | 0.940-1.000 | 60 / 60 |
| `google:gemini-2.5-pro` | `conflict_classifier` | 0.970 | 0.847-0.995 | 32 / 33 |
| `groq:llama-3.1-8b-instant` | `slack_intake` | 0.717 | 0.592-0.815 | 43 / 60 |
| `groq:llama-3.3-70b-versatile` | `memory_compiler` | 0.889 | 0.765-0.952 | 40 / 45 |
| `groq:llama-3.3-70b-versatile` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `groq:openai/gpt-oss-120b` | `conflict_classifier` | 0.667 | 0.496-0.802 | 22 / 33 |
| `groq:openai/gpt-oss-120b` | `memory_compiler` | 0.756 | 0.613-0.858 | 34 / 45 |
| `groq:openai/gpt-oss-120b` | `recall_synthesizer` | 0.667 | 0.503-0.798 | 24 / 36 |
| `openai:gpt-5.4-mini` | `conflict_classifier` | 1.000 | 0.896-1.000 | 33 / 33 |
| `openai:gpt-5.4-mini` | `entity_resolution` | 1.000 | 0.701-1.000 | 9 / 9 |
| `openai:gpt-5.4-mini` | `memory_compiler` | 1.000 | 0.921-1.000 | 45 / 45 |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.4-mini` | `slack_intake` | 1.000 | 0.940-1.000 | 60 / 60 |
| `openai:gpt-5.4-nano` | `entity_resolution` | 1.000 | 0.701-1.000 | 9 / 9 |
| `openai:gpt-5.4-nano` | `memory_compiler` | 1.000 | 0.921-1.000 | 45 / 45 |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.4-nano` | `slack_intake` | 1.000 | 0.940-1.000 | 60 / 60 |

Operational failure classes:
- `provider_error`: 6
- `rate_limit_error`: 51
- `timeout`: 174

## Schema validity

| Model | Role | Schema validity | 95% CI | Valid / Operationally successful |
|---|---|---:|---:|---:|
| `anthropic:claude-haiku-4-5-20251001` | `conflict_classifier` | 1.000 | 0.896-1.000 | 33 / 33 |
| `anthropic:claude-haiku-4-5-20251001` | `entity_resolution` | 1.000 | 0.701-1.000 | 9 / 9 |
| `anthropic:claude-haiku-4-5-20251001` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `anthropic:claude-sonnet-4-6` | `conflict_classifier` | 1.000 | 0.896-1.000 | 33 / 33 |
| `aws-bedrock:mistral.ministral-3-14b-instruct` | `memory_compiler` | 0.956 | 0.852-0.988 | 43 / 45 |
| `aws-bedrock:mistral.ministral-3-14b-instruct` | `slack_intake` | 0.983 | 0.911-0.997 | 59 / 60 |
| `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `slack_intake` | 0.150 | 0.081-0.261 | 9 / 60 |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `conflict_classifier` | 0.000 | 0.000-0.000 | 0 / 0 |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `memory_compiler` | 0.000 | 0.000-0.000 | 0 / 0 |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `recall_synthesizer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `slack_intake` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-2.5-flash` | `conflict_classifier` | 0.606 | 0.437-0.753 | 20 / 33 |
| `google:gemini-2.5-flash` | `entity_resolution` | 0.889 | 0.565-0.980 | 8 / 9 |
| `google:gemini-2.5-flash` | `memory_compiler` | 0.244 | 0.142-0.387 | 11 / 45 |
| `google:gemini-2.5-flash` | `recall_synthesizer` | 0.889 | 0.747-0.956 | 32 / 36 |
| `google:gemini-2.5-flash` | `slack_intake` | 0.600 | 0.474-0.714 | 36 / 60 |
| `google:gemini-2.5-flash-lite` | `memory_compiler` | 1.000 | 0.921-1.000 | 45 / 45 |
| `google:gemini-2.5-flash-lite` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `google:gemini-2.5-flash-lite` | `slack_intake` | 0.983 | 0.911-0.997 | 59 / 60 |
| `google:gemini-2.5-pro` | `conflict_classifier` | 0.594 | 0.423-0.745 | 19 / 32 |
| `groq:llama-3.1-8b-instant` | `slack_intake` | 0.977 | 0.879-0.996 | 42 / 43 |
| `groq:llama-3.3-70b-versatile` | `memory_compiler` | 1.000 | 0.912-1.000 | 40 / 40 |
| `groq:llama-3.3-70b-versatile` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `groq:openai/gpt-oss-120b` | `conflict_classifier` | 1.000 | 0.851-1.000 | 22 / 22 |
| `groq:openai/gpt-oss-120b` | `memory_compiler` | 1.000 | 0.898-1.000 | 34 / 34 |
| `groq:openai/gpt-oss-120b` | `recall_synthesizer` | 1.000 | 0.862-1.000 | 24 / 24 |
| `openai:gpt-5.4-mini` | `conflict_classifier` | 1.000 | 0.896-1.000 | 33 / 33 |
| `openai:gpt-5.4-mini` | `entity_resolution` | 1.000 | 0.701-1.000 | 9 / 9 |
| `openai:gpt-5.4-mini` | `memory_compiler` | 1.000 | 0.921-1.000 | 45 / 45 |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.4-mini` | `slack_intake` | 1.000 | 0.940-1.000 | 60 / 60 |
| `openai:gpt-5.4-nano` | `entity_resolution` | 1.000 | 0.701-1.000 | 9 / 9 |
| `openai:gpt-5.4-nano` | `memory_compiler` | 1.000 | 0.921-1.000 | 45 / 45 |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.4-nano` | `slack_intake` | 1.000 | 0.940-1.000 | 60 / 60 |

Schema / parse failure classes:
- `json_parse_error`: 130
- `schema_invalid`: 15

## Safety / zero-tolerance failures

| Model | Role | Zero-tolerance failures | Upper 95% fail rate | Eligible |
|---|---|---:|---:|---|
| `anthropic:claude-haiku-4-5-20251001` | `conflict_classifier` | 27 | 0.914 | False |
| `anthropic:claude-haiku-4-5-20251001` | `entity_resolution` | 6 | 0.879 | False |
| `anthropic:claude-haiku-4-5-20251001` | `recall_synthesizer` | 0 | 0.083 | False |
| `anthropic:claude-sonnet-4-6` | `conflict_classifier` | 27 | 0.914 | False |
| `aws-bedrock:mistral.ministral-3-14b-instruct` | `memory_compiler` | 18 | 0.545 | False |
| `aws-bedrock:mistral.ministral-3-14b-instruct` | `slack_intake` | 15 | 0.372 | False |
| `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `slack_intake` | 0 | 0.050 | False |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `conflict_classifier` | 0 | 0.091 | False |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `memory_compiler` | 0 | 0.067 | False |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `recall_synthesizer` | 0 | 0.083 | False |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `slack_intake` | 0 | 0.050 | False |
| `google:gemini-2.5-flash` | `conflict_classifier` | 14 | 0.592 | False |
| `google:gemini-2.5-flash` | `entity_resolution` | 5 | 0.811 | False |
| `google:gemini-2.5-flash` | `memory_compiler` | 6 | 0.262 | False |
| `google:gemini-2.5-flash` | `recall_synthesizer` | 1 | 0.142 | False |
| `google:gemini-2.5-flash` | `slack_intake` | 11 | 0.299 | False |
| `google:gemini-2.5-flash-lite` | `memory_compiler` | 20 | 0.588 | False |
| `google:gemini-2.5-flash-lite` | `recall_synthesizer` | 0 | 0.083 | False |
| `google:gemini-2.5-flash-lite` | `slack_intake` | 15 | 0.372 | False |
| `google:gemini-2.5-pro` | `conflict_classifier` | 13 | 0.563 | False |
| `groq:llama-3.1-8b-instant` | `slack_intake` | 13 | 0.336 | False |
| `groq:llama-3.3-70b-versatile` | `memory_compiler` | 21 | 0.609 | False |
| `groq:llama-3.3-70b-versatile` | `recall_synthesizer` | 0 | 0.083 | False |
| `groq:openai/gpt-oss-120b` | `conflict_classifier` | 16 | 0.648 | False |
| `groq:openai/gpt-oss-120b` | `memory_compiler` | 17 | 0.524 | False |
| `groq:openai/gpt-oss-120b` | `recall_synthesizer` | 1 | 0.142 | False |
| `openai:gpt-5.4-mini` | `conflict_classifier` | 26 | 0.893 | False |
| `openai:gpt-5.4-mini` | `entity_resolution` | 4 | 0.733 | False |
| `openai:gpt-5.4-mini` | `memory_compiler` | 21 | 0.609 | False |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | 0 | 0.083 | False |
| `openai:gpt-5.4-mini` | `slack_intake` | 15 | 0.372 | False |
| `openai:gpt-5.4-nano` | `entity_resolution` | 6 | 0.879 | False |
| `openai:gpt-5.4-nano` | `memory_compiler` | 20 | 0.588 | False |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | 2 | 0.181 | False |
| `openai:gpt-5.4-nano` | `slack_intake` | 15 | 0.372 | False |

## Quality scores by role

| Model | Role | Category | Semantic score | 95% CI | Semantic evals | Eligible | Rejection reasons |
|---|---|---|---:|---:|---:|---|---|
| `anthropic:claude-haiku-4-5-20251001` | `conflict_classifier` | `runtime` | 0.718 | 0.662-0.767 | 33 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `anthropic:claude-haiku-4-5-20251001` | `entity_resolution` | `runtime_or_support` | 0.757 | 0.667-0.854 | 9 | False | zero_tolerance_failures_present |
| `anthropic:claude-haiku-4-5-20251001` | `recall_synthesizer` | `runtime` | 0.923 | 0.867-0.970 | 36 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, groundedness_below_threshold |
| `anthropic:claude-sonnet-4-6` | `conflict_classifier` | `runtime` | 0.744 | 0.697-0.784 | 33 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `aws-bedrock:mistral.ministral-3-14b-instruct` | `memory_compiler` | `runtime` | 0.727 | 0.681-0.770 | 43 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, memory_card_extraction_below_threshold |
| `aws-bedrock:mistral.ministral-3-14b-instruct` | `slack_intake` | `runtime` | 0.750 | 0.699-0.799 | 59 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `slack_intake` | `runtime` | 0.722 | 0.575-0.861 | 9 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `conflict_classifier` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `memory_compiler` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `recall_synthesizer` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `slack_intake` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-2.5-flash` | `conflict_classifier` | `runtime` | 0.720 | 0.663-0.771 | 20 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `google:gemini-2.5-flash` | `entity_resolution` | `runtime_or_support` | 0.763 | 0.713-0.819 | 8 | False | zero_tolerance_failures_present |
| `google:gemini-2.5-flash` | `memory_compiler` | `runtime` | 0.701 | 0.663-0.757 | 11 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, memory_card_extraction_below_threshold |
| `google:gemini-2.5-flash` | `recall_synthesizer` | `runtime` | 0.939 | 0.890-0.984 | 32 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, groundedness_below_threshold |
| `google:gemini-2.5-flash` | `slack_intake` | `runtime` | 0.722 | 0.674-0.770 | 36 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `google:gemini-2.5-flash-lite` | `memory_compiler` | `runtime` | 0.709 | 0.670-0.744 | 45 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, memory_card_extraction_below_threshold |
| `google:gemini-2.5-flash-lite` | `recall_synthesizer` | `runtime` | 0.933 | 0.892-0.970 | 36 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, groundedness_below_threshold |
| `google:gemini-2.5-flash-lite` | `slack_intake` | `runtime` | 0.740 | 0.697-0.782 | 59 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `google:gemini-2.5-pro` | `conflict_classifier` | `runtime` | 0.727 | 0.681-0.779 | 19 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `groq:llama-3.1-8b-instant` | `slack_intake` | `runtime` | 0.689 | 0.637-0.742 | 42 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `groq:llama-3.3-70b-versatile` | `memory_compiler` | `runtime` | 0.652 | 0.620-0.683 | 40 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, memory_card_extraction_below_threshold |
| `groq:llama-3.3-70b-versatile` | `recall_synthesizer` | `runtime` | 0.934 | 0.883-0.976 | 36 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, groundedness_below_threshold |
| `groq:openai/gpt-oss-120b` | `conflict_classifier` | `runtime` | 0.736 | 0.685-0.781 | 22 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `groq:openai/gpt-oss-120b` | `memory_compiler` | `runtime` | 0.676 | 0.633-0.717 | 34 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, memory_card_extraction_below_threshold |
| `groq:openai/gpt-oss-120b` | `recall_synthesizer` | `runtime` | 0.915 | 0.866-0.965 | 24 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, groundedness_below_threshold |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `runtime` | 0.723 | 0.672-0.771 | 33 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `openai:gpt-5.4-mini` | `entity_resolution` | `runtime_or_support` | 0.796 | 0.745-0.847 | 9 | False | zero_tolerance_failures_present |
| `openai:gpt-5.4-mini` | `memory_compiler` | `runtime` | 0.715 | 0.673-0.753 | 45 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, memory_card_extraction_below_threshold |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `runtime` | 0.922 | 0.878-0.964 | 36 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, groundedness_below_threshold |
| `openai:gpt-5.4-mini` | `slack_intake` | `runtime` | 0.738 | 0.692-0.783 | 60 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `openai:gpt-5.4-nano` | `entity_resolution` | `runtime_or_support` | 0.782 | 0.713-0.875 | 9 | False | zero_tolerance_failures_present |
| `openai:gpt-5.4-nano` | `memory_compiler` | `runtime` | 0.709 | 0.666-0.746 | 45 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, memory_card_extraction_below_threshold |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `runtime` | 0.890 | 0.846-0.939 | 36 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, groundedness_below_threshold |
| `openai:gpt-5.4-nano` | `slack_intake` | `runtime` | 0.744 | 0.692-0.793 | 60 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |

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
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `anthropic:claude-sonnet-4-6` | 33 | 33 | -0.026 (-0.062--0.000) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `aws-bedrock:nvidia.nemotron-super-3-120b` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-2.5-flash` | 33 | 20 | -0.032 (-0.092-0.020) | 0.000 (0.000-0.000) | 0.394 (0.133-0.667) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-2.5-pro` | 33 | 19 | -0.016 (-0.064-0.027) | 0.030 (0.000-0.139) | 0.424 (0.152-0.667) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-pro` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `groq:openai/gpt-oss-120b` | 33 | 22 | -0.017 (-0.067-0.025) | 0.333 (0.133-0.556) | 0.333 (0.133-0.556) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-mini` | 33 | 33 | -0.005 (-0.048-0.028) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `aws-bedrock:nvidia.nemotron-super-3-120b` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `google:gemini-2.5-flash` | 33 | 20 | 0.003 (-0.037-0.042) | 0.000 (0.000-0.000) | 0.394 (0.133-0.667) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `google:gemini-2.5-pro` | 33 | 19 | 0.012 (-0.021-0.044) | 0.030 (0.000-0.139) | 0.424 (0.152-0.667) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-pro` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `groq:openai/gpt-oss-120b` | 33 | 22 | 0.012 (-0.015-0.042) | 0.333 (0.133-0.556) | 0.333 (0.133-0.556) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.4-mini` | 33 | 33 | 0.021 (-0.002-0.043) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-2.5-flash` | 33 | 0 | n/a | -1.000 (-1.000--1.000) | -0.606 (-0.867--0.333) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-2.5-pro` | 33 | 0 | n/a | -0.970 (-1.000--0.861) | -0.576 (-0.848--0.333) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `groq:openai/gpt-oss-120b` | 33 | 0 | n/a | -0.667 (-0.867--0.444) | -0.667 (-0.867--0.444) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-mini` | 33 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `google:gemini-2.5-pro` | 33 | 13 | 0.010 (-0.048-0.072) | 0.030 (0.000-0.139) | 0.030 (-0.333-0.389) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `groq:openai/gpt-oss-120b` | 33 | 12 | -0.007 (-0.051-0.047) | 0.333 (0.133-0.556) | -0.061 (-0.389-0.278) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `openai:gpt-5.4-mini` | 33 | 20 | 0.019 (-0.027-0.066) | 0.000 (0.000-0.000) | -0.394 (-0.667--0.133) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `groq:openai/gpt-oss-120b` | 33 | 10 | 0.015 (-0.023-0.049) | 0.303 (0.091-0.533) | -0.091 (-0.455-0.300) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `openai:gpt-5.4-mini` | 33 | 19 | 0.005 (-0.048-0.050) | -0.030 (-0.139-0.000) | -0.424 (-0.667--0.167) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `conflict_classifier` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-mini` | 33 | 22 | 0.009 (-0.029-0.048) | -0.333 (-0.556--0.133) | -0.333 (-0.556--0.133) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-2.5-flash` | 9 | 8 | -0.005 (-0.056-0.042) | 0.000 (0.000-0.000) | 0.111 (0.000-0.444) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-mini` | 9 | 9 | -0.039 (-0.139-0.028) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-nano` | 9 | 9 | -0.025 (-0.060-0.000) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `entity_resolution` | `google:gemini-2.5-flash` | `openai:gpt-5.4-mini` | 9 | 8 | -0.039 (-0.116-0.006) | 0.000 (0.000-0.000) | -0.111 (-0.444-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `entity_resolution` | `google:gemini-2.5-flash` | `openai:gpt-5.4-nano` | 9 | 8 | -0.023 (-0.070-0.024) | 0.000 (0.000-0.000) | -0.111 (-0.444-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `entity_resolution` | `openai:gpt-5.4-mini` | `openai:gpt-5.4-nano` | 9 | 9 | 0.014 (-0.042-0.102) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `aws-bedrock:nvidia.nemotron-super-3-120b` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.956 (0.867-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `google:gemini-2.5-flash` | 45 | 10 | 0.028 (-0.036-0.071) | 0.000 (0.000-0.000) | 0.711 (0.458-0.952) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `google:gemini-2.5-flash-lite` | 45 | 43 | 0.019 (-0.003-0.043) | 0.000 (0.000-0.000) | -0.044 (-0.133-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `groq:llama-3.3-70b-versatile` | 45 | 38 | 0.072 (0.035-0.110) | 0.111 (0.021-0.238) | 0.067 (-0.071-0.208) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `groq:openai/gpt-oss-120b` | 45 | 32 | 0.053 (0.023-0.081) | 0.244 (0.111-0.400) | 0.200 (0.022-0.378) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4-mini` | 45 | 43 | 0.014 (-0.013-0.051) | 0.000 (0.000-0.000) | -0.044 (-0.133-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4-nano` | 45 | 43 | 0.020 (-0.010-0.061) | 0.000 (0.000-0.000) | -0.044 (-0.133-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-2.5-flash` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -0.244 (-0.471--0.024) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-2.5-flash-lite` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `groq:llama-3.3-70b-versatile` | 45 | 0 | n/a | -0.889 (-0.979--0.762) | -0.889 (-0.979--0.762) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `groq:openai/gpt-oss-120b` | 45 | 0 | n/a | -0.756 (-0.889--0.600) | -0.756 (-0.889--0.600) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-mini` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-nano` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash` | `google:gemini-2.5-flash-lite` | 45 | 11 | -0.023 (-0.080-0.054) | 0.000 (0.000-0.000) | -0.756 (-0.976--0.529) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `memory_compiler` | `google:gemini-2.5-flash` | `groq:llama-3.3-70b-versatile` | 45 | 9 | 0.046 (0.021-0.076) | 0.111 (0.021-0.238) | -0.644 (-0.905--0.370) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `google:gemini-2.5-flash` | `groq:openai/gpt-oss-120b` | 45 | 10 | 0.017 (-0.042-0.083) | 0.244 (0.111-0.400) | -0.511 (-0.762--0.267) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `google:gemini-2.5-flash` | `openai:gpt-5.4-mini` | 45 | 11 | -0.034 (-0.077-0.027) | 0.000 (0.000-0.000) | -0.756 (-0.976--0.529) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `memory_compiler` | `google:gemini-2.5-flash` | `openai:gpt-5.4-nano` | 45 | 11 | -0.027 (-0.068-0.045) | 0.000 (0.000-0.000) | -0.756 (-0.976--0.529) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `groq:llama-3.3-70b-versatile` | 45 | 40 | 0.054 (0.024-0.084) | 0.111 (0.021-0.238) | 0.111 (0.021-0.238) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `groq:openai/gpt-oss-120b` | 45 | 34 | 0.030 (0.005-0.052) | 0.244 (0.111-0.400) | 0.244 (0.111-0.400) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-mini` | 45 | 45 | -0.006 (-0.029-0.022) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-nano` | 45 | 45 | 0.001 (-0.024-0.029) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `memory_compiler` | `groq:llama-3.3-70b-versatile` | `groq:openai/gpt-oss-120b` | 45 | 29 | -0.016 (-0.045-0.012) | 0.133 (-0.071-0.333) | 0.133 (-0.071-0.333) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:openai/gpt-oss-120b` if a tie-break is required. |
| `memory_compiler` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4-mini` | 45 | 40 | -0.060 (-0.090--0.030) | -0.111 (-0.238--0.021) | -0.111 (-0.238--0.021) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4-nano` | 45 | 40 | -0.058 (-0.091--0.024) | -0.111 (-0.238--0.021) | -0.111 (-0.238--0.021) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-mini` | 45 | 34 | -0.036 (-0.068-0.004) | -0.244 (-0.400--0.111) | -0.244 (-0.400--0.111) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-nano` | 45 | 34 | -0.028 (-0.061-0.011) | -0.244 (-0.400--0.111) | -0.244 (-0.400--0.111) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `openai:gpt-5.4-mini` | `openai:gpt-5.4-nano` | 45 | 45 | 0.006 (-0.013-0.027) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `aws-bedrock:nvidia.nemotron-super-3-120b` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-2.5-flash` | 36 | 32 | -0.019 (-0.101-0.051) | 0.000 (0.000-0.000) | 0.111 (0.000-0.267) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-2.5-flash-lite` | 36 | 36 | -0.010 (-0.078-0.043) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `groq:llama-3.3-70b-versatile` | 36 | 36 | -0.011 (-0.070-0.037) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:llama-3.3-70b-versatile` if a tie-break is required. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `groq:openai/gpt-oss-120b` | 36 | 24 | -0.011 (-0.078-0.038) | 0.333 (0.133-0.545) | 0.333 (0.133-0.545) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-mini` | 36 | 36 | 0.001 (-0.049-0.040) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-nano` | 36 | 36 | 0.033 (-0.039-0.095) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-2.5-flash` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -0.889 (-1.000--0.733) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-2.5-flash-lite` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `groq:llama-3.3-70b-versatile` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `groq:openai/gpt-oss-120b` | 36 | 0 | n/a | -0.667 (-0.867--0.455) | -0.667 (-0.867--0.455) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-mini` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-nano` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `google:gemini-2.5-flash-lite` | 36 | 32 | 0.007 (-0.022-0.034) | 0.000 (0.000-0.000) | -0.111 (-0.267-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `groq:llama-3.3-70b-versatile` | 36 | 32 | 0.001 (-0.040-0.043) | 0.000 (0.000-0.000) | -0.111 (-0.267-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:llama-3.3-70b-versatile` if a tie-break is required. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `groq:openai/gpt-oss-120b` | 36 | 20 | 0.017 (-0.019-0.050) | 0.333 (0.133-0.545) | 0.222 (-0.061-0.489) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `openai:gpt-5.4-mini` | 36 | 32 | 0.021 (-0.023-0.062) | 0.000 (0.000-0.000) | -0.111 (-0.267-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `openai:gpt-5.4-nano` | 36 | 32 | 0.052 (0.018-0.092) | 0.000 (0.000-0.000) | -0.111 (-0.267-0.000) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `groq:llama-3.3-70b-versatile` | 36 | 36 | -0.001 (-0.034-0.038) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `groq:openai/gpt-oss-120b` | 36 | 24 | 0.017 (-0.016-0.051) | 0.333 (0.133-0.545) | 0.333 (0.133-0.545) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-mini` | 36 | 36 | 0.010 (-0.031-0.048) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-nano` | 36 | 36 | 0.043 (0.007-0.084) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `recall_synthesizer` | `groq:llama-3.3-70b-versatile` | `groq:openai/gpt-oss-120b` | 36 | 24 | -0.000 (-0.055-0.043) | 0.333 (0.133-0.545) | 0.333 (0.133-0.545) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4-mini` | 36 | 36 | 0.012 (-0.034-0.054) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:llama-3.3-70b-versatile` if a tie-break is required. |
| `recall_synthesizer` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4-nano` | 36 | 36 | 0.044 (-0.015-0.099) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:llama-3.3-70b-versatile` if a tie-break is required. |
| `recall_synthesizer` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-mini` | 36 | 24 | 0.007 (-0.033-0.044) | -0.333 (-0.545--0.133) | -0.333 (-0.545--0.133) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-nano` | 36 | 24 | 0.034 (0.003-0.072) | -0.333 (-0.545--0.133) | -0.333 (-0.545--0.133) | tradeoff_quality_vs_ops: One model has higher semantic quality while the other is more operationally reliable. |
| `recall_synthesizer` | `openai:gpt-5.4-mini` | `openai:gpt-5.4-nano` | 36 | 36 | 0.032 (-0.007-0.071) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | 60 | 8 | -0.016 (-0.125-0.083) | 0.000 (0.000-0.000) | 0.833 (0.667-0.967) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `aws-bedrock:nvidia.nemotron-super-3-120b` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `google:gemini-2.5-flash` | 60 | 36 | 0.009 (-0.030-0.049) | 0.000 (0.000-0.000) | 0.383 (0.233-0.550) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `google:gemini-2.5-flash-lite` | 60 | 58 | 0.009 (-0.019-0.036) | 0.000 (0.000-0.000) | 0.000 (-0.067-0.067) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `groq:llama-3.1-8b-instant` | 60 | 41 | 0.062 (0.033-0.091) | 0.283 (0.150-0.417) | 0.283 (0.150-0.433) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4-mini` | 60 | 59 | 0.012 (-0.013-0.043) | 0.000 (0.000-0.000) | -0.017 (-0.067-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4-nano` | 60 | 59 | 0.004 (-0.020-0.029) | 0.000 (0.000-0.000) | -0.017 (-0.067-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `aws-bedrock:nvidia.nemotron-super-3-120b` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.150 (0.033-0.300) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `google:gemini-2.5-flash` | 60 | 4 | -0.047 (-0.188-0.047) | 0.000 (0.000-0.000) | -0.450 (-0.650--0.217) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:nvidia.nemotron-nano-9b-v2` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `google:gemini-2.5-flash-lite` | 60 | 8 | 0.023 (-0.047-0.098) | 0.000 (0.000-0.000) | -0.833 (-0.967--0.667) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `groq:llama-3.1-8b-instant` | 60 | 8 | 0.062 (0.000-0.143) | 0.283 (0.150-0.417) | -0.550 (-0.717--0.367) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `openai:gpt-5.4-mini` | 60 | 9 | 0.000 (-0.083-0.075) | 0.000 (0.000-0.000) | -0.850 (-0.967--0.700) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:nvidia.nemotron-nano-9b-v2` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `openai:gpt-5.4-nano` | 60 | 9 | 0.035 (-0.011-0.089) | 0.000 (0.000-0.000) | -0.850 (-0.967--0.700) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:nvidia.nemotron-nano-9b-v2` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-2.5-flash` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -0.600 (-0.750--0.433) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-2.5-flash-lite` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -0.983 (-1.000--0.933) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `groq:llama-3.1-8b-instant` | 60 | 0 | n/a | -0.717 (-0.850--0.583) | -0.700 (-0.833--0.567) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-mini` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-nano` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-2.5-flash` | `google:gemini-2.5-flash-lite` | 60 | 36 | -0.000 (-0.031-0.031) | 0.000 (0.000-0.000) | -0.383 (-0.533--0.233) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `slack_intake` | `google:gemini-2.5-flash` | `groq:llama-3.1-8b-instant` | 60 | 24 | 0.043 (0.006-0.087) | 0.283 (0.150-0.417) | -0.100 (-0.317-0.117) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `google:gemini-2.5-flash` | `openai:gpt-5.4-mini` | 60 | 36 | -0.002 (-0.030-0.033) | 0.000 (0.000-0.000) | -0.400 (-0.567--0.250) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `slack_intake` | `google:gemini-2.5-flash` | `openai:gpt-5.4-nano` | 60 | 36 | -0.009 (-0.045-0.028) | 0.000 (0.000-0.000) | -0.400 (-0.567--0.250) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `groq:llama-3.1-8b-instant` | 60 | 42 | 0.045 (0.016-0.070) | 0.283 (0.150-0.417) | 0.283 (0.150-0.417) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-mini` | 60 | 59 | 0.004 (-0.030-0.039) | 0.000 (0.000-0.000) | -0.017 (-0.067-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-nano` | 60 | 59 | -0.003 (-0.032-0.024) | 0.000 (0.000-0.000) | -0.017 (-0.067-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `slack_intake` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.4-mini` | 60 | 42 | -0.048 (-0.080--0.016) | -0.283 (-0.417--0.150) | -0.300 (-0.433--0.167) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.4-nano` | 60 | 42 | -0.058 (-0.087--0.031) | -0.283 (-0.417--0.150) | -0.300 (-0.433--0.167) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `openai:gpt-5.4-mini` | `openai:gpt-5.4-nano` | 60 | 60 | -0.006 (-0.034-0.022) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |

## Cost and latency

| Model | Role | Cost / 1k successful | p50 ms | p90 ms | p95 ms |
|---|---|---:|---:|---:|---:|
| `anthropic:claude-haiku-4-5-20251001` | `conflict_classifier` | $3.2025 | 4513 | 5452 | 5536 |
| `anthropic:claude-haiku-4-5-20251001` | `entity_resolution` | $2.5906 | 3917 | 4780 | 5370 |
| `anthropic:claude-haiku-4-5-20251001` | `recall_synthesizer` | $2.8203 | 4142 | 5366 | 5752 |
| `anthropic:claude-sonnet-4-6` | `conflict_classifier` | $11.7824 | 11574 | 14294 | 14306 |
| `aws-bedrock:mistral.ministral-3-14b-instruct` | `memory_compiler` | $0.2622 | 5709 | 7954 | 9873 |
| `aws-bedrock:mistral.ministral-3-14b-instruct` | `slack_intake` | $0.1777 | 2557 | 3884 | 9418 |
| `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `slack_intake` | $0.2349 | 5778 | 8947 | 9559 |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `conflict_classifier` | n/a | 0 | 0 | 0 |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `memory_compiler` | n/a | 0 | 0 | 0 |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `recall_synthesizer` | n/a | 0 | 0 | 0 |
| `aws-bedrock:nvidia.nemotron-super-3-120b` | `slack_intake` | n/a | 0 | 0 | 0 |
| `google:gemini-2.5-flash` | `conflict_classifier` | $0.7962 | 8729 | 10207 | 10325 |
| `google:gemini-2.5-flash` | `entity_resolution` | $0.6584 | 3558 | 8522 | 9334 |
| `google:gemini-2.5-flash` | `memory_compiler` | $0.9066 | 9422 | 10286 | 10679 |
| `google:gemini-2.5-flash` | `recall_synthesizer` | $0.7634 | 5805 | 8873 | 9293 |
| `google:gemini-2.5-flash` | `slack_intake` | $0.6735 | 7654 | 10124 | 10483 |
| `google:gemini-2.5-flash-lite` | `memory_compiler` | $0.1971 | 7522 | 16072 | 18271 |
| `google:gemini-2.5-flash-lite` | `recall_synthesizer` | $0.1384 | 6980 | 13153 | 14711 |
| `google:gemini-2.5-flash-lite` | `slack_intake` | $0.1431 | 8259 | 17748 | 21019 |
| `google:gemini-2.5-pro` | `conflict_classifier` | $3.1159 | 13940 | 16631 | 16981 |
| `groq:llama-3.1-8b-instant` | `slack_intake` | $0.0487 | 3841 | 7880 | 8016 |
| `groq:llama-3.3-70b-versatile` | `memory_compiler` | $0.6016 | 2473 | 7579 | 8209 |
| `groq:llama-3.3-70b-versatile` | `recall_synthesizer` | $0.5128 | 4067 | 4393 | 4435 |
| `groq:openai/gpt-oss-120b` | `conflict_classifier` | $0.2508 | 7495 | 8912 | 9125 |
| `groq:openai/gpt-oss-120b` | `memory_compiler` | $0.2428 | 8952 | 9799 | 9928 |
| `groq:openai/gpt-oss-120b` | `recall_synthesizer` | $0.2361 | 7583 | 9387 | 9449 |
| `openai:gpt-5.4-mini` | `conflict_classifier` | $1.8912 | 3724 | 4953 | 15818 |
| `openai:gpt-5.4-mini` | `entity_resolution` | $1.5093 | 3614 | 4287 | 6560 |
| `openai:gpt-5.4-mini` | `memory_compiler` | $2.1893 | 3704 | 6825 | 18112 |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | $1.6844 | 2910 | 4579 | 4644 |
| `openai:gpt-5.4-mini` | `slack_intake` | $1.5414 | 3396 | 4460 | 5064 |
| `openai:gpt-5.4-nano` | `entity_resolution` | $0.5562 | 4167 | 5084 | 5246 |
| `openai:gpt-5.4-nano` | `memory_compiler` | $0.8306 | 4750 | 6773 | 7979 |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | $0.5295 | 3370 | 6437 | 9003 |
| `openai:gpt-5.4-nano` | `slack_intake` | $0.5141 | 3803 | 4697 | 5106 |

## Why non-deployable, if applicable

Missing mandatory roles:
- conflict_classifier
- embeddings
- memory_compiler
- recall_synthesizer
- router
- slack_intake

Observed rejection reasons:
- `conflict_classifier`: conflict_safety_below_threshold (6), operational_success_below_threshold (7), schema_validity_below_threshold (7), semantic_score_below_threshold (6), semantic_score_not_evaluated (1), zero_tolerance_failures_present (6)
- `embeddings`: no eligible candidates were evaluated for this role.
- `memory_compiler`: memory_card_extraction_below_threshold (7), operational_success_below_threshold (8), schema_validity_below_threshold (8), semantic_score_below_threshold (7), semantic_score_not_evaluated (1), zero_tolerance_failures_present (7)
- `recall_synthesizer`: groundedness_below_threshold (7), operational_success_below_threshold (8), schema_validity_below_threshold (8), semantic_score_below_threshold (7), semantic_score_not_evaluated (1), zero_tolerance_failures_present (3)
- `router`: no eligible candidates were evaluated for this role.
- `slack_intake`: decision_correctness_below_threshold (7), operational_success_below_threshold (8), repair_option_usefulness_below_threshold (7), schema_validity_below_threshold (8), semantic_score_below_threshold (7), semantic_score_not_evaluated (1), zero_tolerance_failures_present (6)

## Next actions

- Restore mandatory coverage for: conflict_classifier, embeddings, memory_compiler, recall_synthesizer, router, slack_intake.
- Eliminate the largest blocking failure classes first: quality_failure (557), zero_tolerance_failure (355), timeout (174).
- Rerun after operational issues are fixed so semantic comparisons are based on overlapping evaluable variants.
- Add or refine role-specific fixtures if a mandatory role remains unevaluable after provider issues are resolved.
