# Fine-Grained Eval Live Status

Updated: `2026-05-07 23:07:27 BST`
Expected end: `2026-05-07 23:07:29 BST (0 min remaining at 1060892.2 tests/min)`

Raw dir: `/Volumes/xpg_usb4/sandbox/git/brain/eval_runs/fine_grained_20260507_140116/raw/eval_20260507_130116`

| Model family | Quota / All fail / Seen / Total |
|---|---:|
| `anthropic` | `0 / 0 / 486 / 774` |
| `aws-bedrock` | `0 / 12 / 504 / 2871` |
| `google` | `0 / 102 / 549 / 4437` |
| `openai` | `0 / 20 / 2036 / 9423` |
| `openrouter` | `0 / 0 / 0 / 17064` |

## Preliminary model/role feasibility

| Model | Role | Feasibility | Seen / Total | Ok | Schema | Fail |
|---|---|---|---:|---:|---:|---:|
| `aws-bedrock:mistral.ministral-3-14b-instruct` | `atomic_card_extractor` | pending | 0 / 135 | 0 | 0 | 0 |
| `google:gemini-2.5-flash-lite` | `atomic_card_extractor` | pending | 0 / 135 | 0 | 0 | 0 |
| `openai:gpt-5.4-mini` | `atomic_card_extractor` | pending | 0 / 135 | 0 | 0 | 0 |
| `openai:gpt-5.4-nano` | `atomic_card_extractor` | pending | 0 / 135 | 0 | 0 | 0 |
| `openai:gpt-5.5-high` | `atomic_card_extractor` | pending | 0 / 135 | 0 | 0 | 0 |
| `openrouter:google/gemma-3n-e4b-it` | `atomic_card_extractor` | pending | 0 / 135 | 0 | 0 | 0 |
| `openrouter:google/gemma-4-31b-it-fp8` | `atomic_card_extractor` | pending | 0 / 135 | 0 | 0 | 0 |
| `openrouter:qwen/qwen3.5-27b-fp8` | `atomic_card_extractor` | pending | 0 / 135 | 0 | 0 | 0 |
| `openrouter:qwen/qwen3.5-9b-fp8` | `atomic_card_extractor` | pending | 0 / 135 | 0 | 0 | 0 |
| `aws-bedrock:mistral.ministral-3-14b-instruct` | `conflict_candidate_detector` | pending | 0 / 99 | 0 | 0 | 0 |
| `google:gemini-2.5-flash-lite` | `conflict_candidate_detector` | pending | 0 / 99 | 0 | 0 | 0 |
| `openai:gpt-5.4-mini` | `conflict_candidate_detector` | pending | 0 / 99 | 0 | 0 | 0 |
| `openai:gpt-5.4-nano` | `conflict_candidate_detector` | pending | 0 / 99 | 0 | 0 | 0 |
| `openai:gpt-5.5-high` | `conflict_candidate_detector` | pending | 0 / 99 | 0 | 0 | 0 |
| `openrouter:google/gemma-3n-e4b-it` | `conflict_candidate_detector` | pending | 0 / 99 | 0 | 0 | 0 |
| `openrouter:google/gemma-4-31b-it-fp8` | `conflict_candidate_detector` | pending | 0 / 99 | 0 | 0 | 0 |
| `openrouter:qwen/qwen3.5-27b-fp8` | `conflict_candidate_detector` | pending | 0 / 99 | 0 | 0 | 0 |
| `openrouter:qwen/qwen3.5-9b-fp8` | `conflict_candidate_detector` | pending | 0 / 99 | 0 | 0 | 0 |
| `anthropic:claude-haiku-4-5` | `conflict_explainer` | pending | 0 / 171 | 0 | 0 | 0 |
| `google:gemini-2.5-flash-lite` | `conflict_explainer` | pending | 0 / 171 | 0 | 0 | 0 |
| `openai:gpt-5.4-mini` | `conflict_explainer` | pending | 0 / 171 | 0 | 0 | 0 |
| `openai:gpt-5.4-nano` | `conflict_explainer` | pending | 0 / 171 | 0 | 0 | 0 |
| `openrouter:google/gemma-3n-e4b-it` | `conflict_explainer` | pending | 0 / 171 | 0 | 0 | 0 |
| `openrouter:google/gemma-4-31b-it-fp8` | `conflict_explainer` | pending | 0 / 171 | 0 | 0 | 0 |
| `openrouter:qwen/qwen3.5-27b-fp8` | `conflict_explainer` | pending | 0 / 171 | 0 | 0 | 0 |
| `openrouter:qwen/qwen3.5-9b-fp8` | `conflict_explainer` | pending | 0 / 171 | 0 | 0 | 0 |
| `anthropic:claude-haiku-4-5` | `debug_explainer` | pending | 0 / 72 | 0 | 0 | 0 |
| `anthropic:claude-sonnet-4-6` | `debug_explainer` | pending | 0 / 72 | 0 | 0 | 0 |
| `google:gemini-2.5-flash` | `debug_explainer` | pending | 0 / 72 | 0 | 0 | 0 |
| `google:gemini-2.5-flash-lite` | `debug_explainer` | pending | 0 / 72 | 0 | 0 | 0 |
| `openai:gpt-5.4` | `debug_explainer` | pending | 0 / 72 | 0 | 0 | 0 |
| `openai:gpt-5.4-low` | `debug_explainer` | pending | 0 / 72 | 0 | 0 | 0 |
| `openai:gpt-5.4-mini` | `debug_explainer` | pending | 0 / 72 | 0 | 0 | 0 |
| `openai:gpt-5.5` | `debug_explainer` | pending | 0 / 72 | 0 | 0 | 0 |
| `openai:gpt-5.5-high` | `debug_explainer` | pending | 0 / 72 | 0 | 0 | 0 |
| `openrouter:google/gemma-3n-e4b-it` | `debug_explainer` | pending | 0 / 72 | 0 | 0 | 0 |
| `openrouter:google/gemma-4-31b-it-fp8` | `debug_explainer` | pending | 0 / 72 | 0 | 0 | 0 |
| `openrouter:qwen/qwen3.5-27b-fp8` | `debug_explainer` | pending | 0 / 72 | 0 | 0 | 0 |
| `openrouter:qwen/qwen3.5-9b-fp8` | `debug_explainer` | pending | 0 / 72 | 0 | 0 | 0 |
| `aws-bedrock:mistral.ministral-3-14b-instruct` | `durability_filter` | pending | 0 / 270 | 0 | 0 | 0 |
