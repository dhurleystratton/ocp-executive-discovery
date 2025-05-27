"""Search query generation utilities for executive discovery.

This module provides the :class:`SearchQueryBuilder` used to construct
prioritized Google search queries for finding leadership information about
organizations. Queries include general phrases such as "leadership team" as
well as title-specific searches. Basic normalization handles union locals so
that names like "Local 123 IBEW" become "IBEW Local 123".
"""

from __future__ import annotations

import re
from typing import Iterable, List


class SearchQueryBuilder:
    """Create search queries targeting official organization websites."""

    #: common union abbreviations used for Local ### normalization
    UNION_ABBREVIATIONS = [
        "IBEW",
        "IBT",
        "TEAMSTERS",
        "SEIU",
        "UAW",
        "AFSCME",
        "CWA",
        "LIUNA",
        "UFCW",
        "AFT",
        "UNITE HERE",
        "IATSE",
        "USW",
        "IUOE",
        "IAM",
        "SMART",
    ]

    GENERAL_KEYWORDS = [
        "leadership executives",
        "leadership team",
        "executive team",
        "board of directors",
        "about us",
        "officers",
    ]

    # ------------------------------------------------------------------
    def _normalize_union_name(self, name: str) -> str:
        """Return union names in a consistent "ABBREV Local ###" format."""
        if not name:
            return name

        abbrev_pattern = rf"({'|'.join(self.UNION_ABBREVIATIONS)})"
        local_match = re.search(r"local\s*#?\s*(\d+)", name, flags=re.I)
        abbrev_match = re.search(abbrev_pattern, name, flags=re.I)
        if local_match and abbrev_match:
            number = local_match.group(1)
            abbrev = abbrev_match.group(1).upper()
            return f"{abbrev} Local {number}".strip()
        return name.strip()

    # ------------------------------------------------------------------
    def _base_names(self, org_name: str, dba_name: str | None) -> List[str]:
        """Return list of distinct organization names for query generation."""
        base = self._normalize_union_name(org_name)
        names = [base]
        if dba_name and dba_name.strip() and dba_name.strip().lower() != org_name.strip().lower():
            names.append(self._normalize_union_name(dba_name))
        # remove duplicates while preserving order
        seen = set()
        unique_names = []
        for n in names:
            if n not in seen:
                unique_names.append(n)
                seen.add(n)
        return unique_names

    # ------------------------------------------------------------------
    def generate_primary_queries(self, org_name: str, dba_name: str | None = None) -> List[str]:
        """Return high priority queries for locating leadership information.

        Parameters
        ----------
        org_name:
            Primary legal name of the organization.
        dba_name:
            Optional "doing business as" name.
        """
        queries: List[str] = []
        for name in self._base_names(org_name, dba_name):
            for kw in self.GENERAL_KEYWORDS:
                queries.append(f'"{name}" {kw}')
        return queries

    # ------------------------------------------------------------------
    def generate_title_specific_queries(self, org_name: str, missing_titles: Iterable[str]) -> List[str]:
        """Return queries targeting specific executive titles.

        Parameters
        ----------
        org_name:
            Organization name.
        missing_titles:
            Iterable of executive titles to search for, e.g. ["CEO", "Executive Director"].
        """
        queries: List[str] = []
        for name in self._base_names(org_name, None):
            for title in missing_titles:
                title_clean = title.strip().strip('"')
                queries.append(f'"{name}" "{title_clean}"')
        return queries

    # ------------------------------------------------------------------
    def generate_fallback_queries(self, org_name: str) -> List[str]:
        """Return generic fallback queries when primary searches fail."""
        name = self._normalize_union_name(org_name)
        return [
            f'"{name}" contact',
            f'"{name}" phone',
            f'"{name}" address',
            f'"{name}" staff directory',
        ]


__all__ = ["SearchQueryBuilder"]
