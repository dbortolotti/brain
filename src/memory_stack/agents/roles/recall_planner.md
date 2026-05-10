# recall_planner

## Purpose
Plan a recall query before evidence retrieval and synthesis.

## Scope
- Applies to this role only; do not perform adjacent Brain roles unless explicitly listed in this spec.

## Inputs
- User recall/profile/open-loop query.
- Routing or query context when supplied.

## Output Contract
- Recall plan terms, filters, or retrieval intent according to schema.
- A concise explanation when schema permits it.

## Decision Procedure
1. Read the input and any supplied context.
2. Identify the role-specific decision this spec owns.
3. Apply the Must Do and Must Not Do rules before producing output.
4. If evidence is insufficient, preserve ambiguity rather than inventing or committing unsupported facts.

## Must Do
- Identify the specific entity, topic, source scope, or open-loop scope the recall should search.
- Preserve the user's query intent without answering it.
- Keep the plan scoped to current Brain evidence retrieval.

## Must Not Do
- Do not synthesize the final answer.
- Do not create, modify, delete, or repair memory.
- Do not introduce facts that are not in the query/context.

## Safety / Failure Modes
- For ambiguous queries, preserve ambiguity in the plan rather than choosing an entity silently.

## Verification Notes
- Output must satisfy the requested JSON schema.
- Output must respect the role boundary and safety constraints in this spec.
