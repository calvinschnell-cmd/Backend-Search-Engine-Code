# Open WebUI Local Search Backend (FastAPI, Python 3.11)

Production-oriented local web search backend for Open WebUI external search integration.

## Why this backend is stronger than a toy wrapper

- Uses a real web search result page strategy (DuckDuckGo HTML results parsing), not an instant-answer API.
- Produces **structured ranked results**, not one giant text blob.
- Adds intent-aware ranking (`latest`, `docs`, `general`) with:
  - official-source boosting
  - recency weighting
  - domain quality boosts/penalties
  - query overlap scoring
  - duplicate suppression
- Optionally enriches top 3–5 hits with short page-evidence snippets.
- Includes retries, timeouts, realistic User-Agent, logging, and cache.

## Project structure

- `app.py` - FastAPI entrypoint with `/search` and `/health`.
- `simple_search_backend.py` - single-file launcher variant.
- `search/config.py` - ranking knobs, domain trust lists, runtime settings.
- `search/models.py` - Pydantic response models.
- `search/providers.py` - web search provider and result parsing.
- `search/ranking.py` - ranking logic and dedupe.
- `search/intents.py` - query intent classifier.
- `search/extract.py` - lightweight body extraction + evidence summary.
- `search/cache.py` - in-memory TTL cache.
- `search/utils.py` - URL/date/text helpers.

## Windows PowerShell setup (exact commands)

```powershell
cd C:\path\to\Backend-Search-Engine-Code
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run (PowerShell)

```powershell
cd C:\path\to\Backend-Search-Engine-Code
.\.venv\Scripts\Activate.ps1
python -m uvicorn app:app --host 127.0.0.1 --port 8090 --workers 1
```

Health check:

```powershell
Invoke-RestMethod "http://127.0.0.1:8090/health"
```

## API

### GET `/search?q=<query>`

Optional query params:

- `max_results` (default `8`, max `20`)
- `mode=latest|docs|general` (optional override)

Example:

```powershell
Invoke-RestMethod "http://127.0.0.1:8090/search?q=latest%20NVIDIA%20GPU%20release&max_results=6"
```

## Sample Open WebUI External Search URL

Use this as your external search base URL:

```text
http://127.0.0.1:8090/search?q={query}
```

(If your Open WebUI UI expects only an endpoint URL, use `http://127.0.0.1:8090/search` and let it append `q`.)

## Example test queries

- `latest NVIDIA GPU release`
- `Open WebUI external search setup`
- `Python 3.11 FastAPI uvicorn install Windows`
- `latest Anthropic Claude announcement`

## Example JSON response

```json
{
  "query": "latest NVIDIA GPU release",
  "mode": "latest",
  "total_results": 3,
  "timestamp": "2026-04-21T13:20:00Z",
  "warning": null,
  "results": [
    {
      "title": "NVIDIA Newsroom - New GeForce Announcement",
      "url": "https://www.nvidia.com/en-us/geforce/news/...",
      "snippet": "NVIDIA announced ...",
      "source": "nvidia.com",
      "published_date": "2026-01-08",
      "retrieved_at": "2026-04-21T13:19:55Z",
      "score": 12.8,
      "content": "...short extracted evidence window..."
    }
  ]
}
```

## Customization notes

In `search/config.py`:

- Edit `official_domains`, `quality_news_domains`, `low_quality_domains`.
- Set `domain_whitelist` / `domain_blacklist` for strict filtering.
- Tune recency and relevance weights (`recency_max_boost`, `title_term_boost`, etc.).

## Notes

- This implementation is intentionally non-Docker for local Windows usage.
- For sustained production traffic, consider adding persistent caching and metrics.
