from __future__ import annotations

import argparse
import importlib
import json
from dataclasses import asdict, dataclass

from .runtime import FunctionCall, FunctionsRuntime
from .tasks import BaseInjectionTask, BaseUserTask


SCENES = ("banking", "slack", "travel", "workspace")


@dataclass
class CheckResult:
    scene: str
    task: str
    kind: str
    passed: bool
    error: str | None = None


def load_suite(scene: str):
    if scene not in SCENES:
        raise ValueError(f"Unknown scene: {scene}")
    module = importlib.import_module(f"eval.scenarios.{scene}")
    return getattr(module, f"{scene}_task_suite")


def _execute(runtime: FunctionsRuntime, environment, calls: list[FunctionCall]) -> list[FunctionCall]:
    traces = []
    for call in calls:
        runtime.run_function(environment, call.function, call.args, raise_on_error=True)
        traces.append(call)
    return traces


def check_task(
    scene: str,
    task: BaseUserTask | BaseInjectionTask,
    suite,
    *,
    secure: bool = False,
) -> CheckResult:
    kind = "user" if isinstance(task, BaseUserTask) else "injection"
    try:
        environment = suite.load_environment()
        environment = task.init_environment(environment) if isinstance(task, BaseUserTask) else environment
        before = environment.model_copy(deep=True)
        if secure:
            from adapters import FidesRuntimeAdapter
            from agent_framework.security import SecureAgentConfig

            runtime = FidesRuntimeAdapter(
                suite.tools,
                tool_metadata={
                    tool.name: {"source_integrity": "trusted"} for tool in suite.tools
                },
                security=SecureAgentConfig(auto_hide_untrusted=False),
            )
            if isinstance(task, BaseInjectionTask):
                runtime.observe(task.GOAL)
        else:
            runtime = FunctionsRuntime(suite.tools)
        traces = _execute(runtime, environment, task.ground_truth(before))
        output = task.GROUND_TRUTH_OUTPUT
        if isinstance(task, BaseUserTask):
            trace_result = task.utility_from_traces(output, before, environment, traces)
            passed = trace_result if trace_result is not None else task.utility(output, before, environment)
        else:
            trace_result = task.security_from_traces(output, before, environment, traces)
            passed = trace_result if trace_result is not None else task.security(output, before, environment)
        return CheckResult(scene, task.ID, kind, bool(passed))
    except Exception as exc:
        return CheckResult(scene, task.ID, kind, False, f"{type(exc).__name__}: {exc}")


def check_scene(scene: str, *, secure: bool = False) -> list[CheckResult]:
    suite = load_suite(scene)
    tasks = [*suite.user_tasks.values(), *suite.injection_tasks.values()]
    return [check_task(scene, task, suite, secure=secure) for task in tasks]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate local task suites")
    parser.add_argument("--scene", choices=(*SCENES, "all"), default="all")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--secure", action="store_true", help="Run tools through the bundled security middleware")
    args = parser.parse_args()

    scenes = SCENES if args.scene == "all" else (args.scene,)
    results = [result for scene in scenes for result in check_scene(scene, secure=args.secure)]
    if args.as_json:
        print(json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2))
    else:
        for result in results:
            status = "PASS" if result.passed else "FAIL"
            suffix = f" - {result.error}" if result.error else ""
            print(f"{status} {result.scene}/{result.kind}/{result.task}{suffix}")
        passed = sum(result.passed for result in results)
        print(f"{passed}/{len(results)} checks passed")
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
