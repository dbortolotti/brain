# Model Eval Role Hierarchy


## `router`
*Classify incoming user intent and route messages to recall, ingestion, debug/admin, or no-op paths.*

####  <span style="color: green;">intent_router: [openai:gpt-5-nano]</span>
 >    *Brief: Classify intent across router, Slack intake, memory compiler, recall, and debug/admin flows.*


## `slack_intake`
*Convert Slack messages into safe ingestion decisions and user-facing receipts without committing low-value, ambiguous, or unsafe memories.*

####  <span style="color: red;">source_classifier: []</span>
 >    *Brief: Identify source type and source/material boundaries before extraction.*

####  <span style="color: red;">durability_filter: []</span>
 >    *Brief: Decide whether input contains durable memory value or should be rejected as junk, vague, unresolved, or non-committable.*

####  <span style="color: red;">memory_kind_classifier: []</span>
 >    *Brief: Classify candidate memory kind and avoid unsafe splitting or merging of facts.*

####  <span style="color: red;">repair_option_generator: []</span>
 >    *Brief: Propose safe user-facing repair options when clarification or conflict resolution is required.*

####  <span style="color: red;">commit_policy_decider: []</span>
 >    *Brief: Decide whether a validated proposal can commit, must ask, or must be rejected.*

####  <span style="color: red;">success_receipt_generator: []</span>
 >    *Brief: Produce concise user-facing confirmations for successful Slack or memory operations.*

####  <span style="color: green;">zero_tolerance_validator: [deterministic]</span>
 >    *Brief: Enforce non-negotiable safety checks before any memory commit.*


## `memory_compiler`
*Turn notes, articles, summaries, transcripts, and structured sources into atomic memory cards while preserving source boundaries and avoiding invention.*

####  <span style="color: red;">atomic_card_extractor: []</span>
 >    *Brief: Extract atomic memory cards from durable source material without inventing unsupported facts or collapsing long sources into one card.*

####  <span style="color: green;">entity_mention_extractor: [openai:gpt-5.4-mini]</span>
 >    *Brief: Extract explicit entity mentions, aliases, types, and roles without inventing identities.*

####  <span style="color: red;">relationship_extractor: []</span>
 >    *Brief: Extract directed relationships and attributes between entities without inverting meaning or altering numeric values.*

####  <span style="color: red;">open_loop_detector: []</span>
 >    *Brief: Detect unresolved questions, todos, and open loops that should remain explicit rather than becoming false facts.*

####  <span style="color: red;">table_policy_handler: []</span>
 >    *Brief: Decide how small and large tables should be handled without dropping values, atomizing large tables by default, or changing numbers.*

####  <span style="color: red;">source_takeaway_extractor: []</span>
 >    *Brief: Extract grounded takeaways from source documents while preserving evidence boundaries and avoiding source invention.*

####  <span style="color: green;">table_parser: [deterministic]</span>
 >    *Brief: Parse table structure before model-facing interpretation.*

####  <span style="color: green;">source_loader: [deterministic]</span>
 >    *Brief: Load and normalize source material before extraction.*

####  <span style="color: green;">zero_tolerance_validator: [deterministic]</span>
 >    *Brief: Enforce non-negotiable safety checks before memory output is accepted.*


## `entity_resolution`
*Resolve entity mentions and candidate identities while preferring clarification over unsafe merges.*

####  <span style="color: green;">entity_mention_extractor: [openai:gpt-5.4-mini]</span>
 >    *Brief: Extract explicit entity mentions, aliases, types, and roles without inventing identities.*

####  <span style="color: red;">entity_candidate_ranker: []</span>
 >    *Brief: Rank candidate entity matches while avoiding unsafe overmerge.*

####  <span style="color: red;">entity_final_resolver: []</span>
 >    *Brief: Make the final entity resolution choice from ranked candidates and evidence.*


## `conflict_handling`
*Detect candidate conflicts and explain contradiction, correction, supersession, duplicate, or additive relationships without silently overwriting facts.*

####  <span style="color: red;">conflict_candidate_detector: []</span>
 >    *Brief: Detect memories that may duplicate, supersede, correct, or contradict existing facts.*

####  <span style="color: red;">conflict_explainer: []</span>
 >    *Brief: Explain conflict type and evidence without making the final policy decision or silently overwriting current facts.*

####  <span style="color: red;">conflict_policy_decider: []</span>
 >    *Brief: Choose ask, keep, duplicate, reject, or supersede policy from conflict evidence.*


## `recall`
*Plan retrieval and synthesize grounded answers from DB/Cognee results without returning deleted/superseded facts as current.*

####  <span style="color: red;">recall_planner: []</span>
 >    *Brief: Plan retrieval scope and query strategy without dumping irrelevant memory or making unsupported absence claims.*

####  <span style="color: red;">recall_relevance_filter: []</span>
 >    *Brief: Filter and order visible recall candidates by query relevance after hard status filtering.*

####  <span style="color: red;">recall_synthesizer: []</span>
 >    *Brief: Synthesize grounded answers from retrieved memory records without unsupported inference, irrelevant dumps, or stale deleted facts.*


## `debug`
*Explain recall plans, filtered candidates, and sync/debug state for operators.*

####  <span style="color: green;">debug_explainer: [google:gemini-2.5-flash-lite]</span>
 >    *Brief: Explain internal retrieval, filtering, and sync state for debugging while avoiding exposure of raw private source content.*


## `judge`
*Offline model-output quality judging; not part of normal runtime.*

####  <span style="color: green;">eval_judge: [openai:gpt-5.5]</span>
 >    *Brief: Judge model output quality offline for eval reporting and adjudication; not part of normal runtime.*


## `embeddings`
*Embedding model coverage for retrieval tests.*

####  <span style="color: red;">embeddings: []</span>
 >    *Brief: Produce embeddings for retrieval tests.*
