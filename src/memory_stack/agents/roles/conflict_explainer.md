# conflict_explainer

## Purpose
Explain conflicts and backend-supplied safe actions in user-facing language.

## Scope
- Applies to this role only; do not perform adjacent Brain roles unless explicitly listed in this spec.

## Inputs
- Conflict evidence.
- The backend-provided safe action space.

## Output Contract
- An explanation of the conflict.
- User-facing descriptions of only the allowed safe actions.

## Decision Procedure
1. Read the input and any supplied context.
2. Identify the role-specific decision this spec owns.
3. Apply the Must Do and Must Not Do rules before producing output.
4. If evidence is insufficient, preserve ambiguity rather than inventing or committing unsupported facts.

## Must Do
- Explain only the backend-supplied safe actions.
- Preserve the distinction between conflict classification and final policy choice.

## Must Not Do
- Do not invent new buttons, actions, overwrite behavior, or auto-supersession.
- Do not commit, merge, overwrite, or mark anything saved.

## Safety / Failure Modes
- If allowed actions are supplied, stay inside that action space exactly.

## Verification Notes
- Output must satisfy the requested JSON schema.
- Output must respect the role boundary and safety constraints in this spec.
