import pytest
from AGENTICOPS_orchestrator.models import (
    TaskPlan,
    WorkerOutput,
    CritiqueResult,
    BrandAnalysis,
    ParsedQuery,
)
from AGENTICOPS_orchestrator.tools import (
    search_news_impl,
    fetch_competitor_data_impl,
    fetch_social_mentions_impl,
)


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
        assert analysis.sentiment_score == 0.75

    def test_brand_analysis_score_range_upper(self):
        with pytest.raises(ValueError):
            BrandAnalysis(
                brand="Nike",
                sentiment_score=1.5,
                sentiment_label="positive",
                trend_direction="improving",
                key_drivers=[],
                confidence=0.85,
            )

    def test_brand_analysis_score_range_lower(self):
        with pytest.raises(ValueError):
            BrandAnalysis(
                brand="Nike",
                sentiment_score=-1.5,
                sentiment_label="negative",
                trend_direction="declining",
                key_drivers=[],
                confidence=0.85,
            )

    def test_worker_output_valid_status(self):
        output = WorkerOutput(
            worker_type="brand_sentiment",
            status="complete",
            findings={"score": 0.8},
            sources_used=["news_source"],
            confidence_score=0.5,
        )
        assert output.status == "complete"

    def test_worker_output_invalid_status(self):
        with pytest.raises(ValueError):
            WorkerOutput(
                worker_type="brand_sentiment",
                status="unknown",
                findings={},
                sources_used=[],
                confidence_score=0.5,
            )

    def test_critique_result(self):
        critique = CritiqueResult(
            passed=True,
            score=0.9,
            issues=[],
            suggestions=["Add more sources"],
        )
        assert critique.passed is True
        assert critique.score == 0.9

    def test_parsed_query(self):
        pq = ParsedQuery(
            brands=["Nike", "Adidas"],
            time_period="2026-Q2",
            analysis_type="comprehensive",
        )
        assert len(pq.brands) == 2
        assert pq.analysis_type == "comprehensive"

    def test_parsed_query_invalid_type(self):
        with pytest.raises(ValueError):
            ParsedQuery(
                brands=["Nike"],
                analysis_type="invalid_type",
            )


@pytest.mark.asyncio
class TestTools:
    async def test_search_news_returns_list(self):
        results = await search_news_impl(query="Nike brand sentiment")
        assert isinstance(results, list)
        assert len(results) > 0
        assert "title" in results[0]

    async def test_search_news_with_params(self):
        results = await search_news_impl(
            query="Adidas",
            date_from="2026-01-01",
            date_to="2026-06-01",
            max_results=5,
        )
        assert len(results) <= 5

    async def test_fetch_competitor_data(self):
        result = await fetch_competitor_data_impl(company_name="Nike")
        assert "company" in result
        assert result["company"] == "Nike"
        assert "market_position" in result

    async def test_fetch_social_mentions(self):
        results = await fetch_social_mentions_impl(brand="Nike")
        assert isinstance(results, list)
        assert len(results) > 0
        assert "brand" in results[0]
        assert results[0]["brand"] == "Nike"


class TestOrchestrator:
    def test_build_graph(self):
        from AGENTICOPS_orchestrator.orchestrator import build_graph
        graph = build_graph()
        assert graph is not None
        assert hasattr(graph, "invoke")

    def test_graph_structure(self):
        from AGENTICOPS_orchestrator.orchestrator import build_graph
        graph = build_graph()
        nodes = list(graph.get_graph().nodes.keys())
        expected = [
            "parse_query",
            "plan_tasks",
            "dispatch_workers",
            "synthesize",
            "reflect",
            "rewrite",
            "finalize",
        ]
        for node in expected:
            assert node in nodes, f"Missing node: {node}"
