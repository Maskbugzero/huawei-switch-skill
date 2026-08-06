# 06 - 自动部署模块

> **注意**：请使用项目 `.venv` 虚拟环境运行本模块（详见 `SKILL.md`）。

## 目标
自动下发配置（带安全默认）。

## 已实现
- DeploymentEngine（备份 + 渲染 + **interface 感知**幂等 + 危险命令阻断 + CommandExecutor 下发 + 默认 save）
- RollbackManager（实验性，默认不自动触发）
- DeploymentPlanner（**禁止全局去重**，仅折叠连续相同行）

## 文件
- deployer.py / rollback.py / planner.py

## 核心 API

### DeploymentEngine.deploy 主要参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| connection | - | 已登录的设备连接 |
| template | - | 模板文件名（如 `access_switch.j2`） |
| variables | - | 须含 `admin_password` 等（StrictUndefined） |
| backup | True | 部署前备份（无有效配置时跳过，不写空备份） |
| device_name | `"unknown"` | 备份目录名（仅 `[\w.-]+`，防路径穿越） |
| dry_run | False | 仅模拟 |
| save | **True** | 成功后执行 VRP `save` |
| auto_rollback_on_failure | **False** | 失败自动回滚（实验性） |
| allow_dangerous | **False** | 放行危险命令 |
| dangerous_keywords | reboot/reset/delete/format/shutdown | 可自定义 |

SSH deploy（`AgentAdapter`）与 Console 对齐：**blocked / interface 感知幂等 / Error 检测 / planner 保序 / finally disconnect**。完整回滚建议仍走 Console。

### status 语义

| status | AgentResponse.success | 含义 |
|--------|----------------------|------|
| success | True | 已下发（默认已 save） |
| skipped | True | 目标意图已在对应 interface 上下文满足 |
| dry_run | True | 仅计划 |
| blocked | False | 危险命令未放行 |
| failed | False | 执行失败（含 save 失败） |

### 幂等语义（interface 感知）

- 按 `interface` 块比较：目标接口下的每一行须出现在**同名接口**当前配置中
- 全局行（如 `sysname`、`vlan batch`）在全局区匹配
- **忽略密钥行**（`password` / `irreversible-cipher` / `cipher <secret>` 等），避免设备密文导致永不 skip
- **不再**使用无上下文的扁平行集合

### Planner 语义

- 多接口模板中重复子命令（`port link-type access` 等）**全部保留**
- 仅折叠连续完全相同的行

## 典型用法

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
        dry_run=True,  # 先演练
        # save=True 为默认；dry_run 不会 save
    )
    print(report)
```

**相关文档**：`08-agent.md`、`03-backup.md`、`07-verify.md`、`SKILL.md`
