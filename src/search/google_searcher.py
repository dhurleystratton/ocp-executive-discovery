"""Temporary Google searcher implementation for executive discovery.

This module defines :class:`GoogleSearcher` which is responsible for
querying Google and returning result URLs. The real implementation will
use the Google Custom Search API or scraping, but for now it returns
dummy URLs to enable testing without network access.
"""

from __future__ import annotations

import time
from typing import List

import requests


class GoogleSearcher:
    """Perform Google searches with basic rate limiting."""

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0 Safari/537.36"
        )
    }

    def __init__(self, delay: float = 1.0, timeout: int = 10,
                 headers: dict[str, str] | None = None) -> None:
        """Create a new searcher instance.

        Parameters
        ----------
        delay:
            Minimum delay in seconds between queries.
        timeout:
            HTTP request timeout in seconds.
        headers:
            Optional HTTP headers to use for requests.
        """
        self.delay = delay
        self.timeout = timeout
        self.headers = headers or self.DEFAULT_HEADERS
        self._last_request = 0.0

    # ------------------------------------------------------------------
    def search(self, query: str) -> List[str]:
        """Return up to 10 Google result URLs for ``query``.

        This mock implementation returns placeholder URLs.
        TODO: replace with real Google search using requests.
        """
        # Respect rate limit
        wait = self.delay - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)

        # Placeholder for future implementation
        try:
            # Example of where a real request would be made
            # requests.get("https://www.googleapis.com/customsearch/v1", ...)
            self._last_request = time.time()
        except requests.exceptions.RequestException:
            return []

        return [f"https://example.com/result{i}" for i in range(1, 11)]


__all__ = ["GoogleSearcher"]
