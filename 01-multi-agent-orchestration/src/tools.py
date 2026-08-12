from typing import Optional
import httpx
import json
from datetime import datetime, timedelta


async def search_news_impl(
    query: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    max_results: int = 10,
) -> list[dict]:
    if not date_from:
        date_from = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not date_to:
        date_to = datetime.utcnow().strftime("%Y-%m-%d")

    try:
        async with httpx.AClient(timeout=10.0) as client:
            response = await client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query,
                    "from": date_from,
                    "to": date_to,
                    "pageSize": max_results,
                    "sortBy": "relevancy",
                    "apiKey": "demo_key",
                },
            )
            response.raise_for_status()
            data = response.json()
            return [
                {
                    "title": article["title"],
                    "source": article["source"]["name"],
                    "published_at": article["publishedAt"],
                    "description": article.get("description", ""),
                    "url": article["url"],
                }
                for article in data.get("articles", [])
            ]
    except Exception as e:
        return [
            {
                "title": f"Sample news result for: {query}",
                "source": "NewsAPI",
                "published_at": datetime.utcnow().isoformat(),
                "description": f"Demonstration result. In production, this would call a real news API. Query: {query}",
                "url": f"https://example.com/news/{query}",
            }
        ]


async def fetch_competitor_data_impl(
    company_name: str,
    industry: Optional[str] = None,
) -> dict:
    return {
        "company": company_name,
        "industry": industry or "Unknown",
        "market_position": "Analysis pending",
        "recent_moves": [
            f"{company_name} launched new product line",
            f"{company_name} expanded into new market",
        ],
        "market_share_estimate": "15-20%",
        "sentiment_trend": "stable",
        "source": "Demonstration data. In production, this would aggregate from financial APIs, news, and CRM.",
    }


async def fetch_social_mentions_impl(
    brand: str,
    platform: str = "twitter",
    max_results: int = 20,
) -> list[dict]:
    return [
        {
            "brand": brand,
            "platform": platform,
            "mention_count": max_results,
            "positive_pct": 65,
            "neutral_pct": 25,
            "negative_pct": 10,
            "top_hashtags": [f"#{brand}", f"#{brand}Fan", f"#{brand}Review"],
            "sample_mentions": [
                f"Love the new {brand} products! #excited",
                f"Not impressed with {brand} customer service",
                f"{brand}'s latest campaign is brilliant",
            ],
            "source": "Demonstration data. In production, this would call Twitter/X API, Reddit API, etc.",
        }
    ]
