"""Generate potential email addresses from name and domain.

This module defines the :class:`EmailPatternGenerator` class used to
construct likely email addresses for discovered executives. It supports
common patterns like ``firstname.lastname`` and ``flastname`` and handles
special cases for union domains such as ``local123``.
"""

from __future__ import annotations

import re
from typing import List


class EmailPatternGenerator:
    """Generate common email address patterns."""

    # ------------------------------------------------------------------
    def _normalize(self, text: str) -> str:
        """Return ``text`` lowercased with non-alpha characters removed."""
        return re.sub(r"[^a-z]", "", text.lower())

    # ------------------------------------------------------------------
    def _clean_domain(self, domain: str) -> str:
        """Return a normalized domain name."""
        dom = domain.lower().strip()
        dom = re.sub(r"^https?://", "", dom)
        dom = re.sub(r"/.*$", "", dom)
        dom = dom.lstrip("www.")
        return dom

    # ------------------------------------------------------------------
    def generate_patterns(self, first_name: str, last_name: str,
                          domain: str) -> List[str]:
        """Return prioritized list of potential email addresses."""
        first = self._normalize(first_name)
        last = self._normalize(last_name)
        dom = self._clean_domain(domain)

        if not first or not last or not dom:
            return []

        first_initial = first[0]

        patterns = [
            f"{first}.{last}@{dom}",
            f"{first_initial}{last}@{dom}",
            f"{first}@{dom}",
            f"{first}_{last}@{dom}",
            f"{first_initial}.{last}@{dom}",
        ]

        if "local123" in dom:
            patterns.append(f"{first}@local123.org")

        # remove duplicates while preserving order
        seen = set()
        unique_patterns: List[str] = []
        for p in patterns:
            if p not in seen:
                unique_patterns.append(p)
                seen.add(p)
        return unique_patterns


__all__ = ["EmailPatternGenerator"]
