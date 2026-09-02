from eval.scenarios.workspace.injection_tasks import WorkspaceInjectionTask  # noqa: F401 - Register tasks
from eval.scenarios.workspace.task_suite import task_suite as workspace_task_suite
from eval.scenarios.workspace.user_tasks import WorkspaceUserTask  # noqa: F401 - Register tasks

__all__ = ["workspace_task_suite"]
