# Brain User Guide

Brain is a personal memory, taste, and portable agent-memory system. Use it to save durable facts, decisions, preferences, open questions, useful source material, standing profile context, taste signals, reminders of things you want to recall later, commitments, and, when your client exposes it, chat-session continuity through a dedicated agent-memory workflow.

Most users should interact with Brain through Slack, through an LLM client that has Brain tools enabled, or through the browser user dashboard. You do not need to think in database terms while using it: write clear memory requests, confirm them when asked, and use recall or review when you need the saved context back.

Palate is Brain's taste layer. Use it for wine, restaurants, media, music, cigars, experiences, and other taste-related preferences.

If your client exposes `brain_agent_memory`, use that workflow for portable chat continuity and keep it separate from ordinary durable memory writes.

## Main Workflows

Use Brain and Palate for these day-to-day jobs:

- Save a memory: `remember this...`
- Save source material: `ingest this note/article/transcript...`
- Recall stored context: `what do we know about...`
- Review or correct memory: `show recent writes`, `undo the last one`, or `actually, replace the old fact with...`
- Save or rank taste-related preferences with Palate.
- Preserve chat handovers with `brain_session` and your client's dedicated agent-memory workflow when it is available. If your client exposes `brain_agent_memory`, use that workflow for portable chat continuity and keep it separate from ordinary durable memory writes.

Slack is the strictest interface. It may ask for confirmation or clarification when a memory is ambiguous, sensitive, low-confidence, or potentially conflicts with an existing memory.

## Using Brain From Slack

The Slack app uses the `/brain` command. It is a separate guarded surface and may ask for confirmation or clarification when a memory is ambiguous, sensitive, low-confidence, or potentially conflicts with an existing memory.

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
/brain remember Brain project state: Slack is the primary guarded memory ingestion interface; Telegram is deferred until Slack is stable.
```

Recall stored context:

```text
/brain recall What do we know about Sam from Goldman?
```

Show available commands:

```text
/brain help
```

Help includes buttons for common command templates. Slack does not allow Brain to insert text directly into your message box from those buttons, so pressing one shows a copyable command template.

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

Brain may then classify the final stored card as a more specific memory kind, such as `preference`, `person_fact`, `project_state`, or `source_summary`.
For chat-session continuity and handovers, prefer the dedicated `brain_agent_memory` workflow over `conversation_summary` or `chat_conclusion` when your client exposes that workflow.

## Using the User Dashboard

The browser dashboard is for reviewing and managing your memory. It opens with a sign-in overlay and a session line that says Connect to review memory.

The dashboard is available at `/` and `/user`. The app dashboard is also available at `/app`. The top bar links to User, Admin, and Cognee views.

Main tabs:

- Review: Recent Cards, Open Loops, and Memory Contents. Click a memory card to inspect it.
- Recall: search Brain with a query and an optional limit.
- Remember: preview a memory before saving it. The input type menu includes auto, fact, note, thought, open question, and chat conclusion.
- Profile: add standing answer-tailoring context. The default scope is `answer_tailoring`.
- Prompt: inspect Personal Info In Session, Custom Preprompt Instructions, Latest Session Data, Bias Protocol, and Agent Memory Protocol.
- Data Controls: view App Write Audit, Export Preview, Profile Data, and Recent Memory Data.
- Account: change your password.
- Users: available to superusers for user administration.
- Help: command and usage help.

The dashboard ships with the main app page plus privacy, support, and terms pages.

Use Review before trusting a recall result. It is a safe place to inspect recent memory and open loops without changing data.

## HTTP and Browser Surfaces

Brain also exposes browser pages, auth flows, HTTP endpoints, and MCP surfaces directly.

Useful browser pages:

- `/` and `/user` — memory dashboard
- `/app` — app dashboard
- `/admin` — admin dashboard
- `/admin/users` and `/admin/users/{user_id}` — user administration for superusers
- `/cognee` — user Cognee UI
- `/cognee-login` and `/cognee-logout` — Cognee UI sign-in and sign-out
- `/cognee-api/{path:path}` — Cognee API proxy routes
- `/ui`, `/ui-login`, `/ui-logout`, and `/ui-api/{path:path}` — UI proxy routes
- `/admin/cognee`, `/admin/cognee-api/{path:path}`, and `/admin/cognee/{path:path}` — admin Cognee proxy routes
- `/privacy`, `/support`, `/terms`
- `/app-assets/{asset_name}` and `/app/oauth/callback`
- `/docs/oauth2-redirect`

Useful auth and session endpoints:

- `/.well-known/oauth-authorization-server`
- `/.well-known/oauth-protected-resource`
- `/.well-known/oauth-protected-resource/{resource_path:path}`
- `/.well-known/openai-apps-challenge`
- `/.well-known/openid-configuration`
- `/authorize`
- `/login`
- `/logout`
- `/register`
- `/revoke`
- `/token`
- `/account/password`
- `/api/session`
- `/auth/session`

Useful memory endpoints:

- `/memory/remember`
- `/memory/ingest_source`
- `/memory/recall`
- `/memory/profile_entity`
- `/memory/open_loops`
- `/memory/{memory_id}`
- `/memory/review_recent`
- `/memory/undo_last`
- `/memory/forget`
- `/memory/resolve_conflict`
- `/memory/sync_cognee`
- `/memory/rebuild_cognee`
- `/memory/merge_entities`

Datasource endpoints also exist:

- `/datasources`
- `/create_datasource`
- `/delete_datasource`
- `/list_datasources`
- `/datasources/{datasource}`
- `/delete_datasource/{datasource}`

Slack agent endpoints include:

- `/slack/healthz`
- `/slack/events`
- `/slack/commands`
- `/slack/interactions`

Other common endpoints include `/healthz`, `/docs`, `/redoc`, `/openapi.json`, `/favicon.ico`, `/icon.png`, and `/apple-touch-icon.png`.

MCP surfaces for clients include `/mcp`, `/admin/mcp`, and the legacy curated alias `/app/mcp`. The MCP catch-all route is `/{path:path}`.

## Using Brain Through An LLM

When an LLM has Brain tools available, ask it to use Brain explicitly. Good prompts tell the LLM whether to save, recall, profile, review, or use Palate.

The ChatGPT app surface exposes a smaller subset of tools and does not expose `brain_agent_memory`, `brain_agent_memory_recall`, or `brain_agent_memory_clear`. It does expose `brain_session`, `brain_remember`, `brain_profile_context_remember`, `brain_profile_context_list`, `brain_profile_context_forget`, `brain_app_data_controls`, `brain_ingest_source`, `brain_recall`, `brain_profile_entity`, `brain_list_open_loops`, `brain_get_memory`, `brain_review_recent`, `brain_undo_last`, `brain_palate_describe_item`, `brain_palate_query`, `brain_palate_evaluate_options`, `brain_palate_confirm`, `brain_palate_cancel`, and `brain_palate_correct_proposal`.

Internal or admin surfaces also expose tools such as `brain_app_open_review_panel`, `brain_profile_context_sync`, `brain_get_source`, `brain_resolve_conflict`, `brain_forget`, `brain_merge_entities`, `brain_sync_cognee`, `brain_rebuild_cognee`, `brain_agent_memory`, `brain_agent_memory_recall`, `brain_agent_memory_clear`, `brain_palate_remember`, `brain_palate_log_decision`, `brain_palate_refresh_enrichment`, and `cognee_improve`.

`brain_session` can resolve the active user's Brain profile and standing context. On internal or admin surfaces it also returns the user-scoped `session_id` for portable agent-memory calls; the ChatGPT app surface hides session ids.

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

Preserve chat/session context for handover:

```text
Use brain_session to get my user-scoped session id. If my client exposes an agent-memory workflow, use it to preserve this chat handover. Do not use brain_remember unless there is a separate durable user fact or decision.
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

Load profile context before answering:

```text
Load my preferences from Brain before answering.
```

## Using Palate

Palate is Brain's taste layer. It normalizes messy user input into structured items, enriches those items, stores taste signals, and ranks recommendations.

The ChatGPT app surface exposes `brain_palate_describe_item`, `brain_palate_query`, `brain_palate_evaluate_options`, `brain_palate_confirm`, `brain_palate_cancel`, and `brain_palate_correct_proposal`. Internal or admin surfaces also expose `brain_palate_remember`, `brain_palate_log_decision`, and `brain_palate_refresh_enrichment`.

Palate is best for:

- Wine: producers, vintages, regions, grapes, style, oak, body, acidity, drinking windows, and personal signals.
- Restaurants: cuisine, city, price, occasion, atmosphere, service, and personal fit.
- Media: films, series, books, music, podcasts, and watch/listen/read signals.
- Cigars and experiences: structured preferences, dislikes, and contexts.

Describe an item without storing it:

```text
Use brain_palate_describe_item to describe Chateau Musar 2016 as a wine. Do not store it yet.
```

Remember a wine:

```text
Use Brain Palate to remember:
I want to try Chateau Musar 2016. Sam recommended it. Treat it as a wine.
Notes: likely savory, mature, complex Lebanese red. I am curious but have not tried it.
```

Remember a restaurant:

```text
Use Brain Palate to remember:
Noble Rot is a restaurant I like for wine-led dinners in London. I like the wine list, classic food, and relaxed but serious atmosphere.
```

## What To Save

Good Brain memories are durable, specific, and useful later.

Save:

- Stable preferences: `Maya prefers written briefs.`
- People facts: `Sam works at Goldman.`
- Family or personal context you are allowed to remember.
- Decisions: `Use Brain DB as the source of truth.`
- Project state: `Slack is the primary guarded intake.`
- Commitments: `I promised to send Alex the draft on Friday.`
- Open questions: `I want to learn more about temporal retrieval.`
- Research questions: `I wonder whether vector search improves this recall path?`
- Source summaries, meeting notes, transcripts, articles, and small tables.
- Corrections that clearly replace older facts.
- Taste preferences and ranking signals when the information belongs in Palate.

Do not save:

- Passwords, API keys, tokens, or private credentials.
- Vague notes with no subject: `remember this is important.`
- Temporary chatter: `that was funny.`
- Guesses as facts: `Maybe Sam likes Bill Evans.`
- Sensitive personal facts unless there is a clear reason and permission.
- Chat-session handovers, conversation summaries, or agent workflow learnings; use the dedicated agent-memory workflow in clients that expose it, and keep those handovers separate from ordinary durable facts.
- Full raw dumps when only a concise memory is needed.

## Supported Memory Types

Brain stores memory cards with these kinds:

| Memory kind | Use it for | Example |
| --- | --- | --- |
| `basic_fact` | General durable facts | `Brain runs locally on the production Mac.` |
| `family_fact` | Family relationships or family context | `Tom and Anna are twins.` |
| `person_fact` | Facts about a person | `Sam works at Goldman.` |
| `person_interaction` | Something someone said or did | `Alex mentioned the renewal is due in June.` |
| `preference` | Likes, dislikes, working style, defaults | `Maya prefers written briefs.` |
| `decision` | Explicit decisions | `We decided to keep Slack as the primary intake.` |
| `idea` | Ideas or possible future directions | `Try a weekly open-loop review.` |
| `open_question` | Things to learn, revisit, or track | `I want to learn more about temporal knowledge graphs.` |
| `research_question` | Investigative questions | `Does LanceDB improve local recall quality?` |
| `article_note` | Saved articles or URLs | `Saved article about SQLite vector search.` |
| `key_takeaway` | Important takeaway from a source | `Cognee can be rebuilt from Brain DB.` |
| `conversation_summary` | Summary of a longer conversation | `The architecture review covered Slack, Cognee, and backups.` |
| `chat_conclusion` | Conclusion reached in chat | `Brain DB should be the source of truth.` |
| `experience` | Personal experience or observed lesson | `The live model smoke test caught missing credentials.` |
| `place_note` | Place-specific notes | `The meeting room has unreliable video.` |
| `table_note` | Small tables and tabular observations | `Stored a table of model scores.` |
| `source_summary` | Summary of source material | `Stored source material from the architecture note.` |
| `project_state` | Current project facts and direction | `Telegram is deferred until Slack is stable.` |
| `commitment` | Promises, obligations, or intended follow-ups | `Send the launch notes to Alex by Friday.` |

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

Brain may then classify the final stored card as a more specific memory kind, such as `preference`, `person_fact`, `project_state`, or `source_summary`.
For chat-session continuity and handovers, prefer the dedicated `brain_agent_memory` workflow over `conversation_summary` or `chat_conclusion` when your client exposes that workflow.

## How Memories Are Stored

Every write creates an ingestion run. The ingestion run records what kind of input Brain received, a preview of the input, status, source id if there is one, and context such as Slack provenance.

Brain can store several related objects:

- `memory_cards`: the durable memory statement, memory kind, confidence, status, optional summary, source quote, and source link.
- `sources`: raw or summarized source material such as articles, transcripts, markdown, emails, PDFs, chat logs, and tables.
- `entities`: people, organizations, places, concepts, projects, and artifacts mentioned by memories.
- `relationships`: links between entities, backed by a memory as evidence.
- `open_loops`: open questions and research questions that should be revisited.
- `memory_links`: duplicate, contradiction, and supersession links between memory cards.
- `cognee_sync`: projection state for optional Cognee sync.

Brain DB is the source of truth. Cognee and vector data are projections that can be rebuilt.

## Source Policy

Brain has two common ways to save information:

- Use `/memory/remember` for short durable statements.
- Use `/memory/ingest_source` when the original source matters and Brain should also extract durable memories.

When you are using Slack or an LLM client, choose the simplest write that matches the goal: a direct memory for one durable fact, or source ingestion when you want the source material preserved too.

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

The second example asks Brain to answer now; it does not save a future learning goal.

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

If a recall answer looks wrong, review recent writes in Slack or in the browser Review tab before trusting the result:

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

When Brain detects a possible conflict, Slack may refuse to commit until you confirm whether to keep both facts, supersede the old fact, or clarify the subject.

If you need to remove or revert data, prefer the safest available action:

- `undo-last` reverts the latest ingestion run.
- `forget` is available on internal/admin surfaces for soft-delete, and with confirmation can hard-delete a Brain object.
- `resolve_conflict` is for choosing how to handle contradictions or duplicates between memories.

## Privacy And Safety

Never ask Brain to store:

- passwords
- API keys
- access tokens
- private signing secrets
- recovery codes
- full credential files

Be careful with personal facts. Save them only when they are useful, appropriate, and allowed. Prefer attribution when a fact came from someone else.

Do not use ordinary memory writes as a substitute for backup or release workflows. Production backups and production promotion are operator tasks handled separately from normal user memory editing.

## Safe Review And Recovery

Use Review before trusting a recall result.

For safe review:

- inspect Recent Cards and Open Loops first
- click a memory card to inspect its contents and evidence
- use `brain_get_memory` when you already have a memory id
- use `brain_review_recent` before assuming a recall output is correct
- use `undo-last` for the latest write when you need to reverse a mistake
- use the browser Review tab when you want to inspect data without changing it

For destructive operations, be careful:

- `brain_forget` and `delete`-style actions are not the same as a normal correction
- `brain_undo_last` only targets the latest ingestion run
- deletion, conflict resolution, and rebuild workflows should be used deliberately and only when you understand the effect on stored memory and projections

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

```text
Use Brain Palate to remember:
I want to try Chateau Musar 2016. Sam recommended it. Treat it as a wine.
```

```text
Use Brain Palate to suggest an oaky wine I said I want to try. Explain the ranking.
```

```text
Use brain_palate_describe_item to describe Chateau Musar 2016 as a wine. Do not store it yet.
```

## Related Docs

- [API Setup](API_SETUP_GUIDE.md) explains how to connect HTTP and MCP clients.
- [Slack Setup](SLACK_SETUP.md) explains how to configure the Slack app.
- [Backup Scheme](BACKUP_SCHEME.md) explains how Brain production backups work.
- [Production Secrets](production-secrets.md) explains production secret handling.

<!-- brain-doc-source-hash: 78795afc8e1df9a31817640467c194c8b088ac1fafa20965c2c9f6cd359c05ef -->
