# Purpose

- Own durable Brain documentation, generated documentation facts, diagrams, submission assets, and source manifests.

## Ownership

- User-facing docs include `USER_GUIDE.md`, `API_SETUP_GUIDE.md`, `AGENT_TOOL_GUIDE.md`, and `SLACK_SETUP.md`.
- Operator docs include `production-secrets.md`, `BACKUP_SCHEME.md`, architecture contracts, and cutover plans.
- `sources/llm_docs.yaml` owns the managed-doc source manifest.
- `generated/` owns tracked generated facts, hashes, and release metadata.
- `assets/` and `openai-submission-assets/` own diagrams, screenshots, videos, and submission copy.

## Local Contracts

- Managed docs listed in `sources/llm_docs.yaml` must remain consistent with their declared sources.
- Do not publish real secrets, credentials, private tokens, provider auth state, raw request logs, or private datasets.
- Generated facts and hashes are tracked outputs; update them through the documented scripts, not by hand.
- HTML exports and diagrams must correspond to their source markdown or Mermaid files.

## Work Guidance

- Use `make docs-generate` to refresh `docs/generated/facts.json` and `docs/generated/facts.sha256`.
- Use `make docs-hash` or `make docs-llm` for managed LLM docs when source hashes change.
- Keep submission assets inspectable and tied to the current app surface.

## Verification

- Run `make docs-check` after documentation or source-manifest changes.
- For screenshot or generated asset changes, manually inspect the artifact when visual correctness matters.

## Child DOX Index

- No child AGENTS.md files. Documentation subdirectories are owned here.
