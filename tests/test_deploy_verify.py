# -*- coding: utf-8 -*-
"""部署后浅层 verify 闭环测试。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.deploy.deployer import DeploymentEngine
from src.verify.rules import VerificationRules


def test_verify_rules_sysname_and_vlan_batch():
    rules = VerificationRules()
    after = (
        "sysname SW-01\n"
        "ssh server enable\n"
        "vlan batch 10 20 30\n"
    )
    expected = {"hostname": "SW-01", "vlan_list": [10, 20, 30], "require_ssh": True}

    assert rules._check_sysname("", after, expected)["status"] == "pass"
    assert rules._check_vlan("", after, expected)["status"] == "pass"
    assert rules._check_ssh("", after, expected)["status"] == "pass"

    bad = rules._check_sysname("", "sysname OTHER\n", expected)
    assert bad["status"] == "fail"

    # vlan 1 不得因 vlan 10 误匹配
    assert (
        rules._check_vlan("", "vlan batch 10 20\n", {"vlan_list": [1]})["status"]
        == "fail"
    )


def test_deploy_runs_verify_after_success():
    engine = DeploymentEngine()
    mock_conn = MagicMock()

    after_cfg = (
        "sysname SW-01\n"
        "ssh server enable\n"
        "vlan batch 10 20 30\n"
        "interface Vlanif10\n"
        " ip address 1.1.1.1 24\n"
    )

    with patch.object(engine, "renderer") as mock_renderer, \
         patch("src.deploy.deployer.ConfigCollector") as mock_col_cls, \
         patch("src.deploy.deployer.CommandExecutor") as mock_exec_cls:
        mock_renderer.render.return_value = (
            "sysname SW-01\nssh server enable\nvlan batch 10 20 30\n"
        )
        mock_col = MagicMock()
        mock_col.collect_current_config.side_effect = [
            "sysname OLD\n",  # before
            after_cfg,  # after deploy verify
        ]
        mock_col_cls.return_value = mock_col
        mock_exec = MagicMock()
        mock_exec.send_command.return_value = "OK"
        mock_exec_cls.return_value = mock_exec

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables={
                "hostname": "SW-01",
                "admin_password": "Secret@2026",
                "vlan_list": "10 20 30",
            },
            backup=False,
            save=False,
            verify=True,
        )

    assert report["status"] == "success"
    assert "verify" in report["steps"]
    assert report.get("verification", {}).get("status") == "pass"


def test_deploy_verify_failed_marks_status():
    engine = DeploymentEngine()
    mock_conn = MagicMock()

    with patch.object(engine, "renderer") as mock_renderer, \
         patch("src.deploy.deployer.ConfigCollector") as mock_col_cls, \
         patch("src.deploy.deployer.CommandExecutor") as mock_exec_cls:
        mock_renderer.render.return_value = "sysname SW-01\nssh server enable\n"
        mock_col = MagicMock()
        mock_col.collect_current_config.side_effect = [
            "sysname OLD\n",
            "sysname WRONG\n",  # verify should fail hostname
        ]
        mock_col_cls.return_value = mock_col
        mock_exec = MagicMock()
        mock_exec.send_command.return_value = "OK"
        mock_exec_cls.return_value = mock_exec

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables={"hostname": "SW-01", "admin_password": "Secret@2026"},
            backup=False,
            save=False,
            verify=True,
        )

    assert report["status"] == "verify_failed"
    assert report.get("verification", {}).get("status") == "fail"


def test_deploy_verify_can_be_disabled():
    engine = DeploymentEngine()
    mock_conn = MagicMock()

    with patch.object(engine, "renderer") as mock_renderer, \
         patch("src.deploy.deployer.ConfigCollector") as mock_col_cls, \
         patch("src.deploy.deployer.CommandExecutor") as mock_exec_cls:
        mock_renderer.render.return_value = "sysname SW-01\n"
        mock_col = MagicMock()
        mock_col.collect_current_config.return_value = "sysname OLD\n"
        mock_col_cls.return_value = mock_col
        mock_exec = MagicMock()
        mock_exec.send_command.return_value = "OK"
        mock_exec_cls.return_value = mock_exec

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables={"hostname": "SW-01", "admin_password": "Secret@2026"},
            backup=False,
            save=False,
            verify=False,
        )

    assert report["status"] == "success"
    assert "verify" not in report["steps"]
    assert mock_col.collect_current_config.call_count == 1
