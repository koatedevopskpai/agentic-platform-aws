# Scenario 01 — Multi-Agent Orchestration & Topology Design

## Business Context

AgenticOps's brand analytics platform needs to handle complex multi-step analyses that combine brand sentiment data, competitor positioning, and market trends. Customers want a single query like *"How is Nike's brand sentiment trending this quarter compared to Adidas?"* — and get back a structured, well-reasoned analysis.

A monolithic LLM call produces shallow results. We need an agent system that:
1. Decomposes the query into specialized research tasks
2. Executes them in parallel with appropriate tools
3. Synthesizes findings into a coherent analysis
4. Self-critiques and improves the output before delivery

## User Stories

| ID | User Story | Acceptance Criteria |
|----|-----------|-------------------|
| US-001 | As a brand manager, I want to ask a natural language question about brand sentiment and get a structured analysis | Query decomposed into sub-tasks; final response contains sentiment score, trend direction, key drivers |
| US-002 | As a product manager, I want the system to use live data from news and social sources | Workers call real search APIs; data freshness timestamped |
| US-003 | As a compliance officer, I want to know the system can't leak competitor data | Sub-agents sandboxed with tool-level IAM; no cross-client data access |
| US-004 | As an engineer, I want to see the agent's reasoning trace | Every step logged with tool calls, inputs, outputs |

## Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Task decomposition accuracy | >90% alignment with human breakdown | Manual review of 50 queries |
| Tool call success rate | >95% | Logged tool execution metrics |
| Reflection improvement rate | >60% of outputs improved after reflection | Compare pre/post reflection scores |
| End-to-end latency (p95) | <5s | CloudWatch metrics |
| Structured output parse rate | 100% | Schema validation pass rate |
