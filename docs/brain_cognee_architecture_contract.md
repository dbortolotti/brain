# Brain/Cognee Architecture Contract

This note freezes the hard-cutover ownership model implemented from
`docs/proposed_brain_cognee_flow.md`.

## Brain owns control and policy

Brain is the facade for auth, user/profile scope, bias, session mapping,
confirmation policy, receipt policy, app write audit, and palate policy.
Brain's database is a control store. It can retain old semantic tables for
export, rollback analysis, and debugging, but normal durable write paths must
not create new rows in `memory_cards`, `sources`, `entities`, `relationships`,
or broad semantic `recall_logs`.

## Cognee owns semantic memory

Cognee is required for durable semantic memory, source ingestion, graph/vector
retrieval, source chunks and summaries, session memory contents, query logs,
improvement, and semantic forget/delete operations. If Cognee is unavailable
when a durable write is committed, Brain must fail clearly instead of falling
back to Brain DB semantic rows.

Normal source ingest currently writes the full `BrainSourceDataPoint` and any
compiled `BrainMemoryDataPoint` records to Cognee. `BrainSourceChunkDataPoint`
is part of the contract, but chunk emission is deferred until the Cognee-first
read path is wired so chunking policy and recall hydration can be tested
together.

## Control-store records

Brain stores only control facts needed to operate the facade:

- `brain_session_maps` maps client sessions to Cognee sessions, datasets, and
  node-set scope.
- `brain_external_receipts` records committed external/Cognee actions.
- `brain_pending_confirmations` records proposed writes that need user
  confirmation.
- `brain_context_records` stores profile and bias policy statements that Brain
  applies directly and may project into Cognee when searchable context is
  enabled.
