---
name: huawei-switch-skill
description: "Use when automating Huawei VRP switches: Console for single-device config/deploy, or SSH batch management (inventory backup/command) for managed fleets; also first-login password change."
version: 0.4.0
author: User
license: MIT
tags:
  - huawei
  - switch
  - console
  - network-automation
  - jinja2
  - deployment
  - backup
  - parser
  - vrp
categories:
  - network
  - infrastructure
  - automation
capabilities:
  - serial-console-communication
  - automated-login-and-pager-disable
  - command-execution-with-error-handling
  - dedicated-error-codes-and-exceptions
  - configuration-backup-and-export
  - structured-config-parsing
  - jinja2-template-rendering
  - automated-deployment-with-idempotency-and-rollback
  - ssh-first-connect-with-password-change
  - ssh-mode-agent-adapter-support
  - configuration-verification-and-reporting
  - comprehensive-error-handling-examples
entrypoints:
  python:
    - "from src.console import Connection"
    - "from src.backup import ConfigCollector, ConfigExporter"
    - "from src.deploy import DeploymentEngine"
    - "from src.agent import AgentAdapter"
  cli:
    - "python main.py connect --port COM4 --password xxx"
    - "python main.py backup --port COM4 --password xxx --device SW-01"
dependencies:
  - pyserial>=3.5
  - jinja2>=3.1.0
  - pyyaml>=6.0
  - paramiko
  - netmiko
  - pydantic>=2.0
related_skills: []
---

# 虚拟环境要求（重要）

本 Skill **必须**使用项目自带的虚拟环境，以保证依赖隔离和可复现性。

**执行规则**：

1. 所有 Python 命令**必须**通过项目内的 `.venv` 执行
2. 如果 `.venv` 不存在，**必须先创建**再使用
3. 禁止直接使用系统全局 Python（`python` / `python3`）

**推荐命令格式**：

```powershell
# Windows（推荐直接调用）
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py backup --port COM4 --password xxx --device SW-01

# 或者激活后使用
.\.venv\Scripts\Activate.ps1
python -m pytest tests/ -v
```

**创建虚拟环境（如果不存在）**：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

# Huawei Switch Skill

基于 Python 的华为交换机 Console 自动化 Skill，支持从连接、备份、解析、模板渲染、部署到校验的完整配置生命周期管理。

## 概述

`huawei-switch-skill` 是华为 VRP 交换机自动化 Skill。**Console 与 SSH 只是连接方式不同，VRP 配置命令相同**；当前产品按使用场景分工如下：

| 场景 | 连接方式 | 定位 |
|------|----------|------|
| **单台初始化 / 改配置** | **Console（主路径）** | 备份、模板部署、校验、完整 `DeploymentEngine` |
| **已纳管设备日常/批量运维** | **SSH（批量管理）** | 多设备 backup、command；后续扩展批量巡检与配置 |
| **首次上线强制改密** | SSH（`SSHFirstConnect`） | 独立小工具，不走主配置流 |

**设计原则**：
- **Console = 配置主路径**（最稳、能力最全）
- **SSH = 批量管理通道**（清单驱动，可并发扩展）
- 命令层应复用同一套采集/执行/校验能力，避免两套 CLI 语义
- 模块化、可 Mock、统一 `AgentAdapter` 入口

## 核心能力

| 能力 | 模块 | 说明 |
|------|------|------|
| 串口连接与认证 | `console` | 配置主路径的连接层 |
| 稳定命令执行 | `command` | 错误检测、save 确认（Console 主路径已接入） |
| 配置备份与归档 | `backup` | 时间戳目录；Console / SSH / 批量共用导出 |
| 配置解析 | `parser` | 结构化对象 |
| 模板渲染 | `template` | Jinja2（`admin_password` 必填） |
| 自动部署 | `deploy` | **仅推荐 Console**；危险命令默认阻断、意图子集幂等、Dry-Run |
| 配置校验 | `verify` | 规则校验 |
| SSH 首次改密 | `ssh.first_connect` | 上线改密 |
| SSH 批量管理 | `ssh.batch` | 设备清单 + 批量 backup/command |
| 统一入口 | `agent` | `AgentAdapter` |

**连接方式怎么选**：
1. 机房串口改配置、开局、模板部署 → **Console + `AgentAdapter` / `DeploymentEngine`**
2. 网上多台已通 SSH 的设备备份/巡检/跑命令 → **SSH 批量（`BatchSSHManager`）或 `DeviceInfo(connection_type="ssh")`**
3. 出厂首次登录要改密 → **`SSHFirstConnect`**
4. 单台 SSH deploy **默认禁用**；仅 `dry_run=True` 或显式 `allow_ssh_deploy=True` 才走实验路径。生产改配置优先 Console

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 最简用法（Console 连接）

```python
from src.console import Connection

with Connection(port="COM4", password="your_password") as conn:
    version = conn.send_command("display version")
    print(version)
```

### 一键备份配置

```python
from src.console import Connection
from src.backup import ConfigCollector, ConfigExporter

with Connection(port="COM4", password="xxx") as conn:
    collector = ConfigCollector(conn)
    data = collector.collect_all()
    
    exporter = ConfigExporter()
    path = exporter.export_backup("SW-01", data)
    print(f"备份已保存: {path}")
```

### 模板化部署

```python
from src.console import Connection
from src.deploy import DeploymentEngine

engine = DeploymentEngine()

with Connection(port="COM4", password="xxx") as conn:
    report = engine.deploy(
        connection=conn,
        template="access_switch.j2",
        variables={
            "hostname": "SW-01",
            "admin_password": "YourStrongPass@2026",
            "vlan_list": "10 20 30",
        },
        device_name="SW-01",
        backup=True,
        # auto_rollback_on_failure=False  # 默认关闭
        # allow_dangerous=False           # 默认阻断 reboot/reset/delete/format/shutdown
    )
    print(report)
```

## CLI 使用

项目提供统一的命令行入口（**connect** 和 **backup** 仍可直接使用）：

```bash
# 测试连接
python main.py connect --port COM4 --password xxx

# 备份配置
python main.py backup --port COM4 --password xxx --device SW-01
```

**注意**：`deploy` 子命令已弃用，推荐通过 Python 使用 `AgentAdapter` 进行部署。

## 主要接口

### 1. Connection（核心连接类）

```python
from src.console import Connection

conn = Connection(port="COM4", password="xxx")
conn.connect()
output = conn.send_command("display current-configuration")
conn.disconnect()
```

### 2. AgentAdapter（Skill 统一调用入口）

推荐使用 `DeviceInfo` + 顶层字段的现代用法（已修复旧 `params` 字典不兼容问题）：

```python
from src.agent import AgentAdapter, AgentRequest, DeviceInfo

adapter = AgentAdapter()
request = AgentRequest(
    action="backup",
    device=DeviceInfo(port="COM4", password="xxx"),
    variables={"device_name": "SW-01"}
)
response = adapter.execute(request)
```

支持的 action：
- `backup`
- `deploy`
- `command`
- `validate`（已实现）

**改进说明**：
- 内部使用 `with Connection(...) as conn:` 上下文管理器，彻底解决资源泄漏问题。
- 错误处理已优化，支持更具体的异常捕获与日志记录。
- **AgentRequest 已迁移至 Pydantic 模型**，支持自动 JSON Schema 生成，更适合 LLM Tool Calling。
- `DeviceInfo` 新增可选字段 `connection_type: Literal["console", "ssh"]`，显式指定连接类型时优先于启发式检测（host/port 判断）。

### 3. 其他常用类

- `ConfigCollector` / `ConfigExporter`
- `CommandExecutor`
- `DeploymentEngine`
- `ConfigParser`（多子解析器）
- `TemplateRenderer`

## 幂等部署与 Dry-Run 支持（重要新特性）

从 2026-08 版本开始，`DeploymentEngine` 和 `AgentAdapter` 正式支持**幂等性部署**和 **Dry-Run 模式**，这是企业级网络自动化 Skill 的核心能力。

### 行为说明

| 场景                     | 返回 status     | `AgentResponse.success` | 说明 |
|--------------------------|-----------------|-------------------------|------|
| 配置有差异并下发成功     | `success`       | True                    | 正常下发 |
| 目标意图已满足（子集）   | `skipped`       | True                    | 目标行均已在当前配置中 |
| `dry_run=True`           | `dry_run`       | True                    | 仅模拟 |
| 检测到危险命令且未放行   | `blocked`       | False                   | 默认安全策略 |
| 触及上联/保护口（改 access） | `blocked`    | False                   | 需 `allow_uplink_change=True` |
| 部署失败                 | `failed`        | False                   | 默认不自动回滚 |
| 部署后校验失败           | `verify_failed` | False                   | `DEP003` |

幂等语义：**interface 感知意图子集**（目标接口块 ⊆ 同名接口当前配置；全局行在全局区匹配；**忽略 password/cipher 等密钥行**），不是整机配置全量相等，也不是无上下文扁平行集合。

危险命令：默认关键词 `reboot/reset/delete/format/shutdown`（`undo shutdown` 不视为危险）。需显式 `allow_dangerous=True`（或 variables 中同名，支持字符串 `"true"`/`"false"`）才放行。**deploy 与 command（Console/SSH）均默认阻断**。

SSH 真下发：默认 **禁用**。`connection_type="ssh"` 且 `action="deploy"` 时，除非 `dry_run=True` 或 `allow_ssh_deploy=True`（或 variables 同名），否则返回 `status=blocked` / `reason=ssh_deploy_disabled`（**不建立 SSH 连接**，错误码 `DEP006`）。生产改配请用 Console。

上联保护：自动识别当前配置中 description 含 `uplink` 或宽 trunk（`2 to 4094`）的接口；若目标写成 access/port-security，则 `blocked`（`DEP005`）。也可用 `uplink_ports` / `protected_ports` 显式保护。放行：`allow_uplink_change=True`。

SSH 主机密钥：默认 **拒绝未知密钥**（防 MITM）。信任已写入 `~/.ssh/known_hosts`（或 `HUAWEI_SSH_KNOWN_HOSTS`）。首次实验室环境可 `DeviceInfo(accept_unknown_host_key=True)` 或环境变量 `HUAWEI_SSH_ACCEPT_UNKNOWN=1`。

自动回滚：默认 **关闭**。开启 `auto_rollback_on_failure=True` 时为实验性「备份逐行重放」，不保证完整恢复。

部署成功后默认 **`save=True`** 落盘，并默认 **`verify=True`** 做浅层校验（sysname / vlan / ssh）；校验失败返回 `verify_failed`。

Planner：**不**全局去重，保证多接口模板子命令完整下发；`description ##...##` 不会被当成注释截断。

### 改密与 Dry-Run（运维注意）

- 幂等比较**忽略** password/cipher 行：仅改 `admin_password` 不会触发下发。轮换口令请用 `SSHFirstConnect` 或专用改密流程，不要依赖 deploy skip。
- 生产建议：`backup=True`，先 `dry_run=True`，确认 `diff_summary` 后再真实部署。


### 使用示例（推荐通过 AgentAdapter）

```python
from src.agent import AgentAdapter, AgentRequest, DeviceInfo

adapter = AgentAdapter()

# Dry-Run 模式（强烈推荐在生产环境使用）
request = AgentRequest(
    action="deploy",
    device=DeviceInfo(port="COM4", password="xxx", connection_type="console"),
    template="access_switch.j2",
    variables={"hostname": "SW-01", "vlan_list": "10 20 30", "admin_password": "YourStrongPass@2026"},
    backup=True,
    dry_run=True,
    allow_dangerous=False,
    auto_rollback_on_failure=False,
)
response = adapter.execute(request)

if not response.success:
    print("失败/阻断:", response.message, response.data)
elif response.data.get("status") == "skipped":
    print("配置意图已满足，无需部署")
elif response.data.get("status") == "dry_run":
    print("Dry-Run 完成，可安全执行真实部署")
```

### 设计优势

- **幂等性保护**：即使 Agent 重复调用同一部署请求，也不会造成重复配置或网络抖动。
- **安全验证**：通过 `dry_run=True` 可先观察将要执行的变更，再决定是否真正下发。
- **丰富反馈**：响应中包含 `reason`、`steps`、`changes_detected` 等字段，便于上层 Agent 决策。

---

## 配置说明

- 串口参数：默认 9600/8N1，可通过 `SerialConfig` 自定义
- 备份目录：`backups/<device>/<timestamp>/`
- 模板目录：`templates/`
- 日志：使用统一 logger，支持 DEBUG 级别查看详细交互

## 支持的设备

- Huawei VRP 系列（S5735、S5735R、S1730S 等）
- Console 波特率：9600（主流）
- 已验证固件：VRP V200R022C00SPC500

## 注意事项与限制

- **配置主路径是 Console**；SSH 用于后续批量管理（backup/command），不是开局改配置的首选
- Console 与 SSH 的 VRP **命令相同**，差异只在传输层
- **务必**传 `admin_password`（模板无默认口令；Jinja2 StrictUndefined）
- 部署具有破坏性：建议 `backup=True`，先 `dry_run=True`
- 密码勿硬编码；CLI `--password` 可能进 shell 历史
- 推荐显式 `DeviceInfo.connection_type`（`console` / `ssh`）
- 批量设备清单见 `configs/devices.example.yaml`，勿提交真实密码
- Console 波特率：`DeviceInfo.baudrate`（默认 9600）会传到串口

## 错误码矩阵

| 码 | 含义 | 典型触发 |
|----|------|----------|
| CON001 | 串口未找到 | 端口不存在 |
| CON002 | 串口打开失败 | 占用/权限 |
| CON003 | 登录失败 | 密码错误 / SSH 认证失败 |
| CON004 | 设备无响应 | 超时/断开 |
| CON005 | SSH 主机密钥不受信任 | 未知 host key 且未 `accept_unknown_host_key` |
| CMD001 | 命令执行失败 | 设备返回 Error |
| TPL001 | 模板不存在 | 文件名错误 |
| TPL002 | 模板渲染失败 | 缺变量（StrictUndefined） |
| DEP001 | 部署失败 | 下发中断/其他 deploy 失败 |
| DEP003 | 部署后校验失败 | `verify_failed` |
| DEP004 | 危险命令阻断 | reboot/reset/... 未 `allow_dangerous` |
| DEP005 | 上联/保护口阻断 | 误改 uplink 为 access |
| DEP006 | SSH 真下发禁用 | 未 `allow_ssh_deploy` 且非 dry_run |
| VAL001 | 校验失败 | validate action |
| APT001 | 无效请求 | 缺字段 |
| APT002 | 不支持的操作 | 非法 action |
| BKP001 / RBK001 | 备份/回滚失败 | 预留 |

`AgentResponse.code` 在失败时尽量填充上表码；`data.status` 仍是细粒度状态。

## 相关文档

- `docs/00-overview.md` — 项目整体概览与场景分工
- `docs/runbook-access-onboarding.md` — **接入交换机开局操作手册（推荐照做）**
- `docs/09-ssh.md` — SSH 首次改密
- `docs/10-batch.md` — SSH 批量管理（清单 / backup / command）
- `README.md` — 快速开始
- `docs/06-deploy.md` — 部署（Console 主路径）
- `tests/` — Mock 测试

## 许可证

MIT License

---

**Skill 定位声明**：  
本项目设计为可被上层 Agent / Claude Code 系统直接调用的 **Network Automation Skill**，提供华为交换机 Console 自动化运维的完整能力封装。