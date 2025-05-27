"""Email verification via SMTP handshake.

This module defines :class:`SMTPEmailVerifier` which checks whether an email
address is likely valid by communicating with the recipient's mail server.
It performs a minimal SMTP handshake (``HELO``, ``MAIL FROM``, ``RCPT TO``)
without sending any message data.
"""

from __future__ import annotations

import re
import socket
import smtplib
from typing import List

try:
    import dns.resolver  # type: ignore
except Exception:  # pragma: no cover - dns may be optional
    dns = None  # type: ignore


class SMTPEmailVerifier:
    """Validate email addresses by connecting to their mail servers."""

    def __init__(self, from_address: str = "verify@example.com", timeout: int = 10) -> None:
        """Create a new verifier instance.

        Parameters
        ----------
        from_address:
            Address used in the ``MAIL FROM`` command.
        timeout:
            Seconds to wait when connecting to the SMTP server.
        """
        self.from_address = from_address
        self.timeout = timeout

    # ------------------------------------------------------------------
    def _get_mx_hosts(self, domain: str) -> List[str]:
        """Return list of MX hosts for ``domain``."""
        if dns is None:
            return [domain]
        try:
            answers = dns.resolver.resolve(domain, "MX")  # type: ignore[attr-defined]
        except Exception:
            return [domain]
        records = sorted(
            [(r.preference, r.exchange.to_text()) for r in answers],
            key=lambda t: t[0],
        )
        return [host.rstrip('.') for _, host in records]

    # ------------------------------------------------------------------
    def verify(self, email: str) -> bool:
        """Return ``True`` if ``email`` appears valid via SMTP."""
        match = re.search(r"@([\w.-]+)$", email)
        if not match:
            return False
        domain = match.group(1)
        hosts = self._get_mx_hosts(domain)
        for host in hosts:
            try:
                with smtplib.SMTP(host, 25, timeout=self.timeout) as server:
                    server.helo(socket.gethostname())
                    server.mail(self.from_address)
                    code, _ = server.rcpt(email)
                    if code in (250, 251):
                        return True
            except Exception:
                continue
        return False


__all__ = ["SMTPEmailVerifier"]
