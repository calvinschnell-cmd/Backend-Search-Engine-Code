from __future__ import annotations

from datetime import date

from .config import SearchConfig
from .intents import SearchIntent
from .models import SearchResult
from .utils import overlap_count, url_dedupe_key


def _is_official(source: str, cfg: SearchConfig) -> bool:
    return source in cfg.official_domains or any(source.endswith(f".{d}") for d in cfg.official_domains)


def _is_quality_news(source: str, cfg: SearchConfig) -> bool:
    return source in cfg.quality_news_domains or any(source.endswith(f".{d}") for d in cfg.quality_news_domains)


def _is_low_quality(source: str, cfg: SearchConfig) -> bool:
    return source in cfg.low_quality_domains or any(source.endswith(f".{d}") for d in cfg.low_quality_domains)


def _recency_boost(published_date: str | None, max_boost: float) -> float:
    if not published_date:
        return 0.0
    try:
        pub = date.fromisoformat(published_date)
    except ValueError:
        return 0.0

    days_old = (date.today() - pub).days
    if days_old < 0:
        return max_boost * 0.5
    if days_old <= 7:
        return max_boost
    if days_old <= 30:
        return max_boost * 0.7
    if days_old <= 180:
        return max_boost * 0.35
    return 0.0


def rank_results(results: list[SearchResult], query: str, intent: SearchIntent, cfg: SearchConfig) -> list[SearchResult]:
    seen_keys: set[str] = set()
    ranked: list[SearchResult] = []

    for result in results:
        if cfg.domain_whitelist and result.source not in cfg.domain_whitelist:
            continue
        if result.source in cfg.domain_blacklist:
            continue

        key = url_dedupe_key(str(result.url))
        if key in seen_keys:
            continue
        seen_keys.add(key)

        score = cfg.base_score
        title_overlap = overlap_count(intent.terms, result.title)
        snippet_overlap = overlap_count(intent.terms, result.snippet)

        score += title_overlap * cfg.title_term_boost
        score += snippet_overlap * cfg.snippet_term_boost

        if _is_official(result.source, cfg):
            score += cfg.official_boost
        if _is_low_quality(result.source, cfg):
            score += cfg.low_quality_penalty
        if intent.mode == "latest":
            score += _recency_boost(result.published_date, cfg.recency_max_boost)
            if _is_quality_news(result.source, cfg):
                score += cfg.news_boost
        elif intent.mode == "docs":
            if "doc" in result.title.lower() or "api" in result.title.lower() or "reference" in result.title.lower():
                score += cfg.docs_boost
            if _is_official(result.source, cfg):
                score += 1.5

        result.score = round(score, 3)
        ranked.append(result)

    ranked.sort(key=lambda r: r.score, reverse=True)
    return ranked
