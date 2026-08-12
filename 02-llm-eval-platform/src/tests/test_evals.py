import pytest
from AGENTICOPS_eval.eval_runner import EvalRunner, EvalResult


class TestEvalRunner:
    def test_calculate_cost(self):
        runner = EvalRunner()
        cost = runner._calculate_cost("claude-sonnet-4", 1000, 500)
        assert cost > 0
        assert isinstance(cost, float)

    def test_calculate_cost_zero_tokens(self):
        runner = EvalRunner()
        cost = runner._calculate_cost("claude-sonnet-4", 0, 0)
        assert cost == 0.0

    def test_prompt_hash_consistent(self):
        runner = EvalRunner()
        h1 = runner._compute_prompt_hash("test prompt content")
        h2 = runner._compute_prompt_hash("test prompt content")
        assert h1 == h2

    def test_prompt_hash_different(self):
        runner = EvalRunner()
        h1 = runner._compute_prompt_hash("prompt one")
        h2 = runner._compute_prompt_hash("prompt two")
        assert h1 != h2

    def test_prompt_hash_empty(self):
        runner = EvalRunner()
        h = runner._compute_prompt_hash("")
        assert isinstance(h, str)
        assert len(h) == 16

    def test_cost_unknown_model(self):
        runner = EvalRunner()
        cost = runner._calculate_cost("unknown-model", 1000, 500)
        assert cost == pytest.approx(0.0105, rel=0.01)

    def test_eval_result_model(self):
        result = EvalResult(
            eval_id="ev_test",
            prompt_hash="abc123",
            model="claude-sonnet-4",
            dataset_version="golden_v1",
            dataset_item_id="ds_001",
            input="test input",
            output="test output",
            judge_score=0.85,
            judge_rubric={"accuracy": 0.9, "completeness": 0.8},
            latency_ms=1500.0,
            cost_usd=0.005,
            token_usage={"input": 100, "output": 50, "total": 150},
            guardrail_results={},
            timestamp="2026-06-15T10:00:00Z",
        )
        assert result.judge_score == 0.85
        assert result.model == "claude-sonnet-4"

    def test_eval_result_score_validation(self):
        with pytest.raises(ValueError):
            EvalResult(
                eval_id="ev_test",
                prompt_hash="abc123",
                model="claude-sonnet-4",
                dataset_version="golden_v1",
                dataset_item_id="ds_001",
                input="test",
                output="test",
                judge_score=1.5,
                judge_rubric={},
                latency_ms=0,
                cost_usd=0,
                token_usage={},
                guardrail_results={},
                timestamp="2026-06-15T10:00:00Z",
            )


class TestDatasetGenerator:
    def test_generate_synthetic(self):
        from AGENTICOPS_eval.dataset_generator import DatasetGenerator
        items = DatasetGenerator.generate_synthetic(count=10)
        assert len(items) == 10
        for item in items:
            assert "id" in item
            assert "category" in item
            assert "input" in item

    def test_generate_synthetic_categories(self):
        from AGENTICOPS_eval.dataset_generator import DatasetGenerator
        items = DatasetGenerator.generate_synthetic(count=100)
        categories = set(i["category"] for i in items)
        assert "brand_sentiment" in categories
        assert "trend_analysis" in categories


class TestPromptRegistry:
    def test_list_prompts_empty(self):
        from AGENTICOPS_eval.prompt_registry import PromptRegistry
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            registry = PromptRegistry(registry_path=tmp)
            assert registry.list_prompts() == []

    def test_hash_consistency(self):
        from AGENTICOPS_eval.prompt_registry import PromptRegistry
        h1 = PromptRegistry._hash({"system": "test", "user": "test"})
        h2 = PromptRegistry._hash({"system": "test", "user": "test"})
        assert h1 == h2

    def test_hash_different_content(self):
        from AGENTICOPS_eval.prompt_registry import PromptRegistry
        h1 = PromptRegistry._hash({"system": "prompt A"})
        h2 = PromptRegistry._hash({"system": "prompt B"})
        assert h1 != h2


class TestDashboard:
    def test_empty_dashboard(self):
        from AGENTICOPS_eval.dashboard import EvalDashboard
        dashboard = EvalDashboard()
        cost = dashboard.cost_summary()
        assert cost["total_cost"] == 0
        assert cost["total_evals"] == 0

    def test_dashboard_with_results(self):
        from AGENTICOPS_eval.dashboard import EvalDashboard
        from datetime import datetime
        dashboard = EvalDashboard()
        dashboard.add_result({
            "eval_id": "ev_001",
            "model": "claude-sonnet-4",
            "cost_usd": 0.01,
            "latency_ms": 1000,
            "judge_score": 0.9,
            "token_usage": {"total": 500},
            "timestamp": datetime.utcnow().isoformat(),
        })
        cost = dashboard.cost_summary()
        assert cost["total_cost"] == 0.01
        assert cost["total_evals"] == 1
