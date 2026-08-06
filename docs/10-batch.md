# 10 - SSH 批量管理

> 使用项目 `.venv`。配置主路径仍是 Console；本节描述 **已纳管设备的 SSH 批量运维**。

## 目标

用一份设备清单，对多台华为交换机执行相同的运维动作：

- 批量配置备份
- 批量执行命令（默认面向只读巡检）

VRP 命令与 Console 相同；此处仅通过 SSH transport 访问多台设备。

## 设备清单

复制示例并填入真实环境（**不要提交真实密码**）：

```powershell
copy configs\devices.example.yaml configs\devices.yaml
```

```yaml
# configs/devices.yaml
defaults:
  username: admin
  port: 22
  device_type: huawei_vrp

devices:
  - name: SW-ACCESS-01
    host: 10.0.0.11
    password: "set-me"
  - name: SW-ACCESS-02
    host: 10.0.0.12
    password: "set-me"
    username: admin   # 可覆盖 defaults
```

密码也可用环境变量占位（见 inventory 文档字符串）：`password_env: SW01_PASS`。

## API

```python
from src.ssh.batch import BatchSSHManager

mgr = BatchSSHManager.from_yaml("configs/devices.yaml")

# 1) 批量备份 → backups/<name>/<timestamp>/
report = mgr.backup_all()
print(report.summary())
for r in report.results:
    print(r.name, r.success, r.data)

# 2) 批量命令（只读示例；危险命令默认阻断）
report = mgr.command_all("display version")
print(report.summary())

# 危险命令需显式放行
# report = mgr.command_all("reboot", allow_dangerous=True)

# 3) 指定子集
report = mgr.backup_all(names=["SW-ACCESS-01"])
```

设备回 `Error:` 时该台 `success=False`。`reboot/reset/delete/format/shutdown` 默认全清单阻断。

### 结果模型

- `BatchReport`：`results: list[DeviceResult]`，`summary()` 统计成功/失败
- `DeviceResult`：`name`, `host`, `success`, `message`, `data`, `error`

## 与 Console / AgentAdapter 的关系

| 能力 | Console | SSH 单台 Adapter | SSH 批量 |
|------|---------|------------------|----------|
| 开局 deploy | ✅ 主路径 | 不推荐 | 未作为主路径 |
| backup | ✅ | ✅ | ✅ 清单驱动 |
| command | ✅ | ✅ | ✅ 清单驱动 + Error/危险策略 |
| 首次改密 | - | - | 用 `SSHFirstConnect` 逐台或后续扩展 |

## CLI（可选）

```powershell
.\.venv\Scripts\python.exe -m src.ssh.batch --inventory configs/devices.yaml backup
.\.venv\Scripts\python.exe -m src.ssh.batch --inventory configs/devices.yaml command --cmd "display device"
.\.venv\Scripts\python.exe -m src.ssh.batch -i configs/devices.yaml command --cmd "reboot" --allow-dangerous
```
```

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ssh_batch.py -v
```

无真机时全部 Mock。

## 后续

- 并发 worker 池 + 速率限制
- 批量 `display` 结果解析进 `parser`
- 统一 transport 后批量 dry-run 配置变更
