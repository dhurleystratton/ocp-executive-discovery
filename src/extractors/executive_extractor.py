from __future__ import annotations

from typing import List, Tuple
import re

from bs4 import BeautifulSoup

from ..validators.name_validator import NameValidator


class ExecutiveExtractor:
    """Extract executive names and titles from HTML content."""

    #: common executive titles to search for
    EXECUTIVE_TITLES: List[str] = [
        "chief executive officer",
        "ceo",
        "president",
        "executive director",
        "chief operating officer",
        "coo",
        "chief financial officer",
        "cfo",
        "chief technology officer",
        "cto",
        "vice president",
        "director",
        "board chair",
        "chair",
    ]

    #: keywords used to locate relevant sections of a webpage
    SECTION_KEYWORDS: List[str] = [
        "about",
        "leadership",
        "team",
        "staff",
        "board",
    ]

    def __init__(self, validator: NameValidator | None = None) -> None:
        self.validator = validator or NameValidator()
        title_pattern = r"|".join(re.escape(t) for t in self.EXECUTIVE_TITLES)
        self._title_regex = re.compile(rf"\b({title_pattern})\b", re.I)

    # ------------------------------------------------------------------
    def _candidate_sections(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        """Return HTML sections likely containing executive info."""
        sections: List[BeautifulSoup] = []
        for tag in soup.find_all(True):
            attrs = " ".join(
                [tag.get("id", "")] + [" ".join(tag.get("class", []))]
            ).lower()
            if any(kw in attrs for kw in self.SECTION_KEYWORDS):
                sections.append(tag)
        return sections or [soup]

    # ------------------------------------------------------------------
    def _extract_structured(self, section: BeautifulSoup) -> List[Tuple[str, str, float]]:
        """Return (name, title, confidence) from header + paragraph patterns."""
        results: List[Tuple[str, str, float]] = []
        for header in section.find_all(re.compile(r"^h[1-6]$")):
            name = header.get_text(" ", strip=True)
            next_el = header.find_next_sibling()
            if not next_el:
                continue
            title_text = next_el.get_text(" ", strip=True)
            if not self._title_regex.search(title_text):
                continue
            valid, conf = self.validator.validate(name, f"{name} {title_text}")
            if valid:
                results.append((name, title_text, conf))
        return results

    # ------------------------------------------------------------------
    def _extract_inline(self, text: str) -> List[Tuple[str, str, float]]:
        """Return (name, title, confidence) from inline text patterns."""
        results: List[Tuple[str, str, float]] = []
        # pattern: "John Smith, CEO"
        pattern_name_title = re.compile(
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*,\s*([^,\n]+)",
            re.M,
        )
        # pattern: "CEO: John Smith"
        pattern_title_name = re.compile(
            rf"({self._title_regex.pattern})\s*[:\-]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            re.I,
        )
        for match in pattern_name_title.finditer(text):
            name = match.group(1).strip()
            title = match.group(2).strip()
            if not self._title_regex.search(title):
                continue
            valid, conf = self.validator.validate(name, match.group(0))
            if valid:
                results.append((name, title, conf))
        for match in pattern_title_name.finditer(text):
            title = match.group(1).strip()
            name = match.group(2).strip()
            valid, conf = self.validator.validate(name, match.group(0))
            if valid:
                results.append((name, title, conf))
        return results

    # ------------------------------------------------------------------
    def extract(self, soup: BeautifulSoup) -> List[Tuple[str, str, float]]:
        """Return a list of detected executives from ``soup``."""
        results: List[Tuple[str, str, float]] = []
        for section in self._candidate_sections(soup):
            text = section.get_text(" ", strip=True)
            results.extend(self._extract_inline(text))
            results.extend(self._extract_structured(section))
        return results


__all__ = ["ExecutiveExtractor"]
