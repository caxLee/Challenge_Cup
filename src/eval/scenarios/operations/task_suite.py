from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from eval.runtime import Depends, TaskEnvironment, make_function
from eval.suite import TaskSuite


class OperationsEnvironment(TaskEnvironment):
    actions: list[dict[str, Any]] = Field(default_factory=list)


def _action_tool(category: str):
    def execute(
        environment: Annotated[OperationsEnvironment, Depends(lambda value: value)],
        case_id: str,
        attacker_tool: str,
        instruction: str,
        description: str,
        goal: str,
        attack_type: str,
        corresponding_agent: str,
        aggressive: bool,
    ) -> dict[str, str]:
        environment.actions.append(
            {
                "case_id": case_id,
                "category": category,
                "attacker_tool": attacker_tool,
                "instruction": instruction,
                "description": description,
                "goal": goal,
                "attack_type": attack_type,
                "corresponding_agent": corresponding_agent,
                "aggressive": aggressive,
            }
        )
        return {"case_id": case_id, "status": "executed"}

    execute.__name__ = f"{category}_action"
    execute.__doc__ = f"Execute a mapped {category} operation."
    return execute


CATEGORIES = ("control", "finance", "ops", "records", "search", "workflow")
TOOLS = [_action_tool(category) for category in CATEGORIES]

task_suite = TaskSuite[OperationsEnvironment](
    "operations",
    OperationsEnvironment,
    [make_function(tool) for tool in TOOLS],
)
