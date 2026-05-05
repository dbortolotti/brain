BRAIN REFACTOR / IMPLEMENTATION INSTRUCTIONS FOR CODING AGENT

================================================================================
MISSION
================================================================================

You are working on the repository currently structured around:

  src/memory_stack/
    brain_schema.py
    brain_models.py
    brain_store.py
    brain_service.py
    mcp_server.py
    mcp_stdio.py
    cognee_adapter.py
    ...

Goal:

  Refactor and extend the existing Brain MCP implementation into the planned
  personal memory control plane.

Do NOT scrap the repo.

The repo already has the correct skeleton:

  - Brain-owned Postgres schema
  - Memory cards
  - Sources
  - Entities
  - Relationships
  - Memory links
  - Open loops
  - High-level MCP tools
  - Cognee adapter

But it is still mostly a Phase 1 rule-based MVP. The missing pieces are:

  - robust source ingestion
  - LLM-backed memory compiler
  - entity resolution
  - duplicate/conflict detection
  - Cognee projection and sync
  - Cognee-backed recall
  - better profile rendering
  - stronger tests

Your job is to implement this in phases so nothing is missed.

================================================================================
ARCHITECTURAL INVARIANTS
================================================================================

Keep these invariants throughout the refactor.

1. Brain DB is the source of truth.

   Brain owns:
     - memory identity
     - memory lifecycle
     - entity resolution
     - relationships
     - conflicts
     - supersession
     - reminders/open loops
     - Cognee sync state

2. Cognee is a rebuildable semantic projection.

   Cognee is used for:
     - vector retrieval
     - graph retrieval
     - source recall
     - semantic enrichment

   Cognee must NOT become the only source of truth.

3. Public MCP surface must remain high-level.

   Expose:
     - brain.remember
     - brain.ingest_source
     - brain.recall
     - brain.profile_entity
     - brain.list_open_loops
     - brain.get_memory
     - brain.get_source
     - brain.resolve_conflict
     - brain.forget

   Do NOT expose low-level tools such as:
     - add
     - cognify
     - create_node_set
     - cognee_search_graph_completion
     - sql_query
     - insert_memory_card_row
     - create_entity_row

4. Source and memory are different objects.

   Source:
     Full evidence material: article, transcript, markdown, PDF, table.

   MemoryCard:
     Atomic durable memory: fact, interaction, decision, takeaway, open question.

5. Append-only conflict handling by default.

   Do NOT delete normal conflicts.
   Use:
     - supersedes
     - contradicts
     - duplicates
     - supports
     - derived_from

6. Keep deterministic tests.

   LLM-backed extraction must be mockable.
   Unit tests must not require real LLM calls or real Cognee calls.

================================================================================
PHASE 0 — BASELINE AUDIT AND SAFETY
================================================================================

Objective:

  Establish a clean baseline before changing behaviour.

Tasks:

  [ ] Create a branch:

        brain/memory-compiler-cognee-projection

  [ ] Run the current tests using the project’s intended environment.

        Prefer:
          uv run pytest

        If dependencies are missing, install with:
          uv sync

  [ ] Record current failing tests, if any.

  [ ] Inspect these files before editing:

        src/memory_stack/brain_schema.py
        src/memory_stack/brain_models.py
        src/memory_stack/brain_store.py
        src/memory_stack/brain_service.py
        src/memory_stack/mcp_server.py
        src/memory_stack/mcp_stdio.py
        src/memory_stack/cognee_adapter.py
        tests/test_brain_service.py
        tests/test_mcp_server.py

  [ ] Do not delete legacy Cognee eval files yet.
      They can be isolated later, but first preserve working behaviour.

Acceptance criteria:

  [ ] You know current test status.
  [ ] You understand current MCP tool list.
  [ ] No behavioural changes yet.

================================================================================
PHASE 1 — FIX CURRENT CORRECTNESS BUGS
================================================================================

Objective:

  Fix known correctness issues before adding new systems.

--------------------------------------------------------------------------------
1.1 Fix default memory visibility
--------------------------------------------------------------------------------

Current issue:

  brain_store.search_memory() and entity_profile() appear to exclude only
  superseded memories by default.

This means deleted/archived/rejected memories may still appear.

Required behaviour:

  Default recall/profile should include only:

    status = "current"

  Conflicted memories may be included only if:
    include_conflicts = true

  Superseded memories may be included only if:
    include_superseded = true

  Always hide by default:
    - deleted
    - rejected
    - archived
    - superseded

Implementation:

  [ ] Add a shared helper in brain_store.py or a new module:

        visible_memory_status_filter(
            include_superseded: bool = False,
            include_conflicts: bool = True
        )

  [ ] Use this helper in:
        - search_memory()
        - entity_profile()
        - any recall/profile code path

  [ ] Ensure deleted memories never appear unless explicitly requested by
      an admin/debug function.

Tests:

  [ ] Add test:
        - create current memory
        - create deleted memory
        - create archived memory
        - create superseded memory
        - recall query should return only current by default

  [ ] Add test:
        - include_superseded=true returns superseded but not deleted/rejected

--------------------------------------------------------------------------------
1.2 Fix relationship direction rendering
--------------------------------------------------------------------------------

Current issue:

  entity_profile() fetches relationships where entity is subject OR object,
  but rendering may lose direction.

Example:

  Nur --daughter_of--> Daniele

For Daniele’s profile, do NOT render:

  daughter_of Nur

Correct rendering should preserve direction:

  Nur --daughter_of--> Daniele

or semantically:

  Children:
    - Nur
    - Sara

Implementation:

  [ ] Modify profile relationship output to include:

        subject_entity_id
        subject_name
        predicate
        object_entity_id
        object_name
        direction_relative_to_profile_entity

  [ ] Update profile rendering so direction is explicit.

Tests:

  [ ] Add test using:
        "Nur and Sara are my twin daughters."

  [ ] Query:
        profile_entity("Daniele")

  [ ] Assert that output does not imply:
        Daniele daughter_of Nur

  [ ] Assert that it correctly conveys:
        Nur daughter_of Daniele
        Sara daughter_of Daniele

--------------------------------------------------------------------------------
1.3 Preserve existing golden examples
--------------------------------------------------------------------------------

Run or add tests for:

  [ ] "Nur and Sara are my twin daughters."
      Expected:
        - family_fact memory card
        - entities: Daniele, Nur, Sara
        - relationships:
            Nur daughter_of Daniele
            Sara daughter_of Daniele
            Nur twin_of Sara
            Sara twin_of Nur

  [ ] "Sam from Goldman mentioned that he likes Bill Evans."
      Expected:
        - person_interaction memory card
        - entities: Sam from Goldman, Goldman, Bill Evans
        - relationship candidate:
            Sam likes Bill Evans

  [ ] "I want to learn more about knowledge graphs."
      Expected:
        - open_question memory card
        - open_loop row
        - topic: knowledge_graphs

Acceptance criteria:

  [ ] Existing behaviour still works.
  [ ] Status filtering is correct.
  [ ] Relationship direction is correct.
  [ ] Tests pass.

================================================================================
PHASE 2 — ALIGN MCP AND REST REQUEST MODELS
================================================================================

Objective:

  Make the public API match the intended Brain tool surface.

--------------------------------------------------------------------------------
2.1 Add IngestSourceRequest
--------------------------------------------------------------------------------

Current issue:

  REST /memory/ingest_source appears to accept RememberRequest, while the MCP
  tool brain.ingest_source has a source-oriented schema.

Add model:

  class IngestSourceRequest(BaseModel):
      source: str
      source_kind: Literal[
          "auto",
          "article",
          "transcript",
          "markdown",
          "pdf",
          "email",
          "table",
          "chat_log",
          "other"
      ] = "auto"
      title: str | None = None
      why_saved: str | None = None
      extract_memories: bool = True
      dry_run: bool = False
      metadata: dict[str, Any] = Field(default_factory=dict)

Tasks:

  [ ] Add IngestSourceRequest to brain_models.py.

  [ ] Update REST endpoint:
        /memory/ingest_source

      to accept IngestSourceRequest.

  [ ] Update MCP brain.ingest_source to call the same service method.

  [ ] Preserve backwards compatibility only if already used by tests.
      If compatibility is needed, support both request shapes internally.

Tests:

  [ ] brain.ingest_source with article URL works.
  [ ] brain.ingest_source with raw markdown works.
  [ ] dry_run=true does not write DB rows.

--------------------------------------------------------------------------------
2.2 Ensure MCP tools return structured content
--------------------------------------------------------------------------------

Each MCP tool should return both:

  - human-readable text
  - structured JSON payload

Tasks:

  [ ] Review mcp_server.py and mcp_stdio.py.

  [ ] Ensure each tool has stable structured output.

  [ ] Do not expose internal SQLAlchemy rows directly.

Acceptance criteria:

  [ ] MCP tests confirm tool list contains exactly high-level Brain tools.
  [ ] Old low-level Cognee tools are not exposed.
  [ ] Structured responses are stable enough for clients.

================================================================================
PHASE 3 — RESTRUCTURE WITHOUT BREAKING BEHAVIOUR
================================================================================

Objective:

  Split brain_service.py into proper components while preserving behaviour.

Current likely issue:

  brain_service.py contains orchestration, rule-based extraction, recall,
  profile rendering, conflict operations, and source logic.

Target structure:

  src/memory_stack/ingestion/
    __init__.py
    orchestrator.py
    classifier.py
    rule_compiler.py
    memory_compiler.py
    article_loader.py
    transcript_parser.py
    table_parser.py

  src/memory_stack/resolution/
    __init__.py
    entity_resolver.py
    duplicate_detector.py
    conflict_detector.py

  src/memory_stack/recall/
    __init__.py
    planner.py
    retriever.py
    evidence_builder.py
    profile_builder.py
    synthesizer.py

  src/memory_stack/cognee/
    __init__.py
    serializers.py
    projector.py
    sync_worker.py
    rebuild.py

Tasks:

  [ ] Move existing rule-based compile_input logic into:
        ingestion/rule_compiler.py

  [ ] Keep brain_service.py as an orchestration facade initially.

  [ ] Move profile rendering logic into:
        recall/profile_builder.py

  [ ] Move recall query planning/retrieval into:
        recall/planner.py
        recall/retriever.py

  [ ] Do not change external API behaviour in this phase.

  [ ] Update imports and tests.

Acceptance criteria:

  [ ] Existing tests still pass.
  [ ] brain_service.py is thinner.
  [ ] Rule-based compiler still handles golden examples.
  [ ] No new feature work until this refactor is stable.

================================================================================
PHASE 4 — SOURCE INGESTION PIPELINE
================================================================================

Objective:

  Implement real source handling.

A source is full evidence-bearing material:
  - article
  - transcript
  - markdown
  - PDF
  - table
  - chat log
  - email
  - raw long text

Current limitation:

  URL ingestion likely stores the URL but does not fetch content.
  Long text creates a shallow source_summary.
  Transcript/table extraction is minimal.

--------------------------------------------------------------------------------
4.1 Source classification
--------------------------------------------------------------------------------

Implement source classification in ingestion/classifier.py.

Input:

  IngestSourceRequest or RememberRequest

Output:

  SourceClassification:
    - source_kind
    - should_create_source
    - should_extract_memories
    - reason
    - confidence

Rules:

  - URL → article source unless explicitly other
  - long markdown/text → markdown or transcript depending on structure
  - table-looking text → table
  - short fact/thought → memory only
  - uploaded file path / PDF → source

--------------------------------------------------------------------------------
4.2 Article loader
--------------------------------------------------------------------------------

Implement ingestion/article_loader.py.

MVP behaviour:

  [ ] Accept URL.
  [ ] Fetch content if network is available in runtime.
  [ ] Extract readable title and text if possible.
  [ ] If fetching fails, still store source with:
        raw_text = URL or provided text
        status = failed or processed_with_warning
        metadata.fetch_error = ...
  [ ] Do not fail entire ingestion just because fetch failed.

Tests must mock network.

--------------------------------------------------------------------------------
4.3 Transcript parser
--------------------------------------------------------------------------------

Implement ingestion/transcript_parser.py.

MVP behaviour:

  [ ] Detect speaker lines when obvious.
  [ ] Extract participants.
  [ ] Preserve full transcript as source.
  [ ] Feed transcript text into memory compiler for card extraction.

Do not try to perfectly diarize transcripts in MVP.

--------------------------------------------------------------------------------
4.4 Table parser
--------------------------------------------------------------------------------

Implement ingestion/table_parser.py.

MVP behaviour:

  [ ] Detect markdown table.
  [ ] Detect CSV-like text.
  [ ] Parse headers and rows for small tables.
  [ ] Store original table as source.
  [ ] Create table_note card with:
        columns
        row_count
        sample_rows
        semantic summary

Limits:

  If row_count > configured threshold:
    - store source
    - store schema/summary only
    - do not create one card per row by default

--------------------------------------------------------------------------------
4.5 Source sync marking
--------------------------------------------------------------------------------

When a source is created, mark Cognee sync pending:

  object_type = "source"
  object_id   = source_id
  dataset     = "sources"

Current code appears to mark only memory cards pending.

Tasks:

  [ ] Add source sync marking in source creation path.
  [ ] Add tests.

Acceptance criteria:

  [ ] Article URL creates source row.
  [ ] Long markdown creates source row.
  [ ] Transcript creates source row.
  [ ] Small table creates source row + table_note.
  [ ] New source has cognee_sync pending row.
  [ ] Tests do not require live network.

================================================================================
PHASE 5 — LLM-BACKED MEMORY COMPILER
================================================================================

Objective:

  Add a real memory compiler that can extract multiple atomic memory cards from
  messy input and sources.

Do not remove the rule-based compiler. Keep it as:
  - fast path for simple golden examples
  - deterministic fallback
  - test baseline

--------------------------------------------------------------------------------
5.1 Add provider-agnostic LLM interface
--------------------------------------------------------------------------------

Create:

  src/memory_stack/llm/
    __init__.py
    client.py
    models.py
    fake.py

Interface:

  class LLMClient:
      def complete_json(self, prompt: str, schema: dict, **kwargs) -> dict:
          ...

Implement:

  - FakeLLMClient for tests
  - Real provider stub if env vars are available
  - No real provider calls in unit tests

Config:

  BRAIN_LLM_ENABLED=false by default in tests
  BRAIN_LLM_PROVIDER=...
  BRAIN_LLM_MODEL=...

--------------------------------------------------------------------------------
5.2 Memory compiler output contract
--------------------------------------------------------------------------------

The LLM compiler must return strict JSON:

  {
    "classification": "article | transcript | person_interaction | ...",
    "source": {
      "should_create": true,
      "kind": "article",
      "title": "...",
      "summary": "..."
    },
    "memory_cards": [
      {
        "kind": "person_interaction",
        "statement": "...",
        "summary": "...",
        "entities": [
          {
            "name": "...",
            "type": "person | organization | place | concept | project | artifact",
            "role": "subject | object | mentioned | topic | location | affiliation_context",
            "alias": null
          }
        ],
        "topics": ["..."],
        "relationships": [
          {
            "subject": "...",
            "predicate": "...",
            "object": "...",
            "confidence": "low | medium | high"
          }
        ],
        "confidence": "low | medium | high",
        "observed_at": null,
        "source_quote": null,
        "open_loop": null
      }
    ],
    "possible_conflicts": [],
    "questions_for_user": []
  }

Rules:

  [ ] Preserve uncertainty.
  [ ] Do not invent surnames, dates, firms, or relationships.
  [ ] Direct user statement can be high confidence.
  [ ] Extract multiple cards when source contains multiple durable memories.
  [ ] Reject transient chat filler.
  [ ] Create open loops for "I want to learn..." / "I wonder..." / "need to research..."
  [ ] Ask questions only when ambiguity materially changes storage.

--------------------------------------------------------------------------------
5.3 Compiler routing
--------------------------------------------------------------------------------

Implement:

  ingestion/memory_compiler.py

Routing:

  def compile_memory(input, context):
      result = rule_compiler.try_compile(input)
      if result.confidence == "high" and result.sufficient:
          return result

      if settings.llm_enabled:
          return llm_compiler.compile(input, context)

      return rule_compiler.compile_fallback(input)

Acceptance criteria:

  [ ] Existing tests pass with LLM disabled.
  [ ] New tests can inject FakeLLMClient.
  [ ] Messy transcript fixture produces multiple cards via fake LLM output.
  [ ] Article fixture produces article_note + key_takeaways + open_question.

================================================================================
PHASE 6 — ENTITY RESOLUTION
================================================================================

Objective:

  Move beyond exact name/alias matching.

Create:

  src/memory_stack/resolution/entity_resolver.py

Target flow:

  1. Exact normalized name match
  2. Alias match
  3. Contextual match:
       organization
       location
       source
       project
  4. Semantic/LLM adjudication later
  5. User confirmation only if material

EntityResolution result:

  {
    "entity_id": "...",
    "action": "matched | created | alias_added | ambiguous",
    "confidence": "low | medium | high",
    "reason": "..."
  }

Tasks:

  [ ] Extract entity resolution logic out of BrainStore.
  [ ] Preserve exact/alias behaviour.
  [ ] Add contextual matching for common patterns:
        "Sam from Goldman"
        "Sam at Goldman Sachs"
        "Sam / Goldman"
  [ ] Add alias candidate support if not already present.
  [ ] Do not over-merge low-confidence entities.

Tests:

  [ ] "Sam from Goldman" then "Sam at Goldman" resolves same entity.
  [ ] "Sam from Goldman" and "Sam from Point72" do not automatically merge
      unless strong evidence exists.
  [ ] Alias lookup works.
  [ ] Low-confidence ambiguity is stored, not guessed.

================================================================================
PHASE 7 — DUPLICATE AND CONFLICT DETECTION
================================================================================

Objective:

  Detect duplicates, additive memories, supersessions, and contradictions.

Create:

  src/memory_stack/resolution/duplicate_detector.py
  src/memory_stack/resolution/conflict_detector.py

Conflict classes:

  duplicate:
    Same fact, same meaning.
    Usually do not create new card unless source adds useful provenance.

  additive:
    Both can be true.
    Keep both.

  supersedes:
    New memory replaces old memory.
    New status = current.
    Old status = superseded.
    Link new --supersedes--> old.

  contradicts:
    Both cannot be true, not automatically resolvable.
    Link new --contradicts--> old.
    Mark conflicted if needed.

  correction:
    Explicit "actually..." / "correction..." update.
    Treat as supersedes.

MVP algorithm:

  [ ] For each new candidate card, find similar current cards:
        - same main entity
        - similar kind
        - overlapping topics
        - lexical similarity / simple embedding later

  [ ] Classify relationship using:
        - deterministic heuristics first
        - LLM classifier if enabled

  [ ] Apply safe default:
        - if uncertain, keep both
        - do not delete
        - surface possible conflict in receipt

Tests:

  [ ] Duplicate:
        Sam likes Bill Evans.
        Sam likes Bill Evans.
      Expected:
        no duplicate current card, or duplicate link if retained.

  [ ] Additive:
        Sam likes Bill Evans.
        Sam likes Sonny Rollins.
      Expected:
        both current.

  [ ] Supersession:
        Sam works at Goldman.
        Sam left Goldman and joined Point72.
      Expected:
        old superseded, new current, supersedes link.

  [ ] Correction:
        Actually, Sam likes early Coltrane, not Bill Evans.
      Expected:
        old superseded, new current.

  [ ] Contradiction:
        Sam has two children.
        Sam has no children.
      Expected:
        contradiction link or conflicted status.

================================================================================
PHASE 8 — COGNEE PROJECTION AND SYNC
================================================================================

Objective:

  Actually project Brain records into Cognee.

Current state:

  cognee_adapter.py exists.
  cognee_sync table exists.
  memory cards are marked pending.
  Actual projection/sync is not fully wired.

--------------------------------------------------------------------------------
8.1 Serializers
--------------------------------------------------------------------------------

Create:

  src/memory_stack/cognee/serializers.py

Implement:

  serialize_memory_for_cognee(memory_id) -> str
  serialize_source_for_cognee(source_id) -> str
  node_sets_for_memory(memory) -> list[str]
  node_sets_for_source(source) -> list[str]

Memory projection must include:

  memory_id
  kind
  status
  confidence
  observed_at
  entities
  relationships
  topics
  statement
  summary
  source_id
  source_quote

Example:

  memory_id: mem_20260505_001
  kind: person_interaction
  status: current
  confidence: medium
  observed_at: 2026-05-05

  entities:
    - Sam from Goldman [person, subject]
    - Goldman [organization, affiliation_context]
    - Bill Evans [person, topic]

  relationships:
    - Sam from Goldman --likes--> Bill Evans

  topics:
    - jazz

  statement:
    Sam from Goldman mentioned that he likes Bill Evans.

  source:
    manual_note

Source projection must include:

  source_id
  kind
  title
  uri
  summary
  raw_text or truncated/managed full text
  metadata

--------------------------------------------------------------------------------
8.2 Projector
--------------------------------------------------------------------------------

Create:

  src/memory_stack/cognee/projector.py

Implement:

  project_memory(memory_id)
  project_source(source_id)
  mark_projection_stale(object_type, object_id)
  enqueue_projection(object_type, object_id, dataset)

Use cognee_adapter.py for actual Cognee calls.

MVP:

  - Use serialized text ingestion.
  - Do not implement custom Cognee DataPoints yet.
  - Always embed Brain IDs in text.
  - Use datasets:
      memory
      sources
      data

--------------------------------------------------------------------------------
8.3 Sync worker
--------------------------------------------------------------------------------

Create:

  src/memory_stack/cognee/sync_worker.py

Implement:

  sync_pending_cognee(limit=100)
  sync_one(sync_id)
  retry_failed(limit=100)

Behaviour:

  [ ] Read pending/stale rows from cognee_sync.
  [ ] Serialize object.
  [ ] Send to Cognee dataset.
  [ ] Mark synced with projection_hash.
  [ ] On failure, mark failed with error_message.
  [ ] Do not delete Brain DB rows if Cognee sync fails.

--------------------------------------------------------------------------------
8.4 Rebuild command
--------------------------------------------------------------------------------

Create:

  src/memory_stack/cognee/rebuild.py

Implement CLI or callable:

  brain cognee rebuild --dataset memory
  brain cognee rebuild --dataset sources
  brain cognee rebuild --all

MVP behaviour:

  [ ] Mark all relevant projections stale.
  [ ] Optionally prune Cognee dataset only with explicit confirmation.
  [ ] Reproject all non-deleted Brain records.

--------------------------------------------------------------------------------
8.5 Tests
--------------------------------------------------------------------------------

Use fake Cognee adapter.

Tests:

  [ ] Memory card projection contains memory_id.
  [ ] Source projection contains source_id.
  [ ] Pending sync row becomes synced after fake adapter success.
  [ ] Failed adapter call marks sync failed and preserves Brain DB state.
  [ ] Source creation creates pending source sync row.
  [ ] Memory update marks projection stale.

Acceptance criteria:

  [ ] Cognee projection is real but optional.
  [ ] Brain still works if Cognee unavailable.
  [ ] Cognee can be rebuilt from Brain DB.

================================================================================
PHASE 9 — COGNEE-BACKED RECALL
================================================================================

Objective:

  Combine deterministic Brain DB lookup with Cognee semantic recall.

Current state:

  brain.recall appears DB-first lexical only.
  Cognee adapter exists but is not wired into Brain recall.

Create/complete:

  src/memory_stack/recall/planner.py
  src/memory_stack/recall/retriever.py
  src/memory_stack/recall/evidence_builder.py
  src/memory_stack/recall/synthesizer.py

--------------------------------------------------------------------------------
9.1 Recall planner
--------------------------------------------------------------------------------

Modes:

  auto
  profile
  evidence
  open_loops
  sources
  memories
  debug

Planner should infer:

  "Tell me everything about Sam from Goldman"
    → profile

  "What open ideas do I have about knowledge graphs?"
    → open_loops + concept recall

  "What did I conclude about Cognee?"
    → memories + sources

  "Show me source-backed facts about X"
    → evidence

--------------------------------------------------------------------------------
9.2 Retrieval strategy
--------------------------------------------------------------------------------

For each recall:

  1. DB deterministic retrieval:
       - entity lookup
       - memory_entities
       - relationships
       - memory_links
       - sources
       - open_loops

  2. Cognee retrieval if enabled:
       - dataset memory
       - dataset sources when include_sources=true
       - query contains user query plus identified entity names
       - retrieve serialized projections containing memory_id/source_id

  3. Merge:
       - parse memory_id/source_id from Cognee results
       - hydrate records from Brain DB
       - filter by status
       - de-duplicate

Config:

  BRAIN_COGNEE_RECALL_ENABLED=false by default in tests
  BRAIN_COGNEE_RECALL_TOP_K=10

--------------------------------------------------------------------------------
9.3 Evidence builder
--------------------------------------------------------------------------------

Evidence items should include:

  {
    "memory_id": "...",
    "source_id": "...",
    "quote": "...",
    "confidence": "...",
    "status": "current"
  }

Separate:

  - facts
  - inferences
  - open loops
  - conflicts
  - superseded memories, if requested

--------------------------------------------------------------------------------
9.4 Synthesizer
--------------------------------------------------------------------------------

MVP can be deterministic text rendering.

Later can use LLM synthesis.

Profile output sections:

  Identity
  Known facts
  Preferences
  Interactions
  Relationships
  Open loops
  Conflicts / uncertainties
  Evidence

Concept output sections:

  What I know
  Saved sources
  My takeaways
  Open questions
  Related people/projects

Tests:

  [ ] profile_entity("Sam from Goldman") includes DB facts.
  [ ] recall("knowledge graphs") returns open_question.
  [ ] deleted/superseded memories hidden by default.
  [ ] fake Cognee result with memory_id is hydrated from Brain DB.
  [ ] Cognee unavailable does not break DB recall.

Acceptance criteria:

  [ ] Brain recall works without Cognee.
  [ ] Brain recall improves with Cognee enabled.
  [ ] Brain never trusts Cognee text without hydrating Brain IDs when possible.

================================================================================
PHASE 10 — ADMIN TOOLS
================================================================================

Objective:

  Add later/admin tools only after core recall/projection is stable.

Add MCP tools:

  brain.review_recent
  brain.undo_last
  brain.sync_cognee
  brain.rebuild_cognee
  brain.merge_entities

--------------------------------------------------------------------------------
10.1 brain.review_recent
--------------------------------------------------------------------------------

Use case:

  "What did Brain store today?"

Input:

  {
    "since": "optional datetime",
    "limit": 20,
    "include_sources": true
  }

Output:

  Recent ingestion runs, sources, memory cards, conflicts.

--------------------------------------------------------------------------------
10.2 brain.undo_last
--------------------------------------------------------------------------------

Use case:

  Slack quick undo.

Behaviour:

  [ ] Soft-delete objects created by one ingestion_run.
  [ ] Mark Cognee projections stale/deleted.
  [ ] Never hard delete by default.

--------------------------------------------------------------------------------
10.3 brain.sync_cognee
--------------------------------------------------------------------------------

Manual sync tool.

Input:

  {
    "object_type": "memory | source | data | all",
    "object_id": "optional",
    "dataset": "memory | sources | data | all",
    "force": false
  }

--------------------------------------------------------------------------------
10.4 brain.rebuild_cognee
--------------------------------------------------------------------------------

Dangerous/admin.

Input:

  {
    "dataset": "memory | sources | data | all",
    "prune_first": false,
    "confirm": false
  }

Rules:

  [ ] If prune_first=true, require confirm=true.
  [ ] Do not let ordinary recall/remember flows call this.

--------------------------------------------------------------------------------
10.5 brain.merge_entities
--------------------------------------------------------------------------------

Entity hygiene.

Input:

  {
    "primary_entity_id": "...",
    "duplicate_entity_id": "...",
    "reason": "...",
    "confirm": false
  }

Behaviour:

  [ ] Move aliases.
  [ ] Repoint memory_entities.
  [ ] Repoint relationships.
  [ ] Archive duplicate entity.
  [ ] Add audit link/metadata.

Acceptance criteria:

  [ ] Admin tools are tested.
  [ ] Dangerous tools require confirmation.
  [ ] Default MCP flow remains simple.

================================================================================
PHASE 11 — REMINDERS AND OPEN LOOPS
================================================================================

Objective:

  Make open questions useful.

Current state:

  open_loops table/listing exists.

Add:

  src/memory_stack/workers/reminders.py
  src/memory_stack/workers/scheduler.py

Reminder modes:

  1. Scheduled digest
     Example:
       weekly list of open questions

  2. Opportunistic recall
     Example:
       when current topic is knowledge graphs, surface:
       "You previously wanted to learn more about knowledge graphs."

Tasks:

  [ ] Add open_loop fields if missing:
        priority
        next_review_at
        last_reminded_at
        reminder_policy

  [ ] Implement:
        list_due_open_loops()
        mark_reminded(loop_id)
        find_relevant_open_loops(topic/query)

  [ ] Add suppression:
        - do not remind if recently reminded
        - do not remind archived/closed loops
        - require relevance threshold

Tests:

  [ ] Open question creates open_loop.
  [ ] Closed loop not returned.
  [ ] Recently reminded loop suppressed unless include_recently_reminded=true.
  [ ] Topic query retrieves relevant open loop.

================================================================================
PHASE 12 — SLACK INGESTION AGENT
================================================================================

Objective:

  Add low-friction capture after MCP/core is stable.

Do NOT start here.

Add:

  src/memory_stack/slack/
    app.py
    commands.py
    formatter.py

Commands:

  /brain remember <text>
  /brain article <url> [why]
  /brain transcript
  /brain recall <query>
  /brain profile <entity>
  /brain open
  /brain review
  /brain undo-last

Rules:

  [ ] Slack bot should call Brain API/MCP service methods.
  [ ] Slack bot should not bypass Brain DB.
  [ ] Slack receipt should be concise and structured.
  [ ] Slack undo should soft-delete one ingestion run.

Receipt example:

  Stored 3 memories.

  1. family_fact
     Nur and Sara are your twin daughters.

  2. open_question
     You want to learn more about knowledge graphs.

  3. person_interaction
     Sam from Goldman mentioned that he likes Bill Evans.

  Entities created/updated:
    - Nur
    - Sara
    - Sam from Goldman
    - Goldman
    - Bill Evans

  No conflicts detected.

Acceptance criteria:

  [ ] Slack commands tested with mocked Slack client.
  [ ] No secrets committed.
  [ ] Slack is optional and disabled by default.

================================================================================
PHASE 13 — MIGRATIONS AND PACKAGING
================================================================================

Objective:

  Make DB changes production-safe.

Current schema may be defined directly in brain_schema.py.
Add proper migrations if not already present.

Tasks:

  [ ] Add Alembic if not already configured.
  [ ] Create initial migration matching current schema.
  [ ] Add migration for any new columns/tables.
  [ ] Ensure tests can use in-memory SQLite or test Postgres, depending on current setup.
  [ ] Document DB setup in README.

Required docs:

  README.md update with:
    - local dev setup
    - running MCP server
    - running tests
    - environment variables
    - Cognee optional config
    - LLM optional config
    - Slack optional config

Acceptance criteria:

  [ ] Fresh checkout can create schema.
  [ ] Tests run from clean DB.
  [ ] No manual schema setup required.

================================================================================
PHASE 14 — EVALUATION HARNESS
================================================================================

Objective:

  Turn the old Cognee eval harness into Brain evals.

Current repo has legacy eval files. Do not delete until replaced.

Create:

  src/memory_stack/evals/
    golden_queries.py
    fixtures/
    metrics.py

Golden ingestion fixtures:

  1. "Nur and Sara are my twin daughters."
  2. "Sam from Goldman mentioned that he likes Bill Evans."
  3. "I want to learn more about knowledge graphs."
  4. Long markdown chat summary.
  5. Article text with multiple takeaways.
  6. Small preference table.
  7. Contradiction/update about Sam.
  8. Conversation transcript with multiple durable facts.

Golden recall queries:

  1. Tell me everything about Sam from Goldman.
  2. Who are my daughters?
  3. What open questions do I have about knowledge graphs?
  4. What did I conclude about Brain/Cognee?
  5. What articles have I saved about AI memory?
  6. What facts about Sam are uncertain or stale?

Metrics:

  - memory-card extraction precision
  - entity resolution accuracy
  - duplicate rate
  - conflict detection precision
  - recall precision@k
  - groundedness
  - unsupported claim count
  - latency
  - LLM cost per ingestion
  - Cognee sync failure rate

Acceptance criteria:

  [ ] Golden fixtures run in CI.
  [ ] Fake LLM and fake Cognee are supported.
  [ ] Evals do not require live external services.

================================================================================
PHASE 15 — CLEANUP LEGACY STRUCTURE
================================================================================

Objective:

  Reduce conceptual noise after Brain path is stable.

Current repo has two personalities:

  A. Legacy Cognee eval harness
  B. Brain 2.0 memory control plane

Tasks:

  [ ] Move legacy files under:
        src/memory_stack/legacy_eval/

      or clearly mark as legacy in docs.

  [ ] Ensure primary README focuses on Brain, not Cognee evals.

  [ ] Keep useful eval cases by porting them to Brain eval harness.

  [ ] Remove dead code only after tests prove it is unused.

Acceptance criteria:

  [ ] New contributor sees Brain architecture first.
  [ ] Legacy tools do not appear as primary interface.
  [ ] No accidental removal of useful tests.

================================================================================
GLOBAL TEST REQUIREMENTS
================================================================================

Every phase must end with tests.

Minimum command:

  uv run pytest

If using markers:

  uv run pytest tests/test_brain_service.py
  uv run pytest tests/test_mcp_server.py
  uv run pytest tests/test_cognee_projection.py
  uv run pytest tests/test_recall.py
  uv run pytest tests/test_conflicts.py

Required test categories:

  1. Schema/model tests
  2. Ingestion tests
  3. Entity resolution tests
  4. Conflict tests
  5. Recall/profile tests
  6. MCP tool tests
  7. Cognee projection tests with fake adapter
  8. Source ingestion tests with mocked network/files
  9. Open-loop/reminder tests

Do not introduce real network, real LLM, real Slack, or real Cognee dependencies
into unit tests.

================================================================================
CONFIGURATION REQUIREMENTS
================================================================================

Add/confirm settings:

  BRAIN_DATABASE_URL
  BRAIN_LLM_ENABLED=false
  BRAIN_LLM_PROVIDER
  BRAIN_LLM_MODEL
  BRAIN_COGNEE_ENABLED=false
  BRAIN_COGNEE_RECALL_ENABLED=false
  BRAIN_COGNEE_MEMORY_DATASET=memory
  BRAIN_COGNEE_SOURCES_DATASET=sources
  BRAIN_COGNEE_DATA_DATASET=data
  BRAIN_COGNEE_RECALL_TOP_K=10
  BRAIN_SLACK_ENABLED=false
  BRAIN_LOG_LEVEL=INFO

Defaults:

  - LLM disabled in tests.
  - Cognee disabled in tests unless fake adapter injected.
  - Slack disabled by default.
  - Hard delete disabled unless explicitly confirmed.

================================================================================
CODING STYLE AND DESIGN RULES
================================================================================

1. Keep orchestration separate from storage.

   BrainStore:
     DB operations only.

   BrainService:
     high-level orchestration.

   ingestion/*:
     classification and memory extraction.

   resolution/*:
     entity/duplicate/conflict logic.

   recall/*:
     query planning, retrieval, profile building, synthesis.

   cognee/*:
     projection, sync, rebuild.

2. Keep tool schemas stable.

   Existing MCP clients may depend on:
     brain.remember
     brain.recall
     brain.profile_entity
     brain.list_open_loops

3. Prefer explicit objects over loose dicts.

   Use Pydantic models for:
     - requests
     - responses
     - compiler outputs
     - conflict classifications
     - entity resolution results

4. Preserve Brain IDs in all projections.

   Cognee text must include:
     memory_id
     source_id
     entity names
     status
     kind

5. Do not hide uncertainty.

   Memory cards and relationships must carry confidence.

6. Do not over-merge entities.

   If uncertain, create separate entity or mark ambiguity.

7. Do not silently overwrite.

   Use supersedes/contradicts links.

8. Do not make the user maintain node sets.

   Generate node sets automatically.

================================================================================
FINAL ACCEPTANCE CRITERIA
================================================================================

The refactor is successful when the following work end-to-end:

--------------------------------------------------------------------------------
A. Basic family fact
--------------------------------------------------------------------------------

Input:

  brain.remember("Nur and Sara are my twin daughters.")

Expected:

  - family_fact memory card
  - entities:
      Daniele
      Nur
      Sara
  - relationships:
      Nur daughter_of Daniele
      Sara daughter_of Daniele
      Nur twin_of Sara
      Sara twin_of Nur
  - recall("Who are my daughters?") returns Nur and Sara
  - profile_entity("Sara") returns daughter/twin relationship correctly

--------------------------------------------------------------------------------
B. Person interaction
--------------------------------------------------------------------------------

Input:

  brain.remember("Sam from Goldman mentioned that he likes Bill Evans.")

Expected:

  - person_interaction memory card
  - entities:
      Sam from Goldman
      Goldman
      Bill Evans
  - relationship:
      Sam from Goldman likes Bill Evans
  - profile_entity("Sam from Goldman") returns:
      identity
      preference
      interaction
      uncertainty around surname if unknown
      evidence memory ID

--------------------------------------------------------------------------------
C. Open question
--------------------------------------------------------------------------------

Input:

  brain.remember("I want to learn more about knowledge graphs.")

Expected:

  - open_question memory card
  - open_loop row
  - topic knowledge_graphs
  - list_open_loops(topic="knowledge graphs") returns it
  - recall("What open ideas do I have about knowledge graphs?") returns it

--------------------------------------------------------------------------------
D. Article source
--------------------------------------------------------------------------------

Input:

  brain.ingest_source(source="<article url>", source_kind="article", why_saved="Useful for AI memory design.")

Expected:

  - source row
  - article_note card
  - one or more key_takeaway cards if extract_memories=true
  - possible open_question cards
  - all cards linked to source_id
  - Cognee source sync pending
  - Cognee memory sync pending

--------------------------------------------------------------------------------
E. Long chat summary
--------------------------------------------------------------------------------

Input:

  long markdown summary of a chat

Expected:

  - source row
  - multiple memory cards:
      decisions
      design principles
      open questions
      chat conclusions
  - not stored as one giant memory card only

--------------------------------------------------------------------------------
F. Conflict handling
--------------------------------------------------------------------------------

Inputs:

  brain.remember("Sam works at Goldman.")
  brain.remember("Sam left Goldman and joined Point72.")

Expected:

  - second memory current
  - first memory superseded
  - memory link:
      second --supersedes--> first
  - profile excludes old fact by default
  - include_superseded=true surfaces history

--------------------------------------------------------------------------------
G. Cognee projection
--------------------------------------------------------------------------------

After sync:

  - memory cards projected to Cognee memory dataset
  - sources projected to Cognee sources dataset
  - serialized projection includes Brain IDs
  - Cognee failure does not corrupt Brain DB
  - rebuild can reproject from Brain DB

--------------------------------------------------------------------------------
H. MCP surface
--------------------------------------------------------------------------------

MCP exposes:

  - brain.remember
  - brain.ingest_source
  - brain.recall
  - brain.profile_entity
  - brain.list_open_loops
  - brain.get_memory
  - brain.get_source
  - brain.resolve_conflict
  - brain.forget

MCP does NOT expose:

  - add
  - cognify
  - create_node_set
  - cognee_search_graph_completion
  - sql_query

================================================================================
IMPLEMENTATION ORDER SUMMARY
================================================================================

Do the phases in this order:

  Phase 0   Baseline audit
  Phase 1   Correctness fixes: visibility + relationship direction
  Phase 2   Align MCP/REST request models
  Phase 3   Restructure modules without behaviour change
  Phase 4   Source ingestion pipeline
  Phase 5   LLM-backed memory compiler
  Phase 6   Entity resolution
  Phase 7   Duplicate/conflict detection
  Phase 8   Cognee projection and sync
  Phase 9   Cognee-backed recall
  Phase 10  Admin tools
  Phase 11  Reminders and open loops
  Phase 12  Slack ingestion agent
  Phase 13  Migrations and packaging
  Phase 14  Brain eval harness
  Phase 15  Legacy cleanup

Primary near-term PR should include only Phases 1–3 plus tests.

Second PR should include Phases 4–5.

Third PR should include Phases 6–9.

Do not attempt every phase in one PR.