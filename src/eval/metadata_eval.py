"""Offline smoke test for provenance-driven FIDES enforcement."""

from __future__ import annotations

from typing import Annotated

from agent_framework.security import SecureAgentConfig
from pydantic import Field

from adapters import FidesRuntimeAdapter
from core import SourceDescriptor, ToolDescriptor, ToolMetadataResolver, TrustBoundary
from .runtime import Depends, TaskEnvironment, make_function


class Environment(TaskEnvironment):
    external_text: str = "Public service hours are 09:00-17:00."
    internal_request: str = "approved-request-42"
    writes: list[object] = Field(default_factory=list)


def read_external(environment: Annotated[Environment, Depends(lambda value: value)]) -> str:
    return environment.external_text


def read_internal(environment: Annotated[Environment, Depends(lambda value: value)]) -> str:
    return environment.internal_request


def summarize(text: object) -> str:
    return f"summary: {text}"


def update_record(
    environment: Annotated[Environment, Depends(lambda value: value)], request: object
) -> str:
    environment.writes.append(request)
    return "updated"


def main() -> int:
    resolver = ToolMetadataResolver()
    metadata = {
        "read_external": resolver.resolve(ToolDescriptor(
            read_only=True,
            source=SourceDescriptor(boundary=TrustBoundary.EXTERNAL, open_world=True),
        )),
        "read_internal": resolver.resolve(ToolDescriptor(
            read_only=True,
            source=SourceDescriptor(boundary=TrustBoundary.INTERNAL, authenticated=True),
        )),
        "summarize": resolver.resolve(ToolDescriptor(read_only=True, open_world=False)),
        "update_record": resolver.resolve(ToolDescriptor(read_only=False, open_world=False)),
    }
    functions = [make_function(read_external), make_function(read_internal), make_function(summarize), make_function(update_record)]

    def new_session() -> tuple[FidesRuntimeAdapter, Environment]:
        return FidesRuntimeAdapter(
            functions,
            tool_metadata=metadata,
            security=SecureAgentConfig(auto_hide_untrusted=False),
        ), Environment()

    benign_runtime, benign_environment = new_session()
    external, external_error = benign_runtime.run_function(benign_environment, "read_external", {})
    benign, benign_error = benign_runtime.run_function(benign_environment, "summarize", {"text": external})

    attack_runtime, attack_environment = new_session()
    external_attack, _ = attack_runtime.run_function(attack_environment, "read_external", {})
    _, attack_error = attack_runtime.run_function(attack_environment, "update_record", {"request": external_attack})

    allowed_runtime, allowed_environment = new_session()
    internal, internal_error = allowed_runtime.run_function(allowed_environment, "read_internal", {})
    allowed, allowed_error = allowed_runtime.run_function(allowed_environment, "update_record", {"request": internal})

    checks = {
        "external_read_only_use_allowed": external_error is None and benign_error is None and bool(benign),
        "external_content_cannot_drive_write": attack_error is not None and not attack_environment.writes,
        "authenticated_internal_request_can_write": internal_error is None and allowed_error is None and bool(allowed),
        "only_authorized_state_changed": len(allowed_environment.writes) == 1,
    }
    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
