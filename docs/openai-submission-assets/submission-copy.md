# OpenAI Submission Copy

## App Name

Brain

## Short Description

Private memory and preference recall for authenticated ChatGPT workflows.

## Longer Description

Brain is a private personal-memory service for authenticated users. It helps
users save, review, and recall durable memories, profile context, open loops,
source notes, and Palate preferences from ChatGPT. Brain is designed around
explicit consent for writes: public app write and delete operations preview
first and require user confirmation before storage or removal.

The public ChatGPT App surface is intentionally curated for user-level memory
workflows. System administration, raw Cognee primitives, hard deletes, backup
operations, password management, token handling, and other users' data are not
available from the public app surface.

## Category

Productivity

## Support Contact

`support@dceb.net`

## Privacy Summary

Brain stores personal memory records only for authenticated users. Stored data
can include memories, profile context, open loops, source metadata, Palate
preference records, and auditable ingestion records. Records are scoped to the
authenticated user. Browser sessions use HTTP-only cookies and CSRF tokens; MCP
clients use OAuth bearer tokens. User-registry passwords are stored as Argon2id
hashes.

Brain may use configured model, embedding, search, and place-enrichment
providers to classify, retrieve, summarize, or enrich records. Users should not
store passwords, API keys, OAuth tokens, or other secrets in Brain memories.
Records are retained until the authenticated user or operator removes them, or
until an environment backup/retention policy expires.

## Safety Summary

- Unauthenticated MCP requests fail closed with OAuth metadata.
- The public app surface exposes only curated user-memory tools.
- Write and destructive user-level actions require explicit confirmation.
- The app surface redacts internal user ids, session ids, OAuth client ids,
  request ids, datasets, timestamps, tokens, raw metadata JSON, and password
  fields.
- Admin and system operations are available only to authenticated superusers in
  the browser dashboard or internal admin MCP surface.

## Reviewer Test Prompts

```text
Open my Brain review panel.
```

```text
Remember that the verifier prefers concise release notes.
```

```text
Confirm saving that Brain memory.
```

```text
Show my recent Brain memories.
```

```text
Remove the profile context you just added.
```

## Reviewer Notes

Use the dedicated non-admin reviewer account `brain_verifier`. The password is
stored outside the repository at:

```text
/Volumes/xpg_usb4/prod/brain/shared/secrets/brain-auth-verifier-password
```

Paste the password into the OpenAI submission portal only; do not commit it to
the repository.
