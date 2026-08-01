# 03 - 配置采集模块 (Backup)

> **注意**：请使用项目 `.venv` 虚拟环境运行本模块（详见 `SKILL.md`）。

## 目标
自动获取设备配置并归档。

## 已实现功能
- 标准命令采集：display current-configuration / version / vlan / interface brief / stp brief / device
- 自动备份到 backups/设备名/YYYYMMDD-HHMMSS/ 目录
- 生成：配置文件、设备信息、metadata.json
- 设备清单管理 (inventory.json)

## 文件
- collector.py: ConfigCollector（采集逻辑）
- exporter.py: ConfigExporter（文件导出 + 时间戳目录）
- inventory.py: DeviceInventory（设备元数据管理）

## 核心 API

### ConfigCollector

```python
class ConfigCollector:
    COLLECT_COMMANDS = [
        "display current-configuration",
        "display version",
        ...
    ]

    def __init__(self, connection: Connection) -> None:
        ...

    def collect_all(self) -> Dict[str, str]:
        """采集所有标准命令"""

    def collect_current_config(self) -> str:
        ...
```

### ConfigExporter

```python
class ConfigExporter:
    def export_backup(
        self,
        device_name: str,
        data: Dict[str, str]
    ) -> Path:
        ...
```

### 主要参数

| 参数        | 类型             | 默认值 | 说明                     |
|-------------|------------------|--------|--------------------------|
| connection  | Connection       | -      | Console 连接             |
| device_name | str              | -      | 设备名称（用于目录）     |
| data        | Dict[str, str]   | -      | 采集到的命令输出结果     |

## 典型用法示例

### 完整备份流程
```python
from src.console import Connection
from src.backup import ConfigCollector, ConfigExporter

with Connection(port="COM4", password="xxx") as conn:
    collector = ConfigCollector(conn)
    data = collector.collect_all()          # 采集所有标准命令

    exporter = ConfigExporter()
    backup_path = exporter.export_backup("SW-01", data)
    print(f"备份已保存到: {backup_path}")
```

### 只采集当前配置
```python
current_config = collector.collect_current_config()
```

## 验收标准
一键生成完整设备备份目录（含 metadata.json）。

**相关文档**：
- `08-agent.md`：通过 `AgentAdapter` 统一调用备份功能
- `06-deploy.md`：部署前自动备份的集成用法
