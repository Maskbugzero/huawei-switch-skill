---
name: huawei-switch-skill
description: "Enterprise-grade Huawei VRP switch automation skill via Console. Provides full lifecycle management: serial connection, command execution, configuration backup, parsing, Jinja2 templating, deployment, and verification."
version: 1.0.0
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
  - configuration-backup-and-export
  - structured-config-parsing
  - jinja2-template-rendering
  - automated-deployment-with-rollback
  - configuration-verification-and-reporting
  - ssh-first-connect-with-password-change
entrypoints:
  python:
    - "from src.console import Connection"
    - "from src.backup import ConfigCollector, ConfigExporter"
    - "from src.deploy import DeploymentEngine"
    - "from src.agent import AgentAdapter"
  cli:
    - "python main.py connect --port COM4 --password xxx"
    - "python main.py backup --port COM4 --password xxx --device SW-01"
    - "python main.py deploy --script admin --port COM4 -p xxx --device-name SW-01"
dependencies:
  - pyserial>=3.5
  - jinja2>=3.1.0
  - pyyaml>=6.0
  - paramiko
  - netmiko (optional, for SSH backup)
related_skills: []
---

# Huawei Switch Skill

基于 Python 的华为交换机 Console 自动化 Skill，支持从连接、备份、解析、模板渲染、部署到校验的完整配置生命周期管理。

## 概述

`huawei-switch-skill` 是一个专注于华为 VRP 交换机的 **Console 优先** 自动化 Skill。它封装了串口通信、命令执行、配置全生命周期管理等核心能力，可被 Claude Code、Hermes 或其他 Agent 系统直接调用。

**设计原则**：
- Console 优先（最稳定可靠的接入方式）
- 模块化、可独立使用
- 支持 Mock 测试（无硬件环境可用）
- 提供统一的 `AgentAdapter` 作为 Skill 调用入口

## 核心能力

| 能力                  | 对应模块          | 说明                              |
|-----------------------|-------------------|-----------------------------------|
| 串口连接与认证        | `console`         | 自动登录、关闭分页、提示符识别    |
| 稳定命令执行          | `command`         | 错误检测、save 自动确认           |
| 配置备份与归档        | `backup`          | 按时间戳目录结构化存储            |
| 配置解析              | `parser`          | 转换为结构化 Python 对象          |
| 模板渲染              | `template`        | Jinja2 + YAML 变量                |
| 自动部署 + 回滚       | `deploy`          | 预检查、失败回滚                  |
| 配置一致性校验        | `verify`          | 生成 HTML/Markdown 报告           |
| SSH 首次改密          | `ssh`             | 首次连接强制修改密码              |

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
        template="base_switch.j2",
        variables={"hostname": "SW-01", "vlan_list": "10 20 30"},
        device_name="SW-01",
        backup=True
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

### 3. 其他常用类

- `ConfigCollector` / `ConfigExporter`
- `CommandExecutor`
- `DeploymentEngine`
- `ConfigParser`（多子解析器）
- `TemplateRenderer`

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

- 目前以 **Console（串口）** 为主，SSH 支持处于实验阶段（首次改密流程）
- 部署操作具有破坏性，建议始终开启 `backup=True`
- 密码通过参数传入，**绝不硬编码**。CLI 方式可能泄露到 shell 历史，推荐使用环境变量或 `AgentAdapter` + `getpass`。
- 部分高级特性（如多设备并发）尚未实现

## 相关文档

- `docs/00-overview.md` — 项目整体概览
- `README.md` — 项目概览与快速开始
- `agent.md` — 完整开发路线图（已完成 1-7 阶段）
- `docs/` — 各模块详细 API 文档（01-console.md ~ 09-ssh.md）
- `tests/` — Mock 测试用例

## 许可证

MIT License

---

**Skill 定位声明**：  
本项目设计为可被上层 Agent / Claude Code 系统直接调用的 **Network Automation Skill**，提供华为交换机 Console 自动化运维的完整能力封装。