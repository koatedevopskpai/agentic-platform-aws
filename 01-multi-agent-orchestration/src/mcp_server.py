from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from typing import Any

from .tools import search_news_impl, fetch_competitor_data_impl, fetch_social_mentions_impl

server = Server("AGENTICOPS-mcp-server")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_news",
            description="Search news articles for brand mentions and sentiment analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (e.g., brand name + topic)"},
                    "date_from": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD)",
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD)",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="fetch_competitor_data",
            description="Fetch competitor positioning, market share estimates, and recent strategic moves",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Name of the competitor company",
                    },
                    "industry": {
                        "type": "string",
                        "description": "Industry sector for context",
                    },
                },
                "required": ["company_name"],
            },
        ),
        types.Tool(
            name="fetch_social_mentions",
            description="Fetch social media mentions and sentiment for a brand across platforms",
            inputSchema={
                "type": "object",
                "properties": {
                    "brand": {
                        "type": "string",
                        "description": "Brand name to search for",
                    },
                    "platform": {
                        "type": "string",
                        "enum": ["twitter", "reddit", "news"],
                        "description": "Social media platform",
                        "default": "twitter",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of mentions to return",
                        "default": 20,
                    },
                },
                "required": ["brand"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if arguments is None:
        arguments = {}

    if name == "search_news":
        results = await search_news_impl(
            query=arguments.get("query", ""),
            date_from=arguments.get("date_from"),
            date_to=arguments.get("date_to"),
            max_results=arguments.get("max_results", 10),
        )
        return [types.TextContent(type="text", text=str(results))]

    elif name == "fetch_competitor_data":
        results = await fetch_competitor_data_impl(
            company_name=arguments.get("company_name", ""),
            industry=arguments.get("industry"),
        )
        return [types.TextContent(type="text", text=str(results))]

    elif name == "fetch_social_mentions":
        results = await fetch_social_mentions_impl(
            brand=arguments.get("brand", ""),
            platform=arguments.get("platform", "twitter"),
            max_results=arguments.get("max_results", 20),
        )
        return [types.TextContent(type="text", text=str(results))]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="AGENTICOPS-mcp-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
