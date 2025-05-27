"""Google Custom Search API implementation for executive discovery."""

from __future__ import annotations

import time
from typing import List

import requests

API_KEY = "AIzaSyDDueD80qnmavPt_UMOaGASz553F3e8EJA"
SEARCH_ENGINE_ID = "95730ea59dac44df7"


class GoogleAPISearcher:
    """Perform Google searches using the Custom Search API."""

    SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, delay: float = 1.0, timeout: int = 10,
                 api_key: str = API_KEY, engine_id: str = SEARCH_ENGINE_ID) -> None:
        """Create a new API searcher instance.

        Parameters
        ----------
        delay:
            Minimum delay in seconds between queries.
        timeout:
            HTTP request timeout in seconds.
        api_key:
            Google API key.
        engine_id:
            Custom search engine ID.
        """
        self.delay = delay
        self.timeout = timeout
        self.api_key = api_key
        self.engine_id = engine_id
        self._last_request = 0.0

    # ------------------------------------------------------------------
    def search(self, query: str) -> List[str]:
        """Return up to 10 Google result URLs for ``query``."""
        wait = self.delay - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)

        params = {
            "key": self.api_key,
            "cx": self.engine_id,
            "q": query,
            "num": 10,
        }
        try:
            resp = requests.get(self.SEARCH_URL, params=params,
                                timeout=self.timeout)
            self._last_request = time.time()
        except requests.exceptions.RequestException:
            return []

        if resp.status_code != 200:
            return []

        try:
            data = resp.json()
        except ValueError:
            return []

        items = data.get("items", [])
        urls: List[str] = []
        for item in items:
            link = item.get("link")
            if link:
                urls.append(link)
            if len(urls) >= 10:
                break
        return urls


__all__ = ["GoogleAPISearcher"]
