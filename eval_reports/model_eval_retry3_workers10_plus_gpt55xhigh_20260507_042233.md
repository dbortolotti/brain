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
Only judge, debug/admin, support had eligible candidates. Treat this as a harness validation run, not a model-selection run.

Eligible partials:
- `debug_explainer`: `openai:gpt-5.4-medium`
- `entity_resolution`: `google:gemini-3.1-pro-preview`
- `eval_judge`: `openai:gpt-5.4-low`
- `validator_critic`: `openai:gpt-5.4-medium`

## Deployability status

- Run ID: `appended_new_thinking_variants_reconstructed_20260507`
- Fixture set: `production+eval_judge+new_thinking_variants_reconstructed`
- JSONL output: `eval_runs/prod_retry3_workers10_plus_gpt55xhigh_20260507_042233.jsonl`
- Records: `12243`
- Model-role summaries: `171`
- Deployable stack: `no`
- Eligible runtime role pairs: `0`
- Eligible embedding role pairs: `0`
- Eligible judge role pairs: `16`
- Eligible debug/admin role pairs: `14`
- Eligible support role pairs: `24`

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
| `anthropic:claude-haiku-4-5-20251001` | `conflict_classifier` | 1.000 | 0.896-1.000 | 33 / 33 |
| `anthropic:claude-haiku-4-5-20251001` | `entity_resolution` | 1.000 | 0.701-1.000 | 9 / 9 |
| `anthropic:claude-haiku-4-5-20251001` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `anthropic:claude-opus-4-7` | `eval_judge` | 0.000 | 0.000-0.243 | 0 / 12 |
| `anthropic:claude-sonnet-4-6` | `conflict_classifier` | 1.000 | 0.896-1.000 | 33 / 33 |
| `anthropic:claude-sonnet-4-6` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |
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
| `google:gemini-2.5-flash-lite` | `router` | 1.000 | 0.610-1.000 | 6 / 6 |
| `google:gemini-2.5-flash-lite` | `slack_intake` | 1.000 | 0.940-1.000 | 60 / 60 |
| `google:gemini-2.5-pro` | `conflict_classifier` | 0.970 | 0.847-0.995 | 32 / 33 |
| `google:gemini-3.1-pro-preview` | `conflict_classifier` | 0.000 | 0.000-0.037 | 0 / 99 |
| `google:gemini-3.1-pro-preview` | `debug_explainer` | 0.000 | 0.000-0.051 | 0 / 72 |
| `google:gemini-3.1-pro-preview` | `entity_resolution` | 0.000 | 0.000-0.125 | 0 / 27 |
| `google:gemini-3.1-pro-preview` | `eval_judge` | 0.000 | 0.000-0.096 | 0 / 36 |
| `google:gemini-3.1-pro-preview` | `memory_compiler` | 0.000 | 0.000-0.028 | 0 / 135 |
| `google:gemini-3.1-pro-preview` | `recall_synthesizer` | 0.000 | 0.000-0.034 | 0 / 108 |
| `google:gemini-3.1-pro-preview` | `router` | 0.000 | 0.000-0.176 | 0 / 18 |
| `google:gemini-3.1-pro-preview` | `slack_intake` | 0.000 | 0.000-0.021 | 0 / 180 |
| `google:gemini-3.1-pro-preview` | `validator_critic` | 0.000 | 0.000-0.041 | 0 / 90 |
| `google:gemini-3.1-pro-preview-high` | `conflict_classifier` | 0.000 | 0.000-0.037 | 0 / 99 |
| `google:gemini-3.1-pro-preview-high` | `debug_explainer` | 0.000 | 0.000-0.051 | 0 / 72 |
| `google:gemini-3.1-pro-preview-high` | `entity_resolution` | 0.000 | 0.000-0.125 | 0 / 27 |
| `google:gemini-3.1-pro-preview-high` | `eval_judge` | 0.000 | 0.000-0.096 | 0 / 36 |
| `google:gemini-3.1-pro-preview-high` | `memory_compiler` | 0.000 | 0.000-0.028 | 0 / 135 |
| `google:gemini-3.1-pro-preview-high` | `recall_synthesizer` | 0.000 | 0.000-0.034 | 0 / 108 |
| `google:gemini-3.1-pro-preview-high` | `router` | 0.000 | 0.000-0.176 | 0 / 18 |
| `google:gemini-3.1-pro-preview-high` | `slack_intake` | 0.000 | 0.000-0.021 | 0 / 180 |
| `google:gemini-3.1-pro-preview-high` | `validator_critic` | 0.000 | 0.000-0.041 | 0 / 90 |
| `google:gemini-3.1-pro-preview-low` | `conflict_classifier` | 0.051 | 0.022-0.113 | 5 / 99 |
| `google:gemini-3.1-pro-preview-low` | `debug_explainer` | 0.000 | 0.000-0.051 | 0 / 72 |
| `google:gemini-3.1-pro-preview-low` | `entity_resolution` | 0.000 | 0.000-0.125 | 0 / 27 |
| `google:gemini-3.1-pro-preview-low` | `eval_judge` | 0.000 | 0.000-0.096 | 0 / 36 |
| `google:gemini-3.1-pro-preview-low` | `memory_compiler` | 0.000 | 0.000-0.028 | 0 / 135 |
| `google:gemini-3.1-pro-preview-low` | `recall_synthesizer` | 0.000 | 0.000-0.034 | 0 / 108 |
| `google:gemini-3.1-pro-preview-low` | `router` | 0.000 | 0.000-0.176 | 0 / 18 |
| `google:gemini-3.1-pro-preview-low` | `slack_intake` | 0.000 | 0.000-0.021 | 0 / 180 |
| `google:gemini-3.1-pro-preview-low` | `validator_critic` | 0.000 | 0.000-0.041 | 0 / 90 |
| `google:gemini-3.1-pro-preview-medium` | `conflict_classifier` | 0.000 | 0.000-0.037 | 0 / 99 |
| `google:gemini-3.1-pro-preview-medium` | `debug_explainer` | 0.000 | 0.000-0.051 | 0 / 72 |
| `google:gemini-3.1-pro-preview-medium` | `entity_resolution` | 0.000 | 0.000-0.125 | 0 / 27 |
| `google:gemini-3.1-pro-preview-medium` | `eval_judge` | 0.000 | 0.000-0.096 | 0 / 36 |
| `google:gemini-3.1-pro-preview-medium` | `memory_compiler` | 0.000 | 0.000-0.028 | 0 / 135 |
| `google:gemini-3.1-pro-preview-medium` | `recall_synthesizer` | 0.000 | 0.000-0.034 | 0 / 108 |
| `google:gemini-3.1-pro-preview-medium` | `router` | 0.000 | 0.000-0.176 | 0 / 18 |
| `google:gemini-3.1-pro-preview-medium` | `slack_intake` | 0.000 | 0.000-0.021 | 0 / 180 |
| `google:gemini-3.1-pro-preview-medium` | `validator_critic` | 0.000 | 0.000-0.041 | 0 / 90 |
| `groq:llama-3.1-8b-instant` | `router` | 0.833 | 0.436-0.970 | 5 / 6 |
| `groq:llama-3.1-8b-instant` | `slack_intake` | 0.717 | 0.592-0.815 | 43 / 60 |
| `groq:llama-3.3-70b-versatile` | `memory_compiler` | 0.889 | 0.765-0.952 | 40 / 45 |
| `groq:llama-3.3-70b-versatile` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `groq:openai/gpt-oss-120b` | `conflict_classifier` | 0.667 | 0.496-0.802 | 22 / 33 |
| `groq:openai/gpt-oss-120b` | `memory_compiler` | 0.756 | 0.613-0.858 | 34 / 45 |
| `groq:openai/gpt-oss-120b` | `recall_synthesizer` | 0.667 | 0.503-0.798 | 24 / 36 |
| `groq:openai/gpt-oss-120b` | `slack_intake` | 0.750 | 0.628-0.842 | 45 / 60 |
| `openai:gpt-5-nano` | `router` | 1.000 | 0.610-1.000 | 6 / 6 |
| `openai:gpt-5.4` | `conflict_classifier` | 0.838 | 0.753-0.898 | 83 / 99 |
| `openai:gpt-5.4` | `debug_explainer` | 0.125 | 0.067-0.221 | 9 / 72 |
| `openai:gpt-5.4` | `entity_resolution` | 0.000 | 0.000-0.125 | 0 / 27 |
| `openai:gpt-5.4` | `eval_judge` | 0.333 | 0.202-0.497 | 12 / 36 |
| `openai:gpt-5.4` | `memory_compiler` | 0.000 | 0.000-0.028 | 0 / 135 |
| `openai:gpt-5.4` | `recall_synthesizer` | 0.000 | 0.000-0.034 | 0 / 108 |
| `openai:gpt-5.4` | `router` | 0.000 | 0.000-0.176 | 0 / 18 |
| `openai:gpt-5.4` | `slack_intake` | 0.000 | 0.000-0.021 | 0 / 180 |
| `openai:gpt-5.4` | `validator_critic` | 0.000 | 0.000-0.041 | 0 / 90 |
| `openai:gpt-5.4-high` | `conflict_classifier` | 0.646 | 0.548-0.734 | 64 / 99 |
| `openai:gpt-5.4-high` | `debug_explainer` | 0.000 | 0.000-0.051 | 0 / 72 |
| `openai:gpt-5.4-high` | `entity_resolution` | 0.000 | 0.000-0.125 | 0 / 27 |
| `openai:gpt-5.4-high` | `eval_judge` | 0.000 | 0.000-0.096 | 0 / 36 |
| `openai:gpt-5.4-high` | `memory_compiler` | 0.000 | 0.000-0.028 | 0 / 135 |
| `openai:gpt-5.4-high` | `recall_synthesizer` | 0.000 | 0.000-0.034 | 0 / 108 |
| `openai:gpt-5.4-high` | `router` | 0.000 | 0.000-0.176 | 0 / 18 |
| `openai:gpt-5.4-high` | `slack_intake` | 0.000 | 0.000-0.021 | 0 / 180 |
| `openai:gpt-5.4-high` | `validator_critic` | 0.000 | 0.000-0.041 | 0 / 90 |
| `openai:gpt-5.4-low` | `conflict_classifier` | 0.737 | 0.643-0.814 | 73 / 99 |
| `openai:gpt-5.4-low` | `debug_explainer` | 1.000 | 0.949-1.000 | 72 / 72 |
| `openai:gpt-5.4-low` | `entity_resolution` | 1.000 | 0.875-1.000 | 27 / 27 |
| `openai:gpt-5.4-low` | `eval_judge` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.4-low` | `memory_compiler` | 0.370 | 0.294-0.454 | 50 / 135 |
| `openai:gpt-5.4-low` | `recall_synthesizer` | 0.000 | 0.000-0.034 | 0 / 108 |
| `openai:gpt-5.4-low` | `router` | 0.000 | 0.000-0.176 | 0 / 18 |
| `openai:gpt-5.4-low` | `slack_intake` | 0.700 | 0.629-0.762 | 126 / 180 |
| `openai:gpt-5.4-low` | `validator_critic` | 1.000 | 0.959-1.000 | 90 / 90 |
| `openai:gpt-5.4-medium` | `conflict_classifier` | 0.818 | 0.731-0.882 | 81 / 99 |
| `openai:gpt-5.4-medium` | `debug_explainer` | 0.917 | 0.830-0.961 | 66 / 72 |
| `openai:gpt-5.4-medium` | `entity_resolution` | 0.000 | 0.000-0.125 | 0 / 27 |
| `openai:gpt-5.4-medium` | `eval_judge` | 0.000 | 0.000-0.096 | 0 / 36 |
| `openai:gpt-5.4-medium` | `memory_compiler` | 0.000 | 0.000-0.028 | 0 / 135 |
| `openai:gpt-5.4-medium` | `recall_synthesizer` | 0.463 | 0.372-0.557 | 50 / 108 |
| `openai:gpt-5.4-medium` | `router` | 1.000 | 0.824-1.000 | 18 / 18 |
| `openai:gpt-5.4-medium` | `slack_intake` | 1.000 | 0.979-1.000 | 180 / 180 |
| `openai:gpt-5.4-medium` | `validator_critic` | 1.000 | 0.959-1.000 | 90 / 90 |
| `openai:gpt-5.4-mini` | `conflict_classifier` | 1.000 | 0.896-1.000 | 33 / 33 |
| `openai:gpt-5.4-mini` | `entity_resolution` | 1.000 | 0.701-1.000 | 9 / 9 |
| `openai:gpt-5.4-mini` | `memory_compiler` | 1.000 | 0.921-1.000 | 45 / 45 |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.4-mini` | `slack_intake` | 1.000 | 0.940-1.000 | 60 / 60 |
| `openai:gpt-5.4-nano` | `entity_resolution` | 1.000 | 0.701-1.000 | 9 / 9 |
| `openai:gpt-5.4-nano` | `memory_compiler` | 1.000 | 0.921-1.000 | 45 / 45 |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.4-nano` | `slack_intake` | 1.000 | 0.940-1.000 | 60 / 60 |
| `openai:gpt-5.4-xhigh` | `conflict_classifier` | 0.091 | 0.049-0.164 | 9 / 99 |
| `openai:gpt-5.4-xhigh` | `debug_explainer` | 0.000 | 0.000-0.051 | 0 / 72 |
| `openai:gpt-5.4-xhigh` | `entity_resolution` | 0.000 | 0.000-0.125 | 0 / 27 |
| `openai:gpt-5.4-xhigh` | `eval_judge` | 0.000 | 0.000-0.096 | 0 / 36 |
| `openai:gpt-5.4-xhigh` | `memory_compiler` | 0.000 | 0.000-0.028 | 0 / 135 |
| `openai:gpt-5.4-xhigh` | `recall_synthesizer` | 0.000 | 0.000-0.034 | 0 / 108 |
| `openai:gpt-5.4-xhigh` | `router` | 0.000 | 0.000-0.176 | 0 / 18 |
| `openai:gpt-5.4-xhigh` | `slack_intake` | 0.000 | 0.000-0.021 | 0 / 180 |
| `openai:gpt-5.4-xhigh` | `validator_critic` | 0.000 | 0.000-0.041 | 0 / 90 |
| `openai:gpt-5.5` | `conflict_classifier` | 0.859 | 0.777-0.914 | 85 / 99 |
| `openai:gpt-5.5` | `debug_explainer` | 0.847 | 0.747-0.912 | 61 / 72 |
| `openai:gpt-5.5` | `entity_resolution` | 1.000 | 0.875-1.000 | 27 / 27 |
| `openai:gpt-5.5` | `eval_judge` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.5` | `memory_compiler` | 1.000 | 0.972-1.000 | 135 / 135 |
| `openai:gpt-5.5` | `recall_synthesizer` | 0.306 | 0.227-0.398 | 33 / 108 |
| `openai:gpt-5.5` | `router` | 0.000 | 0.000-0.176 | 0 / 18 |
| `openai:gpt-5.5` | `slack_intake` | 0.117 | 0.078-0.172 | 21 / 180 |
| `openai:gpt-5.5` | `validator_critic` | 0.989 | 0.940-0.998 | 89 / 90 |
| `openai:gpt-5.5-high` | `conflict_classifier` | 0.788 | 0.697-0.857 | 78 / 99 |
| `openai:gpt-5.5-high` | `debug_explainer` | 0.681 | 0.566-0.777 | 49 / 72 |
| `openai:gpt-5.5-high` | `entity_resolution` | 0.000 | 0.000-0.125 | 0 / 27 |
| `openai:gpt-5.5-high` | `eval_judge` | 0.000 | 0.000-0.096 | 0 / 36 |
| `openai:gpt-5.5-high` | `memory_compiler` | 0.000 | 0.000-0.028 | 0 / 135 |
| `openai:gpt-5.5-high` | `recall_synthesizer` | 0.731 | 0.641-0.806 | 79 / 108 |
| `openai:gpt-5.5-high` | `router` | 1.000 | 0.824-1.000 | 18 / 18 |
| `openai:gpt-5.5-high` | `slack_intake` | 0.983 | 0.952-0.994 | 177 / 180 |
| `openai:gpt-5.5-high` | `validator_critic` | 1.000 | 0.959-1.000 | 90 / 90 |
| `openai:gpt-5.5-low` | `conflict_classifier` | 0.869 | 0.788-0.922 | 86 / 99 |
| `openai:gpt-5.5-low` | `debug_explainer` | 0.931 | 0.848-0.970 | 67 / 72 |
| `openai:gpt-5.5-low` | `entity_resolution` | 1.000 | 0.875-1.000 | 27 / 27 |
| `openai:gpt-5.5-low` | `eval_judge` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.5-low` | `memory_compiler` | 0.704 | 0.622-0.774 | 95 / 135 |
| `openai:gpt-5.5-low` | `recall_synthesizer` | 0.000 | 0.000-0.034 | 0 / 108 |
| `openai:gpt-5.5-low` | `router` | 0.000 | 0.000-0.176 | 0 / 18 |
| `openai:gpt-5.5-low` | `slack_intake` | 0.522 | 0.450-0.594 | 94 / 180 |
| `openai:gpt-5.5-low` | `validator_critic` | 1.000 | 0.959-1.000 | 90 / 90 |
| `openai:gpt-5.5-medium` | `conflict_classifier` | 0.788 | 0.697-0.857 | 78 / 99 |
| `openai:gpt-5.5-medium` | `debug_explainer` | 1.000 | 0.949-1.000 | 72 / 72 |
| `openai:gpt-5.5-medium` | `entity_resolution` | 1.000 | 0.875-1.000 | 27 / 27 |
| `openai:gpt-5.5-medium` | `eval_judge` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.5-medium` | `memory_compiler` | 0.104 | 0.063-0.167 | 14 / 135 |
| `openai:gpt-5.5-medium` | `recall_synthesizer` | 0.000 | 0.000-0.034 | 0 / 108 |
| `openai:gpt-5.5-medium` | `router` | 0.000 | 0.000-0.176 | 0 / 18 |
| `openai:gpt-5.5-medium` | `slack_intake` | 0.972 | 0.937-0.988 | 175 / 180 |
| `openai:gpt-5.5-medium` | `validator_critic` | 1.000 | 0.959-1.000 | 90 / 90 |
| `openai:gpt-5.5-xhigh` | `conflict_classifier` | 0.000 | 0.000-0.037 | 0 / 99 |
| `openai:gpt-5.5-xhigh` | `debug_explainer` | 0.000 | 0.000-0.051 | 0 / 72 |
| `openai:gpt-5.5-xhigh` | `entity_resolution` | 0.000 | 0.000-0.125 | 0 / 27 |
| `openai:gpt-5.5-xhigh` | `eval_judge` | 0.333 | 0.202-0.497 | 12 / 36 |
| `openai:gpt-5.5-xhigh` | `memory_compiler` | 0.000 | 0.000-0.028 | 0 / 135 |
| `openai:gpt-5.5-xhigh` | `recall_synthesizer` | 0.000 | 0.000-0.034 | 0 / 108 |
| `openai:gpt-5.5-xhigh` | `router` | 0.000 | 0.000-0.176 | 0 / 18 |
| `openai:gpt-5.5-xhigh` | `slack_intake` | 0.000 | 0.000-0.021 | 0 / 180 |
| `openai:gpt-5.5-xhigh` | `validator_critic` | 0.000 | 0.000-0.041 | 0 / 90 |
| `openai:text-embedding-3-large` | `embeddings` | 1.000 | 0.207-1.000 | 1 / 1 |
| `openai:text-embedding-3-small` | `embeddings` | 1.000 | 0.207-1.000 | 1 / 1 |
| `voyage:voyage-4-lite` | `embeddings` | 1.000 | 0.207-1.000 | 1 / 1 |

Operational failure classes:
- `provider_error`: 783
- `quota_error`: 6062
- `rate_limit_error`: 66
- `timeout`: 940

## Schema validity

| Model | Role | Schema validity | 95% CI | Valid / Operationally successful |
|---|---|---:|---:|---:|
| `anthropic:claude-haiku-4-5` | `conflict_classifier` | 1.000 | 0.896-1.000 | 33 / 33 |
| `anthropic:claude-haiku-4-5-20251001` | `conflict_classifier` | 1.000 | 0.896-1.000 | 33 / 33 |
| `anthropic:claude-haiku-4-5-20251001` | `entity_resolution` | 1.000 | 0.701-1.000 | 9 / 9 |
| `anthropic:claude-haiku-4-5-20251001` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `anthropic:claude-opus-4-7` | `eval_judge` | 0.000 | 0.000-0.000 | 0 / 0 |
| `anthropic:claude-sonnet-4-6` | `conflict_classifier` | 1.000 | 0.896-1.000 | 33 / 33 |
| `anthropic:claude-sonnet-4-6` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |
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
| `google:gemini-2.5-flash-lite` | `router` | 0.833 | 0.436-0.970 | 5 / 6 |
| `google:gemini-2.5-flash-lite` | `slack_intake` | 0.983 | 0.911-0.997 | 59 / 60 |
| `google:gemini-2.5-pro` | `conflict_classifier` | 0.594 | 0.423-0.745 | 19 / 32 |
| `google:gemini-3.1-pro-preview` | `conflict_classifier` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview` | `debug_explainer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview` | `entity_resolution` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview` | `eval_judge` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview` | `memory_compiler` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview` | `recall_synthesizer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview` | `router` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview` | `slack_intake` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview` | `validator_critic` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-high` | `conflict_classifier` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-high` | `debug_explainer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-high` | `entity_resolution` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-high` | `eval_judge` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-high` | `memory_compiler` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-high` | `recall_synthesizer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-high` | `router` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-high` | `slack_intake` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-high` | `validator_critic` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-low` | `conflict_classifier` | 1.000 | 0.566-1.000 | 5 / 5 |
| `google:gemini-3.1-pro-preview-low` | `debug_explainer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-low` | `entity_resolution` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-low` | `eval_judge` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-low` | `memory_compiler` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-low` | `recall_synthesizer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-low` | `router` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-low` | `slack_intake` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-low` | `validator_critic` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-medium` | `conflict_classifier` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-medium` | `debug_explainer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-medium` | `entity_resolution` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-medium` | `eval_judge` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-medium` | `memory_compiler` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-medium` | `recall_synthesizer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-medium` | `router` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-medium` | `slack_intake` | 0.000 | 0.000-0.000 | 0 / 0 |
| `google:gemini-3.1-pro-preview-medium` | `validator_critic` | 0.000 | 0.000-0.000 | 0 / 0 |
| `groq:llama-3.1-8b-instant` | `router` | 1.000 | 0.566-1.000 | 5 / 5 |
| `groq:llama-3.1-8b-instant` | `slack_intake` | 0.977 | 0.879-0.996 | 42 / 43 |
| `groq:llama-3.3-70b-versatile` | `memory_compiler` | 1.000 | 0.912-1.000 | 40 / 40 |
| `groq:llama-3.3-70b-versatile` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `groq:openai/gpt-oss-120b` | `conflict_classifier` | 1.000 | 0.851-1.000 | 22 / 22 |
| `groq:openai/gpt-oss-120b` | `memory_compiler` | 1.000 | 0.898-1.000 | 34 / 34 |
| `groq:openai/gpt-oss-120b` | `recall_synthesizer` | 1.000 | 0.862-1.000 | 24 / 24 |
| `groq:openai/gpt-oss-120b` | `slack_intake` | 1.000 | 0.921-1.000 | 45 / 45 |
| `openai:gpt-5-nano` | `router` | 1.000 | 0.610-1.000 | 6 / 6 |
| `openai:gpt-5.4` | `conflict_classifier` | 1.000 | 0.956-1.000 | 83 / 83 |
| `openai:gpt-5.4` | `debug_explainer` | 1.000 | 0.701-1.000 | 9 / 9 |
| `openai:gpt-5.4` | `entity_resolution` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |
| `openai:gpt-5.4` | `memory_compiler` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4` | `recall_synthesizer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4` | `router` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4` | `slack_intake` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4` | `validator_critic` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-high` | `conflict_classifier` | 0.938 | 0.850-0.975 | 60 / 64 |
| `openai:gpt-5.4-high` | `debug_explainer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-high` | `entity_resolution` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-high` | `eval_judge` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-high` | `memory_compiler` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-high` | `recall_synthesizer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-high` | `router` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-high` | `slack_intake` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-high` | `validator_critic` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-low` | `conflict_classifier` | 1.000 | 0.950-1.000 | 73 / 73 |
| `openai:gpt-5.4-low` | `debug_explainer` | 1.000 | 0.949-1.000 | 72 / 72 |
| `openai:gpt-5.4-low` | `entity_resolution` | 1.000 | 0.875-1.000 | 27 / 27 |
| `openai:gpt-5.4-low` | `eval_judge` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.4-low` | `memory_compiler` | 1.000 | 0.929-1.000 | 50 / 50 |
| `openai:gpt-5.4-low` | `recall_synthesizer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-low` | `router` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-low` | `slack_intake` | 1.000 | 0.970-1.000 | 126 / 126 |
| `openai:gpt-5.4-low` | `validator_critic` | 1.000 | 0.959-1.000 | 90 / 90 |
| `openai:gpt-5.4-medium` | `conflict_classifier` | 1.000 | 0.955-1.000 | 81 / 81 |
| `openai:gpt-5.4-medium` | `debug_explainer` | 1.000 | 0.945-1.000 | 66 / 66 |
| `openai:gpt-5.4-medium` | `entity_resolution` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-medium` | `eval_judge` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-medium` | `memory_compiler` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-medium` | `recall_synthesizer` | 1.000 | 0.929-1.000 | 50 / 50 |
| `openai:gpt-5.4-medium` | `router` | 1.000 | 0.824-1.000 | 18 / 18 |
| `openai:gpt-5.4-medium` | `slack_intake` | 1.000 | 0.979-1.000 | 180 / 180 |
| `openai:gpt-5.4-medium` | `validator_critic` | 1.000 | 0.959-1.000 | 90 / 90 |
| `openai:gpt-5.4-mini` | `conflict_classifier` | 1.000 | 0.896-1.000 | 33 / 33 |
| `openai:gpt-5.4-mini` | `entity_resolution` | 1.000 | 0.701-1.000 | 9 / 9 |
| `openai:gpt-5.4-mini` | `memory_compiler` | 1.000 | 0.921-1.000 | 45 / 45 |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.4-mini` | `slack_intake` | 1.000 | 0.940-1.000 | 60 / 60 |
| `openai:gpt-5.4-nano` | `entity_resolution` | 1.000 | 0.701-1.000 | 9 / 9 |
| `openai:gpt-5.4-nano` | `memory_compiler` | 1.000 | 0.921-1.000 | 45 / 45 |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.4-nano` | `slack_intake` | 1.000 | 0.940-1.000 | 60 / 60 |
| `openai:gpt-5.4-xhigh` | `conflict_classifier` | 0.778 | 0.453-0.937 | 7 / 9 |
| `openai:gpt-5.4-xhigh` | `debug_explainer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-xhigh` | `entity_resolution` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-xhigh` | `eval_judge` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-xhigh` | `memory_compiler` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-xhigh` | `recall_synthesizer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-xhigh` | `router` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-xhigh` | `slack_intake` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.4-xhigh` | `validator_critic` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.5` | `conflict_classifier` | 1.000 | 0.957-1.000 | 85 / 85 |
| `openai:gpt-5.5` | `debug_explainer` | 1.000 | 0.941-1.000 | 61 / 61 |
| `openai:gpt-5.5` | `entity_resolution` | 1.000 | 0.875-1.000 | 27 / 27 |
| `openai:gpt-5.5` | `eval_judge` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.5` | `memory_compiler` | 1.000 | 0.972-1.000 | 135 / 135 |
| `openai:gpt-5.5` | `recall_synthesizer` | 1.000 | 0.896-1.000 | 33 / 33 |
| `openai:gpt-5.5` | `router` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.5` | `slack_intake` | 1.000 | 0.845-1.000 | 21 / 21 |
| `openai:gpt-5.5` | `validator_critic` | 1.000 | 0.959-1.000 | 89 / 89 |
| `openai:gpt-5.5-high` | `conflict_classifier` | 1.000 | 0.953-1.000 | 78 / 78 |
| `openai:gpt-5.5-high` | `debug_explainer` | 1.000 | 0.927-1.000 | 49 / 49 |
| `openai:gpt-5.5-high` | `entity_resolution` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.5-high` | `eval_judge` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.5-high` | `memory_compiler` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.5-high` | `recall_synthesizer` | 1.000 | 0.954-1.000 | 79 / 79 |
| `openai:gpt-5.5-high` | `router` | 1.000 | 0.824-1.000 | 18 / 18 |
| `openai:gpt-5.5-high` | `slack_intake` | 1.000 | 0.979-1.000 | 177 / 177 |
| `openai:gpt-5.5-high` | `validator_critic` | 1.000 | 0.959-1.000 | 90 / 90 |
| `openai:gpt-5.5-low` | `conflict_classifier` | 1.000 | 0.957-1.000 | 86 / 86 |
| `openai:gpt-5.5-low` | `debug_explainer` | 1.000 | 0.946-1.000 | 67 / 67 |
| `openai:gpt-5.5-low` | `entity_resolution` | 1.000 | 0.875-1.000 | 27 / 27 |
| `openai:gpt-5.5-low` | `eval_judge` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.5-low` | `memory_compiler` | 1.000 | 0.961-1.000 | 95 / 95 |
| `openai:gpt-5.5-low` | `recall_synthesizer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.5-low` | `router` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.5-low` | `slack_intake` | 1.000 | 0.961-1.000 | 94 / 94 |
| `openai:gpt-5.5-low` | `validator_critic` | 1.000 | 0.959-1.000 | 90 / 90 |
| `openai:gpt-5.5-medium` | `conflict_classifier` | 1.000 | 0.953-1.000 | 78 / 78 |
| `openai:gpt-5.5-medium` | `debug_explainer` | 1.000 | 0.949-1.000 | 72 / 72 |
| `openai:gpt-5.5-medium` | `entity_resolution` | 1.000 | 0.875-1.000 | 27 / 27 |
| `openai:gpt-5.5-medium` | `eval_judge` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.5-medium` | `memory_compiler` | 1.000 | 0.785-1.000 | 14 / 14 |
| `openai:gpt-5.5-medium` | `recall_synthesizer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.5-medium` | `router` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.5-medium` | `slack_intake` | 1.000 | 0.979-1.000 | 175 / 175 |
| `openai:gpt-5.5-medium` | `validator_critic` | 1.000 | 0.959-1.000 | 90 / 90 |
| `openai:gpt-5.5-xhigh` | `conflict_classifier` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.5-xhigh` | `debug_explainer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.5-xhigh` | `entity_resolution` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.5-xhigh` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |
| `openai:gpt-5.5-xhigh` | `memory_compiler` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.5-xhigh` | `recall_synthesizer` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.5-xhigh` | `router` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.5-xhigh` | `slack_intake` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:gpt-5.5-xhigh` | `validator_critic` | 0.000 | 0.000-0.000 | 0 / 0 |
| `openai:text-embedding-3-large` | `embeddings` | 1.000 | 0.207-1.000 | 1 / 1 |
| `openai:text-embedding-3-small` | `embeddings` | 1.000 | 0.207-1.000 | 1 / 1 |
| `voyage:voyage-4-lite` | `embeddings` | 1.000 | 0.207-1.000 | 1 / 1 |

Schema / parse failure classes:
- `json_parse_error`: 137
- `schema_invalid`: 15

## Safety / zero-tolerance failures

| Model | Role | Zero-tolerance failures | Upper 95% fail rate | Eligible |
|---|---|---:|---:|---|
| `anthropic:claude-haiku-4-5` | `conflict_classifier` | 26 | 0.893 | False |
| `anthropic:claude-haiku-4-5-20251001` | `conflict_classifier` | 27 | 0.914 | False |
| `anthropic:claude-haiku-4-5-20251001` | `entity_resolution` | 6 | 0.879 | False |
| `anthropic:claude-haiku-4-5-20251001` | `recall_synthesizer` | 0 | 0.083 | False |
| `anthropic:claude-opus-4-7` | `eval_judge` | 0 | 0.250 | True |
| `anthropic:claude-sonnet-4-6` | `conflict_classifier` | 27 | 0.914 | False |
| `anthropic:claude-sonnet-4-6` | `eval_judge` | 0 | 0.250 | True |
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
| `google:gemini-2.5-flash-lite` | `router` | 0 | 0.500 | False |
| `google:gemini-2.5-flash-lite` | `slack_intake` | 15 | 0.372 | False |
| `google:gemini-2.5-pro` | `conflict_classifier` | 13 | 0.563 | False |
| `google:gemini-3.1-pro-preview` | `conflict_classifier` | 0 | 0.030 | False |
| `google:gemini-3.1-pro-preview` | `debug_explainer` | 0 | 0.042 | True |
| `google:gemini-3.1-pro-preview` | `entity_resolution` | 0 | 0.111 | True |
| `google:gemini-3.1-pro-preview` | `eval_judge` | 0 | 0.083 | True |
| `google:gemini-3.1-pro-preview` | `memory_compiler` | 0 | 0.022 | False |
| `google:gemini-3.1-pro-preview` | `recall_synthesizer` | 0 | 0.028 | False |
| `google:gemini-3.1-pro-preview` | `router` | 0 | 0.167 | False |
| `google:gemini-3.1-pro-preview` | `slack_intake` | 0 | 0.017 | False |
| `google:gemini-3.1-pro-preview` | `validator_critic` | 0 | 0.033 | True |
| `google:gemini-3.1-pro-preview-high` | `conflict_classifier` | 0 | 0.030 | False |
| `google:gemini-3.1-pro-preview-high` | `debug_explainer` | 0 | 0.042 | True |
| `google:gemini-3.1-pro-preview-high` | `entity_resolution` | 0 | 0.111 | True |
| `google:gemini-3.1-pro-preview-high` | `eval_judge` | 0 | 0.083 | True |
| `google:gemini-3.1-pro-preview-high` | `memory_compiler` | 0 | 0.022 | False |
| `google:gemini-3.1-pro-preview-high` | `recall_synthesizer` | 0 | 0.028 | False |
| `google:gemini-3.1-pro-preview-high` | `router` | 0 | 0.167 | False |
| `google:gemini-3.1-pro-preview-high` | `slack_intake` | 0 | 0.017 | False |
| `google:gemini-3.1-pro-preview-high` | `validator_critic` | 0 | 0.033 | True |
| `google:gemini-3.1-pro-preview-low` | `conflict_classifier` | 5 | 0.113 | False |
| `google:gemini-3.1-pro-preview-low` | `debug_explainer` | 0 | 0.042 | True |
| `google:gemini-3.1-pro-preview-low` | `entity_resolution` | 0 | 0.111 | True |
| `google:gemini-3.1-pro-preview-low` | `eval_judge` | 0 | 0.083 | True |
| `google:gemini-3.1-pro-preview-low` | `memory_compiler` | 0 | 0.022 | False |
| `google:gemini-3.1-pro-preview-low` | `recall_synthesizer` | 0 | 0.028 | False |
| `google:gemini-3.1-pro-preview-low` | `router` | 0 | 0.167 | False |
| `google:gemini-3.1-pro-preview-low` | `slack_intake` | 0 | 0.017 | False |
| `google:gemini-3.1-pro-preview-low` | `validator_critic` | 0 | 0.033 | True |
| `google:gemini-3.1-pro-preview-medium` | `conflict_classifier` | 0 | 0.030 | False |
| `google:gemini-3.1-pro-preview-medium` | `debug_explainer` | 0 | 0.042 | True |
| `google:gemini-3.1-pro-preview-medium` | `entity_resolution` | 0 | 0.111 | True |
| `google:gemini-3.1-pro-preview-medium` | `eval_judge` | 0 | 0.083 | True |
| `google:gemini-3.1-pro-preview-medium` | `memory_compiler` | 0 | 0.022 | False |
| `google:gemini-3.1-pro-preview-medium` | `recall_synthesizer` | 0 | 0.028 | False |
| `google:gemini-3.1-pro-preview-medium` | `router` | 0 | 0.167 | False |
| `google:gemini-3.1-pro-preview-medium` | `slack_intake` | 0 | 0.017 | False |
| `google:gemini-3.1-pro-preview-medium` | `validator_critic` | 0 | 0.033 | True |
| `groq:llama-3.1-8b-instant` | `router` | 0 | 0.500 | False |
| `groq:llama-3.1-8b-instant` | `slack_intake` | 13 | 0.336 | False |
| `groq:llama-3.3-70b-versatile` | `memory_compiler` | 21 | 0.609 | False |
| `groq:llama-3.3-70b-versatile` | `recall_synthesizer` | 0 | 0.083 | False |
| `groq:openai/gpt-oss-120b` | `conflict_classifier` | 16 | 0.648 | False |
| `groq:openai/gpt-oss-120b` | `memory_compiler` | 17 | 0.524 | False |
| `groq:openai/gpt-oss-120b` | `recall_synthesizer` | 1 | 0.142 | False |
| `groq:openai/gpt-oss-120b` | `slack_intake` | 14 | 0.354 | False |
| `openai:gpt-5-nano` | `router` | 0 | 0.500 | False |
| `openai:gpt-5.4` | `conflict_classifier` | 63 | 0.724 | False |
| `openai:gpt-5.4` | `debug_explainer` | 0 | 0.042 | True |
| `openai:gpt-5.4` | `entity_resolution` | 0 | 0.111 | True |
| `openai:gpt-5.4` | `eval_judge` | 0 | 0.083 | True |
| `openai:gpt-5.4` | `memory_compiler` | 0 | 0.022 | False |
| `openai:gpt-5.4` | `recall_synthesizer` | 0 | 0.028 | False |
| `openai:gpt-5.4` | `router` | 0 | 0.167 | False |
| `openai:gpt-5.4` | `slack_intake` | 0 | 0.017 | False |
| `openai:gpt-5.4` | `validator_critic` | 0 | 0.033 | True |
| `openai:gpt-5.4-high` | `conflict_classifier` | 52 | 0.621 | False |
| `openai:gpt-5.4-high` | `debug_explainer` | 0 | 0.042 | True |
| `openai:gpt-5.4-high` | `entity_resolution` | 0 | 0.111 | True |
| `openai:gpt-5.4-high` | `eval_judge` | 0 | 0.083 | True |
| `openai:gpt-5.4-high` | `memory_compiler` | 0 | 0.022 | False |
| `openai:gpt-5.4-high` | `recall_synthesizer` | 0 | 0.028 | False |
| `openai:gpt-5.4-high` | `router` | 0 | 0.167 | False |
| `openai:gpt-5.4-high` | `slack_intake` | 0 | 0.017 | False |
| `openai:gpt-5.4-high` | `validator_critic` | 0 | 0.033 | True |
| `openai:gpt-5.4-low` | `conflict_classifier` | 56 | 0.659 | False |
| `openai:gpt-5.4-low` | `debug_explainer` | 0 | 0.042 | True |
| `openai:gpt-5.4-low` | `entity_resolution` | 16 | 0.755 | False |
| `openai:gpt-5.4-low` | `eval_judge` | 0 | 0.083 | True |
| `openai:gpt-5.4-low` | `memory_compiler` | 18 | 0.201 | False |
| `openai:gpt-5.4-low` | `recall_synthesizer` | 0 | 0.028 | False |
| `openai:gpt-5.4-low` | `router` | 0 | 0.167 | False |
| `openai:gpt-5.4-low` | `slack_intake` | 9 | 0.092 | False |
| `openai:gpt-5.4-low` | `validator_critic` | 0 | 0.033 | True |
| `openai:gpt-5.4-medium` | `conflict_classifier` | 54 | 0.640 | False |
| `openai:gpt-5.4-medium` | `debug_explainer` | 0 | 0.042 | True |
| `openai:gpt-5.4-medium` | `entity_resolution` | 0 | 0.111 | True |
| `openai:gpt-5.4-medium` | `eval_judge` | 0 | 0.083 | True |
| `openai:gpt-5.4-medium` | `memory_compiler` | 0 | 0.022 | False |
| `openai:gpt-5.4-medium` | `recall_synthesizer` | 0 | 0.028 | False |
| `openai:gpt-5.4-medium` | `router` | 0 | 0.167 | False |
| `openai:gpt-5.4-medium` | `slack_intake` | 45 | 0.318 | False |
| `openai:gpt-5.4-medium` | `validator_critic` | 0 | 0.033 | True |
| `openai:gpt-5.4-mini` | `conflict_classifier` | 26 | 0.893 | False |
| `openai:gpt-5.4-mini` | `entity_resolution` | 4 | 0.733 | False |
| `openai:gpt-5.4-mini` | `memory_compiler` | 21 | 0.609 | False |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | 0 | 0.083 | False |
| `openai:gpt-5.4-mini` | `slack_intake` | 15 | 0.372 | False |
| `openai:gpt-5.4-nano` | `entity_resolution` | 6 | 0.879 | False |
| `openai:gpt-5.4-nano` | `memory_compiler` | 20 | 0.588 | False |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | 2 | 0.181 | False |
| `openai:gpt-5.4-nano` | `slack_intake` | 15 | 0.372 | False |
| `openai:gpt-5.4-xhigh` | `conflict_classifier` | 1 | 0.055 | False |
| `openai:gpt-5.4-xhigh` | `debug_explainer` | 0 | 0.042 | True |
| `openai:gpt-5.4-xhigh` | `entity_resolution` | 0 | 0.111 | True |
| `openai:gpt-5.4-xhigh` | `eval_judge` | 0 | 0.083 | True |
| `openai:gpt-5.4-xhigh` | `memory_compiler` | 0 | 0.022 | False |
| `openai:gpt-5.4-xhigh` | `recall_synthesizer` | 0 | 0.028 | False |
| `openai:gpt-5.4-xhigh` | `router` | 0 | 0.167 | False |
| `openai:gpt-5.4-xhigh` | `slack_intake` | 0 | 0.017 | False |
| `openai:gpt-5.4-xhigh` | `validator_critic` | 0 | 0.033 | True |
| `openai:gpt-5.5` | `conflict_classifier` | 57 | 0.668 | False |
| `openai:gpt-5.5` | `debug_explainer` | 0 | 0.042 | True |
| `openai:gpt-5.5` | `entity_resolution` | 15 | 0.724 | False |
| `openai:gpt-5.5` | `eval_judge` | 0 | 0.083 | True |
| `openai:gpt-5.5` | `memory_compiler` | 61 | 0.536 | False |
| `openai:gpt-5.5` | `recall_synthesizer` | 10 | 0.162 | False |
| `openai:gpt-5.5` | `router` | 0 | 0.167 | False |
| `openai:gpt-5.5` | `slack_intake` | 0 | 0.017 | False |
| `openai:gpt-5.5` | `validator_critic` | 0 | 0.033 | True |
| `openai:gpt-5.5-high` | `conflict_classifier` | 50 | 0.601 | False |
| `openai:gpt-5.5-high` | `debug_explainer` | 0 | 0.042 | True |
| `openai:gpt-5.5-high` | `entity_resolution` | 0 | 0.111 | True |
| `openai:gpt-5.5-high` | `eval_judge` | 0 | 0.083 | True |
| `openai:gpt-5.5-high` | `memory_compiler` | 0 | 0.022 | False |
| `openai:gpt-5.5-high` | `recall_synthesizer` | 3 | 0.079 | False |
| `openai:gpt-5.5-high` | `router` | 0 | 0.167 | False |
| `openai:gpt-5.5-high` | `slack_intake` | 45 | 0.318 | False |
| `openai:gpt-5.5-high` | `validator_critic` | 0 | 0.033 | True |
| `openai:gpt-5.5-low` | `conflict_classifier` | 58 | 0.678 | False |
| `openai:gpt-5.5-low` | `debug_explainer` | 0 | 0.042 | True |
| `openai:gpt-5.5-low` | `entity_resolution` | 7 | 0.447 | False |
| `openai:gpt-5.5-low` | `eval_judge` | 0 | 0.083 | True |
| `openai:gpt-5.5-low` | `memory_compiler` | 42 | 0.394 | False |
| `openai:gpt-5.5-low` | `recall_synthesizer` | 0 | 0.028 | False |
| `openai:gpt-5.5-low` | `router` | 0 | 0.167 | False |
| `openai:gpt-5.5-low` | `slack_intake` | 9 | 0.092 | False |
| `openai:gpt-5.5-low` | `validator_critic` | 0 | 0.033 | True |
| `openai:gpt-5.5-medium` | `conflict_classifier` | 52 | 0.621 | False |
| `openai:gpt-5.5-medium` | `debug_explainer` | 0 | 0.042 | True |
| `openai:gpt-5.5-medium` | `entity_resolution` | 7 | 0.447 | False |
| `openai:gpt-5.5-medium` | `eval_judge` | 0 | 0.083 | True |
| `openai:gpt-5.5-medium` | `memory_compiler` | 5 | 0.084 | False |
| `openai:gpt-5.5-medium` | `recall_synthesizer` | 0 | 0.028 | False |
| `openai:gpt-5.5-medium` | `router` | 0 | 0.167 | False |
| `openai:gpt-5.5-medium` | `slack_intake` | 41 | 0.294 | False |
| `openai:gpt-5.5-medium` | `validator_critic` | 0 | 0.033 | True |
| `openai:gpt-5.5-xhigh` | `conflict_classifier` | 0 | 0.030 | False |
| `openai:gpt-5.5-xhigh` | `debug_explainer` | 0 | 0.042 | True |
| `openai:gpt-5.5-xhigh` | `entity_resolution` | 0 | 0.111 | True |
| `openai:gpt-5.5-xhigh` | `eval_judge` | 0 | 0.083 | True |
| `openai:gpt-5.5-xhigh` | `memory_compiler` | 0 | 0.022 | False |
| `openai:gpt-5.5-xhigh` | `recall_synthesizer` | 0 | 0.028 | False |
| `openai:gpt-5.5-xhigh` | `router` | 0 | 0.167 | False |
| `openai:gpt-5.5-xhigh` | `slack_intake` | 0 | 0.017 | False |
| `openai:gpt-5.5-xhigh` | `validator_critic` | 0 | 0.033 | True |
| `openai:text-embedding-3-large` | `embeddings` | 0 | 1.000 | False |
| `openai:text-embedding-3-small` | `embeddings` | 0 | 1.000 | False |
| `voyage:voyage-4-lite` | `embeddings` | 0 | 1.000 | False |

## Quality scores by role

| Model | Role | Category | Semantic score | 95% CI | Semantic evals | Eligible | Rejection reasons |
|---|---|---|---:|---:|---:|---|---|
| `anthropic:claude-haiku-4-5` | `conflict_classifier` | `runtime` | 0.713 | 0.657-0.765 | 33 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `anthropic:claude-haiku-4-5-20251001` | `conflict_classifier` | `runtime` | 0.718 | 0.662-0.767 | 33 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `anthropic:claude-haiku-4-5-20251001` | `entity_resolution` | `runtime_or_support` | 0.757 | 0.667-0.854 | 9 | False | zero_tolerance_failures_present |
| `anthropic:claude-haiku-4-5-20251001` | `recall_synthesizer` | `runtime` | 0.923 | 0.867-0.970 | 36 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, groundedness_below_threshold |
| `anthropic:claude-opus-4-7` | `eval_judge` | `judge` | n/a | n/a | 0 | True | - |
| `anthropic:claude-sonnet-4-6` | `conflict_classifier` | `runtime` | 0.744 | 0.697-0.784 | 33 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `anthropic:claude-sonnet-4-6` | `eval_judge` | `judge` | 0.807 | 0.766-0.854 | 12 | True | - |
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
| `google:gemini-2.5-flash-lite` | `router` | `runtime` | 0.950 | 0.875-1.000 | 5 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold |
| `google:gemini-2.5-flash-lite` | `slack_intake` | `runtime` | 0.740 | 0.697-0.782 | 59 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `google:gemini-2.5-pro` | `conflict_classifier` | `runtime` | 0.727 | 0.681-0.779 | 19 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `google:gemini-3.1-pro-preview` | `conflict_classifier` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview` | `debug_explainer` | `debug_admin` | n/a | n/a | 0 | True | - |
| `google:gemini-3.1-pro-preview` | `entity_resolution` | `runtime_or_support` | n/a | n/a | 0 | True | - |
| `google:gemini-3.1-pro-preview` | `eval_judge` | `judge` | n/a | n/a | 0 | True | - |
| `google:gemini-3.1-pro-preview` | `memory_compiler` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview` | `recall_synthesizer` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview` | `router` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview` | `slack_intake` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview` | `validator_critic` | `support` | n/a | n/a | 0 | True | - |
| `google:gemini-3.1-pro-preview-high` | `conflict_classifier` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview-high` | `debug_explainer` | `debug_admin` | n/a | n/a | 0 | True | - |
| `google:gemini-3.1-pro-preview-high` | `entity_resolution` | `runtime_or_support` | n/a | n/a | 0 | True | - |
| `google:gemini-3.1-pro-preview-high` | `eval_judge` | `judge` | n/a | n/a | 0 | True | - |
| `google:gemini-3.1-pro-preview-high` | `memory_compiler` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview-high` | `recall_synthesizer` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview-high` | `router` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview-high` | `slack_intake` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview-high` | `validator_critic` | `support` | n/a | n/a | 0 | True | - |
| `google:gemini-3.1-pro-preview-low` | `conflict_classifier` | `runtime` | 0.775 | 0.750-0.825 | 5 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `google:gemini-3.1-pro-preview-low` | `debug_explainer` | `debug_admin` | n/a | n/a | 0 | True | - |
| `google:gemini-3.1-pro-preview-low` | `entity_resolution` | `runtime_or_support` | n/a | n/a | 0 | True | - |
| `google:gemini-3.1-pro-preview-low` | `eval_judge` | `judge` | n/a | n/a | 0 | True | - |
| `google:gemini-3.1-pro-preview-low` | `memory_compiler` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview-low` | `recall_synthesizer` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview-low` | `router` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview-low` | `slack_intake` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview-low` | `validator_critic` | `support` | n/a | n/a | 0 | True | - |
| `google:gemini-3.1-pro-preview-medium` | `conflict_classifier` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview-medium` | `debug_explainer` | `debug_admin` | n/a | n/a | 0 | True | - |
| `google:gemini-3.1-pro-preview-medium` | `entity_resolution` | `runtime_or_support` | n/a | n/a | 0 | True | - |
| `google:gemini-3.1-pro-preview-medium` | `eval_judge` | `judge` | n/a | n/a | 0 | True | - |
| `google:gemini-3.1-pro-preview-medium` | `memory_compiler` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview-medium` | `recall_synthesizer` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview-medium` | `router` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview-medium` | `slack_intake` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `google:gemini-3.1-pro-preview-medium` | `validator_critic` | `support` | n/a | n/a | 0 | True | - |
| `groq:llama-3.1-8b-instant` | `router` | `runtime` | 0.975 | 0.917-1.000 | 5 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold |
| `groq:llama-3.1-8b-instant` | `slack_intake` | `runtime` | 0.689 | 0.637-0.742 | 42 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `groq:llama-3.3-70b-versatile` | `memory_compiler` | `runtime` | 0.652 | 0.620-0.683 | 40 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, memory_card_extraction_below_threshold |
| `groq:llama-3.3-70b-versatile` | `recall_synthesizer` | `runtime` | 0.934 | 0.883-0.976 | 36 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, groundedness_below_threshold |
| `groq:openai/gpt-oss-120b` | `conflict_classifier` | `runtime` | 0.736 | 0.685-0.781 | 22 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `groq:openai/gpt-oss-120b` | `memory_compiler` | `runtime` | 0.676 | 0.633-0.717 | 34 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, memory_card_extraction_below_threshold |
| `groq:openai/gpt-oss-120b` | `recall_synthesizer` | `runtime` | 0.915 | 0.866-0.965 | 24 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, groundedness_below_threshold |
| `groq:openai/gpt-oss-120b` | `slack_intake` | `runtime` | 0.694 | 0.645-0.739 | 45 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `openai:gpt-5-nano` | `router` | `runtime` | 0.917 | 0.875-0.979 | 6 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold |
| `openai:gpt-5.4` | `conflict_classifier` | `runtime` | 0.728 | 0.666-0.781 | 83 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `openai:gpt-5.4` | `debug_explainer` | `debug_admin` | 0.889 | 0.625-1.000 | 9 | True | - |
| `openai:gpt-5.4` | `entity_resolution` | `runtime_or_support` | n/a | n/a | 0 | True | - |
| `openai:gpt-5.4` | `eval_judge` | `judge` | 0.802 | 0.755-0.849 | 12 | True | - |
| `openai:gpt-5.4` | `memory_compiler` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.4` | `recall_synthesizer` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.4` | `router` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.4` | `slack_intake` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.4` | `validator_critic` | `support` | n/a | n/a | 0 | True | - |
| `openai:gpt-5.4-high` | `conflict_classifier` | `runtime` | 0.738 | 0.693-0.781 | 60 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `openai:gpt-5.4-high` | `debug_explainer` | `debug_admin` | n/a | n/a | 0 | True | - |
| `openai:gpt-5.4-high` | `entity_resolution` | `runtime_or_support` | n/a | n/a | 0 | True | - |
| `openai:gpt-5.4-high` | `eval_judge` | `judge` | n/a | n/a | 0 | True | - |
| `openai:gpt-5.4-high` | `memory_compiler` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.4-high` | `recall_synthesizer` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.4-high` | `router` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.4-high` | `slack_intake` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.4-high` | `validator_critic` | `support` | n/a | n/a | 0 | True | - |
| `openai:gpt-5.4-low` | `conflict_classifier` | `runtime` | 0.755 | 0.696-0.801 | 73 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `openai:gpt-5.4-low` | `debug_explainer` | `debug_admin` | 0.839 | 0.742-0.928 | 72 | True | - |
| `openai:gpt-5.4-low` | `entity_resolution` | `runtime_or_support` | 0.792 | 0.736-0.859 | 27 | False | zero_tolerance_failures_present |
| `openai:gpt-5.4-low` | `eval_judge` | `judge` | 0.825 | 0.783-0.861 | 36 | True | - |
| `openai:gpt-5.4-low` | `memory_compiler` | `runtime` | 0.681 | 0.625-0.728 | 50 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, memory_card_extraction_below_threshold, source_memory_split_below_threshold |
| `openai:gpt-5.4-low` | `recall_synthesizer` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.4-low` | `router` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.4-low` | `slack_intake` | `runtime` | 0.758 | 0.703-0.811 | 126 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `openai:gpt-5.4-low` | `validator_critic` | `support` | 0.689 | 0.620-0.759 | 90 | True | - |
| `openai:gpt-5.4-medium` | `conflict_classifier` | `runtime` | 0.745 | 0.693-0.791 | 81 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `openai:gpt-5.4-medium` | `debug_explainer` | `debug_admin` | 0.816 | 0.714-0.918 | 66 | True | - |
| `openai:gpt-5.4-medium` | `entity_resolution` | `runtime_or_support` | n/a | n/a | 0 | True | - |
| `openai:gpt-5.4-medium` | `eval_judge` | `judge` | n/a | n/a | 0 | True | - |
| `openai:gpt-5.4-medium` | `memory_compiler` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.4-medium` | `recall_synthesizer` | `runtime` | 0.933 | 0.905-0.964 | 50 | False | operational_success_below_threshold, schema_validity_below_threshold, groundedness_below_threshold |
| `openai:gpt-5.4-medium` | `router` | `runtime` | 0.913 | 0.875-0.955 | 18 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold |
| `openai:gpt-5.4-medium` | `slack_intake` | `runtime` | 0.756 | 0.714-0.795 | 180 | False | zero_tolerance_failures_present, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `openai:gpt-5.4-medium` | `validator_critic` | `support` | 0.695 | 0.610-0.783 | 90 | True | - |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `runtime` | 0.723 | 0.672-0.771 | 33 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `openai:gpt-5.4-mini` | `entity_resolution` | `runtime_or_support` | 0.796 | 0.745-0.847 | 9 | False | zero_tolerance_failures_present |
| `openai:gpt-5.4-mini` | `memory_compiler` | `runtime` | 0.715 | 0.673-0.753 | 45 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, memory_card_extraction_below_threshold |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `runtime` | 0.922 | 0.878-0.964 | 36 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, groundedness_below_threshold |
| `openai:gpt-5.4-mini` | `slack_intake` | `runtime` | 0.738 | 0.692-0.783 | 60 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `openai:gpt-5.4-nano` | `entity_resolution` | `runtime_or_support` | 0.782 | 0.713-0.875 | 9 | False | zero_tolerance_failures_present |
| `openai:gpt-5.4-nano` | `memory_compiler` | `runtime` | 0.709 | 0.666-0.746 | 45 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, memory_card_extraction_below_threshold |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `runtime` | 0.890 | 0.846-0.939 | 36 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, groundedness_below_threshold |
| `openai:gpt-5.4-nano` | `slack_intake` | `runtime` | 0.744 | 0.692-0.793 | 60 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `openai:gpt-5.4-xhigh` | `conflict_classifier` | `runtime` | 0.804 | 0.768-0.875 | 7 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `openai:gpt-5.4-xhigh` | `debug_explainer` | `debug_admin` | n/a | n/a | 0 | True | - |
| `openai:gpt-5.4-xhigh` | `entity_resolution` | `runtime_or_support` | n/a | n/a | 0 | True | - |
| `openai:gpt-5.4-xhigh` | `eval_judge` | `judge` | n/a | n/a | 0 | True | - |
| `openai:gpt-5.4-xhigh` | `memory_compiler` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.4-xhigh` | `recall_synthesizer` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.4-xhigh` | `router` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.4-xhigh` | `slack_intake` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.4-xhigh` | `validator_critic` | `support` | n/a | n/a | 0 | True | - |
| `openai:gpt-5.5` | `conflict_classifier` | `runtime` | 0.762 | 0.703-0.816 | 85 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `openai:gpt-5.5` | `debug_explainer` | `debug_admin` | 0.838 | 0.727-0.935 | 61 | True | - |
| `openai:gpt-5.5` | `entity_resolution` | `runtime_or_support` | 0.797 | 0.753-0.854 | 27 | False | zero_tolerance_failures_present |
| `openai:gpt-5.5` | `eval_judge` | `judge` | 0.814 | 0.752-0.875 | 36 | True | - |
| `openai:gpt-5.5` | `memory_compiler` | `runtime` | 0.694 | 0.652-0.739 | 135 | False | zero_tolerance_failures_present, schema_validity_below_threshold, semantic_score_below_threshold, memory_card_extraction_below_threshold, source_memory_split_below_threshold |
| `openai:gpt-5.5` | `recall_synthesizer` | `runtime` | 0.891 | 0.795-0.995 | 33 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, groundedness_below_threshold |
| `openai:gpt-5.5` | `router` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.5` | `slack_intake` | `runtime` | 0.708 | 0.597-0.792 | 21 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `openai:gpt-5.5` | `validator_critic` | `support` | 0.680 | 0.619-0.740 | 89 | True | - |
| `openai:gpt-5.5-high` | `conflict_classifier` | `runtime` | 0.751 | 0.695-0.801 | 78 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `openai:gpt-5.5-high` | `debug_explainer` | `debug_admin` | 0.791 | 0.680-0.887 | 49 | True | - |
| `openai:gpt-5.5-high` | `entity_resolution` | `runtime_or_support` | n/a | n/a | 0 | True | - |
| `openai:gpt-5.5-high` | `eval_judge` | `judge` | n/a | n/a | 0 | True | - |
| `openai:gpt-5.5-high` | `memory_compiler` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.5-high` | `recall_synthesizer` | `runtime` | 0.970 | 0.943-0.993 | 79 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, groundedness_below_threshold |
| `openai:gpt-5.5-high` | `router` | `runtime` | 0.931 | 0.889-0.972 | 18 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold |
| `openai:gpt-5.5-high` | `slack_intake` | `runtime` | 0.762 | 0.723-0.799 | 177 | False | zero_tolerance_failures_present, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `openai:gpt-5.5-high` | `validator_critic` | `support` | 0.690 | 0.624-0.754 | 90 | True | - |
| `openai:gpt-5.5-low` | `conflict_classifier` | `runtime` | 0.754 | 0.693-0.805 | 86 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `openai:gpt-5.5-low` | `debug_explainer` | `debug_admin` | 0.825 | 0.726-0.919 | 67 | True | - |
| `openai:gpt-5.5-low` | `entity_resolution` | `runtime_or_support` | 0.840 | 0.810-0.868 | 27 | False | zero_tolerance_failures_present |
| `openai:gpt-5.5-low` | `eval_judge` | `judge` | 0.811 | 0.743-0.875 | 36 | True | - |
| `openai:gpt-5.5-low` | `memory_compiler` | `runtime` | 0.694 | 0.642-0.744 | 95 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, memory_card_extraction_below_threshold, source_memory_split_below_threshold |
| `openai:gpt-5.5-low` | `recall_synthesizer` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.5-low` | `router` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.5-low` | `slack_intake` | `runtime` | 0.754 | 0.699-0.812 | 94 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `openai:gpt-5.5-low` | `validator_critic` | `support` | 0.692 | 0.634-0.751 | 90 | True | - |
| `openai:gpt-5.5-medium` | `conflict_classifier` | `runtime` | 0.752 | 0.688-0.804 | 78 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, conflict_safety_below_threshold |
| `openai:gpt-5.5-medium` | `debug_explainer` | `debug_admin` | 0.823 | 0.723-0.920 | 72 | True | - |
| `openai:gpt-5.5-medium` | `entity_resolution` | `runtime_or_support` | 0.840 | 0.796-0.870 | 27 | False | zero_tolerance_failures_present |
| `openai:gpt-5.5-medium` | `eval_judge` | `judge` | 0.806 | 0.745-0.866 | 36 | True | - |
| `openai:gpt-5.5-medium` | `memory_compiler` | `runtime` | 0.640 | 0.625-0.655 | 14 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, memory_card_extraction_below_threshold |
| `openai:gpt-5.5-medium` | `recall_synthesizer` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.5-medium` | `router` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.5-medium` | `slack_intake` | `runtime` | 0.771 | 0.729-0.809 | 175 | False | zero_tolerance_failures_present, operational_success_below_threshold, schema_validity_below_threshold, semantic_score_below_threshold, decision_correctness_below_threshold, repair_option_usefulness_below_threshold |
| `openai:gpt-5.5-medium` | `validator_critic` | `support` | 0.685 | 0.622-0.747 | 90 | True | - |
| `openai:gpt-5.5-xhigh` | `conflict_classifier` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.5-xhigh` | `debug_explainer` | `debug_admin` | n/a | n/a | 0 | True | - |
| `openai:gpt-5.5-xhigh` | `entity_resolution` | `runtime_or_support` | n/a | n/a | 0 | True | - |
| `openai:gpt-5.5-xhigh` | `eval_judge` | `judge` | 0.812 | 0.750-0.875 | 12 | True | - |
| `openai:gpt-5.5-xhigh` | `memory_compiler` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.5-xhigh` | `recall_synthesizer` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.5-xhigh` | `router` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.5-xhigh` | `slack_intake` | `runtime` | n/a | n/a | 0 | False | operational_success_below_threshold, schema_validity_below_threshold, semantic_score_not_evaluated |
| `openai:gpt-5.5-xhigh` | `validator_critic` | `support` | n/a | n/a | 0 | True | - |
| `openai:text-embedding-3-large` | `embeddings` | `embedding` | 1.000 | 1.000-1.000 | 1 | False | operational_success_below_threshold |
| `openai:text-embedding-3-small` | `embeddings` | `embedding` | 1.000 | 1.000-1.000 | 1 | False | operational_success_below_threshold |
| `voyage:voyage-4-lite` | `embeddings` | `embedding` | 1.000 | 1.000-1.000 | 1 | False | operational_success_below_threshold |

## Runtime-role recommendations

Partial recommendations only.
- none

## Embedding recommendations

- none

## Judge/debug/support recommendations

- `debug_explainer`: `openai:gpt-5.4-medium`
- `entity_resolution`: `google:gemini-3.1-pro-preview`
- `eval_judge`: `openai:gpt-5.4-low`
- `validator_critic`: `openai:gpt-5.4-medium`

## Pairwise comparisons

| Role | Model A | Model B | Shared variants | Shared semantic variants | Semantic diff | Operational diff | Schema diff | Recommendation |
|---|---|---|---:|---:|---:|---:|---:|---|
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `anthropic:claude-haiku-4-5-20251001` | 33 | 33 | -0.005 (-0.023-0.013) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `anthropic:claude-haiku-4-5-20251001` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `anthropic:claude-sonnet-4-6` | 33 | 33 | -0.031 (-0.066--0.007) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `aws-bedrock:nvidia.nemotron-super-3-120b` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `google:gemini-2.5-flash` | 33 | 20 | -0.039 (-0.091-0.007) | 0.000 (0.000-0.000) | 0.394 (0.133-0.667) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `google:gemini-2.5-pro` | 33 | 19 | -0.025 (-0.069-0.013) | 0.030 (0.000-0.139) | 0.424 (0.152-0.667) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-pro` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `google:gemini-3.1-pro-preview` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `google:gemini-3.1-pro-preview-high` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `google:gemini-3.1-pro-preview-low` | 33 | 2 | 0.000 (-0.062-0.062) | 0.939 (0.778-1.000) | 0.939 (0.778-1.000) | operational_winner_not_quality_winner: Operational results differ, but semantic overlap is too small for a quality recommendation. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `google:gemini-3.1-pro-preview-medium` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `groq:openai/gpt-oss-120b` | 33 | 22 | -0.019 (-0.066-0.022) | 0.333 (0.133-0.556) | 0.333 (0.133-0.556) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `openai:gpt-5.4` | 33 | 27 | -0.014 (-0.059-0.020) | 0.182 (0.028-0.407) | 0.182 (0.028-0.407) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `openai:gpt-5.4-high` | 33 | 24 | -0.015 (-0.062-0.018) | 0.242 (0.074-0.433) | 0.273 (0.091-0.485) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `openai:gpt-5.4-low` | 33 | 24 | -0.027 (-0.078-0.009) | 0.273 (0.083-0.519) | 0.273 (0.083-0.519) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `openai:gpt-5.4-medium` | 33 | 29 | -0.026 (-0.072-0.008) | 0.121 (0.000-0.306) | 0.121 (0.000-0.306) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `anthropic:claude-haiku-4-5` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `openai:gpt-5.4-mini` | 33 | 33 | -0.010 (-0.051-0.019) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `openai:gpt-5.4-xhigh` | 33 | 3 | -0.167 (-0.250--0.094) | 0.879 (0.697-1.000) | 0.909 (0.733-1.000) | tradeoff_quality_vs_ops: One model has higher semantic quality while the other is more operationally reliable. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `openai:gpt-5.5` | 33 | 28 | -0.048 (-0.110--0.004) | 0.152 (0.026-0.364) | 0.152 (0.026-0.364) | tradeoff_quality_vs_ops: One model has higher semantic quality while the other is more operationally reliable. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `openai:gpt-5.5-high` | 33 | 27 | -0.024 (-0.069-0.005) | 0.182 (0.030-0.367) | 0.182 (0.030-0.367) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `openai:gpt-5.5-low` | 33 | 27 | -0.029 (-0.087-0.013) | 0.182 (0.000-0.444) | 0.182 (0.000-0.444) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `anthropic:claude-haiku-4-5` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `openai:gpt-5.5-medium` | 33 | 25 | -0.041 (-0.094--0.003) | 0.242 (0.067-0.455) | 0.242 (0.067-0.455) | tradeoff_quality_vs_ops: One model has higher semantic quality while the other is more operationally reliable. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5` | `openai:gpt-5.5-xhigh` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `anthropic:claude-sonnet-4-6` | 33 | 33 | -0.026 (-0.062--0.000) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `aws-bedrock:nvidia.nemotron-super-3-120b` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-2.5-flash` | 33 | 20 | -0.032 (-0.092-0.020) | 0.000 (0.000-0.000) | 0.394 (0.133-0.667) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-2.5-pro` | 33 | 19 | -0.016 (-0.064-0.027) | 0.030 (0.000-0.139) | 0.424 (0.152-0.667) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-pro` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-3.1-pro-preview` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-3.1-pro-preview-high` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-3.1-pro-preview-low` | 33 | 2 | 0.000 (-0.062-0.062) | 0.939 (0.778-1.000) | 0.939 (0.778-1.000) | operational_winner_not_quality_winner: Operational results differ, but semantic overlap is too small for a quality recommendation. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-3.1-pro-preview-medium` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `groq:openai/gpt-oss-120b` | 33 | 22 | -0.017 (-0.067-0.025) | 0.333 (0.133-0.556) | 0.333 (0.133-0.556) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4` | 33 | 27 | -0.012 (-0.066-0.033) | 0.182 (0.028-0.407) | 0.182 (0.028-0.407) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-high` | 33 | 24 | -0.003 (-0.049-0.030) | 0.242 (0.074-0.433) | 0.273 (0.091-0.485) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-low` | 33 | 24 | -0.027 (-0.087-0.016) | 0.273 (0.083-0.519) | 0.273 (0.083-0.519) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-medium` | 33 | 29 | -0.022 (-0.078-0.018) | 0.121 (0.000-0.306) | 0.121 (0.000-0.306) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `anthropic:claude-haiku-4-5-20251001` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-mini` | 33 | 33 | -0.005 (-0.048-0.028) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-xhigh` | 33 | 3 | -0.208 (-0.250--0.188) | 0.879 (0.697-1.000) | 0.909 (0.733-1.000) | tradeoff_quality_vs_ops: One model has higher semantic quality while the other is more operationally reliable. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.5` | 33 | 28 | -0.045 (-0.113-0.001) | 0.152 (0.026-0.364) | 0.152 (0.026-0.364) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.5-high` | 33 | 27 | -0.021 (-0.075-0.015) | 0.182 (0.030-0.367) | 0.182 (0.030-0.367) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.5-low` | 33 | 27 | -0.029 (-0.098-0.023) | 0.182 (0.000-0.444) | 0.182 (0.000-0.444) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `anthropic:claude-haiku-4-5-20251001` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.5-medium` | 33 | 25 | -0.040 (-0.099-0.006) | 0.242 (0.067-0.455) | 0.242 (0.067-0.455) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.5-xhigh` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `aws-bedrock:nvidia.nemotron-super-3-120b` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `google:gemini-2.5-flash` | 33 | 20 | 0.003 (-0.037-0.042) | 0.000 (0.000-0.000) | 0.394 (0.133-0.667) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `google:gemini-2.5-pro` | 33 | 19 | 0.012 (-0.021-0.044) | 0.030 (0.000-0.139) | 0.424 (0.152-0.667) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-pro` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `google:gemini-3.1-pro-preview` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `google:gemini-3.1-pro-preview-high` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `google:gemini-3.1-pro-preview-low` | 33 | 2 | 0.000 (-0.062-0.062) | 0.939 (0.778-1.000) | 0.939 (0.778-1.000) | operational_winner_not_quality_winner: Operational results differ, but semantic overlap is too small for a quality recommendation. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `google:gemini-3.1-pro-preview-medium` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `groq:openai/gpt-oss-120b` | 33 | 22 | 0.012 (-0.015-0.042) | 0.333 (0.133-0.556) | 0.333 (0.133-0.556) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.4` | 33 | 27 | 0.019 (-0.009-0.057) | 0.182 (0.028-0.407) | 0.182 (0.028-0.407) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.4-high` | 33 | 24 | 0.028 (-0.012-0.071) | 0.242 (0.074-0.433) | 0.273 (0.091-0.485) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.4-low` | 33 | 24 | 0.005 (-0.020-0.033) | 0.273 (0.083-0.519) | 0.273 (0.083-0.519) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.4-medium` | 33 | 29 | 0.007 (-0.025-0.036) | 0.121 (0.000-0.306) | 0.121 (0.000-0.306) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-medium` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.4-mini` | 33 | 33 | 0.021 (-0.002-0.043) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.4-xhigh` | 33 | 3 | -0.083 (-0.125--0.062) | 0.879 (0.697-1.000) | 0.909 (0.733-1.000) | tradeoff_quality_vs_ops: One model has higher semantic quality while the other is more operationally reliable. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.5` | 33 | 28 | -0.015 (-0.046-0.006) | 0.152 (0.026-0.364) | 0.152 (0.026-0.364) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.5-high` | 33 | 27 | -0.003 (-0.029-0.020) | 0.182 (0.030-0.367) | 0.182 (0.030-0.367) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.5-low` | 33 | 27 | -0.002 (-0.032-0.027) | 0.182 (0.000-0.444) | 0.182 (0.000-0.444) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.5-low` if a tie-break is required. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.5-medium` | 33 | 25 | -0.009 (-0.038-0.022) | 0.242 (0.067-0.455) | 0.242 (0.067-0.455) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.5-xhigh` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-2.5-flash` | 33 | 0 | n/a | -1.000 (-1.000--1.000) | -0.606 (-0.867--0.333) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-2.5-pro` | 33 | 0 | n/a | -0.970 (-1.000--0.861) | -0.576 (-0.848--0.333) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-3.1-pro-preview` | 33 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-3.1-pro-preview-high` | 33 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-3.1-pro-preview-low` | 33 | 0 | n/a | -0.061 (-0.222-0.000) | -0.061 (-0.222-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-3.1-pro-preview-medium` | 33 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `groq:openai/gpt-oss-120b` | 33 | 0 | n/a | -0.667 (-0.867--0.444) | -0.667 (-0.867--0.444) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4` | 33 | 0 | n/a | -0.818 (-0.972--0.593) | -0.818 (-0.972--0.593) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-high` | 33 | 0 | n/a | -0.758 (-0.926--0.567) | -0.727 (-0.909--0.515) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-low` | 33 | 0 | n/a | -0.727 (-0.917--0.481) | -0.727 (-0.917--0.481) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-medium` | 33 | 0 | n/a | -0.879 (-1.000--0.694) | -0.879 (-1.000--0.694) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-mini` | 33 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-xhigh` | 33 | 0 | n/a | -0.121 (-0.303-0.000) | -0.091 (-0.267-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5` | 33 | 0 | n/a | -0.848 (-0.974--0.636) | -0.848 (-0.974--0.636) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5-high` | 33 | 0 | n/a | -0.818 (-0.970--0.633) | -0.818 (-0.970--0.633) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5-low` | 33 | 0 | n/a | -0.818 (-1.000--0.556) | -0.818 (-1.000--0.556) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5-medium` | 33 | 0 | n/a | -0.758 (-0.933--0.545) | -0.758 (-0.933--0.545) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5-xhigh` | 33 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `google:gemini-2.5-pro` | 33 | 13 | 0.010 (-0.048-0.072) | 0.030 (0.000-0.139) | 0.030 (-0.333-0.389) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 0.606 (0.333-0.867) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview-high` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 0.606 (0.333-0.867) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview-low` | 33 | 2 | 0.031 (0.000-0.062) | 0.939 (0.778-1.000) | 0.545 (0.282-0.818) | operational_winner_not_quality_winner: Operational results differ, but semantic overlap is too small for a quality recommendation. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview-medium` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 0.606 (0.333-0.867) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `groq:openai/gpt-oss-120b` | 33 | 12 | -0.007 (-0.051-0.047) | 0.333 (0.133-0.556) | -0.061 (-0.389-0.278) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `openai:gpt-5.4` | 33 | 17 | 0.009 (-0.027-0.059) | 0.182 (0.028-0.407) | -0.212 (-0.524-0.121) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `openai:gpt-5.4-high` | 33 | 15 | 0.014 (-0.034-0.079) | 0.242 (0.074-0.433) | -0.121 (-0.394-0.185) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `openai:gpt-5.4-low` | 33 | 15 | 0.000 (-0.031-0.042) | 0.273 (0.083-0.519) | -0.121 (-0.424-0.194) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `openai:gpt-5.4-medium` | 33 | 19 | 0.000 (-0.045-0.042) | 0.121 (0.000-0.306) | -0.273 (-0.533--0.030) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `openai:gpt-5.4-mini` | 33 | 20 | 0.019 (-0.027-0.066) | 0.000 (0.000-0.000) | -0.394 (-0.667--0.133) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `openai:gpt-5.4-xhigh` | 33 | 3 | -0.021 (-0.047-0.000) | 0.879 (0.697-1.000) | 0.515 (0.267-0.767) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `openai:gpt-5.5` | 33 | 17 | -0.033 (-0.071-0.008) | 0.152 (0.026-0.364) | -0.242 (-0.556-0.074) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `openai:gpt-5.5-high` | 33 | 15 | -0.006 (-0.054-0.052) | 0.182 (0.030-0.367) | -0.212 (-0.564-0.148) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `openai:gpt-5.5-low` | 33 | 18 | -0.023 (-0.061-0.014) | 0.182 (0.000-0.444) | -0.212 (-0.500-0.091) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `openai:gpt-5.5-medium` | 33 | 17 | -0.020 (-0.069-0.042) | 0.242 (0.067-0.455) | -0.152 (-0.433-0.133) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-2.5-flash` | `openai:gpt-5.5-xhigh` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 0.606 (0.333-0.867) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `google:gemini-3.1-pro-preview` | 33 | 0 | n/a | 0.970 (0.861-1.000) | 0.576 (0.333-0.833) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `google:gemini-3.1-pro-preview-high` | 33 | 0 | n/a | 0.970 (0.861-1.000) | 0.576 (0.333-0.833) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `google:gemini-3.1-pro-preview-low` | 33 | 0 | n/a | 0.909 (0.744-1.000) | 0.515 (0.154-0.833) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `google:gemini-3.1-pro-preview-medium` | 33 | 0 | n/a | 0.970 (0.861-1.000) | 0.576 (0.333-0.833) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `groq:openai/gpt-oss-120b` | 33 | 10 | 0.015 (-0.023-0.049) | 0.303 (0.091-0.533) | -0.091 (-0.455-0.300) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `openai:gpt-5.4` | 33 | 15 | 0.028 (-0.013-0.074) | 0.152 (-0.048-0.407) | -0.242 (-0.556-0.133) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-pro` if a tie-break is required. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `openai:gpt-5.4-high` | 33 | 13 | 0.034 (-0.035-0.094) | 0.212 (0.061-0.400) | -0.152 (-0.452-0.185) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `openai:gpt-5.4-low` | 33 | 11 | -0.002 (-0.052-0.056) | 0.242 (0.026-0.519) | -0.152 (-0.515-0.296) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `openai:gpt-5.4-medium` | 33 | 18 | -0.003 (-0.044-0.043) | 0.091 (-0.067-0.278) | -0.303 (-0.576--0.030) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-pro` if a tie-break is required. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `openai:gpt-5.4-mini` | 33 | 19 | 0.005 (-0.048-0.050) | -0.030 (-0.139-0.000) | -0.424 (-0.667--0.167) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `openai:gpt-5.4-xhigh` | 33 | 2 | -0.125 (-0.250-0.000) | 0.848 (0.667-1.000) | 0.485 (0.200-0.778) | operational_winner_not_quality_winner: Operational results differ, but semantic overlap is too small for a quality recommendation. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `openai:gpt-5.5` | 33 | 17 | -0.018 (-0.067-0.021) | 0.121 (-0.056-0.333) | -0.273 (-0.564-0.067) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-pro` if a tie-break is required. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `openai:gpt-5.5-high` | 33 | 13 | 0.003 (-0.031-0.046) | 0.152 (-0.033-0.367) | -0.242 (-0.590-0.152) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-pro` if a tie-break is required. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `openai:gpt-5.5-low` | 33 | 14 | -0.015 (-0.078-0.034) | 0.152 (-0.056-0.444) | -0.242 (-0.583-0.200) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-pro` if a tie-break is required. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `openai:gpt-5.5-medium` | 33 | 14 | 0.000 (-0.048-0.047) | 0.212 (0.000-0.444) | -0.182 (-0.524-0.200) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-pro` if a tie-break is required. |
| `conflict_classifier` | `google:gemini-2.5-pro` | `openai:gpt-5.5-xhigh` | 33 | 0 | n/a | 0.970 (0.861-1.000) | 0.576 (0.333-0.833) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-high` | 99 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-low` | 99 | 0 | n/a | -0.051 (-0.182-0.000) | -0.051 (-0.182-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-medium` | 99 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview` | `groq:openai/gpt-oss-120b` | 33 | 0 | n/a | -0.667 (-0.867--0.455) | -0.667 (-0.867--0.455) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4` | 99 | 0 | n/a | -0.838 (-0.949--0.678) | -0.838 (-0.949--0.678) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-high` | 99 | 0 | n/a | -0.646 (-0.828--0.463) | -0.606 (-0.778--0.422) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-low` | 99 | 0 | n/a | -0.737 (-0.889--0.543) | -0.737 (-0.889--0.543) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-medium` | 99 | 0 | n/a | -0.818 (-0.939--0.677) | -0.818 (-0.939--0.677) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-mini` | 33 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-xhigh` | 99 | 0 | n/a | -0.091 (-0.259-0.000) | -0.071 (-0.222-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5` | 99 | 0 | n/a | -0.859 (-0.968--0.691) | -0.859 (-0.968--0.691) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-high` | 99 | 0 | n/a | -0.788 (-0.939--0.616) | -0.788 (-0.939--0.616) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-low` | 99 | 0 | n/a | -0.869 (-0.974--0.716) | -0.869 (-0.974--0.716) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-medium` | 99 | 0 | n/a | -0.788 (-0.926--0.611) | -0.788 (-0.926--0.611) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-xhigh` | 99 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-low` | 99 | 0 | n/a | -0.051 (-0.182-0.000) | -0.051 (-0.182-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-medium` | 99 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-high` | `groq:openai/gpt-oss-120b` | 33 | 0 | n/a | -0.667 (-0.867--0.455) | -0.667 (-0.867--0.455) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4` | 99 | 0 | n/a | -0.838 (-0.949--0.678) | -0.838 (-0.949--0.678) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-high` | 99 | 0 | n/a | -0.646 (-0.828--0.463) | -0.606 (-0.778--0.422) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-low` | 99 | 0 | n/a | -0.737 (-0.889--0.543) | -0.737 (-0.889--0.543) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-medium` | 99 | 0 | n/a | -0.818 (-0.939--0.677) | -0.818 (-0.939--0.677) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-mini` | 33 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-xhigh` | 99 | 0 | n/a | -0.091 (-0.259-0.000) | -0.071 (-0.222-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5` | 99 | 0 | n/a | -0.859 (-0.968--0.691) | -0.859 (-0.968--0.691) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-high` | 99 | 0 | n/a | -0.788 (-0.939--0.616) | -0.788 (-0.939--0.616) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-low` | 99 | 0 | n/a | -0.869 (-0.974--0.716) | -0.869 (-0.974--0.716) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-medium` | 99 | 0 | n/a | -0.788 (-0.926--0.611) | -0.788 (-0.926--0.611) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-xhigh` | 99 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-low` | `google:gemini-3.1-pro-preview-medium` | 99 | 0 | n/a | 0.051 (0.000-0.182) | 0.051 (0.000-0.182) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-low` | `groq:openai/gpt-oss-120b` | 33 | 2 | 0.000 (0.000-0.000) | -0.606 (-0.818--0.405) | -0.606 (-0.818--0.405) | operational_winner_not_quality_winner: Operational results differ, but semantic overlap is too small for a quality recommendation. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4` | 99 | 5 | -0.050 (-0.087--0.013) | -0.788 (-0.919--0.622) | -0.788 (-0.919--0.622) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-high` | 99 | 3 | -0.021 (-0.062-0.062) | -0.596 (-0.811--0.398) | -0.556 (-0.756--0.359) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-low` | 99 | 5 | -0.037 (-0.062-0.013) | -0.687 (-0.846--0.505) | -0.687 (-0.846--0.505) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-medium` | 99 | 5 | -0.013 (-0.050-0.025) | -0.768 (-0.926--0.616) | -0.768 (-0.926--0.616) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-mini` | 33 | 2 | 0.000 (-0.062-0.062) | -0.939 (-1.000--0.778) | -0.939 (-1.000--0.778) | operational_winner_not_quality_winner: Operational results differ, but semantic overlap is too small for a quality recommendation. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-xhigh` | 99 | 0 | n/a | -0.040 (-0.244-0.121) | -0.020 (-0.210-0.152) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5` | 99 | 5 | -0.075 (-0.113--0.037) | -0.808 (-0.940--0.642) | -0.808 (-0.940--0.642) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-high` | 99 | 5 | -0.037 (-0.062-0.013) | -0.737 (-0.911--0.564) | -0.737 (-0.911--0.564) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-low` | 99 | 5 | -0.062 (-0.113-0.000) | -0.818 (-0.949--0.656) | -0.818 (-0.949--0.656) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-medium` | 99 | 5 | -0.050 (-0.087--0.013) | -0.737 (-0.889--0.566) | -0.737 (-0.889--0.566) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-xhigh` | 99 | 0 | n/a | 0.051 (0.000-0.182) | 0.051 (0.000-0.182) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-medium` | `groq:openai/gpt-oss-120b` | 33 | 0 | n/a | -0.667 (-0.867--0.455) | -0.667 (-0.867--0.455) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4` | 99 | 0 | n/a | -0.838 (-0.949--0.678) | -0.838 (-0.949--0.678) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-high` | 99 | 0 | n/a | -0.646 (-0.828--0.463) | -0.606 (-0.778--0.422) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-low` | 99 | 0 | n/a | -0.737 (-0.889--0.543) | -0.737 (-0.889--0.543) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-medium` | 99 | 0 | n/a | -0.818 (-0.939--0.677) | -0.818 (-0.939--0.677) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-mini` | 33 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-xhigh` | 99 | 0 | n/a | -0.091 (-0.259-0.000) | -0.071 (-0.222-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5` | 99 | 0 | n/a | -0.859 (-0.968--0.691) | -0.859 (-0.968--0.691) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-high` | 99 | 0 | n/a | -0.788 (-0.939--0.616) | -0.788 (-0.939--0.616) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-low` | 99 | 0 | n/a | -0.869 (-0.974--0.716) | -0.869 (-0.974--0.716) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-medium` | 99 | 0 | n/a | -0.788 (-0.926--0.611) | -0.788 (-0.926--0.611) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-xhigh` | 99 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4` | 33 | 17 | 0.006 (-0.031-0.050) | -0.152 (-0.455-0.212) | -0.152 (-0.455-0.212) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:openai/gpt-oss-120b` if a tie-break is required. |
| `conflict_classifier` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-high` | 33 | 17 | 0.026 (-0.010-0.062) | -0.091 (-0.333-0.152) | -0.061 (-0.303-0.185) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:openai/gpt-oss-120b` if a tie-break is required. |
| `conflict_classifier` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-low` | 33 | 15 | 0.003 (-0.034-0.040) | -0.061 (-0.364-0.296) | -0.061 (-0.364-0.296) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:openai/gpt-oss-120b` if a tie-break is required. |
| `conflict_classifier` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-medium` | 33 | 19 | -0.004 (-0.047-0.035) | -0.212 (-0.455-0.026) | -0.212 (-0.455-0.026) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:openai/gpt-oss-120b` if a tie-break is required. |
| `conflict_classifier` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-mini` | 33 | 22 | 0.009 (-0.029-0.048) | -0.333 (-0.556--0.133) | -0.333 (-0.556--0.133) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-xhigh` | 33 | 1 | 0.000 (0.000-0.000) | 0.545 (0.259-0.800) | 0.576 (0.267-0.833) | operational_winner_not_quality_winner: Operational results differ, but semantic overlap is too small for a quality recommendation. |
| `conflict_classifier` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5` | 33 | 19 | -0.022 (-0.051-0.003) | -0.182 (-0.433-0.100) | -0.182 (-0.433-0.100) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:openai/gpt-oss-120b` if a tie-break is required. |
| `conflict_classifier` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5-high` | 33 | 20 | -0.013 (-0.045-0.018) | -0.152 (-0.385-0.100) | -0.152 (-0.385-0.100) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:openai/gpt-oss-120b` if a tie-break is required. |
| `conflict_classifier` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5-low` | 33 | 17 | -0.015 (-0.054-0.022) | -0.152 (-0.462-0.222) | -0.152 (-0.462-0.222) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:openai/gpt-oss-120b` if a tie-break is required. |
| `conflict_classifier` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5-medium` | 33 | 17 | -0.029 (-0.076-0.012) | -0.091 (-0.357-0.190) | -0.091 (-0.357-0.190) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:openai/gpt-oss-120b` if a tie-break is required. |
| `conflict_classifier` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5-xhigh` | 33 | 0 | n/a | 0.667 (0.444-0.867) | 0.667 (0.444-0.867) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `openai:gpt-5.4` | `openai:gpt-5.4-high` | 99 | 50 | -0.014 (-0.041-0.008) | 0.192 (-0.089-0.404) | 0.232 (-0.033-0.434) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4` | `openai:gpt-5.4-low` | 99 | 65 | -0.015 (-0.039--0.000) | 0.101 (-0.051-0.244) | 0.101 (-0.051-0.244) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `conflict_classifier` | `openai:gpt-5.4` | `openai:gpt-5.4-medium` | 99 | 68 | -0.018 (-0.050-0.004) | 0.020 (-0.222-0.222) | 0.020 (-0.222-0.222) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4` | `openai:gpt-5.4-mini` | 33 | 27 | -0.003 (-0.056-0.036) | -0.182 (-0.407--0.028) | -0.182 (-0.407--0.028) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `openai:gpt-5.4` | `openai:gpt-5.4-xhigh` | 99 | 7 | -0.036 (-0.188-0.027) | 0.747 (0.544-0.896) | 0.768 (0.568-0.907) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `openai:gpt-5.4` | `openai:gpt-5.5` | 99 | 72 | -0.037 (-0.085--0.010) | -0.020 (-0.156-0.111) | -0.020 (-0.156-0.111) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `conflict_classifier` | `openai:gpt-5.4` | `openai:gpt-5.5-high` | 99 | 64 | -0.016 (-0.037--0.003) | 0.051 (-0.198-0.265) | 0.051 (-0.198-0.265) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `conflict_classifier` | `openai:gpt-5.4` | `openai:gpt-5.5-low` | 99 | 76 | -0.026 (-0.068--0.001) | -0.030 (-0.148-0.074) | -0.030 (-0.148-0.074) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `conflict_classifier` | `openai:gpt-5.4` | `openai:gpt-5.5-medium` | 99 | 67 | -0.022 (-0.057--0.002) | 0.051 (-0.123-0.198) | 0.051 (-0.123-0.198) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `conflict_classifier` | `openai:gpt-5.4` | `openai:gpt-5.5-xhigh` | 99 | 0 | n/a | 0.838 (0.678-0.949) | 0.838 (0.678-0.949) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `openai:gpt-5.4-high` | `openai:gpt-5.4-low` | 99 | 47 | -0.007 (-0.025-0.011) | -0.091 (-0.303-0.173) | -0.131 (-0.333-0.111) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-high` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4-high` | `openai:gpt-5.4-medium` | 99 | 50 | -0.006 (-0.031-0.015) | -0.172 (-0.414-0.051) | -0.212 (-0.444-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-high` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4-high` | `openai:gpt-5.4-mini` | 33 | 24 | -0.004 (-0.062-0.047) | -0.242 (-0.433--0.077) | -0.273 (-0.481--0.091) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `openai:gpt-5.4-high` | `openai:gpt-5.4-xhigh` | 99 | 4 | -0.031 (-0.250-0.062) | 0.556 (0.308-0.778) | 0.535 (0.296-0.744) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `openai:gpt-5.4-high` | `openai:gpt-5.5` | 99 | 52 | -0.022 (-0.066-0.012) | -0.212 (-0.413-0.037) | -0.253 (-0.436--0.030) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-high` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4-high` | `openai:gpt-5.5-high` | 99 | 44 | -0.015 (-0.035-0.006) | -0.141 (-0.411-0.152) | -0.182 (-0.457-0.100) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-high` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4-high` | `openai:gpt-5.5-low` | 99 | 52 | -0.008 (-0.051-0.028) | -0.222 (-0.426-0.037) | -0.263 (-0.456--0.020) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-high` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4-high` | `openai:gpt-5.5-medium` | 99 | 48 | -0.010 (-0.038-0.016) | -0.141 (-0.394-0.148) | -0.182 (-0.417-0.086) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-high` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4-high` | `openai:gpt-5.5-xhigh` | 99 | 0 | n/a | 0.646 (0.463-0.827) | 0.606 (0.420-0.778) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `openai:gpt-5.4-low` | `openai:gpt-5.4-medium` | 99 | 58 | 0.003 (-0.018-0.020) | -0.081 (-0.344-0.120) | -0.081 (-0.344-0.120) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-medium` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4-low` | `openai:gpt-5.4-mini` | 33 | 24 | 0.018 (-0.029-0.065) | -0.273 (-0.519--0.083) | -0.273 (-0.519--0.083) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `openai:gpt-5.4-low` | `openai:gpt-5.4-xhigh` | 99 | 7 | 0.000 (-0.125-0.042) | 0.646 (0.444-0.808) | 0.667 (0.457-0.827) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `openai:gpt-5.4-low` | `openai:gpt-5.5` | 99 | 65 | -0.018 (-0.051-0.005) | -0.121 (-0.267-0.011) | -0.121 (-0.267-0.011) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-low` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4-low` | `openai:gpt-5.5-high` | 99 | 60 | -0.007 (-0.023-0.005) | -0.051 (-0.300-0.148) | -0.051 (-0.300-0.148) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-low` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4-low` | `openai:gpt-5.5-low` | 99 | 67 | -0.013 (-0.048-0.015) | -0.131 (-0.269-0.000) | -0.131 (-0.269-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-low` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4-low` | `openai:gpt-5.5-medium` | 99 | 55 | -0.008 (-0.035-0.010) | -0.051 (-0.269-0.130) | -0.051 (-0.269-0.130) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-low` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4-low` | `openai:gpt-5.5-xhigh` | 99 | 0 | n/a | 0.737 (0.543-0.889) | 0.737 (0.543-0.889) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-mini` | 33 | 29 | 0.014 (-0.022-0.057) | -0.121 (-0.303-0.000) | -0.121 (-0.303-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-xhigh` | 99 | 7 | 0.018 (-0.125-0.073) | 0.727 (0.565-0.889) | 0.747 (0.589-0.898) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `openai:gpt-5.4-medium` | `openai:gpt-5.5` | 99 | 70 | -0.021 (-0.043-0.000) | -0.040 (-0.231-0.178) | -0.040 (-0.231-0.178) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-medium` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-high` | 99 | 64 | -0.011 (-0.025-0.004) | 0.030 (-0.103-0.185) | 0.030 (-0.103-0.185) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-medium` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-low` | 99 | 71 | -0.007 (-0.027-0.016) | -0.051 (-0.248-0.172) | -0.051 (-0.248-0.172) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-medium` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-medium` | 99 | 67 | -0.009 (-0.026-0.008) | 0.030 (-0.128-0.222) | 0.030 (-0.128-0.222) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-medium` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-xhigh` | 99 | 0 | n/a | 0.818 (0.676-0.939) | 0.818 (0.676-0.939) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `openai:gpt-5.4-mini` | `openai:gpt-5.4-xhigh` | 33 | 3 | -0.083 (-0.125-0.000) | 0.879 (0.697-1.000) | 0.909 (0.733-1.000) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `openai:gpt-5.4-mini` | `openai:gpt-5.5` | 33 | 28 | -0.035 (-0.078--0.007) | 0.152 (0.026-0.364) | 0.152 (0.026-0.364) | tradeoff_quality_vs_ops: One model has higher semantic quality while the other is more operationally reliable. |
| `conflict_classifier` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-high` | 33 | 27 | -0.027 (-0.067-0.000) | 0.182 (0.030-0.367) | 0.182 (0.030-0.367) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-low` | 33 | 27 | -0.023 (-0.056--0.001) | 0.182 (0.000-0.444) | 0.182 (0.000-0.444) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `conflict_classifier` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-medium` | 33 | 25 | -0.022 (-0.067-0.025) | 0.242 (0.067-0.455) | 0.242 (0.067-0.455) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-xhigh` | 33 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5` | 99 | 7 | -0.045 (-0.073-0.000) | -0.768 (-0.910--0.567) | -0.788 (-0.926--0.593) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-high` | 99 | 6 | -0.042 (-0.104-0.000) | -0.697 (-0.869--0.495) | -0.717 (-0.889--0.522) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-low` | 99 | 7 | -0.027 (-0.062-0.000) | -0.778 (-0.917--0.580) | -0.798 (-0.932--0.611) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-medium` | 99 | 7 | 0.000 (-0.057-0.250) | -0.697 (-0.856--0.500) | -0.717 (-0.872--0.522) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `conflict_classifier` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-xhigh` | 99 | 0 | n/a | 0.091 (0.000-0.259) | 0.071 (0.000-0.222) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `openai:gpt-5.5` | `openai:gpt-5.5-high` | 99 | 68 | 0.013 (-0.008-0.041) | 0.071 (-0.167-0.278) | 0.071 (-0.167-0.278) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.5` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.5` | `openai:gpt-5.5-low` | 99 | 76 | 0.010 (-0.003-0.027) | -0.010 (-0.123-0.091) | -0.010 (-0.123-0.091) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.5` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.5` | `openai:gpt-5.5-medium` | 99 | 70 | 0.015 (0.000-0.036) | 0.071 (-0.081-0.211) | 0.071 (-0.081-0.211) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `conflict_classifier` | `openai:gpt-5.5` | `openai:gpt-5.5-xhigh` | 99 | 0 | n/a | 0.859 (0.691-0.968) | 0.859 (0.691-0.968) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `openai:gpt-5.5-high` | `openai:gpt-5.5-low` | 99 | 68 | -0.007 (-0.037-0.017) | -0.081 (-0.278-0.141) | -0.081 (-0.278-0.141) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.5-low` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.5-high` | `openai:gpt-5.5-medium` | 99 | 63 | -0.005 (-0.033-0.015) | 0.000 (-0.185-0.212) | 0.000 (-0.185-0.212) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.5-medium` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.5-high` | `openai:gpt-5.5-xhigh` | 99 | 0 | n/a | 0.788 (0.616-0.938) | 0.788 (0.616-0.938) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `openai:gpt-5.5-low` | `openai:gpt-5.5-medium` | 99 | 69 | 0.010 (-0.005-0.034) | 0.081 (-0.089-0.247) | 0.081 (-0.089-0.247) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.5-low` if a tie-break is required. |
| `conflict_classifier` | `openai:gpt-5.5-low` | `openai:gpt-5.5-xhigh` | 99 | 0 | n/a | 0.869 (0.716-0.972) | 0.869 (0.716-0.972) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `conflict_classifier` | `openai:gpt-5.5-medium` | `openai:gpt-5.5-xhigh` | 99 | 0 | n/a | 0.788 (0.611-0.926) | 0.788 (0.611-0.926) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-high` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-low` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-medium` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4` | 72 | 0 | n/a | -0.125 (-0.321-0.000) | -0.125 (-0.321-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-high` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-low` | 72 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-medium` | 72 | 0 | n/a | -0.917 (-1.000--0.736) | -0.917 (-1.000--0.736) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-xhigh` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5` | 72 | 0 | n/a | -0.847 (-0.972--0.683) | -0.847 (-0.972--0.683) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-high` | 72 | 0 | n/a | -0.681 (-0.952--0.317) | -0.681 (-0.952--0.317) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-low` | 72 | 0 | n/a | -0.931 (-1.000--0.800) | -0.931 (-1.000--0.800) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-medium` | 72 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-xhigh` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-low` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-medium` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4` | 72 | 0 | n/a | -0.125 (-0.321-0.000) | -0.125 (-0.321-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-high` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-low` | 72 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-medium` | 72 | 0 | n/a | -0.917 (-1.000--0.736) | -0.917 (-1.000--0.736) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-xhigh` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5` | 72 | 0 | n/a | -0.847 (-0.972--0.683) | -0.847 (-0.972--0.683) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-high` | 72 | 0 | n/a | -0.681 (-0.952--0.317) | -0.681 (-0.952--0.317) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-low` | 72 | 0 | n/a | -0.931 (-1.000--0.800) | -0.931 (-1.000--0.800) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-medium` | 72 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-xhigh` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-low` | `google:gemini-3.1-pro-preview-medium` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4` | 72 | 0 | n/a | -0.125 (-0.321-0.000) | -0.125 (-0.321-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-high` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-low` | 72 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-medium` | 72 | 0 | n/a | -0.917 (-1.000--0.736) | -0.917 (-1.000--0.736) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-xhigh` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5` | 72 | 0 | n/a | -0.847 (-0.972--0.683) | -0.847 (-0.972--0.683) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-high` | 72 | 0 | n/a | -0.681 (-0.952--0.317) | -0.681 (-0.952--0.317) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-low` | 72 | 0 | n/a | -0.931 (-1.000--0.800) | -0.931 (-1.000--0.800) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-medium` | 72 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-xhigh` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4` | 72 | 0 | n/a | -0.125 (-0.321-0.000) | -0.125 (-0.321-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-high` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-low` | 72 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-medium` | 72 | 0 | n/a | -0.917 (-1.000--0.736) | -0.917 (-1.000--0.736) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-xhigh` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5` | 72 | 0 | n/a | -0.847 (-0.972--0.683) | -0.847 (-0.972--0.683) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-high` | 72 | 0 | n/a | -0.681 (-0.952--0.317) | -0.681 (-0.952--0.317) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-low` | 72 | 0 | n/a | -0.931 (-1.000--0.800) | -0.931 (-1.000--0.800) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-medium` | 72 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-xhigh` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4` | `openai:gpt-5.4-high` | 72 | 0 | n/a | 0.125 (0.000-0.321) | 0.125 (0.000-0.321) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4` | `openai:gpt-5.4-low` | 72 | 9 | -0.014 (-0.083-0.042) | -0.875 (-1.000--0.679) | -0.875 (-1.000--0.679) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-low` on cost. |
| `debug_explainer` | `openai:gpt-5.4` | `openai:gpt-5.4-medium` | 72 | 9 | 0.014 (0.000-0.062) | -0.792 (-0.968--0.593) | -0.792 (-0.968--0.593) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-medium` on cost. |
| `debug_explainer` | `openai:gpt-5.4` | `openai:gpt-5.4-xhigh` | 72 | 0 | n/a | 0.125 (0.000-0.321) | 0.125 (0.000-0.321) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4` | `openai:gpt-5.5` | 72 | 7 | 0.000 (0.000-0.000) | -0.722 (-0.952--0.469) | -0.722 (-0.952--0.469) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5` on cost. |
| `debug_explainer` | `openai:gpt-5.4` | `openai:gpt-5.5-high` | 72 | 9 | 0.014 (0.000-0.062) | -0.556 (-0.841--0.254) | -0.556 (-0.841--0.254) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5-high` on cost. |
| `debug_explainer` | `openai:gpt-5.4` | `openai:gpt-5.5-low` | 72 | 6 | 0.021 (0.000-0.094) | -0.806 (-1.000--0.494) | -0.806 (-1.000--0.494) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5-low` on cost. |
| `debug_explainer` | `openai:gpt-5.4` | `openai:gpt-5.5-medium` | 72 | 9 | 0.014 (0.000-0.062) | -0.875 (-1.000--0.679) | -0.875 (-1.000--0.679) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5-medium` on cost. |
| `debug_explainer` | `openai:gpt-5.4` | `openai:gpt-5.5-xhigh` | 72 | 0 | n/a | 0.125 (0.000-0.321) | 0.125 (0.000-0.321) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4-high` | `openai:gpt-5.4-low` | 72 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4-high` | `openai:gpt-5.4-medium` | 72 | 0 | n/a | -0.917 (-1.000--0.736) | -0.917 (-1.000--0.736) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4-high` | `openai:gpt-5.4-xhigh` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4-high` | `openai:gpt-5.5` | 72 | 0 | n/a | -0.847 (-0.972--0.683) | -0.847 (-0.972--0.683) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4-high` | `openai:gpt-5.5-high` | 72 | 0 | n/a | -0.681 (-0.952--0.317) | -0.681 (-0.952--0.317) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4-high` | `openai:gpt-5.5-low` | 72 | 0 | n/a | -0.931 (-1.000--0.800) | -0.931 (-1.000--0.800) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4-high` | `openai:gpt-5.5-medium` | 72 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4-high` | `openai:gpt-5.5-xhigh` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4-low` | `openai:gpt-5.4-medium` | 72 | 66 | 0.008 (-0.005-0.028) | 0.083 (0.000-0.264) | 0.083 (0.000-0.264) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-medium` on cost. |
| `debug_explainer` | `openai:gpt-5.4-low` | `openai:gpt-5.4-xhigh` | 72 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4-low` | `openai:gpt-5.5` | 72 | 61 | 0.007 (-0.013-0.032) | 0.153 (0.028-0.317) | 0.153 (0.028-0.317) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-low` on cost. |
| `debug_explainer` | `openai:gpt-5.4-low` | `openai:gpt-5.5-high` | 72 | 49 | 0.006 (-0.013-0.027) | 0.319 (0.048-0.683) | 0.319 (0.048-0.683) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-low` on cost. |
| `debug_explainer` | `openai:gpt-5.4-low` | `openai:gpt-5.5-low` | 72 | 67 | 0.005 (-0.009-0.024) | 0.069 (0.000-0.200) | 0.069 (0.000-0.200) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-low` on cost. |
| `debug_explainer` | `openai:gpt-5.4-low` | `openai:gpt-5.5-medium` | 72 | 72 | 0.016 (0.003-0.035) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `debug_explainer` | `openai:gpt-5.4-low` | `openai:gpt-5.5-xhigh` | 72 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-xhigh` | 72 | 0 | n/a | 0.917 (0.736-1.000) | 0.917 (0.736-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4-medium` | `openai:gpt-5.5` | 72 | 55 | -0.002 (-0.023-0.018) | 0.069 (-0.175-0.289) | 0.069 (-0.175-0.289) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-medium` on cost. |
| `debug_explainer` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-high` | 72 | 49 | -0.000 (-0.018-0.018) | 0.236 (0.033-0.524) | 0.236 (0.033-0.524) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-medium` on cost. |
| `debug_explainer` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-low` | 72 | 61 | -0.001 (-0.016-0.016) | -0.014 (-0.238-0.173) | -0.014 (-0.238-0.173) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-medium` on cost. |
| `debug_explainer` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-medium` | 72 | 66 | 0.007 (-0.001-0.020) | -0.083 (-0.264-0.000) | -0.083 (-0.264-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-medium` on cost. |
| `debug_explainer` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-xhigh` | 72 | 0 | n/a | 0.917 (0.736-1.000) | 0.917 (0.736-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5` | 72 | 0 | n/a | -0.847 (-0.972--0.683) | -0.847 (-0.972--0.683) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-high` | 72 | 0 | n/a | -0.681 (-0.952--0.317) | -0.681 (-0.952--0.317) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-low` | 72 | 0 | n/a | -0.931 (-1.000--0.800) | -0.931 (-1.000--0.800) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-medium` | 72 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-xhigh` | 72 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.5` | `openai:gpt-5.5-high` | 72 | 38 | 0.009 (-0.010-0.036) | 0.167 (-0.210-0.611) | 0.167 (-0.210-0.611) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5-high` on cost. |
| `debug_explainer` | `openai:gpt-5.5` | `openai:gpt-5.5-low` | 72 | 57 | 0.003 (-0.009-0.014) | -0.083 (-0.286-0.083) | -0.083 (-0.286-0.083) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5-low` on cost. |
| `debug_explainer` | `openai:gpt-5.5` | `openai:gpt-5.5-medium` | 72 | 61 | 0.011 (-0.000-0.027) | -0.153 (-0.317--0.028) | -0.153 (-0.317--0.028) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5-medium` on cost. |
| `debug_explainer` | `openai:gpt-5.5` | `openai:gpt-5.5-xhigh` | 72 | 0 | n/a | 0.847 (0.683-0.972) | 0.847 (0.683-0.972) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.5-high` | `openai:gpt-5.5-low` | 72 | 44 | -0.006 (-0.022-0.012) | -0.250 (-0.667-0.086) | -0.250 (-0.667-0.086) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5-low` on cost. |
| `debug_explainer` | `openai:gpt-5.5-high` | `openai:gpt-5.5-medium` | 72 | 49 | 0.008 (0.001-0.022) | -0.319 (-0.683--0.049) | -0.319 (-0.683--0.049) | tradeoff_quality_vs_ops: One model has higher semantic quality while the other is more operationally reliable. |
| `debug_explainer` | `openai:gpt-5.5-high` | `openai:gpt-5.5-xhigh` | 72 | 0 | n/a | 0.681 (0.317-0.951) | 0.681 (0.317-0.951) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.5-low` | `openai:gpt-5.5-medium` | 72 | 67 | 0.010 (0.001-0.020) | -0.069 (-0.200-0.000) | -0.069 (-0.200-0.000) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `debug_explainer` | `openai:gpt-5.5-low` | `openai:gpt-5.5-xhigh` | 72 | 0 | n/a | 0.931 (0.800-1.000) | 0.931 (0.800-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `debug_explainer` | `openai:gpt-5.5-medium` | `openai:gpt-5.5-xhigh` | 72 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `embeddings` | `openai:text-embedding-3-large` | `openai:text-embedding-3-small` | 1 | 1 | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:text-embedding-3-small` if a tie-break is required. |
| `embeddings` | `openai:text-embedding-3-large` | `voyage:voyage-4-lite` | 1 | 1 | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `voyage:voyage-4-lite` if a tie-break is required. |
| `embeddings` | `openai:text-embedding-3-small` | `voyage:voyage-4-lite` | 1 | 1 | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:text-embedding-3-small` if a tie-break is required. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-2.5-flash` | 9 | 8 | -0.005 (-0.056-0.042) | 0.000 (0.000-0.000) | 0.111 (0.000-0.444) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-3.1-pro-preview` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-3.1-pro-preview-high` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-3.1-pro-preview-low` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-3.1-pro-preview-medium` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-high` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-low` | 9 | 9 | -0.063 (-0.167-0.000) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `anthropic:claude-haiku-4-5-20251001` if a tie-break is required. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-medium` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-mini` | 9 | 9 | -0.039 (-0.139-0.028) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-nano` | 9 | 9 | -0.025 (-0.060-0.000) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-xhigh` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.5` | 9 | 9 | -0.056 (-0.125-0.007) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `anthropic:claude-haiku-4-5-20251001` if a tie-break is required. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.5-high` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.5-low` | 9 | 9 | -0.056 (-0.125-0.007) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `anthropic:claude-haiku-4-5-20251001` if a tie-break is required. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.5-medium` | 9 | 9 | -0.118 (-0.208--0.021) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `entity_resolution` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.5-xhigh` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.556-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview-high` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.556-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview-low` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.556-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview-medium` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.556-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-2.5-flash` | `openai:gpt-5.4` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.556-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-2.5-flash` | `openai:gpt-5.4-high` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.556-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-2.5-flash` | `openai:gpt-5.4-low` | 9 | 8 | -0.065 (-0.127-0.000) | 0.000 (0.000-0.000) | -0.111 (-0.444-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `entity_resolution` | `google:gemini-2.5-flash` | `openai:gpt-5.4-medium` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.556-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-2.5-flash` | `openai:gpt-5.4-mini` | 9 | 8 | -0.039 (-0.116-0.006) | 0.000 (0.000-0.000) | -0.111 (-0.444-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `entity_resolution` | `google:gemini-2.5-flash` | `openai:gpt-5.4-nano` | 9 | 8 | -0.023 (-0.070-0.024) | 0.000 (0.000-0.000) | -0.111 (-0.444-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `entity_resolution` | `google:gemini-2.5-flash` | `openai:gpt-5.4-xhigh` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.556-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-2.5-flash` | `openai:gpt-5.5` | 9 | 8 | -0.057 (-0.102--0.007) | 0.000 (0.000-0.000) | -0.111 (-0.444-0.000) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `entity_resolution` | `google:gemini-2.5-flash` | `openai:gpt-5.5-high` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.556-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-2.5-flash` | `openai:gpt-5.5-low` | 9 | 8 | -0.042 (-0.088-0.008) | 0.000 (0.000-0.000) | -0.111 (-0.444-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `entity_resolution` | `google:gemini-2.5-flash` | `openai:gpt-5.5-medium` | 9 | 8 | -0.112 (-0.161--0.055) | 0.000 (0.000-0.000) | -0.111 (-0.444-0.000) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `entity_resolution` | `google:gemini-2.5-flash` | `openai:gpt-5.5-xhigh` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.556-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-high` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-low` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-medium` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-high` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-low` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-medium` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-mini` | 9 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-nano` | 9 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-xhigh` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-high` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-low` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-medium` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-xhigh` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-low` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-medium` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-high` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-low` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-medium` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-mini` | 9 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-nano` | 9 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-xhigh` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-high` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-low` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-medium` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-xhigh` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-low` | `google:gemini-3.1-pro-preview-medium` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-high` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-low` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-medium` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-mini` | 9 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-nano` | 9 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-xhigh` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-high` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-low` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-medium` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-xhigh` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-high` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-low` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-medium` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-mini` | 9 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-nano` | 9 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-xhigh` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-high` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-low` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-medium` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-xhigh` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4` | `openai:gpt-5.4-high` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4` | `openai:gpt-5.4-low` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4` | `openai:gpt-5.4-medium` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4` | `openai:gpt-5.4-mini` | 9 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4` | `openai:gpt-5.4-nano` | 9 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4` | `openai:gpt-5.4-xhigh` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4` | `openai:gpt-5.5` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4` | `openai:gpt-5.5-high` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4` | `openai:gpt-5.5-low` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4` | `openai:gpt-5.5-medium` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4` | `openai:gpt-5.5-xhigh` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-high` | `openai:gpt-5.4-low` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-high` | `openai:gpt-5.4-medium` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-high` | `openai:gpt-5.4-mini` | 9 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-high` | `openai:gpt-5.4-nano` | 9 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-high` | `openai:gpt-5.4-xhigh` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-high` | `openai:gpt-5.5` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-high` | `openai:gpt-5.5-high` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-high` | `openai:gpt-5.5-low` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-high` | `openai:gpt-5.5-medium` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-high` | `openai:gpt-5.5-xhigh` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-low` | `openai:gpt-5.4-medium` | 27 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-low` | `openai:gpt-5.4-mini` | 9 | 9 | 0.023 (-0.032-0.086) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `entity_resolution` | `openai:gpt-5.4-low` | `openai:gpt-5.4-nano` | 9 | 9 | 0.037 (0.000-0.106) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `entity_resolution` | `openai:gpt-5.4-low` | `openai:gpt-5.4-xhigh` | 27 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-low` | `openai:gpt-5.5` | 27 | 27 | -0.005 (-0.035-0.022) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-low` if a tie-break is required. |
| `entity_resolution` | `openai:gpt-5.4-low` | `openai:gpt-5.5-high` | 27 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-low` | `openai:gpt-5.5-low` | 27 | 27 | -0.049 (-0.103--0.001) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `entity_resolution` | `openai:gpt-5.4-low` | `openai:gpt-5.5-medium` | 27 | 27 | -0.049 (-0.093--0.007) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `entity_resolution` | `openai:gpt-5.4-low` | `openai:gpt-5.5-xhigh` | 27 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-mini` | 9 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-nano` | 9 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-xhigh` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-medium` | `openai:gpt-5.5` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-high` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-low` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-medium` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-xhigh` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-mini` | `openai:gpt-5.4-nano` | 9 | 9 | 0.014 (-0.042-0.102) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `entity_resolution` | `openai:gpt-5.4-mini` | `openai:gpt-5.4-xhigh` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-mini` | `openai:gpt-5.5` | 9 | 9 | -0.016 (-0.083-0.056) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `entity_resolution` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-high` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-low` | 9 | 9 | -0.016 (-0.063-0.039) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `entity_resolution` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-medium` | 9 | 9 | -0.079 (-0.130--0.023) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `entity_resolution` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-xhigh` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-nano` | `openai:gpt-5.4-xhigh` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-nano` | `openai:gpt-5.5` | 9 | 9 | -0.030 (-0.083-0.021) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `entity_resolution` | `openai:gpt-5.4-nano` | `openai:gpt-5.5-high` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-nano` | `openai:gpt-5.5-low` | 9 | 9 | -0.030 (-0.097-0.021) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `entity_resolution` | `openai:gpt-5.4-nano` | `openai:gpt-5.5-medium` | 9 | 9 | -0.093 (-0.162-0.000) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `entity_resolution` | `openai:gpt-5.4-nano` | `openai:gpt-5.5-xhigh` | 9 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-high` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-low` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-medium` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-xhigh` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.5` | `openai:gpt-5.5-high` | 27 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.5` | `openai:gpt-5.5-low` | 27 | 27 | -0.043 (-0.083--0.009) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `entity_resolution` | `openai:gpt-5.5` | `openai:gpt-5.5-medium` | 27 | 27 | -0.043 (-0.086--0.009) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `entity_resolution` | `openai:gpt-5.5` | `openai:gpt-5.5-xhigh` | 27 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.5-high` | `openai:gpt-5.5-low` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.5-high` | `openai:gpt-5.5-medium` | 27 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.5-high` | `openai:gpt-5.5-xhigh` | 27 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.5-low` | `openai:gpt-5.5-medium` | 27 | 27 | 0.000 (-0.037-0.044) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.5-medium` if a tie-break is required. |
| `entity_resolution` | `openai:gpt-5.5-low` | `openai:gpt-5.5-xhigh` | 27 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `entity_resolution` | `openai:gpt-5.5-medium` | `openai:gpt-5.5-xhigh` | 27 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-opus-4-7` | `anthropic:claude-sonnet-4-6` | 12 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-opus-4-7` | `google:gemini-3.1-pro-preview` | 12 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-opus-4-7` | `google:gemini-3.1-pro-preview-high` | 12 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-opus-4-7` | `google:gemini-3.1-pro-preview-low` | 12 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-opus-4-7` | `google:gemini-3.1-pro-preview-medium` | 12 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-opus-4-7` | `openai:gpt-5.4` | 12 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-opus-4-7` | `openai:gpt-5.4-high` | 12 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-opus-4-7` | `openai:gpt-5.4-low` | 12 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-opus-4-7` | `openai:gpt-5.4-medium` | 12 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-opus-4-7` | `openai:gpt-5.4-xhigh` | 12 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-opus-4-7` | `openai:gpt-5.5` | 12 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-opus-4-7` | `openai:gpt-5.5-high` | 12 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-opus-4-7` | `openai:gpt-5.5-low` | 12 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-opus-4-7` | `openai:gpt-5.5-medium` | 12 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-opus-4-7` | `openai:gpt-5.5-xhigh` | 12 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-sonnet-4-6` | `google:gemini-3.1-pro-preview` | 12 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-sonnet-4-6` | `google:gemini-3.1-pro-preview-high` | 12 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-sonnet-4-6` | `google:gemini-3.1-pro-preview-low` | 12 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-sonnet-4-6` | `google:gemini-3.1-pro-preview-medium` | 12 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.4` | 12 | 12 | 0.005 (-0.062-0.089) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4` on cost. |
| `eval_judge` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.4-high` | 12 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.4-low` | 12 | 12 | -0.016 (-0.047-0.016) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-low` on cost. |
| `eval_judge` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.4-medium` | 12 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.4-xhigh` | 12 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.5` | 12 | 12 | -0.010 (-0.047-0.016) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5` on cost. |
| `eval_judge` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.5-high` | 12 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.5-low` | 12 | 12 | 0.000 (-0.047-0.036) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5-low` on cost. |
| `eval_judge` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.5-medium` | 12 | 12 | 0.010 (-0.021-0.047) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5-medium` on cost. |
| `eval_judge` | `anthropic:claude-sonnet-4-6` | `openai:gpt-5.5-xhigh` | 12 | 12 | -0.005 (-0.047-0.026) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `anthropic:claude-sonnet-4-6` on cost. |
| `eval_judge` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-high` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-low` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-medium` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4` | 36 | 0 | n/a | -0.333 (-0.500--0.167) | -0.333 (-0.500--0.167) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-high` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-low` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-medium` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-xhigh` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-high` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-low` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-medium` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-xhigh` | 36 | 0 | n/a | -0.333 (-0.500--0.167) | -0.333 (-0.500--0.167) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-low` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-medium` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4` | 36 | 0 | n/a | -0.333 (-0.500--0.167) | -0.333 (-0.500--0.167) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-high` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-low` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-medium` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-xhigh` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-high` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-low` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-medium` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-xhigh` | 36 | 0 | n/a | -0.333 (-0.500--0.167) | -0.333 (-0.500--0.167) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-low` | `google:gemini-3.1-pro-preview-medium` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4` | 36 | 0 | n/a | -0.333 (-0.500--0.167) | -0.333 (-0.500--0.167) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-high` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-low` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-medium` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-xhigh` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-high` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-low` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-medium` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-xhigh` | 36 | 0 | n/a | -0.333 (-0.500--0.167) | -0.333 (-0.500--0.167) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4` | 36 | 0 | n/a | -0.333 (-0.500--0.167) | -0.333 (-0.500--0.167) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-high` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-low` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-medium` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-xhigh` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-high` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-low` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-medium` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-xhigh` | 36 | 0 | n/a | -0.333 (-0.500--0.167) | -0.333 (-0.500--0.167) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4` | `openai:gpt-5.4-high` | 36 | 0 | n/a | 0.333 (0.194-0.500) | 0.333 (0.194-0.500) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4` | `openai:gpt-5.4-low` | 36 | 12 | -0.021 (-0.094-0.036) | -0.667 (-0.806--0.500) | -0.667 (-0.806--0.500) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-low` on cost. |
| `eval_judge` | `openai:gpt-5.4` | `openai:gpt-5.4-medium` | 36 | 0 | n/a | 0.333 (0.194-0.500) | 0.333 (0.194-0.500) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4` | `openai:gpt-5.4-xhigh` | 36 | 0 | n/a | 0.333 (0.194-0.500) | 0.333 (0.194-0.500) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4` | `openai:gpt-5.5` | 36 | 12 | -0.016 (-0.094-0.057) | -0.667 (-0.806--0.500) | -0.667 (-0.806--0.500) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4` on cost. |
| `eval_judge` | `openai:gpt-5.4` | `openai:gpt-5.5-high` | 36 | 0 | n/a | 0.333 (0.194-0.500) | 0.333 (0.194-0.500) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4` | `openai:gpt-5.5-low` | 36 | 12 | -0.005 (-0.094-0.068) | -0.667 (-0.806--0.500) | -0.667 (-0.806--0.500) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4` on cost. |
| `eval_judge` | `openai:gpt-5.4` | `openai:gpt-5.5-medium` | 36 | 12 | 0.005 (-0.083-0.073) | -0.667 (-0.806--0.500) | -0.667 (-0.806--0.500) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4` on cost. |
| `eval_judge` | `openai:gpt-5.4` | `openai:gpt-5.5-xhigh` | 36 | 12 | -0.010 (-0.094-0.052) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4` on cost. |
| `eval_judge` | `openai:gpt-5.4-high` | `openai:gpt-5.4-low` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-high` | `openai:gpt-5.4-medium` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-high` | `openai:gpt-5.4-xhigh` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-high` | `openai:gpt-5.5` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-high` | `openai:gpt-5.5-high` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-high` | `openai:gpt-5.5-low` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-high` | `openai:gpt-5.5-medium` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-high` | `openai:gpt-5.5-xhigh` | 36 | 0 | n/a | -0.333 (-0.500--0.167) | -0.333 (-0.500--0.167) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-low` | `openai:gpt-5.4-medium` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-low` | `openai:gpt-5.4-xhigh` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-low` | `openai:gpt-5.5` | 36 | 36 | 0.010 (-0.024-0.052) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-low` on cost. |
| `eval_judge` | `openai:gpt-5.4-low` | `openai:gpt-5.5-high` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-low` | `openai:gpt-5.5-low` | 36 | 36 | 0.014 (-0.026-0.069) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-low` on cost. |
| `eval_judge` | `openai:gpt-5.4-low` | `openai:gpt-5.5-medium` | 36 | 36 | 0.019 (-0.021-0.064) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-low` on cost. |
| `eval_judge` | `openai:gpt-5.4-low` | `openai:gpt-5.5-xhigh` | 36 | 12 | 0.010 (-0.021-0.052) | 0.667 (0.500-0.833) | 0.667 (0.500-0.833) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-low` on cost. |
| `eval_judge` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-xhigh` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-medium` | `openai:gpt-5.5` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-high` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-low` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-medium` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-xhigh` | 36 | 0 | n/a | -0.333 (-0.500--0.167) | -0.333 (-0.500--0.167) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-high` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-low` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-medium` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-xhigh` | 36 | 0 | n/a | -0.333 (-0.500--0.167) | -0.333 (-0.500--0.167) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.5` | `openai:gpt-5.5-high` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.5` | `openai:gpt-5.5-low` | 36 | 36 | 0.003 (-0.014-0.024) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5` on cost. |
| `eval_judge` | `openai:gpt-5.5` | `openai:gpt-5.5-medium` | 36 | 36 | 0.009 (-0.007-0.028) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5` on cost. |
| `eval_judge` | `openai:gpt-5.5` | `openai:gpt-5.5-xhigh` | 36 | 12 | 0.005 (-0.016-0.026) | 0.667 (0.500-0.833) | 0.667 (0.500-0.833) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5` on cost. |
| `eval_judge` | `openai:gpt-5.5-high` | `openai:gpt-5.5-low` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.5-high` | `openai:gpt-5.5-medium` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.5-high` | `openai:gpt-5.5-xhigh` | 36 | 0 | n/a | -0.333 (-0.500--0.167) | -0.333 (-0.500--0.167) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `eval_judge` | `openai:gpt-5.5-low` | `openai:gpt-5.5-medium` | 36 | 36 | 0.005 (-0.012-0.023) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5-medium` on cost. |
| `eval_judge` | `openai:gpt-5.5-low` | `openai:gpt-5.5-xhigh` | 36 | 12 | -0.005 (-0.021-0.000) | 0.667 (0.500-0.833) | 0.667 (0.500-0.833) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5-low` on cost. |
| `eval_judge` | `openai:gpt-5.5-medium` | `openai:gpt-5.5-xhigh` | 36 | 12 | -0.016 (-0.047-0.000) | 0.667 (0.500-0.833) | 0.667 (0.500-0.833) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5-medium` on cost. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `aws-bedrock:nvidia.nemotron-super-3-120b` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.956 (0.867-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `google:gemini-2.5-flash` | 45 | 10 | 0.028 (-0.036-0.071) | 0.000 (0.000-0.000) | 0.711 (0.458-0.952) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `google:gemini-2.5-flash-lite` | 45 | 43 | 0.019 (-0.003-0.043) | 0.000 (0.000-0.000) | -0.044 (-0.133-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `google:gemini-3.1-pro-preview` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.956 (0.867-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `google:gemini-3.1-pro-preview-high` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.956 (0.867-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `google:gemini-3.1-pro-preview-low` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.956 (0.867-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `google:gemini-3.1-pro-preview-medium` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.956 (0.867-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `groq:llama-3.3-70b-versatile` | 45 | 38 | 0.072 (0.035-0.110) | 0.111 (0.021-0.238) | 0.067 (-0.071-0.208) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `groq:openai/gpt-oss-120b` | 45 | 32 | 0.053 (0.023-0.081) | 0.244 (0.111-0.400) | 0.200 (0.022-0.378) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.956 (0.867-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4-high` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.956 (0.867-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4-low` | 45 | 16 | 0.048 (-0.004-0.103) | 0.622 (0.381-0.857) | 0.578 (0.311-0.833) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4-medium` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.956 (0.867-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4-mini` | 45 | 43 | 0.014 (-0.013-0.051) | 0.000 (0.000-0.000) | -0.044 (-0.133-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4-nano` | 45 | 43 | 0.020 (-0.010-0.061) | 0.000 (0.000-0.000) | -0.044 (-0.133-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4-xhigh` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.956 (0.867-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.5` | 45 | 43 | 0.031 (-0.009-0.077) | 0.000 (0.000-0.000) | -0.044 (-0.133-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.5-high` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.956 (0.867-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.5-low` | 45 | 31 | 0.020 (-0.017-0.060) | 0.289 (0.071-0.533) | 0.244 (0.024-0.489) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.5-medium` | 45 | 5 | 0.108 (0.090-0.125) | 0.889 (0.714-1.000) | 0.844 (0.667-1.000) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.5-xhigh` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.956 (0.867-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-2.5-flash` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -0.244 (-0.471--0.024) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-2.5-flash-lite` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-3.1-pro-preview` | 45 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-3.1-pro-preview-high` | 45 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-3.1-pro-preview-low` | 45 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-3.1-pro-preview-medium` | 45 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `groq:llama-3.3-70b-versatile` | 45 | 0 | n/a | -0.889 (-0.979--0.762) | -0.889 (-0.979--0.762) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `groq:openai/gpt-oss-120b` | 45 | 0 | n/a | -0.756 (-0.889--0.600) | -0.756 (-0.889--0.600) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4` | 45 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-high` | 45 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-low` | 45 | 0 | n/a | -0.378 (-0.619--0.143) | -0.378 (-0.619--0.143) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-medium` | 45 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-mini` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-nano` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-xhigh` | 45 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5-high` | 45 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5-low` | 45 | 0 | n/a | -0.711 (-0.929--0.467) | -0.711 (-0.929--0.467) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5-medium` | 45 | 0 | n/a | -0.111 (-0.286-0.000) | -0.111 (-0.286-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5-xhigh` | 45 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash` | `google:gemini-2.5-flash-lite` | 45 | 11 | -0.023 (-0.080-0.054) | 0.000 (0.000-0.000) | -0.756 (-0.976--0.529) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `memory_compiler` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.244 (0.024-0.471) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview-high` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.244 (0.024-0.471) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview-low` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.244 (0.024-0.471) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview-medium` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.244 (0.024-0.471) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash` | `groq:llama-3.3-70b-versatile` | 45 | 9 | 0.046 (0.021-0.076) | 0.111 (0.021-0.238) | -0.644 (-0.905--0.370) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `google:gemini-2.5-flash` | `groq:openai/gpt-oss-120b` | 45 | 10 | 0.017 (-0.042-0.083) | 0.244 (0.111-0.400) | -0.511 (-0.762--0.267) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `google:gemini-2.5-flash` | `openai:gpt-5.4` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.244 (0.024-0.471) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash` | `openai:gpt-5.4-high` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.244 (0.024-0.471) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash` | `openai:gpt-5.4-low` | 45 | 7 | 0.018 (-0.054-0.097) | 0.622 (0.381-0.857) | -0.133 (-0.381-0.125) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `google:gemini-2.5-flash` | `openai:gpt-5.4-medium` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.244 (0.024-0.471) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash` | `openai:gpt-5.4-mini` | 45 | 11 | -0.034 (-0.077-0.027) | 0.000 (0.000-0.000) | -0.756 (-0.976--0.529) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `memory_compiler` | `google:gemini-2.5-flash` | `openai:gpt-5.4-nano` | 45 | 11 | -0.027 (-0.068-0.045) | 0.000 (0.000-0.000) | -0.756 (-0.976--0.529) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `memory_compiler` | `google:gemini-2.5-flash` | `openai:gpt-5.4-xhigh` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.244 (0.024-0.471) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash` | `openai:gpt-5.5` | 45 | 11 | -0.009 (-0.062-0.062) | 0.000 (0.000-0.000) | -0.756 (-0.976--0.529) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `memory_compiler` | `google:gemini-2.5-flash` | `openai:gpt-5.5-high` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.244 (0.024-0.471) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash` | `openai:gpt-5.5-low` | 45 | 8 | -0.023 (-0.097-0.075) | 0.289 (0.071-0.533) | -0.467 (-0.762--0.125) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `google:gemini-2.5-flash` | `openai:gpt-5.5-medium` | 45 | 2 | 0.062 (0.000-0.125) | 0.889 (0.714-1.000) | 0.133 (-0.119-0.378) | operational_winner_not_quality_winner: Operational results differ, but semantic overlap is too small for a quality recommendation. |
| `memory_compiler` | `google:gemini-2.5-flash` | `openai:gpt-5.5-xhigh` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 0.244 (0.024-0.471) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `google:gemini-3.1-pro-preview` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `google:gemini-3.1-pro-preview-high` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `google:gemini-3.1-pro-preview-low` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `google:gemini-3.1-pro-preview-medium` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `groq:llama-3.3-70b-versatile` | 45 | 40 | 0.054 (0.024-0.084) | 0.111 (0.021-0.238) | 0.111 (0.021-0.238) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `groq:openai/gpt-oss-120b` | 45 | 34 | 0.030 (0.005-0.052) | 0.244 (0.111-0.400) | 0.244 (0.111-0.400) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-high` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-low` | 45 | 17 | 0.030 (-0.018-0.082) | 0.622 (0.381-0.857) | 0.622 (0.381-0.857) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-medium` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-mini` | 45 | 45 | -0.006 (-0.029-0.022) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-nano` | 45 | 45 | 0.001 (-0.024-0.029) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-xhigh` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5` | 45 | 45 | 0.012 (-0.022-0.047) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5-high` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5-low` | 45 | 32 | 0.003 (-0.040-0.048) | 0.289 (0.071-0.533) | 0.289 (0.071-0.533) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5-medium` | 45 | 5 | 0.058 (0.014-0.100) | 0.889 (0.714-1.000) | 0.889 (0.714-1.000) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5-xhigh` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-high` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-low` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-medium` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview` | `groq:llama-3.3-70b-versatile` | 45 | 0 | n/a | -0.889 (-0.979--0.762) | -0.889 (-0.979--0.762) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview` | `groq:openai/gpt-oss-120b` | 45 | 0 | n/a | -0.756 (-0.889--0.595) | -0.756 (-0.889--0.595) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-high` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-low` | 135 | 0 | n/a | -0.370 (-0.607--0.148) | -0.370 (-0.607--0.148) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-medium` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-mini` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-nano` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-xhigh` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5` | 135 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-high` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-low` | 135 | 0 | n/a | -0.704 (-0.929--0.472) | -0.704 (-0.929--0.472) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-medium` | 135 | 0 | n/a | -0.104 (-0.268-0.000) | -0.104 (-0.268-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-xhigh` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-low` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-medium` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-high` | `groq:llama-3.3-70b-versatile` | 45 | 0 | n/a | -0.889 (-0.979--0.762) | -0.889 (-0.979--0.762) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-high` | `groq:openai/gpt-oss-120b` | 45 | 0 | n/a | -0.756 (-0.889--0.595) | -0.756 (-0.889--0.595) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-high` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-low` | 135 | 0 | n/a | -0.370 (-0.607--0.148) | -0.370 (-0.607--0.148) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-medium` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-mini` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-nano` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-xhigh` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5` | 135 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-high` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-low` | 135 | 0 | n/a | -0.704 (-0.929--0.472) | -0.704 (-0.929--0.472) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-medium` | 135 | 0 | n/a | -0.104 (-0.268-0.000) | -0.104 (-0.268-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-xhigh` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-low` | `google:gemini-3.1-pro-preview-medium` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-low` | `groq:llama-3.3-70b-versatile` | 45 | 0 | n/a | -0.889 (-0.979--0.762) | -0.889 (-0.979--0.762) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-low` | `groq:openai/gpt-oss-120b` | 45 | 0 | n/a | -0.756 (-0.889--0.595) | -0.756 (-0.889--0.595) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-high` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-low` | 135 | 0 | n/a | -0.370 (-0.607--0.148) | -0.370 (-0.607--0.148) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-medium` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-mini` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-nano` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-xhigh` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5` | 135 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-high` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-low` | 135 | 0 | n/a | -0.704 (-0.929--0.472) | -0.704 (-0.929--0.472) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-medium` | 135 | 0 | n/a | -0.104 (-0.268-0.000) | -0.104 (-0.268-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-xhigh` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-medium` | `groq:llama-3.3-70b-versatile` | 45 | 0 | n/a | -0.889 (-0.979--0.762) | -0.889 (-0.979--0.762) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-medium` | `groq:openai/gpt-oss-120b` | 45 | 0 | n/a | -0.756 (-0.889--0.595) | -0.756 (-0.889--0.595) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-high` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-low` | 135 | 0 | n/a | -0.370 (-0.607--0.148) | -0.370 (-0.607--0.148) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-medium` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-mini` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-nano` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-xhigh` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5` | 135 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-high` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-low` | 135 | 0 | n/a | -0.704 (-0.929--0.472) | -0.704 (-0.929--0.472) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-medium` | 135 | 0 | n/a | -0.104 (-0.268-0.000) | -0.104 (-0.268-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-xhigh` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `groq:llama-3.3-70b-versatile` | `groq:openai/gpt-oss-120b` | 45 | 29 | -0.016 (-0.045-0.012) | 0.133 (-0.071-0.333) | 0.133 (-0.071-0.333) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:openai/gpt-oss-120b` if a tie-break is required. |
| `memory_compiler` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4` | 45 | 0 | n/a | 0.889 (0.762-0.979) | 0.889 (0.762-0.979) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4-high` | 45 | 0 | n/a | 0.889 (0.762-0.979) | 0.889 (0.762-0.979) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4-low` | 45 | 15 | -0.028 (-0.064-0.002) | 0.511 (0.244-0.778) | 0.511 (0.244-0.778) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4-medium` | 45 | 0 | n/a | 0.889 (0.762-0.979) | 0.889 (0.762-0.979) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4-mini` | 45 | 40 | -0.060 (-0.090--0.030) | -0.111 (-0.238--0.021) | -0.111 (-0.238--0.021) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4-nano` | 45 | 40 | -0.058 (-0.091--0.024) | -0.111 (-0.238--0.021) | -0.111 (-0.238--0.021) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4-xhigh` | 45 | 0 | n/a | 0.889 (0.762-0.979) | 0.889 (0.762-0.979) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.5` | 45 | 40 | -0.045 (-0.084--0.010) | -0.111 (-0.238--0.021) | -0.111 (-0.238--0.021) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.5-high` | 45 | 0 | n/a | 0.889 (0.762-0.979) | 0.889 (0.762-0.979) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.5-low` | 45 | 28 | -0.058 (-0.102--0.020) | 0.178 (-0.089-0.452) | 0.178 (-0.089-0.452) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.5-medium` | 45 | 5 | 0.000 (-0.025-0.025) | 0.778 (0.595-0.952) | 0.778 (0.595-0.952) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.5-xhigh` | 45 | 0 | n/a | 0.889 (0.762-0.979) | 0.889 (0.762-0.979) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4` | 45 | 0 | n/a | 0.756 (0.600-0.889) | 0.756 (0.600-0.889) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-high` | 45 | 0 | n/a | 0.756 (0.600-0.889) | 0.756 (0.600-0.889) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-low` | 45 | 13 | -0.002 (-0.053-0.049) | 0.378 (0.095-0.646) | 0.378 (0.095-0.646) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-medium` | 45 | 0 | n/a | 0.756 (0.600-0.889) | 0.756 (0.600-0.889) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-mini` | 45 | 34 | -0.036 (-0.068-0.004) | -0.244 (-0.400--0.111) | -0.244 (-0.400--0.111) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-nano` | 45 | 34 | -0.028 (-0.061-0.011) | -0.244 (-0.400--0.111) | -0.244 (-0.400--0.111) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-xhigh` | 45 | 0 | n/a | 0.756 (0.600-0.889) | 0.756 (0.600-0.889) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5` | 45 | 34 | -0.024 (-0.060-0.017) | -0.244 (-0.400--0.111) | -0.244 (-0.400--0.111) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5-high` | 45 | 0 | n/a | 0.756 (0.600-0.889) | 0.756 (0.600-0.889) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5-low` | 45 | 24 | -0.043 (-0.084-0.001) | 0.044 (-0.222-0.333) | 0.044 (-0.222-0.333) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:openai/gpt-oss-120b` if a tie-break is required. |
| `memory_compiler` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5-medium` | 45 | 4 | 0.010 (0.000-0.031) | 0.644 (0.422-0.844) | 0.644 (0.422-0.844) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5-xhigh` | 45 | 0 | n/a | 0.756 (0.600-0.889) | 0.756 (0.600-0.889) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4` | `openai:gpt-5.4-high` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4` | `openai:gpt-5.4-low` | 135 | 0 | n/a | -0.370 (-0.607--0.148) | -0.370 (-0.607--0.148) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4` | `openai:gpt-5.4-medium` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4` | `openai:gpt-5.4-mini` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4` | `openai:gpt-5.4-nano` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4` | `openai:gpt-5.4-xhigh` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4` | `openai:gpt-5.5` | 135 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4` | `openai:gpt-5.5-high` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4` | `openai:gpt-5.5-low` | 135 | 0 | n/a | -0.704 (-0.929--0.472) | -0.704 (-0.929--0.472) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4` | `openai:gpt-5.5-medium` | 135 | 0 | n/a | -0.104 (-0.268-0.000) | -0.104 (-0.268-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4` | `openai:gpt-5.5-xhigh` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-high` | `openai:gpt-5.4-low` | 135 | 0 | n/a | -0.370 (-0.607--0.148) | -0.370 (-0.607--0.148) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-high` | `openai:gpt-5.4-medium` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-high` | `openai:gpt-5.4-mini` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-high` | `openai:gpt-5.4-nano` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-high` | `openai:gpt-5.4-xhigh` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-high` | `openai:gpt-5.5` | 135 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-high` | `openai:gpt-5.5-high` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-high` | `openai:gpt-5.5-low` | 135 | 0 | n/a | -0.704 (-0.929--0.472) | -0.704 (-0.929--0.472) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-high` | `openai:gpt-5.5-medium` | 135 | 0 | n/a | -0.104 (-0.268-0.000) | -0.104 (-0.268-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-high` | `openai:gpt-5.5-xhigh` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-low` | `openai:gpt-5.4-medium` | 135 | 0 | n/a | 0.370 (0.148-0.607) | 0.370 (0.148-0.607) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-low` | `openai:gpt-5.4-mini` | 45 | 17 | -0.026 (-0.072-0.017) | -0.622 (-0.857--0.378) | -0.622 (-0.857--0.378) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `openai:gpt-5.4-low` | `openai:gpt-5.4-nano` | 45 | 17 | -0.025 (-0.075-0.020) | -0.622 (-0.857--0.378) | -0.622 (-0.857--0.378) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `openai:gpt-5.4-low` | `openai:gpt-5.4-xhigh` | 135 | 0 | n/a | 0.370 (0.148-0.607) | 0.370 (0.148-0.607) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-low` | `openai:gpt-5.5` | 135 | 50 | -0.034 (-0.055--0.010) | -0.630 (-0.852--0.393) | -0.630 (-0.852--0.393) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `openai:gpt-5.4-low` | `openai:gpt-5.5-high` | 135 | 0 | n/a | 0.370 (0.148-0.607) | 0.370 (0.148-0.607) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-low` | `openai:gpt-5.5-low` | 135 | 50 | -0.037 (-0.060--0.014) | -0.333 (-0.571--0.119) | -0.333 (-0.571--0.119) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `openai:gpt-5.4-low` | `openai:gpt-5.5-medium` | 135 | 14 | -0.015 (-0.051-0.009) | 0.267 (0.081-0.484) | 0.267 (0.081-0.484) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `openai:gpt-5.4-low` | `openai:gpt-5.5-xhigh` | 135 | 0 | n/a | 0.370 (0.148-0.607) | 0.370 (0.148-0.607) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-mini` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-nano` | 45 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-xhigh` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-medium` | `openai:gpt-5.5` | 135 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-high` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-low` | 135 | 0 | n/a | -0.704 (-0.929--0.472) | -0.704 (-0.929--0.472) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-medium` | 135 | 0 | n/a | -0.104 (-0.268-0.000) | -0.104 (-0.268-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-xhigh` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-mini` | `openai:gpt-5.4-nano` | 45 | 45 | 0.006 (-0.013-0.027) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `memory_compiler` | `openai:gpt-5.4-mini` | `openai:gpt-5.4-xhigh` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-mini` | `openai:gpt-5.5` | 45 | 45 | 0.017 (-0.017-0.050) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `memory_compiler` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-high` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-low` | 45 | 32 | 0.007 (-0.037-0.050) | 0.289 (0.071-0.533) | 0.289 (0.071-0.533) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-medium` | 45 | 5 | 0.092 (0.042-0.125) | 0.889 (0.714-1.000) | 0.889 (0.714-1.000) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-xhigh` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-nano` | `openai:gpt-5.4-xhigh` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-nano` | `openai:gpt-5.5` | 45 | 45 | 0.011 (-0.022-0.042) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `memory_compiler` | `openai:gpt-5.4-nano` | `openai:gpt-5.5-high` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-nano` | `openai:gpt-5.5-low` | 45 | 32 | 0.008 (-0.036-0.052) | 0.289 (0.071-0.533) | 0.289 (0.071-0.533) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `openai:gpt-5.4-nano` | `openai:gpt-5.5-medium` | 45 | 5 | 0.083 (0.028-0.125) | 0.889 (0.714-1.000) | 0.889 (0.714-1.000) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `openai:gpt-5.4-nano` | `openai:gpt-5.5-xhigh` | 45 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5` | 135 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-high` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-low` | 135 | 0 | n/a | -0.704 (-0.929--0.472) | -0.704 (-0.929--0.472) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-medium` | 135 | 0 | n/a | -0.104 (-0.268-0.000) | -0.104 (-0.268-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-xhigh` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.5` | `openai:gpt-5.5-high` | 135 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.5` | `openai:gpt-5.5-low` | 135 | 95 | 0.005 (-0.005-0.017) | 0.296 (0.071-0.528) | 0.296 (0.071-0.528) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `openai:gpt-5.5` | `openai:gpt-5.5-medium` | 135 | 14 | 0.027 (0.003-0.075) | 0.896 (0.732-1.000) | 0.896 (0.732-1.000) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `memory_compiler` | `openai:gpt-5.5` | `openai:gpt-5.5-xhigh` | 135 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.5-high` | `openai:gpt-5.5-low` | 135 | 0 | n/a | -0.704 (-0.929--0.472) | -0.704 (-0.929--0.472) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.5-high` | `openai:gpt-5.5-medium` | 135 | 0 | n/a | -0.104 (-0.268-0.000) | -0.104 (-0.268-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.5-high` | `openai:gpt-5.5-xhigh` | 135 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.5-low` | `openai:gpt-5.5-medium` | 135 | 14 | 0.018 (0.000-0.050) | 0.600 (0.361-0.852) | 0.600 (0.361-0.852) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `memory_compiler` | `openai:gpt-5.5-low` | `openai:gpt-5.5-xhigh` | 135 | 0 | n/a | 0.704 (0.471-0.929) | 0.704 (0.471-0.929) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `memory_compiler` | `openai:gpt-5.5-medium` | `openai:gpt-5.5-xhigh` | 135 | 0 | n/a | 0.104 (0.000-0.268) | 0.104 (0.000-0.268) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `aws-bedrock:nvidia.nemotron-super-3-120b` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-2.5-flash` | 36 | 32 | -0.019 (-0.101-0.051) | 0.000 (0.000-0.000) | 0.111 (0.000-0.267) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-2.5-flash-lite` | 36 | 36 | -0.010 (-0.078-0.043) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-3.1-pro-preview` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-3.1-pro-preview-high` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-3.1-pro-preview-low` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `google:gemini-3.1-pro-preview-medium` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `groq:llama-3.3-70b-versatile` | 36 | 36 | -0.011 (-0.070-0.037) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:llama-3.3-70b-versatile` if a tie-break is required. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `groq:openai/gpt-oss-120b` | 36 | 24 | -0.011 (-0.078-0.038) | 0.333 (0.133-0.545) | 0.333 (0.133-0.545) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-high` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-low` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-medium` | 36 | 16 | -0.004 (-0.089-0.073) | 0.556 (0.278-0.833) | 0.556 (0.278-0.833) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-mini` | 36 | 36 | 0.001 (-0.049-0.040) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-nano` | 36 | 36 | 0.033 (-0.039-0.095) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.4-xhigh` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.5` | 36 | 10 | 0.001 (-0.073-0.058) | 0.722 (0.455-0.967) | 0.722 (0.455-0.967) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.5-high` | 36 | 26 | -0.037 (-0.106-0.022) | 0.278 (0.033-0.545) | 0.278 (0.033-0.545) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.5-low` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.5-medium` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `anthropic:claude-haiku-4-5-20251001` | `openai:gpt-5.5-xhigh` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-2.5-flash` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -0.889 (-1.000--0.733) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-2.5-flash-lite` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-3.1-pro-preview` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-3.1-pro-preview-high` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-3.1-pro-preview-low` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-3.1-pro-preview-medium` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `groq:llama-3.3-70b-versatile` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `groq:openai/gpt-oss-120b` | 36 | 0 | n/a | -0.667 (-0.867--0.455) | -0.667 (-0.867--0.455) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-high` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-low` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-medium` | 36 | 0 | n/a | -0.444 (-0.722--0.167) | -0.444 (-0.722--0.167) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-mini` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-nano` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-xhigh` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5` | 36 | 0 | n/a | -0.278 (-0.545--0.033) | -0.278 (-0.545--0.033) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5-high` | 36 | 0 | n/a | -0.722 (-0.967--0.455) | -0.722 (-0.967--0.455) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5-low` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5-medium` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5-xhigh` | 36 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `google:gemini-2.5-flash-lite` | 36 | 32 | 0.007 (-0.022-0.034) | 0.000 (0.000-0.000) | -0.111 (-0.267-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.733-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview-high` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.733-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview-low` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.733-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview-medium` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.733-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `groq:llama-3.3-70b-versatile` | 36 | 32 | 0.001 (-0.040-0.043) | 0.000 (0.000-0.000) | -0.111 (-0.267-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:llama-3.3-70b-versatile` if a tie-break is required. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `groq:openai/gpt-oss-120b` | 36 | 20 | 0.017 (-0.019-0.050) | 0.333 (0.133-0.545) | 0.222 (-0.061-0.489) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `openai:gpt-5.4` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.733-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `openai:gpt-5.4-high` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.733-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `openai:gpt-5.4-low` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.733-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `openai:gpt-5.4-medium` | 36 | 14 | 0.027 (-0.058-0.094) | 0.556 (0.278-0.833) | 0.444 (0.128-0.750) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `openai:gpt-5.4-mini` | 36 | 32 | 0.021 (-0.023-0.062) | 0.000 (0.000-0.000) | -0.111 (-0.267-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `openai:gpt-5.4-nano` | 36 | 32 | 0.052 (0.018-0.092) | 0.000 (0.000-0.000) | -0.111 (-0.267-0.000) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `openai:gpt-5.4-xhigh` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.733-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `openai:gpt-5.5` | 36 | 9 | 0.002 (-0.042-0.037) | 0.722 (0.455-0.967) | 0.611 (0.306-0.889) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `openai:gpt-5.5-high` | 36 | 23 | -0.012 (-0.062-0.034) | 0.278 (0.033-0.545) | 0.167 (-0.100-0.452) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `openai:gpt-5.5-low` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.733-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `openai:gpt-5.5-medium` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.733-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash` | `openai:gpt-5.5-xhigh` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 0.889 (0.733-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `google:gemini-3.1-pro-preview` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `google:gemini-3.1-pro-preview-high` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `google:gemini-3.1-pro-preview-low` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `google:gemini-3.1-pro-preview-medium` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `groq:llama-3.3-70b-versatile` | 36 | 36 | -0.001 (-0.034-0.038) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `groq:openai/gpt-oss-120b` | 36 | 24 | 0.017 (-0.016-0.051) | 0.333 (0.133-0.545) | 0.333 (0.133-0.545) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-high` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-low` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-medium` | 36 | 16 | 0.014 (-0.050-0.076) | 0.556 (0.278-0.833) | 0.556 (0.278-0.833) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-mini` | 36 | 36 | 0.010 (-0.031-0.048) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-nano` | 36 | 36 | 0.043 (0.007-0.084) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-xhigh` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5` | 36 | 10 | -0.015 (-0.060-0.031) | 0.722 (0.455-0.967) | 0.722 (0.455-0.967) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5-high` | 36 | 26 | -0.018 (-0.056-0.022) | 0.278 (0.033-0.545) | 0.278 (0.033-0.545) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5-low` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5-medium` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5-xhigh` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-high` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-low` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-medium` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview` | `groq:llama-3.3-70b-versatile` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview` | `groq:openai/gpt-oss-120b` | 36 | 0 | n/a | -0.667 (-0.872--0.452) | -0.667 (-0.872--0.452) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-high` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-low` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-medium` | 108 | 0 | n/a | -0.463 (-0.727--0.182) | -0.463 (-0.727--0.182) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-mini` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-nano` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-xhigh` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5` | 108 | 0 | n/a | -0.306 (-0.564--0.067) | -0.306 (-0.564--0.067) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-high` | 108 | 0 | n/a | -0.731 (-0.981--0.472) | -0.731 (-0.981--0.472) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-low` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-medium` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-xhigh` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-low` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-medium` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-high` | `groq:llama-3.3-70b-versatile` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-high` | `groq:openai/gpt-oss-120b` | 36 | 0 | n/a | -0.667 (-0.872--0.452) | -0.667 (-0.872--0.452) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-high` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-low` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-medium` | 108 | 0 | n/a | -0.463 (-0.727--0.182) | -0.463 (-0.727--0.182) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-mini` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-nano` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-xhigh` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5` | 108 | 0 | n/a | -0.306 (-0.564--0.067) | -0.306 (-0.564--0.067) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-high` | 108 | 0 | n/a | -0.731 (-0.981--0.472) | -0.731 (-0.981--0.472) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-low` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-medium` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-xhigh` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-low` | `google:gemini-3.1-pro-preview-medium` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-low` | `groq:llama-3.3-70b-versatile` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-low` | `groq:openai/gpt-oss-120b` | 36 | 0 | n/a | -0.667 (-0.872--0.452) | -0.667 (-0.872--0.452) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-high` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-low` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-medium` | 108 | 0 | n/a | -0.463 (-0.727--0.182) | -0.463 (-0.727--0.182) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-mini` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-nano` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-xhigh` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5` | 108 | 0 | n/a | -0.306 (-0.564--0.067) | -0.306 (-0.564--0.067) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-high` | 108 | 0 | n/a | -0.731 (-0.981--0.472) | -0.731 (-0.981--0.472) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-low` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-medium` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-xhigh` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-medium` | `groq:llama-3.3-70b-versatile` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-medium` | `groq:openai/gpt-oss-120b` | 36 | 0 | n/a | -0.667 (-0.872--0.452) | -0.667 (-0.872--0.452) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-high` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-low` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-medium` | 108 | 0 | n/a | -0.463 (-0.727--0.182) | -0.463 (-0.727--0.182) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-mini` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-nano` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-xhigh` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5` | 108 | 0 | n/a | -0.306 (-0.564--0.067) | -0.306 (-0.564--0.067) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-high` | 108 | 0 | n/a | -0.731 (-0.981--0.472) | -0.731 (-0.981--0.472) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-low` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-medium` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-xhigh` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `groq:llama-3.3-70b-versatile` | `groq:openai/gpt-oss-120b` | 36 | 24 | -0.000 (-0.055-0.043) | 0.333 (0.133-0.545) | 0.333 (0.133-0.545) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4-high` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4-low` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4-medium` | 36 | 16 | 0.039 (-0.023-0.090) | 0.556 (0.278-0.833) | 0.556 (0.278-0.833) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4-mini` | 36 | 36 | 0.012 (-0.034-0.054) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:llama-3.3-70b-versatile` if a tie-break is required. |
| `recall_synthesizer` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4-nano` | 36 | 36 | 0.044 (-0.015-0.099) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:llama-3.3-70b-versatile` if a tie-break is required. |
| `recall_synthesizer` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.4-xhigh` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.5` | 36 | 10 | -0.010 (-0.047-0.025) | 0.722 (0.455-0.967) | 0.722 (0.455-0.967) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.5-high` | 36 | 26 | -0.018 (-0.054-0.014) | 0.278 (0.033-0.545) | 0.278 (0.033-0.545) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.5-low` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.5-medium` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `groq:llama-3.3-70b-versatile` | `openai:gpt-5.5-xhigh` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4` | 36 | 0 | n/a | 0.667 (0.455-0.867) | 0.667 (0.455-0.867) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-high` | 36 | 0 | n/a | 0.667 (0.455-0.867) | 0.667 (0.455-0.867) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-low` | 36 | 0 | n/a | 0.667 (0.455-0.867) | 0.667 (0.455-0.867) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-medium` | 36 | 11 | -0.017 (-0.089-0.062) | 0.222 (-0.103-0.556) | 0.222 (-0.103-0.556) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:openai/gpt-oss-120b` if a tie-break is required. |
| `recall_synthesizer` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-mini` | 36 | 24 | 0.007 (-0.033-0.044) | -0.333 (-0.545--0.133) | -0.333 (-0.545--0.133) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-nano` | 36 | 24 | 0.034 (0.003-0.072) | -0.333 (-0.545--0.133) | -0.333 (-0.545--0.133) | tradeoff_quality_vs_ops: One model has higher semantic quality while the other is more operationally reliable. |
| `recall_synthesizer` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-xhigh` | 36 | 0 | n/a | 0.667 (0.455-0.867) | 0.667 (0.455-0.867) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5` | 36 | 7 | -0.012 (-0.075-0.016) | 0.389 (0.051-0.727) | 0.389 (0.051-0.727) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5-high` | 36 | 17 | -0.035 (-0.077-0.011) | -0.056 (-0.367-0.282) | -0.056 (-0.367-0.282) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:openai/gpt-oss-120b` if a tie-break is required. |
| `recall_synthesizer` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5-low` | 36 | 0 | n/a | 0.667 (0.455-0.867) | 0.667 (0.455-0.867) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5-medium` | 36 | 0 | n/a | 0.667 (0.455-0.867) | 0.667 (0.455-0.867) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5-xhigh` | 36 | 0 | n/a | 0.667 (0.455-0.867) | 0.667 (0.455-0.867) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4` | `openai:gpt-5.4-high` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4` | `openai:gpt-5.4-low` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4` | `openai:gpt-5.4-medium` | 108 | 0 | n/a | -0.463 (-0.727--0.182) | -0.463 (-0.727--0.182) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4` | `openai:gpt-5.4-mini` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4` | `openai:gpt-5.4-nano` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4` | `openai:gpt-5.4-xhigh` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4` | `openai:gpt-5.5` | 108 | 0 | n/a | -0.306 (-0.564--0.067) | -0.306 (-0.564--0.067) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4` | `openai:gpt-5.5-high` | 108 | 0 | n/a | -0.731 (-0.981--0.472) | -0.731 (-0.981--0.472) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4` | `openai:gpt-5.5-low` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4` | `openai:gpt-5.5-medium` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4` | `openai:gpt-5.5-xhigh` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-high` | `openai:gpt-5.4-low` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-high` | `openai:gpt-5.4-medium` | 108 | 0 | n/a | -0.463 (-0.727--0.182) | -0.463 (-0.727--0.182) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-high` | `openai:gpt-5.4-mini` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-high` | `openai:gpt-5.4-nano` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-high` | `openai:gpt-5.4-xhigh` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-high` | `openai:gpt-5.5` | 108 | 0 | n/a | -0.306 (-0.564--0.067) | -0.306 (-0.564--0.067) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-high` | `openai:gpt-5.5-high` | 108 | 0 | n/a | -0.731 (-0.981--0.472) | -0.731 (-0.981--0.472) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-high` | `openai:gpt-5.5-low` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-high` | `openai:gpt-5.5-medium` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-high` | `openai:gpt-5.5-xhigh` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-low` | `openai:gpt-5.4-medium` | 108 | 0 | n/a | -0.463 (-0.727--0.182) | -0.463 (-0.727--0.182) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-low` | `openai:gpt-5.4-mini` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-low` | `openai:gpt-5.4-nano` | 36 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-low` | `openai:gpt-5.4-xhigh` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-low` | `openai:gpt-5.5` | 108 | 0 | n/a | -0.306 (-0.564--0.067) | -0.306 (-0.564--0.067) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-low` | `openai:gpt-5.5-high` | 108 | 0 | n/a | -0.731 (-0.981--0.472) | -0.731 (-0.981--0.472) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-low` | `openai:gpt-5.5-low` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-low` | `openai:gpt-5.5-medium` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-low` | `openai:gpt-5.5-xhigh` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-mini` | 36 | 16 | -0.006 (-0.057-0.047) | -0.556 (-0.833--0.273) | -0.556 (-0.833--0.273) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-nano` | 36 | 16 | 0.023 (-0.040-0.090) | -0.556 (-0.833--0.273) | -0.556 (-0.833--0.273) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-xhigh` | 108 | 0 | n/a | 0.463 (0.182-0.727) | 0.463 (0.182-0.727) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-medium` | `openai:gpt-5.5` | 108 | 0 | n/a | 0.157 (-0.325-0.630) | 0.157 (-0.325-0.630) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-high` | 108 | 50 | -0.051 (-0.079--0.023) | -0.269 (-0.556--0.065) | -0.269 (-0.556--0.065) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `recall_synthesizer` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-low` | 108 | 0 | n/a | 0.463 (0.182-0.727) | 0.463 (0.182-0.727) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-medium` | 108 | 0 | n/a | 0.463 (0.182-0.727) | 0.463 (0.182-0.727) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-xhigh` | 108 | 0 | n/a | 0.463 (0.182-0.727) | 0.463 (0.182-0.727) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-mini` | `openai:gpt-5.4-nano` | 36 | 36 | 0.032 (-0.007-0.071) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `recall_synthesizer` | `openai:gpt-5.4-mini` | `openai:gpt-5.4-xhigh` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-mini` | `openai:gpt-5.5` | 36 | 10 | -0.034 (-0.094-0.016) | 0.722 (0.455-0.967) | 0.722 (0.455-0.967) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-high` | 36 | 26 | -0.025 (-0.063-0.012) | 0.278 (0.033-0.545) | 0.278 (0.033-0.545) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `recall_synthesizer` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-low` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-medium` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-xhigh` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-nano` | `openai:gpt-5.4-xhigh` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-nano` | `openai:gpt-5.5` | 36 | 10 | -0.074 (-0.182--0.003) | 0.722 (0.455-0.967) | 0.722 (0.455-0.967) | tradeoff_quality_vs_ops: One model has higher semantic quality while the other is more operationally reliable. |
| `recall_synthesizer` | `openai:gpt-5.4-nano` | `openai:gpt-5.5-high` | 36 | 26 | -0.054 (-0.103--0.004) | 0.278 (0.033-0.545) | 0.278 (0.033-0.545) | tradeoff_quality_vs_ops: One model has higher semantic quality while the other is more operationally reliable. |
| `recall_synthesizer` | `openai:gpt-5.4-nano` | `openai:gpt-5.5-low` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-nano` | `openai:gpt-5.5-medium` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-nano` | `openai:gpt-5.5-xhigh` | 36 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5` | 108 | 0 | n/a | -0.306 (-0.564--0.067) | -0.306 (-0.564--0.067) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-high` | 108 | 0 | n/a | -0.731 (-0.981--0.472) | -0.731 (-0.981--0.472) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-low` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-medium` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-xhigh` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.5` | `openai:gpt-5.5-high` | 108 | 4 | 0.000 (0.000-0.000) | -0.426 (-0.919-0.077) | -0.426 (-0.919-0.077) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.5-high` if a tie-break is required. |
| `recall_synthesizer` | `openai:gpt-5.5` | `openai:gpt-5.5-low` | 108 | 0 | n/a | 0.306 (0.067-0.564) | 0.306 (0.067-0.564) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.5` | `openai:gpt-5.5-medium` | 108 | 0 | n/a | 0.306 (0.067-0.564) | 0.306 (0.067-0.564) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.5` | `openai:gpt-5.5-xhigh` | 108 | 0 | n/a | 0.306 (0.067-0.564) | 0.306 (0.067-0.564) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.5-high` | `openai:gpt-5.5-low` | 108 | 0 | n/a | 0.731 (0.468-0.981) | 0.731 (0.468-0.981) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.5-high` | `openai:gpt-5.5-medium` | 108 | 0 | n/a | 0.731 (0.468-0.981) | 0.731 (0.468-0.981) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.5-high` | `openai:gpt-5.5-xhigh` | 108 | 0 | n/a | 0.731 (0.468-0.981) | 0.731 (0.468-0.981) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.5-low` | `openai:gpt-5.5-medium` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.5-low` | `openai:gpt-5.5-xhigh` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `recall_synthesizer` | `openai:gpt-5.5-medium` | `openai:gpt-5.5-xhigh` | 108 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-2.5-flash-lite` | `google:gemini-3.1-pro-preview` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-2.5-flash-lite` | `google:gemini-3.1-pro-preview-high` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-2.5-flash-lite` | `google:gemini-3.1-pro-preview-low` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-2.5-flash-lite` | `google:gemini-3.1-pro-preview-medium` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-2.5-flash-lite` | `groq:llama-3.1-8b-instant` | 6 | 5 | -0.025 (-0.125-0.062) | 0.167 (0.000-0.667) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:llama-3.1-8b-instant` if a tie-break is required. |
| `router` | `google:gemini-2.5-flash-lite` | `openai:gpt-5-nano` | 6 | 5 | 0.050 (-0.094-0.125) | 0.000 (0.000-0.000) | -0.167 (-0.667-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `router` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-high` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-low` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-medium` | 6 | 5 | 0.037 (0.000-0.083) | 0.000 (0.000-0.000) | -0.167 (-0.667-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `router` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-xhigh` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5-high` | 6 | 5 | 0.000 (-0.094-0.075) | 0.000 (0.000-0.000) | -0.167 (-0.667-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `router` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5-low` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5-medium` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5-xhigh` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-high` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-low` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-medium` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview` | `groq:llama-3.1-8b-instant` | 6 | 0 | n/a | -0.833 (-1.000--0.500) | -0.833 (-1.000--0.500) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview` | `openai:gpt-5-nano` | 6 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-high` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-low` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-medium` | 18 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-high` | 18 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-low` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-medium` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-low` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-medium` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-high` | `groq:llama-3.1-8b-instant` | 6 | 0 | n/a | -0.833 (-1.000--0.500) | -0.833 (-1.000--0.500) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5-nano` | 6 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-high` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-low` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-medium` | 18 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-high` | 18 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-low` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-medium` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-low` | `google:gemini-3.1-pro-preview-medium` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-low` | `groq:llama-3.1-8b-instant` | 6 | 0 | n/a | -0.833 (-1.000--0.500) | -0.833 (-1.000--0.500) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5-nano` | 6 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-high` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-low` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-medium` | 18 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-high` | 18 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-low` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-medium` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-medium` | `groq:llama-3.1-8b-instant` | 6 | 0 | n/a | -0.833 (-1.000--0.500) | -0.833 (-1.000--0.500) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5-nano` | 6 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-high` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-low` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-medium` | 18 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-high` | 18 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-low` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-medium` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `groq:llama-3.1-8b-instant` | `openai:gpt-5-nano` | 6 | 5 | 0.075 (0.021-0.125) | -0.167 (-0.667-0.000) | -0.167 (-0.667-0.000) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `router` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.4` | 6 | 0 | n/a | 0.833 (0.333-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.4-high` | 6 | 0 | n/a | 0.833 (0.333-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.4-low` | 6 | 0 | n/a | 0.833 (0.333-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.4-medium` | 6 | 5 | 0.062 (0.010-0.125) | -0.167 (-0.667-0.000) | -0.167 (-0.667-0.000) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `router` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.4-xhigh` | 6 | 0 | n/a | 0.833 (0.333-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.5` | 6 | 0 | n/a | 0.833 (0.333-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.5-high` | 6 | 5 | 0.025 (0.000-0.094) | -0.167 (-0.667-0.000) | -0.167 (-0.667-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:llama-3.1-8b-instant` if a tie-break is required. |
| `router` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.5-low` | 6 | 0 | n/a | 0.833 (0.333-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.5-medium` | 6 | 0 | n/a | 0.833 (0.333-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.5-xhigh` | 6 | 0 | n/a | 0.833 (0.333-1.000) | 0.833 (0.333-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5-nano` | `openai:gpt-5.4` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5-nano` | `openai:gpt-5.4-high` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5-nano` | `openai:gpt-5.4-low` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5-nano` | `openai:gpt-5.4-medium` | 6 | 6 | 0.010 (-0.094-0.104) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5-nano` if a tie-break is required. |
| `router` | `openai:gpt-5-nano` | `openai:gpt-5.4-xhigh` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5-nano` | `openai:gpt-5.5` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5-nano` | `openai:gpt-5.5-high` | 6 | 6 | -0.021 (-0.104-0.083) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5-nano` if a tie-break is required. |
| `router` | `openai:gpt-5-nano` | `openai:gpt-5.5-low` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5-nano` | `openai:gpt-5.5-medium` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5-nano` | `openai:gpt-5.5-xhigh` | 6 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4` | `openai:gpt-5.4-high` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4` | `openai:gpt-5.4-low` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4` | `openai:gpt-5.4-medium` | 18 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4` | `openai:gpt-5.4-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4` | `openai:gpt-5.5` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4` | `openai:gpt-5.5-high` | 18 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4` | `openai:gpt-5.5-low` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4` | `openai:gpt-5.5-medium` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4` | `openai:gpt-5.5-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-high` | `openai:gpt-5.4-low` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-high` | `openai:gpt-5.4-medium` | 18 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-high` | `openai:gpt-5.4-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-high` | `openai:gpt-5.5` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-high` | `openai:gpt-5.5-high` | 18 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-high` | `openai:gpt-5.5-low` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-high` | `openai:gpt-5.5-medium` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-high` | `openai:gpt-5.5-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-low` | `openai:gpt-5.4-medium` | 18 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-low` | `openai:gpt-5.4-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-low` | `openai:gpt-5.5` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-low` | `openai:gpt-5.5-high` | 18 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-low` | `openai:gpt-5.5-low` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-low` | `openai:gpt-5.5-medium` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-low` | `openai:gpt-5.5-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-xhigh` | 18 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-medium` | `openai:gpt-5.5` | 18 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-high` | 18 | 18 | -0.017 (-0.049-0.014) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-medium` if a tie-break is required. |
| `router` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-low` | 18 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-medium` | 18 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-xhigh` | 18 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-high` | 18 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-low` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-medium` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.5` | `openai:gpt-5.5-high` | 18 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.5` | `openai:gpt-5.5-low` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.5` | `openai:gpt-5.5-medium` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.5` | `openai:gpt-5.5-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.5-high` | `openai:gpt-5.5-low` | 18 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.5-high` | `openai:gpt-5.5-medium` | 18 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.5-high` | `openai:gpt-5.5-xhigh` | 18 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.5-low` | `openai:gpt-5.5-medium` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.5-low` | `openai:gpt-5.5-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `router` | `openai:gpt-5.5-medium` | `openai:gpt-5.5-xhigh` | 18 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | 60 | 8 | -0.016 (-0.125-0.083) | 0.000 (0.000-0.000) | 0.833 (0.667-0.967) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `aws-bedrock:nvidia.nemotron-super-3-120b` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `google:gemini-2.5-flash` | 60 | 36 | 0.009 (-0.030-0.049) | 0.000 (0.000-0.000) | 0.383 (0.233-0.550) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `google:gemini-2.5-flash-lite` | 60 | 58 | 0.009 (-0.019-0.036) | 0.000 (0.000-0.000) | 0.000 (-0.067-0.067) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `google:gemini-3.1-pro-preview` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `google:gemini-3.1-pro-preview-high` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `google:gemini-3.1-pro-preview-low` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `google:gemini-3.1-pro-preview-medium` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `groq:llama-3.1-8b-instant` | 60 | 41 | 0.062 (0.033-0.091) | 0.283 (0.150-0.417) | 0.283 (0.150-0.433) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `groq:openai/gpt-oss-120b` | 60 | 44 | 0.050 (0.015-0.083) | 0.250 (0.117-0.400) | 0.233 (0.100-0.383) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4-high` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4-low` | 60 | 40 | 0.016 (-0.018-0.054) | 0.317 (0.117-0.533) | 0.300 (0.100-0.517) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4-medium` | 60 | 59 | -0.007 (-0.042-0.029) | 0.000 (0.000-0.000) | -0.017 (-0.067-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4-mini` | 60 | 59 | 0.012 (-0.013-0.043) | 0.000 (0.000-0.000) | -0.017 (-0.067-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4-nano` | 60 | 59 | 0.004 (-0.020-0.029) | 0.000 (0.000-0.000) | -0.017 (-0.067-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.4-xhigh` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.5` | 60 | 7 | 0.095 (0.000-0.208) | 0.883 (0.733-1.000) | 0.867 (0.700-0.983) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.5-high` | 60 | 58 | -0.012 (-0.042-0.023) | 0.017 (0.000-0.067) | 0.000 (-0.067-0.067) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.5-low` | 60 | 30 | 0.004 (-0.047-0.073) | 0.483 (0.267-0.700) | 0.467 (0.233-0.700) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.5-medium` | 60 | 56 | -0.013 (-0.050-0.027) | 0.050 (0.000-0.133) | 0.033 (-0.050-0.133) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:mistral.ministral-3-14b-instruct` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:mistral.ministral-3-14b-instruct` | `openai:gpt-5.5-xhigh` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `aws-bedrock:nvidia.nemotron-super-3-120b` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.150 (0.033-0.300) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `google:gemini-2.5-flash` | 60 | 4 | -0.047 (-0.188-0.047) | 0.000 (0.000-0.000) | -0.450 (-0.650--0.217) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:nvidia.nemotron-nano-9b-v2` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `google:gemini-2.5-flash-lite` | 60 | 8 | 0.023 (-0.047-0.098) | 0.000 (0.000-0.000) | -0.833 (-0.967--0.667) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `google:gemini-3.1-pro-preview` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.150 (0.033-0.300) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `google:gemini-3.1-pro-preview-high` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.150 (0.033-0.300) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `google:gemini-3.1-pro-preview-low` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.150 (0.033-0.300) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `google:gemini-3.1-pro-preview-medium` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.150 (0.033-0.300) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `groq:llama-3.1-8b-instant` | 60 | 8 | 0.062 (0.000-0.143) | 0.283 (0.150-0.417) | -0.550 (-0.717--0.367) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `groq:openai/gpt-oss-120b` | 60 | 6 | 0.052 (0.010-0.098) | 0.250 (0.117-0.400) | -0.600 (-0.800--0.383) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `openai:gpt-5.4` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.150 (0.033-0.300) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `openai:gpt-5.4-high` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.150 (0.033-0.300) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `openai:gpt-5.4-low` | 60 | 8 | -0.025 (-0.061-0.000) | 0.317 (0.117-0.533) | -0.533 (-0.750--0.317) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `openai:gpt-5.4-medium` | 60 | 9 | -0.003 (-0.097-0.062) | 0.000 (0.000-0.000) | -0.850 (-0.967--0.700) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:nvidia.nemotron-nano-9b-v2` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `openai:gpt-5.4-mini` | 60 | 9 | 0.000 (-0.083-0.075) | 0.000 (0.000-0.000) | -0.850 (-0.967--0.700) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:nvidia.nemotron-nano-9b-v2` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `openai:gpt-5.4-nano` | 60 | 9 | 0.035 (-0.011-0.089) | 0.000 (0.000-0.000) | -0.850 (-0.967--0.700) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:nvidia.nemotron-nano-9b-v2` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `openai:gpt-5.4-xhigh` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.150 (0.033-0.300) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `openai:gpt-5.5` | 60 | 0 | n/a | 0.883 (0.733-1.000) | 0.033 (-0.183-0.233) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `openai:gpt-5.5-high` | 60 | 9 | -0.028 (-0.113-0.050) | 0.017 (0.000-0.067) | -0.833 (-0.950--0.683) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:nvidia.nemotron-nano-9b-v2` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `openai:gpt-5.5-low` | 60 | 4 | -0.094 (-0.188-0.000) | 0.483 (0.267-0.700) | -0.367 (-0.617--0.100) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `openai:gpt-5.5-medium` | 60 | 8 | -0.047 (-0.141-0.000) | 0.050 (0.000-0.133) | -0.800 (-0.950--0.633) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `aws-bedrock:nvidia.nemotron-nano-9b-v2` if a tie-break is required. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-nano-9b-v2` | `openai:gpt-5.5-xhigh` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.150 (0.033-0.300) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-2.5-flash` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -0.600 (-0.750--0.433) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-2.5-flash-lite` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -0.983 (-1.000--0.933) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-3.1-pro-preview` | 60 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-3.1-pro-preview-high` | 60 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-3.1-pro-preview-low` | 60 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `google:gemini-3.1-pro-preview-medium` | 60 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `groq:llama-3.1-8b-instant` | 60 | 0 | n/a | -0.717 (-0.850--0.583) | -0.700 (-0.833--0.567) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `groq:openai/gpt-oss-120b` | 60 | 0 | n/a | -0.750 (-0.883--0.600) | -0.750 (-0.883--0.600) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4` | 60 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-high` | 60 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-low` | 60 | 0 | n/a | -0.683 (-0.883--0.467) | -0.683 (-0.883--0.467) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-medium` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-mini` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-nano` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.4-xhigh` | 60 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5` | 60 | 0 | n/a | -0.117 (-0.267-0.000) | -0.117 (-0.267-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5-high` | 60 | 0 | n/a | -0.983 (-1.000--0.933) | -0.983 (-1.000--0.933) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5-low` | 60 | 0 | n/a | -0.517 (-0.733--0.300) | -0.517 (-0.733--0.300) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5-medium` | 60 | 0 | n/a | -0.950 (-1.000--0.867) | -0.950 (-1.000--0.867) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `aws-bedrock:nvidia.nemotron-super-3-120b` | `openai:gpt-5.5-xhigh` | 60 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-2.5-flash` | `google:gemini-2.5-flash-lite` | 60 | 36 | -0.000 (-0.031-0.031) | 0.000 (0.000-0.000) | -0.383 (-0.533--0.233) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `slack_intake` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.600 (0.433-0.750) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview-high` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.600 (0.433-0.750) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview-low` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.600 (0.433-0.750) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-2.5-flash` | `google:gemini-3.1-pro-preview-medium` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.600 (0.433-0.750) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-2.5-flash` | `groq:llama-3.1-8b-instant` | 60 | 24 | 0.043 (0.006-0.087) | 0.283 (0.150-0.417) | -0.100 (-0.317-0.117) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `google:gemini-2.5-flash` | `groq:openai/gpt-oss-120b` | 60 | 26 | 0.018 (-0.021-0.053) | 0.250 (0.117-0.400) | -0.150 (-0.350-0.050) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `google:gemini-2.5-flash` | `openai:gpt-5.4` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.600 (0.433-0.750) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-2.5-flash` | `openai:gpt-5.4-high` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.600 (0.433-0.750) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-2.5-flash` | `openai:gpt-5.4-low` | 60 | 23 | -0.024 (-0.061-0.008) | 0.317 (0.117-0.533) | -0.083 (-0.367-0.183) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `google:gemini-2.5-flash` | `openai:gpt-5.4-medium` | 60 | 36 | -0.024 (-0.061-0.011) | 0.000 (0.000-0.000) | -0.400 (-0.567--0.250) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `slack_intake` | `google:gemini-2.5-flash` | `openai:gpt-5.4-mini` | 60 | 36 | -0.002 (-0.030-0.033) | 0.000 (0.000-0.000) | -0.400 (-0.567--0.250) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `slack_intake` | `google:gemini-2.5-flash` | `openai:gpt-5.4-nano` | 60 | 36 | -0.009 (-0.045-0.028) | 0.000 (0.000-0.000) | -0.400 (-0.567--0.250) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `slack_intake` | `google:gemini-2.5-flash` | `openai:gpt-5.4-xhigh` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.600 (0.433-0.750) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-2.5-flash` | `openai:gpt-5.5` | 60 | 4 | 0.000 (0.000-0.000) | 0.883 (0.733-1.000) | 0.483 (0.267-0.667) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `google:gemini-2.5-flash` | `openai:gpt-5.5-high` | 60 | 35 | -0.026 (-0.055-0.004) | 0.017 (0.000-0.067) | -0.383 (-0.550--0.217) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash` if a tie-break is required. |
| `slack_intake` | `google:gemini-2.5-flash` | `openai:gpt-5.5-low` | 60 | 20 | -0.055 (-0.099--0.011) | 0.483 (0.267-0.700) | 0.083 (-0.167-0.333) | tradeoff_quality_vs_ops: One model has higher semantic quality while the other is more operationally reliable. |
| `slack_intake` | `google:gemini-2.5-flash` | `openai:gpt-5.5-medium` | 60 | 34 | -0.045 (-0.076--0.020) | 0.050 (0.000-0.133) | -0.350 (-0.533--0.183) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `google:gemini-2.5-flash` | `openai:gpt-5.5-xhigh` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.600 (0.433-0.750) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `google:gemini-3.1-pro-preview` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `google:gemini-3.1-pro-preview-high` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `google:gemini-3.1-pro-preview-low` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `google:gemini-3.1-pro-preview-medium` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `groq:llama-3.1-8b-instant` | 60 | 42 | 0.045 (0.016-0.070) | 0.283 (0.150-0.417) | 0.283 (0.150-0.417) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `groq:openai/gpt-oss-120b` | 60 | 44 | 0.044 (0.010-0.075) | 0.250 (0.117-0.400) | 0.233 (0.100-0.383) | model_a_semantic_winner: Model A has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-high` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-low` | 60 | 40 | -0.002 (-0.041-0.035) | 0.317 (0.117-0.533) | 0.300 (0.100-0.517) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-medium` | 60 | 59 | -0.014 (-0.052-0.022) | 0.000 (0.000-0.000) | -0.017 (-0.067-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-mini` | 60 | 59 | 0.004 (-0.030-0.039) | 0.000 (0.000-0.000) | -0.017 (-0.067-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-nano` | 60 | 59 | -0.003 (-0.032-0.024) | 0.000 (0.000-0.000) | -0.017 (-0.067-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.4-xhigh` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5` | 60 | 7 | 0.036 (-0.125-0.125) | 0.883 (0.733-1.000) | 0.867 (0.700-1.000) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5-high` | 60 | 58 | -0.020 (-0.047-0.007) | 0.017 (0.000-0.067) | 0.000 (-0.067-0.067) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5-low` | 60 | 31 | -0.020 (-0.077-0.043) | 0.483 (0.267-0.700) | 0.467 (0.250-0.683) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5-medium` | 60 | 56 | -0.023 (-0.057-0.012) | 0.050 (0.000-0.133) | 0.033 (-0.050-0.133) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `google:gemini-2.5-flash-lite` if a tie-break is required. |
| `slack_intake` | `google:gemini-2.5-flash-lite` | `openai:gpt-5.5-xhigh` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 0.983 (0.933-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-high` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-low` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-medium` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview` | `groq:llama-3.1-8b-instant` | 60 | 0 | n/a | -0.717 (-0.850--0.583) | -0.700 (-0.833--0.567) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview` | `groq:openai/gpt-oss-120b` | 60 | 0 | n/a | -0.750 (-0.883--0.600) | -0.750 (-0.883--0.600) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-high` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-low` | 180 | 0 | n/a | -0.700 (-0.894--0.500) | -0.700 (-0.894--0.500) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-medium` | 180 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-mini` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-nano` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-xhigh` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5` | 180 | 0 | n/a | -0.117 (-0.267-0.000) | -0.117 (-0.267-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-high` | 180 | 0 | n/a | -0.983 (-1.000--0.956) | -0.983 (-1.000--0.956) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-low` | 180 | 0 | n/a | -0.522 (-0.750--0.311) | -0.522 (-0.750--0.311) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-medium` | 180 | 0 | n/a | -0.972 (-1.000--0.917) | -0.972 (-1.000--0.917) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-xhigh` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-low` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-medium` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-high` | `groq:llama-3.1-8b-instant` | 60 | 0 | n/a | -0.717 (-0.850--0.583) | -0.700 (-0.833--0.567) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-high` | `groq:openai/gpt-oss-120b` | 60 | 0 | n/a | -0.750 (-0.883--0.600) | -0.750 (-0.883--0.600) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-high` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-low` | 180 | 0 | n/a | -0.700 (-0.894--0.500) | -0.700 (-0.894--0.500) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-medium` | 180 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-mini` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-nano` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-xhigh` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5` | 180 | 0 | n/a | -0.117 (-0.267-0.000) | -0.117 (-0.267-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-high` | 180 | 0 | n/a | -0.983 (-1.000--0.956) | -0.983 (-1.000--0.956) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-low` | 180 | 0 | n/a | -0.522 (-0.750--0.311) | -0.522 (-0.750--0.311) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-medium` | 180 | 0 | n/a | -0.972 (-1.000--0.917) | -0.972 (-1.000--0.917) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-xhigh` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-low` | `google:gemini-3.1-pro-preview-medium` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-low` | `groq:llama-3.1-8b-instant` | 60 | 0 | n/a | -0.717 (-0.850--0.583) | -0.700 (-0.833--0.567) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-low` | `groq:openai/gpt-oss-120b` | 60 | 0 | n/a | -0.750 (-0.883--0.600) | -0.750 (-0.883--0.600) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-high` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-low` | 180 | 0 | n/a | -0.700 (-0.894--0.500) | -0.700 (-0.894--0.500) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-medium` | 180 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-mini` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-nano` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-xhigh` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5` | 180 | 0 | n/a | -0.117 (-0.267-0.000) | -0.117 (-0.267-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-high` | 180 | 0 | n/a | -0.983 (-1.000--0.956) | -0.983 (-1.000--0.956) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-low` | 180 | 0 | n/a | -0.522 (-0.750--0.311) | -0.522 (-0.750--0.311) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-medium` | 180 | 0 | n/a | -0.972 (-1.000--0.917) | -0.972 (-1.000--0.917) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-xhigh` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-medium` | `groq:llama-3.1-8b-instant` | 60 | 0 | n/a | -0.717 (-0.850--0.583) | -0.700 (-0.833--0.567) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-medium` | `groq:openai/gpt-oss-120b` | 60 | 0 | n/a | -0.750 (-0.883--0.600) | -0.750 (-0.883--0.600) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-high` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-low` | 180 | 0 | n/a | -0.700 (-0.894--0.500) | -0.700 (-0.894--0.500) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-medium` | 180 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-mini` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-nano` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-xhigh` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5` | 180 | 0 | n/a | -0.117 (-0.267-0.000) | -0.117 (-0.267-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-high` | 180 | 0 | n/a | -0.983 (-1.000--0.956) | -0.983 (-1.000--0.956) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-low` | 180 | 0 | n/a | -0.522 (-0.750--0.311) | -0.522 (-0.750--0.311) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-medium` | 180 | 0 | n/a | -0.972 (-1.000--0.917) | -0.972 (-1.000--0.917) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-xhigh` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `groq:llama-3.1-8b-instant` | `groq:openai/gpt-oss-120b` | 60 | 32 | -0.007 (-0.045-0.027) | -0.033 (-0.217-0.150) | -0.050 (-0.233-0.133) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:llama-3.1-8b-instant` if a tie-break is required. |
| `slack_intake` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.4` | 60 | 0 | n/a | 0.717 (0.583-0.850) | 0.700 (0.567-0.833) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.4-high` | 60 | 0 | n/a | 0.717 (0.583-0.850) | 0.700 (0.567-0.833) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.4-low` | 60 | 28 | -0.053 (-0.091--0.016) | 0.033 (-0.200-0.283) | 0.017 (-0.217-0.267) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.4-medium` | 60 | 42 | -0.063 (-0.102--0.027) | -0.283 (-0.417--0.150) | -0.300 (-0.433--0.167) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.4-mini` | 60 | 42 | -0.048 (-0.080--0.016) | -0.283 (-0.417--0.150) | -0.300 (-0.433--0.167) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.4-nano` | 60 | 42 | -0.058 (-0.087--0.031) | -0.283 (-0.417--0.150) | -0.300 (-0.433--0.167) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.4-xhigh` | 60 | 0 | n/a | 0.717 (0.583-0.850) | 0.700 (0.567-0.833) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.5` | 60 | 5 | -0.017 (-0.125-0.069) | 0.600 (0.383-0.783) | 0.583 (0.367-0.767) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.5-high` | 60 | 42 | -0.063 (-0.095--0.031) | -0.267 (-0.400--0.133) | -0.283 (-0.417--0.150) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.5-low` | 60 | 22 | -0.075 (-0.131--0.014) | 0.200 (-0.050-0.450) | 0.183 (-0.067-0.417) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.5-medium` | 60 | 39 | -0.069 (-0.110--0.032) | -0.233 (-0.400--0.067) | -0.250 (-0.417--0.083) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `groq:llama-3.1-8b-instant` | `openai:gpt-5.5-xhigh` | 60 | 0 | n/a | 0.717 (0.583-0.850) | 0.700 (0.567-0.833) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4` | 60 | 0 | n/a | 0.750 (0.600-0.883) | 0.750 (0.600-0.883) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-high` | 60 | 0 | n/a | 0.750 (0.600-0.883) | 0.750 (0.600-0.883) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-low` | 60 | 30 | -0.036 (-0.073-0.007) | 0.067 (-0.183-0.317) | 0.067 (-0.183-0.317) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:openai/gpt-oss-120b` if a tie-break is required. |
| `slack_intake` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-medium` | 60 | 45 | -0.070 (-0.105--0.037) | -0.250 (-0.400--0.117) | -0.250 (-0.400--0.117) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-mini` | 60 | 45 | -0.038 (-0.069--0.001) | -0.250 (-0.400--0.117) | -0.250 (-0.400--0.117) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-nano` | 60 | 45 | -0.051 (-0.076--0.024) | -0.250 (-0.400--0.117) | -0.250 (-0.400--0.117) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.4-xhigh` | 60 | 0 | n/a | 0.750 (0.600-0.883) | 0.750 (0.600-0.883) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5` | 60 | 6 | 0.000 (-0.125-0.175) | 0.633 (0.433-0.800) | 0.633 (0.433-0.800) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5-high` | 60 | 45 | -0.066 (-0.100--0.027) | -0.233 (-0.367--0.117) | -0.233 (-0.367--0.117) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5-low` | 60 | 22 | -0.045 (-0.102-0.028) | 0.233 (-0.033-0.500) | 0.233 (-0.033-0.500) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `groq:openai/gpt-oss-120b` if a tie-break is required. |
| `slack_intake` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5-medium` | 60 | 43 | -0.064 (-0.101--0.024) | -0.200 (-0.367--0.033) | -0.200 (-0.367--0.033) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `groq:openai/gpt-oss-120b` | `openai:gpt-5.5-xhigh` | 60 | 0 | n/a | 0.750 (0.600-0.883) | 0.750 (0.600-0.883) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4` | `openai:gpt-5.4-high` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4` | `openai:gpt-5.4-low` | 180 | 0 | n/a | -0.700 (-0.894--0.500) | -0.700 (-0.894--0.500) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4` | `openai:gpt-5.4-medium` | 180 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4` | `openai:gpt-5.4-mini` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4` | `openai:gpt-5.4-nano` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4` | `openai:gpt-5.4-xhigh` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4` | `openai:gpt-5.5` | 180 | 0 | n/a | -0.117 (-0.267-0.000) | -0.117 (-0.267-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4` | `openai:gpt-5.5-high` | 180 | 0 | n/a | -0.983 (-1.000--0.956) | -0.983 (-1.000--0.956) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4` | `openai:gpt-5.5-low` | 180 | 0 | n/a | -0.522 (-0.750--0.311) | -0.522 (-0.750--0.311) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4` | `openai:gpt-5.5-medium` | 180 | 0 | n/a | -0.972 (-1.000--0.917) | -0.972 (-1.000--0.917) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4` | `openai:gpt-5.5-xhigh` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-high` | `openai:gpt-5.4-low` | 180 | 0 | n/a | -0.700 (-0.894--0.500) | -0.700 (-0.894--0.500) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-high` | `openai:gpt-5.4-medium` | 180 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-high` | `openai:gpt-5.4-mini` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-high` | `openai:gpt-5.4-nano` | 60 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-high` | `openai:gpt-5.4-xhigh` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-high` | `openai:gpt-5.5` | 180 | 0 | n/a | -0.117 (-0.267-0.000) | -0.117 (-0.267-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-high` | `openai:gpt-5.5-high` | 180 | 0 | n/a | -0.983 (-1.000--0.956) | -0.983 (-1.000--0.956) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-high` | `openai:gpt-5.5-low` | 180 | 0 | n/a | -0.522 (-0.750--0.311) | -0.522 (-0.750--0.311) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-high` | `openai:gpt-5.5-medium` | 180 | 0 | n/a | -0.972 (-1.000--0.917) | -0.972 (-1.000--0.917) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-high` | `openai:gpt-5.5-xhigh` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-low` | `openai:gpt-5.4-medium` | 180 | 126 | -0.006 (-0.024-0.013) | -0.300 (-0.500--0.106) | -0.300 (-0.500--0.106) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.4-low` | `openai:gpt-5.4-mini` | 60 | 41 | 0.005 (-0.019-0.031) | -0.317 (-0.517--0.133) | -0.317 (-0.517--0.133) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.4-low` | `openai:gpt-5.4-nano` | 60 | 41 | -0.004 (-0.035-0.022) | -0.317 (-0.517--0.133) | -0.317 (-0.517--0.133) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.4-low` | `openai:gpt-5.4-xhigh` | 180 | 0 | n/a | 0.700 (0.500-0.894) | 0.700 (0.500-0.894) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-low` | `openai:gpt-5.5` | 180 | 21 | -0.016 (-0.043-0.019) | 0.583 (0.372-0.783) | 0.583 (0.372-0.783) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.4-low` | `openai:gpt-5.5-high` | 180 | 123 | -0.006 (-0.024-0.013) | -0.283 (-0.494--0.083) | -0.283 (-0.494--0.083) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.4-low` | `openai:gpt-5.5-low` | 180 | 94 | -0.014 (-0.039-0.011) | 0.178 (0.033-0.344) | 0.178 (0.033-0.344) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.4-low` | `openai:gpt-5.5-medium` | 180 | 126 | -0.007 (-0.027-0.012) | -0.272 (-0.467--0.100) | -0.272 (-0.467--0.100) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.4-low` | `openai:gpt-5.5-xhigh` | 180 | 0 | n/a | 0.700 (0.500-0.894) | 0.700 (0.500-0.894) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-mini` | 60 | 60 | 0.019 (-0.005-0.044) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `slack_intake` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-nano` | 60 | 60 | 0.013 (-0.020-0.049) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `slack_intake` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-xhigh` | 180 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-medium` | `openai:gpt-5.5` | 180 | 21 | -0.010 (-0.039-0.028) | 0.883 (0.733-1.000) | 0.883 (0.733-1.000) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-high` | 180 | 177 | -0.007 (-0.024-0.009) | 0.017 (0.000-0.044) | 0.017 (0.000-0.044) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-medium` if a tie-break is required. |
| `slack_intake` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-low` | 180 | 94 | 0.003 (-0.019-0.023) | 0.478 (0.250-0.689) | 0.478 (0.250-0.689) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-medium` | 180 | 175 | -0.013 (-0.030-0.002) | 0.028 (0.000-0.083) | 0.028 (0.000-0.083) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-medium` if a tie-break is required. |
| `slack_intake` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-xhigh` | 180 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-mini` | `openai:gpt-5.4-nano` | 60 | 60 | -0.006 (-0.034-0.022) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `slack_intake` | `openai:gpt-5.4-mini` | `openai:gpt-5.4-xhigh` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-mini` | `openai:gpt-5.5` | 60 | 7 | -0.012 (-0.037-0.000) | 0.883 (0.733-1.000) | 0.883 (0.733-1.000) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-high` | 60 | 59 | -0.024 (-0.046--0.003) | 0.017 (0.000-0.067) | 0.017 (0.000-0.067) | model_b_semantic_winner: Model B has a higher semantic score on shared semantically evaluable variants. |
| `slack_intake` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-low` | 60 | 31 | -0.015 (-0.044-0.010) | 0.483 (0.267-0.700) | 0.483 (0.267-0.700) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-medium` | 60 | 57 | -0.023 (-0.048-0.000) | 0.050 (0.000-0.133) | 0.050 (0.000-0.133) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-mini` if a tie-break is required. |
| `slack_intake` | `openai:gpt-5.4-mini` | `openai:gpt-5.5-xhigh` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-nano` | `openai:gpt-5.4-xhigh` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-nano` | `openai:gpt-5.5` | 60 | 7 | 0.036 (-0.125-0.167) | 0.883 (0.733-1.000) | 0.883 (0.733-1.000) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.4-nano` | `openai:gpt-5.5-high` | 60 | 59 | -0.018 (-0.049-0.013) | 0.017 (0.000-0.067) | 0.017 (0.000-0.067) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `slack_intake` | `openai:gpt-5.4-nano` | `openai:gpt-5.5-low` | 60 | 31 | -0.010 (-0.059-0.045) | 0.483 (0.267-0.700) | 0.483 (0.267-0.700) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.4-nano` | `openai:gpt-5.5-medium` | 60 | 57 | -0.018 (-0.056-0.017) | 0.050 (0.000-0.133) | 0.050 (0.000-0.133) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.4-nano` if a tie-break is required. |
| `slack_intake` | `openai:gpt-5.4-nano` | `openai:gpt-5.5-xhigh` | 60 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5` | 180 | 0 | n/a | -0.117 (-0.267-0.000) | -0.117 (-0.267-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-high` | 180 | 0 | n/a | -0.983 (-1.000--0.956) | -0.983 (-1.000--0.956) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-low` | 180 | 0 | n/a | -0.522 (-0.750--0.311) | -0.522 (-0.750--0.311) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-medium` | 180 | 0 | n/a | -0.972 (-1.000--0.917) | -0.972 (-1.000--0.917) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-xhigh` | 180 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.5` | `openai:gpt-5.5-high` | 180 | 21 | 0.010 (-0.012-0.032) | -0.867 (-0.983--0.717) | -0.867 (-0.983--0.717) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.5` | `openai:gpt-5.5-low` | 180 | 21 | 0.006 (-0.033-0.036) | -0.406 (-0.611--0.206) | -0.406 (-0.611--0.206) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.5` | `openai:gpt-5.5-medium` | 180 | 21 | 0.000 (-0.042-0.042) | -0.856 (-0.978--0.706) | -0.856 (-0.978--0.706) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.5` | `openai:gpt-5.5-xhigh` | 180 | 0 | n/a | 0.117 (0.000-0.267) | 0.117 (0.000-0.267) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.5-high` | `openai:gpt-5.5-low` | 180 | 92 | -0.002 (-0.024-0.018) | 0.461 (0.239-0.678) | 0.461 (0.239-0.678) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.5-high` | `openai:gpt-5.5-medium` | 180 | 172 | -0.007 (-0.019-0.004) | 0.011 (-0.033-0.072) | 0.011 (-0.033-0.072) | choose_cheaper: No clear decision signal remained after pairwise comparison; choose `openai:gpt-5.5-medium` if a tie-break is required. |
| `slack_intake` | `openai:gpt-5.5-high` | `openai:gpt-5.5-xhigh` | 180 | 0 | n/a | 0.983 (0.956-1.000) | 0.983 (0.956-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.5-low` | `openai:gpt-5.5-medium` | 180 | 94 | -0.001 (-0.018-0.017) | -0.450 (-0.650--0.250) | -0.450 (-0.650--0.250) | operational_winner_not_quality_winner: Operational reliability differs, but semantic quality does not clearly separate the models. |
| `slack_intake` | `openai:gpt-5.5-low` | `openai:gpt-5.5-xhigh` | 180 | 0 | n/a | 0.522 (0.311-0.750) | 0.522 (0.311-0.750) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `slack_intake` | `openai:gpt-5.5-medium` | `openai:gpt-5.5-xhigh` | 180 | 0 | n/a | 0.972 (0.917-1.000) | 0.972 (0.917-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-high` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-low` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview` | `google:gemini-3.1-pro-preview-medium` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-high` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-low` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-medium` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.4-xhigh` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5` | 90 | 0 | n/a | -0.989 (-1.000--0.956) | -0.989 (-1.000--0.956) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-high` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-low` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-medium` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview` | `openai:gpt-5.5-xhigh` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-low` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-high` | `google:gemini-3.1-pro-preview-medium` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-high` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-low` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-medium` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.4-xhigh` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5` | 90 | 0 | n/a | -0.989 (-1.000--0.956) | -0.989 (-1.000--0.956) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-high` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-low` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-medium` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-high` | `openai:gpt-5.5-xhigh` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-low` | `google:gemini-3.1-pro-preview-medium` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-high` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-low` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-medium` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.4-xhigh` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5` | 90 | 0 | n/a | -0.989 (-1.000--0.956) | -0.989 (-1.000--0.956) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-high` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-low` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-medium` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-low` | `openai:gpt-5.5-xhigh` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-high` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-low` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-medium` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.4-xhigh` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5` | 90 | 0 | n/a | -0.989 (-1.000--0.956) | -0.989 (-1.000--0.956) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-high` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-low` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-medium` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `google:gemini-3.1-pro-preview-medium` | `openai:gpt-5.5-xhigh` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4` | `openai:gpt-5.4-high` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4` | `openai:gpt-5.4-low` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4` | `openai:gpt-5.4-medium` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4` | `openai:gpt-5.4-xhigh` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4` | `openai:gpt-5.5` | 90 | 0 | n/a | -0.989 (-1.000--0.956) | -0.989 (-1.000--0.956) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4` | `openai:gpt-5.5-high` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4` | `openai:gpt-5.5-low` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4` | `openai:gpt-5.5-medium` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4` | `openai:gpt-5.5-xhigh` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4-high` | `openai:gpt-5.4-low` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4-high` | `openai:gpt-5.4-medium` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4-high` | `openai:gpt-5.4-xhigh` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4-high` | `openai:gpt-5.5` | 90 | 0 | n/a | -0.989 (-1.000--0.956) | -0.989 (-1.000--0.956) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4-high` | `openai:gpt-5.5-high` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4-high` | `openai:gpt-5.5-low` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4-high` | `openai:gpt-5.5-medium` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4-high` | `openai:gpt-5.5-xhigh` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4-low` | `openai:gpt-5.4-medium` | 90 | 90 | -0.006 (-0.033-0.020) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-medium` on cost. |
| `validator_critic` | `openai:gpt-5.4-low` | `openai:gpt-5.4-xhigh` | 90 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4-low` | `openai:gpt-5.5` | 90 | 89 | 0.009 (-0.007-0.028) | 0.011 (0.000-0.044) | 0.011 (0.000-0.044) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-low` on cost. |
| `validator_critic` | `openai:gpt-5.4-low` | `openai:gpt-5.5-high` | 90 | 90 | -0.000 (-0.018-0.019) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-low` on cost. |
| `validator_critic` | `openai:gpt-5.4-low` | `openai:gpt-5.5-low` | 90 | 90 | -0.003 (-0.026-0.018) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-low` on cost. |
| `validator_critic` | `openai:gpt-5.4-low` | `openai:gpt-5.5-medium` | 90 | 90 | 0.004 (-0.008-0.022) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-low` on cost. |
| `validator_critic` | `openai:gpt-5.4-low` | `openai:gpt-5.5-xhigh` | 90 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4-medium` | `openai:gpt-5.4-xhigh` | 90 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4-medium` | `openai:gpt-5.5` | 90 | 89 | 0.015 (-0.021-0.054) | 0.011 (0.000-0.044) | 0.011 (0.000-0.044) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-medium` on cost. |
| `validator_critic` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-high` | 90 | 90 | 0.006 (-0.029-0.042) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-medium` on cost. |
| `validator_critic` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-low` | 90 | 90 | 0.003 (-0.038-0.043) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-medium` on cost. |
| `validator_critic` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-medium` | 90 | 90 | 0.010 (-0.020-0.046) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.4-medium` on cost. |
| `validator_critic` | `openai:gpt-5.4-medium` | `openai:gpt-5.5-xhigh` | 90 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5` | 90 | 0 | n/a | -0.989 (-1.000--0.956) | -0.989 (-1.000--0.956) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-high` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-low` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-medium` | 90 | 0 | n/a | -1.000 (-1.000--1.000) | -1.000 (-1.000--1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.4-xhigh` | `openai:gpt-5.5-xhigh` | 90 | 0 | n/a | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.5` | `openai:gpt-5.5-high` | 90 | 89 | -0.010 (-0.027-0.005) | -0.011 (-0.056-0.000) | -0.011 (-0.056-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5` on cost. |
| `validator_critic` | `openai:gpt-5.5` | `openai:gpt-5.5-low` | 90 | 89 | -0.013 (-0.028-0.001) | -0.011 (-0.056-0.000) | -0.011 (-0.056-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5` on cost. |
| `validator_critic` | `openai:gpt-5.5` | `openai:gpt-5.5-medium` | 90 | 89 | -0.005 (-0.019-0.009) | -0.011 (-0.056-0.000) | -0.011 (-0.056-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5-medium` on cost. |
| `validator_critic` | `openai:gpt-5.5` | `openai:gpt-5.5-xhigh` | 90 | 0 | n/a | 0.989 (0.944-1.000) | 0.989 (0.944-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.5-high` | `openai:gpt-5.5-low` | 90 | 90 | -0.003 (-0.019-0.013) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5-low` on cost. |
| `validator_critic` | `openai:gpt-5.5-high` | `openai:gpt-5.5-medium` | 90 | 90 | 0.005 (-0.009-0.019) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5-medium` on cost. |
| `validator_critic` | `openai:gpt-5.5-high` | `openai:gpt-5.5-xhigh` | 90 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.5-low` | `openai:gpt-5.5-medium` | 90 | 90 | 0.008 (-0.009-0.026) | 0.000 (0.000-0.000) | 0.000 (0.000-0.000) | choose_cheaper: Semantic quality is statistically indistinguishable; choose `openai:gpt-5.5-medium` on cost. |
| `validator_critic` | `openai:gpt-5.5-low` | `openai:gpt-5.5-xhigh` | 90 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |
| `validator_critic` | `openai:gpt-5.5-medium` | `openai:gpt-5.5-xhigh` | 90 | 0 | n/a | 1.000 (1.000-1.000) | 1.000 (1.000-1.000) | insufficient_semantic_overlap: No shared variants were semantically evaluable for both models. |

## Cost and latency

| Model | Role | Cost / 1k successful | p50 ms | p90 ms | p95 ms |
|---|---|---:|---:|---:|---:|
| `anthropic:claude-haiku-4-5` | `conflict_classifier` | $3.2349 | 4537 | 5460 | 5624 |
| `anthropic:claude-haiku-4-5-20251001` | `conflict_classifier` | $3.2025 | 4513 | 5452 | 5536 |
| `anthropic:claude-haiku-4-5-20251001` | `entity_resolution` | $2.5906 | 3917 | 4780 | 5370 |
| `anthropic:claude-haiku-4-5-20251001` | `recall_synthesizer` | $2.8203 | 4142 | 5366 | 5752 |
| `anthropic:claude-opus-4-7` | `eval_judge` | n/a | 0 | 0 | 0 |
| `anthropic:claude-sonnet-4-6` | `conflict_classifier` | $11.7824 | 11574 | 14294 | 14306 |
| `anthropic:claude-sonnet-4-6` | `eval_judge` | $12.1342 | 13011 | 16374 | 16374 |
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
| `google:gemini-2.5-flash-lite` | `router` | $0.1249 | 1899 | 2294 | 3036 |
| `google:gemini-2.5-flash-lite` | `slack_intake` | $0.1431 | 8259 | 17748 | 21019 |
| `google:gemini-2.5-pro` | `conflict_classifier` | $3.1159 | 13940 | 16631 | 16981 |
| `google:gemini-3.1-pro-preview` | `conflict_classifier` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview` | `debug_explainer` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview` | `entity_resolution` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview` | `eval_judge` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview` | `memory_compiler` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview` | `recall_synthesizer` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview` | `router` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview` | `slack_intake` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview` | `validator_critic` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-high` | `conflict_classifier` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-high` | `debug_explainer` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-high` | `entity_resolution` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-high` | `eval_judge` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-high` | `memory_compiler` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-high` | `recall_synthesizer` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-high` | `router` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-high` | `slack_intake` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-high` | `validator_critic` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-low` | `conflict_classifier` | $20.1756 | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-low` | `debug_explainer` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-low` | `entity_resolution` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-low` | `eval_judge` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-low` | `memory_compiler` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-low` | `recall_synthesizer` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-low` | `router` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-low` | `slack_intake` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-low` | `validator_critic` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-medium` | `conflict_classifier` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-medium` | `debug_explainer` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-medium` | `entity_resolution` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-medium` | `eval_judge` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-medium` | `memory_compiler` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-medium` | `recall_synthesizer` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-medium` | `router` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-medium` | `slack_intake` | n/a | n/a | n/a | n/a |
| `google:gemini-3.1-pro-preview-medium` | `validator_critic` | n/a | n/a | n/a | n/a |
| `groq:llama-3.1-8b-instant` | `router` | $0.0433 | 1600 | 7599 | 7864 |
| `groq:llama-3.1-8b-instant` | `slack_intake` | $0.0487 | 3841 | 7880 | 8016 |
| `groq:llama-3.3-70b-versatile` | `memory_compiler` | $0.6016 | 2473 | 7579 | 8209 |
| `groq:llama-3.3-70b-versatile` | `recall_synthesizer` | $0.5128 | 4067 | 4393 | 4435 |
| `groq:openai/gpt-oss-120b` | `conflict_classifier` | $0.2508 | 7495 | 8912 | 9125 |
| `groq:openai/gpt-oss-120b` | `memory_compiler` | $0.2428 | 8952 | 9799 | 9928 |
| `groq:openai/gpt-oss-120b` | `recall_synthesizer` | $0.2361 | 7583 | 9387 | 9449 |
| `groq:openai/gpt-oss-120b` | `slack_intake` | $0.1793 | 7561 | 9132 | 9205 |
| `openai:gpt-5-nano` | `router` | $0.1645 | 4667 | 4814 | 5288 |
| `openai:gpt-5.4` | `conflict_classifier` | $6.7228 | n/a | n/a | n/a |
| `openai:gpt-5.4` | `debug_explainer` | $14.1517 | n/a | n/a | n/a |
| `openai:gpt-5.4` | `entity_resolution` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4` | `eval_judge` | $6.8731 | 5927 | 6854 | 6854 |
| `openai:gpt-5.4` | `memory_compiler` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4` | `recall_synthesizer` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4` | `router` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4` | `slack_intake` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4` | `validator_critic` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-high` | `conflict_classifier` | $6.9493 | n/a | n/a | n/a |
| `openai:gpt-5.4-high` | `debug_explainer` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-high` | `entity_resolution` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-high` | `eval_judge` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-high` | `memory_compiler` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-high` | `recall_synthesizer` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-high` | `router` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-high` | `slack_intake` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-high` | `validator_critic` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-low` | `conflict_classifier` | $7.2239 | n/a | n/a | n/a |
| `openai:gpt-5.4-low` | `debug_explainer` | $6.3331 | n/a | n/a | n/a |
| `openai:gpt-5.4-low` | `entity_resolution` | $5.2311 | n/a | n/a | n/a |
| `openai:gpt-5.4-low` | `eval_judge` | $5.1123 | n/a | n/a | n/a |
| `openai:gpt-5.4-low` | `memory_compiler` | $8.8030 | n/a | n/a | n/a |
| `openai:gpt-5.4-low` | `recall_synthesizer` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-low` | `router` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-low` | `slack_intake` | $5.3010 | n/a | n/a | n/a |
| `openai:gpt-5.4-low` | `validator_critic` | $5.5274 | n/a | n/a | n/a |
| `openai:gpt-5.4-medium` | `conflict_classifier` | $6.9886 | n/a | n/a | n/a |
| `openai:gpt-5.4-medium` | `debug_explainer` | $6.3164 | n/a | n/a | n/a |
| `openai:gpt-5.4-medium` | `entity_resolution` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-medium` | `eval_judge` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-medium` | `memory_compiler` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-medium` | `recall_synthesizer` | $6.4218 | n/a | n/a | n/a |
| `openai:gpt-5.4-medium` | `router` | $4.7692 | n/a | n/a | n/a |
| `openai:gpt-5.4-medium` | `slack_intake` | $4.9443 | n/a | n/a | n/a |
| `openai:gpt-5.4-medium` | `validator_critic` | $5.4581 | n/a | n/a | n/a |
| `openai:gpt-5.4-mini` | `conflict_classifier` | $1.8912 | 3724 | 4953 | 15818 |
| `openai:gpt-5.4-mini` | `entity_resolution` | $1.5093 | 3614 | 4287 | 6560 |
| `openai:gpt-5.4-mini` | `memory_compiler` | $2.1893 | 3704 | 6825 | 18112 |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | $1.6844 | 2910 | 4579 | 4644 |
| `openai:gpt-5.4-mini` | `slack_intake` | $1.5414 | 3396 | 4460 | 5064 |
| `openai:gpt-5.4-nano` | `entity_resolution` | $0.5562 | 4167 | 5084 | 5246 |
| `openai:gpt-5.4-nano` | `memory_compiler` | $0.8306 | 4750 | 6773 | 7979 |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | $0.5295 | 3370 | 6437 | 9003 |
| `openai:gpt-5.4-nano` | `slack_intake` | $0.5141 | 3803 | 4697 | 5106 |
| `openai:gpt-5.4-xhigh` | `conflict_classifier` | $14.4225 | n/a | n/a | n/a |
| `openai:gpt-5.4-xhigh` | `debug_explainer` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-xhigh` | `entity_resolution` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-xhigh` | `eval_judge` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-xhigh` | `memory_compiler` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-xhigh` | `recall_synthesizer` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-xhigh` | `router` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-xhigh` | `slack_intake` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.4-xhigh` | `validator_critic` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.5` | `conflict_classifier` | $11.0984 | n/a | n/a | n/a |
| `openai:gpt-5.5` | `debug_explainer` | $11.6213 | n/a | n/a | n/a |
| `openai:gpt-5.5` | `entity_resolution` | $8.7744 | n/a | n/a | n/a |
| `openai:gpt-5.5` | `eval_judge` | $8.4554 | n/a | n/a | n/a |
| `openai:gpt-5.5` | `memory_compiler` | $15.1492 | n/a | n/a | n/a |
| `openai:gpt-5.5` | `recall_synthesizer` | $15.4991 | n/a | n/a | n/a |
| `openai:gpt-5.5` | `router` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.5` | `slack_intake` | $22.8471 | n/a | n/a | n/a |
| `openai:gpt-5.5` | `validator_critic` | $9.2334 | n/a | n/a | n/a |
| `openai:gpt-5.5-high` | `conflict_classifier` | $12.6810 | n/a | n/a | n/a |
| `openai:gpt-5.5-high` | `debug_explainer` | $11.3412 | n/a | n/a | n/a |
| `openai:gpt-5.5-high` | `entity_resolution` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.5-high` | `eval_judge` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.5-high` | `memory_compiler` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.5-high` | `recall_synthesizer` | $10.5194 | n/a | n/a | n/a |
| `openai:gpt-5.5-high` | `router` | $7.6700 | n/a | n/a | n/a |
| `openai:gpt-5.5-high` | `slack_intake` | $9.3154 | n/a | n/a | n/a |
| `openai:gpt-5.5-high` | `validator_critic` | $9.4372 | n/a | n/a | n/a |
| `openai:gpt-5.5-low` | `conflict_classifier` | $11.3332 | n/a | n/a | n/a |
| `openai:gpt-5.5-low` | `debug_explainer` | $10.8439 | n/a | n/a | n/a |
| `openai:gpt-5.5-low` | `entity_resolution` | $8.8467 | n/a | n/a | n/a |
| `openai:gpt-5.5-low` | `eval_judge` | $8.5762 | n/a | n/a | n/a |
| `openai:gpt-5.5-low` | `memory_compiler` | $16.1686 | n/a | n/a | n/a |
| `openai:gpt-5.5-low` | `recall_synthesizer` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.5-low` | `router` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.5-low` | `slack_intake` | $10.7263 | n/a | n/a | n/a |
| `openai:gpt-5.5-low` | `validator_critic` | $9.3648 | n/a | n/a | n/a |
| `openai:gpt-5.5-medium` | `conflict_classifier` | $12.0052 | n/a | n/a | n/a |
| `openai:gpt-5.5-medium` | `debug_explainer` | $10.8250 | n/a | n/a | n/a |
| `openai:gpt-5.5-medium` | `entity_resolution` | $8.6489 | n/a | n/a | n/a |
| `openai:gpt-5.5-medium` | `eval_judge` | $8.5563 | n/a | n/a | n/a |
| `openai:gpt-5.5-medium` | `memory_compiler` | $34.3768 | n/a | n/a | n/a |
| `openai:gpt-5.5-medium` | `recall_synthesizer` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.5-medium` | `router` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.5-medium` | `slack_intake` | $9.0081 | n/a | n/a | n/a |
| `openai:gpt-5.5-medium` | `validator_critic` | $9.2268 | n/a | n/a | n/a |
| `openai:gpt-5.5-xhigh` | `conflict_classifier` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.5-xhigh` | `debug_explainer` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.5-xhigh` | `entity_resolution` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.5-xhigh` | `eval_judge` | $12.2087 | 11936 | 20309 | 20309 |
| `openai:gpt-5.5-xhigh` | `memory_compiler` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.5-xhigh` | `recall_synthesizer` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.5-xhigh` | `router` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.5-xhigh` | `slack_intake` | n/a | n/a | n/a | n/a |
| `openai:gpt-5.5-xhigh` | `validator_critic` | n/a | n/a | n/a | n/a |
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
- `conflict_classifier`: conflict_safety_below_threshold (17), operational_success_below_threshold (22), schema_validity_below_threshold (22), semantic_score_below_threshold (17), semantic_score_not_evaluated (5), zero_tolerance_failures_present (17)
- `embeddings`: operational_success_below_threshold (3)
- `memory_compiler`: memory_card_extraction_below_threshold (11), operational_success_below_threshold (21), schema_validity_below_threshold (22), semantic_score_below_threshold (11), semantic_score_not_evaluated (11), source_memory_split_below_threshold (3), zero_tolerance_failures_present (11)
- `recall_synthesizer`: groundedness_below_threshold (10), operational_success_below_threshold (22), schema_validity_below_threshold (22), semantic_score_below_threshold (8), semantic_score_not_evaluated (12), zero_tolerance_failures_present (5)
- `router`: operational_success_below_threshold (17), schema_validity_below_threshold (17), semantic_score_below_threshold (5), semantic_score_not_evaluated (12)
- `slack_intake`: decision_correctness_below_threshold (14), operational_success_below_threshold (21), repair_option_usefulness_below_threshold (14), schema_validity_below_threshold (23), semantic_score_below_threshold (14), semantic_score_not_evaluated (9), zero_tolerance_failures_present (12)

## Next actions

- Restore mandatory coverage for: conflict_classifier, embeddings, memory_compiler, recall_synthesizer, router, slack_intake.
- Eliminate the largest blocking failure classes first: quota_error (6062), quality_failure (2713), zero_tolerance_failure (1176).
- Rerun after operational issues are fixed so semantic comparisons are based on overlapping evaluable variants.
- Add or refine role-specific fixtures if a mandatory role remains unevaluable after provider issues are resolved.
