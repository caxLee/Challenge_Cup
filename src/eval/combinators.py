from __future__ import annotations

from collections.abc import Sequence
from typing import Generic, TypeVar

from .runtime import FunctionCall, TaskEnvironment
from .tasks import BaseUserTask, TaskDifficulty


TaskT = TypeVar("TaskT", bound=BaseUserTask)
Env = TypeVar("Env", bound=TaskEnvironment)


class TaskCombinator(Generic[TaskT, Env]):
    def __init__(self, task_suite) -> None:
        self.task_suite = task_suite

    def create_combined_task(
        self,
        new_task_name: str,
        first: TaskT,
        second: TaskT,
        prompt: str | None = None,
    ) -> None:
        task_type = type(first)

        class CombinedTask(task_type):
            DIFFICULTY = TaskDifficulty.MEDIUM
            GROUND_TRUTH_OUTPUT = f"1. {first.GROUND_TRUTH_OUTPUT} 2. {second.GROUND_TRUTH_OUTPUT}"
            PROMPT = prompt or f"Complete these tasks in order: 1. {first.PROMPT} 2. {second.PROMPT}"

            def ground_truth(self, pre_environment: Env) -> list[FunctionCall]:
                return first.ground_truth(pre_environment) + second.ground_truth(pre_environment)

            def utility(self, model_output: str, pre_environment: Env, post_environment: Env, strict: bool = True) -> bool:
                return first.utility(model_output, pre_environment, post_environment, strict=False) and second.utility(
                    model_output, pre_environment, post_environment, strict=True
                )

            def utility_from_traces(
                self,
                model_output: str,
                pre_environment: Env,
                post_environment: Env,
                traces: Sequence[FunctionCall],
            ) -> bool | None:
                first_result = first.utility_from_traces(model_output, pre_environment, post_environment, traces)
                second_result = second.utility_from_traces(model_output, pre_environment, post_environment, traces)
                if first_result is None and second_result is None:
                    return None
                if first_result is None or second_result is None:
                    return False
                return first_result and second_result

        CombinedTask.__name__ = new_task_name
        self.task_suite.register_user_task(CombinedTask)
