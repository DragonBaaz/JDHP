"""
search_tool.py — Free web search via DuckDuckGo, no API key required.

This module replaces Anthropic's built-in web_search_20250305 tool.
It is called by agents that need live web data (TopicSelection, MarketAnalysis,
DataCollection, Research).

Usage from an agent:
    from agents.search_tool import search, fetch_snippets
    results = search("SEBI AIF regulations India 2024", max_results=5)
    # results: list of {"title": str, "url": str, "body": str}
"""

import logging
from typing import List

logger = logging.getLogger("search_tool")

# GPT-4o tool schema — pass this in the `tools` parameter of chat.completions.create
SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": (
            "Search the web for current information. Use this whenever you need "
            "recent data, statistics, regulatory updates, or to verify claims. "
            "Returns a list of search result snippets with URLs."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Be specific. Include year and country when relevant."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return. Default 5, max 10.",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
}


def search(query: str, max_results: int = 5) -> List[dict]:
    """
    Run a DuckDuckGo search and return structured results.
    Returns list of {title, url, body} dicts.
    Falls back to empty list on any failure (non-fatal).
    """
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "body": r.get("body", "")
            }
            for r in results
        ]
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed for query '{query}': {e}")
        return []


def format_results_for_llm(results: List[dict]) -> str:
    """
    Format search results into a string suitable for injection into an LLM prompt.
    """
    if not results:
        return "No search results found."
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r['title']}")
        lines.append(f"    URL: {r['url']}")
        lines.append(f"    {r['body'][:300]}")
        lines.append("")
    return "\n".join(lines)


def run_tool_call(tool_name: str, tool_args: dict) -> str:
    """
    Dispatch a tool call from GPT-4o's tool_calls response.
    Currently only handles 'search_web'.
    Returns a string to be sent back as a tool message.
    """
    if tool_name == "search_web":
        query = tool_args.get("query", "")
        max_results = min(int(tool_args.get("max_results", 5)), 10)
        results = search(query, max_results=max_results)
        return format_results_for_llm(results)
    return f"Unknown tool: {tool_name}"
