# Scenario 01 — Multi-Agent Orchestration & Topology Design

## Overview

A supervisor/worker agent system that analyses brand sentiment and competitor positioning for AgenticOps customers. Built with LangGraph, this system demonstrates:

- **Supervisor/Worker topology**: Intelligent task decomposition and dispatch
- **MCP server integration**: Custom tools for news search and competitor data
- **Reflection loop**: Self-critique and rewrite before returning to user
- **Sandboxed sub-agents**: Isolated execution with structured outputs
- **Multi-provider LLM routing**: Claude Sonnet (primary), GPT-4o (fallback)

## Quick Start

```bash
cd 01-multi-agent-orchestration
uv sync
# or pip install -e .

# Run the orchestrator
AGENTICOPS-orchestrator --query "Analyze brand sentiment for Nike and compare with Adidas"
```

## Architecture

```
User Query → Supervisor Agent → Worker Agents → Reflection → Response
               ↓                    ↓
         Task Planner      Brand Sentiment Worker
                           Competitor Positioning Worker
                           Trend Analysis Worker
```

## Key Files

| File | Description |
|------|-------------|
| `src/orchestrator.py` | LangGraph graph definition |
| `src/agents.py` | Supervisor, Worker, Reflection agents |
| `src/mcp_server.py` | MCP server with custom tools |
| `src/models.py` | Pydantic structured output schemas |
| `src/tools.py` | Tool implementations |
| `src/session_store.py` | DynamoDB session manager |
| `src/main.py` | CLI entry point |
| `src/tests/test_agents.py` | Agent unit tests |
| `src/pyproject.toml` | Project configuration |

## Deployment

See [deployment.md](deployment.md) for Terraform, AWS CLI, and Console instructions.
