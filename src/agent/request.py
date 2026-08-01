# -*- coding: utf-8 -*-
"""
Skill 请求与响应模型（AgentRequest / AgentResponse）

本模块定义了 huawei-switch-skill Skill 的标准数据契约。
所有通过 AgentAdapter 进行的调用都应使用这些模型。

推荐用法：
    from src.agent import AgentRequest, AgentResponse, DeviceInfo
    from src.agent.adapter import AgentAdapter
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional


ActionType = Literal["backup", "deploy", "command", "validate"]


@dataclass
class DeviceInfo:
    """
    设备连接信息。

    支持 Console（串口）和 SSH 两种接入方式。
    """
    port: str                          # Console 端口（如 COM4）或 SSH 主机
    password: str
    username: str = "admin"            # SSH 用户名
    baudrate: int = 9600               # Console 波特率
    host: Optional[str] = None         # SSH 主机地址（当 port 为 IP 时使用）
    port_number: int = 22              # SSH 端口

    def is_ssh(self) -> bool:
        """判断是否为 SSH 连接"""
        return self.host is not None or ":" in self.port or self.port.startswith(("10.", "172.", "192.168."))


@dataclass
class AgentRequest:
    """
    Skill 标准请求对象。

    所有 Skill 操作都通过此对象进行标准化调用。

    Attributes:
        action: 操作类型（backup/deploy/command/validate）
        device: 设备连接信息
        template: 部署时使用的 Jinja2 模板名
        variables: 模板变量或命令参数
        config_path: 配置文件路径（validate 时使用）
        backup: 部署前是否自动备份（默认 True）
        dry_run: 是否只模拟执行不实际下发
    """
    action: ActionType
    device: DeviceInfo
    template: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    config_path: Optional[str] = None
    backup: bool = True
    dry_run: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（便于 JSON 传输）"""
        return {
            "action": self.action,
            "device": {
                "port": self.device.port,
                "username": self.device.username,
                "password": "***",  # 安全考虑，不序列化真实密码
                "baudrate": self.device.baudrate,
            },
            "template": self.template,
            "variables": self.variables,
            "backup": self.backup,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentRequest":
        """从字典创建请求对象"""
        device_data = data.get("device", {})
        device = DeviceInfo(
            port=device_data.get("port", ""),
            password=device_data.get("password", ""),
            username=device_data.get("username", "admin"),
            baudrate=device_data.get("baudrate", 9600),
        )
        return cls(
            action=data["action"],
            device=device,
            template=data.get("template"),
            variables=data.get("variables", {}),
            backup=data.get("backup", True),
            dry_run=data.get("dry_run", False),
        )


@dataclass
class AgentResponse:
    """
    Skill 统一响应对象。

    所有 Skill 操作返回此标准化响应，便于上层系统处理。
    """
    success: bool
    code: Optional[str] = None
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "success": self.success,
            "code": self.code,
            "message": self.message,
            "data": self.data,
            "error": self.error,
        }

    def is_success(self) -> bool:
        return self.success
