# taste_enrichment_planner

## Purpose
Plan which allowed enrichment sources may be used for a Taste item.

## Scope
- Owns source-policy decisions for Taste enrichment.
- Does not fetch data, normalize fetched data, or write records.

## Inputs
- Taste category, item identity, route confidence, user text, and configuration flags.

## Output Contract
- Return allowed_sources, blocked_sources, should_enrich, strict_source_required, broader_search_allowed, and warnings when schema permits.

## Decision Procedure
1. Identify the category and its strict source allowlist.
2. Decide whether enrichment is useful and enabled.
3. Keep broader web search disabled unless the user explicitly permits it.
4. Mark failed or skipped enrichment paths as requiring confirmation before minimal storage.

## Must Do
- Use OMDb only for structured media ratings/runtime/country/language/seasons fields.
- Use restaurant allowed sources only for restaurant metadata.
- Keep conservative enrichment for music, wine, cigar, and experience unless category policy is implemented.

## Must Not Do
- Do not broaden search automatically after a strict-source miss.
- Do not mix raw source snippets into normalized metadata.
- Do not create fallback structured claims from prompt text alone after enrichment failure.

## Safety / Failure Modes
- If strict sources are unavailable, return skipped or failed with warnings.
- If the user wants to store anyway, route that as minimal user-input-only storage.

## Verification Notes
- Enrichment status and source policy must be visible in tool responses.
- Strict-source misses must ask whether to broaden search or save minimal input.
