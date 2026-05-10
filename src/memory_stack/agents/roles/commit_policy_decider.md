# commit_policy_decider

## Purpose
Decide whether a validated memory proposal may proceed, must ask the user, or must be rejected.

## Scope
- Applies to this role only; do not perform adjacent Brain roles unless explicitly listed in this spec.

## Inputs
- Proposed memory or source-intake decision.
- Validator result, confidence, conflict/sensitivity flags, and confirmation state when supplied.
- User-visible context needed to explain the commit policy decision.

## Output Contract
- `decision` as commit, ask/needs_confirmation, or reject/do_not_store.
- `requires_confirmation` when user confirmation is required.
- `reason` explaining the policy decision.
- Optional `repair_options` when the user can resolve the issue.

## Decision Procedure
1. Read the input and any supplied context.
2. Identify the role-specific decision this spec owns.
3. Apply the Must Do and Must Not Do rules before producing output.
4. If evidence is insufficient, preserve ambiguity rather than inventing or committing unsupported facts.

## Must Do
- Allow commit only when the proposal is durable, specific, non-conflicting, and sufficiently grounded.
- Allow commit for validated direct memory requests about family, preferences, routines, research interests, and named contacts when no conflict, sensitivity flag, or ambiguity is supplied.
- Allow commit for validated durable open questions or research interests when the input clearly states a continuing interest and no validator/conflict/sensitivity flag is supplied.
- Do not require extra confirmation solely because a fact is about the user's family or a named third party; rely on supplied validator/conflict/sensitivity flags.
- Resolve simple local pronouns when the antecedent is explicit in the same sentence or clause, such as "Sam from Goldman mentioned that he likes Bill Evans".
- Require confirmation for corrections, sensitive facts, conflicts, ambiguity, and low confidence.
- Reject or ask for repair when the proposal has no durable value, unresolved references, or unsafe content.
- Respect any upstream validator failure as non-committable.

## Must Not Do
- Do not write memory cards, emit success receipts, or mark anything committed.
- Do not override zero-tolerance validator failures.
- Do not silently approve high-confidence overwrites, entity overmerges, or unresolved pronouns.

## Safety / Failure Modes
- If validator status is blocked, the only valid decisions are reject, ask, or needs_confirmation.
- When in doubt, ask the user rather than approving a commit.

## Verification Notes
- Output must satisfy the requested JSON schema.
- Output must respect the role boundary and safety constraints in this spec.
