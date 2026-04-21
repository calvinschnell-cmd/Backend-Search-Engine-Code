from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SearchConfig:
    # --- Runtime/network settings ---
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    timeout_seconds: float = 10.0
    max_search_results: int = 15
    max_enriched_results: int = 5
    cache_ttl_seconds: int = 180

    # --- Search endpoints ---
    # DuckDuckGo HTML endpoint provides robust result pages suitable for server-side extraction.
    ddg_html_url: str = "https://html.duckduckgo.com/html/"

    # --- Domain quality and trust settings (customize as needed) ---
    official_domains: set[str] = field(
        default_factory=lambda: {
            "nvidia.com",
            "amd.com",
            "intel.com",
            "microsoft.com",
            "openai.com",
            "anthropic.com",
            "github.com",
            "docs.python.org",
            "developer.mozilla.org",
            "learn.microsoft.com",
        }
    )
    quality_news_domains: set[str] = field(
        default_factory=lambda: {
            "tomshardware.com",
            "anandtech.com",
            "techpowerup.com",
            "theverge.com",
            "arstechnica.com",
            "reuters.com",
            "bloomberg.com",
            "wsj.com",
        }
    )
    low_quality_domains: set[str] = field(
        default_factory=lambda: {
            "pinterest.com",
            "quora.com",
            "w3schools.com",
            "answers.com",
            "fandom.com",
            "top10.com",
        }
    )

    # Optional controls for deployment-specific policies.
    domain_whitelist: set[str] = field(default_factory=set)
    domain_blacklist: set[str] = field(default_factory=set)

    # --- Ranking tuning knobs (customize recency/intent behavior here) ---
    base_score: float = 1.0
    official_boost: float = 4.5
    docs_boost: float = 3.0
    news_boost: float = 2.0
    recency_max_boost: float = 4.0
    title_term_boost: float = 0.6
    snippet_term_boost: float = 0.3
    low_quality_penalty: float = -2.5


DEFAULT_CONFIG = SearchConfig()
