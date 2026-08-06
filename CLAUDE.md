# CLAUDE.md

> **本文件为 Claude Code 专用工程参考文档**，重点记录与 Claude 交互相关的实践、注意事项和架构决策。
> 通用项目介绍请参考 `README.md`；Skill 规范定义请参考 `SKILL.md`。

## 项目概述

`huawei-switch-skill` 是供 Claude Code / Hermes 等调用的 **华为 VRP 网络自动化 Skill**。

**场景分工（写代码时务必遵守）**：

1. **Console = 配置主路径**  
   开局、改配置、模板 deploy、完整 `DeploymentEngine` / 幂等 / 危险命令策略。
2. **SSH = 批量管理通道**  
   已纳管设备的多机 backup、command、后续巡检；清单见 `configs/devices.example.yaml`，实现见 `src/ssh/batch.py`。
3. **命令语义一致**  
   Console/SSH 只是 transport，不要为 SSH 另写一套 VRP CLI 语义；批量能力应复用 `backup` / 错误检测等模块。
4. **SSHFirstConnect**  
   仅首次改密，独立于主配置流。

**不要**：把生产改配置默认走到 SSH deploy。  
**要做**：新配置特性优先落在 Console 路径；批量能力优先 SSH + 清单。

```
huawei-switch-skill/
├── CLAUDE.md
├── SKILL.md              # Skill 元数据定义（最重要参考）
├── README.md
├── docs/archive/agent.md # 开发路线图（历史文档，已归档）
├── examples/             # Skill 使用案例
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
│   ├── deploy/      # 自动部署（含幂等性）
│   ├── verify/      # 配置校验
│   └── agent/       # Skill 统一调用入口 (AgentAdapter)
├── templates/
├── tests/
└── docs/            # 各模块详细文档
```

`huawei-switch-skill` 是一个企业级的 **华为 VRP 交换机网络自动化 Skill**，专门设计为供 Claude Code、Hermes 等 LLM Agent 系统调用的底层执行器。

**核心定位**：提供华为交换机 Console（串口）自动化运维的完整能力封装，而非自主 Agent。

**已完成阶段**：agent.md（历史文档）路线图第 1~7 阶段全部完成。

## 项目结构

```
huawei-switch-skill/
├── CLAUDE.md
├── SKILL.md              # Skill 元数据定义（最重要参考）
├── README.md
├── docs/archive/agent.md # 开发路线图（历史文档，已归档）
├── examples/             # Skill 使用案例
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
│   ├── deploy/      # 自动部署（含幂等性）
│   ├── verify/      # 配置校验
│   └── agent/       # Skill 统一调用入口 (AgentAdapter)
├── templates/
├── tests/
└── docs/            # 各模块详细文档
```

## 开发环境要求（重要）

本项目**必须**使用项目自带的虚拟环境：

```powershell
# 推荐直接使用 venv 中的 Python
.\.venv\Scripts\python.exe -m pytest tests/ -v
.\.venv\Scripts\python.exe examples/03_using_agent_adapter.py
```

**创建虚拟环境（如不存在）**：
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

禁止直接使用系统全局 Python。

## 推荐调用方式

**强烈推荐通过 `AgentAdapter` 统一入口调用**：

```python
from src.agent import AgentAdapter, AgentRequest, DeviceInfo

adapter = AgentAdapter()
request = AgentRequest(
    action="deploy",                    # backup / deploy / command / validate
    device=DeviceInfo(port="COM4", password="xxx"),
    template="access_switch.j2",
    variables={"hostname": "SW-01"},
    backup=True,
    dry_run=False                       # 新增：支持 Dry-Run 模式
)
response = adapter.execute(request)
```

**注意**：`AgentRequest` 已迁移至 **Pydantic 模型**，支持自动 JSON Schema 生成，适合 LLM Tool Calling。

## 核心新特性（2026-08）

### 1. 幂等部署 + Dry-Run + 安全默认
- 部署前做**意图子集匹配**（目标行 ⊆ 当前配置 → `skipped`）
- `dry_run=True` 仅模拟
- 危险命令默认 `blocked`；`allow_dangerous=True` 才放行
- `auto_rollback_on_failure` **默认 False**（逐行重放备份为实验性）
- Adapter：`success` 仅在 status ∈ {success, skipped, dry_run} 时为 True
- 下发走 `CommandExecutor`（错误检测）
- SSH deploy 同样默认 blocked + Error 检测；连接在 `finally` 断开
- `AgentRequest.allow_dangerous` / `auto_rollback_on_failure` 为一等字段
- 异常映射到 `CON*` / `CMD*` / `TPL*` / `DEP*` / `APT*` 错误码

### 2. DeploymentPlanner（全面增强）
- 支持去重、分类、生成回滚计划
- 智能过滤无需回滚的命令（display、ping 等）
- 可通过 `DeploymentEngine.planner` 直接使用

### 3. Pydantic 模型
- `AgentRequest`、`DeviceInfo`、`AgentResponse`、`SSHDevice`、`SSHChangePasswordResult` 等均已迁移
- 字段带有 `description`，便于 LLM 理解

### 4. SSH 模块增强
- `SSHFirstConnect` 新增 `get_summary()`、`is_connected`、`get_connection_info()`
- 大量日志规范化

**注意**：部署操作具有破坏性，始终建议开启 `backup=True`

## 重要注意事项

- **部署操作具有破坏性**：始终建议开启 `backup=True`
- **密码安全**：
  - 绝不硬编码
  - 推荐使用环境变量或 `getpass` 传入
  - CLI 中的 `--password` 可能泄露到 shell history，生产环境优先使用 `AgentAdapter`
- **Console 优先**：当前以串口为主，SSH 支持仍处于实验阶段

## 常用命令

```powershell
# 运行测试
.\.venv\Scripts\python.exe -m pytest tests/ -v

# 运行特定测试
.\.venv\Scripts\python.exe -m pytest tests/test_deploy.py -v

# 运行示例
.\.venv\Scripts\python.exe examples/03_using_agent_adapter.py

# 安装依赖
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 代码风格与架构

- 广泛使用上下文管理器（`with Connection(...) as conn`）
- 模块化设计：console / command / backup / deploy / agent 等独立
- 统一使用 `src/console/logger.py` 的 logger
- 错误处理使用 `src/agent/error_codes.py` 中的错误码

## 测试策略

- 当前以 Mock 测试为主（支持无硬件环境开发）
- 新增功能必须添加对应测试
- 幂等性相关逻辑已有专用测试 `test_deploy_idempotent_skip_when_no_change`

**推荐测试命令**：

```powershell
# 运行所有测试
.\.venv\Scripts\python.exe -m pytest tests/ -v

# 只运行 Console 模块测试
.\.venv\Scripts\python.exe -m pytest tests/test_console.py -v

# 运行部署相关测试
.\.venv\Scripts\python.exe -m pytest tests/test_deploy.py -v
```

目前测试已覆盖：
- Prompt 检测
- 分页处理
- 错误检测
- 命令解析
- Connection 上下文管理
- 部署幂等性

## 参考文档

- `SKILL.md` — Skill 元数据与完整使用指南（最重要）
- `docs/archive/agent.md` — 开发路线图（历史文档）
- `README.md` — 项目概览
- `docs/` — 各模块详细文档

---

**维护原则**：本文件应与 `SKILL.md` 保持同步，重点记录对 Claude Code 交互有帮助的工程实践和注意事项。

## 后续计划（参考）

- 继续丰富 `examples/` 目录中的 Skill 使用案例
- 完善 `AgentAdapter` 的更多 action 支持
- 支持 SSH Transport（已实现首次连接 + 强制改密）
- 丰富模板库
- 第八阶段：图形界面（可选）
