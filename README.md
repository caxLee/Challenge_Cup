# 项目说明

本项目提供面向工具调用型智能体的运行时安全治理能力，包括任务风险识别、工具调用拦截、分级审批、审计记录和评测脚本。项目由后端安全 API、前端演示页面、场景数据和评测模块组成。

## 部署运行说明

### 环境准备

项目要求 Python 3.10 及以上版本。建议在项目根目录创建并启用虚拟环境：

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e ".[test]"
```

Linux/macOS：

```bash
source .venv/bin/activate
pip install -e ".[test]"
```

如需启用语义风险分析器，复制 `.env.example` 为 `.env` 并配置 `MODEL_API_KEY`；不配置时系统仍可使用规则安全策略。

### 启动后端 API

在项目根目录执行：

```bash
python -m uvicorn api.app:app --app-dir src --host 0.0.0.0 --port 8000
```

启动后可访问：

- `GET http://localhost:8000/health`：健康检查。
- `GET http://localhost:8000/docs`：FastAPI 接口文档。
- `GET http://localhost:8000/demo/requests`：演示请求数据。

### 启动前端页面

前端依赖已位于 `frontend` 目录，首次运行时安装依赖：

```bash
cd frontend
npm install
```

开发模式启动：

```bash
npm run dev
```

生产构建：

```bash
npm run build
```

Vite 开发服务器默认监听 `http://localhost:3000`，后端 API 默认监听 `http://localhost:8000`。前端页面通过后端 API 完成任务提交、风险展示、审批和审计查看。

## 评测脚本说明

评测模块位于 `src/eval`，场景包括 `banking`、`slack`、`travel`、`workspace` 和 `operations`。运行评测前，在项目根目录设置源码路径：

```powershell
$env:PYTHONPATH="src"
```

### 场景任务评测

运行全部场景：

```bash
python -m eval.runner --scene all
```

运行指定场景：

```bash
python -m eval.runner --scene operations
```

通过安全中间件运行：

```bash
python -m eval.runner --scene all --secure
```

输出 JSON 结果，便于保存或二次处理：

```bash
python -m eval.runner --scene all --json
```

脚本会逐项执行正常任务和攻击任务，并根据 `utility()` 或 `security()` 的结果判断是否通过；`--secure` 会额外记录风险等级和处置结果。所有任务通过时进程返回码为 `0`，否则返回码为 `1`。

### API 集成评测

`api_eval` 使用 FastAPI 测试客户端验证健康检查、L2 确认、L3 独立审批、L4 阻断和审计接口：

```bash
python -m eval.api_eval
```

### 单元测试

```bash
pytest
```

## 攻击样例介绍

攻击样例位于 `datasets/raw/attacks/`，每个 JSONL 文件的一行对应一个攻击用例。样例覆盖权限提升、凭据获取、敏感数据外传、日志或记录篡改、命令注入、服务中断、流程操纵和检索结果污染等行为。

攻击样例按主题划分：

- `ops.jsonl`：运维、服务器和数据库相关攻击。
- `finance.jsonl`：资金、交易、报销和审批相关攻击。
- `records.jsonl`：档案、敏感信息、证书和业务记录相关攻击。
- `search.jsonl`：知识检索、政策文档、身份信息和内容完整性相关攻击。
- `workflow.jsonl`：订单、退款、合同、采购和项目流程相关攻击。
- `control.jsonl`：传感数据、控制权限、软件更新、通信和运行参数相关攻击。

每条样例主要包含以下字段：

- `Attacker Tool`：攻击工具名称。
- `Attacker Instruction`：交给智能体执行的伪装性或恶意指令。
- `Description`：攻击工具或攻击行为说明。
- `Attack goal`：攻击成功后应达到的目标。
- `Attack Type`：`Stealthy Attack` 或 `Disruptive Attack`。
- `Corresponding Agent`：目标智能体类型。
- `Aggressive`：是否属于激进攻击。

# 数据文件说明

## 攻击条目

文件：

- `datasets/raw/attacks/ops.jsonl`：40 条。包含提权、凭据获取、数据外传、日志篡改、备份破坏、命令注入和服务中断。
- `datasets/raw/attacks/finance.jsonl`：34 条。包含资金调拨、交易复制、报表篡改、未授权提现、账户创建和交易延迟。
- `datasets/raw/attacks/records.jsonl`：104 条。包含档案访问、敏感信息泄露、记录修改、证书签发和数据外发。
- `datasets/raw/attacks/search.jsonl`：40 条。包含检索结果篡改、引用操控、身份伪造、知识库破坏和材料泄露。
- `datasets/raw/attacks/workflow.jsonl`：78 条。包含订单修改、退款、价格调整、合同篡改、证据修改和材料越权共享。
- `datasets/raw/attacks/control.jsonl`：74 条。包含传感数据篡改、控制权限劫持、软件更新植入、通信中断和运行参数修改。

每行是一条攻击用例，字段含义：

- `Attacker Tool`：攻击工具名称。
- `Attacker Instruction`：交给智能体执行的恶意指令。
- `Description`：攻击工具或行为说明。
- `Attack goal`：攻击成功后应达到的目标。
- `Attack Type`：攻击类型，原数据为 `Stealthy Attack` 或 `Disruptive Attack`。
- `Corresponding Agent`：目标智能体类型。
- `Aggressive`：是否属于激进攻击。



## 正常任务

文件：`datasets/raw/scenarios/tasks/{banking,slack,travel,workspace}/user_tasks.py`

- `UserTaskN`：一条正常任务。
- `DIFFICULTY`：任务难度。
- `PROMPT`：用户提交的正常任务。
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

这些文件保存任务执行前的模拟数据，例如邮件、文件、日历、聊天记录、账户和交易。
