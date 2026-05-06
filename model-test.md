# Brain Model + Slack Memory Agent Test Plan

## 0. Purpose

This test plan is for the Brain coding agent.

It defines the test suite required to evaluate:

1. Brain Slack Memory Agent behaviour.
2. LLM model candidates for intake / extraction / repair / recall.
3. Backend guardrails.
4. Memory-card quality.
5. Conflict and entity-resolution safety.
6. Recall and profile quality.
7. Cost/latency trade-offs across model providers.

The goal is to select the cheapest model stack that saturates performance without corrupting the long-term memory store.

Core principle:

```text
Strict on committing.
Helpful on repairing.
Explicit on success.
```

The tests must prove that Brain:

```text
- stores good memories
- rejects or repairs bad memories
- asks when ambiguous
- never silently overwrites high-confidence facts
- never stores source material as one giant memory card
- never over-merges ambiguous entities
- confirms success with exact details
```

---

## 1. Candidate models to test

The model harness should support these candidate models.

### 1.1 Primary candidates

```text
openai:gpt-5.4-nano
openai:gpt-5.4-mini
google:gemini-2.5-flash-lite
google:gemini-2.5-flash
aws-bedrock:mistral-large-3
aws-bedrock:nvidia-nemotron-3-super
groq:llama-3.1-8b-instant
groq:gpt-oss-120b
```

### 1.2 Judge / adjudicator candidates

```text
openai:gpt-5.4
anthropic:claude-sonnet-4.6
```

### 1.3 Embedding candidates

```text
openai:text-embedding-3-small
openai:text-embedding-3-large
voyage:voyage-4-lite
local:nomic-embed-text
```

Embedding tests should be secondary. Do not optimise embeddings before memory-card quality.

---

## 2. Model roles to evaluate

Each model should be evaluated for these roles.

```text
router
  classify Slack command/free-form message intent

slack_intake
  convert Slack message into MemoryProposal / IngestionDecision

memory_compiler
  extract atomic memory cards from notes, articles, transcripts, summaries

validator_critic
  optional low-cost LLM critic; deterministic validator remains authoritative

entity_resolution
  choose whether mentions refer to existing entities or require clarification

conflict_classifier
  classify duplicate/additive/supersedes/contradicts/correction

recall_synthesizer
  turn retrieved Brain records into concise grounded answer

debug_explainer
  explain why recall returned certain records

eval_judge
  judge outputs offline; never in production critical path unless explicitly configured
```

---

## 3. Non-negotiable zero-tolerance failures

A model fails the Brain model eval if it causes any of these on golden tests.

```text
1. Silent overwrite of high-confidence fact.

2. Entity over-merge where two different plausible entities exist.

3. Commit of unresolved pronoun/reference as durable fact.
   Example: "He prefers the other one."

4. Long article/transcript/markdown stored as one giant memory card.

5. Large table atomized into one memory per row by default.

6. Malformed JSON/schema output that cannot be repaired.

7. Auto-commit when decision should be user choice.

8. Storing no-durable-value junk without explicit reason.

9. Failure to include success receipt after commit.

10. Recall answer presents superseded/deleted memory as current.
```

---

## 4. Required test categories

Implement tests in these groups.

```text
tests/model_eval/
  test_schema_validity.py
  test_intake_decisions.py
  test_memory_extraction.py
  test_entity_resolution.py
  test_conflict_classification.py
  test_source_memory_split.py
  test_repair_options.py
  test_recall_quality.py
  test_cost_latency.py

tests/slack/
  test_slack_router.py
  test_slack_ingestion.py
  test_slack_actions.py
  test_slack_formatting.py
  test_slack_debug_admin.py

tests/brain/
  test_proposal_validator.py
  test_memory_commit_policy.py
  test_profile_recall.py
  test_open_loops.py
  test_status_filtering.py
```

External model calls must be behind pytest markers.

```text
@pytest.mark.model_eval
@pytest.mark.external_llm
@pytest.mark.slow
```

Unit tests must use:

```text
FakeLLMClient
FakeSlackClient
FakeCogneeAdapter
temporary test database
mocked source fetcher
```

---

## 5. Evaluation harness design

Create a model evaluation runner.

Suggested path:

```text
src/memory_stack/evals/
  model_matrix.py
  fixtures.py
  runner.py
  scoring.py
  reports.py
```

CLI:

```bash
brain eval models \
  --models openai:gpt-5.4-nano,google:gemini-2.5-flash-lite,groq:llama-3.1-8b-instant \
  --fixtures all \
  --output eval_runs/<timestamp>.jsonl
```

Each model eval run should write JSONL.

Example record:

```json
{
  "run_id": "eval_20260506_001",
  "model": "openai:gpt-5.4-nano",
  "provider": "openai",
  "role": "slack_intake",
  "fixture_id": "ambiguous_sam_001",
  "input_tokens": 2100,
  "output_tokens": 550,
  "estimated_cost_usd": 0.0011,
  "latency_ms": 1430,
  "schema_valid": true,
  "decision_expected": "needs_user_choice",
  "decision_actual": "needs_user_choice",
  "zero_tolerance_failure": false,
  "scores": {
    "decision_correct": 1,
    "memory_card_quality": 0.95,
    "entity_resolution": 1,
    "repair_options": 1,
    "receipt_quality": null
  },
  "raw_output_path": "eval_runs/raw/..."
}
```

---

## 6. Scoring dimensions

Score every model output on these dimensions.

### 6.1 Schema validity

```text
1.0 = valid JSON matching expected schema
0.5 = minor repair needed, automatically repairable
0.0 = invalid/unusable
```

Hard fail if repeated schema failures exceed threshold.

### 6.2 Decision correctness

Expected decision classes:

```text
commit_success
commit_with_warning
needs_clarification
needs_user_choice
propose_repair
reject_with_repair_path
hard_reject
```

Score:

```text
1.0 = exact expected decision
0.5 = safe but suboptimal decision
0.0 = unsafe or wrong decision
```

Examples:

```text
Expected needs_user_choice.
Actual reject_with_repair_path.
Safe but suboptimal → 0.5.

Expected needs_user_choice.
Actual commit_success.
Unsafe → 0.0 and zero-tolerance failure.
```

### 6.3 Memory-card extraction quality

Score:

```text
1.0 = all durable cards extracted, atomic, correctly typed
0.75 = minor missing card or slight over-grouping
0.5 = several misses, but no dangerous write
0.0 = wrong/unsafe extraction
```

### 6.4 Entity resolution

Score:

```text
1.0 = correct entities and aliases
0.75 = minor alias/context omission
0.5 = safe ambiguity preserved
0.0 = over-merged or wrong entity
```

Over-merge is zero-tolerance.

### 6.5 Conflict handling

Score:

```text
1.0 = correct duplicate/additive/supersedes/contradicts/correction classification
0.5 = safe but asks user unnecessarily
0.0 = unsafe overwrite or missed high-confidence conflict
```

### 6.6 Source/memory split

Score:

```text
1.0 = source stored as source; extracted durable cards
0.5 = source stored but extraction weak
0.0 = source stored as one giant memory card
```

Long-source-as-one-memory is zero-tolerance.

### 6.7 Repair-option usefulness

Score:

```text
1.0 = repair options are targeted and actionable
0.75 = mostly useful but missing best option
0.5 = generic repair path
0.0 = no repair path for recoverable error
```

### 6.8 Success receipt completeness

Score successful commits on whether receipt includes:

```text
- memory kind
- statement
- confidence
- entities created/updated
- relationships created
- source ID if any
- memory ID
- Inspect / Undo / Mark wrong actions
```

Score:

```text
1.0 = complete
0.5 = partial
0.0 = vague confirmation such as "Done"
```

### 6.9 Recall quality

Score:

```text
1.0 = grounded, complete, excludes stale/deleted facts, surfaces uncertainty
0.75 = mostly correct, minor omissions
0.5 = incomplete but safe
0.0 = wrong/currentness error/hallucination
```

---

## 7. Acceptance thresholds

A model is eligible for production use in a role only if it meets these thresholds on golden fixtures.

```text
schema validity:                         >= 99.5%
decision correctness:                    >= 97.0%
memory-card extraction quality:          >= 95.0%
entity resolution safety:                >= 99.0%
conflict classification safety:          >= 99.0%
source/memory split safety:              100.0% on zero-tolerance cases
success receipt completeness:            >= 98.0%
repair-option usefulness:                >= 95.0%
silent high-confidence overwrite:        0 tolerated
entity over-merge on golden fixtures:    0 tolerated
unresolved pronoun committed:            0 tolerated
```

Model selection rule:

```text
Choose the cheapest model whose failure rate is statistically indistinguishable
from the next stronger model and has zero zero-tolerance failures.
```

---

## 8. Golden fixtures

Implement each fixture with:

```python
class GoldenFixture(BaseModel):
    id: str
    category: str
    role: str
    existing_state: dict
    user_input: str
    expected_decision: str
    expected_memory_cards: list[dict]
    expected_entities: list[dict]
    expected_relationships: list[dict]
    expected_repair_options: list[str]
    zero_tolerance_checks: list[str]
```

---

# 9. Ingestion fixtures

## 9.1 Clean family fact

Fixture ID:

```text
family_fact_twins_001
```

Existing state:

```text
empty Brain DB, but user identity entity "Daniele" exists
```

Input:

```text
Nur and Sara are my twin daughters.
```

Expected decision:

```text
commit_success
```

Expected memory card:

```json
{
  "kind": "family_fact",
  "statement": "Nur and Sara are Daniele's twin daughters.",
  "confidence": "high"
}
```

Expected entities:

```text
Daniele: person
Nur: person
Sara: person
```

Expected relationships:

```text
Nur --daughter_of--> Daniele
Sara --daughter_of--> Daniele
Nur --twin_of--> Sara
Sara --twin_of--> Nur
```

Success receipt must include:

```text
family_fact
Nur
Sara
Daniele
daughter_of
twin_of
confidence high
Inspect / Undo / Mark wrong
```

Zero-tolerance:

```text
must not create duplicate memory cards for Nur and Sara separately
must not omit twin relationship
must not create vague "children" relation only
```

---

## 9.2 Clean person interaction

Fixture ID:

```text
person_interaction_sam_bill_evans_001
```

Existing state:

```text
no Sam entity exists
```

Input:

```text
Sam from Goldman mentioned that he likes Bill Evans.
```

Expected decision:

```text
commit_success or commit_with_warning
```

Expected card:

```json
{
  "kind": "person_interaction",
  "statement": "Sam from Goldman mentioned that he likes Bill Evans.",
  "confidence": "medium"
}
```

Expected entities:

```text
Sam from Goldman: person
Goldman: organization
Bill Evans: person/concept/person_topic
```

Expected relationship:

```text
Sam from Goldman --likes--> Bill Evans
Sam from Goldman --associated_with--> Goldman
```

Zero-tolerance:

```text
must not invent surname
must not assume Goldman Sachs unless policy allows as low-confidence alias
must not treat Bill Evans as organization
```

---

## 9.3 Open question

Fixture ID:

```text
open_question_knowledge_graphs_001
```

Input:

```text
I want to learn more about knowledge graphs.
```

Expected decision:

```text
commit_success
```

Expected card:

```json
{
  "kind": "open_question",
  "statement": "Daniele wants to learn more about knowledge graphs.",
  "topics": ["knowledge_graphs"],
  "confidence": "high"
}
```

Expected open loop:

```text
status=open
topic=knowledge_graphs
```

Zero-tolerance:

```text
must create open_loop
must not store as basic_fact only
```

---

## 9.4 Research question

Fixture ID:

```text
research_question_language_intelligence_001
```

Input:

```text
I wonder what the relationship is between human intelligence and language. Need to research this.
```

Expected decision:

```text
commit_success
```

Expected card:

```json
{
  "kind": "research_question",
  "statement": "What is the relationship between human intelligence and language?",
  "topics": ["cognitive_science", "language", "intelligence"],
  "confidence": "high"
}
```

Expected open loop:

```text
status=open
```

---

## 9.5 Chat conclusion

Fixture ID:

```text
chat_conclusion_brain_architecture_001
```

Input:

```text
Conclusion from our chat: Brain should treat Cognee as a rebuildable semantic projection, while Brain DB remains the source of truth for memory cards, entities, conflicts, and reminders.
```

Expected decision:

```text
commit_success
```

Expected card:

```json
{
  "kind": "chat_conclusion",
  "statement": "Brain should treat Cognee as a rebuildable semantic projection, while Brain DB remains the source of truth for memory cards, entities, conflicts, and reminders.",
  "topics": ["brain", "cognee", "memory_architecture"],
  "confidence": "high"
}
```

---

## 9.6 Preference

Fixture ID:

```text
preference_jazz_001
```

Input:

```text
I prefer Sonny Rollins over John Coltrane for relaxed Sunday listening.
```

Expected decision:

```text
commit_success
```

Expected card:

```json
{
  "kind": "preference",
  "statement": "Daniele prefers Sonny Rollins over John Coltrane for relaxed Sunday listening.",
  "topics": ["jazz", "music"],
  "confidence": "high"
}
```

Expected entities:

```text
Daniele
Sonny Rollins
John Coltrane
```

---

# 10. Ambiguity and repair fixtures

## 10.1 Ambiguous Sam

Fixture ID:

```text
ambiguous_sam_001
```

Existing state:

```text
Entity: Sam from Goldman
Entity: Sam from Point72
```

Input:

```text
Sam mentioned that he likes Bill Evans.
```

Expected decision:

```text
needs_user_choice
```

Expected repair options:

```text
bind_entity: Sam from Goldman
bind_entity: Sam from Point72
create_entity: new Sam
cancel
```

Zero-tolerance:

```text
must not auto-commit
must not pick one Sam arbitrarily
must not merge Sams
```

---

## 10.2 Unresolved pronoun

Fixture ID:

```text
unresolved_pronoun_001
```

Input:

```text
He prefers the other one.
```

Expected decision:

```text
reject_with_repair_path or needs_clarification
```

Expected reason codes:

```text
unresolved_pronoun
unresolved_object
```

Expected repair options:

```text
choose_person
rewrite_memory
cancel
```

Zero-tolerance:

```text
must not commit memory card
must not invent referents
```

---

## 10.3 Vague memory

Fixture ID:

```text
vague_memory_001
```

Input:

```text
Remember the thing from yesterday.
```

Expected decision:

```text
reject_with_repair_path
```

Expected reason codes:

```text
unresolved_object
malformed_input
```

Expected repair options:

```text
rewrite_memory
cancel
```

Zero-tolerance:

```text
must not commit
```

---

## 10.4 No durable value

Fixture ID:

```text
no_durable_value_weather_001
```

Input:

```text
Today’s weather is cloudy.
```

Expected decision:

```text
reject_with_repair_path
```

Expected reason codes:

```text
no_durable_value
```

Expected repair options:

```text
add_reason
store_anyway_as_low_priority_note
cancel
```

Default expected behaviour:

```text
no commit
```

Zero-tolerance:

```text
must not auto-commit
```

---

## 10.5 Overly broad memory

Fixture ID:

```text
overly_broad_memory_001
```

Input:

```text
Remember everything about AI.
```

Expected decision:

```text
reject_with_repair_path or needs_clarification
```

Expected reason codes:

```text
overly_broad_memory
```

Expected repair options:

```text
rewrite_memory
create_open_question
cancel
```

---

# 11. Conflict fixtures

## 11.1 Duplicate memory

Fixture ID:

```text
duplicate_sam_bill_evans_001
```

Existing memory:

```text
Sam from Goldman mentioned that he likes Bill Evans.
```

Input:

```text
Sam from Goldman said he likes Bill Evans.
```

Expected decision:

```text
commit_with_warning or needs_user_choice
```

Expected conflict classification:

```text
duplicate
```

Expected behaviour:

```text
do not create duplicate current memory unless preserving new source evidence
if retained, link new --duplicates--> old
```

Zero-tolerance:

```text
must not create two indistinguishable current facts with no duplicate link
```

---

## 11.2 Additive preference

Fixture ID:

```text
additive_sam_preferences_001
```

Existing memory:

```text
Sam from Goldman likes Bill Evans.
```

Input:

```text
Sam from Goldman also likes Sonny Rollins.
```

Expected decision:

```text
commit_success
```

Expected classification:

```text
additive
```

Expected behaviour:

```text
both memories current
no supersedes link
```

Zero-tolerance:

```text
must not supersede Bill Evans preference
```

---

## 11.3 Supersession employment

Fixture ID:

```text
supersession_sam_job_001
```

Existing memory:

```text
Sam works at Goldman.
```

Input:

```text
Sam left Goldman and joined Point72.
```

Expected decision:

```text
needs_user_choice or commit_with_warning if policy allows auto-supersession
```

Expected recommended action:

```text
new memory current
old memory superseded
new --supersedes--> old
```

Expected repair options:

```text
approve_supersession
keep_both
reject_new
edit
```

Zero-tolerance:

```text
must not leave both as current employment facts without conflict/supersession
must not delete old memory
```

---

## 11.4 Explicit correction

Fixture ID:

```text
correction_sam_music_001
```

Existing memory:

```text
Sam from Goldman likes Bill Evans.
```

Input:

```text
Correction: Sam from Goldman actually likes early Coltrane, not Bill Evans.
```

Expected decision:

```text
needs_user_choice or commit_with_warning
```

Expected classification:

```text
correction
supersedes
```

Expected recommended action:

```text
new memory current
old memory superseded
new --supersedes--> old
```

Zero-tolerance:

```text
must not keep old preference as current without supersession/conflict
```

---

## 11.5 High-confidence family conflict

Fixture ID:

```text
conflict_sara_niece_001
```

Existing memory:

```text
Sara is Daniele’s daughter and Nur’s twin.
```

Input:

```text
Sara is my niece.
```

Expected decision:

```text
needs_user_choice
```

Expected reason codes:

```text
high_confidence_conflict
ambiguous_entity_possible
```

Expected repair options:

```text
this_is_a_different_sara
correct_old_memory
keep_as_conflicted
reject_new
```

Zero-tolerance:

```text
must not auto-commit as current fact
must not overwrite daughter relationship
must not delete existing family fact
```

---

## 11.6 True contradiction

Fixture ID:

```text
contradiction_sam_children_001
```

Existing memory:

```text
Sam from Goldman has two children.
```

Input:

```text
Sam from Goldman has no children.
```

Expected decision:

```text
needs_user_choice or commit_with_warning as conflicted
```

Expected classification:

```text
contradicts
```

Expected options:

```text
mark_contradiction
correct_old_memory
reject_new
```

Zero-tolerance:

```text
must not silently replace old fact
```

---

# 12. Source/memory split fixtures

## 12.1 Article URL with reason

Fixture ID:

```text
article_url_ai_memory_001
```

Input:

```text
Remember this article: https://example.com/ai-memory
why: useful for thinking about knowledge graph memory design.
```

Mock fetched article:

```text
Title: Graphs as Memory for AI Agents

Body:
The article argues that graph memory helps agents preserve relationships
between entities, but that source provenance and update semantics are still
needed. It gives examples of contradiction handling and temporal facts.
```

Expected decision:

```text
commit_success or commit_with_warning
```

Expected source:

```text
kind=article
title=Graphs as Memory for AI Agents
uri=https://example.com/ai-memory
```

Expected memory cards:

```text
article_note
key_takeaway: graph memory helps preserve relationships
key_takeaway: provenance and update semantics are needed
open_question or idea if model extracts one safely
```

Expected links:

```text
memory cards derived_from source
```

Zero-tolerance:

```text
must not store whole article as one memory card
must not fail if article fetching is mocked
```

---

## 12.2 Article URL fetch failure

Fixture ID:

```text
article_url_fetch_failure_001
```

Input:

```text
Remember this article: https://example.com/missing
why: useful for memory architecture.
```

Mock fetch:

```text
network error / 404
```

Expected decision:

```text
propose_repair or commit_with_warning
```

Expected behaviour:

```text
store source shell with fetch_error metadata if policy allows
ask user to paste article text or store URL-only source
```

Expected repair options:

```text
paste_article_text
store_url_only
cancel
```

Zero-tolerance:

```text
must not invent article content
```

---

## 12.3 Long markdown chat summary

Fixture ID:

```text
long_markdown_chat_summary_001
```

Input:

```text
# Chat Summary: Brain Architecture

We decided that Brain DB should be the source of truth.
Cognee should be a rebuildable semantic projection.
Slack should be a strict memory intake agent.
Open questions:
- Should Telegram be added later?
- Which model is cheapest while saturating performance?
```

Expected source:

```text
kind=markdown or chat_summary
```

Expected memory cards:

```text
decision: Brain DB is source of truth
decision: Cognee is rebuildable projection
decision: Slack is strict memory intake agent
open_question: Should Telegram be added later?
open_question: Which model is cheapest while saturating performance?
```

Zero-tolerance:

```text
must not store whole markdown as one giant memory card only
```

---

## 12.4 Conversation transcript

Fixture ID:

```text
conversation_transcript_sam_001
```

Input:

```text
Daniele: Good to see you, Sam. Still at Goldman?
Sam: No, I left Goldman last month and joined Point72.
Daniele: Still listening to Bill Evans?
Sam: Yes, but lately more early Coltrane.
Daniele: We should catch up about AI infra.
Sam: Definitely, send me that article you mentioned.
```

Existing memory:

```text
Sam works at Goldman.
Sam likes Bill Evans.
```

Expected source:

```text
kind=transcript
```

Expected memory cards:

```text
person_interaction: conversation with Sam
person_fact/project_state: Sam left Goldman and joined Point72
preference: Sam lately listens more to early Coltrane
commitment/open_loop: send Sam article about AI infra
```

Expected conflict classification:

```text
employment fact supersedes old Goldman memory
music preference additive or mild update, not necessarily supersede Bill Evans unless phrased as correction
```

Expected repair options:

```text
approve_supersession for job change
```

Zero-tolerance:

```text
must not infer Sam hates Bill Evans
must not auto-delete old Goldman memory
must not store transcript as one memory card
```

---

## 12.5 Small table

Fixture ID:

```text
small_table_preferences_001
```

Input:

```markdown
| Person | Firm | Preference | Source |
|---|---|---|---|
| Sam | Goldman | Likes Bill Evans | Dinner 2026-05-05 |
| Anna | JPM | Likes Barolo | Lunch 2026-05-01 |
```

Expected decision:

```text
commit_success or propose_repair
```

Expected source:

```text
kind=table
```

Expected card:

```text
table_note with columns and rows
```

Expected entities:

```text
Sam
Goldman
Anna
JPM
Bill Evans
Barolo
```

Zero-tolerance:

```text
must not create excessive row-level memory cards without policy approval
must preserve original table as source
```

---

## 12.6 Large table

Fixture ID:

```text
large_table_500_rows_001
```

Input:

```text
CSV table with 500 rows
```

Expected decision:

```text
propose_repair
```

Expected repair options:

```text
store_as_source_data
store_schema_summary
cancel
```

Expected behaviour:

```text
store source/data object
create schema/summary only
do not atomize every row into memory cards
```

Zero-tolerance:

```text
must not create 500 memory cards
```

---

# 13. Slack UX fixtures

## 13.1 Success receipt completeness

Fixture ID:

```text
slack_success_receipt_001
```

Input:

```text
/brain remember Sam from Goldman mentioned that he likes Bill Evans.
```

Expected Slack blocks/text must include:

```text
Stored
person_interaction
statement
confidence
entities
relationships
memory_id
Inspect button
Undo button
Mark wrong button
```

Zero-tolerance:

```text
must not only say "Done"
```

---

## 13.2 Ambiguous entity buttons

Fixture ID:

```text
slack_ambiguous_entity_buttons_001
```

Existing entities:

```text
Sam from Goldman
Sam from Point72
```

Input:

```text
/brain remember Sam likes Bill Evans.
```

Expected Slack UI:

```text
buttons:
  Sam from Goldman
  Sam from Point72
  Create new Sam
  Cancel
```

Expected backend:

```text
proposal status=pending_user
no memory committed
```

---

## 13.3 Rewrite modal

Fixture ID:

```text
slack_rewrite_modal_001
```

Input:

```text
/brain remember He prefers the other one.
```

Expected Slack UI:

```text
buttons:
  Choose person
  Rewrite memory
  Cancel
```

When user selects Rewrite memory:

```text
modal fields:
  Memory statement
  Person/entity
  Context/source
  Optional date
```

Expected backend:

```text
no memory committed until rewritten proposal validates
```

---

## 13.4 Conflict buttons

Fixture ID:

```text
slack_conflict_buttons_001
```

Existing memory:

```text
Sam works at Goldman.
```

Input:

```text
/brain remember Sam left Goldman and joined Point72.
```

Expected Slack UI:

```text
buttons:
  Approve supersession
  Keep both
  Reject new
  Edit
```

Expected backend before click:

```text
proposal status=pending_user
old memory still current
new memory not yet committed unless policy allows commit_with_warning
```

After Approve supersession:

```text
old status=superseded
new status=current
memory_link new --supersedes--> old
```

---

## 13.5 No durable value repair

Fixture ID:

```text
slack_no_durable_value_repair_001
```

Input:

```text
/brain remember Today’s weather is cloudy.
```

Expected Slack UI:

```text
I won’t store this by default.
Reason: no durable personal-memory value.
buttons:
  Add reason
  Store anyway as low-priority note
  Cancel
```

Expected backend:

```text
no memory committed unless user explicitly chooses store anyway or adds durable reason
```

---

# 14. Recall fixtures

## 14.1 Profile Sam

Fixture ID:

```text
recall_profile_sam_001
```

Existing state:

```text
Sam from Goldman likes Bill Evans.
Sam from Goldman is associated with Goldman.
Sam from Goldman mentioned interest in AI infrastructure.
Open loop: send Sam article about AI infra.
```

Query:

```text
Tell me everything about Sam from Goldman.
```

Expected output sections:

```text
Identity
Known facts
Preferences
Interactions
Relationships
Open loops
Conflicts / uncertainties
Evidence
```

Expected content:

```text
associated with Goldman
likes Bill Evans
interested in AI infrastructure
open loop to send article
surname unknown / uncertainty if not known
```

Zero-tolerance:

```text
must not invent surname
must not include deleted/superseded facts as current
must include evidence memory IDs
```

---

## 14.2 Profile Sara

Fixture ID:

```text
recall_profile_sara_001
```

Existing state:

```text
Nur and Sara are Daniele's twin daughters.
```

Query:

```text
Tell me about Sara.
```

Expected output:

```text
Sara is Daniele's daughter.
Sara is Nur's twin.
Evidence memory ID included.
```

Zero-tolerance:

```text
must not invert daughter_of relationship
```

---

## 14.3 Daughters query

Fixture ID:

```text
recall_daughters_001
```

Existing state:

```text
Nur and Sara are Daniele's twin daughters.
```

Query:

```text
Who are my daughters?
```

Expected output:

```text
Nur and Sara.
They are twins.
Evidence memory ID included.
```

---

## 14.4 Open questions

Fixture ID:

```text
recall_open_questions_knowledge_graphs_001
```

Existing state:

```text
Open question: learn more about knowledge graphs.
Research question: relationship between human intelligence and language.
```

Query:

```text
What open ideas do I have about knowledge graphs?
```

Expected output:

```text
learn more about knowledge graphs
status=open
topic=knowledge_graphs
```

Zero-tolerance:

```text
must not include closed/archived open loops by default
```

---

## 14.5 Source-backed facts

Fixture ID:

```text
recall_source_backed_article_001
```

Existing state:

```text
source article about graph memory
memory cards derived from source
```

Query:

```text
What source-backed facts do I have about graph memory?
```

Expected output:

```text
separate source-backed facts from inferences
include source IDs
include memory IDs
do not hallucinate beyond source
```

---

## 14.6 Superseded memory hidden

Fixture ID:

```text
recall_hide_superseded_001
```

Existing state:

```text
Old memory: Sam works at Goldman. status=superseded
New memory: Sam joined Point72. status=current
```

Query:

```text
Where does Sam work?
```

Expected output:

```text
Sam joined/works at Point72.
Old Goldman fact not presented as current.
May mention historical fact only if include_superseded=true or query asks history.
```

Zero-tolerance:

```text
must not answer "Goldman" as current
```

---

## 14.7 Deleted memory hidden

Fixture ID:

```text
recall_hide_deleted_001
```

Existing state:

```text
Memory A current: Sam likes Bill Evans.
Memory B deleted: Sam likes Taylor Swift.
```

Query:

```text
What music does Sam like?
```

Expected output:

```text
Bill Evans only.
Deleted memory hidden.
```

Zero-tolerance:

```text
must not include deleted memory
```

---

# 15. Debug / inspection fixtures

## 15.1 Inspect memory

Fixture ID:

```text
debug_inspect_memory_001
```

Command:

```text
/brain inspect memory mem_123
```

Expected output:

```text
memory card row
status
kind
statement
confidence
linked entities
relationships
memory_links
source
cognee_sync status
```

---

## 15.2 Inspect entity

Fixture ID:

```text
debug_inspect_entity_sam_001
```

Command:

```text
/brain inspect entity "Sam from Goldman"
```

Expected output:

```text
entity row
aliases
memory_entities
relationships in/out
possible duplicate entities
```

---

## 15.3 Explain recall

Fixture ID:

```text
debug_explain_recall_sam_001
```

Command:

```text
/brain debug recall "Tell me everything about Sam from Goldman"
```

Expected output:

```text
planner decision
DB candidates
Cognee candidates if enabled
status filters
filtered-out memories
final evidence set
answer sections
```

Zero-tolerance:

```text
normal users cannot access admin-only data
```

---

## 15.4 Raw SQL disabled

Fixture ID:

```text
debug_sql_disabled_001
```

Command:

```text
/brain admin sql SELECT * FROM memory_cards
```

Config:

```text
BRAIN_DEBUG_SQL_ENABLED=false
```

Expected output:

```text
denied
```

---

## 15.5 Raw SQL select-only

Fixture ID:

```text
debug_sql_select_only_001
```

Config:

```text
BRAIN_DEBUG_SQL_ENABLED=true
admin user allowed
```

Allowed command:

```text
/brain admin sql SELECT id, kind, status FROM memory_cards LIMIT 10
```

Expected:

```text
allowed
logged
limited
```

Disallowed command:

```text
/brain admin sql DELETE FROM memory_cards
```

Expected:

```text
denied
```

Zero-tolerance:

```text
must not execute non-SELECT
must not execute multiple statements
```

---

# 16. Backend validator fixtures

These tests prove backend enforcement works even if the LLM proposes bad output.

## 16.1 LLM proposes unresolved pronoun

Fixture ID:

```text
validator_blocks_unresolved_pronoun_001
```

LLM proposal:

```json
{
  "memory_cards": [
    {
      "kind": "preference",
      "statement": "He prefers the other one.",
      "confidence": "medium"
    }
  ]
}
```

Expected validator decision:

```text
reject_with_repair_path
```

Expected:

```text
no DB write
reason_codes include unresolved_pronoun and unresolved_object
```

---

## 16.2 LLM proposes transcript as one memory

Fixture ID:

```text
validator_blocks_transcript_as_memory_001
```

LLM proposal:

```json
{
  "memory_cards": [
    {
      "kind": "conversation_summary",
      "statement": "[entire 8000 word transcript]",
      "confidence": "medium"
    }
  ]
}
```

Expected:

```text
propose_repair
source_material_as_memory
no memory commit
repair option: store_source_and_extract
```

---

## 16.3 LLM proposes high-confidence overwrite

Fixture ID:

```text
validator_blocks_high_confidence_overwrite_001
```

Existing memory:

```text
Sara is Daniele’s daughter.
```

LLM proposal:

```text
Sara is Daniele’s niece.
```

Expected:

```text
needs_user_choice
high_confidence_conflict
no automatic commit
```

---

## 16.4 LLM proposes large table atomization

Fixture ID:

```text
validator_blocks_large_table_atomization_001
```

LLM proposal:

```text
500 memory cards, one per CSV row
```

Expected:

```text
reject or propose_repair
table_too_large
no mass memory-card creation
```

---

# 17. Cost and latency tests

Cost tests should not enforce exact provider prices in unit tests. Prices change.

Instead:

```text
- token counts are recorded
- provider/model IDs are recorded
- estimated price uses configurable pricing table
- report sorts by cost per successful fixture
```

Implement:

```text
pricing/models.yaml
```

Example:

```yaml
openai:gpt-5.4-nano:
  input_per_1m: 0.20
  output_per_1m: 1.25

google:gemini-2.5-flash-lite:
  input_per_1m: 0.10
  output_per_1m: 0.40
```

Metrics:

```text
avg_latency_ms
p95_latency_ms
avg_cost_per_ingestion
cost_per_successful_fixture
zero_tolerance_failure_count
```

Report table:

```text
model
role
fixtures_run
schema_validity
decision_accuracy
zero_tolerance_failures
avg_cost
p95_latency
eligible_for_production
```

---

# 18. Model escalation tests

Test the cascade, not just individual models.

## 18.1 Cheap model success

Fixture ID:

```text
cascade_clean_fact_no_escalation_001
```

Input:

```text
Nur and Sara are my twin daughters.
```

Expected:

```text
cheap/default model succeeds
no escalation
commit_success
```

---

## 18.2 Validator failure triggers escalation

Fixture ID:

```text
cascade_validator_failure_escalates_001
```

Cheap model output:

```text
invalid schema or unsafe proposal
```

Expected:

```text
escalate to stronger model
if stronger succeeds, return repair/commit decision
if stronger fails, ask user or reject safely
```

---

## 18.3 High-confidence conflict triggers escalation/user choice

Fixture ID:

```text
cascade_conflict_escalation_001
```

Input:

```text
Sara is my niece.
```

Existing:

```text
Sara is my daughter.
```

Expected:

```text
escalate to conflict model if configured
still no automatic overwrite
return needs_user_choice
```

---

## 18.4 Local/cheap model low confidence asks user

Fixture ID:

```text
cascade_low_confidence_asks_user_001
```

If model confidence low and cloud escalation disabled:

```text
do not commit
ask clarification
```

Expected:

```text
safe behaviour
```

---

# 19. Provider comparison report

The eval harness should generate a markdown report.

Example sections:

```text
# Brain Model Eval Report

Date:
Models tested:
Fixture set version:
Policy version:
Prompt version:

## Summary

| Model | Eligible roles | Zero-tolerance failures | Avg cost | P95 latency | Notes |
|---|---|---:|---:|---:|---|

## Recommended stack

router:
slack_intake:
memory_compiler:
conflict_classifier:
recall_synthesizer:
eval_judge:

## Failure analysis

- Model X over-merged Sam entities.
- Model Y stored long source as memory.
- Model Z had malformed JSON in 3% of cases.

## Cost analysis

- Cost per 1k successful ingestions.
- Cost per 1k source ingestions.
- Cost per 1k recall queries.

## Raw output links

...
```

---

# 20. CI strategy

Unit tests should run on every commit.

```bash
uv run pytest tests/brain tests/slack
```

Model evals should not run by default.

```bash
uv run pytest -m model_eval
uv run pytest -m external_llm
```

Recommended CI split:

```text
PR CI:
  unit tests
  fake LLM tests
  fake Slack tests
  fake Cognee tests

Nightly/manual:
  external model evals
  cost/latency report
```

---

# 21. Final model-selection rule

After all tests are implemented, choose models using this rule.

```text
1. Eliminate any model with zero-tolerance failures.

2. Eliminate any model below threshold on:
   - schema validity
   - decision correctness
   - entity safety
   - conflict safety
   - source/memory split

3. Among remaining models, choose the cheapest model per role.

4. Use escalation for cases where the cheap model is safe but incomplete.

5. Use human choice instead of model guess when ambiguity affects durable memory.
```

Expected initial production stack unless evals prove otherwise:

```text
router:
  deterministic rules
  fallback: cheap model

slack_intake:
  openai:gpt-5.4-nano

memory_compiler:
  openai:gpt-5.4-nano

cheap challenger to test:
  google:gemini-2.5-flash-lite

source/article challenger:
  google:gemini-2.5-flash

conflict escalation:
  openai:gpt-5.4-mini

eval judge:
  anthropic:claude-sonnet-4.6 or openai:gpt-5.4

embeddings:
  openai:text-embedding-3-small
```

---

# 22. Completion criteria for coding agent

The test implementation is complete when:

```text
1. All fixtures above exist in code.

2. The model eval runner can run the same fixtures against multiple providers.

3. Unit tests use fake LLM outputs and require no external services.

4. External model tests are marked and optional.

5. Every zero-tolerance failure is explicitly asserted.

6. Slack receipts and repair options are tested.

7. Backend validator is tested against bad LLM proposals.

8. Recall tests prove deleted/superseded memories are hidden by default.

9. Cost/latency are recorded for model evals.

10. A markdown report is generated after model eval runs.
```