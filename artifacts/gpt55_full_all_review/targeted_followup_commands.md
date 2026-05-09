# Targeted Follow-Up Eval Commands

Run these only after inspecting current zero-tolerance failures. They intentionally avoid a full matrix rerun.

```bash
brain eval models \
  --fixture-set brain-model-test-v2 \
  --mode fine-grained \
  --roles atomic_card_extractor,durability_filter,recall_synthesizer,eval_judge,debug_explainer \
  --models openai:gpt-5.4-mini,openai:gpt-5.5-high,openai:gpt-5.4-nano,google:gemini-2.5-flash-lite,openai:gpt-5.4-low \
  --repeat-runs 1 \
  --endpoint-max-concurrency 3 \
  --output-json artifacts/gpt55_full_all_review/targeted_followups/results.json \
  --raw-output-dir artifacts/gpt55_full_all_review/targeted_followups/raw
```

Focused source/safety rerun if scorer inspection confirms the current failures are genuine:

```bash
brain eval models \
  --fixture-set brain-model-test-v2 \
  --mode fine-grained \
  --roles source_classifier,conflict_candidate_detector,conflict_explainer \
  --models openai:gpt-5-nano,openai:gpt-5.4-mini,google:gemini-2.5-flash-lite \
  --repeat-runs 1 \
  --endpoint-max-concurrency 3 \
  --output-json artifacts/gpt55_full_all_review/targeted_source_safety/results.json \
  --raw-output-dir artifacts/gpt55_full_all_review/targeted_source_safety/raw
```
