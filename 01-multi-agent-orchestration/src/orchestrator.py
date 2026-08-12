from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional, Annotated
import operator

from .agents import (
    parse_query,
    plan_tasks,
    BrandSentimentWorker,
    CompetitorPositioningWorker,
    TrendAnalysisWorker,
)
from .models import CritiqueResult
from .config import settings
from .session_store import SessionStore

from langchain_anthropic import ChatAnthropic

opus = ChatAnthropic(
    model="claude-opus-4-20250514",
    temperature=0.1,
    max_tokens=4096,
    api_key=settings.anthropic_api_key,
)

sonnet = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=0.1,
    max_tokens=4096,
    api_key=settings.anthropic_api_key,
)


class AgentState(TypedDict):
    query: str
    client_id: str
    session_id: str
    parsed_query: Optional[dict]
    plan: Optional[List[dict]]
    plan_reasoning: Optional[str]
    worker_outputs: Annotated[List[dict], operator.add]
    synthesis: Optional[str]
    critique: Optional[dict]
    final_output: Optional[str]
    max_retries: int
    errors: List[str]


def parse_query_node(state: AgentState) -> AgentState:
    SessionStore.append_event(state["session_id"], {"event": "parse_query", "query": state["query"]})
    return parse_query(state)


def plan_tasks_node(state: AgentState) -> AgentState:
    SessionStore.append_event(state["session_id"], {"event": "plan_tasks", "parsed": state.get("parsed_query")})
    return plan_tasks(state)


def dispatch_workers(state: AgentState) -> AgentState:
    SessionStore.append_event(state["session_id"], {"event": "dispatch_workers"})

    worker_map = {
        "brand_sentiment": BrandSentimentWorker,
        "competitor_positioning": CompetitorPositioningWorker,
        "trend_analysis": TrendAnalysisWorker,
    }

    results = []
    for task in state["plan"]:
        worker_class = worker_map.get(task.get("worker_type"))
        if worker_class:
            worker = worker_class(llm=sonnet)
            try:
                result = worker.run(task, state["session_id"])
                results.append(result)
                SessionStore.append_event(
                    state["session_id"],
                    {"event": "worker_complete", "worker": task.get("worker_type"), "result": result},
                )
            except Exception as e:
                error_result = {
                    "worker_type": task.get("worker_type"),
                    "status": "error",
                    "findings": {},
                    "sources_used": [],
                    "confidence_score": 0.0,
                    "error": str(e),
                }
                results.append(error_result)
                state["errors"].append(str(e))
        else:
            results.append({
                "worker_type": task.get("worker_type", "unknown"),
                "status": "error",
                "findings": {},
                "sources_used": [],
                "confidence_score": 0.0,
                "error": f"Unknown worker type: {task.get('worker_type')}",
            })

    state["worker_outputs"] = results
    return state


def synthesize(state: AgentState) -> AgentState:
    import json

    messages = [
        {
            "role": "system",
            "content": "Synthesize the worker outputs into a coherent brand analysis. "
            "Combine findings from all workers into a structured report. "
            "Include sentiment scores, competitor positioning, and trends. "
            "Cite sources where applicable.",
        },
        {
            "role": "user",
            "content": f"Original query: {state['query']}\n\nWorker outputs: {json.dumps(state['worker_outputs'], indent=2)}",
        },
    ]

    response = opus.invoke(messages)
    state["synthesis"] = response.content

    SessionStore.append_event(
        state["session_id"],
        {"event": "synthesize", "synthesis_length": len(response.content)},
    )
    return state


def reflect(state: AgentState) -> AgentState:
    messages = [
        {
            "role": "system",
            "content": "Critique the synthesis. Evaluate: "
            "1) Factual accuracy - are claims supported by worker data? "
            "2) Completeness - does it fully answer the original query? "
            "3) Consistency - no contradictions across sections. "
            "4) Clarity - is it well-structured and understandable? "
            "Output a pass/fail with specific issues and suggestions.",
        },
        {
            "role": "user",
            "content": f"Original query: {state['query']}\n\nSynthesis: {state['synthesis']}",
        },
    ]

    critique = opus.with_structured_output(CritiqueResult).invoke(messages)
    state["critique"] = critique.model_dump()

    SessionStore.append_event(
        state["session_id"],
        {"event": "reflect", "critique": state["critique"]},
    )
    return state


def rewrite(state: AgentState) -> AgentState:
    messages = [
        {
            "role": "system",
            "content": f"Rewrite the synthesis addressing these issues: {state['critique']['issues']}\n\n"
            f"Suggestions: {state['critique']['suggestions']}\n\n"
            "Improve the analysis based on the critique while maintaining all valid content.",
        },
        {
            "role": "user",
            "content": state["synthesis"],
        },
    ]

    response = opus.invoke(messages)
    state["synthesis"] = response.content
    state["max_retries"] -= 1

    SessionStore.append_event(
        state["session_id"],
        {"event": "rewrite", "retries_left": state["max_retries"]},
    )
    return state


def finalize(state: AgentState) -> AgentState:
    state["final_output"] = state["synthesis"]
    SessionStore.append_event(
        state["session_id"],
        {"event": "finalize", "output_length": len(state["final_output"])},
    )
    return state


def should_continue(state: AgentState) -> str:
    if state.get("critique") and state["critique"].get("passed"):
        return "finalize"
    if state["max_retries"] > 0:
        return "rewrite"
    return "finalize"


def all_workers_complete(state: AgentState) -> str:
    if state.get("worker_outputs") and len(state["worker_outputs"]) == len(state["plan"]):
        return "synthesize"
    return "dispatch_workers"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("parse_query", parse_query_node)
    graph.add_node("plan_tasks", plan_tasks_node)
    graph.add_node("dispatch_workers", dispatch_workers)
    graph.add_node("synthesize", synthesize)
    graph.add_node("reflect", reflect)
    graph.add_node("rewrite", rewrite)
    graph.add_node("finalize", finalize)

    graph.add_edge("parse_query", "plan_tasks")
    graph.add_edge("plan_tasks", "dispatch_workers")
    graph.add_conditional_edges("dispatch_workers", all_workers_complete)
    graph.add_edge("synthesize", "reflect")
    graph.add_conditional_edges("reflect", should_continue)
    graph.add_edge("rewrite", "reflect")
    graph.add_edge("finalize", END)

    graph.set_entry_point("parse_query")

    return graph.compile()


def run_analysis(query: str, client_id: str = "demo-client") -> dict:
    store = SessionStore()
    session = store.create_session(client_id)
    graph = build_graph()

    initial_state: AgentState = {
        "query": query,
        "client_id": client_id,
        "session_id": session["session_id"],
        "parsed_query": None,
        "plan": None,
        "plan_reasoning": None,
        "worker_outputs": [],
        "synthesis": None,
        "critique": None,
        "final_output": None,
        "max_retries": settings.max_reflection_retries,
        "errors": [],
    }

    result = graph.invoke(initial_state)
    return result
