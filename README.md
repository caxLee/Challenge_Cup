# 协作开发说明

> **禁止直接向 `master` 提交或推送代码（已关闭权限）。每项修改必须从最新的 `master` 创建功能分支，完成后推送分支并发起合并。**

## 分支命名

修改 `datasets/raw/attacks/` 下的攻击条目：

```text
att/<真实文件名>_<修改行数>
```

示例：

```text
att/control_xx-xx
att/finance_xx-xx
```

修改 `datasets/raw/scenarios/` 下的场景任务：

```text
sce/<场景名>/<文件类型>_<修改行数>
```

示例：

```text
sce/banking/user_xx-xx
sce/workspace/injection_xx-xx
```

其中，攻击条目的 `<真实文件名>` 使用实际 JSONL 文件名且不带 `.jsonl`；场景名使用 `banking`、`slack`、`travel` 或 `workspace`，文件类型使用 `user`、`injection` 或 `environment`。

## Git 操作

开始修改前：

```bash
git switch master
git pull origin master
git switch -c att/control_xx-xx
```

场景任务将最后一行替换为对应分支，例如：

```bash
git switch -c sce/banking/user_xx-xx
```

完成修改后：

```bash
git add <修改的文件>
git commit -m "说明本次修改内容"
git push -u origin <分支名>
```

推送后在 GitHub 发起合并请求，不要使用 `git push origin master`。

# 数据文件说明

## 攻击条目

文件：

- `datasets/raw/attacks/ops.jsonl`：40 条。包含提权、凭据获取、数据外传、日志篡改、备份破坏、命令注入和服务中断，可迁移到政企运维、数据库及服务器管理场景。
- `datasets/raw/attacks/finance.jsonl`：34 条。包含资金调拨、交易复制、报表篡改、未授权提现、账户创建和交易延迟，可迁移到预算、报销、采购付款及资金审批场景。
- `datasets/raw/attacks/records.jsonl`：104 条。包含档案访问、敏感信息泄露、记录修改、证书签发和数据外发，可迁移到人员档案、群众信息、项目材料及政务业务记录场景。
- `datasets/raw/attacks/search.jsonl`：40 条。包含检索结果篡改、引用操控、身份伪造、知识库破坏和材料泄露，可迁移到内部知识库、政策检索、制度查询及报告生成场景。
- `datasets/raw/attacks/workflow.jsonl`：78 条。包含订单修改、退款、价格调整、合同篡改、证据修改和材料越权共享，可迁移到采购、审批、合同、工单及项目流程场景。
- `datasets/raw/attacks/control.jsonl`：74 条。包含传感数据篡改、控制权限劫持、软件更新植入、通信中断和运行参数修改，可迁移到城市设施、物联网、机房及运维控制场景。

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
