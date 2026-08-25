"""Translate framework-neutral labels to the upstream FIDES implementation."""

from __future__ import annotations

from agent_framework.security import (
    ConfidentialityLabel,
    ContentLabel,
    IntegrityLabel,
)

from core.contracts import CanonicalSecurityEvent


class FidesLabelAdapter:
    """A deliberately thin bridge; FIDES remains owned by the upstream package."""

    @staticmethod
    def content_label(event: CanonicalSecurityEvent) -> ContentLabel:
        metadata = {
            "framework": event.framework,
            "session_id": event.session_id,
            **event.principal,
        }
        return ContentLabel(
            integrity=IntegrityLabel(event.integrity.value),
            confidentiality=ConfidentialityLabel(event.confidentiality.value),
            metadata=metadata,
        )
