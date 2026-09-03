"""Exercise the unified manifest-to-execution security path."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from adapters import FidesRuntimeAdapter
from core import DataLevel, ExecutionContext, RiskLevel, ToolManifest
from .runtime import Depends, TaskEnvironment, make_function


class Environment(TaskEnvironment):
    updates: list[str] = Field(default_factory=list)


def records_update(
    environment: Annotated[Environment, Depends(lambda value: value)], record_id: str
) -> str:
    environment.updates.append(record_id)
    return "updated"


def main() -> int:
    manifest = ToolManifest.from_file("config/tools.example.yaml")
    function = make_function(records_update)
    function.name = "records.update"
    runtime = FidesRuntimeAdapter(
        [function], tool_manifest=manifest,
    )
    environment = Environment()
    context = ExecutionContext(
        framework="demo", session_id="session-1",
        principal={"id": "user-1", "role": "staff"},
        task={"id": "task-1"}, sources=({"boundary": "internal"},),
    )
    request, error, assessment = runtime.run_tool(
        environment, "records.update", {"record_id": "42"}, context
    )
    _, approved_error, _ = runtime.run_tool(
        environment, "records.update", {"record_id": "42"}, context,
        approval_response=request.to_function_approval_response(True),
        approver={"id": "user-1", "role": "staff"},
    )
    _, unknown_error, unknown = runtime.run_tool(
        environment, "unknown_tool", {}, context
    )
    external_context = ExecutionContext(
        framework="demo", session_id="session-2",
        principal={"id": "user-1", "role": "staff"},
        sources=({"boundary": "external"},),
    )
    external_event = runtime.event_builder.build(
        "records.update", {"record_id": "43"}, external_context
    )
    external_risk = runtime.risk_engine.evaluate(external_event)
    sensitive_context = ExecutionContext(
        framework="demo", session_id="session-3",
        principal={"id": "user-1", "role": "staff"},
        data_level=DataLevel.SENSITIVE,
    )
    sensitive_event = runtime.event_builder.build(
        "records.update", {"record_id": "44"}, sensitive_context
    )
    sensitive_risk = runtime.risk_engine.evaluate(sensitive_event)
    checks = {
        "manifest_builds_L2_event": error is None and assessment.level is RiskLevel.L2,
        "approval_then_execution": approved_error is None and environment.updates == ["42"],
        "unknown_tool_fails_closed": unknown.level is RiskLevel.L4 and unknown_error is not None,
        "external_influence_upgrades_to_L3": external_risk.level is RiskLevel.L3,
        "runtime_data_classification_upgrades_to_L3": sensitive_risk.level is RiskLevel.L3,
    }
    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
