"""Search backend package for Open WebUI external search integration."""

from .models import SearchResult, SearchResponse
from .intents import SearchIntent, classify_intent

__all__ = ["SearchResult", "SearchResponse", "SearchIntent", "classify_intent"]
