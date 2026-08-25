# 数据文件说明

## 攻击条目

文件：`datasets/raw/attacks/all_attack_tools.jsonl`

每行是一条攻击用例，字段含义：

- `Attacker Tool`：攻击工具名称。
- `Attacker Instruction`：交给智能体执行的恶意指令，迁移场景时主要修改此字段。
- `Description`：攻击工具或行为说明。
- `Attack goal`：攻击成功后应达到的目标。
- `Attack Type`：攻击类型，原数据为 `Stealthy Attack` 或 `Disruptive Attack`。
- `Corresponding Agent`：目标智能体类型，迁移时改为对应的政企业务智能体。
- `Aggressive`：是否属于激进攻击。

## 正常任务

文件：`datasets/raw/scenarios/tasks/{banking,slack,travel,workspace}/user_tasks.py`

- `UserTaskN`：一条正常任务。
- `DIFFICULTY`：任务难度。
- `PROMPT`：用户提交的正常任务，迁移时改为政企业务任务。
- `ground_truth()`：完成正常任务所需的标准工具调用。
- `utility()`：判断正常任务是否完成。

## 攻击任务

文件：`datasets/raw/scenarios/tasks/{banking,slack,travel,workspace}/injection_tasks.py`

- `InjectionTaskN`：一条攻击任务。
- `DIFFICULTY`：攻击任务难度。
- `GOAL`：攻击者希望智能体执行的恶意目标。
- `_RECIPIENT`、`_FILE_ID` 等字段：攻击目标涉及的具体参数。
- `ground_truth()`：攻击成功时预期发生的工具调用。
- `security()`：根据执行后的环境状态判断攻击是否成功。

## 注入位置

文件：`datasets/raw/scenarios/environments/{banking,slack,travel,workspace}/injection_vectors.yaml`

- 顶层键：注入位置的唯一名称。
- `description`：恶意指令将被放入哪个数据对象或字段。
- `default`：未注入攻击指令时的原始内容。

## 环境数据

文件：`datasets/raw/scenarios/environments/{banking,slack,travel,workspace}/environment.yaml`

Workspace 的拆分数据文件：`datasets/raw/scenarios/environments/workspace/include/*.yaml`

这些文件保存任务执行前的模拟数据，例如邮件、文件、日历、聊天记录、账户和交易。迁移时修改其中的人员、机构、文档、业务记录和权限数据。
