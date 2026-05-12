# taste_ranker

## Purpose
Rank Taste candidates using structured attributes, signals, uncertainty, decision feedback, and Brain graph context.

## Scope
- Owns Taste recommendation scoring.
- Does not retrieve unrelated options or create new records.

## Inputs
- Candidate Taste records, query intent, supplied option matches, decision feedback, signals, attributes, intervals, and graph evidence.

## Output Contract
- Return ranked candidates, scores, hard filters, score components, evidence IDs, and warnings when schema permits.

## Decision Procedure
1. Exclude avoided items unless the user explicitly asks to include them.
2. Apply latest explicit rating, structured attributes, interval uncertainty, wanted/tried status, recommender context, and negative signals.
3. Apply decision feedback for chosen and rejected options.
4. Sort by score with documented tie breakers.

## Must Do
- Treat avoid as a hard negative filter.
- Treat disliked, not_my_style, bad_fit, and rejected_option as penalties.
- Preserve constrained option evaluation when options were supplied.

## Must Not Do
- Do not rank unknown attributes.
- Do not ignore uncertainty intervals in detailed scoring mode.
- Do not turn decision logs into Brain memory cards.

## Safety / Failure Modes
- If ranking evidence is thin, expose low confidence rather than inventing rationale.
- If no candidates remain after hard filters, report the filter reason.

## Verification Notes
- Detailed mode must expose weights, penalties, filters, intervals, and evidence IDs.
- Default user-facing explanation should remain concise.
