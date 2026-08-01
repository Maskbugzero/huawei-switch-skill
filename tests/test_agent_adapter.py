# -*- coding: utf-8 -*-
"""
AgentAdapter 边界测试
"""

from unittest.mock import MagicMock, patch

from src.agent import AgentAdapter, AgentRequest, DeviceInfo


def test_agent_adapter_unsupported_action():
    """测试不支持的操作类型"""
    adapter = AgentAdapter()
    request = AgentRequest(
        action="unknown_action",  # 不支持
        device=DeviceInfo(port="COM4", password="xxx"),
    )
    response = adapter.execute(request)

    assert response.success is False
    assert "不支持的操作" in response.message


def test_agent_adapter_missing_device_info():
    """测试缺少设备连接信息"""
    adapter = AgentAdapter()
    request = AgentRequest(
        action="backup",
        device=None,  # 缺少设备信息
    )
    response = adapter.execute(request)

    assert response.success is False
    assert "缺少必要的设备连接信息" in response.message


def test_agent_adapter_validate_with_direct_content():
    """测试 validate 使用直接传入配置内容"""
    adapter = AgentAdapter()
    request = AgentRequest(
        action="validate",
        device=DeviceInfo(port="COM4", password="dummy"),
        variables={
            "before_config": "interface Vlanif10",
            "after_config": "interface Vlanif10\nip address 192.168.10.1 24",
            "expected": {"vlan": "10"}
        }
    )
    response = adapter.execute(request)

    assert response.success is True
    assert "validation_report" in response.data


def test_agent_adapter_command_action():
    """测试 command action"""
    adapter = AgentAdapter()
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "output"

    with patch("src.agent.adapter.Connection", return_value=mock_conn):
        request = AgentRequest(
            action="command",
            device=DeviceInfo(port="COM4", password="xxx"),
            variables={"command": "display version"}
        )
        response = adapter.execute(request)

        assert response.success is True
        assert "output" in response.data
