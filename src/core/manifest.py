"""Tool capability manifests and runtime event construction."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from .contracts import CanonicalSecurityEvent, DataLevel, Integrity, Operation
from .metadata import SourceDescriptor, ToolDescriptor, ToolMetadataResolver, TrustBoundary


@dataclass(frozen=True, slots=True)
class ToolProfile:
    name: str
    operation: Operation
    data_level: DataLevel = DataLevel.PUBLIC
    environment: str = "normal"
    reversible: bool = True
    privileged: bool = False
    read_only: bool = False
    open_world: bool = False
    destination_trust: str = "internal"
    source: SourceDescriptor | None = None

    def fides_metadata(self) -> dict[str, Any]:
        return ToolMetadataResolver().resolve(ToolDescriptor(
            read_only=self.read_only, open_world=self.open_world, source=self.source
        ))


class ToolManifest:
    def __init__(self, profiles: Mapping[str, ToolProfile] | None = None) -> None:
        self._profiles = dict(profiles or {})

    def get(self, name: str) -> ToolProfile | None:
        return self._profiles.get(name)

    def metadata(self) -> dict[str, dict[str, Any]]:
        return {name: profile.fides_metadata() for name, profile in self._profiles.items()}

    @classmethod
    def from_file(cls, path: str | Path) -> "ToolManifest":
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        profiles: dict[str, ToolProfile] = {}
        for name, item in raw.get("tools", {}).items():
            source_data = item.get("source")
            source = None if source_data is None else SourceDescriptor(
                boundary=TrustBoundary(source_data.get("boundary", "unknown")),
                authenticated=bool(source_data.get("authenticated", False)),
                open_world=bool(source_data.get("open_world", False)),
                confidentiality=source_data.get("confidentiality", "public"),
            )
            profiles[name] = ToolProfile(
                name=name,
                operation=Operation(item["operation"]),
                data_level=DataLevel(item.get("data_level", "public")),
                environment=item.get("environment", "normal"),
                reversible=bool(item.get("reversible", True)),
                privileged=bool(item.get("privileged", False)),
                read_only=bool(item.get("read_only", False)),
                open_world=bool(item.get("open_world", False)),
                destination_trust=item.get("destination_trust", "internal"),
                source=source,
            )
        return cls(profiles)


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    framework: str
    session_id: str
    principal: Mapping[str, Any]
    task: Mapping[str, Any] = field(default_factory=dict)
    sources: tuple[Mapping[str, Any], ...] = ()
    destination: Mapping[str, Any] = field(default_factory=dict)
    data_level: DataLevel | None = None
    environment: str | None = None
    reversible: bool | None = None
    authorized: bool = True
    risk_signals: tuple[str, ...] = ()
    observations: tuple[str, ...] = ()


class EventBuilder:
    """Combine connector facts with a registered tool capability profile."""

    def __init__(self, manifest: ToolManifest) -> None:
        self.manifest = manifest

    def build(
        self, tool_name: str, arguments: Mapping[str, Any], context: ExecutionContext
    ) -> CanonicalSecurityEvent:
        profile = self.manifest.get(tool_name)
        unknown = profile is None
        if profile is None:
            profile = ToolProfile(
                name=tool_name, operation=Operation.EXECUTE,
                privileged=True, reversible=False,
            )
        sources = tuple(dict(source) for source in context.sources)
        if profile.source is not None:
            sources = (*sources, {
                "boundary": profile.source.boundary.value,
                "integrity": profile.fides_metadata().get("source_integrity", "untrusted"),
            })
        untrusted = any(
            source.get("integrity") == Integrity.UNTRUSTED.value
            or source.get("boundary") in {"external", "unknown"}
            for source in sources
        )
        destination = {"trust": profile.destination_trust, **context.destination}
        signals = (*context.risk_signals, *(("unregistered_tool",) if unknown else ()))
        return CanonicalSecurityEvent(
            framework=context.framework,
            session_id=context.session_id,
            tool_name=tool_name,
            arguments=dict(arguments),
            integrity=Integrity.UNTRUSTED if untrusted else Integrity.TRUSTED,
            principal=dict(context.principal),
            task=dict(context.task),
            sources=sources,
            destination=dict(destination),
            operation=profile.operation,
            data_level=context.data_level or profile.data_level,
            environment=context.environment or profile.environment,
            reversible=profile.reversible if context.reversible is None else context.reversible,
            privileged=profile.privileged,
            authorized=context.authorized,
            risk_signals=signals,
        )
