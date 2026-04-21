from __future__ import annotations

import logging

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

app = FastAPI(title="Open WebUI Local Search Backend", version="1.0.0")
config = DEFAULT_CONFIG
provider = DuckDuckGoHtmlProvider(config)
cache = TTLCache[SearchResponse](ttl_seconds=config.cache_ttl_seconds)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=2, description="Search query"),
    max_results: int = Query(default=8, ge=1, le=20),
    mode: SearchMode | None = Query(default=None, description="latest|docs|general override"),
) -> SearchResponse:
    cache_key = f"{q}|{max_results}|{mode}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    intent = classify_intent(q, mode_override=mode)
    logger.info("search request query=%r mode=%s", q, intent.mode)

    initial = await provider.search(q, max_results=max(max_results * 2, config.max_search_results))
    ranked = rank_results(initial, q, intent, config)
    final = ranked[:max_results]
    await enrich_results(final, intent, config)

    warning = None
    if intent.mode == "latest" and not any(r.published_date for r in final[:3]):
        warning = (
            "Fresh date signals were limited for this query. "
            "Consider refining with vendor/product names or a tighter timeframe."
        )

    response = SearchResponse(
        query=q,
        mode=intent.mode,
        total_results=len(final),
        results=final,
        warning=warning,
    )
    cache.set(cache_key, response)
    return response
