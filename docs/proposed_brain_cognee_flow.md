# Proposed Brain/Cognee Flow

This diagram shows the proposed narrower split after comparing Brain with Cognee's native information flow.

Brain becomes the policy, profile, bias, and session facade. Cognee becomes the canonical semantic memory substrate for durable memory, source ingestion, entity/relationship graph, vector retrieval, session memory, and graph improvement. Brain keeps only the control-plane state that Cognee does not model as application policy.

## Data Ingestion / Write Flow

```mermaid
flowchart TD
    classDef client fill:#fef3c7,stroke:#a16207,color:#3f2d05;
    classDef brain fill:#dcfce7,stroke:#15803d,color:#08331a;
    classDef policy fill:#e0f2fe,stroke:#0369a9,color:#082f49;
    classDef store fill:#ede9fe,stroke:#6d28d9,color:#241044;
    classDef cognee fill:#f3f4f6,stroke:#374151,color:#111827;
    classDef palate fill:#fce7f3,stroke:#be185d,color:#500724;
    classDef guard fill:#fee2e2,stroke:#b91c1c,color:#450a0a;

    subgraph CLIENTS[Clients and operators]
        REST[REST callers]:::client
        MCP[HTTP and stdio MCP tools]:::client
        APP[Browser app and ChatGPT app]:::client
        OPS[Scripts and maintenance jobs]:::client
    end

    subgraph BRAIN[Brain ingestion policy facade]
        INGRESS[Ingress adapters<br/>REST, MCP, app, scripts]:::brain
        AUTH[Auth, scopes, rate limits,<br/>surface-specific permissions]:::policy
        CONTEXT[Resolve context<br/>user, profile, bias, session_id,<br/>dataset and node-set scope]:::brain
        ROUTER[Tool and intent router]:::brain
        WRITEPOLICY[Write policy<br/>durability, safety, dry-run,<br/>confirmation, receipt shape]:::guard
        PROFILEBIAS[Profile and bias manager]:::brain
        PALATE[Palate policy<br/>normalize, enrich, rank,<br/>proposal gate, decision feedback]:::palate
    end

    subgraph BRAINCTRL[Small Brain control store]
        CONTROL[(Control DB / files<br/>users, profile context, bias context,<br/>session map, pending confirmations,<br/>app write audit, external receipts)]:::store
    end

    subgraph COGNEE[Cognee semantic memory substrate]
        CAPI[Cognee write APIs<br/>remember, add, cognify,<br/>improve]:::cognee
        CDATA[(Cognee relational DB<br/>datasets, data, ACLs,<br/>pipeline status, query logs,<br/>session records, node/edge mirror)]:::store
        FILES[(Raw and converted file storage)]:::store
        GRAPH[(Graph engine<br/>entities, relationships,<br/>datapoints, triplets)]:::store
        VECTOR[(Vector engine<br/>chunks, summaries,<br/>datapoints, triplets)]:::store
        SESSION[(Cognee session cache<br/>QA, trace, feedback,<br/>graph context snapshots)]:::store
    end

    REST --> INGRESS
    MCP --> INGRESS
    APP --> INGRESS
    OPS --> INGRESS

    INGRESS --> AUTH
    AUTH --> CONTEXT
    CONTEXT --> CONTROL
    CONTEXT --> ROUTER

    ROUTER -- profile or bias update --> PROFILEBIAS
    PROFILEBIAS --> CONTROL
    PROFILEBIAS -. optional searchable projection .-> CAPI

    ROUTER -- ordinary memory or source --> WRITEPOLICY
    WRITEPOLICY -- needs user decision --> CONTROL
    WRITEPOLICY -- approved typed datapoint or source --> CAPI

    ROUTER -- palate memory or recommendation --> PALATE
    PALATE --> CONTROL
    PALATE -- TasteItem, TasteSignal,<br/>TasteDecision datapoints --> CAPI

    CAPI -- permanent memory build --> CDATA
    CAPI -- source input --> FILES
    CAPI -- graph extraction<br/>custom DataPoints --> GRAPH
    CAPI -- embeddings --> VECTOR
    CAPI -- session_id writes/recall --> SESSION
    CAPI -- improve --> GRAPH
    CAPI -- improve --> VECTOR
    CAPI -- improve/session bridge --> SESSION

    CDATA --> GRAPH
    CDATA --> VECTOR
    FILES --> CDATA

    CAPI --> WRESULT[Cognee write results<br/>RememberResult, DataPoint IDs,<br/>dataset and pipeline state]:::cognee
    WRESULT --> RECEIPT[Brain receipt<br/>surface-specific summary,<br/>warnings, confirmation state]:::brain
    RECEIPT --> CLIENTS
```

## Data Recall / Read Flow

```mermaid
flowchart TD
    classDef client fill:#fef3c7,stroke:#a16207,color:#3f2d05;
    classDef brain fill:#dcfce7,stroke:#15803d,color:#08331a;
    classDef policy fill:#e0f2fe,stroke:#0369a9,color:#082f49;
    classDef store fill:#ede9fe,stroke:#6d28d9,color:#241044;
    classDef cognee fill:#f3f4f6,stroke:#374151,color:#111827;
    classDef palate fill:#fce7f3,stroke:#be185d,color:#500724;

    subgraph CLIENTS[Clients and operators]
        REST[REST callers]:::client
        MCP[HTTP and stdio MCP tools]:::client
        APP[Browser app and ChatGPT app]:::client
        OPS[Scripts and maintenance jobs]:::client
    end

    subgraph BRAIN[Brain recall policy facade]
        INGRESS[Ingress adapters<br/>REST, MCP, app, scripts]:::brain
        AUTH[Auth, scopes, rate limits,<br/>surface-specific permissions]:::policy
        CONTEXT[Resolve context<br/>user, profile, bias, session_id,<br/>dataset and node-set scope]:::brain
        ROUTER[Tool and intent router]:::brain
        READPOLICY[Read policy<br/>scope, status visibility,<br/>grounding, response format]:::policy
        PALATERANK[Palate ranking policy<br/>option constraints, negative signals,<br/>decision feedback]:::palate
        MAINTREAD[Admin/review read policy<br/>receipts, pending confirmations,<br/>audit, compatibility state]:::policy
    end

    subgraph BRAINCTRL[Small Brain control store]
        CONTROL[(Control DB / files<br/>users, profile context, bias context,<br/>session map, pending confirmations,<br/>app write audit, external receipts)]:::store
    end

    subgraph COGNEE[Cognee semantic memory substrate]
        CAPI[Cognee read APIs<br/>recall, search,<br/>session lookup]:::cognee
        CDATA[(Cognee relational DB<br/>datasets, data, ACLs,<br/>query logs, session records,<br/>node/edge mirror)]:::store
        GRAPH[(Graph engine<br/>entities, relationships,<br/>datapoints, triplets)]:::store
        VECTOR[(Vector engine<br/>chunks, summaries,<br/>datapoints, triplets)]:::store
        SESSION[(Cognee session cache<br/>QA, trace, feedback,<br/>graph context snapshots)]:::store
    end

    REST --> INGRESS
    MCP --> INGRESS
    APP --> INGRESS
    OPS --> INGRESS

    INGRESS --> AUTH
    AUTH --> CONTEXT
    CONTEXT --> CONTROL
    CONTEXT --> ROUTER

    ROUTER -- profile, bias,<br/>pending confirmation,<br/>receipt or audit lookup --> MAINTREAD
    MAINTREAD --> CONTROL
    MAINTREAD --> CONTROLANSWER[Control-store answer<br/>profile, bias, receipt,<br/>review/admin payload]:::brain

    ROUTER -- palate recommendation<br/>or option evaluation --> PALATERANK
    PALATERANK --> CONTROL
    PALATERANK -- scoped palate recall/search --> CAPI

    ROUTER -- memory recall,<br/>source QA, semantic search --> READPOLICY
    READPOLICY --> CONTROL
    READPOLICY -- scoped recall/search<br/>with user, profile, bias,<br/>session_id, node sets --> CAPI

    CAPI --> SCOPE{Retrieval scope}:::cognee
    SCOPE -- session --> SESSION
    SCOPE -- chunks and summaries --> VECTOR
    SCOPE -- graph completion,<br/>Cypher, temporal --> GRAPH
    SCOPE -- dataset metadata,<br/>query/result logs --> CDATA

    SESSION --> CRESULT[Cognee recall/search results]:::cognee
    VECTOR --> CRESULT
    GRAPH --> CRESULT
    CDATA --> CRESULT

    CRESULT --> READPOLICY
    CRESULT --> PALATERANK
    PALATERANK --> ANSWER[User answer, ranked options,<br/>evidence, or recommendation]:::brain
    READPOLICY --> ANSWER
    CONTROLANSWER --> ANSWER
    ANSWER --> CLIENTS
```

## Ownership Split

- **Brain owns context and policy:** user/session/profile resolution, bias context, app surface rules, dry-run and confirmation state, safety gates, response shape, app write audit, and user-visible maintenance decisions.
- **Cognee owns semantic memory:** source ingestion, dataset/data records, graph construction, vector indexing, entity/relationship retrieval, session cache, query logs, improvement, and deletion/reset of semantic memory.
- **Palate remains policy-heavy:** Brain keeps taste normalization, enrichment choices, ranking policy, option constraints, and decision feedback logic; Cognee stores/searches typed palate datapoints.
- **Profile and bias stay in Brain first:** They live in the control store because they shape routing and prompting. Brain can also project them to Cognee as typed datapoints when they should be semantically searchable.
- **No broad Brain memory mirror:** Brain should avoid rebuilding `memory_cards`, `entities`, `relationships`, source text storage, and broad recall logs as a second semantic database. Stable external IDs and receipts can be stored as lightweight control state or embedded in Cognee datapoints.

## Write Path

1. A client calls Brain through REST, MCP, the app, or a script.
2. Brain authenticates the caller and resolves user, profile, bias, session, dataset, and node-set scope.
3. Brain applies write policy. Uncertain or destructive writes become pending confirmations in the control store.
4. Approved ordinary memory/source writes go to Cognee as typed datapoints or source inputs.
5. Cognee stores the data, builds chunks, graph nodes/edges, summaries, embeddings, and queryable dataset state.
6. Brain returns a receipt shaped for the calling surface.

## Recall Path

1. Brain resolves profile, bias, session, and scope.
2. Brain chooses the read policy: direct control-store lookup, palate ranking, or Cognee recall/search.
3. Cognee returns semantic results from session cache, graph, vector, source chunks, summaries, or specialized retrievers.
4. Brain applies visibility, grounding, and response-format rules.
5. Brain returns an answer, evidence, receipt, or admin/review payload.

## Migration Direction

- Replace raw JSON text projection with typed Cognee datapoints for Brain memory, source chunks, profile context, open loops, status events, and palate records.
- Keep Brain control tables/files small and explicit: profile context, bias context, session map, pending confirmations, app write audit, and compatibility receipts.
- Move durable semantic state out of Brain's parallel `sources`, `memory_cards`, `entities`, `relationships`, `memory_links`, broad `ingestion_runs`, and broad `recall_logs` tables as migration allows.
