"""Real Google searcher using requests + BeautifulSoup.

This module defines :class:`RealGoogleSearcher` which performs actual
Google queries by scraping the public results page. It extracts organic
result URLs while avoiding ads and other non-organic elements. Network
errors or blocks by Google are handled gracefully by returning an empty
list.
"""

from __future__ import annotations

import random
import time
from typing import List
from urllib.parse import parse_qs, urlparse, urlunparse, unquote

import requests
from bs4 import BeautifulSoup


class RealGoogleSearcher:
    """Perform Google searches with polite scraping."""

    SEARCH_URL = "https://www.google.com/search"

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:117.0) Gecko/20100101 Firefox/117.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0",
    ]

    BASE_HEADERS = {
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Cache-Control": "no-cache",
    }

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout
        self._last_request = 0.0

    # ------------------------------------------------------------------
    def _headers(self) -> dict[str, str]:
        headers = dict(self.BASE_HEADERS)
        headers["User-Agent"] = random.choice(self.USER_AGENTS)
        return headers

    # ------------------------------------------------------------------
    def _clean_url(self, href: str) -> str | None:
        """Return a cleaned URL from a Google result link."""
        if href.startswith("/url?"):
            parsed = urlparse(href)
            params = parse_qs(parsed.query)
            url = params.get("q", [""])[0]
            href = unquote(url)
        if not href:
            return None
        parsed = urlparse(href)
        # strip unnecessary query parameters added by Google
        cleaned = parsed._replace(fragment="", query="")
        return urlunparse(cleaned)

    # ------------------------------------------------------------------
    def _parse_results(self, soup: BeautifulSoup) -> List[str]:
        urls: List[str] = []
        for result in soup.select("div.g"):
            # skip ads
            if result.select_one("div.uEierd"):
                continue
            link = result.select_one("div.yuRUbf > a[href]")
            if link is None:
                link = result.select_one("a[href]")
            if link is None:
                continue
            url = self._clean_url(link.get("href", ""))
            if url:
                urls.append(url)
            if len(urls) >= 10:
                break
        return urls

    # ------------------------------------------------------------------
    def search(self, query: str) -> List[str]:
        """Return up to 10 organic Google result URLs for ``query``."""
        delay = random.uniform(3, 5)
        elapsed = time.time() - self._last_request
        if elapsed < delay:
            time.sleep(delay - elapsed)

        params = {"q": query, "num": 10, "hl": "en"}
        try:
            resp = requests.get(
                self.SEARCH_URL,
                params=params,
                headers=self._headers(),
                timeout=self.timeout,
            )
            self._last_request = time.time()
        except requests.exceptions.RequestException:
            return []

        if resp.status_code in {429, 503}:
            return []

        text_lower = resp.text.lower()
        if "unusual traffic" in text_lower or "captcha" in text_lower:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        try:
            return self._parse_results(soup)
        except Exception:
            # html structure changed
            return []


__all__ = ["RealGoogleSearcher"]
