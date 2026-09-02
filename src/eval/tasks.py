from __future__ import annotations

import abc
import enum
from collections.abc import Sequence
from typing import Generic, TypeVar

from .runtime import FunctionCall, TaskEnvironment


class TaskDifficulty(enum.Enum):
    EASY = enum.auto()
    MEDIUM = enum.auto()
    HARD = enum.auto()


Env = TypeVar("Env", bound=TaskEnvironment)


class BaseUserTask(abc.ABC, Generic[Env]):
    ID: str
    PROMPT: str
    GROUND_TRUTH_OUTPUT: str = ""
    DIFFICULTY: TaskDifficulty = TaskDifficulty.EASY

    @staticmethod
    def init_environment(environment: Env) -> Env:
        return environment

    @abc.abstractmethod
    def ground_truth(self, pre_environment: Env) -> list[FunctionCall]: ...

    @abc.abstractmethod
    def utility(
        self,
        model_output: str,
        pre_environment: Env,
        post_environment: Env,
        strict: bool = True,
    ) -> bool: ...

    def utility_from_traces(
        self,
        model_output: str,
        pre_environment: Env,
        post_environment: Env,
        traces: Sequence[FunctionCall],
    ) -> bool | None:
        return None


class BaseInjectionTask(abc.ABC, Generic[Env]):
    ID: str
    GOAL: str
    GROUND_TRUTH_OUTPUT: str = ""
    DIFFICULTY: TaskDifficulty = TaskDifficulty.EASY

    @abc.abstractmethod
    def ground_truth(self, pre_environment: Env) -> list[FunctionCall]: ...

    @abc.abstractmethod
    def security(self, model_output: str, pre_environment: Env, post_environment: Env) -> bool: ...

    def security_from_traces(
        self,
        model_output: str,
        pre_environment: Env,
        post_environment: Env,
        traces: Sequence[FunctionCall],
    ) -> bool | None:
        return None
