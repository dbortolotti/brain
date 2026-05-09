# Executive verdict

Deployable stack: **NO**

This run is not sufficient to select a full production Brain model stack.

Missing mandatory roles:
- conflict_handling
- entity_resolution
- memory_compiler
- recall
- slack_intake

Interpretation:
Only runtime, judge, support had eligible candidates. Treat this as a harness validation run, not a model-selection run.

Eligible partials:
- `entity_mention_extractor`: `openai:gpt-5.5`
- `groundedness_checker`: `openai:gpt-5.5`
- `intent_router`: `openai:gpt-5.5`
- `memory_kind_classifier`: `openai:gpt-5.5`
- `recall_planner`: `openai:gpt-5.5`
- `relationship_extractor`: `openai:gpt-5.5`
- `repair_option_generator`: `openai:gpt-5.5`

## Deployability status

- Run ID: `eval_20260508_195937`
- Eval mode: `fine-grained`
- Fixture set: `brain-model-test-v2`
- Canonical output: `artifacts/full_model_suite_gpt55_1repeat_manual_20260508_205815/results_fine_grained_gpt55_1repeat.json`
- Failed manifest JSONL: `artifacts/full_model_suite_gpt55_1repeat_manual_20260508_205815/failed_tests.jsonl`
- Failed manifest markdown: `artifacts/full_model_suite_gpt55_1repeat_manual_20260508_205815/failed_tests.md`
- HTML summary: `artifacts/full_model_suite_gpt55_1repeat_manual_20260508_205815/summary.html`
- Zero-tolerance detail CSV: `artifacts/full_model_suite_gpt55_1repeat_manual_20260508_205815/zero_tolerance_failures_detail.csv`
- Failed fixture summary CSV: `artifacts/full_model_suite_gpt55_1repeat_manual_20260508_205815/failed_fixture_summary.csv`
- Targeted follow-up commands: `artifacts/full_model_suite_gpt55_1repeat_manual_20260508_205815/targeted_followup_commands.md`
- Records: `1278`
- Model-role summaries: `19`
- Deployable stack: `no`
- Eligible runtime role pairs: `2`
- Eligible embedding role pairs: `0`
- Eligible judge role pairs: `1`
- Eligible debug/admin role pairs: `0`
- Eligible support role pairs: `4`
- Eligibility states: `eligible (7); failed_safety (6); insufficient_sample (4); failed_quality (2)`


## Mandatory role coverage

| Target | Required | Eligible models | Status |
|---|---:|---|---|
| `conflict_handling` | yes | `conflict_candidate_detector`: none; `conflict_explainer`: none | MISSING |
| `debug` | yes | `debug_explainer`: none | MISSING |
| `embeddings` | no | none | NOT_TESTED |
| `entity_resolution` | yes | `entity_candidate_ranker`: none; `entity_mention_extractor`: `openai:gpt-5.5` | MISSING |
| `judge` | yes | `eval_judge`: none | MISSING |
| `memory_compiler` | yes | `atomic_card_extractor`: none; `entity_mention_extractor`: `openai:gpt-5.5`; `open_loop_detector`: none; `relationship_extractor`: `openai:gpt-5.5`; `source_takeaway_extractor`: none; `table_policy_handler`: none | MISSING |
| `recall` | yes | `recall_planner`: `openai:gpt-5.5`; `recall_synthesizer`: none | MISSING |
| `router` | yes | `intent_router`: `openai:gpt-5.5` | ELIGIBLE |
| `slack_intake` | yes | `durability_filter`: none; `memory_kind_classifier`: `openai:gpt-5.5`; `repair_option_generator`: `openai:gpt-5.5`; `source_classifier`: none | MISSING |

## Operational reliability

| Model | Role | Operational success | 95% CI | Successes / Total |
|---|---|---:|---:|---:|
| `openai:gpt-5.5` | `atomic_card_extractor` | 1.000 | 0.921-1.000 | 45 / 45 |
| `openai:gpt-5.5` | `conflict_candidate_detector` | 1.000 | 0.896-1.000 | 33 / 33 |
| `openai:gpt-5.5` | `conflict_explainer` | 1.000 | 0.896-1.000 | 33 / 33 |
| `openai:gpt-5.5` | `debug_explainer` | 1.000 | 0.862-1.000 | 24 / 24 |
| `openai:gpt-5.5` | `durability_filter` | 1.000 | 0.959-1.000 | 90 / 90 |
| `openai:gpt-5.5` | `entity_candidate_ranker` | 1.000 | 0.701-1.000 | 9 / 9 |
| `openai:gpt-5.5` | `entity_mention_extractor` | 1.000 | 0.967-1.000 | 114 / 114 |
| `openai:gpt-5.5` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |
| `openai:gpt-5.5` | `groundedness_checker` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.5` | `intent_router` | 1.000 | 0.978-1.000 | 171 / 171 |
| `openai:gpt-5.5` | `memory_kind_classifier` | 1.000 | 0.965-1.000 | 105 / 105 |
| `openai:gpt-5.5` | `open_loop_detector` | 1.000 | 0.965-1.000 | 105 / 105 |
| `openai:gpt-5.5` | `recall_planner` | 1.000 | 0.916-1.000 | 42 / 42 |
| `openai:gpt-5.5` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.5` | `relationship_extractor` | 1.000 | 0.965-1.000 | 105 / 105 |
| `openai:gpt-5.5` | `repair_option_generator` | 1.000 | 0.970-1.000 | 123 / 123 |
| `openai:gpt-5.5` | `source_classifier` | 1.000 | 0.965-1.000 | 105 / 105 |
| `openai:gpt-5.5` | `source_takeaway_extractor` | 1.000 | 0.921-1.000 | 45 / 45 |
| `openai:gpt-5.5` | `table_policy_handler` | 1.000 | 0.921-1.000 | 45 / 45 |

No operational failures were recorded.

## Schema validity

| Model | Role | JSON parse success | 95% CI | Parseable / Operationally successful |
|---|---|---:|---:|---:|
| `openai:gpt-5.5` | `atomic_card_extractor` | 1.000 | 0.921-1.000 | 45 / 45 |
| `openai:gpt-5.5` | `conflict_candidate_detector` | 1.000 | 0.896-1.000 | 33 / 33 |
| `openai:gpt-5.5` | `conflict_explainer` | 1.000 | 0.896-1.000 | 33 / 33 |
| `openai:gpt-5.5` | `debug_explainer` | 1.000 | 0.862-1.000 | 24 / 24 |
| `openai:gpt-5.5` | `durability_filter` | 1.000 | 0.959-1.000 | 90 / 90 |
| `openai:gpt-5.5` | `entity_candidate_ranker` | 1.000 | 0.701-1.000 | 9 / 9 |
| `openai:gpt-5.5` | `entity_mention_extractor` | 1.000 | 0.967-1.000 | 114 / 114 |
| `openai:gpt-5.5` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |
| `openai:gpt-5.5` | `groundedness_checker` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.5` | `intent_router` | 1.000 | 0.978-1.000 | 171 / 171 |
| `openai:gpt-5.5` | `memory_kind_classifier` | 1.000 | 0.965-1.000 | 105 / 105 |
| `openai:gpt-5.5` | `open_loop_detector` | 1.000 | 0.965-1.000 | 105 / 105 |
| `openai:gpt-5.5` | `recall_planner` | 1.000 | 0.916-1.000 | 42 / 42 |
| `openai:gpt-5.5` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.5` | `relationship_extractor` | 1.000 | 0.965-1.000 | 105 / 105 |
| `openai:gpt-5.5` | `repair_option_generator` | 1.000 | 0.970-1.000 | 123 / 123 |
| `openai:gpt-5.5` | `source_classifier` | 1.000 | 0.965-1.000 | 105 / 105 |
| `openai:gpt-5.5` | `source_takeaway_extractor` | 1.000 | 0.921-1.000 | 45 / 45 |
| `openai:gpt-5.5` | `table_policy_handler` | 1.000 | 0.921-1.000 | 45 / 45 |

| Model | Role | Schema validity | 95% CI | Valid / Parseable |
|---|---|---:|---:|---:|
| `openai:gpt-5.5` | `atomic_card_extractor` | 1.000 | 0.921-1.000 | 45 / 45 |
| `openai:gpt-5.5` | `conflict_candidate_detector` | 1.000 | 0.896-1.000 | 33 / 33 |
| `openai:gpt-5.5` | `conflict_explainer` | 1.000 | 0.896-1.000 | 33 / 33 |
| `openai:gpt-5.5` | `debug_explainer` | 1.000 | 0.862-1.000 | 24 / 24 |
| `openai:gpt-5.5` | `durability_filter` | 1.000 | 0.959-1.000 | 90 / 90 |
| `openai:gpt-5.5` | `entity_candidate_ranker` | 1.000 | 0.701-1.000 | 9 / 9 |
| `openai:gpt-5.5` | `entity_mention_extractor` | 1.000 | 0.967-1.000 | 114 / 114 |
| `openai:gpt-5.5` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |
| `openai:gpt-5.5` | `groundedness_checker` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.5` | `intent_router` | 1.000 | 0.978-1.000 | 171 / 171 |
| `openai:gpt-5.5` | `memory_kind_classifier` | 1.000 | 0.965-1.000 | 105 / 105 |
| `openai:gpt-5.5` | `open_loop_detector` | 1.000 | 0.965-1.000 | 105 / 105 |
| `openai:gpt-5.5` | `recall_planner` | 1.000 | 0.916-1.000 | 42 / 42 |
| `openai:gpt-5.5` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.5` | `relationship_extractor` | 1.000 | 0.965-1.000 | 105 / 105 |
| `openai:gpt-5.5` | `repair_option_generator` | 1.000 | 0.970-1.000 | 123 / 123 |
| `openai:gpt-5.5` | `source_classifier` | 1.000 | 0.965-1.000 | 105 / 105 |
| `openai:gpt-5.5` | `source_takeaway_extractor` | 1.000 | 0.921-1.000 | 45 / 45 |
| `openai:gpt-5.5` | `table_policy_handler` | 1.000 | 0.921-1.000 | 45 / 45 |

No schema or parse failures were recorded.

## Semantic evaluability

| Model | Role | Semantic evaluable | 95% CI | Semantic-evaluable / Schema-valid |
|---|---|---:|---:|---:|
| `openai:gpt-5.5` | `atomic_card_extractor` | 1.000 | 0.921-1.000 | 45 / 45 |
| `openai:gpt-5.5` | `conflict_candidate_detector` | 1.000 | 0.896-1.000 | 33 / 33 |
| `openai:gpt-5.5` | `conflict_explainer` | 1.000 | 0.896-1.000 | 33 / 33 |
| `openai:gpt-5.5` | `debug_explainer` | 1.000 | 0.862-1.000 | 24 / 24 |
| `openai:gpt-5.5` | `durability_filter` | 1.000 | 0.959-1.000 | 90 / 90 |
| `openai:gpt-5.5` | `entity_candidate_ranker` | 1.000 | 0.701-1.000 | 9 / 9 |
| `openai:gpt-5.5` | `entity_mention_extractor` | 1.000 | 0.967-1.000 | 114 / 114 |
| `openai:gpt-5.5` | `eval_judge` | 1.000 | 0.757-1.000 | 12 / 12 |
| `openai:gpt-5.5` | `groundedness_checker` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.5` | `intent_router` | 1.000 | 0.978-1.000 | 171 / 171 |
| `openai:gpt-5.5` | `memory_kind_classifier` | 1.000 | 0.965-1.000 | 105 / 105 |
| `openai:gpt-5.5` | `open_loop_detector` | 1.000 | 0.965-1.000 | 105 / 105 |
| `openai:gpt-5.5` | `recall_planner` | 1.000 | 0.916-1.000 | 42 / 42 |
| `openai:gpt-5.5` | `recall_synthesizer` | 1.000 | 0.904-1.000 | 36 / 36 |
| `openai:gpt-5.5` | `relationship_extractor` | 1.000 | 0.965-1.000 | 105 / 105 |
| `openai:gpt-5.5` | `repair_option_generator` | 1.000 | 0.970-1.000 | 123 / 123 |
| `openai:gpt-5.5` | `source_classifier` | 1.000 | 0.965-1.000 | 105 / 105 |
| `openai:gpt-5.5` | `source_takeaway_extractor` | 1.000 | 0.921-1.000 | 45 / 45 |
| `openai:gpt-5.5` | `table_policy_handler` | 1.000 | 0.921-1.000 | 45 / 45 |

## Safety / zero-tolerance failures

| Model | Role | Zero-tolerance failures | Upper 95% fail rate | Eligible | Eligibility state |
|---|---|---:|---:|---|---|
| `openai:gpt-5.5` | `atomic_card_extractor` | 9 | 0.338 | False | `failed_safety` |
| `openai:gpt-5.5` | `conflict_candidate_detector` | 0 | 0.091 | False | `insufficient_sample` |
| `openai:gpt-5.5` | `conflict_explainer` | 24 | 0.849 | False | `failed_safety` |
| `openai:gpt-5.5` | `debug_explainer` | 0 | 0.125 | False | `insufficient_sample` |
| `openai:gpt-5.5` | `durability_filter` | 0 | 0.033 | False | `failed_quality` |
| `openai:gpt-5.5` | `entity_candidate_ranker` | 6 | 0.879 | False | `failed_safety` |
| `openai:gpt-5.5` | `entity_mention_extractor` | 0 | 0.026 | True | `eligible` |
| `openai:gpt-5.5` | `eval_judge` | 0 | 0.250 | False | `insufficient_sample` |
| `openai:gpt-5.5` | `groundedness_checker` | 0 | 0.083 | True | `eligible` |
| `openai:gpt-5.5` | `intent_router` | 0 | 0.018 | True | `eligible` |
| `openai:gpt-5.5` | `memory_kind_classifier` | 0 | 0.029 | True | `eligible` |
| `openai:gpt-5.5` | `open_loop_detector` | 0 | 0.029 | False | `failed_quality` |
| `openai:gpt-5.5` | `recall_planner` | 0 | 0.071 | True | `eligible` |
| `openai:gpt-5.5` | `recall_synthesizer` | 0 | 0.083 | False | `insufficient_sample` |
| `openai:gpt-5.5` | `relationship_extractor` | 0 | 0.029 | True | `eligible` |
| `openai:gpt-5.5` | `repair_option_generator` | 0 | 0.024 | True | `eligible` |
| `openai:gpt-5.5` | `source_classifier` | 17 | 0.244 | False | `failed_safety` |
| `openai:gpt-5.5` | `source_takeaway_extractor` | 6 | 0.262 | False | `failed_safety` |
| `openai:gpt-5.5` | `table_policy_handler` | 8 | 0.313 | False | `failed_safety` |

## Quality scores by role

| Model | Role | Category | Quality pass | 95% CI | Passes / Semantic evals | Semantic score | 95% CI | Eligible | Eligibility state | Rejection reasons |
|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| `openai:gpt-5.5` | `atomic_card_extractor` | `runtime_or_support` | 0.311 | 0.195-0.457 | 14 / 45 | 0.528 | 0.378-0.704 | False | `failed_safety` | zero_tolerance_failures_present, semantic_score_below_threshold, memory_card_quality_below_threshold |
| `openai:gpt-5.5` | `conflict_candidate_detector` | `runtime` | 0.939 | 0.804-0.983 | 31 / 33 | 0.952 | 0.813-1.000 | False | `insufficient_sample` | semantic_evaluable_below_minimum, conflict_safety_below_threshold |
| `openai:gpt-5.5` | `conflict_explainer` | `support` | 0.182 | 0.086-0.344 | 6 / 33 | 0.673 | 0.600-0.778 | False | `failed_safety` | zero_tolerance_failures_present, semantic_evaluable_below_minimum, semantic_score_below_threshold |
| `openai:gpt-5.5` | `debug_explainer` | `debug_admin` | 0.792 | 0.595-0.908 | 19 / 24 | 0.917 | 0.790-1.000 | False | `insufficient_sample` | semantic_evaluable_below_minimum |
| `openai:gpt-5.5` | `durability_filter` | `support` | 0.822 | 0.731-0.888 | 74 / 90 | 0.822 | 0.700-0.933 | False | `failed_quality` | semantic_score_below_threshold, durability_decision_below_threshold |
| `openai:gpt-5.5` | `entity_candidate_ranker` | `runtime_or_support` | 0.000 | 0.000-0.299 | 0 / 9 | 0.200 | 0.200-0.200 | False | `failed_safety` | zero_tolerance_failures_present, records_total_below_minimum, semantic_evaluable_below_minimum, semantic_score_below_threshold, entity_safety_below_threshold |
| `openai:gpt-5.5` | `entity_mention_extractor` | `support` | 0.518 | 0.427-0.607 | 59 / 114 | 0.934 | 0.908-0.958 | True | `eligible` | - |
| `openai:gpt-5.5` | `eval_judge` | `judge` | 0.583 | 0.320-0.807 | 7 / 12 | 0.888 | 0.758-1.000 | False | `insufficient_sample` | semantic_evaluable_below_minimum |
| `openai:gpt-5.5` | `groundedness_checker` | `judge` | 0.861 | 0.713-0.939 | 31 / 36 | 0.938 | 0.840-1.000 | True | `eligible` | - |
| `openai:gpt-5.5` | `intent_router` | `runtime` | 0.877 | 0.820-0.918 | 150 / 171 | 0.877 | 0.789-0.948 | True | `eligible` | - |
| `openai:gpt-5.5` | `memory_kind_classifier` | `support` | 0.943 | 0.881-0.974 | 99 / 105 | 0.983 | 0.956-1.000 | True | `eligible` | - |
| `openai:gpt-5.5` | `open_loop_detector` | `support` | 0.819 | 0.735-0.881 | 86 / 105 | 0.819 | 0.694-0.931 | False | `failed_quality` | semantic_score_below_threshold |
| `openai:gpt-5.5` | `recall_planner` | `runtime` | 0.976 | 0.877-0.996 | 41 / 42 | 0.976 | 0.889-1.000 | True | `eligible` | - |
| `openai:gpt-5.5` | `recall_synthesizer` | `runtime` | 0.861 | 0.713-0.939 | 31 / 36 | 0.945 | 0.852-1.000 | False | `insufficient_sample` | semantic_evaluable_below_minimum |
| `openai:gpt-5.5` | `relationship_extractor` | `runtime_or_support` | 0.981 | 0.933-0.995 | 103 / 105 | 0.993 | 0.976-1.000 | True | `eligible` | - |
| `openai:gpt-5.5` | `repair_option_generator` | `support` | 1.000 | 0.970-1.000 | 123 / 123 | 1.000 | 1.000-1.000 | True | `eligible` | - |
| `openai:gpt-5.5` | `source_classifier` | `support` | 0.676 | 0.582-0.758 | 71 / 105 | 0.854 | 0.775-0.919 | False | `failed_safety` | zero_tolerance_failures_present, semantic_score_below_threshold, source_memory_split_below_threshold |
| `openai:gpt-5.5` | `source_takeaway_extractor` | `runtime_or_support` | 0.244 | 0.142-0.387 | 11 / 45 | 0.710 | 0.620-0.810 | False | `failed_safety` | zero_tolerance_failures_present, semantic_score_below_threshold |
| `openai:gpt-5.5` | `table_policy_handler` | `support` | 0.222 | 0.125-0.363 | 10 / 45 | 0.758 | 0.686-0.833 | False | `failed_safety` | zero_tolerance_failures_present, semantic_score_below_threshold |

## Top failed fixtures by role/model

| Role | Model | Semantic score | Quality pass | Zero tolerance | Schema/parse fails | Eligibility state | Rejection reasons | Top failed fixtures | Top zero-tolerance reasons |
|---|---|---:|---:|---:|---:|---|---|---|---|
| `atomic_card_extractor` | `openai:gpt-5.5` | 0.528 | 0.311 | 9 | 0 | `failed_safety` | zero_tolerance_failures_present;semantic_score_below_threshold;memory_card_quality_below_threshold | memory_compiler_small_table (3); memory_compiler_article_atomic (3); chat_conclusion_brain_architecture_001 (3); article_url_ai_memory_001 (3); article_url_fetch_failure_001 (3) | source_invention (6); numeric_values_altered (3) |
| `conflict_candidate_detector` | `openai:gpt-5.5` | 0.952 | 0.939 | 0 | 0 | `insufficient_sample` | semantic_evaluable_below_minimum;conflict_safety_below_threshold | conflict_sara_niece_001 (2) | - |
| `conflict_explainer` | `openai:gpt-5.5` | 0.673 | 0.182 | 24 | 0 | `failed_safety` | zero_tolerance_failures_present;semantic_evaluable_below_minimum;semantic_score_below_threshold | conflict_employment_transition (3); conflict_correction_like (3); additive_sam_preferences_001 (3); supersession_sam_job_001 (3); correction_sam_music_001 (3) | silent_high_confidence_overwrite (24) |
| `debug_explainer` | `openai:gpt-5.5` | 0.917 | 0.792 | 0 | 0 | `insufficient_sample` | semantic_evaluable_below_minimum | normal_user_admin_attempt_001 (3); debug_sql_disabled_001 (2) | - |
| `durability_filter` | `openai:gpt-5.5` | 0.822 | 0.822 | 0 | 0 | `failed_quality` | semantic_score_below_threshold;durability_decision_below_threshold | mixed_language_open_question_001 (3); slack_conflict_buttons_001 (3); validator_blocks_transcript_as_memory_001 (3); validator_blocks_high_confidence_overwrite_001 (3); open_question_knowledge_graphs_001 (1) | - |
| `entity_candidate_ranker` | `openai:gpt-5.5` | 0.200 | 0.000 | 6 | 0 | `failed_safety` | zero_tolerance_failures_present;records_total_below_minimum;semantic_evaluable_below_minimum;semantic_score_below_threshold;entity_safety_below_threshold | entity_ambiguous_sam_two_people (3); entity_alias_sam_goldman (3); ambiguous_place_001 (3) | entity_overmerge (6) |
| `entity_mention_extractor` | `openai:gpt-5.5` | 0.934 | 0.518 | 0 | 0 | `eligible` | - | ambiguous_sam_001 (3); ambiguous_time_reference_001 (3); typos_shorthand_person_interaction_001 (3); slack_retry_event_001 (3); slack_ambiguous_entity_buttons_001 (3) | - |
| `eval_judge` | `openai:gpt-5.5` | 0.888 | 0.583 | 0 | 0 | `insufficient_sample` | semantic_evaluable_below_minimum | groundedness_metadata_claims_001 (3); groundedness_absence_claims_001 (2) | - |
| `groundedness_checker` | `openai:gpt-5.5` | 0.938 | 0.861 | 0 | 0 | `eligible` | - | recall_profile_sam_001 (3); recall_brain_cognee_conclusions_relevance_001 (1); recall_absence_claims_001 (1) | - |
| `intent_router` | `openai:gpt-5.5` | 0.877 | 0.877 | 0 | 0 | `eligible` | - | open_question_knowledge_graphs_001 (3); mixed_language_open_question_001 (3); research_question_language_intelligence_001 (3); large_table_500_rows_001 (3); slack_retry_event_001 (2) | - |
| `memory_kind_classifier` | `openai:gpt-5.5` | 0.983 | 0.943 | 0 | 0 | `eligible` | - | conversation_transcript_sam_001 (3); email_source_meeting_followup_001 (3) | - |
| `open_loop_detector` | `openai:gpt-5.5` | 0.819 | 0.819 | 0 | 0 | `failed_quality` | semantic_score_below_threshold | slack_prompt_injection_001 (3); typos_shorthand_person_interaction_001 (3); slack_conflict_buttons_001 (3); slack_no_durable_value_repair_001 (3); small_table_preferences_001 (3) | - |
| `recall_planner` | `openai:gpt-5.5` | 0.976 | 0.976 | 0 | 0 | `eligible` | - | router_recall_question (1) | - |
| `recall_synthesizer` | `openai:gpt-5.5` | 0.945 | 0.861 | 0 | 0 | `insufficient_sample` | semantic_evaluable_below_minimum | recall_profile_sam_001 (3); recall_brain_cognee_conclusions_relevance_001 (2) | - |
| `relationship_extractor` | `openai:gpt-5.5` | 0.993 | 0.981 | 0 | 0 | `eligible` | - | person_interaction_sam_bill_evans_001 (2) | - |
| `repair_option_generator` | `openai:gpt-5.5` | 1.000 | 1.000 | 0 | 0 | `eligible` | - | - | - |
| `source_classifier` | `openai:gpt-5.5` | 0.854 | 0.676 | 17 | 0 | `failed_safety` | zero_tolerance_failures_present;semantic_score_below_threshold;source_memory_split_below_threshold | slack_prompt_injection_001 (3); slack_retry_event_001 (3); slack_no_durable_value_repair_001 (3); memory_compiler_article_atomic (3); conversation_transcript_sam_001 (3) | article_url_not_classified_as_source (7); long_source_classified_as_memory (5); table_not_classified_as_table (5) |
| `source_takeaway_extractor` | `openai:gpt-5.5` | 0.710 | 0.244 | 6 | 0 | `failed_safety` | zero_tolerance_failures_present;semantic_score_below_threshold | memory_compiler_small_table (3); memory_compiler_article_atomic (3); chat_conclusion_brain_architecture_001 (3); article_url_ai_memory_001 (3); article_url_fetch_failure_001 (3) | source_invention (6) |
| `table_policy_handler` | `openai:gpt-5.5` | 0.758 | 0.222 | 8 | 0 | `failed_safety` | zero_tolerance_failures_present;semantic_score_below_threshold | memory_compiler_article_atomic (3); memory_compiler_small_table (3); research_question_language_intelligence_001 (3); chat_conclusion_brain_architecture_001 (3); article_url_ai_memory_001 (3) | small_table_must_not_drop_values (6); numeric_values_altered (2) |

## Runtime-role recommendations

Partial recommendations only.
- `intent_router`: `openai:gpt-5.5`
- `recall_planner`: `openai:gpt-5.5`

## Embedding recommendations

- none

## Judge/debug/support recommendations

- `entity_mention_extractor`: `openai:gpt-5.5`
- `groundedness_checker`: `openai:gpt-5.5`
- `memory_kind_classifier`: `openai:gpt-5.5`
- `relationship_extractor`: `openai:gpt-5.5`
- `repair_option_generator`: `openai:gpt-5.5`

## Pairwise comparisons

| Role | Model A | Model B | Shared variants | Shared semantic variants | Semantic diff | Operational diff | Schema diff | Recommendation |
|---|---|---|---:|---:|---:|---:|---:|---|
| | | | | | | | | No pairwise comparisons available. |

## Cost and latency

| Model | Role | Cost / 1k attempted | Cost / 1k successful | Cost / 1k semantic | p50 ms | p90 ms | p95 ms |
|---|---|---:|---:|---:|---:|---:|---:|
| `openai:gpt-5.5` | `atomic_card_extractor` | $14.6793 | $14.6793 | $14.6793 | 4161 | 6236 | 7072 |
| `openai:gpt-5.5` | `conflict_candidate_detector` | $9.1312 | $9.1312 | $9.1312 | 3313 | 4470 | 4857 |
| `openai:gpt-5.5` | `conflict_explainer` | $17.2020 | $17.2020 | $17.2020 | 5548 | 6438 | 6964 |
| `openai:gpt-5.5` | `debug_explainer` | $11.5012 | $11.5012 | $11.5012 | 3762 | 5969 | 6128 |
| `openai:gpt-5.5` | `durability_filter` | $4.0231 | $4.0231 | $4.0231 | 1983 | 2649 | 3389 |
| `openai:gpt-5.5` | `entity_candidate_ranker` | $9.5972 | $9.5972 | $9.5972 | 3243 | 4243 | 4410 |
| `openai:gpt-5.5` | `entity_mention_extractor` | $3.1308 | $3.1308 | $3.1308 | 1421 | 2159 | 2624 |
| `openai:gpt-5.5` | `eval_judge` | $8.6879 | $8.6879 | $8.6879 | 3272 | 4463 | 4463 |
| `openai:gpt-5.5` | `groundedness_checker` | $10.3832 | $10.3832 | $10.3832 | 3265 | 4688 | 4782 |
| `openai:gpt-5.5` | `intent_router` | $9.3567 | $9.3567 | $9.3567 | 3181 | 5642 | 6677 |
| `openai:gpt-5.5` | `memory_kind_classifier` | $4.2656 | $4.2656 | $4.2656 | 1641 | 2676 | 3179 |
| `openai:gpt-5.5` | `open_loop_detector` | $2.9596 | $2.9596 | $2.9596 | 1389 | 2129 | 2491 |
| `openai:gpt-5.5` | `recall_planner` | $10.0454 | $10.0454 | $10.0454 | 3313 | 5235 | 5658 |
| `openai:gpt-5.5` | `recall_synthesizer` | $11.2051 | $11.2051 | $11.2051 | 3512 | 5458 | 5919 |
| `openai:gpt-5.5` | `relationship_extractor` | $3.2185 | $3.2185 | $3.2185 | 1480 | 2464 | 2772 |
| `openai:gpt-5.5` | `repair_option_generator` | $5.1185 | $5.1185 | $5.1185 | 2349 | 4084 | 4621 |
| `openai:gpt-5.5` | `source_classifier` | $3.5947 | $3.5947 | $3.5947 | 1476 | 3115 | 3681 |
| `openai:gpt-5.5` | `source_takeaway_extractor` | $14.2894 | $14.2894 | $14.2894 | 3936 | 7057 | 7299 |
| `openai:gpt-5.5` | `table_policy_handler` | $14.0467 | $14.0467 | $14.0467 | 4153 | 7154 | 9600 |

## Why non-deployable, if applicable

Missing mandatory capabilities:
- conflict_handling
- entity_resolution
- memory_compiler
- recall
- slack_intake

Observed capability gaps:
- `conflict_handling`: missing eligible coverage for `conflict_candidate_detector`, `conflict_explainer`
- `entity_resolution`: missing eligible coverage for `entity_candidate_ranker`
- `memory_compiler`: missing eligible coverage for `atomic_card_extractor`, `open_loop_detector`, `table_policy_handler`, `source_takeaway_extractor`
- `recall`: missing eligible coverage for `recall_synthesizer`
- `slack_intake`: missing eligible coverage for `source_classifier`, `durability_filter`

## Next actions

- Restore mandatory coverage for: conflict_handling, entity_resolution, memory_compiler, recall, slack_intake.
- Eliminate the largest blocking failure classes first: quality_failure (242), zero_tolerance_failure (70).
- Rerun after operational issues are fixed so semantic comparisons are based on overlapping evaluable variants.
- Add or refine role-specific fixtures if a mandatory role remains unevaluable after provider issues are resolved.

## Rerun command

```bash
brain eval rerun-failed --source-json artifacts/full_model_suite_gpt55_1repeat_manual_20260508_205815/results_fine_grained_gpt55_1repeat.json --failed-manifest artifacts/full_model_suite_gpt55_1repeat_manual_20260508_205815/failed_tests.jsonl --endpoint-max-concurrency 3 --output-json artifacts/full_model_suite_gpt55_1repeat_manual_20260508_205815/results_fine_grained_gpt55_1repeat.json --overwrite
```
