# Brain Slack Memory Agent — Coding Agent Implementation Instructions

## 0. Mission

Implement a dedicated Slack-based agent for the Brain memory system.

This Slack agent is **separate from MCP** and is designed for:

- strict, high-quality memory ingestion
- memory recall
- review and correction
- conflict handling
- entity disambiguation
- low-level inspection/debugging for verification

The agent must follow Brain’s core philosophy:

> Strict on committing.  
> Helpful on repairing.  
> Explicit on success.

The Slack agent should **not** be a general assistant. It is a narrow, specialised interface for adding, retrieving, inspecting, and correcting memories in Brain.

---

## 1. Architectural decision

### 1.1 Slack bridge is separate from MCP

Do **not** implement Slack as an MCP client.

Use this structure:

```text
Slack app
  ↓
Slack intake agent / router
  ↓
Brain service layer
  ↓
Brain DB
  ↓
Cognee projection

MCP server
  ↓
Brain service layer
  ↓
Brain DB
  ↓
Cognee projection
```

Slack and MCP should share the same core domain layer:

```text
BrainService
BrainStore
MemoryCompiler
ProposalValidator
EntityResolver
ConflictDetector
RecallAgent
CogneeProjector
```

Do not duplicate memory logic inside Slack handlers.

### 1.2 Slack agent has an extra LLM layer

The Slack bridge should include a dedicated LLM layer:

```text
Slack message
  ↓
Slack Intake Agent LLM
  ↓
MemoryProposal
  ↓
Deterministic validator
  ↓
Brain service
```

The LLM should interpret, classify, propose, and repair.

The LLM must **not** be trusted as the sole enforcement layer.

Backend validation must enforce the rules deterministically.

Correct pattern:

```text
LLM = judgement / proposal / repair UX
Validator = hard policy
Brain DB = source of truth
Cognee = rebuildable projection
```

---

## 2. Core behaviour

The Slack agent must support these outcomes:

```text
COMMIT_SUCCESS
  Clean memory stored.

COMMIT_WITH_WARNING
  Memory stored, but with uncertainty or non-blocking warning.

NEEDS_CLARIFICATION
  Memory cannot be safely stored until the user answers a targeted question.

NEEDS_USER_CHOICE
  Multiple valid actions exist; user must choose.

PROPOSE_REPAIR
  The system proposes a corrected memory card or source policy.

REJECT_WITH_REPAIR_PATH
  The system refuses to store as written, but offers a way to fix it.

HARD_REJECT
  The system refuses and does not offer automatic repair.
```

Hard reject should be rare.

The normal failure mode should be constructive:

```text
Bad memory:
  do not store

Recoverable bad memory:
  ask a sharp question or offer multiple-choice buttons

Good memory:
  store and confirm exactly what was stored

Ambiguous/conflicting memory:
  create proposal, do not commit until resolved
```

---

## 3. Required module structure

Add or adapt the following structure.

```text
src/memory_stack/
  slack/
    __init__.py
    app.py                    # Slack Bolt entrypoint
    router.py                 # intent routing
    intake_agent.py           # LLM-backed intake agent
    policy_loader.py          # loads rule/context files
    formatter.py              # Slack Block Kit formatting
    commands.py               # slash command handlers
    actions.py                # button/modal handlers
    admin_tools.py            # guarded inspection/debug tools
    auth.py                   # Slack user allowlist/admin checks

  rules/
    memory_policy.md          # human-readable policy for LLM context
    memory_policy.yaml        # machine-readable validator policy
    examples.yaml             # golden examples for intake prompt
    tool_permissions.yaml     # normal/debug/admin tool permissions

  prompts/
    slack_intake_system.md
    slack_recall_system.md
    slack_debug_system.md

  ingestion/
    proposal_validator.py     # deterministic validator
    memory_compiler.py        # existing/LLM compiler integration
    rule_compiler.py          # deterministic fast-path compiler

  resolution/
    entity_resolver.py
    duplicate_detector.py
    conflict_detector.py

  recall/
    planner.py
    retriever.py
    evidence_builder.py
    profile_builder.py
    synthesizer.py
```

The Slack package must call existing Brain service methods rather than writing directly to storage.

---

## 4. Configuration

Add or confirm the following environment variables.

```text
BRAIN_SLACK_ENABLED=false

SLACK_BOT_TOKEN=
SLACK_APP_TOKEN=
SLACK_SIGNING_SECRET=

BRAIN_SLACK_ALLOWED_USER_IDS=
BRAIN_SLACK_ADMIN_USER_IDS=

BRAIN_SLACK_DEFAULT_MODE=strict

BRAIN_LLM_ENABLED=false
BRAIN_LLM_PROVIDER=
BRAIN_LLM_MODEL=

BRAIN_DEBUG_SQL_ENABLED=false
BRAIN_DEBUG_SQL_MAX_ROWS=100
BRAIN_DEBUG_SQL_TIMEOUT_SECONDS=5
```

Default behaviour:

```text
Slack disabled by default.
LLM disabled in tests.
Debug SQL disabled by default.
Admin tools restricted to allowlisted Slack user IDs.
Hard delete disabled unless explicitly confirmed.
```

---

## 5. Slack vs MCP boundary

### 5.1 MCP remains high-level

Existing MCP tools should remain:

```text
brain.remember
brain.ingest_source
brain.recall
brain.profile_entity
brain.list_open_loops
brain.get_memory
brain.get_source
brain.resolve_conflict
brain.forget
```

Do not expose low-level database or Cognee operations through normal MCP tools.

### 5.2 Slack gets extra debug/admin flows

Slack should support diagnostic tools for verification, but these must be gated.

Normal users:

```text
remember
recall
profile
open loops
review recent
undo last
inspect own recent memory
```

Admin users:

```text
inspect raw memory
inspect raw source
inspect entity
inspect relationships
inspect Cognee sync
explain recall
run fixture
merge entities
resolve conflict
retry sync
```

Dangerous operations:

```text
hard delete
prune Cognee
rebuild Cognee with prune
raw SQL write
```

Do not expose dangerous operations by default.

---

## 6. Slack commands

Implement these commands.

```text
/brain remember <text>
/brain source <url_or_text>
/brain recall <query>
/brain profile <entity>
/brain open
/brain review
/brain undo-last
/brain inspect <object>
/brain debug <subcommand>
/brain admin <subcommand>
```

### 6.1 `/brain remember`

Primary ingestion command.

Examples:

```text
/brain remember Sam from Goldman mentioned that he likes Bill Evans.
/brain remember Nur and Sara are my twin daughters.
/brain remember I want to learn more about knowledge graphs.
```

Behaviour:

1. Create a `MemoryProposal`.
2. Validate it.
3. Check entities/conflicts.
4. Auto-commit only if safe.
5. Otherwise ask, repair, or reject with repair path.
6. Always return a clear Slack receipt.

### 6.2 `/brain source`

Explicit source ingestion.

Examples:

```text
/brain source https://example.com/article why: useful for AI memory design
/brain source [long pasted markdown]
```

Behaviour:

```text
Short explicit takeaway:
  may produce memory cards.

Long/external material:
  store as source;
  extract durable memory cards if requested/safe.
```

### 6.3 `/brain recall`

Examples:

```text
/brain recall what do I know about knowledge graphs?
/brain recall what did I conclude about Cognee?
```

Calls Brain recall.

### 6.4 `/brain profile`

Examples:

```text
/brain profile Sam from Goldman
/brain profile Sara
```

Calls Brain profile entity.

### 6.5 `/brain open`

Lists open questions / open loops.

Optional arguments:

```text
/brain open
/brain open knowledge graphs
/brain open due
```

### 6.6 `/brain review`

Shows recent ingestions.

Must include buttons:

```text
[Inspect]
[Undo]
[Mark wrong]
[Resolve]
```

### 6.7 `/brain undo-last`

Soft-deletes the latest ingestion run for the current Slack user/session.

Never hard delete.

### 6.8 `/brain inspect`

Read-only diagnostic inspection.

Examples:

```text
/brain inspect memory mem_...
/brain inspect entity "Sam from Goldman"
/brain inspect source src_...
/brain inspect sync failed
```

### 6.9 `/brain debug`

Diagnostic tools.

Examples:

```text
/brain debug recall "Tell me everything about Sam from Goldman"
/brain debug search-memory "Sam Goldman Bill Evans"
/brain debug run-fixture sam_from_goldman
```

### 6.10 `/brain admin`

Admin-only tools.

Examples:

```text
/brain admin merge-entities ent_1 ent_2
/brain admin retry-sync failed
/brain admin sql SELECT ...
```

Admin SQL must be SELECT-only, allowlisted, logged, time-limited, and row-limited.

---

## 7. Slack message routing

Implement `slack/router.py`.

The router classifies incoming Slack messages into intents:

```text
remember
ingest_source
recall
profile_entity
list_open_loops
review_recent
undo_last
inspect
debug
admin
unknown
```

Routing rules:

```text
Explicit slash commands override LLM classification.

Free-form DM messages may be classified by the Slack Intake Agent.

Channel messages should only be handled if:
  - bot is mentioned
  - command is used
  - configured channel is allowlisted
```

Do not allow arbitrary workspace users to write memories unless allowlisted.

---

## 8. MemoryProposal model

Add a proposal layer before committing Slack ingestions.

### 8.1 Database table

Add a table or equivalent persistent model.

```sql
CREATE TABLE memory_proposals (
    id                  TEXT PRIMARY KEY,
    status              TEXT NOT NULL DEFAULT 'draft',
    raw_input           TEXT NOT NULL,
    proposed_json       JSONB NOT NULL,
    policy_version      TEXT NOT NULL,
    prompt_version      TEXT NOT NULL,
    validation_json     JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by          TEXT,
    slack_channel_id    TEXT,
    slack_message_ts    TEXT,
    committed_run_id    TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Proposal statuses:

```text
draft
pending_user
approved
committed
rejected
expired
failed
```

### 8.2 Pydantic model

```python
class MemoryProposal(BaseModel):
    id: str
    raw_input: str
    source_candidate: SourceCandidate | None = None
    memory_cards: list[MemoryCandidate] = Field(default_factory=list)
    entities: list[EntityMention] = Field(default_factory=list)
    relationships: list[RelationshipCandidate] = Field(default_factory=list)
    policy_version: str
    prompt_version: str
    created_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
```

Every Slack ingestion must create a proposal, even if it auto-commits.

---

## 9. IngestionDecision and RepairOption models

Add these models.

```python
class RepairOption(BaseModel):
    label: str
    action: Literal[
        "bind_entity",
        "create_entity",
        "rewrite_memory",
        "store_source_only",
        "store_source_and_extract",
        "approve_supersession",
        "keep_both",
        "mark_contradiction",
        "reject_proposal",
        "cancel",
    ]
    payload: dict[str, Any] = Field(default_factory=dict)
```

```python
class IngestionDecision(BaseModel):
    decision: Literal[
        "commit_success",
        "commit_with_warning",
        "needs_clarification",
        "needs_user_choice",
        "propose_repair",
        "reject_with_repair_path",
        "hard_reject",
    ]
    can_commit_now: bool
    reason_codes: list[str] = Field(default_factory=list)
    user_message: str
    proposed_memory_cards: list[MemoryCandidate] = Field(default_factory=list)
    repair_options: list[RepairOption] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    proposal_id: str | None = None
```

Reason codes:

```text
ambiguous_entity
unresolved_pronoun
unresolved_object
high_confidence_conflict
duplicate_memory
source_material_as_memory
table_too_large
no_durable_value
missing_source
malformed_input
destructive_update
low_confidence_claim
overly_broad_memory
unsupported_inference
```

---

## 10. Policy files

### 10.1 `rules/memory_policy.md`

Create this file.

```markdown
# Brain Memory Policy

You are Brain's strict Slack memory intake agent.

Your purpose is to help Daniele store durable, high-quality personal memory.

You must not store everything.

Store:
- durable facts
- family facts
- person interactions
- preferences
- decisions
- ideas
- open questions
- article takeaways
- chat conclusions
- commitments
- project state
- useful source summaries

Do not store:
- transient junk
- unresolved pronouns
- unresolved references
- duplicate facts
- unsupported assumptions
- whole transcripts as memory cards
- large tables as atomic memories
- vague notes without referents
- weather/news/current facts unless the user states why they matter personally

Always distinguish:
- source material
- memory cards
- open loops
- relationships
- conflicts
- corrections

When a memory is bad:
- do not store it
- explain the problem
- offer a repair path when possible

Ask when:
- entity identity is ambiguous
- new memory conflicts with high-confidence memory
- user implies a correction or supersession
- source cannot be fetched
- user intent is unclear
- references like "he", "she", "it", "the other one" are unresolved

Complain when:
- the memory is malformed
- the memory would pollute the graph
- the input is source material pretending to be an atomic memory
- the memory has no durable personal value
- the memory contradicts current high-confidence memory and no correction intent is clear

Confirm success:
- list exactly what was stored
- list entities created/updated
- list relationships created
- include confidence
- include buttons to inspect, undo, or mark wrong
```

### 10.2 `rules/memory_policy.yaml`

Create this file.

```yaml
version: 1

mode:
  default: strict

auto_store_thresholds:
  min_confidence: high
  allow_medium_confidence_for:
    - person_interaction
    - open_question
    - research_question
    - article_note
    - key_takeaway

require_clarification_when:
  - unresolved_pronoun
  - unresolved_object
  - multiple_entity_candidates
  - high_confidence_conflict
  - destructive_update
  - missing_source_for_claim

reject_or_complain_when:
  - no_durable_value
  - source_material_as_memory_card
  - table_too_large_for_memory
  - unsupported_inference
  - malformed_input
  - overly_broad_memory

source_policy:
  long_text_min_chars: 3000
  store_long_text_as_source: true
  extract_memories_from_sources: true
  never_store_full_transcript_as_single_memory_card: true

conflict_policy:
  default: append_only
  delete_on_conflict: false
  use_supersedes: true
  use_contradicts: true
  ask_on_high_confidence_conflict: true

entity_policy:
  do_not_overmerge: true
  create_ambiguous_entity_when_low_confidence: true
  ask_when_multiple_high_confidence_candidates: true

tables:
  max_rows_to_inline: 25
  large_table_policy: source_plus_schema_summary

success_receipts:
  include_memory_cards: true
  include_entities: true
  include_relationships: true
  include_confidence: true
  include_actions:
    - inspect
    - undo
    - mark_wrong

diagnostics:
  allow_read_only_inspection: true
  allow_arbitrary_sql: false
```

### 10.3 `rules/tool_permissions.yaml`

```yaml
tiers:
  normal:
    tools:
      - intake_dry_run
      - commit_proposal
      - remember
      - ingest_source
      - recall
      - profile_entity
      - list_open_loops
      - get_memory
      - get_source
      - review_recent
      - undo_last

  debug:
    tools:
      - inspect_memory
      - inspect_source
      - inspect_entity
      - inspect_relationships
      - inspect_open_loop
      - inspect_recent_ingestions
      - inspect_cognee_sync
      - explain_recall_plan
      - debug_search_memory
      - debug_search_entities
      - debug_retrieve_candidates
      - run_fixture

  admin:
    tools:
      - resolve_conflict
      - merge_entities
      - archive_memory
      - restore_memory
      - mark_memory_status
      - sync_cognee
      - retry_failed_sync

  dangerous:
    tools:
      - hard_delete
      - rebuild_cognee
      - prune_cognee
      - raw_sql_write
    exposed_by_default: false
```

---

## 11. Slack intake prompt

Create `prompts/slack_intake_system.md`.

```markdown
# Slack Intake Agent System Prompt

You are the Brain Slack Memory Intake Agent.

Your job is to convert Slack messages into high-quality Brain memory proposals.

You are not a general assistant.
You are not a note-taking trash can.
You are not allowed to store low-quality memories just because the user sent them.

You must follow Brain's memory policy.

Core principle:

Strict on committing.
Helpful on repairing.
Explicit on success.

For every user message, decide whether it is:

- a memory to store
- a source to ingest
- a recall query
- a profile query
- an open-loop query
- a debug/admin request
- too ambiguous to store
- not worth storing

When creating memory proposals:

1. Extract only durable memories.
2. Prefer atomic memory cards.
3. Preserve uncertainty.
4. Do not invent names, dates, places, firms, or relationships.
5. Do not resolve ambiguous people unless context is sufficient.
6. Do not store whole transcripts or long articles as memory cards.
7. Store long/external material as sources and extract durable cards.
8. Detect when a memory is a correction or supersession.
9. Ask targeted questions when needed.
10. Offer multiple-choice repairs where possible.
11. If rejecting, explain why and offer a repair path unless hard reject is necessary.
12. If successful, confirm exactly what will be or was stored.

Return strict JSON matching the MemoryProposal / IngestionDecision contract.
Do not return free-form prose unless explicitly requested by the caller.
```

---

## 12. Deterministic proposal validator

Implement `ingestion/proposal_validator.py`.

The validator must check every proposal before commit.

### 12.1 Required checks

```text
Schema validity:
  - valid memory kind
  - non-empty statement
  - valid confidence
  - valid entity types
  - valid relationship endpoints

Source/memory split:
  - long text is source, not one memory card
  - transcript is source + extracted cards
  - article is source + article_note/key_takeaways
  - large table is source/data + schema summary

Entity quality:
  - no unresolved "he", "she", "they", "it", "that one", "the other one"
  - person_interaction must have identifiable person or require clarification
  - family_fact must identify people and relationships clearly

Conflict quality:
  - high-confidence conflicts cannot auto-commit
  - corrections must create supersedes proposals
  - contradictions must create repair options

Durability:
  - reject no-durable-value memories unless user gives reason
  - weather/current trivia should not be stored by default

Safety:
  - no hard delete through ingestion
  - no raw SQL through ingestion
```

### 12.2 Validator output

The validator returns `IngestionDecision`.

Examples:

```text
Clean memory:
  COMMIT_SUCCESS or COMMIT_WITH_WARNING

Ambiguous entity:
  NEEDS_USER_CHOICE with bind_entity/create_entity options

Unresolved pronoun:
  REJECT_WITH_REPAIR_PATH or NEEDS_CLARIFICATION

High-confidence conflict:
  NEEDS_USER_CHOICE with supersede/keep/reject options

Long source:
  PROPOSE_REPAIR with store_source_only/store_source_and_extract options

No durable value:
  REJECT_WITH_REPAIR_PATH
```

---

## 13. Interaction examples

### 13.1 Successful family fact

Input:

```text
/brain remember Nur and Sara are my twin daughters.
```

Expected Slack response:

```text
Stored 1 memory.

family_fact
- Nur and Sara are your twin daughters.

Entities:
- Daniele
- Nur
- Sara

Relationships:
- Nur daughter_of Daniele
- Sara daughter_of Daniele
- Nur twin_of Sara
- Sara twin_of Nur

Confidence: high

[Inspect] [Undo] [Mark wrong]
```

### 13.2 Successful person interaction

Input:

```text
/brain remember Sam from Goldman mentioned that he likes Bill Evans.
```

Expected Slack response:

```text
Stored 1 memory.

person_interaction
- Sam from Goldman mentioned that he likes Bill Evans.

Entities:
- Sam from Goldman
- Goldman
- Bill Evans

Relationships:
- Sam from Goldman likes Bill Evans

Confidence: medium

[Inspect] [Undo] [Mark wrong]
```

### 13.3 Ambiguous entity

Input:

```text
/brain remember Sam mentioned that he likes Bill Evans.
```

If multiple Sams exist, expected response:

```text
I found multiple possible Sams. Which one should this memory attach to?

[Sam from Goldman]
[Sam from Point72]
[Create new Sam]
[Cancel]
```

No memory should be committed until the user chooses.

### 13.4 Unresolved pronoun

Input:

```text
/brain remember He prefers the other one.
```

Expected response:

```text
I can’t store this as a durable memory yet.

Problems:
- “He” is unresolved.
- “The other one” is unresolved.

Fix it:

[Choose person]
[Rewrite memory]
[Cancel]
```

No memory is committed.

### 13.5 Long source masquerading as memory

Input:

```text
/brain remember [8,000 words]
```

Expected response:

```text
This is source material, not an atomic memory.

Recommended action:
- Store the full text as a source.
- Extract durable memory cards from it.

[Store source + extract]
[Store source only]
[Cancel]
```

### 13.6 Conflict with high-confidence fact

Existing memory:

```text
Sara is Daniele’s daughter and Nur’s twin.
```

Input:

```text
/brain remember Sara is my niece.
```

Expected response:

```text
This conflicts with a high-confidence family fact.

Existing:
- Sara is your daughter and Nur’s twin.

New:
- Sara is your niece.

What should happen?

[This is a different Sara]
[Correct old memory]
[Keep as conflicted]
[Reject new]
```

No automatic overwrite.

### 13.7 Supersession

Existing memory:

```text
Sam works at Goldman.
```

Input:

```text
/brain remember Sam left Goldman and joined Point72.
```

Expected response:

```text
Possible supersession detected.

Existing:
- Sam works at Goldman.

New:
- Sam left Goldman and joined Point72.

Recommended action:
- Store the new memory.
- Mark the old memory as superseded.

[Approve supersession]
[Keep both]
[Reject new]
[Edit]
```

### 13.8 No durable value

Input:

```text
/brain remember Today’s weather is cloudy.
```

Expected response:

```text
I won’t store this by default.

Reason:
- I do not see durable personal-memory value.

If this matters, tell me why it should be remembered.

[Add reason]
[Store anyway as low-priority note]
[Cancel]
```

Default action should not store.

---

## 14. Slack formatting requirements

Use Slack Block Kit style receipts.

Each response type should have a renderer in `slack/formatter.py`.

Renderers:

```text
render_commit_success(decision)
render_commit_with_warning(decision)
render_needs_clarification(decision)
render_needs_user_choice(decision)
render_propose_repair(decision)
render_reject_with_repair_path(decision)
render_hard_reject(decision)
render_recall_response(response)
render_profile_response(response)
render_debug_result(result)
```

Every committed memory receipt must include:

```text
- memory kind
- statement
- confidence
- entities
- relationships, if any
- source ID, if any
- memory ID
- actions:
    Inspect
    Undo
    Mark wrong
```

For debug/admin responses, include:

```text
- raw object IDs
- status fields
- links
- sync status
- filtered-out items where relevant
```

---

## 15. Slack actions and modals

Implement `slack/actions.py`.

Required actions:

```text
inspect_memory
undo_ingestion
mark_wrong
choose_entity
create_entity
approve_supersession
keep_both
mark_contradiction
reject_proposal
store_source_only
store_source_and_extract
rewrite_memory
cancel_proposal
```

### 15.1 Choose entity flow

Triggered by ambiguous entity.

User chooses one of:

```text
existing entity
create new entity
cancel
```

After selection:

```text
proposal updated
validator re-runs
commit if safe
return success receipt
```

### 15.2 Rewrite memory flow

Open a modal with fields:

```text
Memory statement
Person/entity
Context/source
Optional date
```

After submission:

```text
create revised proposal
validate
commit/ask/reject
```

### 15.3 Conflict resolution flow

Buttons:

```text
Approve supersession
Keep both
Mark contradiction
Reject new
Edit
```

Behaviour:

```text
Approve supersession:
  commit new memory
  set old memory status=superseded
  create memory_link new --supersedes--> old

Keep both:
  commit new memory as current
  no supersedes link

Mark contradiction:
  commit or retain new memory as conflicted
  create memory_link new --contradicts--> old

Reject new:
  proposal status=rejected
  no memory committed
```

---

## 16. Debug and inspection tools

Implement read-only diagnostic tools for Slack verification.

These should be callable from `/brain inspect` and `/brain debug`.

### 16.1 `inspect_memory`

Input:

```json
{
  "memory_id": "mem_..."
}
```

Returns:

```text
memory_cards row
linked entities
relationships
memory_links
source
open_loop if any
cognee_sync rows
```

### 16.2 `inspect_entity`

Input:

```json
{
  "entity": "Sam from Goldman",
  "include_aliases": true,
  "include_memories": true,
  "include_relationships": true
}
```

Returns:

```text
entity row
aliases
memory_entities
relationships in/out
possible duplicates
```

### 16.3 `inspect_source`

Input:

```json
{
  "source_id": "src_...",
  "include_text": false,
  "include_cards": true
}
```

Returns:

```text
source row
linked memory cards
summary
Cognee sync status
```

### 16.4 `inspect_cognee_sync`

Input:

```json
{
  "status": "failed | pending | stale | synced | any",
  "limit": 20
}
```

Returns:

```text
sync rows
object type/id
dataset
projection hash
last error
last synced at
```

### 16.5 `explain_recall`

Input:

```json
{
  "query": "Tell me everything about Sam from Goldman",
  "mode": "profile"
}
```

Returns:

```text
planner decision
DB candidates
Cognee candidates
filtered-out memories
status filters
final evidence set
answer sections
```

### 16.6 `debug_search_memory`

Input:

```json
{
  "query": "Sam Goldman Bill Evans",
  "include_superseded": true,
  "include_deleted": false,
  "limit": 20
}
```

Returns raw candidate rows.

### 16.7 `run_fixture`

Input:

```json
{
  "fixture": "sam_from_goldman"
}
```

Runs a golden fixture and returns pass/fail details.

---

## 17. Raw SQL policy

Do not expose arbitrary SQL by default.

If implemented at all, only allow:

```text
/brain admin sql SELECT ...
```

Requirements:

```text
- admin Slack user only
- explicit command only
- never auto-called by LLM
- SELECT only
- single statement only
- timeout enforced
- row limit enforced
- no access to secrets/config tables
- query logged
- result truncated
```

Preferred first implementation:

```text
No arbitrary SQL.
Use inspect/debug tools instead.
```

---

## 18. Success receipt requirement

Every successful commit must produce a clear confirmation.

The confirmation must not merely say:

```text
Done.
```

It must state:

```text
- what was stored
- memory kind
- entities created/updated
- relationships created
- confidence
- source link if relevant
- memory IDs
- available actions
```

Example:

```text
Stored 2 memories.

1. person_interaction
   Sam from Goldman mentioned that he likes Bill Evans.
   Memory ID: mem_...
   Confidence: medium

2. relationship
   Sam from Goldman --likes--> Bill Evans.

Entities:
- Sam from Goldman
- Goldman
- Bill Evans

Actions:
[Inspect] [Undo] [Mark wrong]
```

---

## 19. Backend enforcement requirements

Prompt bias is not enforcement.

The backend must prevent bad commits even if the LLM proposes them.

Before writing to Brain DB, validate:

```text
- memory kind is valid
- statement is non-empty
- source/memory split is correct
- entities are sufficiently resolved
- relationship endpoints exist
- no unresolved pronouns in durable fact cards
- no high-confidence conflict auto-overwrite
- no large source stored as one memory card
- no large table atomized into memory cards
- no hard delete from ingestion flow
```

If validation fails:

```text
return IngestionDecision
do not write memory_cards
do not create relationships
do not update Cognee sync
```

If a source is allowed but memory extraction fails:

```text
store source if appropriate
return warning
do not invent memory cards
```

---

## 20. Auto-commit policy

Default Slack mode is strict.

Auto-commit only when:

```text
- proposal is valid
- no unresolved references
- no high-confidence conflict
- entity resolution is high confidence or not material
- memory has durable value
- source/memory split is correct
```

Examples that may auto-commit:

```text
Nur and Sara are my twin daughters.
I want to learn more about knowledge graphs.
Sam from Goldman mentioned that he likes Bill Evans.
```

Examples that should not auto-commit:

```text
He prefers the other one.
Sara is my niece.              # conflicts with daughter memory
Sam left the firm.             # ambiguous if multiple Sams/firms
[pasted 8,000 words]           # source policy choice needed
```

---

## 21. Test requirements

Do not require real Slack, real LLM, real Cognee, or real network in unit tests.

Use:

```text
FakeSlackClient
FakeLLMClient
FakeCogneeAdapter
temporary test database
mocked source fetcher
```

### 21.1 Slack ingestion tests

Add tests for:

```text
clean family fact → commit_success
clean person interaction → commit_success or commit_with_warning
clean open question → commit_success
ambiguous Sam → needs_user_choice
unresolved pronoun → reject_with_repair_path
long source → propose_repair
high-confidence conflict → needs_user_choice
no durable value → reject_with_repair_path
```

### 21.2 Slack action tests

Add tests for:

```text
choose_entity commits pending proposal
rewrite_memory creates revised proposal
approve_supersession creates supersedes link
keep_both commits without supersedes
reject_proposal writes no memory
undo_last soft-deletes ingestion run
mark_wrong opens review/correction flow
```

### 21.3 Success receipt tests

Assert success receipt includes:

```text
memory kind
statement
confidence
entities
relationships
memory ID
Inspect/Undo/Mark wrong actions
```

### 21.4 Debug/admin tests

Add tests for:

```text
normal user cannot call admin tools
admin user can inspect raw memory
debug recall returns planner/candidate/filter information
raw SQL disabled by default
raw SQL, if enabled, rejects non-SELECT
raw SQL applies limit and timeout
```

### 21.5 Backend enforcement tests

Add tests proving backend rejects bad proposals even if LLM proposes them:

```text
LLM proposes memory with unresolved pronoun → validator blocks commit
LLM proposes transcript as one memory card → validator blocks commit
LLM proposes high-confidence conflict overwrite → validator requires user choice
LLM proposes table with too many rows as memory cards → validator blocks
```

---

## 22. Implementation phases

### Phase 1 — Add Slack skeleton

Tasks:

```text
- Add slack/app.py
- Add slack/router.py
- Add slack/commands.py
- Add slack/actions.py
- Add slack/formatter.py
- Add slack/auth.py
- Add config flags
- Add fake Slack tests
```

Acceptance:

```text
- Slack disabled by default
- app can start when enabled
- slash command routing works in tests
- allowlist/admin checks work
```

### Phase 2 — Add rule/context files

Tasks:

```text
- Add rules/memory_policy.md
- Add rules/memory_policy.yaml
- Add rules/examples.yaml
- Add rules/tool_permissions.yaml
- Add prompts/slack_intake_system.md
- Add policy_loader.py
```

Acceptance:

```text
- policy version is loaded
- prompt version is loaded
- ingestion run/proposal records policy_version and prompt_version
```

### Phase 3 — Add proposal layer

Tasks:

```text
- Add memory_proposals table
- Add MemoryProposal model
- Add IngestionDecision model
- Add RepairOption model
- Add proposal store methods
```

Acceptance:

```text
- every Slack ingestion creates proposal
- proposal can be approved/rejected/committed
- dry-run proposals do not write memory cards
```

### Phase 4 — Add Slack intake agent

Tasks:

```text
- Add slack/intake_agent.py
- Integrate FakeLLMClient for tests
- Produce strict MemoryProposal/IngestionDecision JSON
- Fall back to rule compiler if LLM disabled
```

Acceptance:

```text
- LLM disabled tests still pass
- fake LLM can produce proposal
- bad LLM output is rejected safely
```

### Phase 5 — Add deterministic validator

Tasks:

```text
- Add ingestion/proposal_validator.py
- Enforce policy yaml
- Add reason codes
- Add repair options
```

Acceptance:

```text
- unresolved pronouns blocked
- source-as-memory blocked
- large table blocked
- high-confidence conflict requires user choice
- no durable value rejected with repair path
```

### Phase 6 — Add Slack repair UX

Tasks:

```text
- Implement renderers for all decision classes
- Add buttons for repair options
- Add modals for rewrite/choose entity
- Wire button payloads to proposal updates
```

Acceptance:

```text
- ambiguous entity gives multiple-choice buttons
- unresolved pronoun gives rewrite/choose options
- long source gives source-only/source+extract options
- success receipt is explicit
```

### Phase 7 — Add recall/profile/open commands

Tasks:

```text
- /brain recall
- /brain profile
- /brain open
- Slack formatting for recall/profile responses
```

Acceptance:

```text
- profile Sam works
- profile Sara works
- open knowledge graphs works
- outputs include evidence IDs
```

### Phase 8 — Add review/undo/correction

Tasks:

```text
- /brain review
- /brain undo-last
- mark_wrong action
- inspect action from receipt
```

Acceptance:

```text
- recent ingestions shown
- undo soft-deletes only relevant ingestion
- mark_wrong opens correction flow
```

### Phase 9 — Add debug inspection tools

Tasks:

```text
- inspect_memory
- inspect_entity
- inspect_source
- inspect_cognee_sync
- explain_recall
- debug_search_memory
- run_fixture
```

Acceptance:

```text
- normal users can use allowed read-only inspect tools
- admin-only tools are gated
- debug recall shows planner/candidates/filters
```

### Phase 10 — Add admin tools carefully

Tasks:

```text
- resolve_conflict
- merge_entities
- archive/restore memory
- retry_failed_sync
- optional SELECT-only SQL
```

Acceptance:

```text
- admin allowlist enforced
- destructive actions require confirmation
- SQL disabled by default
- no LLM auto-calls dangerous tools
```

---

## 23. Final acceptance criteria

The Slack agent is complete when these flows work end-to-end.

### A. Clean memory success

Input:

```text
/brain remember Nur and Sara are my twin daughters.
```

Expected:

```text
- proposal created
- validator passes
- memory committed
- explicit success receipt
- entities shown
- relationships shown
- Inspect/Undo/Mark wrong buttons shown
```

### B. Ambiguous memory repair

Input:

```text
/brain remember Sam mentioned he likes Bill Evans.
```

With multiple Sams known.

Expected:

```text
- no commit
- needs_user_choice
- buttons for candidate Sams
- choosing entity commits memory
- success receipt confirms selected entity
```

### C. Bad memory repair

Input:

```text
/brain remember He prefers the other one.
```

Expected:

```text
- no commit
- reject_with_repair_path
- explains unresolved references
- offers Choose person / Rewrite / Cancel
```

### D. Conflict flow

Input:

```text
/brain remember Sara is my niece.
```

Existing memory says Sara is daughter/twin.

Expected:

```text
- no automatic overwrite
- conflict shown
- options:
    different Sara
    correct old memory
    keep conflicted
    reject new
```

### E. Long source flow

Input:

```text
/brain remember [long markdown or transcript]
```

Expected:

```text
- not stored as one memory card
- proposes source handling
- buttons:
    Store source + extract
    Store source only
    Cancel
```

### F. Recall flow

Input:

```text
/brain profile Sam from Goldman
```

Expected:

```text
- identity
- known facts
- preferences
- interactions
- relationships
- open loops
- conflicts/uncertainties
- evidence IDs
```

### G. Debug flow

Input:

```text
/brain debug recall "Tell me everything about Sam from Goldman"
```

Expected:

```text
- planner decision
- DB candidates
- Cognee candidates if enabled
- filtered out records
- final evidence set
```

### H. Admin gating

Normal user attempts:

```text
/brain admin sql SELECT * FROM memory_cards
```

Expected:

```text
- denied
```

Admin user attempts SELECT-only SQL when enabled:

```text
/brain admin sql SELECT id, kind, status FROM memory_cards LIMIT 10
```

Expected:

```text
- allowed
- logged
- limited
- no mutations
```

---

## 24. Non-negotiables

Do not violate these.

```text
1. Slack must not bypass BrainService.

2. Slack LLM must not directly write DB rows.

3. Bad memory must not be committed just because the LLM produced it.

4. Rejections must be constructive where possible.

5. Success must be explicitly confirmed.

6. Hard delete must not be available in normal Slack ingestion.

7. Debug/admin tools must be gated.

8. Long source material must not become one giant memory card.

9. Ambiguous entities must not be silently over-merged.

10. Conflicts must use supersedes/contradicts/keep-both flows, not silent overwrite.
```

---

## 25. Summary

Implement Slack as a specialised Brain Memory Agent.

It should be:

```text
strict
interactive
repair-oriented
auditable
debuggable
separate from MCP
backed by deterministic validation
sharing the same Brain service layer
```

The target behaviour is:

```text
Good memory:
  store and confirm

Ambiguous memory:
  ask multiple-choice question

Incorrect/conflicting memory:
  complain and offer repair options

Long/source material:
  store as source and extract durable cards

Debug/testing:
  expose read-only inspection and recall explanation tools

Admin:
  gated, explicit, logged, confirmation-heavy
```