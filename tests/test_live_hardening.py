# -*- coding: utf-8 -*-
"""0.3.x 真机加固相关回归测试。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.console.prompt_detector import PromptDetector
from src.deploy.planner import DeploymentPlanner, _strip_config_line
from src.deploy.deployer import _normalize_config
from src.ssh.batch import BatchSSHManager
from src.ssh.inventory import DeviceInventory, InventoryDevice


def test_planner_preserves_description_double_hash():
    text = "\n".join(
        [
            "system-view",
            "interface GigabitEthernet0/0/1",
            " description ## Uplink to Core ##",
            " undo shutdown",
            "return",
        ]
    )
    steps = DeploymentPlanner().plan(text)
    assert any(s.startswith("description ##") and s.endswith("##") for s in steps)
    assert "description" not in steps  # bare description must not appear


def test_strip_config_line_keeps_description_hash():
    line = " description ## keep me ## "
    assert _strip_config_line(line) == "description ## keep me ##"


def test_strip_config_line_still_strips_real_trailing_comment():
    assert _strip_config_line("vlan batch 10 20 # office") == "vlan batch 10 20"


def test_normalize_config_keeps_description_hash():
    lines = _normalize_config("description ## A ##\nvlan batch 1 # cmt\n")
    assert "description ## A ##" in lines
    assert "vlan batch 1" in lines


def test_prompt_detect_interface_view():
    det = PromptDetector()
    text = "Enter system view\n[1730-24-GigabitEthernet0/0/24]"
    assert det.detect(text) == "[1730-24-GigabitEthernet0/0/24]"
    assert det.is_prompt(text) is True


def test_prompt_is_prompt_user_and_system_view():
    det = PromptDetector()
    assert det.is_prompt("<1730-24>") is True
    assert det.is_prompt("[1730-24]") is True
    assert det.is_prompt("Password:") is False
    assert det.detect("Password:") == "Password:"


def test_batch_connecthandler_no_read_timeout_kwarg():
    """netmiko 4.x ConnectHandler 不得传入 read_timeout。"""
    inv = DeviceInventory(
        devices=[InventoryDevice(name="SW1", host="10.0.0.1", password="x")]
    )
    mgr = BatchSSHManager(inv)
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = ""

    with patch("src.ssh.batch.ConnectHandler", return_value=mock_conn) as ch:
        conn = mgr._connect(inv.devices[0])

    assert conn is mock_conn
    kwargs = ch.call_args.kwargs
    assert "read_timeout" not in kwargs
    assert kwargs.get("host") == "10.0.0.1"
    # read timeout 应在 send_command 上
    mock_conn.send_command.assert_called()
    call_kwargs = mock_conn.send_command.call_args.kwargs
    assert call_kwargs.get("read_timeout") == 30
