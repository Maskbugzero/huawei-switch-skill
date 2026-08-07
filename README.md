# Huawei Switch Skill

> **本文件为项目通用概述**，适合快速了解功能和上手使用。
> Claude Code 专用实践请参考 `CLAUDE.md`；完整 Skill 定义请参考 `SKILL.md`。

**huawei-switch-skill** 是一个企业级的华为 VRP 交换机 Console 自动化 **Skill**。

它封装了从串口连接、命令执行、配置备份、解析、模板渲染、部署到校验的完整生命周期能力，可被 Claude Code、Hermes 或其他上层 Agent 系统直接调用。

**Skill 定位**：提供华为交换机网络自动化运维的标准化能力封装，而非自主 Agent。

### 场景分工（重要）

| 你要做什么 | 用什么 |
|------------|--------|
| 串口开局、改配置、模板部署 | **Console**（主路径） |
| 多台已纳管设备备份 / 跑命令 / 巡检 | **SSH 批量管理** |
| 出厂首次登录改密 | `SSHFirstConnect` |

Console 与 SSH **只是连接方式不同，VRP 命令相同**。当前配置能力做在 Console 上；SSH 面向后续批量运维。

## 项目状态

**当前版本：0.3.2**（见 `CHANGELOG.md` / `src.__version__`）

已完成 agent.md（历史文档）路线图 **第 1~7 阶段**，并完成配置主路径正确性加固、SSH 批量骨架、部署后浅层校验与金样例测试。

| 阶段 | 模块 | 状态 |
|------|------|------|
| 1 | 串口通信层 (console) | ✅ 完成 |
| 2 | 命令执行引擎 (command) | ✅ 完成 |
| 3 | 配置采集模块 (backup) | ✅ 完成 |
| 4 | 配置解析器 (parser) | ✅ 完成 |
| 5 | 模板系统 (template) | ✅ 完成 |
| 6 | 自动部署模块 (deploy) | ✅ 完成 |
| 7 | 配置校验模块 (verify) | ✅ 完成 |

## 核心功能（Skill Capabilities）

- 自动串口连接 + 登录 + 关闭分页
- 稳定命令执行（含 save 自动确认）
- 一键配置备份（按时间戳目录）
- 配置解析为结构化数据
- Jinja2 模板渲染
- 自动部署 + 回滚支持（含**幂等性检查 + Dry-Run 模式** + `DeploymentPlanner` 步骤规划）
- 配置一致性校验 + 报告生成
- 统一的 `AgentAdapter` Skill 调用入口

## 快速开始

```bash
pip install -r requirements.txt
```

### 推荐用法（通过 Skill 统一入口）⭐ 强烈推荐

**这是使用本 Skill 的推荐方式**，适用于 Claude Code、Hermes 或自定义 Agent 系统。

```python
from src.agent import AgentAdapter, AgentRequest, DeviceInfo

adapter = AgentAdapter()
request = AgentRequest(
    action="backup",                    # 或 "deploy", "command", "validate"
    device=DeviceInfo(port="COM4", password="xxx"),
    variables={"device_name": "SW-01"}
)
response = adapter.execute(request)
```

**注意**：CLI 中的 `deploy` 子命令已弃用，请优先使用 `AgentAdapter`。

### 基本用法示例（直接使用模块）

```python
from src.console import Connection

with Connection(port="COM4", password="your_password") as conn:
    print(conn.send_command("display version"))
```

### 完整备份 + 部署示例

```python
from src.console import Connection
from src.backup import ConfigCollector, ConfigExporter
from src.deploy import DeploymentEngine

with Connection(port="COM4", password="xxx") as conn:
    # 备份
    collector = ConfigCollector(conn)
    data = collector.collect_all()
    exporter = ConfigExporter()
    exporter.export_backup("SW-01", data)

    # 部署
    engine = DeploymentEngine()
    report = engine.deploy(
        connection=conn,
        template="access_switch.j2",
        variables={"hostname": "SW-01", "vlan_list": "10 20 30", "admin_password": "YourStrongPass@2026"},
        device_name="SW-01"
    )
    print(report)
```

## 项目结构

```
huawei-switch-skill/
├── SKILL.md              # Skill 元数据定义（规范格式）
├── README.md
├── docs/archive/agent.md # 开发路线图（历史文档，已归档）
├── examples/ (9 个示例)             # Skill 使用案例
│   ├── 01_connect_and_run_command.py
│   ├── 02_backup_config.py
│   ├── 03_using_agent_adapter.py
│   └── 04_template_deploy.py
├── src/
│   ├── console/     # 串口通信
│   ├── command/     # 命令执行
│   ├── backup/      # 配置采集与备份
│   ├── parser/      # 配置解析
│   ├── template/    # Jinja2 模板
│   ├── deploy/      # 自动部署
│   ├── verify/      # 配置校验
│   └── agent/       # Skill 统一调用入口 (AgentAdapter)
├── templates/ (4 个模板)
├── tests/
└── docs/            # 各模块详细文档
```

## 最近改进（2026-08）

- **0.3.2**：SSH 真下发默认禁用（需 `allow_ssh_deploy=True` 或仅 `dry_run`）；版本/LICENSE/联调产物忽略对齐
- **0.3.1**：Console 提示符/接口视图/description `##`/netmiko 4.x 真机加固
- **部署引擎安全默认**：
  - 幂等：意图子集匹配（非整机全量相等）
  - 危险命令默认 `blocked`（需 `allow_dangerous=True`）
  - 自动回滚默认关闭（实验性）
  - `AgentResponse.success` 随 `status` 正确反映失败/阻断
  - 主路径经 `CommandExecutor` 做错误检测
- **模板**：`admin_password` 必填，无弱默认口令
- 测试覆盖失败路径与 SSH 探测启发式

## 测试

项目已添加基础 Mock 测试，支持在无硬件环境下进行单元测试。

**重要**：本项目使用 `.venv` 虚拟环境，建议优先使用项目内的 Python 解释器运行命令。

```bash
# 推荐方式（直接使用项目 venv）
.\.venv\Scripts\python.exe -m pytest tests/ -v

# 或者先激活虚拟环境
.\.venv\Scripts\Activate.ps1
python -m pytest tests/ -v
```

```bash
# 安装测试依赖（首次使用时）
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 运行所有测试
.\.venv\Scripts\python.exe -m pytest tests/ -v

# 只运行 Console 模块测试
.\.venv\Scripts\python.exe -m pytest tests/test_console.py -v
```

目前已覆盖：
- Prompt 检测
- 分页处理
- 错误检测
- 命令解析
- Connection 上下文管理

更多测试用例正在持续添加中。

## 安全使用建议

- **密码处理**：请勿将密码硬编码在脚本中。推荐使用环境变量或交互式输入。
- CLI 中传入的 `--password` 可能出现在 shell 历史记录中，生产环境建议优先使用 Python `AgentAdapter` + 环境变量。
- 部署操作具有破坏性，始终建议开启 `backup=True`。

## 后续计划

- 丰富 SSH 批量管理（并发、结果汇总、与 DeploymentEngine 统一命令通道）
- 继续完善 `examples/` 与模板库
- 可选：图形界面

## 参考

- `docs/00-overview.md` — 项目整体概览
- `docs/archive/agent.md` — 完整开发路线图（历史文档）
- `docs/` — 各阶段详细 API 与用法示例（含 08-agent.md、09-ssh.md）



