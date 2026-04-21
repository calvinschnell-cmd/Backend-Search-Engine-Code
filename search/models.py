from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


SearchMode = Literal["latest", "docs", "general"]


class SearchResult(BaseModel):
    title: str
    url: HttpUrl
    snippet: str
    source: str
    retrieved_at: datetime
    published_date: str | None = None
    score: float = 0.0
    content: str | None = None


class SearchResponse(BaseModel):
    query: str
    mode: SearchMode
    total_results: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    results: list[SearchResult]
    warning: str | None = None
