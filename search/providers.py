from __future__ import annotations

import asyncio
import logging
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from .config import SearchConfig
from .models import SearchResult
from .utils import canonicalize_url, compact_text, domain_from_url, extract_date_like, now_utc

logger = logging.getLogger(__name__)


class DuckDuckGoHtmlProvider:
    def __init__(self, config: SearchConfig) -> None:
        self.config = config

    async def search(self, query: str, max_results: int) -> list[SearchResult]:
        headers = {"User-Agent": self.config.user_agent}
        params = {"q": query}

        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.config.timeout_seconds, headers=headers, follow_redirects=True) as client:
                    resp = await client.get(self.config.ddg_html_url, params=params)
                    resp.raise_for_status()
                    return self._parse(resp.text, max_results)
            except Exception as exc:
                last_exc = exc
                backoff = 0.6 * (2**attempt)
                logger.warning("search request failed attempt=%s error=%s", attempt + 1, exc)
                await asyncio.sleep(backoff)

        logger.error("search failed after retries: %s", last_exc)
        return []

    def _parse(self, html: str, max_results: int) -> list[SearchResult]:
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select(".result")
        results: list[SearchResult] = []
        retrieved_at: datetime = now_utc()

        for row in rows:
            link = row.select_one("a.result__a")
            if not link or not link.get("href"):
                continue

            title = compact_text(link.get_text(" ", strip=True), 180)
            raw_url = link["href"]
            url = canonicalize_url(raw_url)
            source = domain_from_url(url)

            snippet_node = row.select_one(".result__snippet")
            snippet = compact_text(snippet_node.get_text(" ", strip=True), 340) if snippet_node else ""
            published_date = extract_date_like(f"{title} {snippet}")

            if not title or not source:
                continue

            results.append(
                SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source=source,
                    published_date=published_date,
                    retrieved_at=retrieved_at,
                )
            )
            if len(results) >= max_results:
                break

        return results
