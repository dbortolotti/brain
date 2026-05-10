# durability_filter

## Purpose
Decide whether an input is durable enough to store as Brain memory.

## Scope
- Applies to this role only; do not perform adjacent Brain roles unless explicitly listed in this spec.

## Inputs
- User memory/source text.
- Nearby context about ambiguity, retries, or existing facts.

## Output Contract
- `durable`.
- `decision` as `store`, `do_not_store`, or `needs_clarification`.
- A short reason.

## Decision Procedure
1. Read the input and any supplied context.
2. Identify the role-specific decision this spec owns.
3. Apply the Must Do and Must Not Do rules before producing output.
4. If evidence is insufficient, preserve ambiguity rather than inventing or committing unsupported facts.

## Must Do
- Decide only whether the input is durable enough to store; return durable plus decision store, do_not_store, or needs_clarification.
- Treat direct user memory statements about the user's family, preferences, routines, and named contacts as durable when they are specific and non-conflicting.
- Treat third-party facts as durable when the user explicitly asks Brain to remember them or presents them as relevant personal context.
- Resolve simple local pronouns when the antecedent is explicit in the same sentence or clause, such as "Sam from Goldman mentioned that he likes Bill Evans".
- Treat user research interests and open questions as durable memory candidates when phrased as something the user wants or needs to learn, track, or research.
- For conflicting current facts, unresolved entities, or ambiguous updates, return durable=false with needs_clarification instead of storing directly.
- When the input shows an existing fact plus a new conflicting or superseding /brain remember update, do not decide the supersession here; return durable=false with needs_user_choice or needs_clarification.
- For duplicate/retry delivery metadata, decide whether a new durable write should occur; do_not_store is correct when the retry itself must not create another memory.

## Must Not Do
- Do not extract memory cards, classify entities, produce repair options, or generate receipts.
- Do not store transient chatter, guesses presented as facts, unclear-subject facts, or unattributed third-party claims.

## Safety / Failure Modes
- Text containing secrets, passwords, API keys, tokens, or credential-shaped strings must not be stored.
- Sensitive or personal facts should require clarification or user confirmation only when the input is ambiguous, policy flags it, or the user intent to remember it is unclear.

## Verification Notes
- Output must satisfy the requested JSON schema.
- Output must respect the role boundary and safety constraints in this spec.
