BRAIN — PERSONAL MEMORY APP DESIGN / HANDOVER PLAN

================================================================================
0. EXECUTIVE SUMMARY
================================================================================

Brain is a personal memory application exposed via MCP and optionally Slack.

Core user experience:

  "remember this"
  "what do I know about X?"
  "tell me everything about Sam from Goldman"
  "what open ideas do I have about knowledge graphs?"

Core architecture:

  User / Slack / Claude / files / URLs
          ↓
  Brain ingestion agent
          ↓
  Source extraction + memory-card extraction
          ↓
  Brain relational control plane
          ↓
  Cognee semantic graph/vector projection
          ↓
  Brain recall agent
          ↓
  Evidence-aware answer

Key architectural decision:

  Brain is the source of truth for:
    - memory identity
    - memory lifecycle
    - conflicts
    - supersession
    - entity resolution
    - reminders
    - recall policy

  Cognee is the semantic retrieval substrate:
    - graph retrieval
    - vector retrieval
    - source/document recall
    - cross-memory synthesis

Cognee should be treated as a rebuildable index/projection, not as the sole
application database.

================================================================================
1. PRODUCT GOAL
================================================================================

Brain should avoid two failure modes:

  1. Filing-cabinet memory
     Manual datasets, folders, tags, node sets, project splits, and maintenance.

  2. Junk-drawer memory
     Everything gets embedded and stored; recall becomes noisy, stale, and weak.

The goal is a low-maintenance personal memory layer where the user does not need
to decide how to file things.

The user should not need to decide:

  - Is this a person memory?
  - Is this an idea?
  - Should this be in a people dataset?
  - Should I create a node set?
  - Should I delete the old version?
  - Should I run cognify?

The system should decide:

  - whether the input is worth remembering
  - whether it is a source, a memory, or both
  - what entities are involved
  - whether it conflicts with existing memory
  - whether it should create an open loop/reminder
  - how to project it into Cognee

================================================================================
2. CORE DESIGN PRINCIPLES
================================================================================

2.1 Few datasets, rich objects

Do NOT create datasets like:

  people
  places
  experiences
  ideas
  articles
  restaurants
  projects

Those are semantic categories, not storage boundaries.

A single memory can be many things at once:

  "Dinner at Brutto with Sam from Goldman. He mentioned he likes Bill Evans
   and is interested in AI infrastructure."

This is simultaneously:

  - person memory
  - place memory
  - experience
  - jazz memory
  - AI idea
  - relationship note
  - possible follow-up

So it should not be manually filed into a single semantic dataset.

Use datasets only for storage behaviour:

  memory    = distilled memory cards
  sources   = full articles, transcripts, markdown, PDFs, documents
  data      = optional structured tables / small datasets

2.2 Source and memory are different objects

Source:

  Full evidence-bearing material.

Examples:

  - article
  - transcript
  - PDF
  - long markdown summary
  - full chat log
  - table
  - document

Memory card:

  Atomic durable unit extracted from a source or direct statement.

Examples:

  - fact
  - person interaction
  - decision
  - preference
  - article takeaway
  - open question
  - research idea
  - family relationship

A single source can produce zero, one, or many memory cards.

Examples:

  Article
    → source record
    → article_note card
    → several key_takeaway cards
    → one or more open_question cards

  Conversation transcript
    → source record
    → person_interaction cards
    → commitments
    → preferences
    → open loops

  Basic fact
    → memory card only

2.3 Append-only by default

Do not delete normal conflicts.

Use links:

  new_memory --supersedes--> old_memory
  new_memory --contradicts--> old_memory
  new_memory --supports--> old_memory
  new_memory --duplicates--> old_memory
  memory     --derived_from--> source

Delete only for:

  - ingestion error
  - duplicate with no independent value
  - bad OCR / bad parse
  - accidentally ingested material
  - test junk
  - user explicitly requests deletion

2.4 Brain DB is source of truth

Brain should be able to rebuild Cognee from its own database.

Invariant:

  Loss of Cognee index must not imply loss of Brain memory.

Brain Postgres stores:

  - memory cards
  - sources
  - entities
  - aliases
  - explicit relationships
  - memory links
  - conflict state
  - reminders/open loops
  - Cognee sync status
  - ingestion logs
  - recall logs

Cognee stores:

  - semantic/vector projection of memory cards
  - graph projection of entities/relationships
  - full source projections
  - summaries/chunks/embeddings

================================================================================
3. HIGH-LEVEL ARCHITECTURE
================================================================================

  ┌──────────────────────────────────────────────────────────┐
  │                        Clients                           │
  │  Claude Desktop / ChatGPT / Slack / CLI / local scripts  │
  └──────────────────────────┬───────────────────────────────┘
                             │ MCP / HTTP
                             ▼
  ┌──────────────────────────────────────────────────────────┐
  │                    Brain MCP/API Server                  │
  │  stable tools: remember, recall, profile_entity, etc.    │
  └──────────────────────────┬───────────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────────┐
  │                   Ingestion Orchestrator                 │
  │  classify → parse → extract → entity-resolve → conflict  │
  └──────────────┬─────────────────────────────┬─────────────┘
                 │                             │
                 ▼                             ▼
  ┌─────────────────────────────┐   ┌────────────────────────┐
  │       Brain Postgres         │   │     File/Object Store   │
  │ source of truth              │   │ raw files, transcripts  │
  │ memories/entities/links      │   │ PDFs, markdown, tables  │
  └──────────────┬──────────────┘   └────────────────────────┘
                 │
                 │ projection jobs
                 ▼
  ┌──────────────────────────────────────────────────────────┐
  │                         Cognee                           │
  │  memory dataset  → memory cards                          │
  │  sources dataset → full source documents                 │
  │  data dataset    → small structured summaries            │
  │  graph + vector + summaries                              │
  └──────────────────────────┬───────────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────────┐
  │                      Recall Agent                        │
  │  query planning → DB lookup → Cognee recall → synthesis  │
  └──────────────────────────────────────────────────────────┘

================================================================================
4. DATASETS
================================================================================

Use only these Cognee datasets initially:

  memory
  sources
  data

4.1 memory

Contains compact distilled memory cards.

Examples:

  - basic facts
  - family facts
  - person interactions
  - preferences
  - ideas
  - decisions
  - open questions
  - article takeaways
  - chat conclusions
  - project-state summaries

4.2 sources

Contains full evidence-bearing source material.

Examples:

  - articles
  - conversation transcripts
  - long markdown summaries
  - PDFs
  - emails
  - raw notes
  - source documents
  - full chat logs, when explicitly useful

4.3 data

Optional.

Use for:

  - small structured tables
  - CSV-like records
  - table summaries
  - table schemas

Do not use Cognee as the source of truth for large/exact tables.
For large/exact data, use Postgres/SQLite/CSV/parquet and project only summaries,
schemas, and key rows into Cognee.

================================================================================
5. NODE SETS / TAGS
================================================================================

Node sets should be auto-generated, not manually maintained.

Recommended automatic node sets:

  kind:basic_fact
  kind:family_fact
  kind:person_interaction
  kind:open_question
  kind:article_note
  kind:key_takeaway
  kind:decision
  kind:chat_conclusion
  kind:table_note

  status:current
  status:superseded
  status:conflicted
  status:archived

  time:2026-q2
  time:2026-w19

  topic:knowledge_graphs
  topic:ai_memory
  topic:jazz
  topic:restaurants

  source_type:article
  source_type:transcript
  source_type:chat_summary
  source_type:manual_note

Avoid per-entity node sets:

  person:sam
  person:sara
  place:brutto
  article:specific-title

People, places, firms, concepts, and articles should be entities/fields, not
node sets.

================================================================================
6. CORE DOMAIN OBJECTS
================================================================================

6.1 Source

A Source is a durable evidence object.

Examples:

  - article
  - transcript
  - markdown_summary
  - PDF
  - email
  - table
  - manual_note
  - chat_log

Example:

  {
    "id": "src_20260505_001",
    "kind": "article",
    "title": "Example article title",
    "uri": "https://...",
    "content_hash": "sha256:...",
    "raw_text": "...",
    "summary": "...",
    "metadata": {
      "author": "...",
      "published_at": "...",
      "captured_at": "2026-05-05T12:00:00Z"
    },
    "status": "processed"
  }

Sources go to:

  - Brain DB
  - file/object storage if large
  - Cognee sources dataset

6.2 MemoryCard

A MemoryCard is an atomic durable memory.

Universal shape:

  {
    "id": "mem_20260505_001",
    "kind": "person_interaction",
    "statement": "Sam from Goldman mentioned that he likes Bill Evans.",
    "summary": "Sam likes Bill Evans.",
    "entities": [
      {
        "name": "Sam",
        "type": "person",
        "alias": "Sam from Goldman",
        "role": "subject"
      },
      {
        "name": "Goldman",
        "type": "organization",
        "role": "affiliation_context"
      },
      {
        "name": "Bill Evans",
        "type": "person",
        "role": "topic"
      }
    ],
    "topics": ["jazz"],
    "observed_at": "2026-05-05",
    "created_at": "2026-05-05T12:00:00Z",
    "source": {
      "source_id": null,
      "source_type": "manual_note",
      "quote": "Sam from Goldman mentioned that he likes Bill Evans."
    },
    "confidence": "medium",
    "status": "current",
    "supersedes": [],
    "contradicts": [],
    "open_loops": [],
    "metadata": {}
  }

Memory cards go to:

  - Brain DB
  - Cognee memory dataset

6.3 Entity

An Entity is a canonical person, place, organization, concept, project, or artifact.

Examples:

  - Daniele
  - Nur
  - Sara
  - Sam from Goldman
  - Goldman
  - Brutto
  - Cognee
  - knowledge graphs

Example:

  {
    "id": "ent_001",
    "type": "person",
    "canonical_name": "Sam from Goldman",
    "aliases": ["Sam", "Sam at Goldman"],
    "disambiguation": {
      "organization": "Goldman",
      "surname": null
    },
    "confidence": "medium",
    "created_at": "2026-05-05T12:00:00Z"
  }

6.4 Relationship

Relationships are explicit graph-like facts stored in Brain.

Examples:

  Nur --daughter_of--> Daniele
  Sara --daughter_of--> Daniele
  Nur --twin_of--> Sara
  Sam --associated_with--> Goldman
  Sam --likes--> Bill Evans
  MemoryCard --derived_from--> Source
  MemoryCard --supersedes--> MemoryCard

Example:

  {
    "id": "rel_001",
    "subject_entity_id": "ent_nur",
    "predicate": "daughter_of",
    "object_entity_id": "ent_daniele",
    "evidence_memory_id": "mem_20260505_002",
    "confidence": "high",
    "status": "current"
  }

6.5 MemoryLink

Memory links connect memory cards to other memory cards.

Types:

  derived_from
  supersedes
  superseded_by
  contradicts
  supports
  duplicates
  elaborates
  summarizes
  mentions

Example:

  {
    "from_memory_id": "mem_20260811_004",
    "relation": "supersedes",
    "to_memory_id": "mem_20260505_001",
    "confidence": "high"
  }

================================================================================
7. POSTGRES SCHEMA
================================================================================

7.1 sources

  CREATE TABLE sources (
      id                  TEXT PRIMARY KEY,
      kind                TEXT NOT NULL,
      title               TEXT,
      uri                 TEXT,
      file_path           TEXT,
      raw_text            TEXT,
      summary             TEXT,
      content_hash        TEXT NOT NULL,
      metadata_json       JSONB NOT NULL DEFAULT '{}'::jsonb,
      status              TEXT NOT NULL DEFAULT 'pending',
      captured_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
      processed_at        TIMESTAMPTZ,
      created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
  );

  CREATE UNIQUE INDEX sources_content_hash_idx
  ON sources(content_hash);

Statuses:

  pending
  processing
  processed
  failed
  archived
  deleted

7.2 memory_cards

  CREATE TABLE memory_cards (
      id                  TEXT PRIMARY KEY,
      kind                TEXT NOT NULL,
      statement           TEXT NOT NULL,
      summary             TEXT,
      confidence          TEXT NOT NULL DEFAULT 'medium',
      status              TEXT NOT NULL DEFAULT 'current',
      observed_at         TIMESTAMPTZ,
      source_id           TEXT REFERENCES sources(id),
      source_quote        TEXT,
      metadata_json       JSONB NOT NULL DEFAULT '{}'::jsonb,
      content_hash        TEXT NOT NULL,
      created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
  );

  CREATE INDEX memory_cards_kind_idx
  ON memory_cards(kind);

  CREATE INDEX memory_cards_status_idx
  ON memory_cards(status);

  CREATE INDEX memory_cards_source_id_idx
  ON memory_cards(source_id);

  CREATE UNIQUE INDEX memory_cards_content_hash_idx
  ON memory_cards(content_hash);

Statuses:

  candidate
  current
  superseded
  conflicted
  archived
  rejected
  deleted

7.3 entities

  CREATE TABLE entities (
      id                  TEXT PRIMARY KEY,
      type                TEXT NOT NULL,
      canonical_name      TEXT NOT NULL,
      normalized_name     TEXT NOT NULL,
      confidence          TEXT NOT NULL DEFAULT 'medium',
      metadata_json       JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
  );

  CREATE INDEX entities_type_idx
  ON entities(type);

  CREATE INDEX entities_normalized_name_idx
  ON entities(normalized_name);

7.4 entity_aliases

  CREATE TABLE entity_aliases (
      id                  TEXT PRIMARY KEY,
      entity_id           TEXT NOT NULL REFERENCES entities(id),
      alias               TEXT NOT NULL,
      normalized_alias    TEXT NOT NULL,
      source_memory_id    TEXT REFERENCES memory_cards(id),
      confidence          TEXT NOT NULL DEFAULT 'medium',
      created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
  );

  CREATE INDEX entity_aliases_entity_id_idx
  ON entity_aliases(entity_id);

  CREATE INDEX entity_aliases_normalized_alias_idx
  ON entity_aliases(normalized_alias);

7.5 memory_entities

  CREATE TABLE memory_entities (
      memory_id           TEXT NOT NULL REFERENCES memory_cards(id),
      entity_id           TEXT NOT NULL REFERENCES entities(id),
      role                TEXT NOT NULL,
      confidence          TEXT NOT NULL DEFAULT 'medium',
      created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
      PRIMARY KEY (memory_id, entity_id, role)
  );

  CREATE INDEX memory_entities_entity_id_idx
  ON memory_entities(entity_id);

  CREATE INDEX memory_entities_memory_id_idx
  ON memory_entities(memory_id);

Roles:

  subject
  object
  mentioned
  topic
  location
  person
  organization
  source_author
  affiliation_context

7.6 relationships

  CREATE TABLE relationships (
      id                  TEXT PRIMARY KEY,
      subject_entity_id   TEXT NOT NULL REFERENCES entities(id),
      predicate           TEXT NOT NULL,
      object_entity_id    TEXT NOT NULL REFERENCES entities(id),
      evidence_memory_id  TEXT REFERENCES memory_cards(id),
      confidence          TEXT NOT NULL DEFAULT 'medium',
      status              TEXT NOT NULL DEFAULT 'current',
      metadata_json       JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
  );

  CREATE INDEX relationships_subject_idx
  ON relationships(subject_entity_id);

  CREATE INDEX relationships_object_idx
  ON relationships(object_entity_id);

  CREATE INDEX relationships_predicate_idx
  ON relationships(predicate);

7.7 memory_links

  CREATE TABLE memory_links (
      id                  TEXT PRIMARY KEY,
      from_memory_id      TEXT NOT NULL REFERENCES memory_cards(id),
      relation            TEXT NOT NULL,
      to_memory_id        TEXT NOT NULL REFERENCES memory_cards(id),
      confidence          TEXT NOT NULL DEFAULT 'medium',
      metadata_json       JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
  );

  CREATE INDEX memory_links_from_idx
  ON memory_links(from_memory_id);

  CREATE INDEX memory_links_to_idx
  ON memory_links(to_memory_id);

  CREATE INDEX memory_links_relation_idx
  ON memory_links(relation);

7.8 open_loops

  CREATE TABLE open_loops (
      id                  TEXT PRIMARY KEY,
      memory_id           TEXT NOT NULL REFERENCES memory_cards(id),
      status              TEXT NOT NULL DEFAULT 'open',
      priority            TEXT NOT NULL DEFAULT 'normal',
      next_review_at      TIMESTAMPTZ,
      last_reminded_at    TIMESTAMPTZ,
      reminder_policy     TEXT,
      metadata_json       JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
  );

  CREATE INDEX open_loops_status_idx
  ON open_loops(status);

  CREATE INDEX open_loops_next_review_idx
  ON open_loops(next_review_at);

Statuses:

  open
  parked
  in_progress
  closed
  archived

7.9 cognee_sync

  CREATE TABLE cognee_sync (
      id                  TEXT PRIMARY KEY,
      object_type         TEXT NOT NULL,
      object_id           TEXT NOT NULL,
      dataset             TEXT NOT NULL,
      projection_hash     TEXT NOT NULL,
      cognee_reference    TEXT,
      status              TEXT NOT NULL DEFAULT 'pending',
      last_synced_at      TIMESTAMPTZ,
      error_message       TEXT,
      created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
  );

  CREATE UNIQUE INDEX cognee_sync_object_dataset_idx
  ON cognee_sync(object_type, object_id, dataset);

Statuses:

  pending
  synced
  failed
  stale
  deleted

7.10 ingestion_runs

  CREATE TABLE ingestion_runs (
      id                  TEXT PRIMARY KEY,
      input_type          TEXT NOT NULL,
      input_hash          TEXT NOT NULL,
      raw_input_preview   TEXT,
      status              TEXT NOT NULL DEFAULT 'started',
      source_id           TEXT REFERENCES sources(id),
      metadata_json       JSONB NOT NULL DEFAULT '{}'::jsonb,
      error_message       TEXT,
      started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
      finished_at         TIMESTAMPTZ
  );

  CREATE INDEX ingestion_runs_status_idx
  ON ingestion_runs(status);

  CREATE INDEX ingestion_runs_input_hash_idx
  ON ingestion_runs(input_hash);

7.11 recall_logs

  CREATE TABLE recall_logs (
      id                   TEXT PRIMARY KEY,
      query                TEXT NOT NULL,
      mode                 TEXT NOT NULL,
      retrieved_memory_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
      retrieved_source_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
      answer_preview       TEXT,
      metadata_json        JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
  );

================================================================================
8. MEMORY CARD KINDS
================================================================================

Initial kinds:

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
  conversation_summary
  chat_conclusion
  experience
  place_note
  table_note
  source_summary
  project_state
  commitment

8.1 basic_fact / family_fact

Input:

  Nur and Sara are my twin daughters.

Output:

  {
    "kind": "family_fact",
    "statement": "Nur and Sara are Daniele's twin daughters.",
    "entities": [
      {"name": "Daniele", "type": "person", "role": "parent"},
      {"name": "Nur", "type": "person", "role": "child"},
      {"name": "Sara", "type": "person", "role": "child"}
    ],
    "relations": [
      {"subject": "Nur", "predicate": "daughter_of", "object": "Daniele"},
      {"subject": "Sara", "predicate": "daughter_of", "object": "Daniele"},
      {"subject": "Nur", "predicate": "twin_of", "object": "Sara"},
      {"subject": "Sara", "predicate": "twin_of", "object": "Nur"}
    ],
    "confidence": "high",
    "source": "direct_user_statement",
    "status": "current"
  }

Important:

  Create entities for Daniele, Nur, and Sara.
  Create relationship links.
  Do not create three duplicate memory cards.

8.2 person_interaction

Input:

  Sam from Goldman mentioned that he likes Bill Evans.

Output:

  {
    "kind": "person_interaction",
    "statement": "Sam from Goldman mentioned that he likes Bill Evans.",
    "entities": [
      {"name": "Sam", "type": "person", "alias": "Sam from Goldman", "role": "subject"},
      {"name": "Goldman", "type": "organization", "role": "affiliation_context"},
      {"name": "Bill Evans", "type": "person", "role": "topic"}
    ],
    "topics": ["jazz"],
    "confidence": "medium",
    "status": "current"
  }

Relationship candidates:

  Sam --associated_with--> Goldman
  Sam --likes--> Bill Evans

8.3 article_note

Article ingestion usually creates:

  1 source record
  1 article_note
  0-N key_takeaway cards
  0-N open_question cards
  0-N disagreement/idea cards

Example:

  {
    "kind": "article_note",
    "statement": "This article is relevant because it frames knowledge graphs as a useful substrate for AI memory.",
    "title": "Example Article",
    "source_id": "src_20260505_001",
    "why_i_saved_it": "Useful for Brain design.",
    "topics": ["knowledge_graphs", "ai_memory"],
    "confidence": "medium"
  }

One distilled takeaway is often too little.
Prefer several atomic durable takeaways when the article justifies them.

8.4 chat_conclusion

Short conclusion:

  {
    "kind": "chat_conclusion",
    "statement": "Brain should use a few datasets — memory, sources, and optional data — rather than manually filing by people, places, experiences, and ideas.",
    "topics": ["brain", "memory_architecture", "cognee"],
    "confidence": "high",
    "source": "chat_summary"
  }

Long markdown/article-like summary:

  store full markdown in sources
  extract multiple memory cards into memory

8.5 open_question / research_question

Input:

  I would like to learn more about knowledge graphs.

Output:

  {
    "kind": "open_question",
    "statement": "Daniele wants to learn more about knowledge graphs.",
    "topics": ["knowledge_graphs", "ai_memory"],
    "status": "current",
    "open_loop": {
      "status": "open",
      "reminder_policy": "opportunistic_or_weekly",
      "next_review_at": null
    }
  }

Supports:

  - weekly open-question digest
  - opportunistic surfacing when topic comes up

8.6 table_note

Small table strategy:

  1. store original markdown/CSV as source
  2. store structured JSON rows
  3. store semantic summary memory card

Example:

  {
    "kind": "table_note",
    "statement": "Small table of preferences mentioned by contacts.",
    "columns": ["person", "organization", "preference", "source_date"],
    "rows": [
      {
        "person": "Sam",
        "organization": "Goldman",
        "preference": "Likes Bill Evans",
        "source_date": "2026-05-05"
      }
    ],
    "confidence": "medium"
  }

For larger tables or exact queries:

  - store in Postgres/SQLite/CSV/parquet
  - project only summary/schema/key rows into Cognee

================================================================================
9. INGESTION FLOWS
================================================================================

9.1 Article

Input:

  remember article: <url>
  why: useful for thinking about AI memory and knowledge graphs

Flow:

  1. Fetch article.
  2. Store full article in sources.
  3. Summarize article.
  4. Extract article_note card.
  5. Extract durable takeaways.
  6. Extract open questions/follow-ups.
  7. Link all cards to source_id.
  8. Project source to Cognee sources dataset.
  9. Project cards to Cognee memory dataset.

Receipt:

  Stored source: src_...
  Created 5 memory cards:
    - article_note
    - key_takeaway
    - key_takeaway
    - open_question
    - disagreement
  No conflicts detected.

9.2 Conversation transcript

Input:

  pasted transcript or uploaded transcript file

Flow:

  1. Store full transcript as source.
  2. Extract participants.
  3. Extract person_interaction cards.
  4. Extract commitments/open loops.
  5. Extract durable facts/preferences.
  6. Link cards to transcript source.
  7. Project source and cards to Cognee.

Do not store the whole transcript as a single memory card.

9.3 Summary/conclusion of chat

Short conclusion:

  memory card only

Long markdown/article-like summary:

  source + extracted memory cards

Example:

  Source:
    "Brain architecture chat summary.md"

  Cards:
    decision — Cognee is a projection, not source of truth.
    decision — Use memory/sources/data datasets.
    open_question — whether to build Slack ingestion agent.
    design_principle — append-only memory with supersedes links.

9.4 Random thought

Input:

  I wonder what the relationship is between human intelligence and language.
  Need to research this.

Flow:

  1. Create research_question memory card.
  2. Create open_loop row.
  3. Extract topics.
  4. Optionally suggest next action.
  5. Use reminder policy.

Receipt:

  Stored open research question:
    "What is the relationship between human intelligence and language?"

  Topics:
    - cognitive science
    - language
    - intelligence

  Reminder:
    opportunistic + weekly digest

9.5 Interaction with a person

Input:

  Sam from Goldman mentioned that he likes Bill Evans.

Flow:

  1. Resolve "Sam from Goldman" against existing entities.
  2. Create/update Person entity.
  3. Create/update Organization entity.
  4. Create person_interaction card.
  5. Create relationship candidate:
       Sam --likes--> Bill Evans
  6. Store evidence.
  7. Project card to Cognee.

Later query:

  Tell me everything about Sam from Goldman.

Expected output:

  Sam from Goldman

  Identity:
    - Person.
    - Associated with Goldman.
    - Surname unknown.

  Known preferences:
    - Likes Bill Evans. Evidence: mem_...

  Interactions:
    - 2026-05-05: mentioned he likes Bill Evans.

  Open loops:
    - None known.

  Uncertainties:
    - Surname unknown.
    - "Goldman" may mean Goldman Sachs unless clarified.

9.6 Basic family fact

Input:

  Nur and Sara are my twin daughters.

Flow:

  1. Create/update Person entities:
       Daniele
       Nur
       Sara
  2. Create family_fact card.
  3. Create relationships:
       Nur daughter_of Daniele
       Sara daughter_of Daniele
       Nur twin_of Sara
       Sara twin_of Nur
  4. Mark high confidence because direct user statement.

Queries that should work:

  Tell me about Sara.
  Tell me about my daughters.
  Who are Nur and Sara?

9.7 Small table

Small table:

  source + table_note + JSON rows

Large/exact table:

  store externally or in Brain structured tables;
  project summary/schema to Cognee

================================================================================
10. CONFLICT SEMANTICS
================================================================================

10.1 Default rule

Do not delete.

Use:

  supersedes
  contradicts
  duplicates
  supports

10.2 Conflict classes

Duplicate:

  Old: Sam likes Bill Evans.
  New: Sam likes Bill Evans.

Action:

  Do not create a new card unless the source adds useful provenance.
  Link duplicate if retained.

Additive:

  Old: Sam likes Bill Evans.
  New: Sam likes Sonny Rollins.

Action:

  Keep both.
  No conflict.

Update / supersession:

  Old: Sam works at Goldman.
  New: Sam left Goldman and joined Point72.

Action:

  Create new card.
  Mark old card superseded.
  Create supersedes link.
  Update relationship status.

True contradiction:

  Old: Sam has two children.
  New: Sam has no children.

Action:

  Store new card.
  Mark both as conflicted or create contradiction link.
  Ask user only if high-impact or frequently queried.

Correction:

  Old: Sam likes Bill Evans.
  New: Actually, Sam likes early Coltrane, not Bill Evans.

Action:

  New card supersedes old.
  Old status = superseded.

10.3 Conflict detection pseudo-code

  def ingest_candidate_memory(candidate):
      entities = resolve_entities(candidate.entities)
      similar_cards = find_similar_memory_cards(candidate, entities)

      classifications = []

      for existing in similar_cards:
          relation = classify_relation(candidate, existing)
          classifications.append((existing, relation))

      if any(relation == "duplicate" for _, relation in classifications):
          maybe_store_as_supporting_evidence(candidate)
          return

      if any(relation == "supersedes" for _, relation in classifications):
          store(candidate, status="current")
          for existing, relation in classifications:
              if relation == "supersedes":
                  mark_superseded(existing)
                  link(candidate, "supersedes", existing)
          return

      if any(relation == "contradicts" for _, relation in classifications):
          store(candidate, status="conflicted")
          for existing, relation in classifications:
              if relation == "contradicts":
                  link(candidate, "contradicts", existing)
          maybe_request_review(candidate)
          return

      store(candidate, status="current")

10.4 User confirmation policy

Ask the user only when:

  - conflict affects a high-confidence current fact
  - entity identity is ambiguous and materially changes retrieval
  - new fact would overwrite/supersede important relationship state
  - destructive operation is requested

Do not ask for every ambiguity.
Store uncertainty when reasonable.

================================================================================
11. ENTITY RESOLUTION
================================================================================

11.1 Goal

Avoid duplicate entities while not over-merging.

Examples:

  Sam
  Sam from Goldman
  Sam G.
  Sam at Goldman Sachs

These may or may not be the same person.

11.2 Strategy

Layered resolution:

  1. Exact normalized name match
  2. Alias match
  3. Contextual match:
       organization
       location
       project
       source
  4. Semantic match
  5. LLM adjudication
  6. User confirmation only if needed

11.3 Entity confidence

high:

  strong exact/alias/contextual match

medium:

  likely same entity, but missing a disambiguating field

low:

  possible match, but risky

Policy:

  high    → merge/use existing
  medium  → attach alias candidate or use with uncertainty
  low     → create separate entity

11.4 Entity profile generation

profile_entity("Sam from Goldman") should:

  1. Resolve entity.
  2. Fetch deterministic Brain DB facts:
       memory_entities
       relationships
       memory_links
  3. Retrieve semantic context from Cognee.
  4. Merge and de-duplicate.
  5. Exclude superseded facts by default.
  6. Surface conflicts separately.
  7. Return evidence.

================================================================================
12. COGNEE INTEGRATION
================================================================================

12.1 Role

Cognee provides:

  - semantic recall
  - graph-based retrieval
  - source/context retrieval
  - relationship discovery
  - cross-source synthesis

Brain provides:

  - source of truth
  - memory lifecycle
  - entity resolution
  - conflict/supersession logic
  - reminder logic
  - deterministic recall policy

12.2 Projection format: MVP

Serialize each memory card into structured markdown or JSON and ingest that
into Cognee.

Example projection:

  memory_id: mem_20260505_001
  kind: person_interaction
  status: current
  confidence: medium
  observed_at: 2026-05-05

  entities:
    - Sam [person, alias: Sam from Goldman, role: subject]
    - Goldman [organization, role: affiliation_context]
    - Bill Evans [person, role: topic]

  topics:
    - jazz

  statement:
    Sam from Goldman mentioned that he likes Bill Evans.

  source:
    manual_note

Advantages:

  - easy to debug
  - resilient to Cognee API changes
  - works through generic text ingestion
  - embeds Brain IDs into retrievable text

12.3 Projection format: later structured DataPoints

Later, define Cognee DataPoints after Brain schema stabilizes.

Possible models:

  BrainEntity
  BrainMemoryCard
  BrainSource

Use structured DataPoints only after MVP works.

12.4 Cognee datasets

Projection routing:

  MemoryCard → memory
  Source     → sources
  TableNote  → data or memory, depending on exactness need

12.5 Node-set generation

Example logic:

  def node_sets_for_memory(card):
      return [
          f"kind:{card.kind}",
          f"status:{card.status}",
          f"time:{quarter(card.observed_at or card.created_at)}",
          *[f"topic:{slug(t)}" for t in card.topics[:5]],
      ]

Do not expose node-set decisions to the user.

12.6 Cognee sync policy

Brain DB object changes create sync jobs.

  memory card created     → sync to Cognee memory
  memory card updated     → mark Cognee projection stale
  memory card superseded  → sync new status projection
  source created          → sync to Cognee sources
  source deleted          → mark deleted; optional Cognee rebuild

12.7 Rebuild command

Implement:

  brain cognee rebuild --dataset memory
  brain cognee rebuild --dataset sources
  brain cognee rebuild --all

Rebuild flow:

  1. Optionally prune target Cognee dataset/index.
  2. Reproject all non-deleted Brain records.
  3. Re-run Cognee ingestion/cognification if required.
  4. Verify counts.
  5. Mark sync status.

================================================================================
13. SESSION MEMORY POSITION
================================================================================

Use session memory sparingly.

Session memory is useful for:

  - short-term chat handover
  - temporary continuity
  - scratch context before extraction

Do not blindly persist whole sessions.

Recommended policy:

  1. Capture session as scratch if needed.
  2. At end, run Brain memory compiler.
  3. Store only durable memory cards.
  4. Store full transcript as source only when explicitly requested or useful.

Permanent Brain memory should contain extracted durable objects, not chat exhaust.

================================================================================
14. MCP TOOL DESIGN
================================================================================

14.1 remember

General-purpose ingestion.

Input:

  {
    "input": "string",
    "input_type": "auto | note | fact | thought | article_url | transcript | chat_summary | table",
    "observed_at": "optional ISO timestamp",
    "source_policy": "auto | memory_only | source_only | source_and_memory",
    "dry_run": false,
    "context": {
      "client": "claude | slack | cli | chatgpt",
      "conversation_id": "optional",
      "user_note": "optional"
    }
  }

Output:

  {
    "ingestion_run_id": "ing_...",
    "source": {
      "created": true,
      "source_id": "src_..."
    },
    "memory_cards": [
      {
        "id": "mem_...",
        "kind": "person_interaction",
        "statement": "...",
        "status": "current"
      }
    ],
    "entities": [
      {
        "id": "ent_...",
        "canonical_name": "Sam from Goldman",
        "type": "person"
      }
    ],
    "conflicts": [],
    "cognee_sync_status": "pending"
  }

14.2 ingest_source

For explicit source ingestion.

Input:

  {
    "source": "url | file_path | raw_text",
    "source_kind": "article | transcript | markdown | pdf | table | other",
    "title": "optional",
    "why_saved": "optional",
    "extract_memories": true
  }

Use for:

  - articles
  - transcripts
  - markdown files
  - PDFs
  - tables
  - other full source material

14.3 recall

General query.

Input:

  {
    "query": "Tell me everything about Sam from Goldman",
    "mode": "auto | evidence | profile | open_loops | sources | memories",
    "include_sources": true,
    "include_superseded": false,
    "limit": 20
  }

Output:

  {
    "answer": "...",
    "facts": [],
    "inferences": [],
    "open_loops": [],
    "conflicts": [],
    "evidence": [
      {
        "memory_id": "mem_...",
        "source_id": "src_...",
        "quote": "..."
      }
    ]
  }

14.4 profile_entity

Input:

  {
    "name": "Sam from Goldman",
    "entity_type": "person",
    "include_superseded": false,
    "include_sources": true
  }

Output sections:

  Identity
  Known facts
  Preferences
  Interactions
  Relationships
  Open loops
  Conflicts / stale facts
  Evidence

14.5 list_open_loops

Input:

  {
    "topic": "optional",
    "due_before": "optional ISO timestamp",
    "status": "open",
    "limit": 20
  }

Output:

  {
    "open_loops": [
      {
        "memory_id": "mem_...",
        "statement": "Learn more about knowledge graphs.",
        "topics": ["knowledge_graphs"],
        "next_review_at": null
      }
    ]
  }

14.6 resolve_conflict

Input:

  {
    "conflict_memory_id": "mem_new",
    "target_memory_id": "mem_old",
    "action": "supersede | keep_both | mark_duplicate | archive_old | reject_new",
    "note": "optional"
  }

14.7 forget

Default soft delete.

Input:

  {
    "object_type": "memory | source | entity",
    "object_id": "mem_...",
    "hard": false,
    "reason": "optional"
  }

Rules:

  hard=false by default
  hard=true requires explicit confirmation at client layer

14.8 sync_cognee

Input:

  {
    "object_type": "memory | source | all",
    "object_id": "optional",
    "dataset": "memory | sources | data | all",
    "force": false
  }

================================================================================
15. SLACK INGESTION AGENT
================================================================================

15.1 Purpose

Build a dedicated Slack bot.

Reason:

  - low-friction capture
  - mobile-friendly
  - narrow specialised prompt
  - consistent memory schema
  - better than relying on arbitrary Claude chats

The Slack bot should be a capture/ingestion interface, not a general assistant.

15.2 Slack commands

  /brain remember <text>
  /brain article <url> [why]
  /brain transcript
  /brain recall <query>
  /brain profile <entity>
  /brain open
  /brain review
  /brain undo-last

Free-form messages to the bot can call remember(input_type=auto).

15.3 Slack receipt example

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

15.4 Conflict receipt example

  Stored new memory, but found a possible conflict.

  New:
    - Sam mainly likes early Coltrane, not Bill Evans.

  Existing:
    - Sam likes Bill Evans.

  Action:
    - Marked new memory as current.
    - Marked old memory as superseded.

================================================================================
16. RECALL MODES
================================================================================

16.1 Auto recall

Default.

User asks natural question.
Brain chooses profile/source/open-loop/memory strategy.

Example:

  What did I conclude about Cognee?

16.2 Profile recall

For people, places, projects, concepts.

Examples:

  Tell me everything about Sam from Goldman.
  Tell me about Sara.
  What do I know about knowledge graphs?

16.3 Evidence recall

For high-stakes or source-sensitive answers.

Example:

  What source-backed facts do I have about X?

Output separates:

  - source-backed facts
  - inferences
  - unknowns
  - conflicts
  - stale/superseded memories

16.4 Open-loop recall

Examples:

  What open ideas do I have?
  What did I want to research about knowledge graphs?

16.5 Opportunistic recall

When current topic matches open questions:

  Current topic:
    knowledge graphs

  Brain recalls:
    - You wanted to learn more about knowledge graphs.
    - You wondered how human intelligence relates to language.

Only surface if:

  - relevance is high
  - item is still open
  - not reminded recently
  - topic match is explicit enough

================================================================================
17. INGESTION AGENT PROMPT CONTRACT
================================================================================

System instruction skeleton:

  You are Brain's memory compiler.

  Your job is to convert user input into durable memory objects.

  Do not store everything.
  Extract only durable facts, decisions, preferences, open questions,
  person interactions, article takeaways, commitments, and useful source summaries.

  Classify the input as:
    - basic_fact
    - family_fact
    - person_interaction
    - article
    - transcript
    - chat_summary
    - open_question
    - research_question
    - idea
    - table
    - source_only
    - ignore

  For each durable memory, emit a MemoryCard JSON object.

  Rules:
    1. Preserve uncertainty.
    2. Do not invent missing surnames, dates, places, or organizations.
    3. Use direct_user_statement as high confidence only when the user states the fact directly.
    4. Create source records for long or external material.
    5. Create multiple atomic cards when one source contains multiple durable takeaways.
    6. Detect possible conflicts but do not delete.
    7. Represent updates with supersedes/contradicts links.
    8. Ask a clarification question only if ambiguity materially affects identity or overwrites a high-confidence fact.

Expected output:

  {
    "classification": "person_interaction",
    "source": null,
    "memory_cards": [],
    "entities": [],
    "relationships": [],
    "possible_conflicts": [],
    "questions_for_user": []
  }

================================================================================
18. RECALL AGENT PROMPT CONTRACT
================================================================================

System instruction skeleton:

  You are Brain's recall agent.

  Answer using Brain memory records and source evidence.

  Rules:
    1. Distinguish facts, inferences, open questions, and conflicts.
    2. Exclude superseded facts unless requested.
    3. If evidence is weak, say so.
    4. Do not collapse two entities unless Brain entity resolution says they are the same.
    5. Include memory/source IDs in internal evidence structures.
    6. For people, organize output as:
         - Identity
         - Known facts
         - Preferences
         - Interactions
         - Relationships
         - Open loops
         - Conflicts/uncertainties
    7. For concepts, organize output as:
         - What I know
         - Saved sources
         - My takeaways
         - Open questions
         - Related people/projects

================================================================================
19. IMPLEMENTATION STACK
================================================================================

Recommended stack:

  Language:
    Python

  API:
    FastAPI

  MCP:
    Python MCP server

  DB:
    Postgres

  Migrations:
    Alembic

  ORM:
    SQLAlchemy or SQLModel

  Jobs:
    Celery / RQ / Dramatiq / simple asyncio worker initially

  Scheduler:
    cron / APScheduler / worker beat

  Slack:
    Slack Bolt Python

  LLM extraction:
    provider-agnostic interface

  Cognee:
    Python SDK or HTTP/API integration

  File storage:
    local filesystem initially
    S3-compatible object store later

Do not build a UI initially.
MCP + Slack + CLI are enough.

================================================================================
20. PACKAGE / MODULE STRUCTURE
================================================================================

  brain/
    pyproject.toml
    README.md
    alembic.ini
    docker-compose.yml

    brain/
      __init__.py

      config.py

      api/
        main.py
        routes_memory.py
        routes_sources.py
        routes_recall.py
        routes_admin.py

      mcp/
        server.py
        tools.py
        schemas.py

      db/
        base.py
        session.py
        models.py
        migrations/

      domain/
        ids.py
        memory_card.py
        source.py
        entity.py
        relationship.py
        conflict.py
        open_loop.py

      ingestion/
        orchestrator.py
        classifier.py
        extractors.py
        article_loader.py
        transcript_parser.py
        table_parser.py
        memory_compiler.py

      resolution/
        entity_resolver.py
        duplicate_detector.py
        conflict_detector.py

      recall/
        planner.py
        retriever.py
        profile_builder.py
        evidence_builder.py
        synthesizer.py

      cognee/
        client.py
        projector.py
        serializers.py
        sync_worker.py
        rebuild.py
        datapoints.py

      slack/
        app.py
        commands.py
        formatter.py

      workers/
        jobs.py
        scheduler.py
        reminders.py

      evals/
        golden_queries.py
        fixtures/
        metrics.py

      tests/
        test_ingestion.py
        test_entity_resolution.py
        test_conflicts.py
        test_recall.py

================================================================================
21. IMPLEMENTATION PHASES
================================================================================

Phase 1 — Brain DB + basic MCP

Build:

  - DB schema
  - remember tool
  - get_memory tool
  - simple recall over Postgres full-text search
  - ingestion receipt

Do not depend heavily on Cognee yet.

Goal:

  Make memory cards real.

Phase 2 — Ingestion compiler

Build:

  - LLM classifier
  - memory-card extractor
  - source/memory split
  - entity extraction
  - basic entity resolution
  - duplicate detection

Support:

  - basic facts
  - person interactions
  - open questions
  - chat conclusions
  - pasted articles/text

Phase 3 — Cognee projection

Build:

  - memory dataset projection
  - sources dataset projection
  - sync status table
  - rebuild command
  - Cognee recall integration

Goal:

  Semantic/graph recall over Brain records.

Phase 4 — Profile recall

Build:

  - profile_entity
  - entity-centric recall
  - relationship rendering
  - conflict/stale-memory sections

Golden query:

  Tell me everything about Sam from Goldman.

Phase 5 — Slack ingestion agent

Build:

  - Slack bot
  - /brain remember
  - /brain recall
  - /brain open
  - receipts
  - undo-last

Goal:

  Low-friction daily capture.

Phase 6 — Open-loop reminders

Build:

  - scheduled digest
  - opportunistic recall
  - last_reminded_at suppression
  - topic matching

Phase 7 — Custom Cognee DataPoints

Build only after schema stabilizes:

  - BrainMemoryCard DataPoint
  - BrainEntity DataPoint
  - BrainSource DataPoint
  - explicit DataPoint relationships

Rationale:

  Start with robust serialized projections.
  Move to structured Cognee graph insertion once Brain’s schema is stable.

================================================================================
22. EVALUATION PLAN
================================================================================

22.1 Golden ingestion fixtures

Test inputs:

  1. "Nur and Sara are my twin daughters."
  2. "Sam from Goldman mentioned that he likes Bill Evans."
  3. "I want to learn more about knowledge graphs."
  4. Long markdown chat summary.
  5. Article text with multiple takeaways.
  6. Small preference table.
  7. Contradiction/update about Sam.

Expected outputs:

  - correct memory-card kinds
  - correct entities
  - correct relationships
  - correct source/memory split
  - correct conflict links
  - correct open-loop rows

22.2 Golden recall queries

  Tell me everything about Sam from Goldman.
  Who are my daughters?
  What open questions do I have about knowledge graphs?
  What did I conclude about Brain/Cognee?
  What articles have I saved about AI memory?
  What facts about Sam are uncertain or stale?

22.3 Metrics

Track:

  - ingestion precision
  - duplicate rate
  - entity merge error rate
  - conflict detection precision
  - recall precision@k
  - groundedness
  - unsupported claims in answers
  - latency
  - LLM cost per ingestion
  - Cognee sync failure rate

================================================================================
23. OPERATIONAL REQUIREMENTS
================================================================================

23.1 Backups

Back up:

  - Brain Postgres
  - file/object storage
  - configuration

Cognee indexes should be rebuildable.

Critical invariant:

  Loss of Cognee index must not imply loss of Brain memory.

23.2 Idempotency

Every ingestion should have:

  - input_hash
  - content_hash
  - projection_hash

This prevents repeated Slack/Claude calls from duplicating memory.

23.3 Observability

Log:

  - ingestion run ID
  - LLM prompt version
  - LLM model
  - extracted card count
  - source ID
  - entity resolution decisions
  - conflict decisions
  - Cognee sync status
  - recall retrieved IDs

23.4 Destructive actions

Default forget should be soft delete.

Hard delete requires:

  - explicit hard=true
  - reason
  - confirmation at client layer
  - audit log

================================================================================
24. MAIN RISKS AND MITIGATIONS
================================================================================

Risk 1 — Junk memory

Cause:

  storing every chat fragment

Mitigation:

  memory compiler filters durable memories only
  sources store raw material separately

Risk 2 — Duplicate entities

Cause:

  Sam, Sam from Goldman, Sam G.

Mitigation:

  entity aliases
  contextual resolution
  low-confidence separate entities
  merge tool later

Risk 3 — Silent conflict

Cause:

  new facts overwrite old facts mentally but not structurally

Mitigation:

  supersedes/contradicts links
  status field
  conflict detector

Risk 4 — Cognee drift/API changes

Cause:

  fast-moving Cognee API/MCP surface

Mitigation:

  Brain owns schema
  Cognee is projection
  adapter layer
  rebuild command
  serialized projection MVP

Risk 5 — Bad source provenance

Cause:

  memory card loses original article/transcript evidence

Mitigation:

  source_id
  source_quote
  source offsets later
  evidence-first recall mode

Risk 6 — Annoying reminders

Cause:

  opportunistic reminders fire too often

Mitigation:

  relevance threshold
  last_reminded_at
  per-topic cooldown
  weekly digest default

================================================================================
25. RECOMMENDED MVP
================================================================================

Smallest useful Brain:

  1. Postgres schema:
       sources
       memory_cards
       entities
       relationships
       memory_links
       open_loops

  2. MCP tools:
       remember
       recall
       profile_entity
       list_open_loops

  3. Ingestion:
       basic facts
       person interactions
       open questions
       chat conclusions
       pasted articles/text

  4. Cognee:
       memory projection first
       sources projection second

  5. Recall:
       DB-first profile recall
       Cognee semantic recall as enrichment

Do not start by implementing every Cognee feature.

The first hard problem is not graph search.
The first hard problem is creating clean memory cards.

================================================================================
26. KEY TECHNICAL DECISIONS
================================================================================

Decision 1 — Brain owns memory lifecycle

Status:

  accepted

Reason:

  Conflicts, supersession, reminders, and identity are application-level concerns.

Decision 2 — Cognee is rebuildable index/projection

Status:

  accepted

Reason:

  Protects against API drift, indexing bugs, backend changes, and destructive mistakes.

Decision 3 — Use few datasets

Status:

  accepted

Datasets:

  memory
  sources
  data

Reason:

  Manual semantic filing is high-maintenance and brittle.

Decision 4 — Use memory cards

Status:

  accepted

Reason:

  Atomic cards improve recall, conflict handling, provenance, and summarization.

Decision 5 — Use append-only conflict links

Status:

  accepted

Reason:

  Personal memory evolves. Deleting loses history.

Decision 6 — Build Slack ingestion agent

Status:

  recommended

Reason:

  Dedicated capture interface produces more consistent memory than generic chat.

================================================================================
27. OPEN QUESTIONS
================================================================================

1. Should Brain use Cognee SDK directly, Cognee MCP, or Cognee HTTP API?

   Recommendation:
     Use SDK or HTTP from Brain backend.
     MCP is for external clients, not for Brain-to-Cognee internals.

2. Should Brain use custom Cognee DataPoints immediately?

   Recommendation:
     No.
     Start with serialized projections.
     Migrate to custom DataPoints once schema stabilizes.

3. Should Brain maintain its own pgvector index?

   Recommendation:
     Optional.
     Use Postgres full-text/entity lookup first.
     Use Cognee for semantic search initially.

4. Should Slack be first-class from day one?

   Recommendation:
     Build after MCP ingestion works.

5. Should long chats be stored automatically?

   Recommendation:
     No.
     Store extracted cards.
     Store full chat as source only when explicitly requested or when the summary is long/important.

================================================================================
28. FIRST IMPLEMENTATION PR
================================================================================

Goal:

  Create the foundation for Brain as a memory-card control plane.

Scope:

  - Add Postgres schema/migrations.
  - Add domain models:
      Source
      MemoryCard
      Entity
      Relationship
      MemoryLink
      OpenLoop
  - Add MCP tools:
      remember
      recall
      profile_entity
      list_open_loops
  - Implement simple rule-based ingestion for:
      basic_fact
      family_fact
      person_interaction
      open_question
  - Implement deterministic DB-first recall.
  - Stub Cognee projector but do not require it to work fully yet.
  - Add golden tests.

Acceptance tests:

  1. Input:
       "Nur and Sara are my twin daughters."

     Expected:
       - family_fact memory card
       - entities: Daniele, Nur, Sara
       - relationships:
           Nur daughter_of Daniele
           Sara daughter_of Daniele
           Nur twin_of Sara
           Sara twin_of Nur

  2. Input:
       "Sam from Goldman mentioned that he likes Bill Evans."

     Expected:
       - person_interaction card
       - entities: Sam from Goldman, Goldman, Bill Evans
       - relationship candidate:
           Sam likes Bill Evans

  3. Input:
       "I want to learn more about knowledge graphs."

     Expected:
       - open_question memory card
       - open_loop row
       - topic: knowledge_graphs

  4. Query:
       "Tell me everything about Sam from Goldman."

     Expected:
       - profile-style answer
       - identity
       - known preferences
       - interactions
       - uncertainties
       - evidence memory IDs

  5. Query:
       "Who are my daughters?"

     Expected:
       - Nur and Sara
       - twin relationship
       - evidence memory ID

================================================================================
29. HANDOVER SUMMARY
================================================================================

Build Brain as a deterministic personal memory control plane.

Do not build a generic vector-store wrapper.

Core primitive:

  MemoryCard

Core distinction:

  Source ≠ Memory

Core invariant:

  Brain DB is source of truth.
  Cognee is rebuildable semantic projection.

Core user experience:

  remember this
  what do I know about X?

Initial datasets:

  memory
  sources
  data

Initial MCP tools:

  remember
  ingest_source
  recall
  profile_entity
  list_open_loops
  get_memory
  resolve_conflict
  forget

Initial memory kinds:

  basic_fact
  family_fact
  person_interaction
  person_fact
  decision
  idea
  open_question
  research_question
  article_note
  key_takeaway
  chat_conclusion
  conversation_summary
  table_note

Initial killer tests:

  - Nur and Sara are my twin daughters.
  - Sam from Goldman mentioned that he likes Bill Evans.
  - I want to learn more about knowledge graphs.
  - Tell me everything about Sam from Goldman.
  - What open ideas do I have about knowledge graphs?

If those work cleanly, Brain is on the right track.