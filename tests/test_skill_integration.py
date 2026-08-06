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
    """测试 DeviceInfo 的 SSH / Console 判断（显式优先 + 收紧启发式）。"""
    assert DeviceInfo(port="COM4", password="xxx").is_ssh() is False
    assert DeviceInfo(port="/dev/ttyUSB0", password="xxx").is_ssh() is False
    assert DeviceInfo(port="cu.usbserial", password="xxx").is_ssh() is False

    # host 显式设置 → SSH
    assert DeviceInfo(port="COM4", password="xxx", host="10.0.0.1").is_ssh() is True
    # IPv4 / hostname → SSH
    assert DeviceInfo(port="10.0.0.1", password="xxx").is_ssh() is True
    assert DeviceInfo(port="203.0.113.10", password="xxx").is_ssh() is True
    assert DeviceInfo(port="sw-core-01.example.com", password="xxx").is_ssh() is True
    # connection_type 覆盖启发式
    assert DeviceInfo(
        port="10.0.0.1", password="xxx", connection_type="console"
    ).is_ssh() is False
    assert DeviceInfo(
        port="COM4", password="xxx", connection_type="ssh"
    ).is_ssh() is True


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


def test_agent_request_allow_dangerous_field():
    """allow_dangerous / auto_rollback_on_failure 为一等字段。"""
    req = AgentRequest(
        action="deploy",
        device=DeviceInfo(port="COM4", password="x"),
        allow_dangerous=True,
        auto_rollback_on_failure=True,
        dry_run=True,
    )
    assert req.allow_dangerous is True
    assert req.auto_rollback_on_failure is True
    data = req.to_dict()
    assert data["allow_dangerous"] is True
    assert data["auto_rollback_on_failure"] is True


# ==================== Parser / Verify 针对性测试 ====================

def test_parser_interface_basic():
    """测试 InterfaceParser 基础解析能力"""
    from src.parser.interface_parser import InterfaceParser

    parser = InterfaceParser()
    config = """
interface GigabitEthernet0/0/1
 description Uplink
 ip address 192.168.1.1 255.255.255.0
 undo shutdown
interface Vlanif10
 ip address 10.0.0.1 255.255.255.0
 shutdown
"""
    result = parser.parse(config)
    assert len(result) >= 2
    ge = next((i for i in result if "GigabitEthernet" in i["name"]), None)
    assert ge is not None
    assert ge["ip_address"] == "192.168.1.1"
    assert ge["description"] is not None


def test_parser_interface_edge_cases():
    """测试 InterfaceParser 边界情况"""
    from src.parser.interface_parser import InterfaceParser
    parser = InterfaceParser()

    # 空输入
    assert parser.parse("") == []

    # 极大输入（触发截断保护，仍应能解析至少一个接口）
    large_config = "interface GigabitEthernet0/0/1\n ip address 1.1.1.1 255.255.255.0\n" + "x" * 600000
    result = parser.parse(large_config)
    assert len(result) >= 1
    assert result[0]["name"] == "GigabitEthernet0/0/1"

    # shutdown 状态判断
    config = "interface Vlanif20\nshutdown"
    result = parser.parse(config)
    assert result[0]["shutdown"] is True


def test_parser_vlan_basic():
    """测试 VlanParser 基础解析能力"""
    from src.parser.vlan_parser import VlanParser

    parser = VlanParser()
    config = "vlan batch 10 20 30\nvlan 100 name MGMT"
    result = parser.parse(config)
    assert any(v["type"] == "batch" for v in result)
    assert any(v.get("id") == 100 and v.get("name") == "MGMT" for v in result)


def test_verify_rules_basic():
    """测试 VerificationRules 实际校验逻辑"""
    from src.verify.rules import VerificationRules

    rules = VerificationRules()
    all_rules = rules.get_rules()

    # VLAN 检查
    vlan_result = all_rules["vlan_consistency"](
        before="", after="vlan 10\nvlan 20",
        expected={"vlan_list": [10, 20]}
    )
    assert vlan_result["status"] == "pass"

    # SSH 检查
    ssh_result = all_rules["ssh_status"](
        before="", after="ssh server enable",
        expected={}
    )
    assert ssh_result["status"] == "pass"


def test_verify_rules_edge_cases():
    """测试 Verify 规则边界情况"""
    from src.verify.rules import VerificationRules
    rules = VerificationRules()
    all_rules = rules.get_rules()

    # 未提供 expected 时跳过
    result = all_rules["vlan_consistency"]("", "", {})
    assert result["status"] == "skipped"

    # VLAN 缺失
    result = all_rules["vlan_consistency"]("", "vlan 10", {"vlan_list": [10, 99]})
    assert result["status"] == "fail"
    assert "99" in result["message"]
