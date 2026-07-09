# Brain Agent Tool Guide

Brain is a personal memory, taste, and portable chat-continuity system for agents.

Most users should interact with Brain through Slack, through an LLM client that has Brain tools enabled, or through the browser user dashboard.

Use Brain when you want an agent to remember durable facts, decisions, preferences, project state, open loops, research questions, source material, standing profile context, palate or taste signals, or chat-session continuity. Use Cognee-backed chat continuity when you want continuity between agent chats and a dedicated portable session memory. Use Palate when the memory is about taste: wine, restaurants, media, music, cigars, experiences, and other supported preference categories.

If your client exposes external chat-continuity workflow, use that workflow for portable chat continuity and keep it separate from ordinary durable memory writes.

The practical rule is simple:

- Brain owns memory policy, durable facts and preferences, cleanup, ranking policy, and palate decisions.
- Bias context owns response-style preferences.
- Cognee owns semantic recall and rebuildable projections.
- Palate owns taste normalization, enrichment, recommendation ranking, and feedback on taste choices.
- Agent memory is a dedicated user-scoped Cognee dataset for chat-session continuity; it is not the canonical store for everything.

## Quick Start

Ask the agent directly:

```text
Use Brain to remember: Daniele prefers short answers unless implementation detail is needed.
```

```text
Use Brain to recall what we decided about the Brain and Cognee split.
```

```text
Use Brain Palate to remember that I want to try Chateau Musar 2016 because Sam recommended it.
```

```text
Use Brain Palate to suggest an oaky wine I said I want to try. Explain the ranking.
```

```text
Load my preferences from Brain before answering.
```

```text
Call brain_session, then use Brain's chat-continuity workflow with the returned user-scoped session_id.
```

## What Brain Is Good For

Use Brain for durable information that should affect future conversations.

Good memories:

- Daniele prefers short answers unless implementation detail is needed.
- The Brain production and dev services run on the same host and must use separate ports.
- We decided Brain keeps policy and ranking logic while Cognee keeps rebuildable projections and retrieval.
- Sam recommended Chateau Musar 2016 and Daniele wants to try it.
- Standing profile context for answer tailoring, such as a stable name, background, work context, or communication need.
- Durable project facts, decisions, constraints, open questions, and research questions.

Poor memories:

- This is important.
- The user sounded happy.
- Maybe this might matter later.
- Chat-session handovers, conversation summaries, and workflow learnings; use external chat-continuity workflow for those when your surface exposes it.
- Full transcripts when one sentence would preserve the useful fact.
- Secrets, passwords, API keys, OAuth tokens, or credentials.
- Sensitive personal facts unless there is a clear reason and permission.

## Core MCP Tools

Tool availability varies by surface. The ChatGPT app surface exposes a smaller subset; the internal or admin surface exposes the full set, including source lookup, conflict resolution, deletion, Cognee maintenance, chat-continuity cleanup, merge, the full Palate toolset, and bias-context tools. The ChatGPT app surface also exposes external chat-continuity workflow and external chat-continuity recall for portable chat continuity.

Most agents should use these tools rather than lower-level storage details.

| Tool | Use it for |
| --- | --- |
| `brain_app_open_review_panel` | Open the app review panel. Internal or admin only. |
| `brain_session` | Resolve the active user's Brain profile and standing context. Internal or admin surfaces also return the user-scoped session_id for portable chat-continuity calls; the ChatGPT app surface hides session ids. |
| `brain_app_data_controls` | Inspect app data controls and related dashboard state. Available on ChatGPT app and internal or admin surfaces. |
| `brain_profile_context_remember` | Store stable user-profile context for answer tailoring. Available on ChatGPT app and internal or admin surfaces. |
| `brain_profile_context_list` | List stable user-profile context. Available on ChatGPT app and internal or admin surfaces. |
| `brain_profile_context_forget` | Remove one stable user-profile context item. Available on ChatGPT app and internal or admin surfaces. |
| `brain_bias_context_remember` | Store stable response-style preference context. Internal or admin only. |
| `brain_bias_context_list` | List response-style preference context. Internal or admin only. |
| `brain_bias_context_forget` | Remove one stable response-style preference item. Internal or admin only. |
| `brain_remember` | Store a durable memory, fact, preference, decision, open question, research question, or short note. High-confidence palate memories may route to Brain Palate automatically. Do not use this for read-only palate describe/enrich requests; use `brain_palate_describe_item` instead. |
| `brain_ingest_source` | Store longer source material and optionally extract memories. |
| `brain_recall` | Answer a memory query with evidence. |
| `brain_profile_entity` | Build a profile for a person, project, place, or other entity. |
| `brain_list_open_loops` | List open questions, reminders, and parked research threads. |
| `brain_get_memory` | Read one memory card by id. |
| `brain_get_source` | Read source metadata and optionally source text. Internal or admin only. |
| `brain_review_recent` | Review recent writes and ingestion runs. |
| `brain_undo_last` | Undo the latest ingestion receipt by calling Cognee native forget and writing audit evidence. |
| `brain_forget` | Forget a Cognee-backed memory or source via Cognee native forget. Internal or admin only. |
| `brain_resolve_conflict` | Resolve contradictions or duplicates between memories. Internal or admin only. |
| `brain_merge_entities` | Merge duplicate entities after confirmation. Internal or admin only. |
| external chat-continuity workflow | Bridge the active user's Cognee session into their dedicated chat-continuity dataset. Available on ChatGPT app and internal or admin surfaces; internal or admin can also manage cleanup. |
| external chat-continuity recall | Search the active user's dedicated chat-continuity dataset. Available on ChatGPT app and internal or admin surfaces. |
| external chat-continuity cleanup | Clear that dataset after explicit confirmation. Internal or admin only. |

Maintenance tools:

| Tool | Use it for |
| --- | --- |
| `brain_profile_context_sync` | Sync standing profile context to the configured projection. Internal or admin only. |
| `brain_sync_cognee` | Hard-deprecated after the Cognee cutover. Durable semantic writes go directly to Cognee. |
| `brain_rebuild_cognee` | Hard-deprecated after the Cognee cutover. Use Cognee-native forget/cognify maintenance instead. |
| `cognee_improve` | Run Cognee native improve on a configured dataset. Internal or admin only. |

Normal users rarely need maintenance tools. Use them when operating the system, debugging projections, or intentionally improving a Cognee dataset.

## HTTP and Dashboard Surface

Brain also exposes HTTP endpoints and browser pages. Use them when you are not talking to the MCP tools directly.

- Health and docs: `/`, `/healthz`, `/docs`, `/docs/oauth2-redirect`, `/redoc`, `/openapi.json`, `/favicon.ico`, `/icon.png`, `/apple-touch-icon.png`, `/.well-known/openai-apps-challenge`
- Auth and session: `/.well-known/oauth-authorization-server`, `/.well-known/oauth-protected-resource`, `/.well-known/oauth-protected-resource/{resource_path:path}`, `/.well-known/openid-configuration`, `/authorize`, `/login`, `/logout`, `/register`, `/revoke`, `/token`, `/account/password`, `/api/session`, `/auth/session`, `/admin/tokens`, `/admin/tokens/{token_id}`
- User administration: `/admin/users` and `/admin/users/{user_id}`
- UI pages: `/app`, `/app-assets/{asset_name}`, `/app/oauth/callback`, `/user`, `/admin`, `/privacy`, `/support`, `/terms`
- Memory endpoints: `/memory/remember`, `/memory/ingest_source`, `/memory/recall`, `/memory/profile_entity`, `/memory/open_loops`, `/memory/{memory_id}`, `/memory/review_recent`, `/memory/undo_last`, `/memory/forget`, `/memory/resolve_conflict`, `/memory/merge_entities`
- Datasource endpoints: `/datasources`, `/create_datasource`, `/delete_datasource`, `/list_datasources`, `/datasources/{datasource}`, `/delete_datasource/{datasource}`
- Cognee UI proxy routes: `/cognee`, `/cognee-api/{path:path}`, `/cognee-login`, `/cognee-logout`, `/ui`, `/ui-api/{path:path}`, `/ui-login`, `/ui-logout`, `/admin/cognee`, `/admin/cognee-api/{path:path}`, `/admin/cognee/{path:path}`
- The MCP catch-all route is `/{path:path}`

The browser dashboard ships with `index.html`, `privacy.html`, `support.html`, and `terms.html`.

The dashboard surfaces Review, Recall, Remember, Profile, Prompt, Data Controls, Account, Users, and Help. The top bar links to User, Admin, and Cognee views.

The Prompt tab includes Personal Info In Session, Custom Preprompt Instructions, Latest Session Data, Bias Protocol, and Agent Memory Protocol. The Data Controls area includes App Write Audit, Export Preview, Profile Data, and Recent Memory Data.

## Slack Surface

Brain's Slack app is a separate guarded surface and should not be treated as an MCP client. It shares the Brain service layer and uses `/brain` commands. It is the strictest interface and may ask for confirmation or clarification when a memory is ambiguous, sensitive, low-confidence, or conflicts with an existing memory.

The Slack memory agent is conservative by default and is not a general Slack assistant. It shares the core Brain service layer, but it should not expose arbitrary SQL, Cognee primitives, or row-level write tools.

Slack should use the deterministic Brain service and validation layers rather than relying on the LLM alone. The LLM can classify, propose, and repair, but policy enforcement should remain deterministic.

Slack provenance belongs in Brain request-context metadata, not in the memory statement itself. The provenance fields are team id, channel id, user id, thread timestamp, message timestamp, and permalink.

Supported command templates include:

```text
/brain remember <text>
/brain source <url_or_text>
/brain recall <query>
/brain profile <entity>
/brain open
/brain review
/brain undo-last
/brain inspect <object>
/brain debug <subcommand>
/brain admin <subcommand>
```

The Slack proposal layer accepts a limited input set:

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

Brain may still classify the final stored card more specifically.

The Slack intake layer is conservative. It returns JSON-only proposals with decision, reason, user_message, proposed_memory, questions, conflicts, and requires_confirmation. The decision value can be ask, complain, dry_run, commit, recall, profile, debug, or unsupported. Inside `proposed_memory`, the common fields are input, input_type, source_policy, confidence, and entities.

Slack memory policy:

- Allowed memory kinds are `fact`, `note`, `person_interaction`, `open_question`, `research_question`, `chat_conclusion`, and `table`.
- Refuse text that contains secrets, passwords, API keys, tokens, private authentication material, or credential-shaped strings.
- Refuse weak memories such as transient chatter, guesses presented as facts, facts with unclear subject, or third-party claims without attribution.
- Ask a concise clarification when pronouns such as `he`, `she`, `they`, `it`, or `that` cannot be resolved from nearby Brain context.
- Ask before storing sensitive or personal facts even when confidence is high.
- Treat contradictions and corrections as blockers unless the user explicitly confirms the proposed write. When the user is correcting a memory, prefer clear correction language such as `actually`, `replace`, `supersedes`, or `correction`.
- Keep the tone concise, direct, and specific. Ask one pointed question when possible, and name the exact blocker when complaining.

## Palate Tools

Palate is Brain's taste layer. It normalizes messy user input into structured items, enriches those items, stores taste signals, and ranks recommendations.

The ChatGPT app surface exposes `brain_palate_describe_item`, `brain_palate_query`, `brain_palate_evaluate_options`, `brain_palate_confirm`, `brain_palate_cancel`, and `brain_palate_correct_proposal`. The internal or admin surface additionally exposes `brain_palate_remember`, `brain_palate_log_decision`, and `brain_palate_refresh_enrichment`.

| Tool | Use it for |
| --- | --- |
| `brain_palate_describe_item` | Normalize and enrich an item without storing it. |
| `brain_palate_remember` | Store an approved palate item and its signals. Internal or admin only. |
| `brain_palate_query` | Rank stored palate records for a recommendation query. |
| `brain_palate_evaluate_options` | Rank only the options supplied by the user. |
| `brain_palate_log_decision` | Record which recommendation was chosen. Internal or admin only. |
| `brain_palate_confirm` | Confirm a pending palate proposal. |
| `brain_palate_cancel` | Cancel a pending palate proposal. |
| `brain_palate_correct_proposal` | Correct a pending palate proposal before storing it. |
| `brain_palate_refresh_enrichment` | Refresh enrichment for one stored palate item. Internal or admin only. |

Palate is best for:

- Wine: producers, vintages, regions, grapes, style, oak, body, acidity, drinking windows, and personal signals.
- Restaurants: cuisine, city, price, occasion, atmosphere, service, and personal fit.
- Media: films, series, books, music, podcasts, and watch, listen, or read signals.
- Cigars and experiences: structured preferences, dislikes, and contexts.

## Palate Examples

Describe an item without storing it:

```text
Use brain_palate_describe_item to describe Chateau Musar 2016 as a wine.
Do not store it yet.
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

Store a dislike or avoid signal:

```text
Use Brain Palate to remember:
Avoid over-oaked Napa Cabernet for casual dinners. I find it too heavy and sweet-fruited unless the meal really calls for it.
```

Query recommendations:

```text
Use Brain Palate to suggest an oaky wine I said I want to try.
Exclude anything I marked avoid or disliked. Explain the winner briefly.
```

Compare supplied options:

```text
Use brain_palate_evaluate_options for this query:
Where should I book for a serious but relaxed wine dinner in London?

Options:
- Noble Rot
- Kiln
- The Barbary
- St John
```

Log feedback after a recommendation:

```text
Use brain_palate_log_decision to record that I chose Noble Rot for the query serious but relaxed wine dinner in London.
```

Correct a pending proposal:

```text
Use brain_palate_correct_proposal:
The producer is Chateau Musar, the vintage is 2016, and the region is Bekaa Valley. Keep wanted=true and tried=false.
```

Refresh an old item:

```text
Use brain_palate_refresh_enrichment for the stored Chateau Musar 2016 item.
Keep my personal signals unchanged.
```

## How Palate Ranking Works

Palate ranking is policy-driven. Cognee can retrieve relevant structured records, but Brain decides what wins.

A good recommendation query should include:

- The category: wine, restaurant, movie, music, cigar, experience.
- The desired attributes: oaky, restrained, high-acid, casual, serious, low-intervention, classic, celebratory.
- The user's signal: wanted to try, liked, tried, avoid, disliked, recommended by someone, high rating.
- The context: dinner, gift, date night, solo watching, group meal, budget, location.

Good prompt:

```text
Use Brain Palate to suggest a wine for steak tonight.
Prefer things I liked or wanted to try. Exclude avoid and disliked items.
I want something structured, savory, and not too sweet-fruited.
Explain the top 3 in one sentence each.
```

Less useful prompt:

```text
What wine should I drink?
```

Good ranking instructions for an agent:

```text
Before ranking, use Brain Palate recall or query rather than guessing from the current chat. Treat avoid and disliked as hard exclusions. Treat wanted_to_try, liked, recommended_by, and high rating as positive signals. If two items are close, prefer the one with better context fit over the one with a higher generic score.
```

## Agent Memory

Agent memory is for continuity between agent chats. It uses a dedicated, user-scoped Cognee dataset so it can be cleaned up separately if it becomes noisy.

The default chat-continuity session id is configured in Brain settings. Do not hardcode that value. `brain_session` derives the active user's session id from that configuration and resolves the matching user-scoped chat-continuity dataset. On surfaces that expose it, `brain_session` also returns the user-scoped `session_id` for portable chat-continuity calls.

Minimal agent preprompt:

```text
Use Brain as the user's durable memory. At conversation start, call brain_session, then load relevant preferences and standing profile context for the returned session and apply them. Use external chat-continuity recall at the start of the conversation, then use external chat-continuity workflow whenever your surface exposes it to preserve chat-session memory, handovers, conversation summaries, and workflow learnings. Use the returned session_id whenever a Brain workflow accepts session_id. Use brain_remember only for durable user facts, stable preferences, explicit constraints, durable decisions, open questions, research questions, and Palate or taste memories. If the user asks to remember a stable fact about who they are, their expertise, work, background, or communication needs, use brain_profile_context_remember. Store concise declarative facts, not transcripts.
```

Use the Agent Memory Protocol, if your client exposes one, to inject operating instructions into an agent. The protocol tells the agent to:

- use the same `session_id` consistently;
- call external chat-continuity recall at the start of a conversation;
- use external chat-continuity workflow to preserve chat-session memory, handovers, conversation summaries, and workflow learnings;
- keep `brain_remember` reserved for durable user facts, stable preferences, explicit constraints, durable decisions, open questions, research questions, and Palate or taste memories;
- store concise declarative facts, not transcripts.

Prompt to start a chat with portable memory:

```text
Call brain_session, then use Brain's chat-continuity workflow with the returned user-scoped session_id. Before answering, recall relevant memory from that session with external chat-continuity recall. During the chat, preserve chat-session context through external chat-continuity workflow without narrating tool calls. Use brain_remember only for durable user facts and decisions that should live in Brain's durable memory graph.
```

Prompt to preserve the session at the end:

```text
Call brain_session, then record this chat using Brain's chat-continuity workflow with the returned user-scoped session_id. Store only durable decisions, project facts, and open questions.
```

Useful tools:

| Tool | Use it for |
| --- | --- |
| `brain_session` | Resolve the active user's default session id and Brain workflow names. |
| `brain_profile_context_remember` | Store standing user-profile context returned by `brain_session`. |
| `brain_profile_context_list` | List standing user-profile context. |
| `brain_profile_context_forget` | Remove one standing user-profile context item by id. |
| `brain_bias_context_remember` | Store stable response-style preference context. Internal or admin only. |
| `brain_bias_context_list` | List response-style preference context. Internal or admin only. |
| `brain_bias_context_forget` | Remove one response-style preference item. Internal or admin only. |
| `brain_profile_context_sync` | Sync standing user-profile context to the configured projection. Internal or admin only. |
| external chat-continuity workflow | Bridge the active user's Cognee session into their dedicated chat-continuity dataset. Available on ChatGPT app and internal or admin surfaces; internal or admin can also manage cleanup. |
| external chat-continuity recall | Search the active user's dedicated chat-continuity dataset. Available on ChatGPT app and internal or admin surfaces. |
| external chat-continuity cleanup | Clear that dataset after explicit confirmation. Internal or admin only. |

## Configuration, Auth, Backups, and Release Notes

Brain is configured through environment variables. Common groups include `ALLOW_EMBEDDING_DIMENSION_CHANGE`, `BRAIN_ADMIN_MCP_PATH`, `BRAIN_AUTH_ACCESS_TOKEN_SECONDS`, `BRAIN_AUTH_PASSWORD_FILE`, `BRAIN_AUTH_REFRESH_TOKEN_SECONDS`, `BRAIN_AUTH_REQUIRE_PKCE`, `BRAIN_AUTH_SCOPES`, `BRAIN_AUTH_STATE_PATH`, `BRAIN_AUTH_TOKEN`, `BRAIN_AUTH_USERS_FILE`, `BRAIN_BACKUP_DIR`, `BRAIN_COGNEE_DATA_DATASET`, `BRAIN_COGNEE_MEMORY_DATASET`, `BRAIN_COGNEE_PALATE_DATASET`, `BRAIN_COGNEE_RECALL_ENABLED`, `BRAIN_COGNEE_RECALL_TOP_K`, `BRAIN_COGNEE_SOURCES_DATASET`, `BRAIN_COGNEE_SYNC_ON_INGEST`, `BRAIN_COGNEE_SYNC_ON_INGEST_SWEEP_LIMIT`, `BRAIN_DATABASE_URL`, `BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED`, `BRAIN_GOOGLE_DRIVE_FOLDER`, `BRAIN_GOOGLE_DRIVE_LOCAL_PATH`, `BRAIN_GOOGLE_DRIVE_REMOTE`, `BRAIN_HEALTH_PATH`, `BRAIN_INGEST_BACKGROUND_AUTO_CHARS`, `BRAIN_LAUNCHD_LABEL`, `BRAIN_LLM_ENABLED`, `BRAIN_LOG_LEVEL`, `BRAIN_MCP_HOST`, `BRAIN_MCP_PATH`, `BRAIN_MCP_PORT`, `BRAIN_NEO4J_BREW_SERVICE`, `BRAIN_NEO4J_DOCKER_CONTAINER`, `BRAIN_NEO4J_DUMP_ENABLED`, `BRAIN_NEO4J_LAUNCHD_LABEL`, `BRAIN_NEO4J_STOP_FOR_DUMP`, `BRAIN_OPENAI_APPS_CHALLENGE_TOKEN`, `BRAIN_OWNER_FULL_NAME`, `BRAIN_OWNER_NAME`, `BRAIN_PROD_ROOT`, `BRAIN_PROFILE_CONTEXT_PATH`, `BRAIN_PROVIDER_AUTH_PROFILES_PATH`, `BRAIN_PROVIDER_AUTH_STATE_DIR`, `BRAIN_PUBLIC_ADMIN_MCP_PATH`, `BRAIN_PUBLIC_BASE_URL`, `BRAIN_PUBLIC_MCP_PATH`, `BRAIN_PUBLIC_UI_API_PATH`, `BRAIN_PUBLIC_UI_PATH`, `BRAIN_RELEASE_ENV`, `BRAIN_RELEASE_SHA`, `BRAIN_RELEASE_VERSION`, `BRAIN_REQUEST_LOG_ENABLED`, `BRAIN_REQUEST_LOG_MAX_BODY_BYTES`, `BRAIN_REQUEST_LOG_PATH`, `BRAIN_REQUEST_LOG_RETENTION_DAYS`, `BRAIN_ROUTING_LOG_ENABLED`, `BRAIN_ROUTING_LOG_PATH`, `BRAIN_ROUTING_LOG_RETENTION_DAYS`, `BRAIN_SERVICE_NAME`, `BRAIN_SLACK_ADMIN_USER_IDS`, `BRAIN_SLACK_AGENT_ENABLED`, `BRAIN_SLACK_AGENT_HOST`, `BRAIN_SLACK_AGENT_PORT`, `BRAIN_SLACK_ALLOWED_CHANNEL_IDS`, `BRAIN_SLACK_ALLOWED_TEAM_IDS`, `BRAIN_SLACK_ALLOWED_USER_IDS`, `BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE`, `BRAIN_SLACK_ENABLED`, `BRAIN_TASTE_AUTO_ENRICH_ENABLED`, `BRAIN_TASTE_AUTO_WRITE_THRESHOLD`, `BRAIN_TASTE_CANONICAL_STORE`, `BRAIN_TASTE_CONFIRMATION_THRESHOLD`, `BRAIN_TASTE_ENABLED`, `BRAIN_TASTE_LLM_MODEL`, `BRAIN_TASTE_LLM_REASONING_EFFORT`, `BRAIN_TASTE_LLM_ROUTING_ENABLED`, `BRAIN_TASTE_OPEN_LOOP_CLOSE_THRESHOLD`, `BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD`, `BRAIN_TASTE_PROPOSAL_EXPIRY_HOURS`, `BRAIN_TASTE_WEB_ENRICHMENT_ENABLED`, `BRAIN_UI_BACKEND_PORT`, `BRAIN_UI_ENABLED`, `BRAIN_UI_FRONTEND_PORT`, `BRAIN_UI_HOST`, `BRAIN_UI_LAUNCHD_LABEL`, `BRAIN_UI_PROXY_PORT`, `BRAIN_UI_SESSION_SECONDS`, `BRAIN_USER_ID`, `CONFIG_ENV`, `DATA_ROOT_DIRECTORY`, `DB_HOST`, `DB_NAME`, `DB_PASSWORD`, `DB_PORT`, `DB_PROVIDER`, `DB_USERNAME`, `EMBEDDING_DIMENSIONS`, `EMBEDDING_MODEL`, `EMBEDDING_PROVIDER`, `ENABLE_BACKEND_ACCESS_CONTROL`, `GOOGLE_FREE_TIER`, `GRAPH_DATABASE_NAME`, `GRAPH_DATABASE_PASSWORD`, `GRAPH_DATABASE_PROVIDER`, `GRAPH_DATABASE_URL`, `GRAPH_DATABASE_USERNAME`, `LLM_MAX_TOKENS`, `LLM_MODEL`, `LLM_PROVIDER`, `LLM_TEMPERATURE`, `OPENAI_AUTH_MODE`, `OPENAI_CODEX_AUTH_PROFILE`, `OPENAI_CODEX_BASE_URL`, `PROFILE`, `SYSTEM_ROOT_DIRECTORY`, `VECTOR_DATASET_DATABASE_HANDLER`, `VECTOR_DB_HOST`, `VECTOR_DB_KEY`, `VECTOR_DB_NAME`, `VECTOR_DB_PASSWORD`, `VECTOR_DB_PORT`, `VECTOR_DB_PROVIDER`, `VECTOR_DB_URL`, `VECTOR_DB_USERNAME`.

Key reminders:

- The default chat-continuity session id comes from Brain settings. Do not hardcode that value.
- `BRAIN_MCP_PATH`, `BRAIN_ADMIN_MCP_PATH`, `BRAIN_PUBLIC_ADMIN_MCP_PATH`, `BRAIN_PUBLIC_MCP_PATH`, `BRAIN_PUBLIC_UI_PATH`, and `BRAIN_PUBLIC_UI_API_PATH` control the exposed MCP and UI paths.
- `BRAIN_AUTH_ACCESS_TOKEN_SECONDS`, `BRAIN_AUTH_REFRESH_TOKEN_SECONDS`, `BRAIN_AUTH_PASSWORD_FILE`, `BRAIN_AUTH_USERS_FILE`, `BRAIN_AUTH_STATE_PATH`, `BRAIN_AUTH_SCOPES`, `BRAIN_AUTH_REQUIRE_PKCE`, `BRAIN_AUTH_TOKEN`, and `BRAIN_AUTH_SUPERUSER_IDS` control auth and session behavior. `BRAIN_AUTH_SUPERUSER_IDS` is relevant in prod, staging, and QA.
- The `BRAIN_COGNEE_*_DATASET` settings separate memory, data, sources, and palate datasets. `BRAIN_COGNEE_RECALL_ENABLED`, `BRAIN_COGNEE_RECALL_TOP_K`, `BRAIN_COGNEE_SYNC_ON_INGEST`, and `BRAIN_COGNEE_SYNC_ON_INGEST_SWEEP_LIMIT` control Cognee availability, recall, and ingest synchronization.
- `BRAIN_BACKUP_DIR` and Google Drive backup settings control backups.
- `BRAIN_RELEASE_ENV`, `BRAIN_RELEASE_SHA`, and `BRAIN_RELEASE_VERSION` identify the release; use the QA, staging, release, and validation workflows, `deploy-local-qa.yml`, `deploy-local-staging.yml`, `release.yml`, and `validate.yml` intentionally when validating or promoting changes.
- `BRAIN_CONFIG_RENDER_SHA`, `BRAIN_CONFIG_RENDERED_AT`, and `BRAIN_CONFIG_RENDER_SOURCE` may appear in rendered config.
- In dev, qa, staging, and prod, `BRAIN_LOG_LEVEL` and `BRAIN_UI_ENABLED` are also available.
- The deploy and promotion workflows are `deploy-local-qa.yml`, `deploy-local-staging.yml`, `release.yml`, and `validate.yml`.

Never store secrets, passwords, API keys, OAuth tokens, or credentials in Brain.

## Bias And Preference Prompt

Bias memory is for durable user preferences: answer length, formatting, engineering taste, naming conventions, default tools, and always or never instructions.

Use the Bias Protocol when you want an agent to load and maintain those preferences. If your surface exposes `brain_bias_context_*`, use that workflow for response-style preferences, and keep it separate from ordinary durable memory writes.

Start a new chat:

```text
Use Brain's Bias Protocol. Load my preferences from Brain before answering.
```

Store a new preference:

```text
Use Brain Bias Context to remember this preference:
Daniele prefers MCP tool names to use underscores rather than dots.
```

Revise a preference:

```text
Use Brain Bias Context to remember this updated preference:
Daniele prefers concise final answers, but wants detailed implementation updates while work is in progress.
```

Prompt an agent to apply preferences silently:

```text
Load my preferences from Brain. Apply any relevant response style, coding, and architecture preferences silently. Do not tell me that you are applying them unless I ask.
```

## Source Ingestion

Use `brain_ingest_source` when the input is too large or too source-like for a single memory card: meeting notes, articles, design docs, transcripts, tables, or copied research.

Good source-ingestion prompt:

```text
Use Brain to ingest this architecture note as source material.
Extract only durable decisions, open questions, and project facts.
Do not store temporary discussion or unresolved speculation as facts.

[paste note]
```

Good article prompt:

```text
Use Brain to ingest this article URL and save the key takeaways relevant to Brain, Cognee, memory retrieval, and local deployment. Keep the source attached for evidence.
```

When to use `brain_remember` instead:

```text
Use Brain to remember: Production and dev Brain services must use separate ports because they run on the same host.
```

## Recall Patterns

Ask recall questions the way you would ask a focused research assistant.

Specific recall:

```text
Use Brain to recall what we decided about SQLite versus Cognee for palate.
```

Entity profile:

```text
Use Brain to profile the Brain project, focusing on deployment, Cognee, Palate, and open architecture questions.
```

Open loops:

```text
Use Brain to list open loops about chat continuity and palate enrichment.
```

Before ambiguous work:

```text
Before implementing, use Brain to recall what the Cognee split referred to in our prior Brain discussions.
```

Evidence-oriented:

```text
Use Brain to answer with evidence: why did we decide not to keep SQLite as the canonical store for approved palate items?
```

## Cleanup And Correction

Brain is designed to be corrected. Use cleanup tools when memory quality drifts.

Review recent writes:

```text
Use brain_review_recent and summarize the last 10 memory writes. Flag anything that looks too broad, duplicated, or wrong.
```

Undo the latest write:

```text
Use brain_undo_last to undo the most recent ingestion run.
```

Forget a bad memory:

```text
Use brain_forget to remove the memory that says dev and prod can share the same Neo4j database. That is wrong.
```

Resolve a contradiction:

```text
Use brain_resolve_conflict:
The newer memory saying Brain keeps policy and ranking logic should replace the older memory saying SQLite is canonical for palate.
```

Merge duplicates:

```text
Use brain_merge_entities to merge the duplicate Cognee and cognee.ai entities. Keep Cognee as primary.
```

Clear chat continuity if it becomes noisy:

```text
Use external chat-continuity cleanup with confirm=true. I want to reset the dedicated portable chat-continuity dataset.
```

Prefer targeted `brain_forget` or `brain_undo_last`; both use Cognee native forget for Cognee-backed semantic data and keep status-event datapoints only as audit evidence. Hard delete should remain restricted and explicitly confirmed when available.

## Cognee Operations

Most users should not need Cognee operations directly. Use them when managing the retrieval backend.

Run native improve on a dataset:

```text
Call brain_session, then use cognee_improve on dataset chat_continuity with the returned session_id. Run it in the background if supported.
```

Manually sync Brain projections:

```text
Do not use brain_sync_cognee. It is hard-deprecated; retry the original Cognee write or use Cognee-native maintenance.
```

Rebuild Cognee-native memory:

```text
Use Cognee-native maintenance: cognee.forget(dataset="memory", memory_only=true), then cognee.cognify(datasets=["memory"]).
```

Delete and rebuild only when you are intentionally resetting a Cognee dataset:

```text
Use cognee.forget(dataset="palate") only with explicit operator confirmation, then re-export or re-ingest the dataset.
```

## Best Practices For Prompting Agents

Use Brain explicitly. Agents should not have to infer whether a fact is durable.

Good:

```text
Use Brain to remember this as a durable architecture decision:
Brain keeps policy and ranking logic; Cognee keeps rebuildable retrieval and portable chat-continuity projections.
```

Weak:

```text
Remember this whole conversation.
```

Ask for atomic memories. One fact per sentence is easier to recall, dedupe, and correct.

Good:

```text
Use Brain to store these as separate memories:
1. Daniele prefers short final answers.
2. Daniele wants implementation progress updates while work is in progress.
3. Daniele prefers production and dev services to be isolated by port and data directory when they share a host.
```

Use context labels when the same phrase may be ambiguous.

Good:

```text
Use Brain to recall palate canonical store in the context of the Brain project, not the generic concept of taste.
```

Make recommendations policy-aware.

Good:

```text
Use Brain Palate to recommend a restaurant for Friday in London.
Prefer places I liked or wanted to try. Exclude avoid or disliked. Prioritize serious wine, relaxed atmosphere, and not too formal.
```

Tell agents when not to write memory.

Good:

```text
Use Brain recall for context, but do not write any new memories unless I explicitly say remember.
```

Use recall before implementation when history matters.

Good:

```text
Before changing the Brain MCP tool names, use Brain to recall our naming decision about dots versus underscores.
```

Use cleanup after experiments.

Good:

```text
Review recent Brain writes from this session. Soft-delete anything that was temporary experiment state rather than a durable decision.
```

## Suggested Agent Starter Prompts

General Brain-aware agent:

```text
You have Brain MCP tools. At the start, use brain_recall for relevant project context if my request depends on prior decisions. Use brain_remember only for durable user facts, stable preferences, explicit constraints, durable decisions, Palate or taste memories, open questions, and research questions. Use brain_session plus external chat-continuity workflow for chat-session handovers and workflow continuity. Store one declarative sentence per fact. Do not store temporary scratch or transcripts.
```

Brain plus preferences:

```text
Use Brain's Bias Protocol, then load my preferences from Brain. Apply recalled preferences silently. If I state a new durable preference or revise an old one, store it with brain_remember or brain_bias_context_remember when it is a response-style preference.
```

Brain plus portable chat continuity:

```text
Call brain_session, then use external chat-continuity workflow with the returned user-scoped session_id. Recall relevant session memory before answering. During the conversation, preserve handover-worthy chat context with external chat-continuity workflow; use brain_remember only for durable user facts, stable preferences, explicit constraints, durable decisions, open questions, research questions, and Palate or taste memories.
```

Brain plus Palate:

```text
Use Brain Palate for taste-related memories and recommendations. Normalize and enrich items before storing. Treat avoid or disliked as hard exclusions. Treat wanted_to_try, liked, high rating, and recommended_by as positive signals. After I choose an option, log the decision.
```

Implementation agent:

```text
Before coding, use Brain to recall prior decisions about this project area. After implementation, remember only durable decisions or new constraints that future agents should know. Do not store test logs, temporary failures, or transient debugging notes.
```

Research agent:

```text
Use Brain to recall what we already know about this topic before researching. When done, ingest source material only if it is likely to be useful later. Store key takeaways as evidence-backed memories, and keep open questions separate from facts.
```

Palate recommendation agent:

```text
Use Brain Palate to answer taste questions. If the user asks for a suggestion, retrieve candidate palate records, exclude avoid or disliked items, rank by fit to the query and user signals, and explain the top result briefly. If the user chooses something, call brain_palate_log_decision.
```

## Common Workflows

### Save A Decision

```text
Use Brain to remember this decision:
Brain DB owns durable memory lifecycle and taste policy; Cognee owns rebuildable semantic retrieval and the dedicated chat-continuity projection.
```

### Save A Preference

```text
Use Brain to remember:
Daniele prefers short, direct answers for status updates.
```

### Save A Palate Item

```text
Use Brain Palate to remember:
I tried Noble Rot and liked it for serious but relaxed wine dinners in London.
```

### Get A Recommendation

```text
Use Brain Palate to suggest a restaurant for a relaxed but serious wine dinner in London. Prefer places I liked or wanted to try. Exclude avoid or disliked.
```

### Continue Work In A New Agent Chat

```text
Call brain_session, then use external chat-continuity workflow with the returned user-scoped session_id. Load my preferences from Brain. Then use external chat-continuity recall to recall what we decided about the Brain palate migration before proposing next steps.
```

### End A Session Cleanly

```text
Use Brain's chat-continuity workflow to preserve a concise wrap-up with the standard session_id from brain_session:
- durable decisions we made;
- open questions;
- project facts future agents need;
- palate choices or decisions, using Palate tools where appropriate.

Do not store temporary debugging output, and do not use brain_remember for chat-session handover unless there is a separate durable user fact or decision.
```

## Troubleshooting

If recall feels wrong:

```text
Use brain_review_recent to inspect recent writes related to this topic. Identify duplicates, contradictions, or overly broad memories.
```

If a recommendation includes something you dislike:

```text
Use Brain Palate to remember that I want to avoid that item in this context, then rerun the recommendation excluding avoid and disliked items.
```

If an agent keeps storing too much:

```text
Use Brain only for durable decisions, preferences, project facts, palate signals, open questions, and research questions. Do not store summaries of ordinary back-and-forth.
```

If portable session memory becomes messy:

```text
Use external chat-continuity recall to inspect what is being retrieved for this topic. If it is not useful, clear your dedicated chat-continuity dataset with external chat-continuity cleanup confirm=true.
```

If Cognee semantic memory is stale:

```text
Use Cognee-native maintenance for the relevant dataset. brain_rebuild_cognee is hard-deprecated and should not be used.
```

## Mental Model

Brain is not a diary. It is a control plane for facts that should change future agent behavior.

Palate is not just a list of restaurants and wines. It is the structured taste layer: enrichment, personal signals, ranking, decisions, and feedback.

Agent memory is not the canonical store for everything. It is a portable conversation-memory layer that can be improved and removed cleanly if it gets noisy.

The best Brain usage is explicit, concise, and reversible:

```text
Recall before relying on history.
Remember only durable facts.
Use Palate for taste.
Log decisions after recommendations.
Review and clean up when memory quality drifts.
```

<!-- brain-doc-source-hash: b497b0c3020424a742c96ba0ac0fdb3f9a87edb8110b5c2ff08fea978bdb7017 -->
<!-- brain-doc-source-commit: 698187a22eedb822d84471a1e38a54e2528d59ed -->
