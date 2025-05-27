"""Email verification via DNS MX record lookup."""

from __future__ import annotations

import re
from typing import Dict

import dns.resolver


class DNSEmailVerifier:
    """Check whether an email's domain has MX records."""

    def __init__(self, cache: Dict[str, bool] | None = None, timeout: float = 2.0) -> None:
        """Create a new verifier.

        Parameters
        ----------
        cache:
            Optional dictionary used to cache domain lookups for speed.
        timeout:
            DNS resolution timeout in seconds.
        """
        self.cache: Dict[str, bool] = cache or {}
        self.timeout = timeout

    # ------------------------------------------------------------------
    def verify(self, email: str) -> bool:
        """Return ``True`` if the domain of ``email`` has MX records."""
        match = re.search(r"@([^@]+)$", email)
        if not match:
            return False

        domain = match.group(1).lower().strip()
        if domain in self.cache:
            return self.cache[domain]

        try:
            dns.resolver.resolve(domain, "MX", lifetime=self.timeout)
            self.cache[domain] = True
        except dns.resolver.DNSException:
            self.cache[domain] = False
        return self.cache[domain]


__all__ = ["DNSEmailVerifier"]
