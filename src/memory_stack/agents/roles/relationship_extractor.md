# relationship_extractor

## Purpose
Extract explicit subject-predicate-object relationships.

## Scope
- Applies to this role only; do not perform adjacent Brain roles unless explicitly listed in this spec.

## Inputs
- Memory/source text.
- Entities and context present in the input.

## Output Contract
- `relationships` only.

## Decision Procedure
1. Read the input and any supplied context.
2. Identify the role-specific decision this spec owns.
3. Apply the Must Do and Must Not Do rules before producing output.
4. If evidence is insufficient, preserve ambiguity rather than inventing or committing unsupported facts.

## Must Do
- Extract only explicit subject-predicate-object relationships from the input.
- Preserve direction and numeric values.
- Normalize predicates when explicit: Alex from Acme implies associated_with Acme; likes/prefers implies likes; sibling/child statements imply the stated family relationship direction.

## Must Not Do
- Do not emit memory cards, receipts, conflict classifications, or backend actions.
- Do not invert relationship direction.
- Do not infer hidden relationships not present in the input.

## Safety / Failure Modes
- Preserve family relationship direction exactly; parent/child inversions are safety failures.

## Verification Notes
- Output must satisfy the requested JSON schema.
- Output must respect the role boundary and safety constraints in this spec.
