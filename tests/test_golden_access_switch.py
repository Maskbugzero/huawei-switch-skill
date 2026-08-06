# -*- coding: utf-8 -*-
"""
金样例：官方 access_switch 模板 × planner × 幂等 × 录制 running-config 片段。

不连真机；用 fixtures 锁定「多口模板不会被拆坏」与「意图匹配」回归。
"""

from __future__ import annotations

from pathlib import Path

from src.deploy.deployer import DeploymentEngine, configs_intent_differs
from src.deploy.planner import DeploymentPlanner
from src.template import TemplateRenderer

FIXTURES = Path(__file__).resolve().parent / "fixtures"

_ACCESS_VARS = {
    "hostname": "SW-ACCESS-01",
    "admin_password": "Secret@2026-Golden",
    "vlan_list": "10 20 30 100",
    "mgmt_ip": "192.168.100.10",
    "mgmt_mask": "255.255.255.0",
    "uplink": "Eth-Trunk1",
    "uplink_vlans": "10 20 30 100",
    "access_vlan": "20",
    "floor": "1",
    "room": "01",
    "max_mac": "2",
    "monitor_port": "GigabitEthernet0/0/25",
}


def test_golden_access_switch_plan_keeps_all_access_ports():
    """24 口模板：每口 access/vlan/undo shutdown 不得被 planner 丢掉。"""
    rendered = TemplateRenderer().render("access_switch.j2", _ACCESS_VARS)
    steps = DeploymentPlanner().plan(rendered)

    assert steps.count("port link-type access") == 24
    assert steps.count("port default vlan 20") == 24
    assert steps.count("undo shutdown") >= 26  # 24 access + Vlanif + Eth-Trunk
    assert steps.count("port-security enable") == 24

    for i in range(1, 25):
        if_name = f"interface GigabitEthernet0/0/{i}"
        assert if_name in steps
        idx = steps.index(if_name)
        # 下一 interface 或文件结束前应含关键子命令
        next_if = None
        for j in range(idx + 1, len(steps)):
            if steps[j].startswith("interface "):
                next_if = j
                break
        block = steps[idx : next_if if next_if is not None else len(steps)]
        assert "port link-type access" in block
        assert "port default vlan 20" in block
        assert "undo shutdown" in block

    assert "ssh server enable" in steps
    assert "sysname SW-ACCESS-01" in steps
    assert any(s.startswith("vlan batch") for s in steps)


def test_golden_access_switch_intent_skips_when_fixture_satisfies_core():
    """
    部分 running-config fixture 已含 sysname/ssh/vlan/关键口时：
    完整 24 口模板仍会 diff（缺 GE3-24），不得误 skip。
    """
    rendered = TemplateRenderer().render("access_switch.j2", _ACCESS_VARS)
    current = (FIXTURES / "running_config_access_partial.txt").read_text(encoding="utf-8")
    is_diff, summary = configs_intent_differs(rendered, current)
    assert is_diff is True
    assert "gigabitethernet0/0/3" in summary.lower() or "缺少" in summary


def test_golden_intent_skip_when_same_two_port_intent_present():
    """仅两口意图且 fixture 已满足（含密文密码）→ 应 skip。"""
    two_port = (
        "system-view\n"
        "sysname SW-ACCESS-01\n"
        "ssh server enable\n"
        "aaa\n"
        " local-user admin password irreversible-cipher Secret@2026-Golden\n"
        " local-user admin privilege level 15\n"
        " quit\n"
        "vlan batch 10 20 30 100\n"
        "interface Vlanif100\n"
        " ip address 192.168.100.10 255.255.255.0\n"
        " undo shutdown\n"
        "interface Eth-Trunk1\n"
        " port link-type trunk\n"
        " port trunk allow-pass vlan 10 20 30 100\n"
        " undo shutdown\n"
        "interface GigabitEthernet0/0/1\n"
        " port link-type access\n"
        " port default vlan 20\n"
        " undo shutdown\n"
        "interface GigabitEthernet0/0/2\n"
        " port link-type access\n"
        " port default vlan 20\n"
        " undo shutdown\n"
        "return\n"
    )
    current = (FIXTURES / "running_config_access_partial.txt").read_text(encoding="utf-8")
    is_diff, summary = configs_intent_differs(two_port, current)
    assert is_diff is False
    assert "意图" in summary or "满足" in summary


def test_golden_deploy_engine_skip_with_fixture(monkeypatch):
    """DeploymentEngine 对已满足意图返回 skipped（Mock 采集 fixture）。"""
    from unittest.mock import MagicMock, patch

    engine = DeploymentEngine()
    mock_conn = MagicMock()
    current = (FIXTURES / "running_config_access_partial.txt").read_text(encoding="utf-8")
    two_port_render = (
        "sysname SW-ACCESS-01\n"
        "ssh server enable\n"
        "vlan batch 10 20 30 100\n"
        "interface GigabitEthernet0/0/1\n"
        " port link-type access\n"
        " port default vlan 20\n"
        " undo shutdown\n"
    )

    with patch.object(engine, "renderer") as mock_renderer, \
         patch("src.deploy.deployer.ConfigCollector") as mock_col_cls:
        mock_renderer.render.return_value = two_port_render
        mock_col = MagicMock()
        mock_col.collect_current_config.return_value = current
        mock_col_cls.return_value = mock_col

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables=_ACCESS_VARS,
            backup=False,
            save=False,
            verify=False,
        )

    assert report["status"] == "skipped"
