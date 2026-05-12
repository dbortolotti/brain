# taste_memory_projector

## Purpose
Project user-originated Taste writes into Brain entities, memory cards, relationships, and open loops.

## Scope
- Owns Taste-specific projection planning.
- Brain remains responsible for final entity resolution, memory storage, relationship storage, open-loop lifecycle, privacy, backup, and conflicts.

## Inputs
- Validated Taste remember request, enriched item payload, extracted signals, owner context, recommender context, and open-loop thresholds.

## Output Contract
- Return projected Brain entity, evidence memory card, relationships, open loops, proposed closures, warnings, and IDs when available.

## Decision Procedure
1. Ensure the Taste item has or will have one Brain entity.
2. Create one Brain memory card for every user-originated Taste write.
3. Link the evidence memory to the Taste item entity and relevant people.
4. Create relationships and wanted-to-try/watch/listen open loops when signals require them.
5. Close matching open loops only above the configured high-confidence threshold; otherwise propose confirmation.

## Must Do
- Project recommended_by, wanted, rated, disliked, avoid, and experienced signals into relationships when applicable.
- Preserve evidence history on updates.
- Return relationship and open-loop IDs in write responses.

## Must Not Do
- Do not write anything for read-only describe_item.
- Do not create Brain memory cards for decision logs by default.
- Do not hard-delete Taste records without explicit confirmation.

## Safety / Failure Modes
- If projection confidence is medium, create a persisted proposal rather than silently closing loops.
- If entity identity is ambiguous, require confirmation before projection.

## Verification Notes
- Every Taste item must map to a Brain entity.
- Every user-originated Taste write must create exactly one evidence memory card for that write.
