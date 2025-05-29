"""Minimal web page scraper with basic error handling and rate limiting."""

from __future__ import annotations

import time
from typing import Optional

import requests
from bs4 import BeautifulSoup


class SimpleScraper:
    """Fetch and parse HTML pages politely."""

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0 Safari/537.36"
        )
    }

    def __init__(self, timeout: int = 10, delay: float = 1.0,
                 headers: dict[str, str] | None = None) -> None:
        """Create a new scraper instance.

        Parameters
        ----------
        timeout:
            Seconds to wait for a response before giving up.
        delay:
            Minimum delay in seconds between consecutive requests.
        headers:
            Optional HTTP headers to send with each request. ``User-Agent`` will
            default to :data:`DEFAULT_HEADERS` if not provided.
        """
        self.timeout = timeout
        self.delay = delay
        self.headers = headers or self.DEFAULT_HEADERS
        self._last_request = 0.0

    # ------------------------------------------------------------------
    def fetch(self, url: str) -> Optional[BeautifulSoup]:
        """Return parsed HTML for ``url`` or ``None`` on error."""
        # Respect rate limit
        wait = self.delay - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)

        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            self._last_request = time.time()
        except requests.exceptions.Timeout:
            return None
        except requests.exceptions.RequestException:
            return None

        if response.status_code == 404:
            return None
        if not response.ok:
            return None

        content_type = response.headers.get("Content-Type", "").lower()
        if "text/html" not in content_type:
            return None

        return BeautifulSoup(response.text, "html.parser")


__all__ = ["SimpleScraper"]
