# Palate Migration Plan

## Executive summary

Merge `palate` into `brain` as an internal **Taste domain module**. Brain remains the unified memory/control plane. Taste preserves Palate's specialized enrichment, structured taste storage, ranking, option matching, and decision-feedback logic.

The user-facing interface remains unified:

```text
Slack:
  /brain ...

MCP:
  brain.*
  brain.taste.*
```

No separate Palate service, DB, HTTP endpoint namespace, or MCP server should remain after the merge.

Critical constraint:

> Do not collapse Palate into generic Brain memory cards. Brain memory cards are evidence/provenance/projection. Structured taste state must live in dedicated Brain-managed `taste_*` tables.

Brain remains the source of truth for memory identity, lifecycle, entity resolution, conflicts, open loops, and source provenance. Taste becomes a first-class domain module for taste-specific enrichment, structured attributes, signals, ranking, and decisions.

---

## 1. Goals

### 1.1 Product goals

Implement one Brain system where:

```text
/brain remember Sam recommended Château Musar 2016.
```

automatically creates:

- a Brain entity for `Sam`, if needed;
- a Brain entity for `Château Musar 2016`;
- a structured taste record;
- a taste recommendation signal;
- a Brain memory card as evidence;
- a Brain relationship: `Sam -> recommended -> Château Musar 2016`;
- optionally a wanted-to-try open loop if implied.

And:

```text
/brain recall What wines did Sam recommend?
```

retrieves the relevant taste-linked Brain evidence and taste data.

### 1.2 Technical goals

- Move Palate logic into the Brain repository.
- Delete standalone Palate server/service code.
- Create Brain-managed `taste_*` tables via Brain migrations.
- Expose explicit `brain.taste.*` MCP tools.
- Add semantic taste routing inside generic `brain.remember` and `brain.recall`.
- Preserve Palate enrichment, ranking, option matching, and decision feedback.
- Add strict tests/evals before considering the merge complete.

---

## 2. Non-goals

Do **not** do the following:

- Do not keep a separate Palate MCP server.
- Do not keep a separate Palate DB.
- Do not preserve old `palate_*` MCP tool names.
- Do not add `/taste/*` HTTP endpoints initially.
- Do not implement a generic plugin framework for arbitrary future taste categories.
- Do not mass-enrich every taste mention inside large source documents.
- Do not auto-broaden web enrichment beyond strict source allowlists.
- Do not write enriched records when enrichment fails unless the user confirms minimal storage.
- Do not store every taste decision as a Brain memory card.

---

## 3. Final architecture

### 3.1 Module layout

Target layout inside Brain:

```text
src/memory_stack/
  taste/
    __init__.py
    schema.py
    store.py
    service.py
    routing.py
    enrichment/
      __init__.py
      planner.py
      normalizer.py
      omdb.py
      restaurants.py
      music.py
      wine.py
      cigar.py
      experience.py
      sources.py
    ranking.py
    option_matching.py
    projection.py
    proposals.py
    mcp_tools.py
    evals/
      __init__.py
      cases.py
      runner.py
      scoring.py
```

Prefer integrating tests under the existing Brain test directory:

```text
tests/taste/
```

or equivalent existing convention.

### 3.2 Ownership boundaries

| Concern | Owner |
|---|---|
| Durable memory lifecycle | Brain |
| Entity identity / aliases | Brain |
| Sources / provenance | Brain |
| Relationships | Brain |
| Open loops | Brain |
| Conflicts / supersession | Brain |
| Taste category classification | Taste |
| Taste enrichment | Taste |
| Taste structured attributes | Taste |
| Taste rating/signals | Taste |
| Taste option matching | Taste |
| Taste ranking | Taste |
| Taste decision log | Taste |
| Generic recall synthesis | Brain |
| Taste recommendation explanation | Taste, using Brain evidence |

---

## 4. Data model

Implement Brain-managed SQLAlchemy tables with migrations.

### 4.1 `taste_items`

```text
taste_items
  id TEXT PRIMARY KEY
  brain_entity_id TEXT NOT NULL REFERENCES entities(id)
  type TEXT NOT NULL
  canonical_name TEXT NOT NULL
  normalized_name TEXT NOT NULL
  source_text TEXT
  notes TEXT
  metadata_json JSON NOT NULL DEFAULT {}
  enrichment_metadata_json JSON NOT NULL DEFAULT {}
  enrichment_status TEXT NOT NULL DEFAULT 'not_attempted'
  status TEXT NOT NULL DEFAULT 'current'
  created_at TIMESTAMP
  updated_at TIMESTAMP
```

Supported `type` values only:

```text
wine
restaurant
music
cigar
experience
movie
series
```

Every taste item **must** have a `brain_entity_id`.

### 4.2 `taste_attributes`

```text
taste_attributes
  taste_item_id TEXT NOT NULL REFERENCES taste_items(id)
  key TEXT NOT NULL
  value REAL NOT NULL CHECK 0 <= value <= 1
  lower_95 REAL NOT NULL CHECK 0 <= lower_95 <= 1
  upper_95 REAL NOT NULL CHECK 0 <= upper_95 <= 1
  created_at TIMESTAMP
  updated_at TIMESTAMP
  PRIMARY KEY (taste_item_id, key)
```

Attributes are strict per-category. Unknown attributes go to:

```text
taste_items.enrichment_metadata_json
taste_items.notes
warnings
```

not `taste_attributes`.

### 4.3 `taste_signals`

```text
taste_signals
  id TEXT PRIMARY KEY
  taste_item_id TEXT NOT NULL REFERENCES taste_items(id)
  signal_type TEXT NOT NULL
  value_json JSON NOT NULL
  provenance_memory_id TEXT REFERENCES memory_cards(id)
  provenance_entity_id TEXT REFERENCES entities(id)
  source TEXT
  created_at TIMESTAMP
```

Supported initial signal types:

```text
rating
tried
watched
listened
wanted_to_try
wanted_to_watch
wanted_to_listen
recommended_by
disliked
avoid
not_my_style
bad_fit
rejected_option
```

Rating semantics:

```text
Current effective rating = latest explicit user rating.
Older ratings remain as evidence/signals.
```

Negative signal semantics:

```text
avoid:
  hard negative filter unless user explicitly asks to include avoided items

disliked / not_my_style / bad_fit:
  ranking penalty

rejected_option:
  decision-feedback penalty for similar future queries
```

### 4.4 `taste_decisions`

```text
taste_decisions
  id TEXT PRIMARY KEY
  query TEXT NOT NULL
  context_json JSON NOT NULL DEFAULT {}
  options_json JSON NOT NULL DEFAULT []
  ranked_json JSON NOT NULL DEFAULT []
  chosen_taste_item_id TEXT REFERENCES taste_items(id)
  created_at TIMESTAMP
```

Decision logs do **not** create Brain memory cards by default.

Only create memory cards when:

- user explicitly says to remember/save the decision; or
- the input contains a durable taste preference.

### 4.5 `taste_proposals`

Persist server-side confirmation proposals.

```text
taste_proposals
  id TEXT PRIMARY KEY
  original_text TEXT NOT NULL
  proposal_json JSON NOT NULL
  warnings_json JSON NOT NULL DEFAULT []
  source_metadata_json JSON NOT NULL DEFAULT {}
  status TEXT NOT NULL
  correction_count INTEGER NOT NULL DEFAULT 0
  last_correction_text TEXT
  last_corrected_at TIMESTAMP
  created_at TIMESTAMP
  expires_at TIMESTAMP
```

Statuses:

```text
pending
confirmed
cancelled
expired
superseded
```

Initial expiry:

```text
24 hours
```

Expired proposals cannot be confirmed or corrected. They must be regenerated.

### 4.6 Backup inclusion

Brain backups must include:

- taste items;
- taste attributes;
- taste signals;
- taste decisions;
- taste enrichment metadata;
- taste proposals in all statuses;
- linked Brain entities;
- linked memory cards;
- linked relationships;
- linked open loops.

---

## 5. Configuration

Use Brain config with taste-prefixed settings.

Add settings similar to:

```text
BRAIN_TASTE_ENABLED=true
BRAIN_TASTE_AUTO_ENRICH_ENABLED=true
BRAIN_TASTE_OMDB_API_KEY=
BRAIN_TASTE_WEB_ENRICHMENT_ENABLED=true
BRAIN_TASTE_GOOGLE_PLACES_API_KEY=
BRAIN_TASTE_AUTO_WRITE_THRESHOLD=0.95
BRAIN_TASTE_CONFIRMATION_THRESHOLD=0.70
BRAIN_TASTE_OPEN_LOOP_CLOSE_THRESHOLD=0.97
BRAIN_TASTE_PROPOSAL_EXPIRY_HOURS=24
```

Do not preserve Palate env vars like:

```text
PALATE_DB_PATH
PALATE_MODEL
PALATE_BACKUP_DIR
PALATE_AUTH_ENABLED
```

---

## 6. MCP and HTTP surface

### 6.1 Generic Brain MCP tools

Keep existing Brain MCP tools as primary user path:

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
brain.review_recent
brain.undo_last
```

Update tool descriptions so clients know generic `brain.remember` and `brain.recall` may invoke taste logic automatically.

### 6.2 Explicit taste MCP tools

Expose explicit tools:

```text
brain.taste.describe_item
brain.taste.remember
brain.taste.query
brain.taste.evaluate_options
brain.taste.log_decision
brain.taste.confirm
brain.taste.cancel
brain.taste.correct_proposal
brain.taste.refresh_enrichment
```

No `palate_*` aliases.

### 6.3 HTTP routes

Do not add `/taste/*` HTTP endpoints initially.

Taste functionality should be reachable through:

```text
MCP brain.taste.*
generic Brain HTTP routes such as /memory/remember and /memory/recall
```

---

## 7. Slack UX

Keep only:

```text
/brain ...
```

No `/brain taste` subcommand initially.

Semantic routing handles taste automatically.

### 7.1 High-confidence write

Example:

```text
/brain remember Sam recommended Château Musar 2016.
```

If confidence is high enough:

```text
>= 0.95
```

Brain should write directly, subject to validation.

Response must confirm taste record creation/update and include enriched highlights.

### 7.2 Medium-confidence write

For ambiguous or medium-confidence cases:

```text
0.70 <= confidence < 0.95
```

Slack should show a structured confirmation card with:

- detected taste category;
- proposed canonical item;
- enriched normalized fields;
- enrichment metadata summary;
- proposed Brain memory card;
- proposed Brain entity links;
- proposed relationships;
- proposed open loop, if any;
- warnings / ambiguity reasons;
- free-text correction option.

Free-text correction examples:

```text
Yes, but this detail should be XXX.
Save it, but category is restaurant, not wine.
Correct the vintage to 2016.
```

Correction updates the existing proposal in place and keeps `proposal_id` stable.

### 7.3 Low-confidence write

If confidence is below threshold:

```text
< 0.70
```

Treat as normal Brain memory unless the user explicitly asks for taste handling.

---

## 8. Semantic routing

### 8.1 Taste router

Add `taste_domain_router`.

Output:

```json
{
  "domain": "taste | general | ambiguous",
  "taste_intent": "remember | describe | query | evaluate_options | log_decision | refresh | none",
  "entity_type_hint": "wine | restaurant | music | movie | series | cigar | experience | null",
  "confidence": 0.0,
  "requires_enrichment": true,
  "requires_confirmation": false,
  "ambiguity_reasons": []
}
```

### 8.2 Routing thresholds

Initial policy:

```text
confidence >= 0.95:
  auto-enrich and write, if write intent is explicit

0.70 <= confidence < 0.95:
  create persisted proposal and ask confirmation

confidence < 0.70:
  normal Brain behavior unless explicitly taste-directed
```

### 8.3 Ambiguity examples

Ambiguous:

```text
Blue Note
The Bear
Burgundy
Noble / Nobble Rot
```

These should usually trigger confirmation unless surrounding context resolves them.

---

## 9. Enrichment

Palate's enrichment layer must be treated as first-class. It supports media metadata, restaurant metadata, cuisine, Michelin, Google, and web-search-style grounding. In the merged system, enrichment must remain separate from storage.

### 9.1 Enrichment architecture

Implement:

```text
TasteEnrichmentService.describe_item(...)
TasteEnrichmentService.plan(...)
TasteEnrichmentService.normalize(...)
TasteEnrichmentService.refresh(...)
```

Enrichment should return:

```json
{
  "canonical_name": "...",
  "entity_type": "restaurant",
  "normalized_metadata": {},
  "attributes": {},
  "attribute_intervals_95": {},
  "enrichment_metadata": {},
  "sources": [],
  "warnings": [],
  "confidence": 0.0,
  "enrichment_status": "success | partial | failed | skipped"
}
```

### 9.2 Normalized vs free-form metadata

Separate clean normalized metadata from freer source-qualified enrichment metadata.

```text
taste_items.metadata_json
  cleaned normalized domain metadata

taste_items.enrichment_metadata_json
  source-qualified/free-form enrichment payload
  checked_at timestamps
  source URLs
  consulted web sources
  raw/semi-structured notes
  diagnostics/warnings
```

### 9.3 Strict source allowlist

Use explicit source allowlists per category.

Initial policy:

```text
media:
  OMDb only for IMDb/Rotten Tomatoes/runtime/country/language/seasons unless another source is explicitly added.

restaurant:
  official site
  Michelin Guide
  Google/Places data where available
  controlled web-search grounding for cuisine/menu/ambiance/setting only when source URLs are retained.

music:
  conservative initial enrichment.
  no uncontrolled source expansion without category rules.

wine:
  conservative initial enrichment.
  source allowlist required before structured external claims are trusted.

cigar:
  conservative initial enrichment.
  source allowlist required before structured external claims are trusted.

experience:
  minimal enrichment unless explicitly designed.
```

### 9.4 Broader web search

If strict-source enrichment fails:

- do not broaden search automatically;
- ask whether to search more broadly;
- if user permits broader search, keep data lower-trust and mostly in `enrichment_metadata_json`;
- only promote to normalized fields if category validation passes.

### 9.5 Failed enrichment

If enrichment fails:

```text
Do not silently write an enriched record from prompt-only data.
```

Behavior:

```text
If item identity is clear but enrichment failed:
  create minimal proposal and ask confirmation.

If item identity may be misspelled:
  ask clarification or suggest possible matches.

If user explicitly says "store anyway":
  store minimal user-input-only taste record.
```

Record fields:

```json
{
  "enrichment_status": "failed",
  "enrichment_warnings": ["No strict-source match found"],
  "normalized_fields_source": "user_input_only"
}
```

### 9.6 Read-only enrichment

Support query-only enrichment.

Examples:

```text
Tell me about wine XYZ using Brain enrichment, but don't save it.
Describe Noble Rot, don't add it to memory.
Would I like restaurant X? Don't store anything.
```

Tool:

```text
brain.taste.describe_item
```

Response:

```json
{
  "stored": false,
  "source": "read_only_enrichment",
  "enriched": {},
  "suggested_remember_payload": {},
  "warnings": [],
  "server_llm_used": {}
}
```

No persistent DB writes:

- no taste item;
- no Brain entity;
- no memory card;
- no relationship;
- no open loop.

---

## 10. Taste writes

### 10.1 User-originated taste write

For every user-originated taste write:

1. classify taste domain and category;
2. enrich if high-confidence and appropriate;
3. resolve/create Brain entity for taste item;
4. create/update `taste_items`;
5. upsert strict attributes;
6. append taste signals;
7. create Brain memory card as evidence;
8. link memory card to taste entity;
9. create Brain relationships when relevant;
10. create/open/close open loops when relevant;
11. return confirmation including taste record count and enriched data.

### 10.2 Response shape

Successful taste write must explicitly confirm records created/updated.

Example:

```json
{
  "stored": true,
  "taste_records_created": 1,
  "taste_records_updated": 0,
  "taste_records": [
    {
      "id": "taste_...",
      "type": "wine",
      "canonical_name": "Château Musar 2016",
      "brain_entity_id": "ent_...",
      "evidence_memory_id": "mem_...",
      "attributes": {},
      "attribute_intervals_95": {},
      "metadata": {},
      "enrichment_metadata": {},
      "signals": []
    }
  ],
  "brain_projection": {
    "memory_ids": ["mem_..."],
    "relationship_ids": ["rel_..."],
    "open_loop_ids": []
  },
  "enrichment": {
    "status": "success",
    "sources": [],
    "warnings": []
  }
}
```

Normal user-facing responses should summarize the stored data and enriched highlights. Exact full records should be exposed when:

- explicit `brain.taste.*` tool contract requires it;
- user asks for exact record/details/debug;
- dry-run/confirmation payload is returned.

---

## 11. Brain projection

Implement `taste/projection.py`.

### 11.1 Taste item entity

Every taste record gets a Brain entity.

Example:

```text
taste_item.brain_entity_id -> entities.id
```

### 11.2 Memory card

Every user-originated taste write creates a Brain memory card.

Examples:

```text
Sam recommended Château Musar 2016.
Daniele wants to try Noble Rot.
Daniele rated The Bear 8.5/10.
```

### 11.3 Relationships

Examples:

```text
Sam -> recommended -> Château Musar 2016
Daniele -> wants_to_try -> Noble Rot
Daniele -> rated -> The Bear
```

Use Brain's existing relationship model.

### 11.4 Open loops

Automatically create open loops for wanted intents:

```text
wine / restaurant / cigar / experience:
  wanted_to_try

movie / series:
  wanted_to_watch

music:
  wanted_to_listen
```

Completion should auto-close matching open loops only at very high confidence:

```text
confidence >= 0.97:
  auto-close

0.80 <= confidence < 0.97:
  ask confirmation

confidence < 0.80:
  do not close
```

---

## 12. Source ingestion with taste mentions

For large source ingestion, do not fully enrich every taste mention.

Policy:

```text
Large source document
  -> normal Brain source ingestion
  -> detect taste mentions
  -> classify candidate taste mentions
  -> only promote/enrich/store durable, salient, actionable items
```

Initial thresholds:

```text
<= 3 high-salience taste items:
  propose/enrich/store if confidence is high

4-10 taste items:
  create structured proposal requiring confirmation

> 10 taste items:
  do not enrich automatically
  summarize candidates and ask user to select
```

Examples:

| Source content | Behavior |
|---|---|
| "Sam recommended Château Musar 2016" | Create taste item + memory card + relationship |
| "I want to try Noble Rot" | Create taste item + wanted-to-try open loop |
| "The menu included Barolo, Burgundy, Riesling" | Usually source text only |
| "Here is a list of 40 restaurants" | Store source, ask whether to select/enrich |
| "My Paris wishlist: Septime, Clamato..." | Proposal, not mass write if many |

---

## 13. Recall and query behavior

### 13.1 Generic Brain recall

Generic Brain recall should include relevant taste-linked memories when:

- taste item is linked to a relevant Brain entity;
- evidence memory card is current and visible;
- taste record adds useful context;
- user did not ask to exclude taste.

Example:

```text
What do we know about Sam?
```

May include:

```text
Sam recommended Château Musar 2016.
Sam suggested trying Noble Rot.
```

### 13.2 Taste-specific query

Intent-sensitive behavior:

```text
Recommendation / choice / ranking / comparison / option evaluation:
  use taste ranking.

What do I know / remember / who recommended / what was stored:
  use Brain recall, with linked taste evidence.
```

Examples:

```text
What wine should I bring?
  -> taste ranking

What wines did Sam recommend?
  -> Brain recall + taste-linked evidence

Which of these restaurants should I choose?
  -> taste option evaluation

What do I know about Noble Rot?
  -> Brain entity profile/recall with taste record included
```

---

## 14. Ranking and explanations

### 14.1 Ranking

Port Palate ranking logic into `taste/ranking.py`.

Ranking should use:

- structured attributes;
- 95% intervals;
- current effective rating;
- tried/watched/listened status;
- wanted-to-try status;
- negative signals;
- decision feedback;
- Brain graph context, such as recommender identity;
- hard filters such as `avoid`.

### 14.2 Explanation style

Default:

- concise grounded explanation;
- no full scoring dump.

When user asks for details, scoring, breakdown, why exactly, confidence, attributes, or ranking logic:

- expose numeric score components;
- weights;
- penalties;
- filters;
- uncertainty interval effects;
- decision-feedback adjustments;
- evidence IDs.

---

## 15. Confirmation/proposals

### 15.1 Proposal creation

For ambiguous taste writes, create persisted proposals with `proposal_id`.

Proposal contains:

- original text;
- proposed taste records;
- normalized enriched data;
- enrichment metadata;
- proposed Brain memory cards;
- proposed Brain entities;
- proposed relationships;
- proposed open loops;
- warnings/ambiguity;
- client/source metadata;
- expiry.

### 15.2 Proposal actions

Expose:

```text
brain.taste.confirm
brain.taste.cancel
brain.taste.correct_proposal
```

No generic confirmation endpoint initially.

### 15.3 Correction behavior

Free-text correction updates the existing proposal in place.

Keep:

```text
proposal_id stable
correction_count
last_correction_text
last_corrected_at
```

Re-run proposal generation when correction affects identity, category, attributes, enrichment, relationships, or open-loop behavior.

### 15.4 Expiry behavior

Expired proposals:

- cannot be confirmed;
- cannot be corrected;
- must be regenerated;
- may be marked cancelled/no-op if user cancels.

---

## 16. Refresh enrichment

Expose:

```text
brain.taste.refresh_enrichment
```

Refresh is explicit only. Do not refresh automatically on read/query.

Response:

```json
{
  "refreshed": true,
  "taste_record_id": "taste_...",
  "previous_enrichment_checked_at": "...",
  "new_enrichment_checked_at": "...",
  "changed_fields": [],
  "warnings": []
}
```

### 16.1 Memory cards for refresh

Routine refresh updates only enrichment metadata.

Create Brain memory card only for material changes.

Initial materiality rules:

```text
Michelin star count changes
Michelin status appears/disappears
Michelin Green Star changes
restaurant appears/disappears from official guide metadata
Google rating changes by >= 0.3
Google rating count changes by >= 500 or >= 25%
OMDb IMDb rating changes by >= 0.3
Rotten Tomatoes critic score changes by >= 10 percentage points
runtime/seasons/country/language/genre materially corrected
canonical identity changes
enrichment contradicts existing stored metadata
```

---

## 17. LLM and schema validation

Use LLM-first for taste semantics, with strict insertion schemas.

Allowed LLM-backed tasks:

- taste classification;
- attribute extraction;
- signal extraction;
- enrichment normalization;
- explanation.

Required validator behavior:

```text
No free-form model output writes directly to DB.
```

Before insertion:

- category must be allowed;
- attributes must be allowed for category;
- values must be valid;
- intervals must be normalized;
- unknown keys go to enrichment metadata/notes/warnings;
- conflicts/ambiguity trigger proposal/confirmation.

---

## 18. Deletion and privacy

### 18.1 Delete behavior

Default: soft-delete.

```text
taste_items.status = deleted
```

Deleted taste records are excluded from default ranking/query results.

Hard-delete only if explicitly requested, and should require confirmation.

### 18.2 Privacy

Use Brain's existing privacy/sensitivity/status model. Do not add a separate taste privacy layer initially.

Taste visibility follows:

- linked memory cards;
- linked entities;
- source provenance;
- generic recall visibility rules;
- admin/debug scope.

---

## 19. Tests and evals

Port and expand Palate evals immediately.

### 19.1 Unit tests

Add tests for:

- schema/migrations;
- taste item creation;
- Brain entity creation;
- memory card projection;
- relationship projection;
- open-loop creation;
- open-loop closure;
- attribute strictness;
- signal semantics;
- latest-rating-wins;
- negative-signal ranking effects;
- soft delete;
- proposal persistence;
- proposal correction;
- proposal expiry;
- refresh materiality;
- backup inclusion.

### 19.2 Integration tests

Add tests for:

```text
brain.remember -> taste route -> taste write -> Brain projection
brain.recall -> includes taste-linked evidence
brain.taste.describe_item -> no DB writes
brain.taste.remember -> writes taste + Brain projection
brain.taste.evaluate_options -> constrained option matching
Slack medium-confidence proposal -> free-text correction -> confirm
source ingestion with many taste mentions -> no mass enrichment
failed strict enrichment -> confirmation instead of prompt-only write
strict-source miss -> asks whether to broaden search
```

### 19.3 Eval coverage

Add eval cases for:

- taste-domain routing;
- entity classification;
- enrichment normalization;
- strict schema validation;
- option matching;
- ranking quality;
- negative-signal handling;
- decision feedback;
- Brain entity projection;
- Brain memory-card projection;
- relationship creation;
- open-loop creation/closure;
- generic Brain recall including taste evidence;
- detailed ranking explainability.

---

## 20. Acceptance criteria

The merge is complete only when all of these pass:

```text
brain.remember routes high-confidence taste writes.
brain.taste.* tools work.
taste records use Brain DB.
taste writes create Brain entities.
taste writes create Brain memory cards.
taste writes create Brain relationships when applicable.
wanted-to-try/watch/listen creates Brain open loops.
tried/watched/listened completion closes matching open loops at high confidence.
generic Brain recall includes taste-linked memories.
taste ranking works.
option matching is constrained to supplied options.
read-only enrichment performs no writes.
failed strict enrichment asks confirmation before minimal storage.
large source ingestion avoids mass enrichment.
enrichment separates normalized fields from source-qualified/free-form metadata.
Slack confirmation supports free-text correction.
MCP confirmation supports proposal_id confirm/cancel/correct.
Brain backups include taste tables and proposals.
All relevant tests/evals pass.
Standalone Palate server code is removed.
No separate Palate DB/service/MCP server remains.
```

---

## 21. Suggested implementation phases

### Phase 1 — Move code and create Brain-native taste module

1. Copy relevant Palate logic into `src/memory_stack/taste/`.
2. Do not copy standalone `palate.server` as runnable service.
3. Delete/deprecate standalone service code.
4. Keep enrichment/ranking/core logic as reusable modules.
5. Add initial Brain config settings.

Deliverable:

```text
Taste code exists inside Brain repo, no separate service.
```

### Phase 2 — Add schema and store

1. Add SQLAlchemy tables/migrations for `taste_*`.
2. Implement `TasteStore`.
3. Implement strict category/attribute schemas.
4. Add unit tests for DB behavior.

Deliverable:

```text
Brain DB can store structured taste records.
```

### Phase 3 — Port enrichment

1. Port OMDb/media enrichment.
2. Port restaurant enrichment.
3. Implement source allowlist.
4. Implement normalized vs enrichment metadata separation.
5. Implement read-only `describe_item`.
6. Add failed-enrichment confirmation behavior.

Deliverable:

```text
brain.taste.describe_item works with stored=false and no DB writes.
```

### Phase 4 — Brain projection

1. Implement taste item -> Brain entity creation.
2. Implement user-originated taste write -> Brain memory card.
3. Implement relationships.
4. Implement wanted-to-try/watch/listen open loops.
5. Implement high-confidence open-loop closure.

Deliverable:

```text
Taste writes compound with Brain entity graph.
```

### Phase 5 — MCP tools

Implement:

```text
brain.taste.describe_item
brain.taste.remember
brain.taste.query
brain.taste.evaluate_options
brain.taste.log_decision
brain.taste.confirm
brain.taste.cancel
brain.taste.correct_proposal
brain.taste.refresh_enrichment
```

Deliverable:

```text
Explicit taste tools work and return structured confirmations.
```

### Phase 6 — Semantic routing in generic Brain tools

1. Add `taste_domain_router`.
2. Wire into `brain.remember`.
3. Wire into `brain.recall`.
4. Add thresholds.
5. Add proposal flow for medium-confidence routing.
6. Add source-ingestion taste mention policy.

Deliverable:

```text
Users can use /brain and brain.* naturally without selecting Taste manually.
```

### Phase 7 — Ranking and decision feedback

1. Port ranking logic.
2. Port option matching.
3. Port decision feedback.
4. Implement negative signals.
5. Implement detailed scoring explainability.

Deliverable:

```text
Taste recommendation quality matches or exceeds current Palate behavior.
```

### Phase 8 — Slack confirmation

1. Add structured confirmation card.
2. Add free-text correction.
3. Implement proposal confirm/cancel/correct path.
4. Ensure proposal expiry handling.

Deliverable:

```text
Ambiguous Slack taste writes are safe and correctable.
```

### Phase 9 — Tests/evals/backup/deployment cleanup

1. Add full tests/evals.
2. Add taste tables to backup/export verification.
3. Remove Palate standalone deployment artifacts.
4. Update docs.
5. Update README and API setup docs.

Deliverable:

```text
Strict acceptance criteria pass.
```

---

## 22. Coding-agent instruction block

Use this as the direct instruction to the coding agent:

```text
Implement Brain Taste integration by moving Palate into Brain as an internal taste domain module.

Do not preserve the old Palate DB, service, MCP server, or tool names. Do not add /taste/* HTTP routes initially. Expose explicit brain.taste.* MCP tools and route high-confidence taste-related brain.remember / brain.recall calls semantically.

Brain remains the source of truth for entities, memory cards, sources, relationships, open loops, conflict lifecycle, backup, privacy/status visibility, and recall. Taste owns structured taste records, enrichment, attributes, signals, decisions, option matching, ranking, and recommendation explanations.

Every taste record must have a Brain entity. Every user-originated taste write must create a Brain memory card as evidence. Wanted-to-try/watch/listen must create Brain open loops. Completion closes matching open loops only at very high confidence.

Preserve Palate enrichment as a first-class layer. Separate normalized metadata from free-form/source-qualified enrichment metadata. Use strict source allowlists. If strict enrichment fails, do not silently write enriched data from the prompt alone; ask confirmation or store a minimal user-input-only record only when explicitly requested.

Support read-only enrichment through brain.taste.describe_item with stored=false and no persistent DB writes.

Use LLM-first taste semantics but strict DB insertion schemas. Only allowed categories and per-category attributes may enter structured tables. Unknowns go to enrichment metadata/notes/warnings.

Port and expand Palate evals immediately. The merge is not complete until strict acceptance criteria pass.
```

---

## 23. Open implementation details the coding agent may choose

The coding agent may choose under these constraints:

- exact SQLAlchemy naming conventions;
- exact migration file organization;
- exact schema JSON field names if semantically equivalent;
- exact scoring formula, provided it is testable and explainable;
- exact Slack UI mechanics for structured confirmation;
- exact model prompt layout for taste roles;
- exact backup verification implementation.

The agent must not change the architectural decisions above without explicit approval.
