# Scenario 01 — Implementation

## Project Structure

```
src/
├── __init__.py
├── orchestrator.py      # LangGraph graph definition
├── agents.py            # Agent definitions
├── mcp_server.py        # MCP server implementation
├── models.py            # Pydantic schemas
├── tools.py             # Tool implementations
├── session_store.py     # DynamoDB session manager
├── config.py            # Configuration
├── main.py              # CLI entry point
└── tests/
    ├── __init__.py
    └── test_agents.py
pyproject.toml
```

## Core Implementation Details

### LangGraph Graph (`src/orchestrator.py`)

The orchestrator defines a state graph with the following nodes:

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional, Annotated
import operator

class AgentState(TypedDict):
    query: str
    client_id: str
    session_id: str
    plan: Optional[List[dict]]
    worker_outputs: Annotated[List[dict], operator.add]
    synthesis: Optional[str]
    critique: Optional[dict]
    final_output: Optional[str]
    max_retries: int

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("parse_query", parse_query)
    graph.add_node("plan_tasks", plan_tasks)
    graph.add_node("dispatch_workers", dispatch_workers)
    graph.add_node("synthesize", synthesize)
    graph.add_node("reflect", reflect)
    graph.add_node("rewrite", rewrite)
    graph.add_node("finalize", finalize)

    graph.add_conditional_edges(
        "dispatch_workers",
        lambda state: "synthesize" if all(
            "complete" in w for w in state["worker_outputs"]
        ) else "dispatch_workers"
    )

    graph.add_conditional_edges(
        "reflect",
        lambda state: "finalize" if state["critique"]["passed"] else "rewrite"
    )

    graph.add_edge("rewrite", "reflect")

    graph.set_entry_point("parse_query")
    graph.set_finish_point("finalize")

    return graph.compile()
```

### Supervisor Agent (`src/agents.py`)

```python
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from .models import TaskPlan, WorkerOutput, CritiqueResult
from .config import settings

llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=0.1,
    max_tokens=4096,
    api_key=settings.ANTHROPIC_API_KEY,
)

def parse_query(state: AgentState) -> AgentState:
    messages = [
        SystemMessage(
            content="You are a brand intelligence analyst. Parse the user's query "
                    "into structured fields: brands mentioned, time period, analysis type."
        ),
        HumanMessage(content=state["query"]),
    ]
    response = llm.invoke(messages)
    state["parsed_query"] = {"raw": state["query"], "analysis": response.content}
    return state

def plan_tasks(state: AgentState) -> AgentState:
    messages = [
        SystemMessage(
            content="Decompose the analysis into 2-3 parallel tasks. "
                    "Each task must specify: worker_type, tool_needed, parameters."
        ),
        HumanMessage(content=str(state["parsed_query"])),
    ]
    response = llm.with_structured_output(TaskPlan).invoke(messages)
    state["plan"] = response.tasks
    return state
```

### Worker Agents

```python
def dispatch_workers(state: AgentState) -> AgentState:
    worker_map = {
        "brand_sentiment": BrandSentimentWorker,
        "competitor_positioning": CompetitorPositioningWorker,
        "trend_analysis": TrendAnalysisWorker,
    }

    results = []
    for task in state["plan"]:
        worker_class = worker_map.get(task["worker_type"])
        if worker_class:
            worker = worker_class(llm=llm)
            result = worker.run(task, state["session_id"])
            results.append(result)

    state["worker_outputs"] = results
    return state
```

### Reflection Loop

```python
def reflect(state: AgentState) -> AgentState:
    messages = [
        SystemMessage(
            content="Critique the synthesis. Check for: "
                    "1) Factual accuracy 2) Completeness 3) Consistency. "
                    "Output a pass/fail with specific improvement points."
        ),
        HumanMessage(content=state["synthesis"]),
    ]
    critique = llm.with_structured_output(CritiqueResult).invoke(messages)
    state["critique"] = critique.dict()
    return state

def rewrite(state: AgentState) -> AgentState:
    messages = [
        SystemMessage(
            content=f"Rewrite the synthesis addressing these issues: "
                    f"{state['critique']['issues']}"
        ),
        HumanMessage(content=state["synthesis"]),
    ]
    response = llm.invoke(messages)
    state["synthesis"] = response.content
    state["max_retries"] -= 1
    return state
```

### MCP Server (`src/mcp_server.py`)

```python
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from typing import Any

server = Server("AGENTICOPS-mcp-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_news",
            description="Search news articles for brand mentions and sentiment",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "date_from": {"type": "string"},
                    "date_to": {"type": "string"},
                    "max_results": {"type": "integer", "default": 10},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="fetch_competitor_data",
            description="Fetch competitor positioning, market share, and recent moves",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"},
                    "industry": {"type": "string"},
                },
                "required": ["company_name"],
            },
        ),
        types.Tool(
            name="fetch_social_mentions",
            description="Fetch social media mentions for a brand",
            inputSchema={
                "type": "object",
                "properties": {
                    "brand": {"type": "string"},
                    "platform": {
                        "type": "string",
                        "enum": ["twitter", "reddit", "news"],
                    },
                    "max_results": {"type": "integer", "default": 20},
                },
                "required": ["brand"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name == "search_news":
        results = await search_news_impl(arguments)
        return [types.TextContent(type="text", text=str(results))]
    elif name == "fetch_competitor_data":
        results = await fetch_competitor_data_impl(arguments)
        return [types.TextContent(type="text", text=str(results))]
    elif name == "fetch_social_mentions":
        results = await fetch_social_mentions_impl(arguments)
        return [types.TextContent(type="text", text=str(results))]
    raise ValueError(f"Unknown tool: {name}")
```

### Structured Output Schemas (`src/models.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class TaskPlan(BaseModel):
    tasks: List[dict] = Field(
        description="List of tasks, each with worker_type, tool_needed, parameters"
    )
    reasoning: str = Field(description="Why this decomposition was chosen")

class WorkerOutput(BaseModel):
    worker_type: str
    status: Literal["complete", "error", "timeout"]
    findings: dict
    sources_used: List[str]
    confidence_score: float = Field(ge=0.0, le=1.0)
    raw_data: Optional[dict] = None

class CritiqueResult(BaseModel):
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    issues: List[str]
    suggestions: List[str]

class BrandAnalysis(BaseModel):
    brand: str
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    sentiment_label: Literal["positive", "neutral", "negative"]
    trend_direction: Literal["improving", "declining", "stable"]
    key_drivers: List[str]
    competitor_comparison: Optional[dict] = None
    confidence: float = Field(ge=0.0, le=1.0)
```

### Session Store (`src/session_store.py`)

```python
import boto3
import json
import os
from datetime import datetime, timedelta
from typing import Optional
from .models import BrandAnalysis

dynamodb = boto3.resource("dynamodb")
table_name = os.getenv("SESSION_TABLE", "AGENTICOPS-sessions-01")
table = dynamodb.Table(table_name)


class SessionStore:
    TTL_HOURS = 1

    @staticmethod
    def create_session(client_id: str) -> dict:
        session_id = f"sess_{client_id}_{int(datetime.utcnow().timestamp())}"
        item = {
            "session_id": session_id,
            "client_id": client_id,
            "created_at": datetime.utcnow().isoformat(),
            "ttl": int((datetime.utcnow() + timedelta(hours=SessionStore.TTL_HOURS)).timestamp()),
            "state": "active",
            "events": [],
        }
        table.put_item(Item=item)
        return item

    @staticmethod
    def append_event(session_id: str, event: dict):
        table.update_item(
            Key={"session_id": session_id},
            UpdateExpression="SET #evts = list_append(if_not_exists(#evts, :empty), :event)",
            ExpressionAttributeNames={"#evts": "events"},
            ExpressionAttributeValues={":event": [event], ":empty": []},
        )

    @staticmethod
    def get_session(session_id: str) -> Optional[dict]:
        response = table.get_item(Key={"session_id": session_id})
        return response.get("Item")

    @staticmethod
    def save_analysis(session_id: str, analysis: BrandAnalysis):
        table.update_item(
            Key={"session_id": session_id},
            UpdateExpression="SET analysis = :analysis, #st = :status, updated_at = :now",
            ExpressionAttributeNames={"#st": "state"},
            ExpressionAttributeValues={
                ":analysis": analysis.model_dump(),
                ":status": "completed",
                ":now": datetime.utcnow().isoformat(),
            },
        )
```

### CLI Entry Point (`src/main.py`)

```python
import argparse
import asyncio
from .orchestrator import build_graph
from .session_store import SessionStore
from .config import settings


def main():
    parser = argparse.ArgumentParser(description="AgenticOps Brand Intelligence Agent")
    parser.add_argument("--query", "-q", required=True, help="Analysis query")
    parser.add_argument("--client-id", default="demo-client")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    session = SessionStore.create_session(args.client_id)
    graph = build_graph()

    initial_state = {
        "query": args.query,
        "client_id": args.client_id,
        "session_id": session["session_id"],
        "max_retries": 2,
    }

    result = graph.invoke(initial_state)
    print("\n" + "=" * 60)
    print("BRAND ANALYSIS RESULT")
    print("=" * 60)
    print(result["final_output"])


if __name__ == "__main__":
    main()
```

### Configuration (`src/config.py`)

```python
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    session_table: str = "AGENTICOPS-sessions-01"
    artifact_bucket: str = "AGENTICOPS-artifacts-01"
    log_level: str = "INFO"
    graph_timeout_seconds: int = 60
    worker_timeout_seconds: int = 30
    max_reflection_retries: int = 2

    class Config:
        env_prefix = "AGENTICOPS_"


settings = Settings()
```

### pyproject.toml

```toml
[project]
name = "AGENTICOPS-orchestrator"
version = "0.1.0"
description = "AgenticOps Multi-Agent Orchestrator"
requires-python = ">=3.11"
dependencies = [
    "langgraph>=0.4.0",
    "langchain-anthropic>=0.3.0",
    "langchain-openai>=0.3.0",
    "langchain-core>=0.3.0",
    "mcp>=1.0.0",
    "boto3>=1.35.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "httpx>=0.28.0",
]

[project.scripts]
AGENTICOPS-orchestrator = "AGENTICOPS_orchestrator.main:main"

[build-system]
requires = ["setuptools>=75.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
```

### Tests (`src/tests/test_agents.py`)

```python
import pytest
from AGENTICOPS_orchestrator.models import TaskPlan, WorkerOutput, CritiqueResult, BrandAnalysis


class TestModels:
    def test_brand_analysis_valid(self):
        analysis = BrandAnalysis(
            brand="Nike",
            sentiment_score=0.75,
            sentiment_label="positive",
            trend_direction="improving",
            key_drivers=["Olympic campaigns", "new product launches"],
            confidence=0.85,
        )
        assert analysis.sentiment_label == "positive"

    def test_brand_analysis_score_range(self):
        with pytest.raises(ValueError):
            BrandAnalysis(
                brand="Nike",
                sentiment_score=1.5,
                sentiment_label="positive",
                trend_direction="improving",
                key_drivers=[],
                confidence=0.85,
            )

    def test_worker_output_status(self):
        with pytest.raises(ValueError):
            WorkerOutput(
                worker_type="brand_sentiment",
                status="unknown",
                findings={},
                sources_used=[],
                confidence_score=0.5,
            )


@pytest.mark.asyncio
class TestSessionStore:
    async def test_create_session(self):
        store = SessionStore()
        session = store.create_session("test-client")
        assert session["client_id"] == "test-client"
        assert session["state"] == "active"
