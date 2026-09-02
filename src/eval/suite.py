from __future__ import annotations

import copy
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Generic, TypeVar

import yaml
from pydantic import BaseModel

from .runtime import Function, TaskEnvironment
from .tasks import BaseInjectionTask, BaseUserTask
from .yaml_loader import dump_yaml, load_yaml


Env = TypeVar("Env", bound=TaskEnvironment)
Version = tuple[int, int, int]


class InjectionVector(BaseModel):
    description: str
    default: str


def _compatible(items: dict[str, dict[Version, object]], version: Version) -> dict[str, object]:
    result = {}
    for item_id, versions in items.items():
        candidates = [candidate for candidate in versions if candidate <= version]
        if candidates:
            result[item_id] = versions[max(candidates)]
    return result


class TaskSuite(Generic[Env]):
    def __init__(
        self,
        name: str,
        environment_type: type[Env],
        tools: list[Function],
        data_path: Path | None = None,
        version: Version = (1, 0, 0),
    ) -> None:
        self.name = name
        self.environment_type = environment_type
        self.tools = tools
        self.data_path = data_path or Path(__file__).resolve().parents[2] / "datasets" / "raw" / "scenarios" / "environments" / name
        self.version = version
        self._user_tasks: dict[str, dict[Version, BaseUserTask[Env]]] = defaultdict(dict)
        self._injection_tasks: dict[str, dict[Version, BaseInjectionTask[Env]]] = defaultdict(dict)

    @staticmethod
    def _number(task_type: type, prefix: str) -> int:
        match = re.match(rf"{prefix}(\d+)", task_type.__name__)
        if match is None:
            raise ValueError(f"Task class must be named {prefix}<number>: {task_type.__name__}")
        return int(match.group(1))

    def register_user_task(self, task_type: type[BaseUserTask[Env]]) -> type[BaseUserTask[Env]]:
        task_id = f"user_task_{self._number(task_type, 'UserTask')}"
        task_type.ID = task_id
        self._user_tasks[task_id][(1, 0, 0)] = task_type()
        return task_type

    def register_injection_task(
        self, task_type: type[BaseInjectionTask[Env]]
    ) -> type[BaseInjectionTask[Env]]:
        task_id = f"injection_task_{self._number(task_type, 'InjectionTask')}"
        task_type.ID = task_id
        self._injection_tasks[task_id][(1, 0, 0)] = task_type()
        return task_type

    def update_user_task(self, version: Version):
        def decorator(task_type: type[BaseUserTask[Env]]) -> type[BaseUserTask[Env]]:
            task_id = f"user_task_{self._number(task_type, 'UserTask')}"
            task_type.ID = task_id
            self._user_tasks[task_id][version] = task_type()
            return task_type

        return decorator

    @property
    def user_tasks(self) -> dict[str, BaseUserTask[Env]]:
        return _compatible(self._user_tasks, self.version)  # type: ignore[return-value]

    @property
    def injection_tasks(self) -> dict[str, BaseInjectionTask[Env]]:
        return _compatible(self._injection_tasks, self.version)  # type: ignore[return-value]

    @lru_cache
    def get_user_task_by_id(self, task_id: str) -> BaseUserTask[Env]:
        return self.user_tasks[task_id]

    def get_injection_task_by_id(self, task_id: str) -> BaseInjectionTask[Env]:
        return self.injection_tasks[task_id]

    def get_injection_vector_defaults(self) -> dict[str, str]:
        raw = load_yaml(self.data_path / "injection_vectors.yaml")
        return {name: InjectionVector.model_validate(value).default for name, value in raw.items()}

    def load_environment(self, injections: dict[str, str] | None = None) -> Env:
        injections = injections or {}
        defaults = self.get_injection_vector_defaults()
        unknown = set(injections) - set(defaults)
        if unknown:
            raise ValueError(f"Unknown injection vectors: {sorted(unknown)}")
        values = defaults | injections
        expanded = load_yaml(self.data_path / "environment.yaml")
        rendered = dump_yaml(expanded).format(**values)
        return self.environment_type.model_validate(yaml.safe_load(rendered))

    def copy_environment(self, injections: dict[str, str] | None = None) -> Env:
        return copy.deepcopy(self.load_environment(injections))
