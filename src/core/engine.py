"""Policy engine boundary; business policy is intentionally not implemented yet."""

from __future__ import annotations

from typing import Protocol

from .contracts import CanonicalSecurityEvent, PolicyDecision


class SecurityEngine(Protocol):
    """Implemented once and called by every framework-specific adapter."""

    async def evaluate(self, event: CanonicalSecurityEvent) -> PolicyDecision:
        """Return an allow, approval, or block decision for one tool call."""
        ...
