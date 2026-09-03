"""Translate connector facts into metadata understood by the security runtime."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TrustBoundary(str, Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    USER = "user"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SourceDescriptor:
    """Facts supplied by a connector, independent of the content it returns."""

    boundary: TrustBoundary = TrustBoundary.UNKNOWN
    authenticated: bool = False
    open_world: bool = False
    confidentiality: str = "public"


@dataclass(frozen=True, slots=True)
class ToolDescriptor:
    """Capabilities advertised by a tool or its connector."""

    read_only: bool | None = None
    open_world: bool | None = None
    source: SourceDescriptor | None = None


class SourceResolver:
    """Resolve provenance facts without inspecting content or case labels."""

    def resolve(self, source: SourceDescriptor) -> dict[str, Any]:
        trusted = (
            source.boundary is TrustBoundary.INTERNAL
            and source.authenticated
            and not source.open_world
        )
        return {
            "source_integrity": "trusted" if trusted else "untrusted",
            "source_confidentiality": source.confidentiality,
        }


class ToolMetadataResolver:
    """Map generic/MCP-style capability facts to FIDES tool properties."""

    def __init__(self, source_resolver: SourceResolver | None = None) -> None:
        self.source_resolver = source_resolver or SourceResolver()

    def resolve(self, tool: ToolDescriptor) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        if tool.source is not None:
            metadata.update(self.source_resolver.resolve(tool.source))
        elif tool.open_world is not None:
            metadata["source_integrity"] = "untrusted" if tool.open_world else "trusted"

        # Match MCP semantics: only an explicit read-only declaration is a safe
        # source. Missing/false is treated as a possible state-changing sink.
        metadata["accepts_untrusted"] = tool.read_only is True
        if tool.read_only is not True:
            metadata["max_allowed_confidentiality"] = "public"
        return metadata
