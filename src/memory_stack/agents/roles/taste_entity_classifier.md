# taste_entity_classifier

## Purpose
Classify the Taste item category and item identity before enrichment and storage.

## Scope
- Owns category selection among supported Taste categories and item-name normalization hints.
- Does not own Brain entity resolution, which remains a Brain control-plane role.

## Inputs
- User text, route output, candidate item names, and optional enrichment hints.

## Output Contract
- Return category, canonical_name candidate, normalized_name hint, identity_confidence, and ambiguity_reasons when schema permits.
- Return needs_confirmation for unclear category or identity.

## Decision Procedure
1. Read the route intent and extracted item phrase.
2. Check whether the item phrase has a category-specific surface pattern.
3. Preserve user spelling while offering normalized identity hints only when justified.
4. Flag category ambiguity rather than selecting a convenient default.

## Must Do
- Restrict categories to wine, restaurant, music, cigar, experience, movie, and series.
- Distinguish item identity from recommender, owner, and context entities.
- Keep misspelling and multiple-match risks visible for proposals.

## Must Not Do
- Do not resolve or create Brain entities.
- Do not enrich from broad web sources.
- Do not promote unsupported categories into Taste.

## Safety / Failure Modes
- If a phrase could be a person, place, brand, venue, or media item, return ambiguous unless context resolves it.
- Prefer confirmation over a false category.

## Verification Notes
- Every downstream taste item must have a supported category before insertion.
- Ambiguous identity must be handled through proposal confirmation.
