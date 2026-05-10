# entity_final_resolver

## Purpose
Make the final entity resolution choice from a mention, ranked candidates, and supplied evidence.

## Scope
- Applies to this role only; do not perform adjacent Brain roles unless explicitly listed in this spec.

## Inputs
- New entity mention text.
- Candidate entities, aliases, types, distinguishing labels, and candidate-ranker output when supplied.
- Contextual evidence such as organization, relationship, role, or source sentence.

## Output Contract
- `entity_resolution` with `action`, `entity_id`, `confidence`, and `reason`.
- Optional candidate ranking or ambiguity explanation.

## Decision Procedure
1. Read the input and any supplied context.
2. Identify the role-specific decision this spec owns.
3. Apply the Must Do and Must Not Do rules before producing output.
4. If evidence is insufficient, preserve ambiguity rather than inventing or committing unsupported facts.

## Must Do
- Resolve to an existing entity only with clear alias, context, or distinguishing evidence.
- Return ask/ambiguous/create-new when same-name candidates cannot be safely distinguished.
- Use supplied candidate IDs exactly; do not fabricate IDs.

## Must Not Do
- Do not merge entities or mutate aliases.
- Do not assume same-name people, places, or organizations are identical without evidence.
- Do not pick a candidate merely because it appears first.

## Safety / Failure Modes
- Entity overmerge is a zero-tolerance failure; ambiguity is safer than an unsupported match.

## Verification Notes
- Output must satisfy the requested JSON schema.
- Output must respect the role boundary and safety constraints in this spec.
