from eval.scenarios.slack.injection_tasks import SlackInjectionTask  # noqa: F401 - Register tasks
from eval.scenarios.slack.task_suite import task_suite as slack_task_suite
from eval.scenarios.slack.user_tasks import SlackUserTask  # noqa: F401 - Register tasks

__all__ = ["slack_task_suite"]
