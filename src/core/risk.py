"""Small, deterministic risk policy for tool calls."""

from __future__ import annotations

from .contracts import (
    CanonicalSecurityEvent,
    DataLevel,
    Disposition,
    Integrity,
    Operation,
    RiskAssessment,
    RiskLevel,
)


_DISPOSITION = {
    RiskLevel.L0: Disposition.ALLOW,
    RiskLevel.L1: Disposition.AUDIT,
    RiskLevel.L2: Disposition.CONFIRM,
    RiskLevel.L3: Disposition.APPROVE,
    RiskLevel.L4: Disposition.BLOCK,
}


class RuleRiskEngine:
    """Classify runtime facts without inspecting prompts or case identifiers."""

    def evaluate(self, event: CanonicalSecurityEvent) -> RiskAssessment:
        matches: list[tuple[RiskLevel, str, str]] = []

        def add(level: RiskLevel, rule_id: str, reason: str) -> None:
            matches.append((level, rule_id, reason))

        external_destination = event.destination.get("trust") in {"external", "unknown"}
        state_changing = event.operation is not Operation.READ

        if event.operation is Operation.READ and event.data_level is DataLevel.PUBLIC:
            add(RiskLevel.L0, "public-read", "Public read-only operation")
        if event.operation is Operation.READ and event.data_level is DataLevel.INTERNAL:
            add(RiskLevel.L1, "internal-read", "Internal read-only operation")
        if "prompt_injection" in event.risk_signals:
            add(RiskLevel.L2, "injection-signal", "Prompt-injection signal detected")
        if "unregistered_tool" in event.risk_signals:
            add(RiskLevel.L4, "unregistered-tool", "Tool has no approved capability manifest")
        if set(event.risk_signals) & {"data_exfiltration", "credential_exposure"}:
            add(RiskLevel.L4, "semantic-egress", "Semantic analysis detected sensitive data exposure")
        if set(event.risk_signals) & {"privilege_escalation", "security_bypass"}:
            add(RiskLevel.L4, "semantic-privilege", "Semantic analysis detected privilege or security-control abuse")
        if "destructive_action" in event.risk_signals:
            add(RiskLevel.L4, "semantic-destruction", "Semantic analysis detected destructive action")
        if "arbitrary_code_execution" in event.risk_signals:
            add(RiskLevel.L3, "semantic-execution", "Semantic analysis detected arbitrary code execution")
        if event.operation is Operation.WRITE:
            add(RiskLevel.L2, "ordinary-write", "Operation changes business state")
        if event.operation is Operation.EXECUTE:
            add(RiskLevel.L3, "code-execution", "Operation executes code or commands")
        if event.data_level in {DataLevel.SENSITIVE, DataLevel.SECRET}:
            add(RiskLevel.L3, "sensitive-data", "Operation accesses sensitive data")
        if event.environment == "production" or event.privileged:
            add(RiskLevel.L3, "critical-context", "Production or privileged operation")
        if event.integrity is Integrity.UNTRUSTED and state_changing:
            add(RiskLevel.L3, "untrusted-influence", "Untrusted content influences a state-changing operation")
        if not event.authorized:
            add(RiskLevel.L4, "out-of-scope", "Operation exceeds the principal's authorization scope")
        if external_destination and event.data_level in {DataLevel.SENSITIVE, DataLevel.SECRET}:
            add(RiskLevel.L4, "sensitive-egress", "Sensitive data targets an external or unknown destination")
        if event.operation is Operation.SECURITY_CONTROL:
            add(RiskLevel.L4, "security-bypass", "Operation changes or bypasses security controls")
        if event.operation is Operation.DELETE and not event.reversible:
            add(RiskLevel.L4, "irreversible-delete", "Operation performs irreversible deletion")

        level = max((item[0] for item in matches), key=lambda value: int(value.value[1]), default=RiskLevel.L0)
        selected = [item for item in matches if item[0] is level]
        return RiskAssessment(
            level=level,
            disposition=_DISPOSITION[level],
            rule_ids=tuple(item[1] for item in selected),
            reasons=tuple(item[2] for item in selected),
        )
