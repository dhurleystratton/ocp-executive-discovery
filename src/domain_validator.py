"""Domain validation utilities for executive discovery.

This module defines the :class:`DomainValidator` used to assess whether a
website domain likely belongs to a target organization. It filters out known
charity aggregator and social media sites (e.g., ``charitynavigator.org`` or
``linkedin.com``), performs fuzzy matching against the organization name, and
optionally checks that the domain resolves via DNS.

Example
-------
>>> from src.domain_validator import DomainValidator
>>> validator = DomainValidator()
>>> validator.validate("local123.org", "IBEW Local 123")
(True, 0.9)
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Iterable, Tuple
import re
import socket


class DomainValidator:
    """Validate organization website domains."""

    #: common aggregator sites that should not be treated as valid domains
    DEFAULT_BLACKLIST: Iterable[str] = [
        "charitynavigator.org",
        "yellowpages.com",
        "guidestar.org",
        "charitywatch.org",
        "greatnonprofits.org",
        "linkedin.com",
        "facebook.com",
        "twitter.com",
        "yelp.com",
        "bbb.org",
        "nonprofitfacts.com",
        "findnonprofits.com",
    ]

    def __init__(self, blacklist: Iterable[str] | None = None,
                 threshold: float = 0.6) -> None:
        """Create a new validator.

        Parameters
        ----------
        blacklist:
            Optional custom blacklist of domains to reject. By default
            :data:`DEFAULT_BLACKLIST` is used.
        threshold:
            Minimum relevance score required for a domain to be considered
            valid. Scores range from 0 to 1.
        """
        self.blacklist = {b.lower().strip() for b in (blacklist or self.DEFAULT_BLACKLIST)}
        self.threshold = threshold

    # ------------------------------------------------------------------
    def _normalize_domain(self, domain: str) -> str:
        """Return a normalized domain without scheme or trailing path."""
        dom = domain.lower().strip()
        dom = re.sub(r"^https?://", "", dom)
        dom = re.sub(r"/.*$", "", dom)
        dom = dom.lstrip("www.")
        return dom

    # ------------------------------------------------------------------
    def _domain_resolves(self, domain: str) -> bool:
        """Return ``True`` if ``domain`` has a DNS entry."""
        try:
            socket.getaddrinfo(domain, None)
            return True
        except OSError:
            return False

    # ------------------------------------------------------------------
    def _fuzzy_match_score(self, domain: str, organization: str) -> float:
        """Return fuzzy match ratio between domain and organization name."""
        base = domain.split(".")[0]
        base_clean = re.sub(r"[^a-z0-9]", "", base)
        org_clean = re.sub(r"[^a-z0-9]", "", organization.lower())
        ratio = SequenceMatcher(None, base_clean, org_clean).ratio()

        # handle union local patterns like "local123" matching "local 123"
        match = re.search(r"local(\d+)", base_clean)
        if match and re.search(rf"local\s*#?\s*{match.group(1)}", organization.lower()):
            ratio = max(ratio, 0.8)
        return ratio

    # ------------------------------------------------------------------
    def validate(self, domain: str, organization: str) -> Tuple[bool, float]:
        """Validate ``domain`` against ``organization``.

        Parameters
        ----------
        domain:
            Domain name to evaluate.
        organization:
            Target organization name to compare against.

        Returns
        -------
        tuple
            ``(is_valid, relevance_score)`` where ``relevance_score`` is a float
            between 0 and 1 representing confidence.
        """
        dom = self._normalize_domain(domain)
        if not dom:
            return False, 0.0

        if any(dom == b or dom.endswith("." + b) for b in self.blacklist):
            return False, 0.0

        score = self._fuzzy_match_score(dom, organization)
        if self._domain_resolves(dom):
            score = min(1.0, score + 0.1)
        else:
            score = max(0.0, score - 0.1)

        is_valid = score >= self.threshold
        return is_valid, round(score, 2)


__all__ = ["DomainValidator"]
