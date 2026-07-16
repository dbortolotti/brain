# Purpose

- Own agent prompt contracts, role markdown, shared memory-agent rules, and utilities that load and validate role specifications.

## Ownership

- `role_specs.py` owns role markdown discovery and section extraction.
- `prompt_contracts.py` owns prompt contract helpers.
- `roles/` owns per-role markdown instructions.
- `shared/` owns shared architecture and memory-agent rules.

## Local Contracts

- Every file in `roles/` must keep the required sections from `REQUIRED_ROLE_SPEC_SECTIONS` in `role_specs.py`.
- Role specs must define output contracts and failure modes clearly enough for automated evals and agents to enforce them.
- Prompt rules must not instruct agents to store secrets, credentials, raw logs, full datasets, or unsupported sensitive material.

## Work Guidance

- Keep prompt markdown operational: purpose, scope, inputs, output contract, decision procedure, required behavior, forbidden behavior, safety, and verification notes.
- Update eval fixtures or role-spec tests when changing role behavior.

## Verification

- Run `uv run pytest tests/test_agent_role_specs.py` after role markdown or prompt loader changes.
- Run model evals only when behavior changes are broad enough to need live or offline quality measurement.

## Child DOX Index

- No child AGENTS.md files. `roles/` and `shared/` are owned here.
