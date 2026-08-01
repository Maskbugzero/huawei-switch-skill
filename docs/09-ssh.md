# 09 - SSH 连接模块（规划中）

> **注意**：请使用项目 `.venv` 虚拟环境运行本模块（详见 `SKILL.md`）。

## 目标
支持通过 SSH 连接华为交换机，实现与 Console 一致的自动化能力。

## 已实现（初期）
- `SSHFirstConnect`：SSH 首次连接 + 强制修改密码流程
  - 自动接受主机指纹
  - 处理 “The password needs to be changed” 交互
  - 改密成功后重新验证登录
  - 改密后自动执行配置备份（使用 Netmiko 作为过渡）

## 文件
- `src/ssh/first_connect.py`：`SSHFirstConnect` + `SSHDevice`
- `src/ssh/__init__.py`

## 核心 API（当前版本）

```python
@dataclass
class SSHDevice:
    host: str
    username: str = "admin"
    old_password: str = ""
    new_password: str = ""
    port: int = 22

class SSHFirstConnect:
    def __init__(self, device: SSHDevice, timeout: int = 15):
        ...

    def change_password_and_verify(self) -> bool:
        """执行首次连接 + 改密 + 验证"""
        ...
```

## 典型用法示例

### SSH 首次改密
```python
from src.ssh import SSHFirstConnect, SSHDevice

device = SSHDevice(
    host="10.207.8.117",
    username="admins",
    old_password="phar@2021.SX",
    new_password="Phar@2021.sx"
)

ssh_tool = SSHFirstConnect(device)
success = ssh_tool.change_password_and_verify()
print("改密结果:", success)
```

## 后续计划
- 实现 `SSHTransport`，与 `SerialTransport` 统一接口
- 让 `Connection` 类支持 `transport="ssh"`
- 在 `AgentAdapter` 中支持 SSH 连接方式
- 完善错误码和重试机制

## 验收标准（阶段目标）
- 能够通过 SSH 完成首次连接 + 强制改密 + 验证
- 改密后可正常执行配置备份和命令
