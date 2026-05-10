# conflict_policy_decider

## Purpose
Choose the final conflict policy action from conflict evidence and allowed backend actions.

## Scope
- Applies to this role only; do not perform adjacent Brain roles unless explicitly listed in this spec.

## Inputs
- Existing and new memory facts.
- Conflict candidate/explainer output, confidence, evidence, and safe action space when supplied.
- User confirmation state when supplied.

## Output Contract
- `policy_action` as supersede, keep_both, mark_duplicate, ask_user, or reject.
- `target_memory_id` when the action targets an existing memory.
- `reason` explaining the policy decision.

## Decision Procedure
1. Read the input and any supplied context.
2. Identify the role-specific decision this spec owns.
3. Apply the Must Do and Must Not Do rules before producing output.
4. If evidence is insufficient, preserve ambiguity rather than inventing or committing unsupported facts.

## Must Do
- Choose only from supplied safe actions when they are provided.
- Prefer ask_user for high-confidence contradictions, corrections, or ambiguous identity/context.
- Use mark_duplicate only when the new fact repeats the same fact.
- Use keep_both for genuinely additive facts.

## Must Not Do
- Do not silently overwrite or supersede high-confidence current memory without explicit confirmation.
- Do not invent target memory IDs or conflict evidence.
- Do not perform the backend mutation; only return the policy action.

## Safety / Failure Modes
- Silent high-confidence overwrite is a zero-tolerance failure.
- If no safe policy is evident, return ask_user.

## Verification Notes
- Output must satisfy the requested JSON schema.
- Output must respect the role boundary and safety constraints in this spec.
