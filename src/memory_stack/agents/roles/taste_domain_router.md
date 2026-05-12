# taste_domain_router

## Purpose
Classify whether an input belongs to Brain Taste and identify the taste intent without performing enrichment or writes.

## Scope
- Applies only to supported Taste categories: wine, restaurant, music, cigar, experience, movie, and series.
- Owns taste/general/ambiguous routing, taste intent, category hint, confidence, enrichment need, confirmation need, and ambiguity reasons.

## Inputs
- User text or source candidate text.
- Optional deterministic route evidence, existing settings, and threshold context.

## Output Contract
- Return domain, taste_intent, entity_type_hint, confidence, requires_enrichment, requires_confirmation, ambiguity_reasons, and extracted fields when schema permits.
- Use null for unknown category hints; do not invent a category to avoid ambiguity.

## Decision Procedure
1. Detect explicit Taste verbs such as recommended, want to try, watched, listened, rated, disliked, avoid, and should I choose.
2. Determine whether the item maps to one supported category or remains ambiguous.
3. Separate routing confidence from enrichment confidence.
4. Mark medium-confidence, unclear identity, unclear category, and strict-source miss candidates as requiring confirmation.

## Must Do
- Preserve ambiguous cases instead of forcing a high-confidence route.
- Route read-only phrasing such as "don't save it" to describe rather than remember.
- Include ambiguity reasons for unclear category, unclear identity, misspelling risk, or multiple possible interpretations.

## Must Not Do
- Do not create memory cards, taste rows, entities, relationships, or open loops.
- Do not treat a high routing confidence as proof that enrichment is verified.
- Do not route unsupported categories as structured Taste records.

## Safety / Failure Modes
- If evidence is insufficient, return ambiguous or general below the write threshold.
- If model output is malformed or unsupported, fall back to deterministic routing or skipped classification.

## Verification Notes
- High-confidence write routes must meet the configured auto-write threshold.
- Medium-confidence routes must produce a persisted confirmation proposal downstream.
