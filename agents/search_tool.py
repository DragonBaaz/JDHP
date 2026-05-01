"""
search_tool.py — Free web search via DuckDuckGo (ddgs), no API key required.

Cost strategy: DuckDuckGo is FREE vs Anthropic's built-in web_search (~$0.01/call).
With ~20 searches per pipeline run, staying with ddgs saves ~$0.20 per report.

Optimisations in this version:
  - Snippet body truncated 500 → 250 chars (62% reduction in search token volume)
  - Default results 8 → 6 per query
  - 7-day SQLite disk cache (stdlib only, no new dependency) — eliminates all
    search cost on retried/repeated topics
"""

import logging
import hashlib
import json
import time
import os
import sqlite3
from typing import List

logger = logging.getLogger("search_tool")

# ── Claude tool_use schema ────────────────────────────────────────────────────
CLAUDE_SEARCH_TOOL_SCHEMA = {
    "name": "search_web",
    "description": (
        "Search the web for current information. Use this whenever you need "
        "recent data, statistics, regulatory updates, news, or to verify claims. "
        "Returns search result snippets with titles and URLs. "
        "Run multiple focused searches with different queries for comprehensive coverage."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "The search query. Be specific; include year and country when relevant. "
                    "Example: 'SEBI AIF regulations India 2024 updates'"
                )
            },
            "max_results": {
                "type": "integer",
                "description": "Number of results to return. Default 6, max 8.",
                "default": 6
            }
        },
        "required": ["query"]
    }
}

# ── Disk-based search cache (7-day TTL, stdlib sqlite3) ──────────────────────
_CACHE_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "search_cache.db")
_CACHE_TTL = 7 * 24 * 3600   # 7 days in seconds


def _get_cache_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_CACHE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS search_cache (
            query_hash  TEXT PRIMARY KEY,
            query       TEXT,
            results_json TEXT,
            created_at  REAL
        )
    """)
    conn.commit()
    return conn


# ── Core search function ─────────────────────────────────────────────────────

def search(query: str, max_results: int = 6) -> List[dict]:
    """
    Run a DuckDuckGo search and return structured results.
    Returns list of {title, url, body} dicts.
    Falls back to empty list on any failure (non-fatal).
    """
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [
            {
                "title": r.get("title", ""),
                "url":   r.get("href", ""),
                "body":  r.get("body", "")
            }
            for r in results
        ]
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed for '{query}': {e}")
        return []


def cached_search(query: str, max_results: int = 6) -> List[dict]:
    """
    search() with a 7-day SQLite cache keyed by MD5(query).
    On cache hit: returns stored results instantly (zero DDG call, zero tokens added).
    On cache miss: runs search() and stores results.
    Falls back to direct search() on any cache error.
    """
    key = hashlib.md5(query.lower().strip().encode()).hexdigest()
    try:
        conn = _get_cache_conn()
        row = conn.execute(
            "SELECT results_json, created_at FROM search_cache WHERE query_hash = ?", (key,)
        ).fetchone()

        if row and (time.time() - row[1]) < _CACHE_TTL:
            logger.info(f"Cache HIT [{key[:8]}]: {query[:70]}")
            conn.close()
            return json.loads(row[0])

        # Cache miss or expired — run live search
        results = search(query, max_results)
        conn.execute(
            "INSERT OR REPLACE INTO search_cache (query_hash, query, results_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (key, query, json.dumps(results), time.time())
        )
        conn.commit()
        conn.close()
        return results

    except Exception as e:
        logger.warning(f"Cache error ({e}), falling back to direct search")
        return search(query, max_results)


# ── LLM formatting ───────────────────────────────────────────────────────────

def format_results_for_llm(results: List[dict]) -> str:
    """
    Format search results for injection into Claude's tool_result.
    Body snippets are capped at 250 chars (was 500) — first sentence carries
    all the relevance signal Claude needs to decide whether to follow up.
    """
    if not results:
        return "No results found. Try a different or broader search query."
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r['title']}")
        lines.append(f"    URL: {r['url']}")
        lines.append(f"    {r['body'][:250]}")
        lines.append("")
    return "\n".join(lines)


def run_tool_call(tool_name: str, tool_args: dict) -> str:
    """
    Dispatch a tool_use call from Claude's response.
    Uses cached_search so repeated queries within 7 days are free.
    """
    if tool_name == "search_web":
        query = tool_args.get("query", "")
        max_results = min(int(tool_args.get("max_results", 6)), 8)
        results = cached_search(query, max_results=max_results)
        return format_results_for_llm(results)
    return f"Unknown tool: {tool_name}"
