# taste_enrichment_normalizer

## Purpose
Convert allowed-source enrichment payloads into normalized Taste metadata and source-qualified enrichment metadata.

## Scope
- Owns normalized/free-form metadata separation for Taste.
- Does not decide routing, source policy, ranking, or writes.

## Inputs
- Category, canonical item identity, allowed-source payloads, user notes, and validation context.

## Output Contract
- Return canonical_name, entity_type, normalized_metadata, attributes, attribute_intervals_95, enrichment_metadata, sources, warnings, confidence, and enrichment_status when schema permits.

## Decision Procedure
1. Normalize only fields supported by category policy.
2. Place source-qualified raw payloads, checked timestamps, URLs, diagnostics, and warnings in enrichment_metadata.
3. Validate attributes through strict category registries.
4. Mark unsupported or uncertain fields as warnings rather than structured fields.

## Must Do
- Keep normalized metadata clean and domain-shaped.
- Preserve source provenance separately.
- Report partial and failed enrichment explicitly.

## Must Not Do
- Do not put raw web snippets in normalized metadata.
- Do not add unknown attributes to structured attributes.
- Do not invent ratings, awards, genres, cuisines, or identity claims.

## Safety / Failure Modes
- On source contradiction, emit warnings and keep conflicting details in enrichment metadata.
- On unsupported provider data, preserve it only as source-qualified metadata when useful.

## Verification Notes
- Unknown fields must not affect ranking until promoted by a code change.
- Read-only enrichment must return stored=false downstream and perform no writes.
