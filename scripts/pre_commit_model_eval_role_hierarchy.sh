#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

uv run python skills/brain-model-eval-role-hierarchy/scripts/generate_model_eval_role_hierarchy.py \
  --repo . \
  --output artifacts/model_eval_phase_role_hierarchy.md

git status --short artifacts/model_eval_phase_role_hierarchy.md skills/brain-model-eval-role-hierarchy
