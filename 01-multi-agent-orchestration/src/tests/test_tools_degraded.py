"""Regression tests for a bug where `httpx.AClient` (not a real class) raised inside a blanket `except`, so every call
silently returned demonstration data that looked like a real news result."""

import httpx
import pytest

from agenticops_orchestrator.tools import search_news_impl


@pytest.mark.asyncio
async def test_failed_news_call_is_flagged_as_degraded():
    results = await search_news_impl(query="Nike")  # conftest makes the HTTP call return 503
    assert results[0]["degraded"] is True
    assert "503" in results[0]["degraded_reason"]


@pytest.mark.asyncio
async def test_successful_news_call_is_real_and_not_flagged(mock_http):
    payload = {
        "articles": [
            {
                "title": "Nike launches a shoe",
                "source": {"name": "Example Wire"},
                "publishedAt": "2026-01-01T00:00:00Z",
                "description": "d",
                "url": "https://example.test/a",
            }
        ]
    }
    mock_http["handler"] = lambda request: httpx.Response(200, json=payload)
    results = await search_news_impl(query="Nike")
    assert results == [
        {
            "title": "Nike launches a shoe",
            "source": "Example Wire",
            "published_at": "2026-01-01T00:00:00Z",
            "description": "d",
            "url": "https://example.test/a",
        }
    ]
    assert "degraded" not in results[0]


@pytest.mark.asyncio
async def test_a_real_asyncclient_is_what_gets_constructed(mock_http):
    seen = {}

    def handler(request):
        seen["host"] = request.url.host
        return httpx.Response(200, json={"articles": []})

    mock_http["handler"] = handler
    assert await search_news_impl(query="Nike") == []
    assert seen["host"] == "newsapi.org"  # proves the request went through httpx.AsyncClient, not the fallback
