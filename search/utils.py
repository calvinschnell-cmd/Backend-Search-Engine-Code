from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import parse_qs, unquote, urlparse

DATE_PATTERN = re.compile(r"\b(20\d{2})[-/\.](0?[1-9]|1[0-2])[-/\.](0?[1-9]|[12]\d|3[01])\b")
WORD_PATTERN = re.compile(r"[a-zA-Z0-9]{2,}")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def domain_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return host


def canonicalize_url(url: str) -> str:
    """Normalize URL and unwrap common redirect wrappers."""
    parsed = urlparse(url)

    # DuckDuckGo redirect links often include uddg parameter.
    if parsed.netloc.endswith("duckduckgo.com"):
        query = parse_qs(parsed.query)
        if "uddg" in query and query["uddg"]:
            return canonicalize_url(unquote(query["uddg"][0]))

    scheme = parsed.scheme or "https"
    netloc = parsed.netloc.lower().replace(":80", "").replace(":443", "")
    path = parsed.path.rstrip("/")
    return f"{scheme}://{netloc}{path}" if path else f"{scheme}://{netloc}"


def url_dedupe_key(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.rstrip("/")
    return f"{host}{path}"


def tokenize(text: str) -> set[str]:
    return {t.lower() for t in WORD_PATTERN.findall(text)}


def overlap_count(query_terms: set[str], text: str) -> int:
    if not query_terms:
        return 0
    return len(query_terms.intersection(tokenize(text)))


def extract_date_like(text: str) -> str | None:
    m = DATE_PATTERN.search(text)
    if not m:
        return None
    year, month, day = m.group(1), int(m.group(2)), int(m.group(3))
    return f"{year}-{month:02d}-{day:02d}"


def compact_text(text: str, max_len: int = 280) -> str:
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def unique_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out
