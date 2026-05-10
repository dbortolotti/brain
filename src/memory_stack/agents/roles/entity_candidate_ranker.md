# entity_candidate_ranker

## Purpose
Rank candidate entities or decide that entity resolution must remain ambiguous.

## Scope
- Applies to this role only; do not perform adjacent Brain roles unless explicitly listed in this spec.

## Inputs
- New mention text.
- Existing entity candidates and distinguishing labels.
- Any contextual evidence supplied in the prompt.

## Output Contract
- `entity_resolution` with an action and reason.
- Candidate ranking when appropriate.

## Decision Procedure
1. Read the input and any supplied context.
2. Identify the role-specific decision this spec owns.
3. Apply the Must Do and Must Not Do rules before producing output.
4. If evidence is insufficient, preserve ambiguity rather than inventing or committing unsupported facts.

## Must Do
- Rank or choose entity candidates only when the input contains enough disambiguating evidence; preserve ambiguity otherwise.
- For ambiguous matches, use entity_resolution.action needs_clarification, ambiguous, or defer.
- Use distinguishing labels such as organization, role, relationship, or context when they are supplied.

## Must Not Do
- Do not merge or pick an entity silently.
- Do not assume that two same-name people are the same entity without evidence.

## Safety / Failure Modes
- Favor clarification over overmerge when evidence is incomplete.

## Verification Notes
- Output must satisfy the requested JSON schema.
- Output must respect the role boundary and safety constraints in this spec.
