# 06 - 自动部署模块

> **注意**：请使用项目 `.venv` 虚拟环境运行本模块（详见 `SKILL.md`）。

## 目标
自动下发配置。

## 已实现
- DeploymentEngine（备份 + 渲染 + 下发）
- RollbackManager
- DeploymentPlanner

## 文件
- deployer.py / rollback.py / planner.py

## 核心 API

### DeploymentEngine

```python
class DeploymentEngine:
    def __init__(self) -> None:
        ...

    def deploy(
        self,
        connection: Connection,
        template: str,
        variables: Dict[str, Any],
        backup: bool = True,
        device_name: str = "unknown",
    ) -> Dict[str, Any]:
        ...
```

### 主要参数

| 参数        | 类型             | 默认值     | 说明                        |
|-------------|------------------|------------|-----------------------------|
| connection  | Connection       | -          | 已登录的设备连接            |
| template    | str              | -          | 模板文件名                  |
| variables   | Dict[str, Any]   | -          | 模板变量                    |
| backup      | bool             | True       | 是否在部署前自动备份        |
| device_name | str              | "unknown"  | 设备名称（用于备份目录）    |

返回 report 包含：`status`、`steps`、`backup_path`、`error` 等。

## 典型用法示例

### 完整部署流程
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

## 验收
能够自动完成新交换机初始化部署（含可选备份）。

**相关文档**：
- `08-agent.md`：通过 `AgentAdapter` 统一调用部署
- `03-backup.md`：部署前自动备份集成
- `07-verify.md`：部署后配置校验
