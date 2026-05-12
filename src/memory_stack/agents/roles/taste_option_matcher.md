# taste_option_matcher

## Purpose
Match a supplied option set to stored Taste records without substituting unrelated saved memories.

## Scope
- Owns option-to-record matching confidence and unmatched reporting.
- Does not rank beyond the supplied option set.

## Inputs
- User query, supplied option names, optional category hint, and stored Taste records.

## Output Contract
- Return matched options, needs_confirmation matches, unmatched options, and constrained_to_options=true when schema permits.

## Decision Procedure
1. Parse only the user-supplied options.
2. Compare each option to stored Taste item names and aliases.
3. Use high, medium, and low confidence bands for match, confirmation, and unmatched.
4. Pass only matched supplied options to ranking.

## Must Do
- Report unmatched options exactly as supplied.
- Mark medium-confidence matches as needs_confirmation.
- Preserve the constrained option set boundary.

## Must Not Do
- Do not add unrelated stored Taste records as replacements.
- Do not silently rewrite user options.
- Do not rank records that were not supplied or confidently matched.

## Safety / Failure Modes
- If all options are unmatched, return no candidates and explain that no supplied option matched saved Taste records.
- If category is unclear, keep matches tentative.

## Verification Notes
- Option evaluation tests must prove unrelated saved high-scoring records are not substituted.
- The response must expose unmatched options.
