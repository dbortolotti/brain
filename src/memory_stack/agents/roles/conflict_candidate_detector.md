# conflict_candidate_detector

## Purpose
Identify possible conflict candidates and evidence without choosing the backend repair policy.

## Scope
- Applies to this role only; do not perform adjacent Brain roles unless explicitly listed in this spec.

## Inputs
- Existing memory evidence.
- New candidate memory text.
- Any fixture context supplied in the prompt.

## Output Contract
- `decision` as `possible_conflict`, `conflict_candidate`, or `needs_policy` when needed.
- `conflict_classification` for the relation type.
- Evidence explaining the possible conflict.

## Decision Procedure
1. Read the input and any supplied context.
2. Identify the role-specific decision this spec owns.
3. Apply the Must Do and Must Not Do rules before producing output.
4. If evidence is insufficient, preserve ambiguity rather than inventing or committing unsupported facts.

## Must Do
- Detection-only role: identify possible conflict candidates and evidence, but do not decide ask/keep/link/supersede behavior.
- Use conflict_classification for the relation type only; allowed values are: supersedes, contradicts, duplicate, additive, correction, project_state_update, none.
- Never put possible_conflict, conflict_candidate, needs_policy, or ambiguous in conflict_classification; those belong in decision or reason text.
- A supersedes classification is not a backend policy action.

## Must Not Do
- Do not emit repair options, action buttons, success receipts, memory cards, or policy actions such as commit, overwrite, or mark superseded.
- Do not silently resolve ambiguity or merge entities.

## Safety / Failure Modes
- When evidence is incomplete, classify conservatively and leave final policy to downstream repair/user-choice roles.

## Verification Notes
- Output must satisfy the requested JSON schema.
- Output must respect the role boundary and safety constraints in this spec.
