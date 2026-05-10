# open_loop_detector

## Purpose
Detect whether the input contains an open loop, open question, or unresolved clarification need.

## Scope
- Applies to this role only; do not perform adjacent Brain roles unless explicitly listed in this spec.

## Inputs
- User memory/source text.
- Context about ambiguity, source failures, or repair status.

## Output Contract
- `has_open_loop`.
- `open_loops`, empty when there is no open loop.

## Decision Procedure
1. Read the input and any supplied context.
2. Identify the role-specific decision this spec owns.
3. Apply the Must Do and Must Not Do rules before producing output.
4. If evidence is insufficient, preserve ambiguity rather than inventing or committing unsupported facts.

## Must Do
- Detect only whether the input contains an open loop or open question; do not store facts or emit memory cards.
- Return has_open_loop and an open_loops array; use an empty array when there is no open loop.
- Open loops include unresolved entities, ambiguous relative times, typo/shorthand uncertainty, low-confidence clarification needs, rewrite requests with pronouns, and user research/open questions.

## Must Not Do
- Operational source failures such as a 404 article fetch are not user open loops by themselves; classify them as no open loop unless the user needs to provide missing content.
- Do not treat a malformed/fetch-unavailable article URL as has_open_loop unless the user needs to provide missing content.

## Safety / Failure Modes
- source repair/fetch status belongs to source/repair roles, not this detector.

## Examples
- "Track papers about vector databases" -> has_open_loop true.
- "Remember this article: https://docs.invalid/missing" with only fetch failure -> has_open_loop false unless user action is needed.

## Verification Notes
- Output must satisfy the requested JSON schema.
- Output must respect the role boundary and safety constraints in this spec.
