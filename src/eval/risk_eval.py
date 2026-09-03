"""Smoke test for risk routing and FIDES approval round trips."""

from __future__ import annotations

from typing import Annotated

from adapters import FidesApprovalAdapter, FidesRuntimeAdapter
from core import (
    CanonicalSecurityEvent, DataLevel, Integrity, Operation, RuleRiskEngine, RiskLevel,
)
from pydantic import Field
from .runtime import Depends, TaskEnvironment, make_function


class Environment(TaskEnvironment):
    writes: list[str] = Field(default_factory=list)


def update_record(
    environment: Annotated[Environment, Depends(lambda value: value)], record_id: str
) -> str:
    environment.writes.append(record_id)
    return "updated"


def event(**changes: object) -> CanonicalSecurityEvent:
    values = {
        "framework": "validation", "session_id": "session-1", "tool_name": "records.update",
        "arguments": {"record_id": "42"}, "principal": {"id": "user-1", "role": "staff"},
    }
    values.update(changes)
    return CanonicalSecurityEvent(**values)  # type: ignore[arg-type]


def main() -> int:
    engine = RuleRiskEngine()
    approval = FidesApprovalAdapter()

    public_read = engine.evaluate(event(operation=Operation.READ, data_level=DataLevel.PUBLIC))
    ordinary_write_event = event(operation=Operation.WRITE)
    ordinary_write = engine.evaluate(ordinary_write_event)
    confirm_request = approval.request(ordinary_write_event, ordinary_write)
    confirmation = approval.resolve(
        ordinary_write_event, ordinary_write,
        confirm_request.to_function_approval_response(True), approver={"id": "user-1", "role": "staff"},
    )
    replay = approval.resolve(
        ordinary_write_event, ordinary_write,
        confirm_request.to_function_approval_response(True), approver={"id": "user-1", "role": "staff"},
    )

    sensitive_event = event(operation=Operation.READ, data_level=DataLevel.SENSITIVE)
    sensitive = engine.evaluate(sensitive_event)
    approval_request = approval.request(sensitive_event, sensitive)
    independent_approval = approval.resolve(
        sensitive_event, sensitive,
        approval_request.to_function_approval_response(True), approver={"id": "manager-1", "role": "approver"},
    )
    blocked = engine.evaluate(event(
        operation=Operation.EXFILTRATE, data_level=DataLevel.SECRET,
        integrity=Integrity.UNTRUSTED, destination={"trust": "external"},
    ))

    runtime = FidesRuntimeAdapter(
        [make_function(update_record)],
        tool_metadata={"update_record": {"source_integrity": "trusted"}},
    )
    runtime_event = event(tool_name="update_record", operation=Operation.WRITE)
    runtime_environment = Environment()
    runtime_request, _, _ = runtime.run_event(runtime_environment, runtime_event)
    _, runtime_error, _ = runtime.run_event(
        runtime_environment,
        runtime_event,
        approval_response=runtime_request.to_function_approval_response(True),
        approver={"id": "user-1", "role": "staff"},
    )

    checks = {
        "L0_public_read": public_read.level is RiskLevel.L0,
        "L2_user_confirmation": ordinary_write.level is RiskLevel.L2 and confirmation.approved,
        "approval_is_one_time": not replay.approved,
        "L3_independent_approval": sensitive.level is RiskLevel.L3 and independent_approval.approved,
        "L4_sensitive_egress": blocked.level is RiskLevel.L4,
        "approval_audited": len(approval.audit_log) == 5,
        "approval_controls_execution": runtime_error is None and runtime_environment.writes == ["42"],
    }
    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
