from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Query

from search.cache import TTLCache
from search.config import DEFAULT_CONFIG
from search.extract import enrich_results
from search.intents import classify_intent
from search.models import SearchMode, SearchResponse
from search.providers import DuckDuckGoHtmlProvider
from search.ranking import rank_results

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("search-backend")

app = FastAPI(title="Open WebUI Local Search Backend", version="1.1.0")
config = DEFAULT_CONFIG
provider = DuckDuckGoHtmlProvider(config)
cache = TTLCache[SearchResponse](ttl_seconds=config.cache_ttl_seconds)


def _result_to_external_item(result: Any) -> dict[str, Any]:
    return {
        "title": result.title,
        "url": str(result.url),
        "snippet": result.snippet,
        "source": result.source,
        "content": result.content,
        "published_date": result.published_date,
        "retrieved_at": result.retrieved_at.isoformat(),
        "score": result.score,
    }


async def _run_search(
    query_text: str,
    max_results: int,
    mode: SearchMode | None,
) -> SearchResponse:
    cache_key = f"{query_text}|{max_results}|{mode}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    intent = classify_intent(query_text, mode_override=mode)
    logger.info("search request query=%r mode=%s", query_text, intent.mode)

    initial = await provider.search(
        query_text,
        max_results=max(max_results * 2, config.max_search_results),
    )
    ranked = rank_results(initial, query_text, intent, config)
    final = ranked[:max_results]
    await enrich_results(final, intent, config)

    warning = None
    if intent.mode == "latest" and not any(r.published_date for r in final[:3]):
        warning = (
            "Fresh date signals were limited for this query. "
            "Consider refining with vendor/product names or a tighter timeframe."
        )

    response = SearchResponse(
        query=query_text,
        mode=intent.mode,
        total_results=len(final),
        results=final,
        warning=warning,
    )
    cache.set(cache_key, response)
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=2, description="Search query"),
    max_results: int = Query(default=8, ge=1, le=20),
    mode: SearchMode | None = Query(default=None, description="latest|docs|general override"),
) -> SearchResponse:
    return await _run_search(q, max_results, mode)


@app.get("/external-search")
async def external_search(
    q: str | None = Query(default=None, min_length=2),
    query: str | None = Query(default=None, min_length=2),
    max_results: int = Query(default=8, ge=1, le=20),
    mode: SearchMode | None = Query(default=None),
) -> list[dict[str, Any]]:
    query_text = q or query
    if not query_text:
        return []

    response = await _run_search(query_text, max_results, mode)
    return [_result_to_external_item(item) for item in response.results]
