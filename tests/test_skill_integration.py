# -*- coding: utf-8 -*-
"""
Skill 集成测试

使用 Mock 测试 Skill 的核心功能和数据模型。
"""

import pytest
from unittest.mock import MagicMock, patch

from src.agent import AgentRequest, DeviceInfo


def test_agent_request_serialization():
    """测试 AgentRequest 的序列化与反序列化"""
    device = DeviceInfo(port="COM4", password="secret123")
    request = AgentRequest(
        action="deploy",
        device=device,
        template="access_switch.j2",
        variables={"hostname": "SW-01", "vlan_list": "10 20 30"}
    )

    # 序列化
    data = request.to_dict()
    assert data["action"] == "deploy"
    assert data["device"]["password"] == "***"  # 密码已掩码
    assert data["template"] == "access_switch.j2"
    assert "hostname" in data["variables"]

    # 反序列化
    restored = AgentRequest.from_dict({
        "action": "backup",
        "device": {"port": "COM5", "password": "pass123", "username": "admin"},
        "variables": {"device_name": "SW-02"}
    })
    assert restored.action == "backup"
    assert restored.device.port == "COM5"
    assert restored.variables["device_name"] == "SW-02"


def test_device_info_ssh_detection():
    """测试 DeviceInfo 的 SSH 判断功能"""
    console_device = DeviceInfo(port="COM4", password="xxx")
    assert console_device.is_ssh() is False

    ssh_device = DeviceInfo(port="10.0.0.1", password="xxx", host="10.0.0.1")
    assert ssh_device.is_ssh() is True


def test_agent_response_structure():
    """测试 AgentResponse 的基本结构"""
    from src.agent.request import AgentResponse

    resp = AgentResponse(
        success=True,
        message="操作成功",
        data={"backup_path": "/tmp/backup/"}
    )

    assert resp.success is True
    assert resp.is_success() is True
    d = resp.to_dict()
    assert d["success"] is True
    assert "backup_path" in d["data"]


def test_agent_request_validate_action():
    """测试 validate action 的请求构造（新支持的 action）"""
    device = DeviceInfo(port="COM4", password="secret")
    request = AgentRequest(
        action="validate",
        device=device,
        variables={
            "before_config": "interface Vlanif10",
            "after_config": "interface Vlanif10\nip address 192.168.10.1 24",
            "expected": {"vlan": "10"}
        }
    )
    assert request.action == "validate"
    assert "before_config" in request.variables