from eval.scenarios.tools.banking_client import (
    BankAccount,
    get_balance,
    get_iban,
    get_most_recent_transactions,
    get_scheduled_transactions,
    schedule_transaction,
    send_money,
    update_scheduled_transaction,
)
from eval.scenarios.tools.file_reader import Filesystem, read_file
from eval.scenarios.tools.user_account import UserAccount, get_user_info, update_password, update_user_info
from eval.runtime import TaskEnvironment, make_function
from eval.suite import TaskSuite


class BankingEnvironment(TaskEnvironment):
    bank_account: BankAccount
    filesystem: Filesystem
    user_account: UserAccount


TOOLS = [
    get_iban,
    send_money,
    schedule_transaction,
    update_scheduled_transaction,
    get_balance,
    get_most_recent_transactions,
    get_scheduled_transactions,
    read_file,
    get_user_info,
    update_password,
    update_user_info,
]

task_suite = TaskSuite[BankingEnvironment]("banking", BankingEnvironment, [make_function(tool) for tool in TOOLS])
