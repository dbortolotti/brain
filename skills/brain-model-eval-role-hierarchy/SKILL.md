---
name: brain-model-eval-role-hierarchy
description: Generate or refresh the Brain model eval role hierarchy Markdown artifact from the brain repo, including coarse roles, fine roles, deterministic roles, eligible models, close-to-eligible models, color-coded row status, and brief role descriptions.
metadata:
  short-description: Generate Brain model eval role hierarchy artifact
---

# Brain Model Eval Role Hierarchy

Use this skill when asked to create, refresh, or reformat Brain's model eval role hierarchy artifact.

Always run this skill before committing changes in the Brain repo, so the generated hierarchy artifact stays in sync with `brain_model_registry.yaml`.

## Output

Default output path from a Brain repo root:

```bash
artifacts/model_eval_phase_role_hierarchy.md
```

The artifact format is:

```md
# Model Eval Role Hierarchy


## `coarse_role`
*Coarse role brief.*

####  <span style="color: green;">fine_role: [model-or-deterministic]</span>
 >    *Brief: Fine role brief.*
```

Color rules:

- green: row has an eligible model or `[deterministic]`
- orange: row has a close-to-eligible model from `likely_after_more_samples`
- red: model role has no eligible model yet

Do not include the wording `eligible models` or `close to eligible models` in the rendered rows.

## Sources

Read from the Brain repo:

- `brain_model_registry.yaml`: `fine_grained_capabilities` and `fine_grained_deployment_decisions`

The same fine role may appear under multiple coarse roles; repeat it under each coarse role.

## Generate

From any directory, run:

```bash
python /Volumes/xpg_usb4/sandbox/git/brain/skills/brain-model-eval-role-hierarchy/scripts/generate_model_eval_role_hierarchy.py --repo /Volumes/xpg_usb4/sandbox/git/brain
```

From the Brain repo root:

```bash
python skills/brain-model-eval-role-hierarchy/scripts/generate_model_eval_role_hierarchy.py --repo . --output artifacts/model_eval_phase_role_hierarchy.md
```

Before every Brain repo commit:

```bash
make pre-commit
```

Equivalent direct script:

```bash
scripts/pre_commit_model_eval_role_hierarchy.sh
```

## Verify

After generation:

```bash
sed -n '1,240p' artifacts/model_eval_phase_role_hierarchy.md
git status --short artifacts/model_eval_phase_role_hierarchy.md
```

If the user asks to commit after creating or changing this repo-local skill, commit both the skill files and the generated artifact unless they ask for a narrower commit.
