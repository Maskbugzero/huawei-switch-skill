# 项目概览

`huawei-switch-skill` 是企业级华为 VRP 交换机自动化 Skill，供 Claude Code、Hermes 或其它 Agent 调用。

## 环境要求（重要）

必须使用项目 `.venv`：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

## 核心定位与场景分工

- **Skill 而非 Agent**：标准化能力封装
- **Console = 配置主路径**：单台开局、改配置、模板部署、校验
- **SSH = 批量管理通道**：已纳管多设备 backup / command / 后续巡检
- **命令相同、连接不同**：Console 与 SSH 都是 VRP CLI，差异只在 transport

| 场景 | 推荐入口 |
|------|----------|
| 串口配置 / deploy | `Connection` + `DeploymentEngine` 或 `AgentAdapter` + `connection_type="console"` |
| 接入开局操作手册 | **`docs/runbook-access-onboarding.md`** |
| 多机备份 / 批量命令 | `BatchSSHManager`（`src/ssh/batch.py`）+ `configs/devices.yaml` |
| 首次改密 | `SSHFirstConnect` |
| 单台 SSH 临时 backup/command | `AgentAdapter` + `connection_type="ssh"` |

## 主要能力

| 模块 | 目录 | 角色 |
|------|------|------|
| 串口通信 | `console/` | 配置主路径连接层 |
| 命令执行 | `command/` | 错误检测（主路径已接入 deploy） |
| 配置备份 | `backup/` | 采集与归档（Console/SSH/批量共用导出） |
| 解析 / 模板 / 部署 / 校验 | `parser/` `template/` `deploy/` `verify/` | 配置生命周期（deploy 推荐 Console） |
| SSH | `ssh/` | 首次改密 + **批量管理** |
| 统一入口 | `agent/` | `AgentAdapter` |

## 推荐调用

### Console 配置（主路径）

```python
from src.agent import AgentAdapter, AgentRequest, DeviceInfo

adapter = AgentAdapter()
response = adapter.execute(AgentRequest(
    action="deploy",
    device=DeviceInfo(port="COM4", password="xxx", connection_type="console"),
    template="access_switch.j2",
    variables={"hostname": "SW-01", "admin_password": "YourStrongPass@2026"},
    dry_run=True,
))
```

### SSH 批量备份（批量管理）

```python
from src.ssh.batch import BatchSSHManager

mgr = BatchSSHManager.from_yaml("configs/devices.yaml")
report = mgr.backup_all()
print(report.summary())
```

## 项目结构

```
huawei-switch-skill/
├── configs/          # 设备清单示例（勿提交真实密码）
├── src/
│   ├── console/      # 配置主路径
│   ├── command/
│   ├── backup/
│   ├── deploy/       # 推荐仅 Console 生产部署
│   ├── agent/
│   └── ssh/          # first_connect + batch
├── docs/             # 含 09-ssh.md、10-batch.md
├── examples/
└── tests/
```

## 相关文档

- `SKILL.md` — Skill 定义
- `docs/06-deploy.md` — 部署（Console）
- `docs/09-ssh.md` — 首次改密
- `docs/10-batch.md` — 批量管理
- `CHANGELOG.md`
