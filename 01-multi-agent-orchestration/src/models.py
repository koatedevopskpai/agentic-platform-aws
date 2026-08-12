from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class TaskPlan(BaseModel):
    tasks: List[dict] = Field(
        description="List of tasks, each with worker_type, tool_needed, parameters"
    )
    reasoning: str = Field(
        description="Why this decomposition was chosen"
    )


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


class ParsedQuery(BaseModel):
    brands: List[str]
    time_period: Optional[str] = None
    analysis_type: Literal["sentiment", "competitor", "trend", "comprehensive"]
    additional_focus: Optional[List[str]] = None
