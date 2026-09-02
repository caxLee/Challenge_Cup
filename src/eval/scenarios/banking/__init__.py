from eval.scenarios.banking.injection_tasks import BankingInjectionTask  # noqa: F401 - Register tasks
from eval.scenarios.banking.task_suite import task_suite as banking_task_suite
from eval.scenarios.banking.user_tasks import BankingUserTask  # noqa: F401 - Register tasks

__all__ = ["banking_task_suite"]
