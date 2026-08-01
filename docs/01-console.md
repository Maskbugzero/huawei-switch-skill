# 01 - Console 通信层

> **注意**：请使用项目 `.venv` 虚拟环境运行本模块（详见 `SKILL.md`）。

## 目标
建立稳定可靠的 Console 通信能力。

## 已实现功能
- 自动扫描 COM 端口
- 自动连接串口
- 提示符识别
- 自动关闭分页 (screen-length 0 temporary)
- 输出日志记录
- 收发数据缓存管理

## 文件
- serial_manager.py: 串口扫描、配置、Transport 抽象和 SerialTransport
- connection.py: Connection 类，处理登录、命令发送、断开
- prompt_detector.py: PromptDetector 提示符检测
- pager_handler.py: PagerHandler 分页处理

## 核心 API

### Connection

```python
class Connection:
    def __init__(
        self,
        port: Optional[str] = None,
        password: Optional[str] = None,
        transport: Optional[Transport] = None,
        config: Optional[SerialConfig] = None,
        timeout: float = 30.0,
    ) -> None:
        ...

    def connect(self) -> None:
        """建立连接并自动登录"""

    def send_command(self, command: str, timeout: Optional[float] = None) -> str:
        ...

    def disconnect(self) -> None:
        ...

    def __enter__(self):
        ...

    def __exit__(self, exc_type, exc_val, exc_tb):
        ...
```

### 主要参数说明

| 参数      | 类型                | 默认值 | 说明                     |
|-----------|---------------------|--------|--------------------------|
| port      | Optional[str]       | None   | 串口号（如 "COM4"）      |
| password  | Optional[str]       | None   | Console 登录密码         |
| timeout   | float               | 30.0   | 命令超时时间（秒）       |
| transport | Optional[Transport] | None   | 自定义传输层（测试用）   |

## 典型用法示例

### 上下文管理器方式（推荐）
```python
from src.console import Connection

with Connection(port="COM4", password="your_password") as conn:
    version = conn.send_command("display version")
    print(version)
```

### 手动控制方式
```python
conn = Connection(port="COM4", password="xxx", timeout=60)
conn.connect()
try:
    output = conn.send_command("display current-configuration")
finally:
    conn.disconnect()
```

## 验收
能够自动连接交换机并执行 `display version` 正确返回结果。
