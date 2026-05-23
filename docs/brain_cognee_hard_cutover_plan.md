# Brain/Cognee Hard Cutover Plan

## Summary

Refactor Brain to match the proposed diagrams: Brain becomes the policy/profile/bias/session facade; Cognee becomes required for durable semantic memory, source ingestion, graph/vector retrieval, session memory, and improvement.

Key decisions locked:
- **Migration strategy:** hard cutover from Brain DB semantic ownership to Cognee ownership.
- **Cognee dependency:** durable memory/source writes require Cognee and fail clearly if Cognee is unavailable.
- **Slack:** remove Slack from supported docs/default config; leave runtime code dormant for later deletion, unless it blocks the cutover.
- **Public surface:** keep current REST/MCP/app tool names where feasible, but change internals and response semantics to Cognee-first.
- **Legacy projection maintenance:** `brain_sync_cognee` and `brain_rebuild_cognee` are hard-deprecated; Brain no longer syncs or rebuilds Cognee from legacy Brain DB semantic rows or `cognee_sync` projection state.

## Phase 0: Freeze Architecture Contract

- Treat `docs/proposed_brain_cognee_flow.md` as the source of truth for implementation.
- Update current/legacy docs so they no longer claim Brain DB is the semantic source of truth.
- Define these ownership rules in one internal architecture note:
  - Brain owns auth, scopes, profile, bias, session mapping, confirmation policy, receipt policy, app write audit, and palate policy.
  - Cognee owns durable memory/source records, semantic graph, vector retrieval, source chunks/summaries, session memory contents, query logs, improve, and forget/delete of semantic memory.
  - Brain must not create new `memory_cards`, `sources`, `entities`, `relationships`, or broad `recall_logs` for durable semantic operations after cutover.

## Phase 1: Control Store Schema

Add a new Brain control-store migration and update `brain_schema.py`.

Keep:
- `brain_users`
- `app_write_audit`
- profile context storage, but move toward structured control records
- taste proposal/control records if still needed for confirmation workflow

Add:
- `brain_session_maps`
  - `id`, `user_id`, `profile_name`, `surface`, `client_session_id`, `cognee_session_id`, `cognee_dataset`, `node_sets_json`, `metadata_json`, `created_at`, `updated_at`, `last_used_at`
  - unique key on `user_id`, `profile_name`, `surface`, `client_session_id`
- `brain_external_receipts`
  - `id`, `user_id`, `surface`, `tool_name`, `action`, `status`, `summary`, `cognee_dataset`, `cognee_reference`, `cognee_result_json`, `warnings_json`, `metadata_json`, `created_at`
- `brain_pending_confirmations`
  - `id`, `user_id`, `surface`, `action`, `original_input`, `proposed_payload_json`, `reason`, `options_json`, `status`, `expires_at`, `confirmed_at`, `metadata_json`, `created_at`, `updated_at`
- `brain_context_records`
  - `id`, `user_id`, `kind` (`profile` or `bias`), `statement`, `scope`, `source`, `status`, `metadata_json`, `cognee_reference`, `created_at`, `updated_at`

Hard-cutover handling:
- Leave old semantic tables physically present for migration/export/debug only.
- Stop writing them in normal service paths.
- Mark old semantic-store APIs as legacy/internal and remove them from public/admin MCP where they imply semantic authority.

## Phase 2: Cognee DataPoint Contract

Create a new Cognee-facing module for typed datapoints and node-set scope.

Define typed datapoints:
- `BrainMemoryDataPoint`
  - stable external id, user id, profile name, kind, statement, summary, confidence, status, observed_at, source reference, metadata
- `BrainSourceDataPoint`
  - stable external id, user id, profile name, source kind, title, uri/file metadata, content hash, summary, metadata
- `BrainSourceChunkDataPoint`
  - stable external id, parent source id, chunk index, chunk text, content hash, metadata
- `BrainContextDataPoint`
  - profile/bias context id, kind, statement, scope, source, status
- `BrainStatusEventDataPoint`
  - receipt id, target external id, action, status, reason, timestamp
- Existing palate datapoints remain, but align naming and node sets with this module.

Node-set rules:
- Always include `brain`, `user:<normalized_user_id>`, `profile:<profile_name>`.
- Durable memory includes `brain_memory`, `memory_kind:<kind>`, `memory_status:<status>`.
- Sources include `brain_source`, `source_kind:<kind>`, `source:<source_id>`.
- Profile/bias includes `brain_context`, `context_kind:<profile|bias>`, `context_scope:<scope>`.
- Palate includes `brain_palate`, `taste:<type>`, plus status/type node sets.
- Do not pass raw Slack node sets because Slack is not a supported surface.

## Phase 3: Cognee Write Path

Refactor `brain_service.remember()` and `brain_service.ingest_source()`.

New durable write behavior:
- Validate Cognee is enabled/importable before durable write.
- Resolve Brain context: user, profile, bias, surface, session id, dataset, node sets.
- Apply existing durability/safety/taste routing policy.
- If dry-run or confirmation needed, write only `brain_pending_confirmations` and return a preview receipt.
- If approved, call Cognee directly with typed datapoints/source input.
- Store a `brain_external_receipts` record with Cognee result references.
- Return `IngestionReceipt` with:
  - `ingestion_run_id` set to receipt id
  - `memory_cards` populated only as compatibility receipt items, not Brain DB rows
  - `source.source_id` set to stable external source id when relevant
  - `cognee_sync_status` replaced or fixed to `synced`/`not_applicable`

Remove from normal durable write path:
- `BrainStore.create_ingestion_run`
- `BrainStore.upsert_source`
- `BrainStore.upsert_memory_card`
- entity/relationship/open-loop writes to Brain DB
- `cognee_sync` pending/stale projection rows
- background `sync_cognee` after ingestion

Source ingestion behavior:
- Source text goes to Cognee `remember/add/cognify` as source data.
- Brain stores only receipt/control metadata.
- `extract_memories=True` becomes a Cognee graph/source processing option, not Brain DB card extraction.
- Large source ingestion uses Cognee's storage/chunking; Brain must not store raw source text in its DB.

Cognee unavailable behavior:
- Durable write/source ingest returns a clear error through REST/MCP/app surfaces.
- No fallback semantic Brain DB write is allowed.
- Dry-run and pending-confirmation creation may still work without Cognee if no commit is attempted.

## Phase 4: Recall / Read Path

Refactor `brain_service.recall()` and retrieval modules to be Cognee-first.

New recall behavior:
- Resolve context and node-set scope from control store.
- For direct profile/bias/receipt/pending-confirmation/admin lookup, answer from control store.
- For palate recommendations, run Brain palate ranking policy and use Cognee palate recall/search for semantic evidence.
- For ordinary memory/source QA, call Cognee `recall` or `search`.
- Apply Brain read policy after Cognee returns results:
  - user/profile scope
  - status visibility where status is present in datapoints
  - grounding/evidence formatting
  - app-safe response shaping

Remove from normal recall path:
- Brain DB `search_memory`
- Brain DB entity profile as semantic source
- Broad "Known memories" rendering from Brain DB rows
- Brain DB recall log writes as the semantic query log

Compatibility:
- `RecallResponse` remains the MCP/REST output model.
- `facts` and `evidence` are built from Cognee result payloads/datapoint metadata.
- `open_loops` are returned from Cognee datapoints or control records, not old `open_loops` rows.

## Phase 5: Profile, Bias, and Session Context

Refactor profile/bias/session code so it aligns with the diagrams.

Profile/bias:
- Store profile and bias records in `brain_context_records`.
- Keep legacy profile-context JSON import for one migration pass only.
- `brain_profile_context_remember/list/forget` operate on `brain_context_records`.
- On create/update/delete, optionally project `BrainContextDataPoint` to Cognee when searchable context is enabled.

Session maps:
- Replace ad hoc session id derivation as the only source of truth with `brain_session_maps`.
- `brain_session_payload()` returns the mapped Cognee session id and dataset.
- external chat-continuity workflow and external chat-continuity recall use the mapped Cognee session/dataset.
- Preserve deterministic fallback id generation only for creating new session-map rows.

Bias:
- Add bias context as first-class records under `kind="bias"`.
- Bias records are injected into Brain read/write policy and may be projected to Cognee as context datapoints.
- Keep current `brain_bias_protocol` behavior but source its facts from `brain_context_records`.

## Phase 6: Palate Cutover

Keep Brain as palate policy owner, but remove Brain semantic projections.

- Make Cognee palate store the default canonical palate store.
- Keep Brain-side taste logic for:
  - normalization
  - enrichment
  - ranking policy
  - negative-signal handling
  - proposal/confirmation workflow
  - decision feedback
- Store approved palate items, signals, and decisions as Cognee typed datapoints.
- Stop creating Brain `memory_cards`, Brain `entities`, Brain `relationships`, or Brain `open_loops` for palate evidence.
- Update palate query/evaluate tools to combine:
  - Brain ranking policy
  - Cognee semantic evidence
  - control-store decision history

Migration note:
- Existing SQLite taste tables can be exported to Cognee once, then treated as legacy/debug data.
- Tests should target Cognee-backed in-memory adapters, not Brain DB taste projections.

## Phase 7: Admin, Maintenance, and Tool Surface

Reclassify tools to match new ownership.

Keep public/user tools:
- `brain_session`
- `brain_remember`
- `brain_ingest_source`
- `brain_recall`
- profile/bias context tools
- app data controls
- palate describe/query/evaluate/confirm/cancel/correct
- chat continuity tools

Change admin tools:
- Deprecate or replace old projection tools:
  - `brain_rebuild_cognee` is hard-deprecated.
  - `brain_sync_cognee` is hard-deprecated.
- Replace `brain_get_memory` / `brain_get_source` internals with Cognee lookup by external id.
- Replace `brain_review_recent` with receipt/control-store review.
- Replace `brain_undo_last` with receipt-based Cognee native forget, with status-event datapoints retained only as audit evidence.
- Replace `brain_resolve_conflict` with status-event/control-policy flow against Cognee datapoints.
- Remove `brain_merge_entities` from normal admin surface unless Cognee exposes a safe graph merge API.

Response compatibility:
- Keep tool names where possible.
- Update descriptions so they no longer promise Brain DB memory cards/entities.
- Update output schemas only where necessary; prefer adding `receipt_id`, `cognee_reference`, and `control_status` over removing existing fields in the first cutover.

## Phase 8: Slack Unsupported Surface

Do not delete Slack code in this change, but make it unsupported.

- Set `BRAIN_SLACK_ENABLED=false` and `BRAIN_SLACK_AGENT_ENABLED=false` in all default environment/config files.
- Remove Slack setup from primary README/API docs and move any remaining instructions to an "unsupported legacy adapter" note.
- Exclude Slack from docs index, diagrams, app UI links, public route summaries, and deployment requirement expectations.
- Keep tests for Slack code only if they are quarantined as legacy and do not imply supported product behavior.
- Do not update Slack logic for the new Cognee-first semantic model unless needed to prevent import/test breakage.

## Phase 9: Migration / Cutover Mechanics

Implement a hard cutover with explicit one-time export utilities.

One-time export command:
- Export current Brain DB semantic rows into Cognee typed datapoints:
  - current memory cards -> `BrainMemoryDataPoint`
  - sources -> `BrainSourceDataPoint` and optional chunks
  - open loops -> memory/status/context datapoints
  - taste rows -> palate datapoints
  - profile context JSON/old projection rows -> `brain_context_records` and optional Cognee datapoints
- Write one receipt per exported object into `brain_external_receipts`.
- Do not keep `cognee_sync` rows as the authoritative migration state.

Post-export:
- Normal service paths must not write old semantic tables.
- Existing old tables remain for backup/debug until a later cleanup migration.
- Add an integrity verifier:
  - counts exported records
  - samples Cognee recall/search by external id
  - confirms no new semantic Brain rows were created during cutover tests

## Phase 10: Tests

Rewrite tests around the new ownership model.

Core service tests:
- `brain_remember` commits to fake Cognee adapter and writes only control receipt rows.
- Cognee unavailable causes durable write failure and no semantic Brain rows.
- Dry-run creates no Cognee write and returns preview receipt.
- Pending confirmation writes only `brain_pending_confirmations`; confirm commits to Cognee.
- `brain_ingest_source` sends source content to Cognee and does not store raw text in Brain DB.
- `brain_recall` calls Cognee and formats `RecallResponse` from Cognee payloads.
- Control-store lookup answers profile/bias/receipt/admin queries without Cognee recall.

Profile/session tests:
- `brain_session_payload` creates/returns stable session-map rows.
- User/profile/surface separation produces distinct Cognee session ids and datasets.
- Profile/bias records are listed, forgotten, and optionally projected to Cognee.

Palate tests:
- Approved palate item writes typed Cognee datapoints.
- Palate query combines Brain ranking policy with Cognee evidence.
- Negative signals and decision feedback remain Brain policy behavior.
- No Brain memory/entity/relationship rows are created for palate writes.

Admin/tool tests:
- MCP tool lists and descriptions reflect Cognee-first ownership.
- Deprecated sync/rebuild behavior is removed or clearly mapped to Cognee maintenance.
- Review/undo operate through receipts and Cognee native forget, with status events used only as audit evidence.
- App confirmation requirements still hold.

Migration tests:
- Legacy Brain DB fixture exports to Cognee datapoints.
- Export is idempotent.
- Export writes external receipts.
- After cutover, old semantic tables do not receive new rows.

Docs/config tests:
- Proposed diagrams have no Slack references.
- README/API docs no longer present Slack as supported.
- Default configs disable Slack in dev/qa/staging/prod.
- Public docs say Cognee is required for durable memory.

## Phase 11: Rollout and Verification

Local verification:
- Run unit tests for service, MCP, palate, profile/session, Cognee adapters, migrations.
- Run migration export against a copied local Brain DB.
- Verify no new rows are written to old semantic tables during write/recall tests.
- Verify Cognee recall works for exported memory/source/profile/palate records.

Staging rollout:
- Backup Brain DB, Cognee DB, vector store, graph store, profile context files, and configs.
- Run export utility.
- Start Brain with Cognee-required durable writes.
- Smoke test REST/MCP/app:
  - session payload
  - profile/bias list and remember
  - durable remember
  - source ingest
  - recall
  - palate query
  - undo/review through receipts
- Confirm Slack endpoints are not advertised or enabled.

Production rollout:
- Repeat staging sequence.
- Keep old semantic tables for rollback/debug only.
- Monitor request errors, Cognee write failures, recall failures, and receipt creation.
- Rollback strategy is config/code rollback plus restored backups, not dual-writing.

## Explicit Assumptions

- Public tool names remain stable unless a tool fundamentally conflicts with the new ownership model.
- Brain DB remains as a small control store, not as a semantic memory store.
- Cognee typed datapoints are the contract; Brain should not depend on Cognee private relational tables for normal operations.
- Existing old semantic tables are retained physically during this project but are no longer written by normal paths.
- Slack is unsupported and disabled in docs/config, but code deletion is deferred.
- The proposed diagrams remain valid; this plan does not require diagram changes.
