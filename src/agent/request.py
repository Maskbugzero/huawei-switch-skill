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

import re
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, SecretStr


ActionType = Literal["backup", "deploy", "command", "validate"]

_IPV4_RE = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$"
)
_CONSOLE_PORT_RE = re.compile(
    r"^(COM\d+|/dev/[\w./-]+|tty[\w./-]*|cu\.[\w.-]+)$",
    re.IGNORECASE,
)


class DeviceInfo(BaseModel):
    """
    设备连接信息。

    支持 Console（串口）和 SSH 两种接入方式。

    connection_type 字段说明：
    - 可选显式指定连接类型（"console" 或 "ssh"）。
    - 若设置，则优先于启发式检测。
    - 推荐在明确知道连接类型时使用，避免启发式误判。
    """
    model_config = ConfigDict(extra="ignore")

    port: str = Field(..., description="Console port (e.g. COM4) or SSH hostname/IP")
    password: SecretStr = Field(..., description="Login password for the device")
    username: str = Field(default="admin", description="SSH username (default: admin)")
    baudrate: int = Field(default=9600, description="Console baud rate (default: 9600)")
    host: Optional[str] = Field(default=None, description="Explicit SSH host (alternative to detecting from port)")
    port_number: int = Field(default=22, description="SSH port (default: 22)")
    connection_type: Optional[Literal["console", "ssh"]] = Field(
        default=None,
        description="Explicit connection type override. If set, takes precedence over heuristic detection."
    )

    def is_ssh(self) -> bool:
        """判断是否为 SSH 连接。"""
        if self.connection_type is not None:
            return self.connection_type == "ssh"
        if self.host is not None:
            return True

        port = (self.port or "").strip()
        if not port:
            return False

        # 明确的 Console 串口形态
        if _CONSOLE_PORT_RE.match(port):
            return False

        # IPv4
        if _IPV4_RE.match(port):
            return True

        # IPv6 粗判 / host:port
        if ":" in port:
            return True

        # 主机名（含字母，且不是 COMx）
        if any(c.isalpha() for c in port):
            return True

        # 无法判断时保持 Console（向后兼容纯数字等特殊 port 名）
        return False



class AgentRequest(BaseModel):
    """
    Skill 标准请求对象。

    所有 Skill 操作都通过此对象进行标准化调用。
    """
    model_config = ConfigDict(extra="ignore")

    action: ActionType = Field(..., description="Operation type: backup / deploy / command / validate")
    device: DeviceInfo = Field(..., description="Device connection information")
    template: Optional[str] = Field(default=None, description="Jinja2 template name for deploy action")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Template variables or command parameters")
    config_path: Optional[str] = Field(default=None, description="Path to config file (used by validate)")
    backup: bool = Field(default=True, description="Whether to backup before deploy (default: True)")
    dry_run: bool = Field(default=False, description="If True, simulate without making changes")
    allow_dangerous: bool = Field(
        default=False,
        description="If True, allow deploy of commands matching dangerous keywords (reboot/reset/delete/format/shutdown)",
    )
    auto_rollback_on_failure: bool = Field(
        default=False,
        description="If True, attempt experimental line-replay rollback after deploy failure (default: False)",
    )
    save: bool = Field(
        default=True,
        description="If True (default), run VRP save after successful deploy",
    )
    verify: bool = Field(
        default=True,
        description="If True (default), run shallow post-deploy verification (sysname/vlan/ssh)",
    )

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（便于 JSON 传输）"""
        data = self.model_dump()
        # 安全考虑：不序列化真实密码
        if "device" in data and isinstance(data["device"], dict):
            data["device"]["password"] = "***"
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentRequest":
        """从字典创建请求对象"""
        return cls.model_validate(data)



class AgentResponse(BaseModel):
    """
    Skill 统一响应对象。

    所有 Skill 操作返回此标准化响应，便于上层系统处理。
    """
    model_config = ConfigDict(extra="ignore")

    success: bool = Field(..., description="Whether the operation succeeded")
    code: Optional[str] = Field(default=None, description="Error code if failed")
    message: str = Field(default="", description="Human-readable message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Structured result data")
    error: Optional[str] = Field(default=None, description="Detailed error information")

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return self.model_dump()

    def is_success(self) -> bool:
        return self.success

