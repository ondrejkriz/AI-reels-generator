"""Wikipedia source retrieval via the public MediaWiki API."""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .models import FactSource
from .utils import utc_now_iso

LOGGER = logging.getLogger(__name__)


class WikipediaClient:
    """Fetches topic summaries from Wikipedia with safe fallback behavior."""

    def __init__(self, language: str = "cs", timeout_seconds: int = 10, user_agent: str = "did-you-know-reels-generator/0.1") -> None:
        self.language = language
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent

    def fetch_source(self, query: str) -> FactSource | None:
        """Search Wikipedia and return a summary source for the best matching page."""

        title = self._search_title(query)
        if not title:
            return None
        extract = self._fetch_extract(title)
        if not extract:
            return None
        page_url = f"https://{self.language}.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"
        return FactSource(
            source_name="wikipedia",
            source_title=title,
            source_url=page_url,
            summary=extract,
            retrieved_at=utc_now_iso(),
            language=self.language,
        )

    def _search_title(self, query: str) -> str | None:
        params = urlencode(
            {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": 1,
                "format": "json",
                "utf8": 1,
            }
        )
        payload = self._request_json(f"https://{self.language}.wikipedia.org/w/api.php?{params}")
        search_results = payload.get("query", {}).get("search", [])
        if not search_results:
            return None
        return str(search_results[0]["title"])

    def _fetch_extract(self, title: str) -> str | None:
        params = urlencode(
            {
                "action": "query",
                "prop": "extracts",
                "explaintext": 1,
                "exintro": 1,
                "titles": title,
                "format": "json",
                "utf8": 1,
            }
        )
        payload = self._request_json(f"https://{self.language}.wikipedia.org/w/api.php?{params}")
        pages = payload.get("query", {}).get("pages", {})
        if not pages:
            return None
        page = next(iter(pages.values()))
        extract = str(page.get("extract", "")).strip()
        return extract or None

    def _request_json(self, url: str) -> dict[str, Any]:
        request = Request(url, headers={"User-Agent": self.user_agent})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            LOGGER.warning("Wikipedia request failed for %s: %s", url, exc)
            return {}
