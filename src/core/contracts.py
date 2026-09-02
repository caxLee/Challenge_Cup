"""Minimal contracts shared by all runtime and benchmark adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Integrity(str, Enum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"


class Confidentiality(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    USER_IDENTITY = "user_identity"


class Decision(str, Enum):
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    BLOCK = "block"


class RiskLevel(str, Enum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


class Disposition(str, Enum):
    ALLOW = "allow"
    AUDIT = "audit"
    CONFIRM = "confirm"
    APPROVE = "approve"
    BLOCK = "block"


class Operation(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    EXFILTRATE = "exfiltrate"
    SECURITY_CONTROL = "security_control"


class DataLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    SECRET = "secret"


@dataclass(frozen=True, slots=True)
class CanonicalSecurityEvent:
    """A tool call expressed independently of any agent framework."""

    framework: str
    session_id: str
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    integrity: Integrity = Integrity.TRUSTED
    confidentiality: Confidentiality = Confidentiality.PUBLIC
    principal: dict[str, Any] = field(default_factory=dict)
    task: dict[str, Any] = field(default_factory=dict)
    sources: tuple[dict[str, Any], ...] = ()
    destination: dict[str, Any] = field(default_factory=dict)
    operation: Operation = Operation.READ
    data_level: DataLevel = DataLevel.PUBLIC
    environment: str = "normal"
    reversible: bool = True
    privileged: bool = False
    authorized: bool = True
    risk_signals: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    level: RiskLevel
    disposition: Disposition
    reasons: tuple[str, ...]
    rule_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    decision: Decision
    reasons: tuple[str, ...] = ()
    policy_ids: tuple[str, ...] = ()
    risk_score: int | None = None
