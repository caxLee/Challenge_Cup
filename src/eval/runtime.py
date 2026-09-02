from __future__ import annotations

import dataclasses
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from typing import Annotated, Any, get_args, get_origin, get_type_hints

from pydantic import BaseModel


class TaskEnvironment(BaseModel):
    """Mutable state exposed to scenario tools."""


@dataclasses.dataclass(frozen=True)
class Depends:
    env_dependency: str | Callable[[BaseModel], BaseModel]

    def extract(self, environment: BaseModel) -> BaseModel:
        if callable(self.env_dependency):
            return self.env_dependency(environment)
        return getattr(environment, self.env_dependency)


class FunctionCall(BaseModel):
    function: str
    args: MutableMapping[str, Any]
    id: str | None = None
    placeholder_args: Mapping[str, Any] | None = None


@dataclasses.dataclass
class Function:
    name: str
    run: Callable[..., Any]
    dependencies: dict[str, Depends]


def make_function(function: Callable[..., Any]) -> Function:
    dependencies: dict[str, Depends] = {}
    for name, annotation in get_type_hints(function, include_extras=True).items():
        if get_origin(annotation) is Annotated:
            metadata = get_args(annotation)[1:]
            if metadata and isinstance(metadata[0], Depends):
                dependencies[name] = metadata[0]
    return Function(name=function.__name__, run=function, dependencies=dependencies)


class ToolNotFoundError(LookupError):
    pass


class FunctionsRuntime:
    def __init__(self, functions: Sequence[Function] = ()) -> None:
        self.functions = {function.name: function for function in functions}

    def _resolve_nested(self, environment: TaskEnvironment, value: Any) -> Any:
        if isinstance(value, FunctionCall):
            result, error = self.run_function(environment, value.function, value.args, raise_on_error=True)
            if error:
                raise RuntimeError(error)
            return result
        if isinstance(value, list):
            return [self._resolve_nested(environment, item) for item in value]
        if isinstance(value, dict):
            return {key: self._resolve_nested(environment, item) for key, item in value.items()}
        return value

    def run_function(
        self,
        environment: TaskEnvironment,
        function_name: str,
        arguments: Mapping[str, Any],
        *,
        raise_on_error: bool = False,
    ) -> tuple[Any, str | None]:
        function = self.functions.get(function_name)
        if function is None:
            error = f"ToolNotFoundError: {function_name}"
            if raise_on_error:
                raise ToolNotFoundError(error)
            return "", error

        try:
            resolved = {key: self._resolve_nested(environment, value) for key, value in arguments.items()}
            dependencies = {
                name: dependency.extract(environment) for name, dependency in function.dependencies.items()
            }
            return function.run(**(resolved | dependencies)), None
        except Exception as exc:
            if raise_on_error:
                raise
            return "", f"{type(exc).__name__}: {exc}"
