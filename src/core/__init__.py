"""Stable, framework-neutral contracts."""

from .contracts import CanonicalSecurityEvent, PolicyDecision
from .engine import SecurityEngine
from .metadata import (
    SourceDescriptor,
    SourceResolver,
    ToolDescriptor,
    ToolMetadataResolver,
    TrustBoundary,
)

__all__ = [
    "CanonicalSecurityEvent",
    "PolicyDecision",
    "SecurityEngine",
    "SourceDescriptor",
    "SourceResolver",
    "ToolDescriptor",
    "ToolMetadataResolver",
    "TrustBoundary",
]
