# Brain Model Eval Report

- Run ID: `eval_20260506_130842`
- Fixture set: `production`
- JSONL output: `eval_runs/model_test_openai54_fix_20260506_140842.jsonl`
- Records: `1107`

## Executive Summary

- Model-role summaries: `11`
- Provider/schema failures: `2`
- Zero-tolerance failures: `235`
- Eligible model-role pairs: `0`

## Eligibility

| Model | Role | Variants | Overall | CI 95% | Zero tolerance | Upper 95% fail rate | Cost / 1k successful | p50/p90/p95 ms | Eligible | Rejection |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `openai:gpt-5.4` | `eval_judge` | 36 | 0.838 | 0.796-0.872 | 0 | 0.083 | $4.7373 | 5417/6337/6675 | False | decision_correctness below threshold |
| `openai:gpt-5.4-mini` | `conflict_classifier` | 99 | 0.755 | 0.724-0.787 | 70 | 0.788 | $1.8508 | 3623/5287/5648 | False | 70 zero-tolerance failures |
| `openai:gpt-5.4-mini` | `debug_explainer` | 72 | 0.855 | 0.789-0.911 | 0 | 0.042 | $1.9249 | 3657/4792/5211 | False | decision_correctness below threshold |
| `openai:gpt-5.4-mini` | `entity_resolution` | 27 | 0.802 | 0.753-0.877 | 18 | 0.814 | $1.6040 | 4098/5395/6385 | False | 18 zero-tolerance failures |
| `openai:gpt-5.4-mini` | `memory_compiler` | 135 | 0.736 | 0.701-0.768 | 41 | 0.386 | $2.2865 | 3718/5231/5504 | False | 41 zero-tolerance failures |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | 108 | 0.937 | 0.911-0.971 | 13 | 0.195 | $1.7295 | 3066/4422/4794 | False | 13 zero-tolerance failures |
| `openai:gpt-5.4-mini` | `slack_intake` | 180 | 0.765 | 0.732-0.797 | 9 | 0.092 | $1.5212 | 3192/4703/5425 | False | 9 zero-tolerance failures |
| `openai:gpt-5.4-nano` | `entity_resolution` | 27 | 0.809 | 0.761-0.889 | 18 | 0.814 | $0.5247 | 4199/4902/5989 | False | 18 zero-tolerance failures |
| `openai:gpt-5.4-nano` | `memory_compiler` | 135 | 0.733 | 0.700-0.763 | 42 | 0.394 | $0.8259 | 5194/7375/7860 | False | 1 provider/schema failures |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | 108 | 0.882 | 0.854-0.916 | 15 | 0.217 | $0.5136 | 3413/5183/6275 | False | 1 provider/schema failures |
| `openai:gpt-5.4-nano` | `slack_intake` | 180 | 0.767 | 0.726-0.806 | 9 | 0.092 | $0.5005 | 3934/5405/5805 | False | 9 zero-tolerance failures |

## Subscores

| Model | Role | Subscore | Mean | 95% CI |
|---|---|---|---:|---:|
| `openai:gpt-5.4` | `eval_judge` | `schema_validity` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4` | `eval_judge` | `decision_correctness` | 0.000 | 0.000-0.000 |
| `openai:gpt-5.4` | `eval_judge` | `memory_card_quality` | 0.847 | 0.625-1.000 |
| `openai:gpt-5.4` | `eval_judge` | `entity_safety` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4` | `eval_judge` | `conflict_safety` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4` | `eval_judge` | `source_memory_split` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4` | `eval_judge` | `repair_quality` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4` | `eval_judge` | `success_receipt_quality` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4` | `eval_judge` | `recall_quality` | 0.694 | 0.528-0.861 |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `schema_validity` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `decision_correctness` | 0.182 | 0.000-0.357 |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `memory_card_quality` | 0.904 | 0.694-1.000 |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `entity_safety` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_safety` | 0.131 | 0.015-0.344 |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `source_memory_split` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `repair_quality` | 0.909 | 0.750-1.000 |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `success_receipt_quality` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `recall_quality` | 0.667 | 0.461-0.826 |
| `openai:gpt-5.4-mini` | `debug_explainer` | `schema_validity` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `debug_explainer` | `decision_correctness` | 0.750 | 0.429-1.000 |
| `openai:gpt-5.4-mini` | `debug_explainer` | `memory_card_quality` | 0.537 | 0.284-0.786 |
| `openai:gpt-5.4-mini` | `debug_explainer` | `entity_safety` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `debug_explainer` | `conflict_safety` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `debug_explainer` | `source_memory_split` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `debug_explainer` | `repair_quality` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `debug_explainer` | `success_receipt_quality` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `debug_explainer` | `recall_quality` | 0.408 | 0.224-0.581 |
| `openai:gpt-5.4-mini` | `entity_resolution` | `schema_validity` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `entity_resolution` | `decision_correctness` | 0.333 | 0.000-1.000 |
| `openai:gpt-5.4-mini` | `entity_resolution` | `memory_card_quality` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `entity_resolution` | `entity_safety` | 0.000 | 0.000-0.000 |
| `openai:gpt-5.4-mini` | `entity_resolution` | `conflict_safety` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `entity_resolution` | `source_memory_split` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `entity_resolution` | `repair_quality` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `entity_resolution` | `success_receipt_quality` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `entity_resolution` | `recall_quality` | 0.889 | 0.778-1.000 |
| `openai:gpt-5.4-mini` | `memory_compiler` | `schema_validity` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `memory_compiler` | `decision_correctness` | 0.000 | 0.000-0.000 |
| `openai:gpt-5.4-mini` | `memory_compiler` | `memory_card_quality` | 0.167 | 0.017-0.364 |
| `openai:gpt-5.4-mini` | `memory_compiler` | `entity_safety` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `memory_compiler` | `conflict_safety` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `memory_compiler` | `source_memory_split` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `memory_compiler` | `repair_quality` | 0.881 | 0.708-1.000 |
| `openai:gpt-5.4-mini` | `memory_compiler` | `success_receipt_quality` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `memory_compiler` | `recall_quality` | 0.578 | 0.403-0.744 |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `schema_validity` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `decision_correctness` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `memory_card_quality` | 0.620 | 0.418-0.849 |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `entity_safety` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `conflict_safety` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `source_memory_split` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `repair_quality` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `success_receipt_quality` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `recall_quality` | 0.815 | 0.670-0.950 |
| `openai:gpt-5.4-mini` | `slack_intake` | `schema_validity` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `slack_intake` | `decision_correctness` | 0.033 | 0.000-0.078 |
| `openai:gpt-5.4-mini` | `slack_intake` | `memory_card_quality` | 0.658 | 0.472-0.828 |
| `openai:gpt-5.4-mini` | `slack_intake` | `entity_safety` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `slack_intake` | `conflict_safety` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `slack_intake` | `source_memory_split` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-mini` | `slack_intake` | `repair_quality` | 0.721 | 0.526-0.903 |
| `openai:gpt-5.4-mini` | `slack_intake` | `success_receipt_quality` | 0.911 | 0.774-1.000 |
| `openai:gpt-5.4-mini` | `slack_intake` | `recall_quality` | 0.560 | 0.412-0.699 |
| `openai:gpt-5.4-nano` | `entity_resolution` | `schema_validity` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-nano` | `entity_resolution` | `decision_correctness` | 0.333 | 0.000-1.000 |
| `openai:gpt-5.4-nano` | `entity_resolution` | `memory_card_quality` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-nano` | `entity_resolution` | `entity_safety` | 0.000 | 0.000-0.000 |
| `openai:gpt-5.4-nano` | `entity_resolution` | `conflict_safety` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-nano` | `entity_resolution` | `source_memory_split` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-nano` | `entity_resolution` | `repair_quality` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-nano` | `entity_resolution` | `success_receipt_quality` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-nano` | `entity_resolution` | `recall_quality` | 0.951 | 0.852-1.000 |
| `openai:gpt-5.4-nano` | `memory_compiler` | `schema_validity` | 0.993 | 0.976-1.000 |
| `openai:gpt-5.4-nano` | `memory_compiler` | `decision_correctness` | 0.000 | 0.000-0.000 |
| `openai:gpt-5.4-nano` | `memory_compiler` | `memory_card_quality` | 0.173 | 0.030-0.369 |
| `openai:gpt-5.4-nano` | `memory_compiler` | `entity_safety` | 0.993 | 0.976-1.000 |
| `openai:gpt-5.4-nano` | `memory_compiler` | `conflict_safety` | 0.993 | 0.976-1.000 |
| `openai:gpt-5.4-nano` | `memory_compiler` | `source_memory_split` | 0.993 | 0.976-1.000 |
| `openai:gpt-5.4-nano` | `memory_compiler` | `repair_quality` | 0.859 | 0.659-1.000 |
| `openai:gpt-5.4-nano` | `memory_compiler` | `success_receipt_quality` | 0.993 | 0.976-1.000 |
| `openai:gpt-5.4-nano` | `memory_compiler` | `recall_quality` | 0.600 | 0.444-0.741 |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `schema_validity` | 0.991 | 0.970-1.000 |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `decision_correctness` | 0.991 | 0.970-1.000 |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `memory_card_quality` | 0.587 | 0.430-0.762 |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `entity_safety` | 0.991 | 0.970-1.000 |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `conflict_safety` | 0.991 | 0.970-1.000 |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `source_memory_split` | 0.991 | 0.970-1.000 |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `repair_quality` | 0.991 | 0.970-1.000 |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `success_receipt_quality` | 0.991 | 0.970-1.000 |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_quality` | 0.418 | 0.205-0.658 |
| `openai:gpt-5.4-nano` | `slack_intake` | `schema_validity` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-nano` | `slack_intake` | `decision_correctness` | 0.000 | 0.000-0.000 |
| `openai:gpt-5.4-nano` | `slack_intake` | `memory_card_quality` | 0.626 | 0.455-0.792 |
| `openai:gpt-5.4-nano` | `slack_intake` | `entity_safety` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-nano` | `slack_intake` | `conflict_safety` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-nano` | `slack_intake` | `source_memory_split` | 1.000 | 1.000-1.000 |
| `openai:gpt-5.4-nano` | `slack_intake` | `repair_quality` | 0.716 | 0.519-0.903 |
| `openai:gpt-5.4-nano` | `slack_intake` | `success_receipt_quality` | 0.908 | 0.771-1.000 |
| `openai:gpt-5.4-nano` | `slack_intake` | `recall_quality` | 0.653 | 0.480-0.812 |

## Pairwise Comparisons

| Role | Model A | Model B | Paired fixtures | Score diff A-B | 95% CI | Cheaper | Recommendation |
|---|---|---|---:|---:|---:|---|---|
| `entity_resolution` | `openai:gpt-5.4-mini` | `openai:gpt-5.4-nano` | 27 | -0.007 | -0.025-0.016 | `openai:gpt-5.4-nano` | quality_difference_not_statistically_clear_choose_openai:gpt-5.4-nano |
| `memory_compiler` | `openai:gpt-5.4-mini` | `openai:gpt-5.4-nano` | 135 | 0.003 | -0.013-0.021 | `openai:gpt-5.4-nano` | quality_difference_not_statistically_clear_choose_openai:gpt-5.4-nano |
| `recall_synthesizer` | `openai:gpt-5.4-mini` | `openai:gpt-5.4-nano` | 108 | 0.055 | 0.029-0.083 | `openai:gpt-5.4-nano` | openai:gpt-5.4-mini_higher_quality |
| `slack_intake` | `openai:gpt-5.4-mini` | `openai:gpt-5.4-nano` | 180 | -0.002 | -0.018-0.015 | `openai:gpt-5.4-nano` | quality_difference_not_statistically_clear_choose_openai:gpt-5.4-nano |

## Failures

| Model | Role | Fixture | Error |
|---|---|---|---|
| `openai:gpt-5.4-nano` | `memory_compiler` | `long_markdown_chat_summary_001` | Invalid control character at: line 96 column 24 (char 2709) |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_ai_memory_articles_relevance_001__punctuation` | HTTP 502: <!DOCTYPE html> <!--[if lt IE 7]> <html class="no-js ie6 oldie" lang="en-US"> <![endif]--> <!--[if IE 7]> <html class="no-js ie7 oldie" lang="en-US... |

## Zero-Tolerance Failures

| Model | Role | Fixture | Notes |
|---|---|---|---|
| `openai:gpt-5.4-nano` | `entity_resolution` | `entity_ambiguous_sam_two_people` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `entity_resolution` | `entity_ambiguous_sam_two_people` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `entity_resolution` | `entity_ambiguous_sam_two_people` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `entity_resolution` | `entity_ambiguous_sam_two_people__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `entity_resolution` | `entity_ambiguous_sam_two_people__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `entity_resolution` | `entity_ambiguous_sam_two_people__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `entity_resolution` | `entity_ambiguous_sam_two_people__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `entity_resolution` | `entity_ambiguous_sam_two_people__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `entity_resolution` | `entity_ambiguous_sam_two_people__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `entity_resolution` | `ambiguous_place_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `entity_resolution` | `ambiguous_place_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `entity_resolution` | `ambiguous_place_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `entity_resolution` | `ambiguous_place_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `entity_resolution` | `ambiguous_place_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `entity_resolution` | `ambiguous_place_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `entity_resolution` | `ambiguous_place_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `entity_resolution` | `ambiguous_place_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `entity_resolution` | `ambiguous_place_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `memory_compiler_small_table` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `memory_compiler_small_table` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `memory_compiler_small_table__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `memory_compiler_small_table__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `memory_compiler_small_table` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `memory_compiler_small_table__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `memory_compiler_small_table__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `memory_compiler_small_table__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `memory_compiler_small_table__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_ai_memory_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_ai_memory_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_ai_memory_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_ai_memory_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_ai_memory_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_ai_memory_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_ai_memory_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_ai_memory_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_ai_memory_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_fetch_failure_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_fetch_failure_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_fetch_failure_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_fetch_failure_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_fetch_failure_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_fetch_failure_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_fetch_failure_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_fetch_failure_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `long_markdown_chat_summary_001` | schema_failure |
| `openai:gpt-5.4-nano` | `memory_compiler` | `email_source_meeting_followup_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `email_source_meeting_followup_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `email_source_meeting_followup_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `email_source_meeting_followup_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `email_source_meeting_followup_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `email_source_meeting_followup_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `small_table_preferences_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `small_table_preferences_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `small_table_preferences_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `small_table_preferences_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `small_table_preferences_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `small_table_preferences_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `small_table_preferences_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `small_table_preferences_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `memory_compiler` | `small_table_preferences_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_absence_scoped` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_absence_scoped` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_absence_scoped__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_absence_scoped__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_absence_scoped__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_ai_memory_articles_relevance_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_brain_cognee_conclusions_relevance_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_brain_cognee_conclusions_relevance_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_brain_cognee_conclusions_relevance_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_brain_cognee_conclusions_relevance_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_brain_cognee_conclusions_relevance_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_brain_cognee_conclusions_relevance_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_brain_cognee_conclusions_relevance_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_brain_cognee_conclusions_relevance_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_brain_cognee_conclusions_relevance_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `slack_intake` | `slack_success_receipt_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `slack_intake` | `slack_success_receipt_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `slack_intake` | `slack_success_receipt_001` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `slack_intake` | `slack_success_receipt_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `slack_intake` | `slack_success_receipt_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `slack_intake` | `slack_success_receipt_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `slack_intake` | `slack_success_receipt_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `slack_intake` | `slack_success_receipt_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-nano` | `slack_intake` | `slack_success_receipt_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_employment_transition` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_employment_transition` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_employment_transition__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_employment_transition` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_employment_transition__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_employment_transition__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_employment_transition__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_employment_transition__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_correction_like` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_employment_transition__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_correction_like` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_correction_like` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_correction_like__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_correction_like__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_correction_like__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_correction_like__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_correction_like__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_correction_like__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `additive_sam_preferences_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `additive_sam_preferences_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `additive_sam_preferences_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `additive_sam_preferences_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `additive_sam_preferences_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `additive_sam_preferences_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `additive_sam_preferences_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `supersession_sam_job_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `supersession_sam_job_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `supersession_sam_job_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `supersession_sam_job_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `supersession_sam_job_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `supersession_sam_job_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `supersession_sam_job_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `correction_sam_music_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `supersession_sam_job_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `supersession_sam_job_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `correction_sam_music_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `correction_sam_music_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `correction_sam_music_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `correction_sam_music_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `correction_sam_music_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `correction_sam_music_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `correction_sam_music_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `correction_sam_music_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_sara_niece_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_sara_niece_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_sara_niece_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_sara_niece_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_sara_niece_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_sara_niece_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_sara_niece_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_sara_niece_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `conflict_sara_niece_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `contradiction_sam_children_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `contradiction_sam_children_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `contradiction_sam_children_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `contradiction_sam_children_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `contradiction_sam_children_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `contradiction_sam_children_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `contradiction_sam_children_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `contradiction_sam_children_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `contradiction_sam_children_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `concurrent_conflict_writes_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `concurrent_conflict_writes_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `concurrent_conflict_writes_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `concurrent_conflict_writes_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `concurrent_conflict_writes_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `concurrent_conflict_writes_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `concurrent_conflict_writes_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `concurrent_conflict_writes_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `conflict_classifier` | `concurrent_conflict_writes_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `entity_ambiguous_sam_two_people` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `entity_ambiguous_sam_two_people` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `entity_ambiguous_sam_two_people__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `entity_ambiguous_sam_two_people` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `entity_ambiguous_sam_two_people__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `entity_ambiguous_sam_two_people__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `entity_ambiguous_sam_two_people__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `entity_ambiguous_sam_two_people__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `entity_ambiguous_sam_two_people__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `ambiguous_place_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `ambiguous_place_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `ambiguous_place_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `ambiguous_place_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `ambiguous_place_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `ambiguous_place_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `ambiguous_place_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `ambiguous_place_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `entity_resolution` | `ambiguous_place_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `memory_compiler_small_table` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `memory_compiler_small_table` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `memory_compiler_small_table__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `memory_compiler_small_table__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `memory_compiler_small_table` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `memory_compiler_small_table__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `memory_compiler_small_table__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `memory_compiler_small_table__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `memory_compiler_small_table__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_ai_memory_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_ai_memory_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_ai_memory_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_ai_memory_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_ai_memory_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_ai_memory_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_ai_memory_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_ai_memory_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_ai_memory_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_fetch_failure_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_fetch_failure_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_fetch_failure_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_fetch_failure_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_fetch_failure_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_fetch_failure_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_fetch_failure_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_fetch_failure_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `article_url_fetch_failure_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `email_source_meeting_followup_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `email_source_meeting_followup_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `email_source_meeting_followup_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `email_source_meeting_followup_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `email_source_meeting_followup_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `small_table_preferences_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `small_table_preferences_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `small_table_preferences_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `small_table_preferences_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `small_table_preferences_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `small_table_preferences_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `small_table_preferences_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `small_table_preferences_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `memory_compiler` | `small_table_preferences_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `recall_absence_scoped` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `recall_absence_scoped` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `recall_absence_scoped` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `recall_absence_scoped__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `recall_absence_scoped__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `recall_brain_cognee_conclusions_relevance_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `recall_brain_cognee_conclusions_relevance_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `recall_brain_cognee_conclusions_relevance_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `recall_brain_cognee_conclusions_relevance_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `recall_brain_cognee_conclusions_relevance_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `recall_brain_cognee_conclusions_relevance_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `recall_brain_cognee_conclusions_relevance_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `recall_synthesizer` | `recall_brain_cognee_conclusions_relevance_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `slack_intake` | `slack_success_receipt_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `slack_intake` | `slack_success_receipt_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `slack_intake` | `slack_success_receipt_001` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `slack_intake` | `slack_success_receipt_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `slack_intake` | `slack_success_receipt_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `slack_intake` | `slack_success_receipt_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `slack_intake` | `slack_success_receipt_001__punctuation` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `slack_intake` | `slack_success_receipt_001__context` | zero_tolerance_failed |
| `openai:gpt-5.4-mini` | `slack_intake` | `slack_success_receipt_001__punctuation` | zero_tolerance_failed |

## Worst Failure Examples

| Model | Role | Fixture | Overall score | Raw output |
|---|---|---|---:|---|
| `openai:gpt-5.4-nano` | `memory_compiler` | `long_markdown_chat_summary_001` | 0.000 | `eval_runs/raw/eval_20260506_130842/openai_gpt-5.4-nano__long_markdown_chat_summary_001__2.json` |
| `openai:gpt-5.4-nano` | `recall_synthesizer` | `recall_ai_memory_articles_relevance_001__punctuation` | 0.000 | `eval_runs/raw/eval_20260506_130842/openai_gpt-5.4-nano__recall_ai_memory_articles_relevance_001__punctuation__2.json` |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_fetch_failure_001` | 0.556 | `eval_runs/raw/eval_20260506_130842/openai_gpt-5.4-nano__article_url_fetch_failure_001__0.json` |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_fetch_failure_001` | 0.556 | `eval_runs/raw/eval_20260506_130842/openai_gpt-5.4-nano__article_url_fetch_failure_001__1.json` |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_fetch_failure_001` | 0.556 | `eval_runs/raw/eval_20260506_130842/openai_gpt-5.4-nano__article_url_fetch_failure_001__2.json` |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_fetch_failure_001__context` | 0.556 | `eval_runs/raw/eval_20260506_130842/openai_gpt-5.4-nano__article_url_fetch_failure_001__context__0.json` |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_fetch_failure_001__context` | 0.556 | `eval_runs/raw/eval_20260506_130842/openai_gpt-5.4-nano__article_url_fetch_failure_001__context__1.json` |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_fetch_failure_001__punctuation` | 0.556 | `eval_runs/raw/eval_20260506_130842/openai_gpt-5.4-nano__article_url_fetch_failure_001__punctuation__0.json` |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_fetch_failure_001__context` | 0.556 | `eval_runs/raw/eval_20260506_130842/openai_gpt-5.4-nano__article_url_fetch_failure_001__context__2.json` |
| `openai:gpt-5.4-nano` | `memory_compiler` | `article_url_fetch_failure_001__punctuation` | 0.556 | `eval_runs/raw/eval_20260506_130842/openai_gpt-5.4-nano__article_url_fetch_failure_001__punctuation__2.json` |

## Recommended Production Defaults

- No model-role pair met the eligibility gates in this run.

## Recommended Escalation Rules

- Escalate high-confidence conflicts, ambiguous entity resolution, malformed JSON, and source/material split failures to the strongest eligible model for that role.
- Prefer user choice over model guessing whenever entity ambiguity or durable-memory overwrite risk remains.
- Reject or request repair when all models fail a zero-tolerance gate for a fixture family.

## Known Uncertainties

- Provider quotas, account credits, and regional model availability can make a model fail operationally even when the harness is correct.
- The fixture catalogue is code-backed and broad, but scoring remains heuristic; borderline/failure samples should be judge-audited before production selection.
- Confidence intervals are scenario-group bootstraps over the configured fixture set; they become meaningful only when enough variants are run.
