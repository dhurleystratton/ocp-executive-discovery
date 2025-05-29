#!/usr/bin/env python3
"""Command line interface for :class:`SitemapScraper`."""

from __future__ import annotations

import sys
from pprint import pprint

from src.scrapers.sitemap_scraper import SitemapScraper


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: run_sitemap_scraper.py <organization name> <domain>")
        raise SystemExit(1)
    org_name = sys.argv[1]
    domain = sys.argv[2]
    scraper = SitemapScraper()
    results = scraper.scrape(org_name, domain)
    pprint(results)
    if scraper.pdf_links:
        print("\nPDF links discovered:")
        pprint(scraper.pdf_links)


if __name__ == "__main__":
    main()
