# Palate → Brain Migration: Detailed Coding-Agent Implementation Spec

## 0. Status and purpose

This document is the implementation authority for merging `dbortolotti/palate` into `dbortolotti/brain` as Brain's first-class **Taste** domain module.

The coding agent should use this document to avoid re-asking already-decided architectural questions. If an implementation detail is not specified here, the coding agent may choose a reasonable approach only if it does not violate the decisions and invariants below.

## 1. Top-level decisions already made

### 1.1 Repository and service model

* Move Palate logic into the Brain repository.
* Delete standalone Palate server code during the merge.
* Do **not** keep a separate Palate service.
* Do **not** keep a separate Palate MCP server.
* Do **not** keep a separate Palate DB.
* Do **not** keep a separate Palate launch agent, Cloudflare route, or deployment path.
* Use the old Palate repository only as a reference if needed.

### 1.2 User-facing interface

* Slack remains unified under `/brain ...`.
* Do **not** add `/brain taste ...` subcommands initially.
* MCP should expose generic `brain.*` tools plus explicit `brain.taste.*` tools.
* Do **not** preserve old `palate_*` MCP tool names.
* Do **not** add `/taste/*` HTTP routes initially.
* Taste behavior should be invoked semantically through generic Brain tools when the content is clearly taste-related.

### 1.3 Storage transition

* Palate is new and has few records.
* No Palate data migration is required.
* No import bridge from the old Palate SQLite DB is required.
* Create new Brain-managed `taste_*` tables directly.
* Use Brain's DB and migration system.

### 1.4 Core architectural rule

Do **not** collapse Palate into generic Brain memory cards.

Brain memory cards are evidence/provenance/projection. The canonical structured taste state must live in dedicated Brain-managed `taste_*` tables.

Brain owns:

* identity;
* entity resolution;
* memory cards;
* source provenance;
* relationships;
* open loops;
* conflicts / supersession;
* visibility / privacy / lifecycle;
* backup;
* generic recall.

Taste owns:

* supported taste categories;
* category-specific enrichment;
* structured taste items;
* taste attributes;
* 95% attribute intervals;
* taste signals;
* taste decisions;
* option matching;
* ranking;
* recommendation explanations.

## 2. Product behavior target

A user should be able to write:

```text
/brain remember Sam recommended Château Musar 2016.
```

Brain should infer that this is a taste-related memory, then create or update:

* a Brain entity for `Sam`, if needed;
* a Brain entity for `Château Musar 2016`;
* a structured taste item for the wine;
* a `recommended_by` taste signal;
* a Brain memory card as evidence;
* a Brain relationship: `Sam -> recommended -> Château Musar 2016`;
* a confirmation response that explicitly says a taste record was created or updated and includes the enriched data summary.

A user should be able to ask:

```text
/brain recall What wines did Sam recommend?
```

Brain should retrieve linked Brain evidence and taste records, rather than relying on string search alone.

A user should be able to ask:

```text
Tell me about Noble Rot, but don't save it.
```

Brain should run read-only enrichment where appropriate and return `stored=false`, with no DB writes.

## 3. Supported categories

Initial categories only:

* `wine`
* `restaurant`
* `music`
* `cigar`
* `experience`
* `movie`
* `series`

Do not build a generic plugin framework.

Adding a category later must be a deliberate code change including:

* category semantics;
* allowed attributes;
* enrichment source policy;
* ranking policy;
* validation;
* tests/evals.

## 4. Target module layout

Recommended layout:

```text
src/memory_stack/
  taste/
    __init__.py
    schema.py
    store.py
    service.py
    routing.py
    validation.py
    categories.py
    attributes.py
    signals.py
    projection.py
    proposals.py
    option_matching.py
    ranking.py
    explanations.py
    mcp_tools.py
    enrichment/
      __init__.py
      planner.py
      normalizer.py
      sources.py
      omdb.py
      restaurants.py
      music.py
      wine.py
      cigar.py
      experience.py
      media.py
    evals/
      __init__.py
      cases.py
      runner.py
      scoring.py
```

Recommended tests:

```text
tests/taste/
  test_schema.py
  test_store.py
  test_routing.py
  test_enrichment.py
  test_projection.py
  test_proposals.py
  test_ranking.py
  test_option_matching.py
  test_mcp_tools.py
  test_slack_taste_confirmation.py
  test_source_ingestion_taste_mentions.py
```

The coding agent may adjust file names to fit existing Brain conventions, but the logical modules must remain represented.

## 5. Data model

Implement Brain-managed SQLAlchemy tables with migrations.

### 5.1 `taste_items`

Fields:

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
  created_at TIMESTAMP NOT NULL
  updated_at TIMESTAMP NOT NULL
```

Required semantics:

* Every taste item must have `brain_entity_id`.
* `type` must be one of the supported categories.
* `status` should include at least `current` and `deleted`.
* Soft-delete is default.
* Hard-delete only if explicitly requested and should require confirmation.

### 5.2 `taste_attributes`

Fields:

```text
taste_attributes
  taste_item_id TEXT NOT NULL REFERENCES taste_items(id)
  key TEXT NOT NULL
  value REAL NOT NULL CHECK 0 <= value <= 1
  lower_95 REAL NOT NULL CHECK 0 <= lower_95 <= 1
  upper_95 REAL NOT NULL CHECK 0 <= upper_95 <= 1
  created_at TIMESTAMP NOT NULL
  updated_at TIMESTAMP NOT NULL
  PRIMARY KEY (taste_item_id, key)
```

Required semantics:

* Attributes are strict per-category.
* Unknown keys must not enter `taste_attributes`.
* Unknown/exploratory fields go to `enrichment_metadata_json`, `notes`, or warnings.
* `lower_95 <= value <= upper_95` after normalization.
* Clamp invalid numeric values only if this is an explicit validator decision; otherwise reject and warn.

### 5.3 `taste_signals`

Fields:

```text
taste_signals
  id TEXT PRIMARY KEY
  taste_item_id TEXT NOT NULL REFERENCES taste_items(id)
  signal_type TEXT NOT NULL
  value_json JSON NOT NULL
  provenance_memory_id TEXT REFERENCES memory_cards(id)
  provenance_entity_id TEXT REFERENCES entities(id)
  source TEXT
  created_at TIMESTAMP NOT NULL
```

Initial allowed signal types:

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

* Preserve all rating signals.
* Current effective rating is the latest explicit user rating.
* Older ratings remain as history/evidence.

Negative signal semantics:

* `avoid`: hard negative filter unless the user explicitly asks to include avoided items.
* `disliked`, `not_my_style`, `bad_fit`: ranking penalty, not necessarily exclusion.
* `rejected_option`: decision-feedback penalty for similar future queries.

### 5.4 `taste_decisions`

Fields:

```text
taste_decisions
  id TEXT PRIMARY KEY
  query TEXT NOT NULL
  context_json JSON NOT NULL DEFAULT {}
  options_json JSON NOT NULL DEFAULT []
  ranked_json JSON NOT NULL DEFAULT []
  chosen_taste_item_id TEXT REFERENCES taste_items(id)
  created_at TIMESTAMP NOT NULL
```

Required semantics:

* Decision logs do not create Brain memory cards by default.
* If the user wants a decision remembered, generic Brain memory should handle that explicitly.
* Decision logs are for ranking feedback and eval/tuning.

### 5.5 `taste_proposals`

Fields:

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
  created_at TIMESTAMP NOT NULL
  expires_at TIMESTAMP NOT NULL
```

Allowed statuses:

```text
pending
confirmed
cancelled
expired
superseded
```

Required semantics:

* Proposals are persisted server-side.
* Confirm/cancel/correct operate by `proposal_id`.
* Initial expiry: 24 hours.
* Expired proposals cannot be confirmed.
* Expired proposals cannot be corrected.
* Expired proposals must be regenerated.
* Correction updates the existing proposal in place and preserves the same `proposal_id`.
* Keep minimal audit fields: `correction_count`, `last_correction_text`, `last_corrected_at`.

### 5.6 Backup behavior

Brain backups must include:

* taste items;
* taste attributes;
* taste signals;
* taste decisions;
* taste enrichment metadata;
* taste proposals in all statuses;
* linked Brain entities;
* linked memory cards;
* linked relationships;
* linked open loops.

Do not exclude pending/expired/cancelled proposals from backups.

## 6. Configuration

Use Brain config with taste-prefixed settings.

Recommended settings:

```text
BRAIN_TASTE_ENABLED=true
BRAIN_TASTE_AUTO_ENRICH_ENABLED=true
BRAIN_TASTE_AUTO_WRITE_THRESHOLD=0.95
BRAIN_TASTE_CONFIRMATION_THRESHOLD=0.70
BRAIN_TASTE_OPEN_LOOP_CLOSE_THRESHOLD=0.97
BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD=0.80
BRAIN_TASTE_PROPOSAL_EXPIRY_HOURS=24
BRAIN_TASTE_WEB_ENRICHMENT_ENABLED=true
BRAIN_TASTE_OMDB_API_KEY=
BRAIN_TASTE_GOOGLE_PLACES_API_KEY=
```

Do not preserve old Palate settings such as:

```text
PALATE_DB_PATH
PALATE_MODEL
PALATE_BACKUP_DIR
PALATE_AUTH_ENABLED
PALATE_PORT
PALATE_MCP_PATH
```

Even though `BRAIN_TASTE_ENABLED` exists, the decision is that once implemented and tests pass, taste routing is active by default. The main safety mechanism is conservative confidence thresholds and structured confirmation, not a staged feature-flag rollout.

## 7. MCP tool surface

### 7.1 Generic Brain tools remain primary

Generic Brain MCP tools should be the default user path:

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

Update descriptions for `brain.remember`, `brain.recall`, and `brain.ingest_source` to state that Brain may invoke Taste logic when the content clearly involves supported taste categories.

### 7.2 Explicit taste tools

Expose these explicit tools:

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

Do not expose:

```text
palate_query
palate_remember
palate_describe_item
palate_evaluate_options
```

### 7.3 Tool response contracts

`brain.taste.remember` and any generic `brain.remember` path that creates taste data must explicitly state:

* whether anything was stored;
* how many taste records were created;
* how many taste records were updated;
* the enriched data summary;
* Brain memory-card IDs;
* Brain entity IDs;
* relationship IDs if any;
* open-loop IDs if any;
* warnings;
* whether server LLM/enrichment was used.

Example structured response:

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

For ordinary user-facing summaries, show enriched highlights rather than dumping every field. Full record output is required when:

* explicit `brain.taste.*` tool contract requires it;
* user asks for exact record/details/debug;
* dry-run/confirmation payload is returned.

## 8. HTTP and Slack surface

### 8.1 HTTP

Do not add `/taste/*` routes initially.

Taste is reachable through:

* generic Brain HTTP routes such as `/memory/remember` and `/memory/recall`;
* MCP `brain.taste.*` tools.

### 8.2 Slack

Keep only:

```text
/brain ...
```

Do not add `/brain taste` initially.

Examples:

```text
/brain remember Sam recommended Château Musar 2016.
/brain remember I want to try Noble Rot.
/brain recall What wines did Sam recommend?
```

All should route semantically.

## 9. Semantic routing policy

### 9.1 Router output

Implement a taste router that returns:

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

### 9.2 Initial thresholds

Use conservative thresholds:

```text
confidence >= 0.95:
  auto-enrich and write, if write intent is explicit and validation passes

0.70 <= confidence < 0.95:
  create persisted proposal and ask confirmation

confidence < 0.70:
  treat as normal Brain memory unless explicitly taste-directed
```

### 9.3 High-confidence examples

Likely high confidence:

```text
Sam recommended Château Musar 2016.
I want to try Noble Rot Soho.
I watched The Bear and rate it 8/10.
I listened to Kind of Blue and loved it.
I smoked a Partagas Serie D No. 4 and disliked it.
```

### 9.4 Ambiguous examples

Usually require confirmation:

```text
Blue Note is important.
Sam likes Burgundy.
I want to try Noble.
Remember The Bear.
Sam recommended Musar.
```

Ambiguity causes:

* item may be a place/person/brand/media item;
* category is unclear;
* spelling may be wrong;
* enrichment cannot verify identity;
* multiple candidates match.

### 9.5 Routing and enrichment are separate

A high-confidence taste route does not automatically mean external enrichment is trusted.

Route classification answers:

```text
Is this taste-related?
```

Enrichment answers:

```text
Can we verify and normalize this item from allowed sources?
```

Both must pass validation before an enriched write occurs.

## 10. Fine-grained taste roles

Brain's generic roles should not be duplicated for Taste. Add taste-specific roles only where the problem is genuinely taste-specific.

### 10.1 New taste-specific roles

Add logical roles/contracts for:

```text
taste_domain_router
taste_entity_classifier
taste_enrichment_planner
taste_enrichment_normalizer
taste_attribute_extractor
taste_signal_extractor
taste_option_matcher
taste_ranker
taste_explanation_synthesizer
taste_memory_projector
```

### 10.2 Reuse Brain roles

Do not create taste-specific duplicates for:

```text
entity_mention_extractor
entity_final_resolver
conflict_candidate_detector
conflict_policy_decider
open_loop_detector
recall_relevance_filter
success_receipt_generator
zero_tolerance_validator
```

Brain owns these control-plane roles.

### 10.3 Role placement

Write path:

```text
brain.remember
  -> taste_domain_router
  -> taste_entity_classifier
  -> taste_enrichment_planner
  -> taste_enrichment_normalizer
  -> taste_attribute_extractor
  -> taste_signal_extractor
  -> Brain entity resolution
  -> taste_memory_projector
  -> Brain conflict/open-loop handling
  -> taste store write
```

Query path:

```text
brain.recall / brain.taste.query
  -> taste_domain_router
  -> taste_option_matcher if options supplied
  -> taste_ranker for recommendation-style queries
  -> Brain recall for memory-style queries
  -> taste_explanation_synthesizer where appropriate
```

## 11. Enrichment policy

### 11.1 Enrichment is first-class

Palate's enrichment layer is not optional glue. It is the layer that converts messy real-world items into structured taste objects.

Preserve and port enrichment behavior into Brain's `taste/enrichment/` modules.

### 11.2 Enrichment output

Recommended normalized output:

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

### 11.3 Normalized vs free-form metadata

Separate:

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

Do not mix raw web-search snippets into normalized fields.

### 11.4 Strict source allowlist

Use category-specific allowlists.

Initial policy:

```text
media:
  OMDb for IMDb / Rotten Tomatoes / runtime / country / language / seasons.
  Do not add other media providers unless explicitly implemented and tested.

restaurant:
  official website
  Michelin Guide
  Google/Places where available
  controlled web-search grounding for cuisine/menu/ambiance/setting only when source URLs are retained.

music:
  conservative initial enrichment.
  No uncontrolled source expansion without explicit category rules.

wine:
  conservative initial enrichment.
  Source allowlist required before structured external claims are trusted.

cigar:
  conservative initial enrichment.
  Source allowlist required before structured external claims are trusted.

experience:
  minimal enrichment unless explicitly designed.
```

### 11.5 Failed enrichment

If enrichment fails, do **not** silently write enriched data from the prompt alone.

Default behavior:

```text
If item identity is clear but enrichment failed:
  create a minimal proposal and ask confirmation.

If item identity may be misspelled:
  ask clarification or suggest possible matches.

If user explicitly says "store anyway":
  store minimal user-input-only taste record.
```

Minimal user-input-only record should include:

```json
{
  "enrichment_status": "failed",
  "normalized_fields_source": "user_input_only",
  "enrichment_warnings": ["No strict-source match found"]
}
```

### 11.6 Broader web search

If strict sources do not find the item:

* do not broaden search automatically;
* ask the user whether to search more broadly;
* if the user permits broader search, clearly label source quality;
* place broad-web data primarily in `enrichment_metadata_json`;
* promote to normalized fields only after category-specific validation.

Example response:

```text
I could not verify "Nobble Rot" using the allowed restaurant sources, so I have not stored enriched data. Did you mean "Noble Rot"? I can also search the broader web or save a minimal user-input-only record if you confirm.
```

### 11.7 Read-only enrichment

Support query-only enrichment.

Examples:

```text
Tell me about wine XYZ using Brain enrichment, but don't save it.
Describe Noble Rot, don't add it to memory.
Would I like restaurant X? Don't store anything.
```

`brain.taste.describe_item` must return:

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

No persistent DB writes are allowed in read-only enrichment:

* no taste item;
* no Brain entity;
* no memory card;
* no relationship;
* no open loop;
* no proposal unless the user asks to save or confirmation is needed for a write.

## 12. Taste writes

### 12.1 Required write sequence

For every user-originated taste write:

1. classify taste domain and category;
2. decide whether to enrich, propose, or store minimal;
3. enrich if allowed and useful;
4. validate category and attributes;
5. resolve/create Brain entity for the taste item;
6. create/update `taste_items`;
7. upsert strict attributes;
8. append taste signals;
9. create Brain memory card as evidence;
10. link memory card to taste entity;
11. create Brain relationships when relevant;
12. create/open/close open loops when relevant;
13. return a response confirming taste record creation/update and including enriched data.

### 12.2 Always create Brain memory cards for user-originated writes

Every user-originated taste write creates a Brain memory card as evidence.

Examples:

```text
Sam recommended Château Musar 2016.
Daniele wants to try Noble Rot.
Daniele rated The Bear 8.5/10.
Daniele disliked a Partagas Serie D No. 4.
```

### 12.3 Update policy

When a new taste write refers to an existing taste item:

* update the current taste record in place;
* append new signals where applicable;
* create a new Brain memory card as evidence;
* preserve previous evidence via existing memory cards and signals;
* do not create a second taste item unless the item identity is materially distinct.

### 12.4 Rating policy

If multiple ratings exist:

* preserve all ratings;
* latest explicit user rating wins as current effective rating;
* older ratings remain in history/evidence.

## 13. Brain projection rules

### 13.1 Entity projection

Every taste item must map to a Brain entity.

The entity should use a suitable type. The coding agent may choose exact entity type names if consistent with Brain's existing schema, but the entity must be resolvable and profile-able through Brain.

### 13.2 Relationship projection

Examples:

```text
Sam -> recommended -> Château Musar 2016
Daniele -> wants_to_try -> Noble Rot
Daniele -> rated -> The Bear
Daniele -> disliked -> Partagas Serie D No. 4
```

Relationships should be backed by evidence memory IDs when available.

### 13.3 Open loop projection

Automatically create open loops for:

```text
wine / restaurant / cigar / experience:
  wanted_to_try

movie / series:
  wanted_to_watch

music:
  wanted_to_listen
```

Open-loop text should be user-readable, for example:

```text
Try Noble Rot.
Watch The Bear.
Listen to Kind of Blue.
```

### 13.4 Open loop closure

When user later says they tried/watched/listened:

```text
confidence >= 0.97:
  auto-close matching taste open loop

0.80 <= confidence < 0.97:
  ask confirmation

confidence < 0.80:
  do not close
```

Return closed `open_loop_id` when auto-closed.

## 14. Large source ingestion

Taste items mentioned inside a large source document require special handling.

Do not enrich/store every taste mention automatically.

### 14.1 Policy

```text
Large source document
  -> normal Brain source ingestion
  -> detect taste mentions
  -> classify candidate taste mentions
  -> only promote/enrich/store if durable, salient, and actionable
```

### 14.2 Thresholds

Initial policy:

```text
<= 3 high-salience taste items:
  propose/enrich/store if confidence is high and write intent is clear

4-10 taste items:
  create structured proposal requiring confirmation

> 10 taste items:
  do not enrich automatically
  summarize candidates and ask user to select
```

### 14.3 Examples

| Source content                                          | Behavior                                       |
| ------------------------------------------------------- | ---------------------------------------------- |
| "Sam recommended Château Musar 2016"                    | Create taste item + memory card + relationship |
| "I want to try Noble Rot"                               | Create taste item + wanted-to-try open loop    |
| "The menu included Barolo, Burgundy, and Riesling"      | Usually source text only                       |
| "Here is a list of 40 restaurants from an article"      | Store source; ask which to enrich/store        |
| "My Paris wishlist: Septime, Clamato, Le Chateaubriand" | Create proposal; no mass write if many         |

### 14.4 Source-only preservation

Even when taste items are not promoted to structured records, the source should still be saved according to normal Brain source policy.

## 15. Recall and query behavior

### 15.1 Generic Brain recall includes relevant taste evidence

Generic Brain recall should include taste-linked memories when relevant.

Example:

```text
What do we know about Sam?
```

May include:

```text
Sam recommended Château Musar 2016.
Sam suggested trying Noble Rot.
```

Include taste-linked evidence only when:

* the taste item is linked to a relevant Brain entity;
* the evidence memory card is current and visible;
* the taste record adds useful context;
* the user did not ask to exclude taste.

### 15.2 Intent-sensitive behavior

Recommendation-style queries use taste ranking.

Memory-style queries use Brain recall.

Examples:

```text
What wine should I bring?
  -> taste ranking

Which of these restaurants should I choose?
  -> taste option evaluation

What wines did Sam recommend?
  -> Brain recall + taste-linked evidence

What do I know about Noble Rot?
  -> Brain entity profile / recall with taste record included
```

## 16. Option matching

Option-set tools must stay constrained to provided options.

If the user pastes options and asks for an evaluation:

* rank only provided options;
* match provided option names to stored taste items where possible;
* return unmatched options;
* return `needs_confirmation` for medium-confidence matches;
* do not substitute unrelated stored items.

Suggested confidence bands:

```text
>= 0.85:
  confident match

0.50 <= confidence < 0.85:
  needs confirmation

< 0.50:
  unmatched
```

## 17. Ranking and explanations

### 17.1 Ranking inputs

Taste ranking should use:

* structured attributes;
* 95% intervals;
* latest explicit rating;
* tried/watched/listened status;
* wanted status;
* negative signals;
* decision feedback;
* Brain graph context, e.g. recommender identity;
* hard `avoid` filters.

### 17.2 Ranking transparency

Default responses are concise.

If the user asks for details, elaborate, breakdown, scoring, confidence, attributes, trade-offs, ranking logic, or debug info, expose:

* numeric score components;
* ranking weights;
* penalties;
* filters;
* uncertainty interval effects;
* decision-feedback adjustments;
* evidence IDs.

### 17.3 Explanation default

Default style:

```text
Recommendation: Pick X.

Why: It matches your stored preference for ..., avoids ..., and has relevant evidence from ...
```

Avoid long scoring dumps by default.

## 18. Proposals and confirmation

### 18.1 When to create a proposal

Create a persisted proposal when:

* taste route confidence is medium;
* category is ambiguous;
* item identity is ambiguous;
* enrichment failed but user likely wants a taste write;
* strict-source lookup fails and spelling may be wrong;
* multiple taste items are detected in a source and require selection;
* a write would close an open loop below auto-close threshold.

### 18.2 Proposal contents

Proposal must include:

* `proposal_id`;
* original user text;
* proposed taste records;
* normalized enriched fields;
* enrichment metadata summary;
* proposed Brain memory cards;
* proposed Brain entities;
* proposed relationships;
* proposed open loops;
* warnings;
* ambiguity reasons;
* allowed actions: confirm, cancel, correct.

### 18.3 Slack confirmation

Slack confirmation should be a structured card where possible.

It must support free-text correction, e.g.:

```text
Yes, but this detail should be XXX.
Save it, but category is restaurant, not wine.
Correct the vintage to 2016.
```

### 18.4 MCP confirmation

MCP confirmation should use:

```text
brain.taste.confirm
brain.taste.cancel
brain.taste.correct_proposal
```

Start taste-specific. If implementation later proves identical to generic confirmation, it may be consolidated, but not initially.

### 18.5 Correction behavior

Correction updates the existing proposal in place.

Re-run proposal generation when correction changes:

* category;
* identity;
* spelling;
* attributes;
* enrichment;
* relationships;
* open-loop behavior.

## 19. Refresh enrichment

Expose:

```text
brain.taste.refresh_enrichment
```

Refresh is explicit only.

Do not refresh automatically on read/query.

### 19.1 Refresh response

Return:

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

### 19.2 Memory cards for refresh

Routine refresh updates only enrichment metadata.

Create a Brain memory card only for material changes.

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

## 20. LLM and validation

### 20.1 LLM-first taste semantics

Taste classification, attribute extraction, signal extraction, enrichment normalization, and explanation may be LLM-first.

### 20.2 Strict DB insertion

No free-form model output may write directly to Brain DB or taste tables.

Before insertion:

* category must be allowed;
* attributes must be allowed for that category;
* signal type must be allowed;
* values must validate;
* intervals must validate;
* entity identity must be resolved or created safely;
* conflicts/ambiguity must be handled through proposals.

### 20.3 Unknown fields

Unknown fields must go to:

* `enrichment_metadata_json`;
* notes;
* warnings.

They must not affect ranking until promoted into the strict schema by a code change.

## 21. Deletion, privacy, and lifecycle

### 21.1 Delete behavior

Default: soft delete.

```text
taste_items.status = deleted
```

Deleted taste records:

* excluded from default ranking/query;
* visible only in admin/debug or explicit include-deleted requests;
* preserve linked Brain evidence.

Hard delete:

* only on explicit request;
* should require confirmation;
* must handle dependent rows safely.

### 21.2 Privacy

Use Brain's existing privacy/status visibility model.

Do not add a separate taste privacy layer initially.

Taste visibility follows linked:

* memory cards;
* entities;
* sources;
* status visibility filters;
* admin/debug scope.

## 22. Tests and evals

Port and expand Palate evals immediately.

### 22.1 Unit tests

Required test areas:

* schema/migrations;
* strict category validation;
* strict attribute validation;
* taste item creation/update;
* Brain entity creation for every taste item;
* memory card projection for every user-originated write;
* relationship projection;
* open-loop creation;
* open-loop closure thresholds;
* rating latest-wins;
* negative signal effects;
* soft delete;
* hard-delete confirmation path if implemented;
* proposal persistence;
* proposal correction in place;
* proposal expiry;
* enrichment failure behavior;
* read-only enrichment no-write guarantee;
* source allowlist behavior;
* refresh materiality;
* backup inclusion.

### 22.2 Integration tests

Required integration tests:

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
completion statement -> closes open loop only above threshold
generic recall of person -> includes linked taste recommendations
```

### 22.3 Eval coverage

Required eval cases:

* taste-domain routing;
* taste entity classification;
* enrichment normalization;
* strict schema validation;
* option matching;
* ranking quality;
* negative-signal handling;
* decision feedback;
* Brain entity projection;
* Brain memory-card projection;
* relationship creation;
* open-loop creation;
* open-loop closure;
* generic Brain recall including taste-linked evidence;
* detailed ranking explainability;
* failed enrichment safety;
* large source ingestion selectivity.

## 23. Implementation phases

### Phase 1 — Move code and establish module skeleton

1. Move relevant Palate logic into `src/memory_stack/taste/`.
2. Do not preserve standalone `palate.server`.
3. Do not expose old `palate_*` tools.
4. Add module skeleton and tests directory.
5. Add Brain taste config settings.

Deliverable:

```text
Taste module exists inside Brain repo. No separate Palate service remains.
```

### Phase 2 — Schema and store

1. Add `taste_*` tables to Brain schema/migrations.
2. Implement `TasteStore`.
3. Implement strict category and attribute registries.
4. Add unit tests.

Deliverable:

```text
Brain DB can store structured taste records with validated attributes/signals.
```

### Phase 3 — Enrichment

1. Port OMDb/media enrichment.
2. Port restaurant enrichment.
3. Implement strict source allowlist.
4. Implement normalized/free-form metadata split.
5. Implement read-only `describe_item`.
6. Implement failed-enrichment confirmation behavior.

Deliverable:

```text
brain.taste.describe_item can enrich read-only with stored=false and no DB writes.
```

### Phase 4 — Projection

1. Create Brain entity for every taste item.
2. Create Brain memory cards for every user-originated taste write.
3. Create relationships.
4. Create wanted-to-try/watch/listen open loops.
5. Implement high-confidence open-loop closure.

Deliverable:

```text
Taste writes compound with Brain's entity graph.
```

### Phase 5 — Explicit MCP tools

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
Explicit taste MCP tools work and return structured confirmations.
```

### Phase 6 — Semantic routing in Brain tools

1. Add taste router.
2. Wire into `brain.remember`.
3. Wire into `brain.recall`.
4. Wire into source ingestion selectivity.
5. Add thresholds and proposal behavior.

Deliverable:

```text
Users can use /brain and brain.* naturally without manually selecting Taste.
```

### Phase 7 — Ranking, option matching, decisions

1. Port ranking logic.
2. Port option matching.
3. Port decision feedback.
4. Add negative signal effects.
5. Add detailed scoring explainability.

Deliverable:

```text
Taste recommendations work with structured ranking and explainable scoring.
```

### Phase 8 — Slack confirmation UX

1. Add structured Slack confirmation.
2. Add free-text correction.
3. Wire proposal confirm/cancel/correct.
4. Enforce expiry.

Deliverable:

```text
Ambiguous Slack taste writes are safe, inspectable, and correctable.
```

### Phase 9 — Tests/evals/docs/backup cleanup

1. Add full tests/evals.
2. Verify backup includes taste tables.
3. Remove standalone Palate deployment artifacts.
4. Update README/API docs/user docs.
5. Confirm strict acceptance criteria.

Deliverable:

```text
Merge is complete.
```

## 24. Acceptance criteria

The merge is complete only when all are true:

* `brain.remember` routes high-confidence taste writes.
* `brain.taste.*` tools work.
* Taste records use Brain DB.
* Every taste record has a Brain entity.
* Every user-originated taste write creates a Brain memory card.
* Taste writes create relationships when applicable.
* Wanted-to-try/watch/listen creates Brain open loops.
* Tried/watched/listened completion closes matching open loops only above high threshold.
* Generic Brain recall includes relevant taste-linked memories.
* Taste ranking works.
* Option matching is constrained to supplied options.
* Read-only enrichment performs no persistent writes.
* Failed strict enrichment asks confirmation before minimal storage.
* Strict-source misses ask whether to broaden search.
* Large source ingestion avoids mass enrichment.
* Enrichment separates normalized fields from source-qualified/free-form metadata.
* Slack confirmation supports free-text correction.
* MCP confirmation supports `proposal_id` confirm/cancel/correct.
* Brain backups include taste tables and proposals.
* Tests/evals cover routing, enrichment, storage, projection, ranking, recall, and safety cases.
* Standalone Palate server code is removed.
* No separate Palate DB/service/MCP server remains.

## 25. Coding-agent instruction block

Use this as the direct instruction to the coding agent:

```text
Implement Brain Taste integration by moving Palate into Brain as an internal taste domain module.

Do not preserve the old Palate DB, service, MCP server, HTTP route namespace, or tool names. Do not add /taste/* HTTP routes initially. Expose explicit brain.taste.* MCP tools and route high-confidence taste-related brain.remember / brain.recall calls semantically.

Brain remains the source of truth for entities, memory cards, sources, relationships, open loops, conflict lifecycle, backup, privacy/status visibility, and generic recall. Taste owns structured taste records, enrichment, attributes, signals, decisions, option matching, ranking, and recommendation explanations.

Every taste record must have a Brain entity. Every user-originated taste write must create a Brain memory card as evidence. Wanted-to-try/watch/listen must create Brain open loops. Completion closes matching open loops only at very high confidence.

Preserve Palate enrichment as a first-class layer. Separate normalized metadata from free-form/source-qualified enrichment metadata. Use strict source allowlists. If strict enrichment fails, do not silently write enriched data from the prompt alone; ask confirmation or store a minimal user-input-only record only when explicitly requested.

Support read-only enrichment through brain.taste.describe_item with stored=false and no persistent DB writes.

Use LLM-first taste semantics but strict DB insertion schemas. Only allowed categories and per-category attributes may enter structured tables. Unknowns go to enrichment metadata/notes/warnings.

Port and expand Palate evals immediately. The merge is not complete until strict acceptance criteria pass.
```

## 26. Questions the coding agent should not ask again

The following are already decided:

* No old Palate DB migration is needed.
* No old `palate_*` MCP aliases are needed.
* Explicit `brain.taste.*` MCP tools are required.
* Taste-write responses must confirm created/updated taste records and include enriched data.
* Auto-enrich high-confidence taste writes only with a very high threshold.
* Ask confirmation for medium-confidence or ambiguous writes.
* Every taste record gets a Brain entity.
* Every user-originated taste write gets a Brain memory card.
* Wanted-to-try/watch/listen creates an open loop.
* Completion can auto-close an open loop only at very high confidence.
* Decision logs do not become Brain memory cards by default.
* Generic Brain recall includes relevant taste-linked evidence.
* Taste-specific query behavior is intent-sensitive: ranking for recommendations, recall for memory-style queries.
* Read-only enrichment is allowed and must not store unless asked.
* Strict-source failures should ask before broader web search.
* Enrichment source metadata should be preserved separately from normalized fields.
* Taste records update in place with evidence history.
* Latest explicit rating wins.
* Explicit negative signals are required.
* Strict per-category attribute schemas are required.
* New categories require deliberate code changes.
* Slack uses only `/brain ...`.
* No `/taste/*` HTTP routes initially.
* Use Brain config with taste-prefixed settings.
* Remove separate Palate service.
* Delete standalone Palate server code.
* Include all taste data and proposals in Brain backups.
* Soft-delete taste records by default.
* Use Brain's existing privacy/sensitivity model.
* Strict acceptance criteria are required.
* Active by default after implementation/tests; no staged feature flag requirement.

## 27. Implementation details the coding agent may decide

The coding agent may decide these, provided all constraints above are respected:

* exact SQLAlchemy class/table naming;
* exact migration file names;
* exact ID prefixes;
* exact Slack card UI representation;
* exact prompt format for LLM-first taste extraction;
* exact scoring formula and weights, provided detailed mode exposes them and tests cover them;
* exact backup verification mechanics;
* exact doc organization.

The coding agent must not change any architectural decision in this document without explicit approval.
