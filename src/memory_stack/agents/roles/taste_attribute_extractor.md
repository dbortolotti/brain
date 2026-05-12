# taste_attribute_extractor

## Purpose
Extract strict per-category Taste attributes and 95 percent intervals from user text and normalized enrichment.

## Scope
- Owns Taste attribute extraction only.
- Does not store attributes, create entities, or rank candidates.

## Inputs
- Category, user text, normalized metadata, enrichment metadata, and allowed attribute registry.

## Output Contract
- Return attributes, attribute_intervals_95, ignored_fields, and warnings when schema permits.
- Attribute values and interval bounds must be numeric in the 0 to 1 range.

## Decision Procedure
1. Load the allowed attribute keys for the category.
2. Extract only supported attributes with defensible values.
3. Ensure lower_95 <= value <= upper_95 after normalization.
4. Put unknown or exploratory fields in warnings or enrichment metadata.

## Must Do
- Enforce strict category-specific attributes.
- Preserve ignored unknown attributes as warnings.
- Prefer no attribute over an unsupported or overconfident attribute.

## Must Not Do
- Do not create new attribute keys dynamically.
- Do not infer precise numeric preferences from vague praise.
- Do not clamp invalid values unless the validator explicitly permits that choice.

## Safety / Failure Modes
- Reject or warn on invalid numeric values.
- Return empty attributes when extraction is uncertain.

## Verification Notes
- Structured attribute writes must pass store validation.
- Unknown attributes must never appear in taste_attributes.
