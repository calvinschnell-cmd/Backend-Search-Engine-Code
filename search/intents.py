from __future__ import annotations

from .models import SearchMode
from .utils import tokenize

LATEST_TERMS = {
    "latest",
    "recent",
    "current",
    "news",
    "release",
    "announced",
    "announcement",
    "today",
}
DOCS_TERMS = {
    "docs",
    "documentation",
    "spec",
    "specs",
    "reference",
    "manual",
    "api",
    "sdk",
}


class SearchIntent:
    def __init__(self, mode: SearchMode, terms: set[str]) -> None:
        self.mode = mode
        self.terms = terms


def classify_intent(query: str, mode_override: SearchMode | None = None) -> SearchIntent:
    terms = tokenize(query)
    if mode_override in {"latest", "docs", "general"}:
        return SearchIntent(mode=mode_override, terms=terms)

    if terms.intersection(LATEST_TERMS):
        return SearchIntent(mode="latest", terms=terms)
    if terms.intersection(DOCS_TERMS):
        return SearchIntent(mode="docs", terms=terms)
    return SearchIntent(mode="general", terms=terms)
