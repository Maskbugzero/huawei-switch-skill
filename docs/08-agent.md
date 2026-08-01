# 08 - Agent 统一适配层

> **注意**：请使用项目 `.venv` 虚拟环境运行本模块（详见 `SKILL.md`）。

## 目标
提供单一调用入口（AgentAdapter），编排 Console、Backup、Deploy、Command 等模块，实现完整自动化流程。

## 已实现
- `AgentAdapter.execute()` 统一入口
- 支持四种 action：`deploy`、`backup`、`command`、`validate`（validate 已完整实现）
- `AgentRequest` / `AgentResponse` 数据模型（使用 `DeviceInfo`）
- 统一错误码体系（CON*、APT* 等）
- **自动连接管理**：内部使用 `with Connection(...) as conn:` 上下文管理器，彻底解决资源泄漏
- **错误处理优化**：特定异常捕获 + 日志记录（connection / deployer 等模块已改进）

## 文件
- `adapter.py`：AgentAdapter 核心编排逻辑
- `request.py`：DeviceInfo、AgentRequest、AgentResponse
- `error_codes.py`：统一 ErrorCode 定义

## 核心 API

### AgentAdapter

```python
class AgentAdapter:
    SUPPORTED_ACTIONS = {"deploy", "backup", "command", "validate"}

    def execute(self, request: AgentRequest) -> AgentResponse:
        ...
```

### AgentRequest 参数

| 参数          | 类型                  | 默认值     | 说明                          |
|---------------|-----------------------|------------|-------------------------------|
| action        | str                   | -          | deploy / backup / command / validate |
| device        | DeviceInfo            | -          | 设备连接信息                  |
| template      | Optional[str]         | None       | 模板文件名（deploy 时使用）   |
| variables     | Dict[str, Any]        | {}         | 模板变量或命令参数            |
| backup        | bool                  | True       | deploy 前是否自动备份         |
| dry_run       | bool                  | False      | 是否仅模拟执行                |

### DeviceInfo

| 参数      | 类型 | 默认值 | 说明             |
|-----------|------|--------|------------------|
| port      | str  | -      | 串口号（如 COM4）|
| password  | str  | -      | Console 密码     |
| baudrate  | int  | 9600   | 波特率           |

### AgentResponse

```python
@dataclass
class AgentResponse:
    success: bool
    code: Optional[str] = None
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]: ...
```

## 典型用法示例

### 1. 一键备份
```python
from src.agent import AgentAdapter, AgentRequest, DeviceInfo

adapter = AgentAdapter()
request = AgentRequest(
    action="backup",
    device=DeviceInfo(port="COM4", password="your_password"),
    variables={"device_name": "SW-01"}
)
resp = adapter.execute(request)
print(resp.data.get("backup_path"))
```

**注意**：`AgentAdapter` 内部已使用上下文管理器，无需手动 `conn.connect()` / `disconnect()`。

### 2. 模板化部署
```python
request = AgentRequest(
    action="deploy",
    device=DeviceInfo(port="COM4", password="xxx"),
    template="base_switch.j2",
    variables={"hostname": "SW-01", "vlan_list": [10, 20, 30]},
    backup=True
)
resp = adapter.execute(request)
print(resp.success, resp.data)
```

### 3. 执行单条命令
```python
request = AgentRequest(
    action="command",
    device=DeviceInfo(port="COM4", password="xxx"),
    variables={"command": "display version"}
)
resp = adapter.execute(request)
print(resp.data.get("output"))
```

## 错误处理
- 使用统一错误码（`APT002` = 不支持的操作，`CON003` = 登录失败等）
- `resp.success == False` 时可通过 `resp.code` 和 `resp.error` 定位问题

## 验收标准
通过 `AgentAdapter.execute()` 能够成功完成 backup/deploy/command 操作，并返回标准 `AgentResponse`。
