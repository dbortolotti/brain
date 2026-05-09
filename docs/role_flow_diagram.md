# Brain Flow Diagrams

This document contains two related but different views of Brain:

1. **Current runtime flow** - what the application code executes today.
2. **Fine-grained role topology** - the model/eval capability map declared in
   `brain_model_registry.yaml`.

The fine-grained topology is useful for model evaluation and deployment
planning, but it is not a literal runtime call graph. Current production
runtime is mostly deterministic. The only normal runtime LLM hooks are:

- an optional Slack proposal model when `SlackMemoryAgent` is constructed with
  an injected `llm_client`
- an optional broad memory compiler fallback when `BRAIN_LLM_ENABLED=true` and
  deterministic rule compilation is not already high-confidence

## Current Runtime Flow

Source of truth: `src/memory_stack/brain_service.py`,
`src/memory_stack/slack_memory_agent.py`, `src/memory_stack/ingestion/*`,
`src/memory_stack/resolution/*`, and `src/memory_stack/recall/*`.

```mermaid
flowchart LR
    classDef det fill:#dcfce7,stroke:#15803d,color:#08331a;
    classDef opt fill:#e0f2fe,stroke:#0369a1,color:#082f49;
    classDef store fill:#f3f4f6,stroke:#374151,color:#111827;
    classDef ext fill:#fef3c7,stroke:#a16207,color:#3f2d05;

    USER[/"User or client"/]:::ext
    SLACK[/"Slack events<br/>commands<br/>interactions"/]:::ext
    HTTP[/"HTTP or MCP tools"/]:::ext
    DB[("Brain DB")]:::store
    COGNEE[("Cognee projection")]:::store

    SLACK --> SAUTH[verify Slack signature<br/>allowlists]:::det
    SAUTH --> SPARSE[parse Slack intent]:::det
    SPARSE --> SREMEMBER[remember / confirm]:::det
    SPARSE --> SREAD[recall / profile / open loops / debug]:::det

    SREMEMBER --> SPROPOSE[proposal + guardrails<br/>dry run + confirmation]:::det
    SPROPOSE -. "optional injected LLM" .-> SLLM[Slack proposal model]:::opt
    SPROPOSE --> REMEMBER[brain_service.remember]:::det

    HTTP --> HROUTE[FastAPI endpoint<br/>MCP tool dispatch]:::det
    HROUTE --> REMEMBER
    HROUTE --> INGEST[brain_service.ingest_source]:::det
    HROUTE --> RECALL[brain_service.recall]:::det
    HROUTE --> ADMIN[get / profile / review<br/>undo / resolve / sync]:::det

    INGEST --> TOREMEMBER[build RememberRequest]:::det
    TOREMEMBER --> REMEMBER

    REMEMBER --> COMPILE[compile_memory]:::det
    COMPILE --> RULES[rule_compiler<br/>classify + create candidates]:::det
    RULES -. "if enabled and rules are not high-confidence" .-> CLLM[broad LLM compiler fallback]:::opt
    RULES --> RUN[create ingestion run]:::det
    CLLM --> RUN

    RUN --> UPSOURCE[upsert source<br/>mark Cognee pending]:::det
    RUN --> UPMEM[upsert memory card]:::det
    UPMEM --> ENT[resolve + link entities]:::det
    ENT --> REL[create relationships<br/>open loops]:::det
    REL --> CONFLICT[detect/apply duplicate<br/>supersession/conflict rules]:::det
    CONFLICT --> PENDING[mark Cognee pending/stale<br/>finish run + receipt]:::det
    UPSOURCE --> DB
    PENDING --> DB
    PENDING -. "out-of-band sync" .-> COGNEE

    SREAD --> RECALL
    RECALL --> MODE[infer recall mode]:::det
    MODE --> RETRIEVE[search Brain DB<br/>optional Cognee hydration]:::det
    RETRIEVE --> FILTER[status visibility filter]:::det
    FILTER --> ANSWER[build facts/evidence<br/>render templated answer]:::det
    ANSWER --> DBLOG[log recall]:::det
    DBLOG --> DB
    ANSWER --> USER

    ADMIN --> DB
    ADMIN -. "sync/rebuild" .-> COGNEE
```

## Runtime Notes

1. **Routing is deterministic.** HTTP requests are dispatched by FastAPI routes
   and MCP tool names. Slack requests are dispatched by command/event parsing.
   The runtime does not call a fine-grained `intent_router` model.
2. **Compilation is deterministic first.** `compile_memory` calls the rule
   compiler first. A broad LLM compiler can run only when LLMs are enabled and
   the rule result is not already sufficient high-confidence.
3. **Fine-grained extractor roles are not separate runtime calls.** Roles such
   as `atomic_card_extractor`, `entity_mention_extractor`,
   `relationship_extractor`, `open_loop_detector`, and
   `source_takeaway_extractor` are currently represented by deterministic rule
   compiler behavior, or by the optional broad compiler fallback.
4. **Memory cards are written before conflict handling.** Runtime writes the
   memory card, resolves and links entities, creates relationships/open loops,
   then runs deterministic duplicate/conflict/supersession handling.
5. **Recall is deterministic.** Recall mode inference, retrieval, status
   filtering, evidence construction, and answer rendering are code paths, not a
   fine-grained `recall_synthesizer` model call.
6. **Eval and embeddings remain model-backed outside this flow.** `eval_judge`
   is used by eval tooling. Embedding models are used when vector/Cognee paths
   are enabled.

## Runtime Role Status

| Role | Current runtime status |
| --- | --- |
| `intent_router` | Deterministic route/command parsing |
| `source_classifier` | Deterministic heuristics |
| `durability_filter` | Deterministic guardrails / rule sufficiency |
| `memory_kind_classifier` | Deterministic classification |
| `repair_option_generator` | Default deterministic; only model-based if an injected Slack LLM client is provided |
| `atomic_card_extractor` | Deterministic rule compiler by default; optional broad compiler LLM fallback, not a separate role |
| `entity_mention_extractor` | Deterministic from compiled card entities by default; optional broad compiler fallback |
| `relationship_extractor` | Deterministic from rule compiler by default; optional broad compiler fallback |
| `open_loop_detector` | Deterministic rules |
| `table_policy_handler` | Deterministic table handling |
| `source_takeaway_extractor` | Deterministic source summary/card creation by default; optional broad compiler fallback |
| `entity_candidate_ranker` | Not a runtime model role; entity resolution is deterministic |
| `entity_final_resolver` | Deterministic |
| `conflict_candidate_detector` | Deterministic duplicate/regex conflict detection |
| `conflict_explainer` | Not model-backed at runtime |
| `conflict_policy_decider` | Deterministic code / explicit user action |
| `recall_planner` | Deterministic mode inference |
| `recall_filter` | Deterministic status filtering |
| `recall_synthesizer` | Deterministic templated rendering |
| `debug_explainer` | Deterministic DB inspection at runtime |
| `eval_judge` | Model-based in eval tooling only |
| `embeddings` | Embedding-model based when vector/Cognee paths are used |

## Fine-Grained Role Topology

### Legend

- **model** (blue) — fine-grained role backed by an LLM
- **det** (green) — deterministic policy / validator
- **solid arrows** — intended information flow between coarse capabilities
- **dotted arrows** — intended ordering inside a coarse capability
- **dashed arrows** — out-of-band / supporting roles

Source of truth: `brain_model_registry.yaml` (`fine_grained_capabilities`,
lines 71-145).

```mermaid
flowchart LR
    classDef model fill:#dbeafe,stroke:#1d4ed8,color:#0b1f4a;
    classDef det   fill:#dcfce7,stroke:#15803d,color:#08331a;
    classDef store fill:#f3f4f6,stroke:#374151,color:#111827;
    classDef ext   fill:#fef3c7,stroke:#a16207,color:#3f2d05;

    INPUT[/"External input<br/>Slack · HTTP · Source URL"/]:::ext

    subgraph ROUTER["router"]
        intent_router[intent_router]:::model
    end

    subgraph SLACK["slack_intake"]
        direction TB
        sl_source_classifier[source_classifier]:::model
        sl_durability_filter[durability_filter]:::model
        sl_memory_kind_classifier[memory_kind_classifier]:::model
        sl_repair_option_generator[repair_option_generator]:::model
        sl_zero_tolerance_validator[zero_tolerance_validator]:::det
        sl_commit_policy[commit_policy]:::det
        sl_success_receipt_template[success_receipt_template]:::det
        sl_source_classifier -.-> sl_durability_filter -.-> sl_memory_kind_classifier -.-> sl_repair_option_generator -.-> sl_zero_tolerance_validator -.-> sl_commit_policy -.-> sl_success_receipt_template
    end

    subgraph COMPILER["memory_compiler"]
        direction TB
        mc_source_loader[source_loader]:::det
        mc_table_parser[table_parser]:::det
        mc_atomic_card_extractor[atomic_card_extractor]:::model
        mc_entity_mention_extractor[entity_mention_extractor]:::model
        mc_relationship_extractor[relationship_extractor]:::model
        mc_open_loop_detector[open_loop_detector]:::model
        mc_table_policy_handler[table_policy_handler]:::model
        mc_source_takeaway_extractor[source_takeaway_extractor]:::model
        mc_zero_tolerance_validator[zero_tolerance_validator]:::det
        mc_source_loader -.-> mc_table_parser -.-> mc_atomic_card_extractor -.-> mc_entity_mention_extractor -.-> mc_relationship_extractor -.-> mc_open_loop_detector -.-> mc_table_policy_handler -.-> mc_source_takeaway_extractor -.-> mc_zero_tolerance_validator
    end

    subgraph ENTITY["entity_resolution"]
        direction TB
        er_entity_mention_extractor[entity_mention_extractor]:::model
        er_entity_candidate_ranker[entity_candidate_ranker]:::model
        er_entity_final_resolver[entity_final_resolver]:::det
        er_entity_mention_extractor -.-> er_entity_candidate_ranker -.-> er_entity_final_resolver
    end

    subgraph CONFLICT["conflict_handling"]
        direction TB
        ch_conflict_candidate_detector[conflict_candidate_detector]:::model
        ch_conflict_explainer[conflict_explainer]:::model
        ch_conflict_policy_decider[conflict_policy_decider]:::det
        ch_conflict_candidate_detector -.-> ch_conflict_explainer -.-> ch_conflict_policy_decider
    end

    subgraph RECALL["recall"]
        direction TB
        rc_recall_planner[recall_planner]:::model
        rc_recall_filter[recall_filter]:::det
        rc_recall_synthesizer[recall_synthesizer]:::model
        rc_recall_planner -.-> rc_recall_filter -.-> rc_recall_synthesizer
    end

    subgraph DEBUG["debug"]
        debug_explainer[debug_explainer]:::model
    end

    subgraph EMBED["embeddings"]
        embeddings[embeddings]:::model
    end

    subgraph JUDGE["judge (offline)"]
        eval_judge[eval_judge]:::model
    end

    DB[("Brain DB + Cognee store")]:::store
    USER[/"User<br/>(asks · confirms · sees receipts)"/]:::ext

    INPUT --> ROUTER
    ROUTER -- "intent: ingest (slack)" --> SLACK
    ROUTER -- "intent: ingest (source)" --> COMPILER
    ROUTER -- "intent: recall" --> RECALL
    ROUTER -- "intent: debug/admin" --> DEBUG

    SLACK -- "approved memory cards" --> ENTITY
    COMPILER -- "extracted cards + mentions" --> ENTITY
    ENTITY -- "resolved entity links" --> CONFLICT
    CONFLICT -- "commit / supersede / merge" --> DB

    SLACK -. "ask / clarify" .-> USER
    CONFLICT -. "confirm conflict resolution" .-> USER
    SLACK -. "success receipt" .-> USER

    RECALL <-- "query · filtered candidates" --> DB
    RECALL -- "grounded answer" --> USER

    DEBUG <-- "inspect state · plans" --> DB
    DEBUG -- "operator output" --> USER

    EMBED -. "vectors" .-> DB
    JUDGE -. "offline scoring" .-> DB
```

### How to Read the Topology

1. **This is a registry/eval topology.** The diagram shows how coarse
   capabilities decompose into fine-grained roles for model evaluation and
   deployment decisions. It should not be read as the exact runtime call graph.
2. **The intended pattern is model proposes, deterministic policy enforces.**
   Fine-grained model roles recommend extraction, classification, or synthesis;
   deterministic roles validate or gate the result.
3. **Ingestion capabilities conceptually converge.** In this topology,
   `slack_intake` and `memory_compiler` produce candidate memory cards and
   entity mentions, which flow through `entity_resolution` and then
   `conflict_handling`.
4. **Recall is represented as planner/filter/synthesizer.** In current runtime
   this is deterministic mode inference, deterministic filtering, and templated
   answer rendering.
5. **User loop.** The user is involved at three points: clarification
   (`repair_option_generator`), conflict confirmation, and final receipts /
   answers.
6. **Out-of-band.** `embeddings` supplies vectors to the store when projection
   paths are enabled; `judge` runs offline against eval fixtures and is not on
   the normal runtime path.

### Coarse → fine-grained mapping (canonical)

| Coarse role        | Model roles                                                                                                                     | Deterministic roles                                                       |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| router             | intent_router                                                                                                                   | —                                                                         |
| slack_intake       | source_classifier, durability_filter, memory_kind_classifier, repair_option_generator                                           | zero_tolerance_validator, commit_policy, success_receipt_template         |
| memory_compiler    | atomic_card_extractor, entity_mention_extractor, relationship_extractor, open_loop_detector, table_policy_handler, source_takeaway_extractor | table_parser, source_loader, zero_tolerance_validator         |
| entity_resolution  | entity_mention_extractor, entity_candidate_ranker                                                                               | entity_final_resolver                                                     |
| conflict_handling  | conflict_candidate_detector, conflict_explainer                                                                                 | conflict_policy_decider                                                   |
| recall             | recall_planner, recall_synthesizer                                                                                              | recall_filter                                                             |
| debug              | debug_explainer                                                                                                                 | —                                                                         |
| judge (offline)    | eval_judge                                                                                                                      | —                                                                         |
| embeddings         | embeddings                                                                                                                      | —                                                                         |
