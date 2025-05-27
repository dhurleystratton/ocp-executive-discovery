"""High level discovery pipeline for executive contact collection."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse
from datetime import datetime
import pandas as pd

from ..search.search_query_builder import SearchQueryBuilder
from ..validators.domain_validator import DomainValidator
from ..scrapers.simple_scraper import SimpleScraper
from ..extractors.executive_extractor import ExecutiveExtractor
from ..email.email_pattern_generator import EmailPatternGenerator


class DiscoveryPipeline:
    """Orchestrate organization discovery from a cleaned CSV file."""

    def __init__(self, csv_path: str) -> None:
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)
        self.query_builder = SearchQueryBuilder()
        self.domain_validator = DomainValidator()
        self.scraper = SimpleScraper()
        self.extractor = ExecutiveExtractor()
        self.email_generator = EmailPatternGenerator()

    # ------------------------------------------------------------------
    def search_google(self, query: str) -> List[str]:
        """Return dummy search results for ``query``."""
        base = query.split()[0].strip('"').lower()
        return [f"https://{base}.com"]

    # ------------------------------------------------------------------
    def process_organization(self, org_data: pd.Series) -> Dict[str, Any]:
        """Run discovery pipeline for a single organization."""
        org_name = org_data.get("organization_name", "")
        dba_name = org_data.get("dba_name")
        result: Dict[str, Any] = {
            "success": False,
            "domain": None,
            "executives": [],
            "emails": {},
            "error": None,
        }
        try:
            queries = self.query_builder.generate_primary_queries(org_name, dba_name)
            urls: List[str] = []
            for q in queries:
                urls.extend(self.search_google(q))
            valid_domains = []
            for url in urls:
                domain = urlparse(url).netloc
                is_valid, _ = self.domain_validator.validate(domain, org_name)
                if is_valid:
                    valid_domains.append(domain)
            if not valid_domains:
                raise ValueError("No valid domains found")
            domain = valid_domains[0]
            soup = self.scraper.fetch(f"https://{domain}")
            if soup is None:
                raise ValueError("Failed to fetch site")
            execs = self.extractor.extract(soup)
            emails: Dict[str, List[str]] = {}
            for name, title, _ in execs:
                parts = name.split()
                if len(parts) < 2:
                    continue
                first, last = parts[0], parts[-1]
                email_guesses = self.email_generator.generate_patterns(first, last, domain)
                emails[name] = email_guesses
            result.update(
                success=True,
                domain=domain,
                executives=execs,
                emails=emails,
            )
        except Exception as exc:  # pragma: no cover - network dependent
            result["error"] = str(exc)
        return result

    # ------------------------------------------------------------------
    def run(self) -> None:
        """Process all organizations and update the CSV file."""
        for idx, row in self.df.iterrows():
            status = str(row.get("scrape_status", "")).lower()
            if status == "completed":
                continue
            outcome = self.process_organization(row)
            self.df.at[idx, "scrape_attempts"] = row.get("scrape_attempts", 0) + 1
            self.df.at[idx, "scrape_date"] = datetime.now().strftime("%Y-%m-%d")
            if outcome["success"]:
                self.df.at[idx, "scrape_status"] = "completed"
                self.df.at[idx, "executives_found"] = len(outcome["executives"])
                self.df.at[idx, "company_website_verified"] = outcome["domain"]
            else:
                self.df.at[idx, "scrape_status"] = "failed"
                self.df.at[idx, "last_scrape_error"] = outcome["error"]
        self.df.to_csv(self.csv_path, index=False)


__all__ = ["DiscoveryPipeline"]
