# Role Flow Diagram — Coarse & Fine-Grained Roles

This diagram shows how information and decisions flow through Brain's role
system. Each **coarse role** is a top-level capability (subgraph) composed of
**fine-grained roles** that either run an LLM (`model`) or apply policy
deterministically (`det`). The recurring pattern within every coarse role is:
model roles **recommend**, deterministic roles **validate / enforce**.

Source of truth: `brain_model_registry.yaml` (`fine_grained_capabilities`,
lines 71-145).

## Legend

- **model** (blue) — fine-grained role backed by an LLM
- **det** (green) — deterministic policy / validator
- **solid arrows** — primary information flow between coarse roles
- **dotted arrows** — internal ordering inside a coarse role
- **dashed arrows** — out-of-band / supporting roles

## End-to-end flow

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

## How to read this

1. **Router fans out.** The single LLM role `intent_router` decides whether
   the request is a Slack memory commit, a long-form source ingestion, a
   recall query, or a debug request, and dispatches accordingly.
2. **Ingestion paths converge.** Both `slack_intake` and `memory_compiler`
   produce candidate memory cards and entity mentions, which flow through
   `entity_resolution` and then `conflict_handling` before any write to the
   Brain DB / Cognee store.
3. **Model recommends, deterministic enforces.** Within each coarse role the
   dotted arrows show the order of execution: LLM-backed roles run first to
   propose extractions / classifications, and deterministic roles
   (`zero_tolerance_validator`, `commit_policy`, `entity_final_resolver`,
   `conflict_policy_decider`, `recall_filter`) gate the result before it
   leaves the coarse role.
4. **Recall reads, never writes.** `recall` queries the store, runs the
   deterministic `recall_filter` to drop deleted/superseded records, then
   `recall_synthesizer` produces the grounded answer.
5. **User loop.** The user is involved at three points: clarification
   (`repair_option_generator`), conflict confirmation, and final receipts /
   answers.
6. **Out-of-band.** `embeddings` supplies vectors to the store; `judge` runs
   offline against eval fixtures and is not on the runtime path.

## Coarse → fine-grained mapping (canonical)

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
