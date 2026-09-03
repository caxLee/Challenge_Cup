"""Contracts for optional semantic risk signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence


RISK_SIGNALS = frozenset({
    "prompt_injection",
    "task_deviation",
    "data_exfiltration",
    "credential_exposure",
    "destructive_action",
    "privilege_escalation",
    "security_bypass",
    "arbitrary_code_execution",
})


@dataclass(frozen=True, slots=True)
class SemanticAnalysis:
    signals: tuple[str, ...] = ()
    confidence: float = 0.0
    evidence: tuple[str, ...] = ()
    error: str | None = None


class RiskAnalyzer(Protocol):
    def analyze(
        self,
        *,
        task: Mapping[str, Any],
        observations: Sequence[str],
        tool_name: str,
        arguments: Mapping[str, Any],
    ) -> SemanticAnalysis: ...
