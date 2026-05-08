# Brain Fine-Grained Model Eval Test Plan — Coding Agent Instructions

## 0. Objective

Implement the next version of the Brain model-evaluation harness using **fine-grained roles**, not the previous broad roles.

The previous broad roles were:

```text
slack_intake
memory_compiler
conflict_classifier
entity_resolution
recall_synthesizer
```

Those were useful diagnostically, but too coarse. The latest evals showed that multiple model families failed the same hard cases, especially:

```text
- high-confidence conflict handling
- entity over-merge
- source invention
- table-value loss
- missing success receipts
- missing open loops
- invented surnames/dates/calendar events
```

Therefore, the next framework must test narrower model capabilities and move final safety decisions into deterministic backend policy.

Core principle:

```text
Model proposes.
Backend validates.
Backend decides safety.
User confirms ambiguity.
Model explains and summarizes.
```

---

## 1. Required model-eval behaviour

The harness must:

```text
1. Test fine-grained roles.
2. Test only the appropriate models for each role.
3. Log every attempted test, including success/failure status and failure reason.
4. Generate a failed-tests manifest at the end of each run.
5. Support rerunning only failed tests from that manifest.
6. When rerunning, write back to the original JSON file and overwrite the records being rerun.
7. Preserve stable IDs so records can be replaced deterministically.
8. Produce aggregate reports from the updated canonical JSON.
```

---

## 2. Mandatory logging requirements

Every attempted test must produce a record, even if the provider call fails before a response is received.

### 2.1 Per-attempt record fields

Each eval record must contain:

```json
{
  "record_id": "stable deterministic ID",
  "run_id": "eval_YYYYMMDD_HHMMSS",
  "rerun_of_run_id": "optional prior run id",
  "fixture_set_version": "brain-model-test-v2",
  "policy_version": "memory-policy-v1",

  "model": "provider:model-id",
  "provider": "openai | google | anthropic | groq | aws-bedrock | voyage",
  "role": "fine_grained_role",
  "fixture_id": "fixture id",
  "scenario_group": "scenario group",
  "variant_id": "base | context | punctuation | ...",
  "repeat_idx": 0,

  "status": "ok | fail | schema_fail | schema_invalid | skipped",
  "failure_class": "none | provider_error | authentication_error | quota_error | rate_limit_error | timeout | unsupported_model | transport_error | schema_invalid | json_parse_error | policy_validation_failure | quality_failure | zero_tolerance_failure",
  "failure_number": "integer monotonically assigned within run, null if no failure",
  "failure_message": "string or null",
  "failure_reason_codes": [],

  "operational_success": true,
  "json_parseable": true,
  "schema_valid": true,
  "semantic_evaluable": true,

  "quality_score": 0.0,
  "subscores": {},

  "zero_tolerance_failure": false,
  "zero_tolerance_failure_types": [],

  "input_tokens": 0,
  "output_tokens": 0,
  "estimated_cost_usd": 0.0,
  "latency_ms": 0.0,

  "raw_output_path": "path or null",
  "parsed_output_path": "path or null",
  "notes": []
}
```

### 2.2 Stable `record_id`

The `record_id` must be deterministic and must not depend on run timestamp.

Use:

```text
record_id = sha256(
  fixture_set_version
  + policy_version
  + model
  + role
  + fixture_id
  + variant_id
  + repeat_idx
)
```

This is critical for reruns.

### 2.3 Failure number

Assign `failure_number` to every failed attempt.

Example:

```text
failure_number: 172
failure_class: json_parse_error
failure_message: "output did not contain a JSON object"
```

The failure number should appear both in:

```text
- the canonical JSON
- the failed-tests manifest
- the markdown report
```

This lets a human inspect logs and trace a failed record.

---

## 3. Failure taxonomy

Use the following failure classes.

```python
class FailureClass(str, Enum):
    NONE = "none"

    # Operational failures
    PROVIDER_ERROR = "provider_error"
    AUTHENTICATION_ERROR = "authentication_error"
    QUOTA_ERROR = "quota_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    TIMEOUT = "timeout"
    UNSUPPORTED_MODEL = "unsupported_model"
    TRANSPORT_ERROR = "transport_error"

    # Output/schema failures
    SCHEMA_INVALID = "schema_invalid"
    JSON_PARSE_ERROR = "json_parse_error"
    STRUCTURED_OUTPUT_INVALID = "structured_output_invalid"

    # Brain policy / quality failures
    POLICY_VALIDATION_FAILURE = "policy_validation_failure"
    QUALITY_FAILURE = "quality_failure"
    ZERO_TOLERANCE_FAILURE = "zero_tolerance_failure"
```

Important distinction:

```text
Operational failure:
  Model was not semantically evaluated.

Schema failure:
  Provider responded, but output format was unusable.

Quality failure:
  Output was parseable/evaluable but semantically poor.

Zero-tolerance failure:
  Output violated a hard Brain safety rule.
```

---

## 4. Failed-tests manifest

At the end of every run, generate:

```text
eval_runs/<run_id>/failed_tests.jsonl
eval_runs/<run_id>/failed_tests.md
```

### 4.1 `failed_tests.jsonl`

Each row must be enough to rerun the exact failed test:

```json
{
  "record_id": "stable id",
  "failure_number": 172,
  "run_id": "eval_20260507_123000",
  "model": "openai:gpt-5.4-nano",
  "role": "atomic_card_extractor",
  "fixture_id": "memory_compiler_article_atomic",
  "variant_id": "context",
  "repeat_idx": 2,
  "failure_class": "zero_tolerance_failure",
  "failure_reason_codes": ["source_invention"],
  "failure_message": "Model invented source-backed claim not present in source.",
  "raw_output_path": "...",
  "parsed_output_path": "..."
}
```

### 4.2 `failed_tests.md`

The markdown file should group failures by:

```text
- failure_class
- role
- fixture_id
- model
```

Example:

```markdown
# Failed tests

## zero_tolerance_failure

### atomic_card_extractor / article_url_ai_memory_001

| Failure # | Model | Variant | Repeat | Reason |
|---:|---|---|---:|---|
| 172 | openai:gpt-5.4-nano | context | 2 | source_invention |
```

### 4.3 Rerun command

The report should print a command such as:

```bash
brain eval rerun-failed \
  --source-json eval_runs/eval_20260507_123000/results.json \
  --failed-manifest eval_runs/eval_20260507_123000/failed_tests.jsonl \
  --concurrency 10 \
  --output-json eval_runs/eval_20260507_123000/results.json \
  --overwrite
```

---

## 5. Rerun semantics

### 5.1 Required behaviour

When rerunning a subset:

```text
- Load the original canonical JSON.
- Load the failed-tests manifest.
- Rerun only listed records.
- Replace records in the original JSON by matching `record_id`.
- Preserve all records not being rerun.
- Write atomically.
```

### 5.2 Atomic write

Do not risk corrupting the canonical JSON.

Implementation:

```text
1. Read original JSON.
2. Build dict by record_id.
3. Rerun failed tests.
4. Replace matching record_id entries.
5. Write to temp file.
6. Validate JSON.
7. Rename temp file over original file.
8. Regenerate summary/report/failed manifest.
```

### 5.3 Rerun metadata

Each replacement record should include:

```json
{
  "rerun_of_run_id": "eval_20260507_123000",
  "rerun_timestamp": "2026-05-07T..."
}
```

---

## 6. Fine-grained roles

The next evaluation framework should test these roles.

### 6.1 `intent_router`

Classifies user message intent.

Allowed intents:

```text
remember
ingest_source
recall
profile_entity
list_open_loops
review_recent
debug_inspect
admin
unknown
```

Mostly deterministic. Model only handles free-form ambiguity.

---

### 6.2 `source_classifier`

Classifies input as:

```text
memory
source
article
transcript
markdown
table
chat_log
email
junk
```

Hard rules:

```text
long text       → source first
transcript      → source + extracted cards
article URL     → source + extracted takeaways
table           → source/data + table policy
short fact      → memory only
junk            → reject/ask
```

---

### 6.3 `durability_filter`

Decides whether an input has durable personal-memory value.

Examples:

```text
"Today’s weather is cloudy." → reject unless reason supplied
"I want to learn more about knowledge graphs." → durable
"Sam likes Bill Evans." → durable
```

---

### 6.4 `memory_kind_classifier`

Classifies memory kind only.

Allowed kinds:

```text
basic_fact
family_fact
person_fact
person_interaction
preference
decision
idea
open_question
research_question
article_note
key_takeaway
chat_conclusion
conversation_summary
experience
place_note
table_note
source_summary
project_state
commitment
```

---

### 6.5 `atomic_card_extractor`

Extracts atomic durable memory cards from already-classified input.

Scoring:

```text
atomicity
completeness
no invented details
no duplicate cards
confidence calibration
```

---

### 6.6 `entity_mention_extractor`

Extracts entity mentions only.

This role must not resolve/merge entities.

---

### 6.7 `entity_candidate_ranker`

Ranks candidate entities for a mention.

Backend owns final decision.

Hard backend rule:

```text
multiple plausible candidates → ask user
low confidence                → ask or create separate entity
exact/alias match             → bind
```

---

### 6.8 `relationship_extractor`

Extracts proposed relationships.

Example:

```text
Sam from Goldman mentioned that he likes Bill Evans.
```

Expected relationships:

```text
Sam from Goldman --likes--> Bill Evans
Sam from Goldman --associated_with--> Goldman
```

---

### 6.9 `open_loop_detector`

Detects research questions, follow-ups, and commitments.

Backend rule:

```text
if kind in {open_question, research_question, commitment, follow_up}:
  open_loop row is required
```

---

### 6.10 `table_policy_handler`

Decides small/large table handling.

Backend parser should be deterministic.

Rules:

```text
small table:
  preserve original table
  parse rows
  create table_note
  do not create one card per row by default

large table:
  source/data + schema summary
  do not atomize rows
```

---

### 6.11 `source_takeaway_extractor`

Extracts source-backed takeaways, open questions, and article notes.

Hard rules:

```text
do not invent source content
preserve provenance
separate source-backed facts from user reaction
```

---

### 6.12 `conflict_candidate_detector`

Detects possible conflicts.

This role must not decide final write action.

---

### 6.13 Deterministic `conflict_policy_decider`

Do not model-evaluate this as an autonomous LLM.

Rules:

```text
high-confidence conflict → needs_user_choice
explicit correction       → propose_supersession
duplicate                 → link/ignore
additive                  → keep both
contradiction             → mark conflicted or ask
```

---

### 6.14 `conflict_explainer`

Generates user-facing conflict explanation and Slack options after deterministic policy has constrained the allowed actions.

---

### 6.15 `repair_option_generator`

Generates bounded repair options.

Examples:

```text
ambiguous entity → choose candidate / create new / cancel
long source      → store source only / source + extract / cancel
bad memory       → rewrite / cancel
```

Backend must validate repair options.

---

### 6.16 `success_receipt_generator`

Generates explicit receipt after commit.

Preferred: deterministic template.

Required fields:

```text
memory kind
statement
confidence
entities
relationships
memory ID
source ID if relevant
Inspect / Undo / Mark wrong actions
```

---

### 6.17 `recall_planner`

Plans retrieval strategy:

```text
profile
source_search
open_loop_search
memory_search
debug
```

---

### 6.18 Deterministic `recall_filter`

Filters retrieved records.

Rules:

```text
exclude deleted by default
exclude superseded unless requested
exclude unrelated memories
include conflicts separately
source-backed query requires source evidence
```

---

### 6.19 `recall_synthesizer`

Synthesizes already-filtered evidence into a grounded answer.

---

### 6.20 `groundedness_checker`

Checks whether a recall answer is supported by evidence.

Hybrid:

```text
deterministic checks for evidence IDs and stale/deleted facts
judge model for fuzzy completeness / overstatement
```

---

### 6.21 `debug_explainer`

Explains recall/debug state.

---

### 6.22 `eval_judge`

Offline judge only.

Use for:

```text
repair usefulness
summary completeness
groundedness nuance
quality comparison
```

Do not use for hard policy decisions.

---

## 7. Which models to test for which role

Do not test every model on every role.

Use the following targeted matrix.

```yaml
intent_router:
  - openai:gpt-5-nano
  - google:gemini-2.5-flash-lite
  - groq:llama-3.1-8b-instant

source_classifier:
  - openai:gpt-5-nano
  - openai:gpt-5.4-nano
  - google:gemini-2.5-flash-lite
  - aws-bedrock:mistral.ministral-3-14b-instruct

durability_filter:
  - openai:gpt-5.4-nano
  - openai:gpt-5.4-mini
  - google:gemini-2.5-flash-lite
  - aws-bedrock:mistral.ministral-3-14b-instruct

memory_kind_classifier:
  - openai:gpt-5-nano
  - openai:gpt-5.4-nano
  - google:gemini-2.5-flash-lite
  - aws-bedrock:mistral.ministral-3-14b-instruct

atomic_card_extractor:
  - openai:gpt-5.4-nano
  - openai:gpt-5.4-mini
  - openai:gpt-5.5-high
  - google:gemini-2.5-flash-lite
  - aws-bedrock:mistral.ministral-3-14b-instruct
  - groq:llama-3.3-70b-versatile

entity_mention_extractor:
  - openai:gpt-5.4-nano
  - openai:gpt-5.4-mini
  - google:gemini-2.5-flash-lite
  - aws-bedrock:mistral.ministral-3-14b-instruct

entity_candidate_ranker:
  - openai:gpt-5.4-nano
  - openai:gpt-5.4-mini
  - openai:gpt-5.5-high
  - google:gemini-2.5-flash-lite
  - anthropic:claude-haiku-4-5

relationship_extractor:
  - openai:gpt-5.4-nano
  - openai:gpt-5.4-mini
  - google:gemini-2.5-flash-lite
  - aws-bedrock:mistral.ministral-3-14b-instruct
  - groq:llama-3.3-70b-versatile

open_loop_detector:
  - openai:gpt-5.4-nano
  - openai:gpt-5.4-mini
  - google:gemini-2.5-flash-lite
  - aws-bedrock:mistral.ministral-3-14b-instruct

table_policy_handler:
  - openai:gpt-5.4-nano
  - openai:gpt-5.4-mini
  - google:gemini-2.5-flash-lite
  - aws-bedrock:mistral.ministral-3-14b-instruct

source_takeaway_extractor:
  - openai:gpt-5.4-nano
  - openai:gpt-5.4-mini
  - openai:gpt-5.5-high
  - google:gemini-2.5-flash-lite
  - google:gemini-2.5-flash
  - aws-bedrock:mistral.ministral-3-14b-instruct

conflict_candidate_detector:
  - openai:gpt-5.4-nano
  - openai:gpt-5.4-mini
  - openai:gpt-5.5-high
  - google:gemini-2.5-flash-lite
  - aws-bedrock:mistral.ministral-3-14b-instruct
  - groq:llama-3.3-70b-versatile

conflict_explainer:
  - openai:gpt-5.4-nano
  - openai:gpt-5.4-mini
  - google:gemini-2.5-flash-lite
  - anthropic:claude-haiku-4-5

repair_option_generator:
  - openai:gpt-5.4-nano
  - openai:gpt-5.4-mini
  - google:gemini-2.5-flash-lite
  - aws-bedrock:mistral.ministral-3-14b-instruct

success_receipt_generator:
  - openai:gpt-5-nano
  - openai:gpt-5.4-nano
  - google:gemini-2.5-flash-lite

recall_planner:
  - openai:gpt-5.4-nano
  - openai:gpt-5.4-mini
  - google:gemini-2.5-flash-lite
  - aws-bedrock:mistral.ministral-3-14b-instruct

recall_synthesizer:
  - google:gemini-2.5-flash-lite
  - groq:llama-3.3-70b-versatile
  - openai:gpt-5.4-mini
  - openai:gpt-5.4-nano
  - anthropic:claude-haiku-4-5

groundedness_checker:
  - openai:gpt-5.4-low
  - openai:gpt-5.4
  - openai:gpt-5.5-high
  - anthropic:claude-sonnet-4-6

debug_explainer:
  - openai:gpt-5.4-low
  - openai:gpt-5.4-mini
  - google:gemini-2.5-flash-lite
  - anthropic:claude-haiku-4-5

eval_judge:
  - openai:gpt-5.4-low
  - openai:gpt-5.4
  - openai:gpt-5.5
  - openai:gpt-5.5-high
  - anthropic:claude-sonnet-4-6
```

---

## 8. Models to skip in next fine-grained run

Do not include these until operational issues are fixed:

```text
openai:gpt-5.5-xhigh
google:gemini-3.1-pro-preview
google:gemini-3.1-pro-preview-low
google:gemini-3.1-pro-preview-medium
google:gemini-3.1-pro-preview-high
aws-bedrock:nvidia.nemotron-super-3-120b
```

Reason:

```text
Too many quota/provider/timeout failures in latest broad runs.
They do not give clean semantic evidence yet.
```

---

## 9. Required CLI behaviour

### 9.1 Full fine-grained run

```bash
brain eval models \
  --registry brain_model_registry.yaml \
  --fixture-set brain-model-test-v2 \
  --mode fine-grained \
  --concurrency 10 \
  --repeat 3 \
  --output-json eval_runs/fine_grained_$(date +%Y%m%d_%H%M%S)/results.json
```

### 9.2 Rerun failed tests

```bash
brain eval rerun-failed \
  --source-json eval_runs/fine_grained_YYYYMMDD_HHMMSS/results.json \
  --failed-manifest eval_runs/fine_grained_YYYYMMDD_HHMMSS/failed_tests.jsonl \
  --concurrency 10 \
  --output-json eval_runs/fine_grained_YYYYMMDD_HHMMSS/results.json \
  --overwrite
```

### 9.3 Rerun selected failure class

```bash
brain eval rerun-failed \
  --source-json eval_runs/fine_grained_YYYYMMDD_HHMMSS/results.json \
  --failed-manifest eval_runs/fine_grained_YYYYMMDD_HHMMSS/failed_tests.jsonl \
  --failure-class json_parse_error \
  --concurrency 10 \
  --output-json eval_runs/fine_grained_YYYYMMDD_HHMMSS/results.json \
  --overwrite
```

### 9.4 Rerun selected role

```bash
brain eval rerun-failed \
  --source-json eval_runs/fine_grained_YYYYMMDD_HHMMSS/results.json \
  --failed-manifest eval_runs/fine_grained_YYYYMMDD_HHMMSS/failed_tests.jsonl \
  --role atomic_card_extractor \
  --concurrency 10 \
  --output-json eval_runs/fine_grained_YYYYMMDD_HHMMSS/results.json \
  --overwrite
```

---

## 10. Report requirements

Every run should generate:

```text
results.json
failed_tests.jsonl
failed_tests.md
summary.md
cost_latency.csv
model_role_summary.csv
zero_tolerance_summary.csv
```

### 10.1 `summary.md` must include

```text
Executive verdict
Deployability status
Roles tested
Models tested
Operational failures by provider/model
Schema failures
Zero-tolerance failures
Fine-grained role winners
Cost/latency by role
Failed tests manifest location
Rerun command
```

### 10.2 Fine-grained role recommendation format

```markdown
## Role recommendations

| Role | Recommended model | Fallback | Status | Reason |
|---|---|---|---|---|
| intent_router | gpt-5-nano | gemini-flash-lite | deployable | zero failures, reliable schema |
| atomic_card_extractor | none | none | not deployable | source invention failures |
```

---

## 11. Acceptance criteria

This patch is complete when:

```text
1. Fine-grained roles are implemented as separate eval roles.
2. The targeted model-role matrix is loaded from config.
3. Every attempted test writes a record.
4. Failed attempts have failure_number and failure_class.
5. failed_tests.jsonl and failed_tests.md are generated.
6. Rerun command can rerun failed tests only.
7. Rerun overwrites matching records in the original JSON using record_id.
8. Summary report reflects the updated canonical JSON.
9. Operational failures are not scored as semantic quality failures.
10. Deterministic backend roles are not treated as autonomous model roles.
```

---

## 12. Final instruction

Do not run another broad all-model/all-role bakeoff until this fine-grained framework is in place.

The next useful evaluation should answer:

```text
Which cheap model is good enough for each narrow role?
Which roles require deterministic backend policy?
Which premium model is worth keeping only as judge/tie-break?
```

Not:

```text
Which single model can do all of Brain?
```
