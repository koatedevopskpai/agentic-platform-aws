# Scenario 01 — Architecture Decision Records

## ADR-001: Supervisor/Worker vs Planner/Executor Topology

| Attribute | Detail |
|-----------|--------|
| **Status** | Accepted |
| **Context** | Need to choose agent topology for brand intelligence analyses |
| **Options** | Supervisor/Worker, Planner/Executor, Single Agent |

**Supervisor/Worker** selected because:
- Tasks are heterogeneous (sentiment, competitors, trends) requiring different tools
- Workers can execute in parallel, reducing latency
- Supervisor can dynamically assign tasks based on query complexity
- Easier to observe and debug per-worker behavior

## ADR-002: LangGraph vs Custom Orchestrator

| Attribute | Detail |
|-----------|--------|
| **Status** | Accepted |
| **Context** | Framework choice for agent graph execution |
| **Options** | LangGraph, Custom Python orchestrator, Semantic Kernel |

**LangGraph** selected because:
- First-class support for cycles (essential for reflection loop)
- Built-in state management with TypedDict schemas
- LangChain integration for provider-agnostic LLM calls
- Community maturity and documentation
- Easy to trace and debug with LangSmith

## ADR-003: MCP Server vs Direct Tool Functions

| Attribute | Detail |
|-----------|--------|
| **Status** | Accepted |
| **Context** | How to expose tools to agents |
| **Options** | MCP Server, LangChain tools, Direct function calls |

**MCP Server** selected because:
- Standardized protocol for tool discovery and execution
- Decouples tool implementation from agent framework
- Tools can be independently deployed (Lambda) and scaled
- MCP is becoming industry standard for agent interoperability
- Easy to extend with new tools without agent code changes

## ADR-004: Provider Selection Per Agent Role

| Agent Role | Primary Provider | Rationale |
|------------|-----------------|-----------|
| **Supervisor** (planning, routing) | Claude Sonnet 4 | Best-in-class structured output, low hallucination, fast |
| **Worker** (research, extraction) | GPT-4o | Strong at extraction, tool use, lower cost than Opus |
| **Reflection** (critique) | Claude Opus 4.5 | Highest reasoning accuracy; critique requires careful judgment |
| **Rewrite** | Claude Sonnet 4 | Good balance of quality and cost for rewrite |

## ADR-005: Structured Output Strategy

| Attribute | Detail |
|-----------|--------|
| **Status** | Accepted |
| **Context** | Ensuring parseable outputs at every LLM boundary |
| **Decision** | Pydantic models with `with_structured_output()` and JSON mode |
| **Rationale** | Pydantic provides type safety, validation, and serialization. LangChain's `with_structured_output` handles prompt engineering for JSON generation |
| **Fallback** | Raw JSON parsing with retry on failure |
