# LLM-Promoted Workflow Test Battery

## Purpose

This battery validates the roles promoted from deterministic ownership to LLM-owned role-agent decisions.

Runtime safety validators, schema checks, source loaders, parsers, and hard status gates remain backend-owned. The tested judgment and wording roles are LLM-owned.

## Roles Covered

- `commit_policy_decider`
- `success_receipt_generator`
- `entity_final_resolver`
- `conflict_policy_decider`
- `recall_relevance_filter`

## Role Checks

- Commit policy: clean high-confidence memory may commit; unconfirmed conflict must ask.
- Success receipt: generated receipt must stay grounded in backend receipt data.
- Entity final resolver: alias evidence can match; ambiguous same-name candidates must ask.
- Conflict policy: duplicates can be marked duplicate; supersession without confirmation must ask.
- Recall relevance filter: blocked memory IDs must not be restored; broad visible retrieval can be semantically pruned.

## Run Command

```bash
RUN_DIR=eval_runs/llm_promoted_workflows
uv run brain eval models \
  --fixture-set llm-promoted-workflows \
  --mode fine-grained \
  --roles commit_policy_decider,success_receipt_generator,entity_final_resolver,conflict_policy_decider,recall_relevance_filter \
  --models <model-ref> \
  --repeat-runs 3 \
  --output-json "$RUN_DIR/results.json" \
  --report-md "$RUN_DIR/summary.md" \
  --raw-output-dir "$RUN_DIR/raw"
```

## HTML Monitor

Start the monitor before or during the eval run. It refreshes `index.html` every
10 seconds and serves the run directory over HTTP.

```bash
RUN_DIR=eval_runs/llm_promoted_workflows
mkdir -p "$RUN_DIR"
uv run python scripts/brain_eval_monitor.py \
  --run-dir "$RUN_DIR" \
  --results-json "$RUN_DIR/results.json" \
  --raw-dir "$RUN_DIR/raw" \
  --interval-seconds 10 \
  --loop \
  --serve \
  --bind 0.0.0.0 \
  --port 18084
```

Open:

```text
http://localhost:18084/
```

## Acceptance Gate

- Zero zero-tolerance failures.
- No entity overmerge.
- No silent high-confidence overwrite.
- No hallucinated receipt facts or IDs.
- No deleted, rejected, archived, or superseded memory returned as current.
- Semantic quality for each promoted role must meet that role's fine-grained eligibility gate.
