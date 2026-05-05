# Slack Memory Agent Plan

## Goal

Add a dedicated Slack-based agent whose only product job is adding to and retrieving from Brain memory. It must be separate from the MCP endpoint and must be stricter than the MCP interface: ingestion should be guarded by an LLM policy layer that asks clarifying questions, refuses low-quality memories, and calls out likely incorrect or contradictory memories before anything is written.

## Core Decisions

- Run the Slack bridge as its own service, not as MCP.
- Keep the MCP endpoint at `/mcp` unchanged.
- Add Slack-specific HTTP routes such as `/slack/events`, `/slack/interactions`, and `/slack/healthz`.
- Use Brain service/store internals directly or through a small internal Brain client, not MCP tool calls.
- Put the Slack agent's behavior rules in a versioned rule/context file loaded at runtime.
- Expose low-level storage inspection only as bounded, read-only, admin-only Slack agent tools.
- Do not expose arbitrary SQL, Cognee primitives, or row-level write tools to Slack.

## Proposed Runtime Shape

```text
Slack
  -> Cloudflare route /slack/events or /slack/interactions
  -> memory_stack.slack_agent_server
  -> memory_stack.slack_memory_agent
  -> LLM guard/proposal layer using config/slack_memory_agent_rules.md
  -> memory_stack.brain_service
  -> Brain DB
  -> Cognee projection queue
```

This keeps Slack separate from MCP at the transport and tool-selection levels while reusing Brain's high-level domain operations.

## Files To Add

- `src/memory_stack/slack_agent_server.py`
  FastAPI app or router for Slack Events API, slash commands, interactions, health, and signature verification.

- `src/memory_stack/slack_memory_agent.py`
  Core agent orchestration: parse intent, retrieve context, call the LLM guard layer, decide whether to ask, complain, dry-run, write, recall, or inspect.

- `src/memory_stack/slack_guardrails.py`
  Deterministic validation around LLM proposals: schema validation, confidence thresholds, contradiction flags, PII/secret rejection, confirmation rules, and admin checks.

- `config/slack_memory_agent_rules.md`
  The high-bias rule/context file. This should be treated as part of the product contract, not a loose prompt.

- `tests/test_slack_memory_agent.py`
  Unit tests for guardrail behavior and memory/retrieval flows using fake LLM responses.

- `tests/test_slack_agent_server.py`
  Route, auth, Slack signature, and admin debug endpoint tests.

## Configuration

Add settings:

- `BRAIN_SLACK_AGENT_ENABLED=false`
- `BRAIN_SLACK_AGENT_HOST=127.0.0.1`
- `BRAIN_SLACK_AGENT_PORT=8003`
- `BRAIN_SLACK_SIGNING_SECRET=`
- `BRAIN_SLACK_BOT_TOKEN=`
- `BRAIN_SLACK_ALLOWED_TEAM_IDS=`
- `BRAIN_SLACK_ALLOWED_CHANNEL_IDS=`
- `BRAIN_SLACK_ALLOWED_USER_IDS=`
- `BRAIN_SLACK_ADMIN_USER_IDS=`
- `BRAIN_SLACK_RULES_PATH=./config/slack_memory_agent_rules.md`
- `BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE=false`

Production should run this under a separate launchd label, for example `com.brain.slack-agent`, with separate logs.

## Slack User Surface

Supported interactions:

- `/brain remember <text>`
- `/brain recall <query>`
- `/brain profile <entity>`
- `/brain open-loops [topic]`
- `/brain get-memory <memory_id>`
- `/brain debug ...` for admin-only read-only verification
- DM or mention with equivalent natural language

The agent should respond in thread when possible and should use ephemeral messages for clarifications, warnings, and debug output.

## Ingestion Flow

1. Verify Slack signature, timestamp, team, channel, and user allowlists.
2. Normalize the Slack event into an internal request with message text, user id, channel id, thread id, permalink, timestamp, and command source.
3. Classify intent: remember, recall, profile, open loop, correction/conflict, debug, or unsupported.
4. For `remember`, retrieve nearby Brain context before proposing a write:
   - similar memories by lexical/semantic recall
   - known entity profile if an entity is named
   - recent conflicts or superseded memories
5. Call the LLM guard layer with:
   - `config/slack_memory_agent_rules.md`
   - user message and Slack context
   - retrieved Brain evidence
   - allowed output schema
6. Validate the LLM proposal deterministically.
7. If the proposal is ambiguous, low confidence, unsupported, sensitive, or contradictory, ask a question or complain with the reason.
8. If the proposal is acceptable, run `brain.remember` logic in dry-run mode first.
9. Commit only when either:
   - the command is explicit and passes high-confidence rules with no conflicts, and auto-commit is enabled
   - or the user confirms the proposed memory
10. Return a concise receipt with memory ids, entity ids, conflict status, and verification hints.

## Guardrail Philosophy

The Slack agent should be conservative. It should prefer asking a pointed question over storing a weak memory.

Rules for writes:

- Store durable user-level memory, not transient Slack chatter.
- Do not store secrets, credentials, tokens, or private authentication details.
- Do not convert guesses into facts.
- Do not store third-party claims as facts about the user unless attribution is clear.
- Preserve uncertainty explicitly.
- Require a clear subject. Pronouns like "he", "she", "they", "it", and "that" require resolvable context.
- Require correction semantics for overwrites: "replace", "actually", "supersedes", or an explicit confirmation.
- Treat contradictions as blockers until resolved.
- Never silently overwrite an existing memory.
- For sensitive or personal facts, ask for confirmation even if the command is explicit.
- For Slack-originated memories, store Slack provenance in metadata, not as part of the statement.

The agent should complain when useful, for example:

- "That conflicts with an existing memory: Nur and Sara are Daniele's twin daughters. Do you want to supersede it or keep both?"
- "I cannot store this as written because the subject is unclear. Who does 'he' refer to?"
- "This looks like a temporary task, not a durable memory. Should I make it an open loop instead?"
- "This contains a token/password-shaped string, so I will not store it."

## Rule File Contract

`config/slack_memory_agent_rules.md` should define:

- Mission and non-goals
- Allowed memory kinds
- Required fields for a memory proposal
- Refusal criteria
- Clarification criteria
- Conflict behavior
- Slack provenance handling
- Tone rules for asking and complaining
- Output schema

The LLM should return structured JSON only, for example:

```json
{
  "decision": "ask|complain|dry_run|commit|recall|profile|debug|unsupported",
  "reason": "short explanation",
  "user_message": "Slack-ready response text",
  "proposed_memory": {
    "input": "durable memory statement",
    "input_type": "auto|fact|note|person_interaction|open_question|research_question|chat_conclusion|table",
    "source_policy": "memory_only|source_and_memory",
    "confidence": "low|medium|high",
    "entities": ["optional names"]
  },
  "questions": [],
  "conflicts": [],
  "requires_confirmation": true
}
```

The deterministic layer should reject malformed or policy-violating JSON even if the LLM says it is safe.

## Retrieval Flow

Recall/profile/open-loop requests should not require the write guard path, but they should still:

- verify Slack auth and allowlists
- avoid leaking debug/raw storage to non-admin users
- include memory ids in responses
- distinguish facts from inferences
- include concise evidence when useful

## Low-Level Testing And Verification Tools

The Slack agent can expose admin-only read-only tools:

- `debug.snapshot`
  Return table counts and recent ids for Brain tables.

- `debug.raw_record`
  Fetch one allowlisted table row by id.

- `debug.search_rows`
  Search allowlisted text-bearing columns with a hard result limit.

- `debug.ingestion_run`
  Show an ingestion run, created memories, source id, and Cognee sync state.

- `debug.cognee_sync`
  Show projection status for a memory/source/object id.

Constraints:

- Admin-only by Slack user id.
- No arbitrary SQL.
- No write operations.
- Hard limits on row counts and text lengths.
- Redact source raw text by default.
- Include request ids/log correlation ids for verification.

## Production Deployment

Add a separate service:

- launchd label: `com.brain.slack-agent`
- local port: `8003`
- public route: `https://brain.dceb.net/slack/events` and `/slack/interactions`
- same production root and shared data model as Brain
- separate stdout/stderr logs
- separate verifier script for Slack route health and signature failure behavior

Cloudflare should route Slack paths to the Slack agent port, not to the MCP service. `/mcp` should continue to route only to the MCP service.

## Test Plan

Unit tests:

- explicit remember produces a proposal and dry-run
- ambiguous pronoun asks a clarification question and writes nothing
- contradiction complains and writes nothing
- secret/token-shaped content is refused
- open-loop phrasing maps to open-loop memory
- correction request requires confirmation
- fake LLM malformed JSON is rejected
- fake LLM tries to bypass rules and deterministic guard rejects it

Server tests:

- invalid Slack signature returns unauthorized
- stale Slack timestamp returns unauthorized
- non-allowlisted user/channel is rejected
- MCP `/mcp` tests remain unchanged
- Slack routes are not available through MCP
- admin debug works for admin user
- admin debug is rejected for non-admin user

Integration-style tests:

- Slack remember -> confirmation -> Brain memory exists
- Slack recall -> returns expected memory id and evidence
- Slack debug ingestion run -> shows created memory and source ids

## Implementation Phases

1. Add rule file and structured guardrail contracts.
2. Add Slack agent orchestration with fake-LLM test support.
3. Add Slack server routes, signature verification, and configuration.
4. Add bounded read-only debug inspectors.
5. Add launchd/deploy/env documentation.
6. Add production verifier for Slack route separation and auth failure behavior.

## Open Questions

- Should high-confidence explicit `/brain remember` ever auto-commit, or should Slack always require confirmation?
- Should the public Slack endpoint live under `brain.dceb.net/slack/*` or a dedicated hostname?
- Should debug output include redacted raw source text, or only ids/counts by default?
- Should Slack writes always create a source record with Slack permalink provenance?
