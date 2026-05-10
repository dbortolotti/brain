# Post Fine-Grained Tests — State of Play

## Executive summary

The fine-grained model-eval harness is now producing useful signal.

The earlier broad-role evals showed that no single model could safely handle the full write path. The fine-grained split has confirmed the right direction: some narrow roles are now passing, while several write-path roles remain blocked by either real safety failures or role/scorer-contract mismatches.

Current deployability:

```text
Deployable full Brain stack: NO
```

Current genuinely eligible fine-grained model-role pairs:

```text
intent_router              → openai:gpt-5-nano
entity_mention_extractor   → openai:gpt-5.4-mini
```

Likely near-eligible after more samples or small implementation changes:

```text
debug_explainer            → google:gemini-2.5-flash-lite
eval_judge                 → openai:gpt-5.5
success_receipt_generator  → deterministic template, optionally polished by gpt-5-nano
```

Still materially failing:

```text
conflict_candidate_detector
conflict_explainer
atomic_card_extractor
recall_synthesizer
source_classifier, as currently scored
durability_filter, at least for Gemini Flash-Lite
```

The next work should be **targeted role fixes and selective reruns**, not another broad matrix.

---

## 1. What changed since the broad-role tests

The original broad roles were too coarse:

```text
slack_intake
memory_compiler
conflict_classifier
entity_resolution
recall_synthesizer
```

They mixed many responsibilities into a single model call, which made model selection hard to interpret.

The new fine-grained decomposition is better:

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

The split has already produced one clear result: models can pass narrow extraction/routing roles where they previously failed broad write-path roles.

---

## 2. Current reliable conclusions

### 2.1 Eligible role: `intent_router`

```text
Recommended default:
  openai:gpt-5-nano

Challenger:
  google:gemini-2.5-flash-lite
```

Current interpretation:

```text
gpt-5-nano is good enough as the model fallback for free-form routing.
Explicit commands should still be routed deterministically.
```

Production shape:

```text
/brain remember → deterministic
/brain recall   → deterministic
/brain profile  → deterministic
free-form       → gpt-5-nano fallback
```

Use `gpt-5-nano` only where deterministic command parsing cannot decide.

---

### 2.2 Eligible role: `entity_mention_extractor`

```text
Recommended default:
  openai:gpt-5.4-mini

Cheaper challenger:
  openai:gpt-5.4-nano
```

Current interpretation:

```text
gpt-5.4-mini is currently the strongest passed candidate for extracting entity mentions.
```

Important boundary:

```text
This does not mean gpt-5.4-mini should perform final entity resolution.
```

Entity handling should remain:

```text
entity_mention_extractor:
  model-assisted

entity_candidate_ranker:
  model-assisted, still needs a passing model

entity_final_resolver:
  deterministic / user-confirmed
```

Backend rule:

```text
exact match      → bind
alias match      → bind
multiple matches → ask user
low confidence   → ask or create separate entity
```

---

## 3. Roles that look close

### 3.1 `debug_explainer`

Current best signal:

```text
google:gemini-2.5-flash-lite
```

Status:

```text
promising, but insufficient sample
```

Interpretation:

```text
Gemini Flash-Lite looks cheap and useful for debug explanations.
Add samples rather than changing model first.
```

Suggested next run:

```yaml
debug_explainer:
  - google:gemini-2.5-flash-lite   # add more samples
  - openai:gpt-5.4-mini            # optional comparison
  - openai:gpt-5.5                 # benchmark only if needed
```

---

### 3.2 `eval_judge`

Current best signal:

```text
openai:gpt-5.5
```

Status:

```text
promising, but insufficient sample
```

Interpretation:

```text
GPT-5.5 is plausible as a judge / benchmark model.
It should not be used in routine runtime paths.
```

Suggested next run:

```yaml
eval_judge:
  - openai:gpt-5.5
  - openai:gpt-5.5-high
  - openai:gpt-5.4-low
  - anthropic:claude-sonnet-4-6
```

Use judge models for:

```text
- offline eval scoring
- audit of hard examples
- tie-breaks
- benchmark comparison
```

Do not use judge models to patch unsafe runtime logic.

---

### 3.3 `success_receipt_generator`

Current best signal:

```text
openai:gpt-5-nano
```

Status:

```text
close, but has safety failures
```

Recommendation:

```text
Make success receipts deterministic.
```

Reason:

```text
A receipt is a contract, not a creative task.
```

Required receipt fields:

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

Updated implementation direction:

```text
success_receipt_generator:
  llm-owned, with backend grounding validation
```

The LLM-promotion battery supersedes the older deterministic-template recommendation for this role.

---

## 4. Roles still failing materially

### 4.1 `conflict_candidate_detector`

Observed issue:

```text
many zero-tolerance failures
main failure: silent_high_confidence_overwrite
```

Interpretation:

```text
The role is still too close to policy decision-making.
```

Desired role contract:

```json
{
  "possible_conflict": true,
  "conflict_type": "duplicate | additive | possible_supersession | possible_contradiction | correction | none",
  "affected_memory_ids": [],
  "requires_user_choice": true
}
```

The model should not decide:

```text
commit_success
overwrite
supersede automatically
mark current
```

Backend should own:

```text
high-confidence conflict → needs_user_choice
possible supersession     → propose, do not auto-commit
duplicate                 → link/ignore
contradiction             → mark conflicted or ask
```

Next step:

```text
Rewrite fixture expectations and output schema so this role is detection-only.
Then rerun.
```

---

### 4.2 `conflict_explainer`

Observed issue:

```text
unsafe options / silent overwrite-style failures still appear
```

Interpretation:

```text
The model is probably being asked to generate or choose actions.
```

Correct contract:

```text
Backend provides the allowed actions.
Model only phrases the explanation.
```

Model input should include:

```json
{
  "safe_action_space": [
    "approve_supersession",
    "keep_both",
    "reject_new",
    "edit"
  ]
}
```

Model output should not introduce new actions.

Next step:

```text
Constrain conflict_explainer to backend-provided buttons.
Fail if it invents an action outside the safe_action_space.
```

---

### 4.3 `source_classifier`

Current observation:

```text
high semantic score
but non-trivial zero-tolerance failures
```

This is suspicious.

A pure classifier should not fail for:

```text
source_invention
small_table_must_not_drop_values
raw_email_exposed
long_source_as_single_memory_card
```

unless it is also producing extraction or commit decisions.

Correct role contract:

```json
{
  "input_class": "memory | source | table | article | transcript | markdown | email | junk",
  "source_kind": "article | transcript | markdown | pdf | email | table | chat_log | other | null",
  "should_create_source": true,
  "should_extract_memories": true,
  "confidence": "low | medium | high",
  "reason_codes": []
}
```

Next step:

```text
Audit source_classifier zero-tolerance mapping.
It should be judged on classification, not extraction fidelity.
```

Possible source_classifier-specific zero-tolerance checks:

```text
long_source_classified_as_memory
table_not_classified_as_table
article_url_not_classified_as_source
email_not_classified_as_email
junk_not_rejected
```

---

### 4.4 `durability_filter`

Current observation:

```text
Gemini Flash-Lite has no major safety issue but fails quality.
```

Interpretation:

```text
Gemini may not be strong enough for durable-vs-junk judgement, or the fixture contract is still misaligned.
```

Next tests:

```yaml
durability_filter:
  - openai:gpt-5.4-nano
  - openai:gpt-5.4-mini
  - google:gemini-2.5-flash-lite
```

Role output should be simple:

```json
{
  "durable": true,
  "memory_value": "none | low | medium | high",
  "reason_codes": [],
  "repair_options": []
}
```

---

### 4.5 `atomic_card_extractor`

Current observation:

```text
Gemini Flash-Lite fails; sample is small and hard-fixture-heavy.
```

Interpretation:

```text
This is a core extraction role and likely needs stronger models.
```

Next tests:

```yaml
atomic_card_extractor:
  - openai:gpt-5.4-mini
  - openai:gpt-5.5-high
  - google:gemini-2.5-flash-lite
```

Expected scoring dimensions:

```text
atomicity
completeness
no invented details
no duplicate cards
confidence calibration
source-memory split where relevant
```

---

### 4.6 `recall_synthesizer`

Current observation:

```text
openai:gpt-5.5 has safety failures
top issues: unsupported_absence_claim, irrelevant_memory_dump
```

Interpretation:

```text
This is a genuine concern.
```

Recall synthesis must not:

```text
make unsupported absence claims
return irrelevant memory dumps
treat stale/superseded facts as current
hide uncertainty
```

Before changing model, verify retrieval/filtering contract:

```text
recall_planner → should produce tight retrieval plan
recall_filter  → deterministic; excludes deleted/superseded/unrelated records
recall_synthesizer → only synthesizes already-filtered evidence
```

Next tests:

```yaml
recall_synthesizer:
  - google:gemini-2.5-flash-lite
  - openai:gpt-5.4-mini
  - openai:gpt-5.5
```

Also test `recall_filter` deterministically; do not leave filtering to the model.

---

## 5. Coarse capability coverage

Current coarse capability state:

```text
router:
  covered by intent_router → gpt-5-nano

entity_resolution:
  partially covered
  entity_mention_extractor → gpt-5.4-mini
  missing entity_candidate_ranker
  final resolver must remain deterministic/user-confirmed

slack_intake:
  not covered
  missing or failing source_classifier, durability_filter, success_receipt_generator

memory_compiler:
  not covered
  missing/failing atomic_card_extractor, source_takeaway_extractor, etc.

conflict_handling:
  not covered
  conflict roles failing

recall:
  not covered
  recall_synthesizer failing safety

debug:
  likely close
  needs more samples

judge:
  likely close
  needs more samples

embeddings:
  not evaluated in this fine-grained run
```

---

## 6. Model policy going forward

### Keep in active fine-grained matrix

```text
openai:gpt-5-nano
openai:gpt-5.4-nano
openai:gpt-5.4-mini
openai:gpt-5.4-low
openai:gpt-5.4
openai:gpt-5.5
openai:gpt-5.5-high
google:gemini-2.5-flash-lite
google:gemini-2.5-flash
anthropic:claude-haiku-4-5
anthropic:claude-sonnet-4-6
```

### Remove / keep excluded

```text
groq:*                                # server instability / throttling
aws-bedrock:mistral.*                 # removed from eval matrix
aws-bedrock:nvidia.nemotron-super-*   # timeouts / instability
google:gemini-3.1-pro-preview*        # not operationally stable enough
openai:gpt-5.5-xhigh                  # too expensive / unstable for broad use
```

### Benchmark use only

```text
openai:gpt-5.5-high
```

Use as a benchmark for:

```text
atomic_card_extractor
source_takeaway_extractor
entity_candidate_ranker
conflict_candidate_detector
recall_synthesizer
groundedness_checker
eval_judge
```

Do not use it for:

```text
intent_router
success_receipt_generator
routine Slack intake
```

---

## 7. Updated candidate table

| Fine-grained role | Current best model | Status | Next action |
|---|---|---:|---|
| `intent_router` | `openai:gpt-5-nano` | Eligible | Promote as fallback router. |
| `entity_mention_extractor` | `openai:gpt-5.4-mini` | Eligible | Promote for mention extraction. |
| `debug_explainer` | `google:gemini-2.5-flash-lite` | Likely close | Add samples. |
| `eval_judge` | `openai:gpt-5.5` | Likely close | Add samples / compare with 5.4-low. |
| `success_receipt_generator` | `openai:gpt-5-nano` | Close but safety fail | Replace with deterministic template. |
| `source_classifier` | `openai:gpt-5-nano` | Scoring suspicious | Audit zero-tolerance mapping. |
| `durability_filter` | `google:gemini-2.5-flash-lite` | Quality fail | Test OpenAI 5.4 nano/mini. |
| `entity_candidate_ranker` | none yet | Missing | Test 5.4-mini, 5.5-high, Claude Haiku. |
| `atomic_card_extractor` | none yet | Failing | Test 5.4-mini and 5.5-high. |
| `conflict_candidate_detector` | none yet | Failing | Redesign as detection-only. |
| `conflict_explainer` | none yet | Failing | Backend-bound options only. |
| `recall_synthesizer` | none yet | Failing | Test Gemini Flash-Lite / GPT-5.4-mini and inspect failures. |

---

## 8. Suggested next test set

Do not run the full matrix.

Run targeted tests only.

```yaml
durability_filter:
  - openai:gpt-5.4-nano
  - openai:gpt-5.4-mini

atomic_card_extractor:
  - openai:gpt-5.4-mini
  - openai:gpt-5.5-high

entity_candidate_ranker:
  - openai:gpt-5.4-mini
  - openai:gpt-5.5-high
  - anthropic:claude-haiku-4-5

recall_synthesizer:
  - google:gemini-2.5-flash-lite
  - openai:gpt-5.4-mini

debug_explainer:
  - google:gemini-2.5-flash-lite   # add samples

eval_judge:
  - openai:gpt-5.5                 # add samples
  - openai:gpt-5.4-low             # compare default judge candidate
```

Do not rerun:

```text
intent_router / gpt-5-nano
entity_mention_extractor / gpt-5.4-mini
```

unless fixtures or thresholds change.

---

## 9. Suggested implementation changes before next run

### 9.1 Source classifier scorer

Make `source_classifier` scoring role-specific.

It should not be responsible for:

```text
source invention after extraction
table value preservation after parsing
raw email exposure after summarization
```

It should be responsible for:

```text
classifies input type correctly
sets source/table/email flags correctly
chooses source-first when appropriate
rejects junk when appropriate
```

---

### 9.2 Conflict roles

Split and constrain:

```text
conflict_candidate_detector:
  detects possible conflict only

conflict_policy_decider:
  deterministic backend

conflict_explainer:
  only phrases backend-supplied options
```

Do not allow conflict models to choose commit actions.

---

### 9.3 Success receipt

Move to deterministic template.

Model should not be required to invent a receipt structure.

---

### 9.4 Recall

Ensure recall synthesis receives already-filtered evidence.

Do not let the synthesizer solve retrieval/filtering at the same time.

---

### 9.5 OpenAI latency

OpenAI latency remains missing or blank in some artifacts. Add wall-clock timing around every provider call independent of provider-returned timing.

---

## 10. Recommended provisional production wiring

Do not deploy full Brain yet, but these components can be wired behind flags.

```yaml
router:
  deterministic:
    enabled: true
  model_fallback:
    model: openai:gpt-5-nano
    status: eligible

entity_mention_extractor:
  model: openai:gpt-5.4-mini
  status: eligible

entity_final_resolver:
  deterministic: true
  status: required

success_receipt:
  deterministic_template: true
  model_polish:
    model: openai:gpt-5-nano
    optional: true

debug_explainer:
  model: google:gemini-2.5-flash-lite
  status: promising_needs_more_samples

eval_judge:
  model: openai:gpt-5.5
  status: promising_needs_more_samples
```

Keep disabled:

```yaml
conflict_candidate_detector:
  enabled: false
  reason: failing safety

conflict_explainer:
  enabled: false
  reason: unsafe options / needs backend-constrained action space

atomic_card_extractor:
  enabled: false
  reason: no passing model yet

recall_synthesizer:
  enabled: false
  reason: unsupported absence / irrelevant dump failures

source_classifier:
  enabled: false
  reason: scorer contract still suspicious
```

---

## 11. Decision log

Current accepted decisions:

```text
1. Broad all-in-one write-path model is not safe.
2. Fine-grained role decomposition is the right approach.
3. Groq is removed due to server instability/throttling.
4. Mistral is removed from the active eval matrix.
5. GPT-5.5-high is retained only as benchmark.
6. Intent routing can use gpt-5-nano as fallback.
7. Entity mention extraction can use gpt-5.4-mini.
8. Final entity resolution remains deterministic/user-confirmed.
9. Conflict policy remains deterministic.
10. Success receipt should be templated.
```

---

## 12. Bottom line

The fine-grained eval harness is now useful.

The current state is:

```text
Passed:
  intent_router → gpt-5-nano
  entity_mention_extractor → gpt-5.4-mini

Close:
  debug_explainer → gemini-flash-lite
  eval_judge → gpt-5.5
  success_receipt_generator → template + optional gpt-5-nano polish

Still blocked:
  conflict roles
  atomic extraction
  recall synthesis
  source/durability classification
```

Recommended next step:

```text
Run targeted follow-ups only.
Do not run the full matrix again.
Fix source/conflict/receipt role contracts before spending more provider calls.
