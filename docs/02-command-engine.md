# 02 - 命令执行引擎

## 目标
实现稳定的命令下发能力。

## 已实现功能
- `send_command()` / `send_commands()`
- 错误识别（Error:、Failed:、Incomplete command、Unrecognized command）
- `save` 命令自动 [Y/N] 确认
- 命令执行日志

## 文件
- executor.py（主执行器）
- response_parser.py
- error_detector.py
- save_handler.py

## 核心 API

### CommandExecutor

```python
class CommandExecutor:
    def __init__(self, connection: Connection) -> None:
        ...

    def send_command(
        self,
        command: str,
        timeout: Optional[float] = None,
        save_confirm: bool = True
    ) -> str:
        ...

    def send_commands(
        self,
        commands: List[str],
        timeout: Optional[float] = None
    ) -> List[str]:
        ...
```

### 主要参数

| 参数         | 类型          | 默认值 | 说明                          |
|--------------|---------------|--------|-------------------------------|
| connection   | Connection    | -      | 已建立的 Console 连接         |
| command      | str           | -      | 要执行的命令                  |
| commands     | List[str]     | -      | 批量命令列表                  |
| timeout      | Optional[float] | None | 单个命令超时时间              |
| save_confirm | bool          | True   | save 命令是否自动确认 [Y]     |

## 典型用法示例

### 单条命令执行
```python
from src.console import Connection
from src.command import CommandExecutor

with Connection(port="COM4", password="xxx") as conn:
    executor = CommandExecutor(conn)
    result = executor.send_command("display vlan")
    print(result)
```

### 批量命令 + 自动 save
```python
commands = [
    "system-view",
    "vlan batch 10 20 30",
    "save"
]
results = executor.send_commands(commands)
```

## 错误处理
执行失败时会抛出 `CommandError` 或返回包含 "Error" / "Failed" 的输出，建议配合 `error_detector` 使用。

## 验收标准
能够自动执行 `system-view`、`vlan batch 10`、`save` 并成功保存配置。
