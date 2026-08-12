from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Any
from .models import TaskPlan, WorkerOutput, CritiqueResult, ParsedQuery
from .config import settings

sonnet = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=0.1,
    max_tokens=4096,
    api_key=settings.anthropic_api_key,
)

gpt4o = ChatOpenAI(
    model="gpt-4o",
    temperature=0.1,
    max_tokens=4096,
    api_key=settings.openai_api_key,
)

opus = ChatAnthropic(
    model="claude-opus-4-20250514",
    temperature=0.1,
    max_tokens=4096,
    api_key=settings.anthropic_api_key,
)


def parse_query(state: dict) -> dict:
    messages = [
        SystemMessage(
            content="You are a brand intelligence analyst. Parse the user's query into "
            "structured fields: brands mentioned, time period, analysis type. "
            "Analysis types: sentiment, competitor, trend, comprehensive."
        ),
        HumanMessage(content=state["query"]),
    ]
    parsed = sonnet.with_structured_output(ParsedQuery).invoke(messages)
    state["parsed_query"] = parsed.model_dump()
    return state


def plan_tasks(state: dict) -> dict:
    messages = [
        SystemMessage(
            content="Decompose the analysis into parallel tasks. Each task must specify: "
            "worker_type (brand_sentiment, competitor_positioning, trend_analysis), "
            "tool_needed (search_news, fetch_competitor_data, fetch_social_mentions, market_trends), "
            "and parameters. Output 2-3 tasks that can run in parallel."
        ),
        HumanMessage(content=str(state["parsed_query"])),
    ]
    plan = sonnet.with_structured_output(TaskPlan).invoke(messages)
    state["plan"] = plan.tasks
    state["plan_reasoning"] = plan.reasoning
    return state


class BrandSentimentWorker:
    def __init__(self, llm: Any):
        self.llm = llm

    def run(self, task: dict, session_id: str) -> dict:
        messages = [
            SystemMessage(
                content="Analyze brand sentiment from the provided data. "
                "Output a sentiment score (-1 to 1), sentiment label, "
                "trend direction, and key drivers."
            ),
            HumanMessage(content=str(task)),
        ]
        result = self.llm.with_structured_output(WorkerOutput).invoke(messages)
        return result.model_dump()


class CompetitorPositioningWorker:
    def __init__(self, llm: Any):
        self.llm = llm

    def run(self, task: dict, session_id: str) -> dict:
        messages = [
            SystemMessage(
                content="Analyze competitor positioning from the provided data. "
                "Output findings about market position, recent moves, and threats."
            ),
            HumanMessage(content=str(task)),
        ]
        result = self.llm.with_structured_output(WorkerOutput).invoke(messages)
        return result.model_dump()


class TrendAnalysisWorker:
    def __init__(self, llm: Any):
        self.llm = llm

    def run(self, task: dict, session_id: str) -> dict:
        messages = [
            SystemMessage(
                content="Analyze market trends from the provided data. "
                "Identify emerging patterns, shifts in consumer behavior, and industry movements."
            ),
            HumanMessage(content=str(task)),
        ]
        result = self.llm.with_structured_output(WorkerOutput).invoke(messages)
        return result.model_dump()
