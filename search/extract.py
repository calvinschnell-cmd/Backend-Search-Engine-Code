from __future__ import annotations

import asyncio
import logging

import httpx
from bs4 import BeautifulSoup

from .config import SearchConfig
from .intents import SearchIntent
from .models import SearchResult
from .utils import compact_text

logger = logging.getLogger(__name__)

_DROP_TAGS = {"script", "style", "noscript", "header", "footer", "nav", "aside", "form", "svg"}
_DROP_SELECTORS = [
    "[role='navigation']",
    ".cookie",
    ".cookies",
    ".consent",
    ".advert",
    ".ads",
    ".sidebar",
    ".menu",
]


async def enrich_results(results: list[SearchResult], intent: SearchIntent, cfg: SearchConfig) -> None:
    target = results[: cfg.max_enriched_results]
    async with httpx.AsyncClient(timeout=cfg.timeout_seconds, headers={"User-Agent": cfg.user_agent}, follow_redirects=True) as client:
        await asyncio.gather(*( _fetch_and_summarize(client, r, intent) for r in target), return_exceptions=True)


async def _fetch_and_summarize(client: httpx.AsyncClient, result: SearchResult, intent: SearchIntent) -> None:
    try:
        resp = await client.get(str(result.url))
        if resp.status_code >= 400 or "text/html" not in resp.headers.get("content-type", ""):
            return

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag_name in _DROP_TAGS:
            for node in soup.find_all(tag_name):
                node.decompose()
        for selector in _DROP_SELECTORS:
            for node in soup.select(selector):
                node.decompose()

        body_text = soup.get_text(" ", strip=True)
        summary = _extract_evidence_window(body_text, result.snippet, intent)
        if summary:
            result.content = summary
    except Exception as exc:
        logger.debug("content enrichment failed url=%s error=%s", result.url, exc)


def _extract_evidence_window(text: str, snippet: str, intent: SearchIntent) -> str | None:
    if not text:
        return None

    content = " ".join(text.split())
    if len(content) < 80:
        return None

    terms = [t for t in intent.terms if len(t) > 3]
    selected = content[:450]
    for term in terms[:5]:
        idx = content.lower().find(term.lower())
        if idx != -1:
            start = max(0, idx - 120)
            end = min(len(content), idx + 320)
            selected = content[start:end]
            break

    merged = f"{snippet} {selected}" if snippet else selected
    return compact_text(merged, 420)
