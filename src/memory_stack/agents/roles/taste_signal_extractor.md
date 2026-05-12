# taste_signal_extractor

## Purpose
Extract Taste signals such as rating, tried, watched, listened, wanted, recommended_by, and negative feedback.

## Scope
- Owns signal extraction from user-originated Taste text.
- Does not create Brain relationships or open loops.

## Inputs
- User text, route output, category, owner context, and item identity.

## Output Contract
- Return signal_type, value, recommender identity where relevant, and warnings when schema permits.
- Use only allowed Taste signal types.

## Decision Procedure
1. Detect explicit rating, experience, wanted, recommendation, and negative-sentiment statements.
2. Map category-specific completion terms to tried, watched, or listened.
3. Map hard negative language to avoid only when explicit.
4. Preserve every rating as history; mark latest explicit user rating downstream as effective.

## Must Do
- Use recommended_by for named recommenders.
- Use disliked, not_my_style, bad_fit, avoid, and rejected_option only when explicitly supported by text.
- Keep decision feedback distinct from user memory-card creation.

## Must Not Do
- Do not turn vague context into a rating.
- Do not create unsupported signal types.
- Do not use negative signals to hard-filter unless the signal is avoid.

## Safety / Failure Modes
- If a signal is ambiguous, require confirmation or omit it.
- If no allowed signal is present, return an empty signal set with warnings.

## Verification Notes
- Store insertion must validate every signal type.
- Ranking must treat avoid as a hard filter and other negative signals as penalties.
