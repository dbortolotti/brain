# Deterministic vs LLM Workflow Test Battery

## Purpose

This battery compares the promoted LLM role-agent workflows against the deterministic workflow baselines they may eventually augment.

It is eval-first only. Runtime writes, status filters, parsers, and source loaders remain deterministic.

## Roles Covered

- `commit_policy_decider`
- `success_receipt_generator`
- `entity_final_resolver`
- `conflict_policy_decider`
- `recall_relevance_filter`

## Baseline Comparisons

- Commit policy: clean high-confidence memory may commit; unconfirmed conflict must ask.
- Success receipt: LLM receipt must stay grounded in backend receipt data.
- Entity final resolver: alias evidence can match; ambiguous same-name candidates must ask.
- Conflict policy: duplicates can be marked duplicate; supersession without confirmation must ask.
- Recall relevance filter: hard status-filtered memories must not be restored; broad deterministic retrieval can be semantically pruned.

## Run Command

```bash
RUN_DIR=eval_runs/deterministic_vs_llm_workflows
uv run brain eval models \
  --fixture-set development \
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
RUN_DIR=eval_runs/deterministic_vs_llm_workflows
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
