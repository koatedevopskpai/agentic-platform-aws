# Scenario 01 — Architecture Design

## Agent Topology

```mermaid
graph TD
    USER[User Query] --> SUP[Supervisor Agent]
    
    subgraph Supervisor
        SUP --> PLAN[Task Planner]
        PLAN --> DISPATCH[Task Dispatcher]
    end
    
    subgraph Worker Pool
        DISPATCH --> W1[Brand Sentiment Worker]
        DISPATCH --> W2[Competitor Positioning Worker]
        DISPATCH --> W3[Trend Analysis Worker]
    end
    
    W1 --> MCP1[MCP: search_news]
    W1 --> MCP2[MCP: fetch_social_mentions]
    W2 --> MCP3[MCP: fetch_competitor_data]
    W3 --> MCP4[MCP: search_news]
    W3 --> MCP5[MCP: market_trends]
    
    W1 --> SYNTH[Synthesis]
    W2 --> SYNTH
    W3 --> SYNTH
    
    SYNTH --> REF[Reflection Agent]
    REF --> CRITIQUE{Critique Pass?}
    CRITIQUE -->|No| REWRITE[Rewrite]
    REWRITE --> REF
    CRITIQUE -->|Yes| OUT[Final Response]
    
    OUT --> USER
```

## LangGraph State Graph

```mermaid
stateDiagram-v2
    [*] --> ParseQuery
    ParseQuery --> PlanTasks
    PlanTasks --> DispatchWorkers
    DispatchWorkers --> BrandSentiment
    DispatchWorkers --> CompetitorPositioning
    DispatchWorkers --> TrendAnalysis
    BrandSentiment --> Synthesize
    CompetitorPositioning --> Synthesize
    TrendAnalysis --> Synthesize
    Synthesize --> Reflect
    Reflect --> Rewrite: critique fails
    Reflect --> Finalize: critique passes
    Rewrite --> Reflect
    Finalize --> [*]
```

## Component Interactions

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   FastAPI App   │────→│  LangGraph Graph │────→│   MCP Server    │
│  (ECS Fargate)  │     │  (Supervisor)    │     │  (Lambda/ECS)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                        │
         ↓                       ↓                        ↓
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  DynamoDB       │     │  S3 Artifact     │     │  CloudWatch     │
│  Session Store  │     │  Store           │     │  Logs & Metrics │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Data Flow

1. **User query received** via API Gateway → ECS Fargate (FastAPI)
2. **Session created** in DynamoDB (TTL: 1h)
3. **Supervisor agent** parses query, plans tasks using Claude Sonnet
4. **Workers dispatched** — each worker runs in a sub-graph with:
   - 30s timeout
   - Tool access scoped to specific MCP functions
   - Structured output schema (Pydantic)
5. **Results synthesized** by supervisor
6. **Reflection loop** evaluates output quality:
   - Factual accuracy check
   - Completeness check against original query
   - Consistency check across sources
7. **Final response** returned to user, stored in S3 artifact store

## Sandboxing Strategy

| Boundary | Mechanism |
|----------|-----------|
| Worker isolation | Each worker runs as separate LangGraph node with isolated state |
| Tool access | Tool-level IAM; workers can only call permitted tools |
| Execution timeout | 30s per worker, 60s total graph timeout |
| Output validation | Pydantic models at every LLM boundary |
| Data access | Client context injected at session start; workers cannot read other sessions |
