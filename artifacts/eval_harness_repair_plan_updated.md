# Brain Eval Harness Repair Plan — Updated Testing Plan

## 0. Scope

This plan updates the existing fine-grained eval repair plan for the current
repo layout and code surface in `dbortolotti/brain`.

It is based on the current implementation in:

- `src/memory_stack/evals/scoring.py`
- `src/memory_stack/evals/model_runner.py`
- `src/memory_stack/evals/model_matrix.py`
- `src/memory_stack/evals/model_fixtures.py`
- `src/memory_stack/evals/cli.py`
- `brain_model_registry.yaml`

The repo already has the infrastructure needed to repair the harness:

```text
- fine-grained eval mode exists
- model registry loading exists
- fine_grained_eval_matrix support exists
- stable record_id logic exists
- failed-tests manifest generation exists
- rerun-failed overwrite flow exists
- raw/parsed output paths exist
- operational/schema/semantic flags exist
- endpoint-level concurrency exists
```

The main problem remains scoring correctness, not execution plumbing.

Current failure mode:

```text
Broad zero-tolerance checks are being applied directly to narrow fine-grained roles.
That causes role-inappropriate failures and distorts eligibility and deployability.
```

Correct implementation sequence:

```text
1. Fix role-specific scoring.
2. Add fine-to-coarse capability coverage.
3. Add fine-grained thresholds and subscore mapping.
4. Fix cost/latency aggregation and reporting.
5. Add provider-free rescore support.
6. Tighten rerun semantics coverage.
7. Clean up the fine-grained model matrix.
8. Rescore existing results before any large rerun.
```

## 1. Current repo mapping

The original draft assumed a `tests/evals/` tree. This repo uses a flat test
layout under `tests/`.

Recommended test file placement:

- scorer and zero-tolerance logic:
  - `tests/test_scoring.py`
  - or new `tests/test_scoring_fine_grained.py`
- aggregation, artifact generation, rescore, rerun:
  - `tests/test_model_eval_runner.py`
  - or new `tests/test_eval_rescore.py`
- model matrix hygiene:
  - `tests/test_model_registry.py`
  - or new `tests/test_model_matrix_fine_grained.py`

Recommended code ownership:

- scoring, thresholds, eligibility, capability coverage:
  - `src/memory_stack/evals/scoring.py`
  - or split new helper into `src/memory_stack/evals/capabilities.py`
- run rewrite / artifact regeneration / rescore:
  - `src/memory_stack/evals/model_runner.py`
- CLI command wiring:
  - `src/memory_stack/evals/cli.py`
- matrix cleanup:
  - `brain_model_registry.yaml`
  - `src/memory_stack/evals/model_matrix.py` if validation logic needs updates

## 2. Delivery slices

### Slice 1 — Scorer correctness

Goal:

```text
Fine-grained roles should only be penalized for failures they own.
```

Files:

- `src/memory_stack/evals/scoring.py`
- `tests/test_scoring.py` or `tests/test_scoring_fine_grained.py`

### Slice 2 — Capability coverage and deployability

Goal:

```text
Fine-grained runs should map to coarse runtime capabilities instead of being
marked non-deployable because broad role names were never executed directly.
```

Files:

- `src/memory_stack/evals/scoring.py`
- optional new `src/memory_stack/evals/capabilities.py`
- `tests/test_scoring.py` or new `tests/test_eval_capabilities.py`

### Slice 3 — Thresholds, subscore aliases, and aggregation

Goal:

```text
Fine-grained roles should use role-appropriate thresholds, and cost/latency
reports should contain real values.
```

Files:

- `src/memory_stack/evals/scoring.py`
- `src/memory_stack/evals/model_runner.py`
- `tests/test_scoring.py`
- `tests/test_model_eval_runner.py`

### Slice 4 — Provider-free rescore

Goal:

```text
Existing eval results should be rescored and artifacts regenerated without
calling model providers.
```

Files:

- `src/memory_stack/evals/model_runner.py`
- `src/memory_stack/evals/cli.py`
- `tests/test_model_eval_runner.py`
- optional new `tests/test_eval_rescore.py`

### Slice 5 — Matrix hygiene

Goal:

```text
Remove unsupported/undesired candidates and keep benchmark-only models limited
to benchmark-appropriate roles.
```

Files:

- `brain_model_registry.yaml`
- `tests/test_model_registry.py`

### Slice 6 — Rerun overwrite guarantees

Goal:

```text
Reruns must replace records by stable record_id and preserve all non-rerun rows.
```

Files:

- `src/memory_stack/evals/model_runner.py`
- `tests/test_model_eval_runner.py`

## 3. Scorer correctness

### 3.1 Problem

Current fixtures can carry broad zero-tolerance checks such as:

```text
source_invention
small_table_must_not_drop_values
success_receipt_missing
open_loop_missing
```

Those are useful fixture annotations, but they must not automatically apply to
every fine-grained role.

Examples:

```text
intent_router:
  should be judged on routing and command safety, not table retention

entity_mention_extractor:
  should be judged on entity extraction fidelity, not success receipt content

success_receipt_generator:
  should still fail when required receipt content is absent
```

### 3.2 Add role-specific allowed zero-tolerance map

Add a role filter in `src/memory_stack/evals/scoring.py`:

```python
ROLE_ALLOWED_ZERO_TOLERANCE_CHECKS = {
    "intent_router": {
        "wrong_intent_for_explicit_command",
        "unsafe_admin_routing",
        "unknown_for_clear_command",
    },
    "source_classifier": {
        "long_source_classified_as_memory",
        "table_not_classified_as_table",
        "article_url_not_classified_as_source",
        "source_material_as_memory_card",
    },
    "durability_filter": {
        "stores_no_durable_value_without_reason",
        "rejects_clear_family_fact",
        "rejects_clear_open_question",
    },
    "memory_kind_classifier": {
        "open_question_classified_as_basic_fact",
        "family_fact_not_classified_as_family_fact",
        "person_interaction_lost",
    },
    "atomic_card_extractor": {
        "must_not_split_twins_into_duplicate_cards",
        "open_loop_missing",
        "source_invention",
        "invented_surname",
        "invented_precise_date",
        "unsupported_inference",
    },
    "entity_mention_extractor": {
        "invented_entity",
        "missed_primary_entity",
        "wrong_entity_type",
        "invented_surname",
    },
    "entity_candidate_ranker": {
        "entity_overmerge",
        "wrong_entity_bound",
        "ambiguous_entity_auto_bound",
    },
    "relationship_extractor": {
        "invented_relationship",
        "relationship_direction_reversed",
        "numeric_values_altered",
    },
    "open_loop_detector": {
        "open_loop_missing",
        "commitment_not_detected",
        "research_question_not_detected",
    },
    "table_policy_handler": {
        "small_table_must_not_drop_values",
        "large_table_atomized_by_default",
        "numeric_values_altered",
    },
    "source_takeaway_extractor": {
        "source_invention",
        "unsupported_inference",
        "long_source_as_single_memory_card",
        "raw_email_exposed",
    },
    "conflict_candidate_detector": {
        "misses_high_confidence_conflict",
        "marks_contradiction_as_safe_current",
        "marks_additive_as_supersession",
    },
    "conflict_explainer": {
        "offers_unsafe_auto_commit",
        "omits_reject_option",
        "misstates_existing_memory",
    },
    "repair_option_generator": {
        "unsafe_repair_option",
        "missing_cancel_option",
        "missing_user_choice_for_ambiguity",
    },
    "success_receipt_generator": {
        "success_receipt_missing",
        "missing_memory_id",
        "missing_undo_action",
        "missing_entities",
    },
    "recall_planner": {
        "wrong_strategy",
        "broad_memory_dump",
        "source_query_not_routed_to_sources",
    },
    "recall_synthesizer": {
        "unsupported_inference",
        "unsupported_absence_claim",
        "stale_fact_as_current",
        "evidence_id_missing",
    },
    "groundedness_checker": {
        "unsupported_claim_labeled_grounded",
        "missing_evidence_not_detected",
    },
    "debug_explainer": {
        "raw_email_exposed",
        "admin_secret_exposed",
        "misstates_debug_state",
    },
    "eval_judge": {
        "unsafe_output_marked_safe",
        "zero_tolerance_missed",
    },
}
```

### 3.3 Filter checks before evaluation

In `zero_tolerance_failure_types()` replace direct fixture use:

```python
checks = set(fixture.zero_tolerance_checks)
```

with:

```python
raw_checks = set(fixture.zero_tolerance_checks)
allowed = ROLE_ALLOWED_ZERO_TOLERANCE_CHECKS.get(fixture.role)
checks = raw_checks & allowed if allowed is not None else raw_checks
```

Important:

```text
Do not delete broad zero-tolerance checks from fixtures.
Fixtures should remain rich.
The scorer is responsible for filtering which checks apply to a given role.
```

## 4. Capability coverage and fine-to-coarse deployability

### 4.1 Problem

Current deployability checks are still broad-role oriented:

```text
router
slack_intake
memory_compiler
conflict_classifier
recall_synthesizer
embeddings
```

But fine-grained runs exercise roles like:

```text
intent_router
source_classifier
atomic_card_extractor
entity_candidate_ranker
success_receipt_generator
```

So a fine-grained run can be declared non-deployable even when the actual
capability surface is covered.

### 4.2 Add capability mapping

Add a capability map in `src/memory_stack/evals/scoring.py` or a new
`src/memory_stack/evals/capabilities.py`:

```python
COARSE_CAPABILITIES = {
    "router": {
        "required_model_roles": ["intent_router"],
        "deterministic_roles": [],
    },
    "slack_intake": {
        "required_model_roles": [
            "source_classifier",
            "durability_filter",
            "memory_kind_classifier",
            "repair_option_generator",
            "success_receipt_generator",
        ],
        "deterministic_roles": [
            "zero_tolerance_validator",
            "commit_policy",
        ],
    },
    "memory_compiler": {
        "required_model_roles": [
            "atomic_card_extractor",
            "entity_mention_extractor",
            "relationship_extractor",
            "open_loop_detector",
            "table_policy_handler",
            "source_takeaway_extractor",
        ],
        "deterministic_roles": [
            "table_parser",
            "source_loader",
            "zero_tolerance_validator",
        ],
    },
    "entity_resolution": {
        "required_model_roles": [
            "entity_mention_extractor",
            "entity_candidate_ranker",
        ],
        "deterministic_roles": [
            "entity_final_resolver",
        ],
    },
    "conflict_handling": {
        "required_model_roles": [
            "conflict_candidate_detector",
            "conflict_explainer",
        ],
        "deterministic_roles": [
            "conflict_policy_decider",
        ],
    },
    "recall": {
        "required_model_roles": [
            "recall_planner",
            "recall_synthesizer",
        ],
        "deterministic_roles": [
            "recall_filter",
        ],
    },
    "debug": {
        "required_model_roles": [
            "debug_explainer",
        ],
        "deterministic_roles": [],
    },
    "judge": {
        "required_model_roles": [
            "eval_judge",
        ],
        "deterministic_roles": [],
    },
    "embeddings": {
        "required_model_roles": [
            "embeddings",
        ],
        "deterministic_roles": [],
        "optional_if_not_tested": True,
    },
}
```

### 4.3 Add capability coverage helper

Implement a helper like:

```python
def capability_coverage(summaries):
    ...
```

Required behavior:

```text
- collect tested roles
- collect eligible models per fine-grained role
- mark a capability eligible only if every required model role has at least one
  eligible summary
- mark embeddings as not_tested if embeddings were not part of the run
```

### 4.4 Update deployability behavior

Keep broad mode as-is.

For fine-grained mode:

```text
- derive deployability from capability coverage
- do not require literal broad role names to appear
```

## 5. Fine-grained thresholds and subscore aliases

### 5.1 Problem

The current `ROLE_THRESHOLDS` and `ROLE_SUBSCORE_ALIASES` remain broad-role
oriented. Fine-grained roles need their own thresholds and direct subscore
aliases.

### 5.2 Add fine-grained thresholds

Extend `ROLE_THRESHOLDS` with the fine-grained thresholds from the draft plan.
Keep them role-local and avoid reusing broad-role thresholds where they do not
fit the narrower responsibility.

Roles to add:

```text
intent_router
source_classifier
durability_filter
memory_kind_classifier
atomic_card_extractor
entity_mention_extractor
entity_candidate_ranker
relationship_extractor
open_loop_detector
table_policy_handler
source_takeaway_extractor
conflict_candidate_detector
conflict_explainer
repair_option_generator
success_receipt_generator
recall_planner
recall_synthesizer
groundedness_checker
debug_explainer
eval_judge
```

### 5.3 Fix alias naming

The plan should normalize aliases to actual scorer outputs:

```python
{
    "memory_card_quality": "memory_card_quality",
    "entity_safety": "entity_safety",
    "conflict_safety": "conflict_safety",
    "source_memory_split": "source_memory_split",
    "repair_quality": "repair_quality",
    "success_receipt_quality": "success_receipt_quality",
    "recall_quality": "recall_quality",
    "decision_correctness": "decision_correctness",
}
```

Do not leave stale alias names like:

```text
repair_option_usefulness
memory_card_extraction
groundedness
```

unless they are explicitly mapped on purpose for backward compatibility.

## 6. Cost and latency aggregation

### 6.1 Problem

The existing summary model only exposes `cost_per_1k_successful`, while report
analysis would benefit from attempted and semantic-evaluable cost views too.

### 6.2 Extend summary fields

Add to `ModelRoleSummary`:

```python
cost_per_1k_attempted: float | None
cost_per_1k_successful: float | None
cost_per_1k_semantic: float | None
```

### 6.3 Compute against the correct row sets

In `aggregate_model_role_records()` compute:

```text
- attempted rows: all rows
- successful rows: operational_success
- semantic rows: semantic_evaluable
```

Then derive:

```text
cost_per_1k_attempted
cost_per_1k_successful
cost_per_1k_semantic
```

Latency should use successful rows only:

```python
latency_values = [
    float(r.latency_ms)
    for r in successful_rows
    if r.latency_ms is not None
]
```

Update CSV and summary report generation so the new cost columns appear in
artifact outputs where appropriate.

## 7. Provider-free rescore command

### 7.1 Objective

Most current fine-grained failures may be scoring artifacts. Add a rescore path
that rewrites records and artifacts without provider calls.

### 7.2 CLI shape

Add a new eval CLI command in `src/memory_stack/evals/cli.py`:

```bash
brain eval rescore \
  --source-json eval_runs/fine_grained/results.json \
  --output-json eval_runs/fine_grained/results.json \
  --overwrite
```

### 7.3 Behavior

Required behavior:

```text
- load existing canonical records
- accept both JSON array files and JSONL files
- recompute schema_valid
- recompute semantic_evaluable
- recompute subscores
- recompute quality_score
- recompute zero_tolerance_failure and zero_tolerance_failure_types
- recompute failure_class and failure_reason_codes
- preserve raw_output_path and parsed_output_path
- reassign failure_number
- atomically rewrite output records
- regenerate summary.md
- regenerate failed_tests.jsonl
- regenerate failed_tests.md
- regenerate model_role_summary.csv
- regenerate cost_latency.csv
- regenerate zero_tolerance_summary.csv
```

Implementation preference:

```text
Use existing record read/write helpers where possible instead of introducing a
second record serialization path.
```

## 8. Rerun semantics validation

The current rerun flow is structurally close to correct. The next step is to
lock it down with tests.

Required guarantees:

```text
- canonical records are loaded from source JSON
- failed manifest rows are filtered by CLI options
- rerun rows replace canonical rows by stable record_id
- non-rerun rows are preserved
- output is written atomically
- artifacts are regenerated from the merged canonical record set
```

## 9. Matrix hygiene

### 9.1 Remove Mistral

Remove:

```text
aws-bedrock:mistral.ministral-3-14b-instruct
```

from the fine-grained matrix and any tests that still expect it.

### 9.2 Keep GPT-5.5-high in benchmark roles only

Allowed roles:

```text
atomic_card_extractor
source_takeaway_extractor
entity_candidate_ranker
conflict_candidate_detector
recall_synthesizer
groundedness_checker
eval_judge
```

### 9.3 Apply the lean matrix update

Use the candidate list from the draft plan as the target matrix revision for
`brain_model_registry.yaml`.

## 10. Test plan

### 10.1 Group A — Role-specific zero-tolerance filtering

Implement:

- router ignores table/source checks
- entity mention extractor ignores receipt checks
- success receipt generator still fails missing receipt

Suggested home:

- `tests/test_scoring.py`
- or new `tests/test_scoring_fine_grained.py`

### 10.2 Group B — Fine-to-coarse capability coverage

Implement:

- router capability satisfied by `intent_router`
- slack intake missing when one component is absent
- embeddings marked `not_tested` when not part of a fine-grained run

Suggested home:

- `tests/test_scoring.py`
- or new `tests/test_eval_capabilities.py`

### 10.3 Group C — Cost/latency aggregation

Implement:

- `cost_per_1k_successful` remains correct
- new attempted/semantic cost metrics compute correctly
- latency p50/p90/p95 derive from successful rows

Suggested home:

- `tests/test_model_eval_runner.py`
- or `tests/test_scoring.py`

### 10.4 Group D — Rescore command

Implement:

- rescore path does not call providers
- rescore removes role-inappropriate zero-tolerance failures
- rescore regenerates artifacts
- rescore supports JSON arrays and JSONL

Suggested home:

- `tests/test_model_eval_runner.py`
- or new `tests/test_eval_rescore.py`

### 10.5 Group E — Rerun overwrite semantics

Implement:

- rerun replaces by `record_id`
- non-rerun rows are preserved
- artifact regeneration occurs from merged rows

Suggested home:

- `tests/test_model_eval_runner.py`

### 10.6 Group F — Model matrix hygiene

Implement:

- Mistral absent from the fine-grained matrix
- GPT-5.5-high only appears in benchmark-appropriate roles

Suggested home:

- `tests/test_model_registry.py`
- or new `tests/test_model_matrix_fine_grained.py`

## 11. Post-implementation commands

### 11.1 Rescore existing results first

```bash
brain eval rescore \
  --source-json eval_runs/fine_grained/results.json \
  --output-json eval_runs/fine_grained/results.json \
  --overwrite
```

### 11.2 Inspect generated artifacts

```bash
cat eval_runs/fine_grained/summary.md
cat eval_runs/fine_grained/failed_tests.md
cat eval_runs/fine_grained/model_role_summary.csv
cat eval_runs/fine_grained/cost_latency.csv
cat eval_runs/fine_grained/zero_tolerance_summary.csv
```

### 11.3 Rerun genuine provider/schema failures only

Use the actual existing CLI flag name:

```bash
brain eval rerun-failed \
  --source-json eval_runs/fine_grained/results.json \
  --failed-manifest eval_runs/fine_grained/failed_tests.jsonl \
  --failure-class json_parse_error \
  --endpoint-max-concurrency 10 \
  --output-json eval_runs/fine_grained/results.json \
  --overwrite
```

Then:

```bash
brain eval rerun-failed \
  --source-json eval_runs/fine_grained/results.json \
  --failed-manifest eval_runs/fine_grained/failed_tests.jsonl \
  --failure-class timeout \
  --endpoint-max-concurrency 10 \
  --output-json eval_runs/fine_grained/results.json \
  --overwrite
```

Do not rerun zero-tolerance failures until after rescoring.

## 12. Acceptance criteria

This work is complete when:

```text
1. intent_router is no longer failed for table/source/open-loop failures.
2. entity_mention_extractor is no longer failed for receipt/source/table failures.
3. success_receipt_generator still fails missing receipt.
4. fine-grained deployability maps correctly to coarse capabilities.
5. embeddings are not marked missing when they were not part of the run.
6. cost/latency CSVs contain real values.
7. rescore works without provider calls.
8. rerun-failed overwrites records by stable record_id.
9. non-rerun records are preserved.
10. Mistral is absent from the fine-grained matrix.
11. GPT-5.5-high appears only in benchmark-appropriate roles.
12. summary.md clearly distinguishes:
    - attempted
    - operationally successful
    - schema-valid
    - semantically evaluable
    - eligible / passed
    - recommended
```

## 13. Final recommendation

Do not rerun the full fine-grained matrix until the scorer is patched.

Current correct sequence:

```text
1. Patch scorer.
2. Rescore existing results without provider calls.
3. Inspect updated eligibility and capability coverage.
4. Rerun only genuine provider/schema failures.
5. Run a smaller fresh matrix only if gaps remain.
```
