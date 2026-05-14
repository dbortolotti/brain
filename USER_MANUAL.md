# Brain User Manual

Brain is a personal memory and taste system for agents.

Use Brain when you want an agent to remember durable facts, decisions,
preferences, project state, open loops, source material, or palate/taste
signals. Use Cognee-backed agent memory when you want continuity between agent
chats. Use Palate when the memory is about taste: wine, restaurants, media,
music, cigars, experiences, and other supported preference categories.

The practical rule is simple:

- Brain owns memory policy, durable preferences, cleanup, ranking, and palate
  decisions.
- Cognee owns semantic recall and session-memory retrieval.
- Palate owns taste normalization, enrichment, and recommendation ranking.

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
Use Brain's agent-memory protocol for this chat with session_id portable_agent_session.
```

## What Brain Is Good For

Use Brain for durable information that should affect future conversations.

Good memories:

- "Daniele prefers short answers unless implementation detail is needed."
- "The Brain production and dev services run on the same host and must use
  separate ports."
- "We decided palate-approved records should live primarily in Cognee
  DataPoints."
- "The open question is whether agent-memory improvement creates too much
  noise over time."
- "Sam recommended Chateau Musar 2016 and Daniele wants to try it."

Poor memories:

- "This is important."
- "The user sounded happy."
- "Maybe this might matter later."
- Full transcripts when one sentence would preserve the useful fact.
- Secrets, passwords, API keys, OAuth tokens, or credentials.

## Core MCP Tools

Most agents should use these tools rather than lower-level storage details.

| Tool | Use it for |
| --- | --- |
| `brain_remember` | Store a durable memory, fact, preference, decision, or short note. |
| `brain_ingest_source` | Store longer source material and optionally extract memories. |
| `brain_recall` | Answer a memory query with evidence. |
| `brain_profile_entity` | Build a profile for a person, project, place, or other entity. |
| `brain_list_open_loops` | List open questions, reminders, and parked research threads. |
| `brain_get_memory` | Read one memory card by id. |
| `brain_get_source` | Read source metadata and optionally source text. |
| `brain_review_recent` | Review recent writes and ingestion runs. |
| `brain_undo_last` | Undo the latest ingestion run by soft-deleting its objects. |
| `brain_forget` | Soft-delete or, with confirmation, hard-delete a Brain object. |
| `brain_resolve_conflict` | Resolve contradictions or duplicates between memories. |
| `brain_merge_entities` | Merge duplicate entities after confirmation. |

Maintenance tools:

| Tool | Use it for |
| --- | --- |
| `brain_sync_cognee` | Manually sync pending Brain projections to Cognee. |
| `brain_rebuild_cognee` | Mark Cognee projections stale so they can be rebuilt. |
| `cognee_improve` | Run Cognee native improve on a configured dataset. |

Normal users rarely need maintenance tools. Use them when operating the system,
debugging projections, or intentionally improving a Cognee dataset.

## Palate Tools

Palate is Brain's taste layer. It normalizes messy user input into structured
items, enriches those items, stores taste signals, and ranks recommendations.

| Tool | Use it for |
| --- | --- |
| `brain_palate_describe_item` | Normalize and enrich an item without storing it. |
| `brain_palate_remember` | Store an approved palate item and its signals. |
| `brain_palate_query` | Rank stored palate records for a recommendation query. |
| `brain_palate_evaluate_options` | Rank only the options supplied by the user. |
| `brain_palate_log_decision` | Record which recommendation was chosen. |
| `brain_palate_confirm` | Confirm a pending palate proposal. |
| `brain_palate_cancel` | Cancel a pending palate proposal. |
| `brain_palate_correct_proposal` | Correct a pending palate proposal before storing it. |
| `brain_palate_refresh_enrichment` | Refresh enrichment for one stored palate item. |

Palate is best for:

- Wine: producers, vintages, regions, grapes, style, oak, body, acidity,
  drinking windows, and personal signals.
- Restaurants: cuisine, city, price, occasion, atmosphere, service, and personal
  fit.
- Media: films, series, books, music, podcasts, and watch/listen/read signals.
- Cigars and experiences: structured preferences, dislikes, and contexts.

## Palate Examples

Describe an item without storing it:

```text
Use brain_palate_describe_item to describe Chateau Musar 2016 as a wine.
Do not store it yet. Fetch external ratings if available, but do not use broad
web search unless needed.
```

Remember a wine:

```text
Use Brain Palate to remember:
I want to try Chateau Musar 2016. Sam recommended it. Treat it as a wine.
Notes: likely savory, mature, complex Lebanese red. I am curious but have not
tried it.
```

Remember a restaurant:

```text
Use Brain Palate to remember:
Noble Rot is a restaurant I like for wine-led dinners in London. I like the
wine list, classic food, and relaxed but serious atmosphere.
```

Store a dislike or avoid signal:

```text
Use Brain Palate to remember:
Avoid over-oaked Napa Cabernet for casual dinners. I find it too heavy and
sweet-fruited unless the meal really calls for it.
```

Query recommendations:

```text
Use Brain Palate to suggest an oaky wine I said I want to try.
Exclude anything I marked avoid or disliked. Explain the winner briefly.
```

Compare supplied options:

```text
Use brain_palate_evaluate_options for this query:
"Where should I book for a serious but relaxed wine dinner in London?"

Options:
- Noble Rot
- Kiln
- The Barbary
- St John
```

Log feedback after a recommendation:

```text
Use brain_palate_log_decision to record that I chose Noble Rot for the query
"serious but relaxed wine dinner in London".
```

Correct a pending proposal:

```text
Use brain_palate_correct_proposal:
The producer is Chateau Musar, the vintage is 2016, and the region is Bekaa
Valley. Keep wanted=true and tried=false.
```

Refresh an old item:

```text
Use brain_palate_refresh_enrichment for the stored Chateau Musar 2016 item.
Keep my personal signals unchanged.
```

## How Palate Ranking Works

Palate ranking is policy-driven. Cognee can retrieve relevant structured
DataPoints, but Brain decides what wins.

A good recommendation query should include:

- The category: wine, restaurant, movie, music, cigar, experience.
- The desired attributes: oaky, restrained, high-acid, casual, serious,
  low-intervention, classic, celebratory.
- The user's signal: wanted to try, liked, tried, avoid, disliked,
  recommended by someone.
- The context: dinner, gift, date night, solo watching, group meal, budget,
  location.

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
Before ranking, use Brain Palate recall/query rather than guessing from the
current chat. Treat avoid and disliked as hard exclusions. Treat wanted_to_try
and recommended_by as positive signals. If two items are close, prefer the one
with better context fit over the one with a higher generic score.
```

## Agent Memory

Agent memory is for continuity between agent chats. It uses a dedicated Cognee
dataset so it can be cleaned up separately if it becomes noisy.

The default session id is:

```text
portable_agent_session
```

Use the prompt `brain_agent_memory_protocol` to inject operating instructions
into an agent. The protocol tells the agent to:

- call Cognee `recall` at the start of a conversation;
- use the same `session_id` consistently;
- call Cognee `remember` when decisions, preferences, constraints, or project
  facts are established;
- store concise declarative facts, not transcripts;
- use Brain's `brain_agent_memory` workflow when asked to preserve the chat
  memory.

Prompt to start a chat with portable memory:

```text
Use Brain's brain_agent_memory_protocol with session_id portable_agent_session.
Before answering, recall relevant memory from that session. During the chat,
record durable decisions and project facts without narrating tool calls.
```

Prompt to preserve the session at the end:

```text
Record this chat using Brain's agent-memory workflow with session_id
portable_agent_session. Store only durable decisions, project facts, and open
questions.
```

Useful tools:

| Tool | Use it for |
| --- | --- |
| `brain_agent_memory` | Bridge one Cognee session into the dedicated agent-memory dataset. |
| `brain_agent_memory_recall` | Search the dedicated agent-memory dataset. |
| `brain_agent_memory_clear` | Clear that dataset after explicit confirmation. |

The production automation is intended to improve `portable_agent_session`
nightly at 03:00 UK time. Manual improvement is still useful after an important
long session.

## Bias And Preference Prompt

Bias memory is for durable user preferences: answer length, formatting,
engineering taste, naming conventions, default tools, and "always/never"
instructions.

Use the prompt `brain_bias_protocol` when you want an agent to load and maintain
those preferences.

Start a new chat:

```text
Use Brain's brain_bias_protocol. Load my preferences from Brain before answering.
```

Store a new preference:

```text
Use Brain to remember this preference:
Daniele prefers MCP tool names to use underscores rather than dots.
```

Revise a preference:

```text
Use Brain to remember this updated preference:
Daniele prefers concise final answers, but wants detailed implementation updates
while work is in progress.
```

Prompt an agent to apply preferences silently:

```text
Load my preferences from Brain. Apply any relevant response style, coding, and
architecture preferences silently. Do not tell me that you are applying them
unless I ask.
```

## Source Ingestion

Use `brain_ingest_source` when the input is too large or too source-like for a
single memory card: meeting notes, articles, design docs, transcripts, tables,
or copied research.

Good source-ingestion prompt:

```text
Use Brain to ingest this architecture note as source material.
Extract only durable decisions, open questions, and project facts.
Do not store temporary discussion or unresolved speculation as facts.

[paste note]
```

Good article prompt:

```text
Use Brain to ingest this article URL and save the key takeaways relevant to
Brain, Cognee, memory retrieval, and local deployment. Keep the source attached
for evidence.
```

When to use `brain_remember` instead:

```text
Use Brain to remember: Production and dev Brain services must use separate
ports because they run on the same host.
```

## Recall Patterns

Ask recall questions the way you would ask a focused research assistant.

Specific recall:

```text
Use Brain to recall what we decided about SQLite versus Cognee for palate.
```

Entity profile:

```text
Use Brain to profile the Brain project, focusing on deployment, Cognee, Palate,
and open architecture questions.
```

Open loops:

```text
Use Brain to list open loops about agent memory and palate enrichment.
```

Before ambiguous work:

```text
Before implementing, use Brain to recall what "the Cognee split" referred to in
our prior Brain discussions.
```

Evidence-oriented:

```text
Use Brain to answer with evidence: why did we decide not to keep SQLite as the
canonical store for approved palate items?
```

## Cleanup And Correction

Brain is designed to be corrected. Use cleanup tools when memory quality drifts.

Review recent writes:

```text
Use brain_review_recent and summarize the last 10 memory writes. Flag anything
that looks too broad, duplicated, or wrong.
```

Undo the latest write:

```text
Use brain_undo_last to undo the most recent ingestion run.
```

Forget a bad memory:

```text
Use brain_forget to soft-delete the memory that says dev and prod can share the
same Neo4j database. That is wrong.
```

Resolve a contradiction:

```text
Use brain_resolve_conflict:
The newer memory saying "Palate approved records are canonical in Cognee" should
replace the older memory saying "SQLite is canonical for palate".
```

Merge duplicates:

```text
Use brain_merge_entities to merge the duplicate "Cognee" and "cognee.ai"
entities. Keep "Cognee" as primary.
```

Clear agent memory if it becomes noisy:

```text
Use brain_agent_memory_clear with confirm=true. I want to reset the dedicated
portable agent-memory dataset.
```

## Cognee Operations

Most users should not need Cognee operations directly. Use them when managing
the retrieval backend.

Run native improve on a dataset:

```text
Use cognee_improve on dataset agent_memory with session_ids
["portable_agent_session"]. Run it in the background if supported.
```

Manually sync Brain projections:

```text
Use brain_sync_cognee for dataset palate and object_type all.
```

Rebuild projections:

```text
Use brain_rebuild_cognee for dataset memory. Do not prune first.
```

Prune and rebuild only when you are intentionally resetting a projection:

```text
Use brain_rebuild_cognee for dataset palate with prune_first=true and
confirm=true.
```

## Best Practices For Prompting Agents

Use Brain explicitly. Agents should not have to infer whether a fact is durable.

Good:

```text
Use Brain to remember this as a durable architecture decision:
Approved palate items are stored as Cognee DataPoints; Brain keeps policy and
ranking logic.
```

Weak:

```text
Remember this whole conversation.
```

Ask for atomic memories. One fact per sentence is easier to recall, dedupe, and
correct.

Good:

```text
Use Brain to store these as separate memories:
1. Daniele prefers short final answers.
2. Daniele wants implementation progress updates while work is in progress.
3. Daniele prefers production and dev services to be isolated by port and data
   directory when they share a host.
```

Use context labels when the same phrase may be ambiguous.

Good:

```text
Use Brain to recall "palate canonical store" in the context of the Brain
project, not the generic concept of taste.
```

Make recommendations policy-aware.

Good:

```text
Use Brain Palate to recommend a restaurant for Friday in London.
Prefer places I liked or wanted to try. Exclude avoid/disliked. Prioritize
serious wine, relaxed atmosphere, and not too formal.
```

Tell agents when not to write memory.

Good:

```text
Use Brain recall for context, but do not write any new memories unless I
explicitly say "remember".
```

Use recall before implementation when history matters.

Good:

```text
Before changing the Brain MCP tool names, use Brain to recall our naming
decision about dots versus underscores.
```

Use cleanup after experiments.

Good:

```text
Review recent Brain writes from this session. Soft-delete anything that was
temporary experiment state rather than a durable decision.
```

## Suggested Agent Starter Prompts

General Brain-aware agent:

```text
You have Brain MCP tools. At the start, use brain_recall for relevant project
context if my request depends on prior decisions. Use brain_remember only for
durable decisions, preferences, project facts, and open loops. Store one
declarative sentence per fact. Do not store temporary scratch or transcripts.
```

Brain plus preferences:

```text
Use brain_bias_protocol, then load my preferences from Brain. Apply recalled
preferences silently. If I state a new durable preference or revise an old one,
store it with brain_remember.
```

Brain plus portable agent memory:

```text
Use brain_agent_memory_protocol with session_id portable_agent_session. Recall
relevant session memory before answering. During the conversation, record durable
decisions, project facts, constraints, and open questions as concise facts.
```

Brain plus Palate:

```text
Use Brain Palate for taste-related memories and recommendations. Normalize and
enrich items before storing. Treat avoid/disliked as hard exclusions. Treat
wanted_to_try, liked, high rating, and recommended_by as positive signals.
After I choose an option, log the decision.
```

Implementation agent:

```text
Before coding, use Brain to recall prior decisions about this project area.
After implementation, remember only durable decisions or new constraints that
future agents should know. Do not store test logs, temporary failures, or
transient debugging notes.
```

Research agent:

```text
Use Brain to recall what we already know about this topic before researching.
When done, ingest source material only if it is likely to be useful later.
Store key takeaways as evidence-backed memories, and keep open questions
separate from facts.
```

Palate recommendation agent:

```text
Use Brain Palate to answer taste questions. If the user asks for a suggestion,
retrieve candidate palate records, exclude avoid/disliked items, rank by fit to
the query and user signals, and explain the top result briefly. If the user
chooses something, call brain_palate_log_decision.
```

## Common Workflows

### Save A Decision

```text
Use Brain to remember this decision:
Brain owns schema and taste policy; Cognee owns memory and retrieval.
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
Use Brain Palate to suggest a restaurant for a relaxed but serious wine dinner
in London. Prefer places I liked or wanted to try. Exclude avoid/disliked.
```

### Continue Work In A New Agent Chat

```text
Use brain_agent_memory_protocol with session_id portable_agent_session.
Load my preferences from Brain. Then recall what we decided about the Brain
palate migration before proposing next steps.
```

### End A Session Cleanly

```text
Use Brain to store a concise wrap-up:
- durable decisions we made;
- open questions;
- project facts future agents need;
- palate choices or decisions, using Palate tools where appropriate.

Do not store temporary debugging output.
```

## Troubleshooting

If recall feels wrong:

```text
Use brain_review_recent to inspect recent writes related to this topic. Identify
duplicates, contradictions, or overly broad memories.
```

If a recommendation includes something you dislike:

```text
Use Brain Palate to remember that I want to avoid that item in this context,
then rerun the recommendation excluding avoid and disliked items.
```

If an agent keeps storing too much:

```text
Use Brain only for durable decisions, preferences, project facts, palate
signals, and open loops. Do not store summaries of ordinary back-and-forth.
```

If portable session memory becomes messy:

```text
Use brain_agent_memory_recall to inspect what is being retrieved for this topic.
If it is not useful, clear the dedicated agent-memory dataset with
brain_agent_memory_clear confirm=true.
```

If Cognee projection is stale:

```text
Use brain_sync_cognee for the relevant dataset. If that does not fix it, use
brain_rebuild_cognee without pruning first.
```

## Mental Model

Brain is not a diary. It is a control plane for facts that should change future
agent behavior.

Palate is not just a list of restaurants and wines. It is the structured taste
layer: enrichment, personal signals, ranking, decisions, and feedback.

Agent memory is not the canonical store for everything. It is a portable
conversation-memory layer that can be improved nightly and removed cleanly if it
gets noisy.

The best Brain usage is explicit, concise, and reversible:

```text
Recall before relying on history.
Remember only durable facts.
Use Palate for taste.
Log decisions after recommendations.
Review and clean up when memory quality drifts.
```
