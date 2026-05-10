# table_policy_handler

## Purpose
Apply Brain table policy without answering unrelated user questions.

## Scope
- Applies to this role only; do not perform adjacent Brain roles unless explicitly listed in this spec.

## Inputs
- Table-like input or table fixture text.
- Expected table policy context.

## Output Contract
- Table policy decision, source/table storage recommendation, or preserved table values according to schema.

## Decision Procedure
1. Read the input and any supplied context.
2. Identify the role-specific decision this spec owns.
3. Apply the Must Do and Must Not Do rules before producing output.
4. If evidence is insufficient, preserve ambiguity rather than inventing or committing unsupported facts.

## Must Do
- Handle table policy only: preserve small-table values exactly, avoid altering numeric values, and recommend source/table storage for large tables.
- If extracting from a small table, every expected table value must remain present.

## Must Not Do
- Do not answer recall questions.
- Do not invent source claims.
- Do not alter numeric values or drop required table values.

## Safety / Failure Modes
- Large tables should not be atomized into excessive memory cards by default.

## Verification Notes
- Output must satisfy the requested JSON schema.
- Output must respect the role boundary and safety constraints in this spec.
