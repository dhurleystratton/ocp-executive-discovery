"""Name validation utilities for executive discovery.

This module provides the :class:`NameValidator` class to help reduce the
false positive rate when extracting executive names from text sources. It
uses spaCy's named entity recognition (NER) model and additional heuristics
to determine whether a piece of text represents a valid person name.

Example
-------
>>> from src.name_validator import NameValidator
>>> validator = NameValidator()
>>> text = "Our CEO John Doe will attend the meeting"
>>> name = "John Doe"
>>> context = validator.extract_context(text, name)
>>> validator.validate(name, context)
(True, 0.9)
"""

from __future__ import annotations

from typing import List, Tuple

import re

try:
    import spacy
except ImportError:  # pragma: no cover - spaCy may not be available during docs generation
    spacy = None


class NameValidator:
    """Validate potential executive names using spaCy NER and heuristics."""

    #: default list of phrases that should not be considered names
    DEFAULT_FALSE_POSITIVES: List[str] = [
        "Annual Return",
        "Blue Cross",
        "Blue Shield",
        "Organization",
        "Corporation",
        # Additional false positives commonly found in Taft-Hartley data
        "Form 5500",
        "Benefit Plan",
        "Trust Fund",
        "Welfare Fund",
        "Pension Plan",
        "Medical Plan",
        "Health Plan",
    ]

    EXECUTIVE_TITLES: List[str] = [
        "chief executive officer",
        "ceo",
        "president",
        "director",
        "vice president",
        "chair",
        "secretary",
        "treasurer",
        "cfo",
        "coo",
        "cto",
        "chief",
    ]

    def __init__(self, model: str = "en_core_web_sm", context_window: int = 5,
                 false_positives: List[str] | None = None) -> None:
        """Initialize the validator.

        Parameters
        ----------
        model:
            Name of the spaCy model to load. ``en_core_web_sm`` is the
            default. If spaCy is not installed, NER checks will be skipped.
        context_window:
            Number of tokens to include on each side when extracting context.
        false_positives:
            Optional custom list of false positive phrases. If ``None``,
            :data:`DEFAULT_FALSE_POSITIVES` is used.
        """
        self.context_window = context_window
        self.false_positives = set(
            phrase.lower() for phrase in (false_positives or self.DEFAULT_FALSE_POSITIVES)
        )

        if spacy is not None:
            try:
                self.nlp = spacy.load(model)
            except Exception:  # pragma: no cover - handle missing model
                self.nlp = None
        else:  # pragma: no cover - spaCy import failed
            self.nlp = None

    # ------------------------------------------------------------------
    def extract_context(self, text: str, name: str) -> str:
        """Return surrounding text for a candidate name.

        The returned context includes ``context_window`` tokens before and
        after the first occurrence of ``name`` in ``text``.

        Parameters
        ----------
        text:
            Full text from which the name was extracted.
        name:
            Candidate name to search for in ``text``.

        Returns
        -------
        str
            Context string around the name. If the name is not found, an
            empty string is returned.
        """
        pattern = re.escape(name)
        match = re.search(pattern, text)
        if not match:
            return ""

        tokens = text.split()
        # find token index of the start word
        name_tokens = name.split()
        start_index = None
        for i in range(len(tokens)):
            if tokens[i:i + len(name_tokens)] == name_tokens:
                start_index = i
                break
        if start_index is None:
            return ""

        begin = max(0, start_index - self.context_window)
        end = min(len(tokens), start_index + len(name_tokens) + self.context_window)
        return " ".join(tokens[begin:end])

    # ------------------------------------------------------------------
    def _has_proper_capitalization(self, name: str) -> bool:
        """Return ``True`` if ``name`` is title-cased with no all-caps words."""
        if name.isupper() or name.islower():
            return False
        # ensure each token starts with an upper case letter
        return all(token[0].isupper() for token in name.split() if token)

    # ------------------------------------------------------------------
    def _has_executive_title(self, context: str) -> bool:
        """Check if an executive title appears in ``context``."""
        ctx = context.lower()
        return any(title in ctx for title in self.EXECUTIVE_TITLES)

    # ------------------------------------------------------------------
    def validate(self, name: str, context: str = "") -> Tuple[bool, float]:
        """Validate a potential executive name.

        Parameters
        ----------
        name:
            The text suspected to be a person's name.
        context:
            Optional surrounding text that may contain job titles.

        Returns
        -------
        tuple
            ``(is_valid, confidence)`` where ``confidence`` ranges from ``0``
            to ``1``.
        """
        name_clean = name.strip()
        if name_clean.lower() in self.false_positives:
            return False, 0.0

        if not self._has_proper_capitalization(name_clean):
            return False, 0.1

        confidence = 0.0
        is_person = False

        if self.nlp is not None:
            doc = self.nlp(name_clean)
            is_person = any(ent.label_ == "PERSON" for ent in doc.ents)
        else:
            # When spaCy isn't available, rely on capitalization heuristic
            is_person = bool(re.match(r"^[A-Z][a-z]+\s+[A-Z][a-z]+", name_clean))

        if not is_person:
            return False, 0.2

        confidence = 0.6  # base confidence if spaCy says it's a person

        if context and self._has_executive_title(context):
            confidence = min(1.0, confidence + 0.3)

        return True, confidence


__all__ = ["NameValidator"]
