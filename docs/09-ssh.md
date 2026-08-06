# 09 - SSH 模块

> 使用项目 `.venv`（见 `SKILL.md`）。

## 定位

Console 与 SSH **只是连接方式不同，VRP 命令相同**。

本仓库中 SSH 承担两类职责：

| 能力 | 模块 | 何时用 |
|------|------|--------|
| 首次登录强制改密 | `SSHFirstConnect` | 设备刚上线、系统要求改密 |
| **批量管理** | `BatchSSHManager` | 多台已纳管设备 backup / command |

**改配置、模板部署的主路径仍是 Console。**  
单台 SSH backup/command 也可经 `AgentAdapter` + `connection_type="ssh"`。

批量管理详见 **[10-batch.md](./10-batch.md)**。

## 已实现

### 1. 首次改密 — `SSHFirstConnect`

- 自动接受主机指纹
- 处理 “password needs to be changed”
- 改密后验证登录
- 可选改密后备份（netmiko）

```python
from src.ssh import SSHFirstConnect, SSHDevice

device = SSHDevice(
    host="10.0.0.1",
    username="admin",
    old_password="old",
    new_password="new",
)
ok = SSHFirstConnect(device).change_password_and_verify()
```

### 2. 批量管理 — `BatchSSHManager`

见 `docs/10-batch.md` 与 `configs/devices.example.yaml`。

### 3. AgentAdapter 单台 SSH

```python
DeviceInfo(port="10.0.0.1", password="xxx", connection_type="ssh")
# action: backup | command |（deploy 非主推）
```

## 文件

- `src/ssh/first_connect.py`
- `src/ssh/batch.py` — 清单加载 + 批量 backup/command
- `src/ssh/inventory.py` — YAML 设备清单模型
- `configs/devices.example.yaml`

## 演进方向

1. 批量结果汇总报告、失败重试
2. 可选并发（线程池），注意设备管理面压力
3. 与 Console 共用统一 `send_command` 抽象后，批量配置可接同一 `DeploymentEngine`
4. 密钥/保险库对接，避免明文密码进清单

## 安全

- 示例清单勿含真实生产密码；用环境变量或本地未跟踪的 `configs/devices.yaml`
- 批量 command 同样可能有破坏性，默认应对只读命令（`display ...`）
