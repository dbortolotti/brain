---
name: brain-model-eval-iteration
description: Run the Brain repo's fine-grained model evaluation loop for one requested model, with configurable repeats, endpoint concurrency, roles, output folder under eval_runs, live progress/ETA updates, fixture_prompt_expected_failure_table.csv review, harness/scoring fixes, failed-case reruns, and iteration until no further harness/scoring misspecifications are found.
metadata:
  short-description: Iterate Brain model evals and harness fixes
---

# Brain Model Eval Iteration

Use this skill in the Brain repo when the user asks to run or iterate model evaluation tests, evaluate one model's production readiness, rerun failures, audit `fixture_prompt_expected_failure_table.csv`, or improve scoring/harness issues found by those evals.

## Evaluation Bias

Start skeptical. The job is to test whether the requested model is appropriate for Brain's production roles, not to rescue the model or make the eval pass.

Default prior:

- Assume the model is not appropriate until the eval evidence shows it satisfies the role contracts.
- Treat failures as true model failures unless there is clear evidence that the harness, scorer, fixture, or prompt contract is wrong.
- Do not patch scoring/harness simply because the model gave a plausible answer.
- Only modify harness/scoring when confident the current check is inappropriate, misleading, or too narrow for the documented role contract.
- Modify prompts or role descriptions when the role description is insufficient, ambiguous, or does not state a requirement that the scorer enforces.
- When uncertain, preserve the failure and mark it `uncertain` or `requires_user_decision`; do not weaken the gate.

## Defaults

Unless the user specifies otherwise:

- Model: `openai:gpt-5.5`
- Repeats: `3`
- Endpoint max concurrency: `10`
- Roles: all fine-grained roles, excluding embeddings. In the current CLI, omit `--roles` with `--mode fine-grained` to get this set.
- Fixture set: `production`
- Output root: `eval_runs/<chosen-run-folder>` under the repo root

If the user does not specify an output folder, pick:

```bash
eval_runs/model_eval_<sanitized-model>_$(date +%Y%m%d_%H%M%S)
```

Tell the user the chosen folder before starting.

## Initial Checks

From the repo root:

```bash
pwd
git status --short
uv run brain eval models --help
```

Do not require a clean worktree. Do not revert unrelated changes. If existing user changes touch scoring, fixtures, prompts, or model runner code, inspect them before editing and work with them.

## Production Model Secrets

Use the same model/provider secrets as the production deployment. Do not invent ad hoc API keys or switch auth modes for eval convenience.

Before running the eval, load or verify the production deployment environment/secrets used by the local production service. Prefer the repo's existing production deploy/render scripts and generated production env file if present. Redact secret values in all user-facing output and logs.

Confirm the active model-secret source in the status update before starting, for example:

```text
Using production deployment model secrets from <redacted-source>; values redacted.
```

If production model secrets are unavailable or ambiguous, stop and ask the user where the production deployment env/secrets should be sourced from. Do not silently fall back to unrelated local shell credentials.

## Run Command

Create the output directory, then run:

```bash
uv run brain eval models \
  --registry brain_model_registry.yaml \
  --fixture-set production \
  --mode fine-grained \
  --models <model-ref> \
  --repeat-runs <repeats> \
  --endpoint-max-concurrency <concurrency> \
  --output-json <run-dir>/results.json \
  --report-md <run-dir>/summary.md \
  --raw-output-dir <run-dir>/raw
```

Only add `--roles <comma-separated-roles>` if the user supplied roles.

The run must produce:

- `<run-dir>/results.json`
- `<run-dir>/summary.md`
- `<run-dir>/summary.html`
- `<run-dir>/failed_tests.jsonl`
- `<run-dir>/fixture_prompt_expected_failure_table.csv`
- `<run-dir>/fixture_prompt_expected_failure_table.md`

If the monitor is useful, start it in another terminal/session:

```bash
uv run python scripts/brain_eval_monitor.py \
  --run-dir <run-dir> \
  --results-json <run-dir>/results.json \
  --loop \
  --serve \
  --bind 0.0.0.0 \
  --port 18084
```

Tell the user the Tailscale URL shape:

```text
http://<mac-tailscale-name-or-ip>:18084/
```

## Status Updates And ETA

Print concise status updates about every 30 seconds while a long run is active.

Include:

- Current phase: running eval, auditing failures, patching harness/scoring, rerunning failed cases, or verifying
- Progress as `done/total` when available
- Status counts when available
- ETA when enough progress exists
- Served HTML monitor link when available, e.g. `http://<mac-tailscale-name-or-ip>:18084/`

For ETA, use the run start time and current progress:

```text
elapsed = now - start
rate = done / elapsed
remaining = total - done
eta = now + remaining / rate
```

If progress is unavailable, say so and report the latest log line or artifact timestamp instead.

When the monitor server is running, include the monitor URL in every periodic update so the user can open the live HTML page from their iPhone. If the exact Tailscale hostname/IP is unknown, include the URL shape and the local port.

Useful status commands:

```bash
tail -80 <run-dir>/run.log
cat <run-dir>/live_status.json
wc -l <run-dir>/fixture_prompt_expected_failure_table.csv
```

If the eval command is run through `exec_command`, redirect output to `<run-dir>/run.log` and keep the process/session until it exits.

## Failure Audit

After each eval or rerun, read:

```bash
<run-dir>/fixture_prompt_expected_failure_table.csv
<run-dir>/failed_tests.jsonl
<run-dir>/summary.md
```

For each failure cluster, inspect enough evidence to classify it:

- fixture input and expected behavior
- prompt contract
- parsed output
- raw output
- scoring code in `src/memory_stack/evals/scoring.py`
- fixture construction/contracts in `src/memory_stack/evals/model_fixtures.py`
- artifact generation in `src/memory_stack/evals/model_runner.py` if descriptions or manifests are wrong

Always check whether the scoring logic is appropriate for the role as defined and for the fixture expectations. The scorer must measure the actual role contract, not an adjacent broad capability or an implicit expectation that is absent from the prompt/fixture. If the role definition, expected fields, and scorer disagree, classify the cluster as `prompt_contract_issue`, `fixture_issue`, or `harness_scoring_issue` according to the concrete source of the mismatch.

Classify failures as:

- `true_model_error`: prompt/expected/scorer are coherent and the model output violates them
- `harness_scoring_issue`: scorer rejects an acceptable answer, uses the wrong label, conflates separate requirements, or cannot express accepted equivalents
- `fixture_issue`: expected output or fixture text is ambiguous, contradictory, stale, or too broad for the role
- `prompt_contract_issue`: prompt omits a requirement that the scorer enforces, or asks for a different ontology than the scorer expects
- `uncertain`: insufficient evidence; do not patch blindly

Write or update an audit note in:

```bash
<run-dir>/failure_harness_audit.md
```

Keep the audit focused on concrete code-actionable clusters, not every individual row.

## Fix Rules

Patch harness/scoring only when the evidence shows a misspecification and you are confident the existing check is inappropriate.

Good fixes include:

- accepting equivalent safe labels or decisions
- separating zero-tolerance checks from generic quality score failures
- making role-specific expectations explicit
- aligning fixture expected values with the role prompt ontology
- tightening prompts when the scorer already reflects the intended product contract
- improving failure descriptions when they are misleading
- expanding role descriptions in prompts when the scorer relies on role behavior that was not adequately described

Avoid:

- lowering thresholds just to pass the run
- deleting hard safety checks without replacing them with a more accurate check
- changing model outputs or raw artifacts
- broad refactors unrelated to the failure cluster
- reclassifying a failure as harness/scoring issue because the model output is subjectively reasonable but still violates the prompt, expected fixture behavior, or product contract

Use focused tests after code changes:

```bash
uv run pytest tests/test_model_eval_runner.py -q
```

Add or update tests when changing scorer or fixture semantics.

## Rerun Failed Cases

After a harness/scoring fix, rerun only failed cases:

```bash
uv run brain eval rerun-failed \
  --registry brain_model_registry.yaml \
  --source-json <run-dir>/results.json \
  --failed-manifest <run-dir>/failed_tests.jsonl \
  --output-json <run-dir>/results.json \
  --endpoint-max-concurrency <concurrency> \
  --overwrite \
  --model <model-ref>
```

If only one role or failure class was affected, narrow the rerun:

```bash
--role <role>
--failure-class <failure-class>
```

After rerun, reread `fixture_prompt_expected_failure_table.csv`, `summary.md`, and `failed_tests.jsonl`, then repeat the audit/fix/rerun cycle.

## Stop Condition

Stop iterating when:

- no remaining failure clusters are clearly harness/scoring/fixture/prompt misspecifications, or
- a proposed fix would change product semantics and needs user approval, or
- external provider/runtime issues block further evals.

Final report must include:

- run folder
- model, repeats, concurrency, roles
- final status counts and deployability verdict from `summary.md`
- harness/scoring fixes made, with file paths
- reruns performed
- remaining failures grouped as true model errors, uncertain, or requiring user decision
- tests run and whether they passed

## Clarifying Questions

Ask at most five short questions only when needed. Prefer proceeding with the defaults above. Useful questions are:

1. Which model ref should be tested?
2. How many repeats?
3. What endpoint max concurrency?
4. Which roles, if not all non-embedding fine-grained roles?
5. What folder name under `eval_runs/`?
