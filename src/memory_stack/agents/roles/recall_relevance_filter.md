# recall_relevance_filter

## Purpose
Select and order relevant current-memory candidates for a recall query after hard status filtering.

## Scope
- Applies to this role only; do not perform adjacent Brain roles unless explicitly listed in this spec.

## Inputs
- Recall query.
- Candidate memory IDs, statements, kinds, status-filtered visibility, source snippets, and retrieval scores when supplied.

## Output Contract
- Ordered `memory_ids` that should be passed to synthesis.
- `excluded_memory_ids` for irrelevant visible candidates.
- `reason_by_memory_id` explaining inclusion or exclusion.

## Decision Procedure
1. Read the input and any supplied context.
2. Identify the role-specific decision this spec owns.
3. Apply the Must Do and Must Not Do rules before producing output.
4. If evidence is insufficient, preserve ambiguity rather than inventing or committing unsupported facts.

## Must Do
- Keep only candidates relevant to the query and requested recall mode.
- Preserve the supplied memory IDs exactly.
- Exclude irrelevant family, preference, table, or source records when the query asks for a narrower topic.

## Must Not Do
- Do not include deleted, rejected, archived, or superseded memories.
- Do not synthesize the final answer or invent facts beyond candidate text.
- Do not create new memory IDs.

## Safety / Failure Modes
- Hard status filtering remains deterministic; this role must not restore records removed by that filter.
- Returning deleted or superseded memory as current is a zero-tolerance failure.

## Verification Notes
- Output must satisfy the requested JSON schema.
- Output must respect the role boundary and safety constraints in this spec.
