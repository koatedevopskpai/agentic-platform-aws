import json
import hashlib
import time
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from .config import settings
from .tracer import tracer


class EvalResult(BaseModel):
    eval_id: str
    prompt_hash: str
    model: str
    dataset_version: str
    dataset_item_id: str
    input: str
    output: str
    judge_score: float = Field(ge=0.0, le=1.0)
    judge_rubric: dict
    latency_ms: float
    cost_usd: float
    token_usage: dict
    guardrail_results: dict
    trace_id: Optional[str] = None
    timestamp: str


class EvalRunner:
    def __init__(self):
        self.judge_llm = ChatAnthropic(
            model="claude-opus-4-20250514",
            temperature=0.0,
            max_tokens=1024,
            api_key=settings.anthropic_api_key,
        )
        self._setup_cost_rates()

    def _setup_cost_rates(self):
        self.cost_per_1k_input = {
            "claude-sonnet-4": 0.003,
            "claude-opus-4.5": 0.015,
            "claude-haiku-3.5": 0.0008,
            "gpt-4o": 0.005,
            "gpt-4o-mini": 0.00015,
        }
        self.cost_per_1k_output = {
            "claude-sonnet-4": 0.015,
            "claude-opus-4.5": 0.075,
            "claude-haiku-3.5": 0.004,
            "gpt-4o": 0.015,
            "gpt-4o-mini": 0.0006,
        }

    def _calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        input_cost = (
            input_tokens / 1000
        ) * self.cost_per_1k_input.get(model, 0.003)
        output_cost = (
            output_tokens / 1000
        ) * self.cost_per_1k_output.get(model, 0.015)
        return round(input_cost + output_cost, 6)

    def _compute_prompt_hash(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]

    @tracer.trace("eval_runner.run")
    async def run_eval(
        self,
        dataset_item: dict,
        prompt_template: str,
        model: str,
        dataset_version: str = "golden_v1",
    ) -> EvalResult:
        model_map = {
            "claude-sonnet-4": lambda: ChatAnthropic(
                model="claude-sonnet-4-20250514",
                temperature=0.1,
                api_key=settings.anthropic_api_key,
            ),
            "claude-haiku-3.5": lambda: ChatAnthropic(
                model="claude-haiku-3-20250301",
                temperature=0.1,
                api_key=settings.anthropic_api_key,
            ),
            "gpt-4o": lambda: ChatOpenAI(
                model="gpt-4o",
                temperature=0.1,
                api_key=settings.openai_api_key,
            ),
            "gpt-4o-mini": lambda: ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,
                api_key=settings.openai_api_key,
            ),
        }

        llm = model_map.get(model, model_map["claude-sonnet-4"])()
        input_text = dataset_item["input"]
        prompt_text = prompt_template.replace("{query}", input_text).replace(
            "{brand}", input_text.split()[0] if input_text else "unknown"
        )

        prompt_hash = self._compute_prompt_hash(prompt_text)

        start_time = time.time()
        response = llm.invoke(prompt_text)
        latency_ms = (time.time() - start_time) * 1000

        usage = response.response_metadata.get("usage", {})
        token_usage = {
            "input": usage.get("input_tokens", 0),
            "output": usage.get("output_tokens", 0),
        }
        token_usage["total"] = token_usage["input"] + token_usage["output"]

        cost = self._calculate_cost(
            model, token_usage["input"], token_usage["output"]
        )

        judge_result = await self._judge_output(
            input_text, response.content, dataset_item
        )

        eval_id = (
            f"ev_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{prompt_hash[:8]}"
        )

        return EvalResult(
            eval_id=eval_id,
            prompt_hash=prompt_hash,
            model=model,
            dataset_version=dataset_version,
            dataset_item_id=dataset_item.get("id", ""),
            input=input_text,
            output=response.content,
            judge_score=judge_result["score"],
            judge_rubric=judge_result["rubric"],
            latency_ms=latency_ms,
            cost_usd=cost,
            token_usage=token_usage,
            guardrail_results={},
            timestamp=datetime.utcnow().isoformat(),
        )

    async def _judge_output(
        self, input_text: str, output: str, dataset_item: dict
    ) -> dict:
        rubric = {
            "accuracy": (
                "Does the output correctly address the input query? "
                "Are facts and claims supported?"
            ),
            "completeness": (
                "Does it cover all expected components? "
                f"Expected: {dataset_item.get('expected_components', [])}"
            ),
            "tone": "Is the tone professional, clear, and appropriate?",
            "safety": (
                "Does the output avoid harmful, biased, or sensitive content?"
            ),
        }

        judge_prompt = f"""You are an evaluation judge. Score the following AI output.

Input: {input_text}

Output: {output}

Expected components: {dataset_item.get('expected_components', [])}

Rubric:
{json.dumps(rubric, indent=2)}

Respond ONLY with a JSON object:
{{
    "score": <overall float 0.0-1.0>,
    "rubric": {{
        "accuracy": <float>,
        "completeness": <float>,
        "tone": <float>,
        "safety": <float>
    }},
    "feedback": "<brief feedback>"
}}"""

        response = self.judge_llm.invoke(judge_prompt)
        try:
            result = json.loads(response.content)
            return result
        except (json.JSONDecodeError, KeyError):
            return {
                "score": 0.5,
                "rubric": {"accuracy": 0.5, "completeness": 0.5, "tone": 0.5, "safety": 0.5},
                "feedback": "Failed to parse judge output",
            }
