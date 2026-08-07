# -*- coding: utf-8 -*-
"""上联保护 / host key / 错误码 / baudrate 等中期能力测试。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.deploy.port_guard import (
    check_uplink_protection,
    detect_uplink_like_interfaces,
    find_protected_touches,
)
from src.deploy.deployer import DeploymentEngine
from src.agent import AgentAdapter, AgentRequest, DeviceInfo
from src.agent.error_codes import DEP004, DEP005, DEP006, code_for_deploy_status
from src.console.serial_manager import SerialConfig
from src.ssh.hostkeys import host_key_policy, netmiko_hostkey_kwargs
from paramiko import AutoAddPolicy, RejectPolicy


def test_detect_uplink_like_from_description_and_wide_trunk():
    cfg = """
interface GigabitEthernet0/0/24
 description uplink-switch
 port link-type trunk
 port trunk allow-pass vlan 2 to 4094
interface GigabitEthernet0/0/1
 port link-type access
"""
    found = detect_uplink_like_interfaces(cfg)
    assert "gigabitethernet0/0/24" in found
    assert "gigabitethernet0/0/1" not in found


def test_block_access_config_on_detected_uplink():
    current = """
interface GigabitEthernet0/0/24
 description uplink-switch
 port link-type trunk
 port trunk allow-pass vlan 2 to 4094
"""
    target = """
interface GigabitEthernet0/0/24
 description access
 port link-type access
 port default vlan 20
"""
    ok, reason, details = check_uplink_protection(
        target, variables={}, current_config=current, allow_uplink_change=False
    )
    assert ok is False
    assert "gigabitethernet0/0/24" in details["touched_protected"]
    assert "protected/uplink" in reason


def test_allow_trunk_uplink_template_when_already_uplink():
    """模板继续写 trunk 上联不应被 auto 保护误杀。"""
    current = """
interface Eth-Trunk1
 description uplink
 port link-type trunk
 port trunk allow-pass vlan 2 to 4094
"""
    target = """
interface Eth-Trunk1
 description ## Uplink to Aggregation ##
 port link-type trunk
 port trunk allow-pass vlan 10 20 30
 undo shutdown
"""
    ok, reason, details = check_uplink_protection(
        target, current_config=current, allow_uplink_change=False
    )
    assert ok is True
    assert details["touched_protected"] == []


def test_explicit_protected_ports_always_block():
    target = """
interface GigabitEthernet0/0/10
 description x
 undo shutdown
"""
    ok, reason, _ = check_uplink_protection(
        target,
        variables={"protected_ports": ["GigabitEthernet0/0/10"]},
        allow_uplink_change=False,
    )
    assert ok is False
    assert "gigabitethernet0/0/10" in reason


def test_allow_uplink_change_overrides():
    target = """
interface GigabitEthernet0/0/24
 port link-type access
"""
    current = """
interface GigabitEthernet0/0/24
 description uplink-switch
 port link-type trunk
 port trunk allow-pass vlan 2 to 4094
"""
    ok, _, details = check_uplink_protection(
        target, current_config=current, allow_uplink_change=True
    )
    assert ok is True
    assert details.get("skipped") is True


def test_deploy_engine_blocks_uplink_access_change():
    engine = DeploymentEngine()
    mock_conn = MagicMock()
    current = (
        "sysname SW\n"
        "interface GigabitEthernet0/0/24\n"
        " description uplink-switch\n"
        " port link-type trunk\n"
        " port trunk allow-pass vlan 2 to 4094\n"
    )
    with patch("src.deploy.deployer.ConfigCollector") as col_cls, \
         patch.object(engine, "renderer") as rend:
        col = MagicMock()
        col.collect_current_config.return_value = current
        col_cls.return_value = col
        rend.render.return_value = (
            "system-view\n"
            "interface GigabitEthernet0/0/24\n"
            " port link-type access\n"
            " port default vlan 20\n"
            "return\n"
        )
        report = engine.deploy(
            connection=mock_conn,
            template="x.j2",
            variables={"hostname": "SW"},
            backup=False,
            dry_run=True,
            save=False,
            verify=False,
        )
    assert report["status"] == "blocked"
    assert "uplink" in report.get("reason", "").lower() or "protected" in report.get("reason", "")


def test_error_code_matrix_helpers():
    assert code_for_deploy_status("verify_failed") == "DEP003"
    assert code_for_deploy_status("blocked", "dangerous commands") == DEP004.code
    assert code_for_deploy_status("blocked", "protected/uplink") == DEP005.code
    assert code_for_deploy_status("blocked", "ssh_deploy_disabled") == DEP006.code
    assert code_for_deploy_status("success") is None


def test_hostkey_policy_default_accept_unknown():
    """新机器场景：默认 AutoAdd；strict 时 Reject。"""
    assert isinstance(host_key_policy(True), AutoAddPolicy)
    assert isinstance(host_key_policy(False), RejectPolicy)
    kw = netmiko_hostkey_kwargs(accept_unknown=True)
    assert kw["ssh_strict"] is False
    assert kw["system_host_keys"] is True
    kw2 = netmiko_hostkey_kwargs(accept_unknown=False)
    assert kw2["ssh_strict"] is True
    # 无显式参数时默认接受
    kw3 = netmiko_hostkey_kwargs()
    assert kw3["ssh_strict"] is False


def test_adapter_passes_baudrate_to_serial_config():
    adapter = AgentAdapter()
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = False
    mock_conn.send_command.return_value = "ok"

    with patch("src.agent.adapter.Connection", return_value=mock_conn) as conn_cls, \
         patch("src.agent.adapter.CommandExecutor") as ex_cls:
        ex = MagicMock()
        ex.send_command.return_value = "ok"
        ex_cls.return_value = ex
        adapter.execute(
            AgentRequest(
                action="command",
                device=DeviceInfo(port="COM4", password="x", baudrate=115200),
                variables={"command": "display clock"},
            )
        )
    kwargs = conn_cls.call_args.kwargs
    assert "config" in kwargs
    assert isinstance(kwargs["config"], SerialConfig)
    assert kwargs["config"].baudrate == 115200


def test_ssh_deploy_disabled_uses_dep006():
    adapter = AgentAdapter()
    with patch("src.agent.adapter.ConnectHandler") as ch:
        r = adapter.execute(
            AgentRequest(
                action="deploy",
                device=DeviceInfo(port="10.0.0.1", password="x", connection_type="ssh"),
                template="access_switch.j2",
                variables={"hostname": "X", "admin_password": "Secret@2026"},
                dry_run=False,
            )
        )
    assert r.success is False
    assert r.code == DEP006.code
    ch.assert_not_called()
