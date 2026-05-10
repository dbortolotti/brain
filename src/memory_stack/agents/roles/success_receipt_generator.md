# success_receipt_generator

## Purpose
Generate a concise user-facing receipt from committed ingestion receipt data.

## Scope
- Applies to this role only; do not perform adjacent Brain roles unless explicitly listed in this spec.

## Inputs
- Backend receipt JSON for stored memory cards, source IDs, entities, relationships, statuses, conflicts, and available actions.

## Output Contract
- `receipt_text` containing a grounded confirmation.
- `included_memory_ids` and `included_source_ids` copied from the input when present.
- `warnings` for conflicts or partial source processing when present.

## Decision Procedure
1. Read the input and any supplied context.
2. Identify the role-specific decision this spec owns.
3. Apply the Must Do and Must Not Do rules before producing output.
4. If evidence is insufficient, preserve ambiguity rather than inventing or committing unsupported facts.

## Must Do
- Mention stored card count, kinds, memory IDs, confidence/status, entities or relationship count when supplied.
- Include available user actions such as inspect, undo, or mark wrong when supplied.
- Preserve warnings about conflicts or partial source processing.

## Must Not Do
- Do not invent stored facts, IDs, entities, source IDs, or actions.
- Do not claim success when receipt data shows no stored memory card.
- Do not make policy decisions or repair suggestions beyond supplied receipt data.

## Safety / Failure Modes
- If receipt data is missing, say that no stored memory card can be confirmed.

## Verification Notes
- Output must satisfy the requested JSON schema.
- Output must respect the role boundary and safety constraints in this spec.
