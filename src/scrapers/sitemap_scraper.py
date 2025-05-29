from __future__ import annotations

"""Sitemap driven scraper for discovering executive information."""

import io
import os
import re
import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .simple_scraper import SimpleScraper
from ..extractors.executive_extractor import ExecutiveExtractor


class SitemapScraper:
    """Scrape organization websites using their sitemap."""

    FILTER_KEYWORDS = [
        "about",
        "leadership",
        "board",
        "team",
        "governance",
        "staff",
    ]

    PRIORITY_KEYWORDS = ["leadership", "about/board", "team", "governance"]

    def __init__(self, delay: float = 1.0, timeout: int = 10,
                 cache_dir: str = "cache") -> None:
        self.scraper = SimpleScraper(timeout=timeout, delay=delay)
        self.extractor = ExecutiveExtractor()
        self.cache_dir = cache_dir
        self.pdf_links: List[str] = []

    # ------------------------------------------------------------------
    def _fetch_text(self, url: str) -> Optional[str]:
        """Return response text for ``url`` or ``None`` on error."""
        wait = self.scraper.delay - (time.time() - self.scraper._last_request)
        if wait > 0:
            time.sleep(wait)
        try:
            resp = requests.get(url, headers=self.scraper.headers,
                                timeout=self.scraper.timeout)
            self.scraper._last_request = time.time()
        except requests.exceptions.RequestException:
            return None
        if not resp.ok:
            return None
        return resp.text

    # ------------------------------------------------------------------
    def _discover_sitemaps(self, domain: str) -> List[str]:
        """Return sitemap URLs for ``domain``."""
        urls: List[str] = []
        robots_txt = self._fetch_text(f"https://{domain}/robots.txt")
        if robots_txt:
            for line in robots_txt.splitlines():
                if line.lower().startswith("sitemap:"):
                    url = line.split(":", 1)[1].strip()
                    if url:
                        urls.append(url)
        if not urls:
            for path in ["sitemap.xml", "sitemap_index.xml"]:
                url = f"https://{domain}/{path}"
                if self._fetch_text(url):
                    urls.append(url)
                    break
        return urls

    # ------------------------------------------------------------------
    def _parse_sitemap(self, content: str) -> List[str]:
        """Return all URLs listed in a sitemap XML ``content``."""
        urls: List[str] = []
        try:
            context = ET.iterparse(io.StringIO(content), events=("end",))
            for _, elem in context:
                tag = elem.tag.split('}', 1)[-1]
                if tag == "loc" and elem.text:
                    urls.append(elem.text.strip())
                elem.clear()
        except ET.ParseError:
            return []

        expanded: List[str] = []
        for u in urls:
            if u.endswith(".xml"):
                txt = self._fetch_text(u)
                if txt:
                    expanded.extend(self._parse_sitemap(txt))
            else:
                expanded.append(u)
        return expanded

    # ------------------------------------------------------------------
    def _candidate_urls(self, domain: str) -> List[str]:
        """Return sitemap URLs filtered and prioritized."""
        urls: List[str] = []
        for sm in self._discover_sitemaps(domain):
            content = self._fetch_text(sm)
            if not content:
                continue
            urls.extend(self._parse_sitemap(content))
        # record pdf links and drop them from html candidates
        for u in urls:
            if u.lower().endswith(".pdf"):
                self.pdf_links.append(u)
        urls = [u for u in urls if not u.lower().endswith(".pdf")]
        filtered = [
            u for u in urls
            if any(kw in u.lower() for kw in self.FILTER_KEYWORDS)
        ]
        priority = [
            u for u in filtered
            if any(pk in u.lower() for pk in self.PRIORITY_KEYWORDS)
        ]
        others = [u for u in filtered if u not in priority]
        return priority + others

    # ------------------------------------------------------------------
    def _slugify(self, url: str) -> str:
        path = urlparse(url).path
        if not path or path == "/":
            return "index"
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", path.strip("/"))
        return slug or "page"

    # ------------------------------------------------------------------
    def scrape(self, org_name: str, domain: str) -> List[Dict[str, str]]:
        """Return executive data for ``domain``."""
        results: List[Dict[str, str]] = []
        urls = self._candidate_urls(domain)
        os.makedirs(os.path.join(self.cache_dir, domain), exist_ok=True)
        total_batches = (len(urls) - 1) // 20 + 1 if urls else 0
        for i in range(0, len(urls), 20):
            print(f"Processing batch {i//20 + 1}/{total_batches}")
            batch = urls[i:i + 20]
            for url in batch:
                print(f"Fetching {url}")
                soup = self.scraper.fetch(url)
                if soup is None:
                    continue
                slug = self._slugify(url)
                html_path = os.path.join(self.cache_dir, domain, f"{slug}.html")
                text_path = os.path.join(self.cache_dir, domain, f"{slug}.txt")
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(str(soup))
                with open(text_path, "w", encoding="utf-8") as f:
                    f.write(soup.get_text(" ", strip=True))
                for name, title, _ in self.extractor.extract(soup):
                    results.append({
                        "name": name,
                        "title": title,
                        "url": url,
                    })
        print(f"Found {len(results)} executives across {len(urls)} pages")
        return results


__all__ = ["SitemapScraper"]
