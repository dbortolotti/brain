# Brain User Guide

Brain is a personal memory system. Use it to save durable facts, decisions,
preferences, open questions, useful source material, and reminders of things you
want to recall later.

Most users should interact with Brain through Slack or through an LLM client
that has Brain tools enabled. You do not need to think in database terms while
using it: write clear memory requests, confirm them when asked, and use recall
when you need the saved context back.

## Main Workflows

Use Brain for four day-to-day jobs:

- Save a memory: "remember this..."
- Save source material: "ingest this note/article/transcript..."
- Recall stored context: "what do we know about..."
- Review or correct memory: "show recent writes", "undo the last one", or
  "actually, replace the old fact with..."

Slack is the strictest interface. It dry-runs writes and asks for confirmation
by default. An LLM client can use the same Brain tools directly, usually with
more natural phrasing.

## Using Brain From Slack

The Slack app uses the `/brain` command.

Save a simple memory:

```text
/brain remember Sam from Goldman prefers morning calls.
```

Save a decision:

```text
/brain remember We decided Brain DB is the source of truth and Cognee is only a rebuildable projection.
```

Save a preference:

```text
/brain remember Maya prefers concise written briefs before meetings.
```

Save an open question:

```text
/brain remember I want to learn more about temporal knowledge graphs.
```

Save a research question:

```text
/brain remember I wonder whether LanceDB or SQLite FTS is better for local recall experiments?
```

Save a person interaction:

```text
/brain remember Alex mentioned that the vendor contract renewal is due in June.
```

Save a project state update:

```text
/brain remember Brain project state: Slack is the primary guarded memory ingestion interface; Telegram can come later.
```

Recall stored context:

```text
/brain recall What do we know about Sam from Goldman?
```

Show available commands:

```text
/brain help
```

Profile an entity:

```text
/brain profile Brain
```

List open loops:

```text
/brain open-loops Brain
```

Fetch a specific memory if you have its id:

```text
/brain get-memory mem_...
```

Review recent writes:

```text
/brain review
```

Undo the latest write:

```text
/brain undo-last
```

Confirm a proposed write:

```text
/brain confirm Sam from Goldman prefers morning calls.
```

Slack may ask for confirmation or clarification when a memory is ambiguous,
sensitive, low-confidence, or potentially conflicts with an existing memory.

## Using Brain Through An LLM

When an LLM has Brain tools available, ask it to use Brain explicitly. Good
prompts tell the LLM whether to save, recall, profile, or review.

Save one durable memory:

```text
Use Brain to remember: Sam from Goldman prefers morning calls.
```

Save a decision from conversation:

```text
Use Brain to remember this as a decision: Brain DB is the source of truth. Cognee should remain rebuildable from Brain DB.
```

Save an open loop:

```text
Use Brain to remember this as an open question: I want to learn more about graph-based memory conflict resolution.
```

Save a source and extract memories:

```text
Use Brain to ingest this meeting note and extract durable memories:

Decision: Slack stays as the primary guarded intake for Brain.
Open question: should we add Telegram later?
Context: this came from the May architecture review.
```

Recall context:

```text
Use Brain to recall what we know about the Slack memory agent.
```

Build an entity profile:

```text
Use Brain to profile Daniele.
```

Review recent changes before trusting a result:

```text
Use Brain to review the recent memory writes and tell me if anything looks wrong.
```

Correct an older memory:

```text
Use Brain to remember this correction: Actually, Sam from Goldman now prefers afternoon calls, replacing the older morning-calls preference.
```

For important writes, ask the LLM to dry-run first:

```text
Use Brain to dry-run this memory before committing it: Maya prefers written briefs before vendor calls.
```

## What To Save

Good Brain memories are durable, specific, and useful later.

Save:

- Stable preferences: "Maya prefers written briefs."
- People facts: "Sam works at Goldman."
- Family or personal context you are allowed to remember.
- Decisions: "Use Brain DB as the source of truth."
- Project state: "Slack is the primary guarded intake."
- Commitments: "I promised to send Alex the draft on Friday."
- Open questions: "I want to learn more about temporal retrieval."
- Research questions: "I wonder whether vector search improves this recall path?"
- Source summaries, meeting notes, transcripts, articles, and small tables.
- Corrections that clearly replace older facts.

Do not save:

- Passwords, API keys, tokens, or private credentials.
- Vague notes with no subject: "remember this is important."
- Temporary chatter: "that was funny."
- Guesses as facts: "Maybe Sam likes Bill Evans."
- Sensitive personal facts unless there is a clear reason and permission.
- Full raw dumps when only a concise memory is needed.

## Supported Memory Types

Brain stores memory cards with these kinds:

| Memory kind | Use it for | Example |
| --- | --- | --- |
| `basic_fact` | General durable facts | "Brain runs locally on the production Mac." |
| `family_fact` | Family relationships or family context | "Tom and Anna are twins." |
| `person_fact` | Facts about a person | "Sam works at Goldman." |
| `person_interaction` | Something someone said or did | "Alex mentioned the renewal is due in June." |
| `preference` | Likes, dislikes, working style, defaults | "Maya prefers written briefs." |
| `decision` | Explicit decisions | "We decided to keep Slack as the primary intake." |
| `idea` | Ideas or possible future directions | "Try a weekly open-loop review." |
| `open_question` | Things to learn, revisit, or track | "I want to learn more about temporal knowledge graphs." |
| `research_question` | Investigative questions | "Does LanceDB improve local recall quality?" |
| `article_note` | Saved articles or URLs | "Saved article about SQLite vector search." |
| `key_takeaway` | Important takeaway from a source | "Cognee can be rebuilt from Brain DB." |
| `conversation_summary` | Summary of a longer conversation | "The architecture review covered Slack, Cognee, and backups." |
| `chat_conclusion` | Conclusion reached in chat | "Brain DB should be the source of truth." |
| `experience` | Personal experience or observed lesson | "The live model smoke test caught missing credentials." |
| `place_note` | Place-specific notes | "The meeting room has unreliable video." |
| `table_note` | Small tables and tabular observations | "Stored a table of model scores." |
| `source_summary` | Summary of source material | "Stored source material from the architecture note." |
| `project_state` | Current project facts and direction | "Telegram is deferred until Slack is stable." |
| `commitment` | Promises, obligations, or intended follow-ups | "Send the launch notes to Alex by Friday." |

Slack's proposal layer accepts a smaller input set:

```text
auto
fact
note
person_interaction
open_question
research_question
chat_conclusion
table
```

Brain may then classify the final stored card as a more specific memory kind,
such as `preference`, `person_fact`, `project_state`, or `source_summary`.

## How Memories Are Stored

Every write creates an ingestion run. The ingestion run records what kind of
input Brain received, a preview of the input, status, source id if there is one,
and context such as Slack provenance.

Brain can store several related objects:

- `memory_cards`: the durable memory statement, memory kind, confidence, status,
  optional summary, source quote, and source link.
- `sources`: raw or summarized source material such as articles, transcripts,
  markdown, emails, PDFs, chat logs, and tables.
- `entities`: people, organizations, places, concepts, projects, and artifacts
  mentioned by memories.
- `relationships`: links between entities, backed by a memory as evidence.
- `open_loops`: open questions and research questions that should be revisited.
- `memory_links`: duplicate, contradiction, and supersession links between
  memory cards.
- `cognee_sync`: projection state for optional Cognee sync.

Brain DB is the source of truth. Cognee and vector data are projections that can
be rebuilt.

## Source Policy

Brain has two common ways to save information:

`memory_only`

Use this for short durable statements. Example:

```text
/brain remember Sam from Goldman prefers morning calls.
```

`source_and_memory`

Use this when the original source matters and Brain should also extract durable
memories. Example for an LLM:

```text
Use Brain to ingest this as source material and extract memories:
<meeting notes>
```

`source_only` exists for keeping source material without extracting memory cards,
but it is mainly an API/tooling option rather than a normal Slack workflow.

## Writing Good Memories

Use clear subjects.

Better:

```text
/brain remember Sam from Goldman prefers morning calls.
```

Worse:

```text
/brain remember He prefers mornings.
```

Include context when names are ambiguous.

Better:

```text
/brain remember Sam Patel from Goldman prefers morning calls.
```

Worse:

```text
/brain remember Sam prefers morning calls.
```

Use correction language when replacing old information.

Better:

```text
/brain remember Correction: Sam from Goldman now prefers afternoon calls, replacing the older morning-calls preference.
```

Worse:

```text
/brain remember Sam likes afternoon calls.
```

Separate unrelated memories.

Better:

```text
/brain remember Maya prefers written briefs.
/brain remember Maya's contract renewal is due in June.
```

Worse:

```text
/brain remember Maya prefers written briefs and the renewal is due in June and Brain should use Slack.
```

Preserve attribution for third-party claims.

Better:

```text
/brain remember Alex said the vendor renewal is due in June.
```

Worse:

```text
/brain remember The vendor renewal is due in June.
```

Mark uncertainty explicitly.

Better:

```text
/brain remember Low confidence: I think Sam from Goldman may prefer afternoon calls; confirm later.
```

Worse:

```text
/brain remember Sam from Goldman prefers afternoon calls.
```

Use open questions for things to revisit.

Better:

```text
/brain remember I want to learn more about model eval confidence intervals.
```

Worse:

```text
/brain recall model eval confidence intervals
```

The second example asks Brain to answer now; it does not save a future learning
goal.

## Recall Best Practices

Ask specific questions:

```text
/brain recall What decisions have we made about Slack as Brain intake?
```

Ask for entity profiles:

```text
/brain profile Cognee
```

Ask for open loops:

```text
/brain open-loops model eval
```

Ask for evidence when using an LLM:

```text
Use Brain to recall what we know about Cognee projection, including evidence and conflicts.
```

If a recall answer looks wrong, review recent writes:

```text
/brain review
```

Then undo or add a correction.

## Corrections And Conflicts

Brain tries not to silently overwrite memories. Corrections should be explicit:

```text
/brain remember Correction: Brain production backups now use verified Neo4j dumps.
```

```text
/brain remember Actually, Slack writes require confirmation by default; replace any older memory saying they auto-commit.
```

When Brain detects a possible conflict, Slack may refuse to commit until you
confirm whether to keep both facts, supersede the old fact, or clarify the
subject.

## Privacy And Safety

Never ask Brain to store:

- passwords
- API keys
- access tokens
- private signing secrets
- recovery codes
- full credential files

Be careful with personal facts. Save them only when they are useful,
appropriate, and allowed. Prefer attribution when a fact came from someone else.

## Quick Examples

```text
/brain remember Priya prefers diagrams before implementation details.
/brain remember I want to learn more about OAuth protected resource metadata.
/brain remember We decided to keep Slack and MCP as separate services.
/brain remember Alex said the contract renewal is due in June.
/brain recall What do we know about Priya's working style?
/brain profile Brain
/brain open-loops OAuth
/brain help
```

LLM examples:

```text
Use Brain to remember: Priya prefers diagrams before implementation details.
```

```text
Use Brain to ingest these meeting notes as source material and extract durable memories.
```

```text
Use Brain to recall the current project state for Slack intake and include any conflicts.
```

## Related Docs

- [API Setup](API_SETUP_GUIDE.md) explains how to connect HTTP and MCP clients.
- [Slack Setup](SLACK_SETUP.md) explains how to configure the Slack app.
- [Backup Scheme](BACKUP_SCHEME.md) explains how Brain production backups work.
- [Production Secrets](production-secrets.md) explains production secret
  handling.
