# -*- coding: utf-8 -*-
"""
SSH 批量管理测试（Mock，无真机）。
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.ssh.inventory import DeviceInventory, InventoryDevice, load_inventory
from src.ssh.batch import BatchSSHManager, BatchReport, DeviceResult


def test_load_inventory_merges_defaults(tmp_path: Path):
    inv_file = tmp_path / "devices.yaml"
    inv_file.write_text(
        yaml.safe_dump(
            {
                "defaults": {"username": "admin", "port": 22},
                "devices": [
                    {"name": "SW1", "host": "10.0.0.1", "password": "p1"},
                    {
                        "name": "SW2",
                        "host": "10.0.0.2",
                        "password": "p2",
                        "username": "ops",
                        "port": 2222,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    inv = load_inventory(inv_file)
    assert len(inv.devices) == 2
    assert inv.devices[0].username == "admin"
    assert inv.devices[0].port == 22
    assert inv.devices[1].username == "ops"
    assert inv.devices[1].port == 2222


def test_load_inventory_password_env(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SW_TEST_PASS", "from-env")
    inv_file = tmp_path / "devices.yaml"
    inv_file.write_text(
        yaml.safe_dump(
            {
                "devices": [
                    {
                        "name": "SW1",
                        "host": "10.0.0.1",
                        "password_env": "SW_TEST_PASS",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    inv = load_inventory(inv_file)
    assert inv.devices[0].password.get_secret_value() == "from-env"


def test_batch_backup_all_success(tmp_path: Path):
    inv = DeviceInventory(
        devices=[
            InventoryDevice(name="SW1", host="10.0.0.1", password="x"),
            InventoryDevice(name="SW2", host="10.0.0.2", password="y"),
        ]
    )
    mgr = BatchSSHManager(inv, backup_base_dir=str(tmp_path / "backups"))

    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "sysname SW\n#"

    with patch("src.ssh.batch.ConnectHandler", return_value=mock_conn):
        report = mgr.backup_all()

    assert report.success_count == 2
    assert report.failed_count == 0
    assert all(r.success for r in report.results)
    assert all("backup_path" in r.data for r in report.results)
    mock_conn.disconnect.assert_called()


def test_batch_backup_partial_failure(tmp_path: Path):
    inv = DeviceInventory(
        devices=[
            InventoryDevice(name="SW1", host="10.0.0.1", password="x"),
            InventoryDevice(name="SW2", host="10.0.0.2", password="y"),
        ]
    )
    mgr = BatchSSHManager(inv, backup_base_dir=str(tmp_path / "backups"))

    calls = {"n": 0}

    def connect_side_effect(**kwargs):
        calls["n"] += 1
        if kwargs.get("host") == "10.0.0.2":
            raise OSError("connection refused")
        m = MagicMock()
        m.send_command.return_value = "cfg"
        return m

    with patch("src.ssh.batch.ConnectHandler", side_effect=connect_side_effect):
        report = mgr.backup_all()

    assert report.success_count == 1
    assert report.failed_count == 1
    by_name = {r.name: r for r in report.results}
    assert by_name["SW1"].success is True
    assert by_name["SW2"].success is False


def test_batch_command_all(tmp_path: Path):
    inv = DeviceInventory(
        devices=[InventoryDevice(name="SW1", host="10.0.0.1", password="x")]
    )
    mgr = BatchSSHManager(inv)

    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = lambda cmd, **kw: f"out:{cmd}"

    with patch("src.ssh.batch.ConnectHandler", return_value=mock_conn):
        report = mgr.command_all("display version")

    assert report.success_count == 1
    assert "display version" in report.results[0].data.get("output", "")


def test_batch_command_detects_device_error():
    """设备回 Error 时 success=False（ErrorDetector）。"""
    inv = DeviceInventory(
        devices=[InventoryDevice(name="SW1", host="10.0.0.1", password="x")]
    )
    mgr = BatchSSHManager(inv)
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "Error: Unrecognized command found at '^' position"

    with patch("src.ssh.batch.ConnectHandler", return_value=mock_conn):
        report = mgr.command_all("display verison")

    assert report.success_count == 0
    assert report.failed_count == 1
    assert report.results[0].success is False
    assert report.results[0].error


def test_batch_command_blocks_dangerous_by_default():
    inv = DeviceInventory(
        devices=[InventoryDevice(name="SW1", host="10.0.0.1", password="x")]
    )
    mgr = BatchSSHManager(inv)

    with patch("src.ssh.batch.ConnectHandler") as ch:
        report = mgr.command_all("reboot")

    ch.assert_not_called()
    assert report.failed_count == 1
    assert report.results[0].success is False
    assert "dangerous" in (report.results[0].error or "").lower() or \
           "dangerous" in report.results[0].message.lower()


def test_batch_command_allow_dangerous():
    inv = DeviceInventory(
        devices=[InventoryDevice(name="SW1", host="10.0.0.1", password="x")]
    )
    mgr = BatchSSHManager(inv)
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "Info: System is rebooting"

    with patch("src.ssh.batch.ConnectHandler", return_value=mock_conn):
        report = mgr.command_all("reboot", allow_dangerous=True)

    assert report.success_count == 1


def test_batch_command_rejects_empty():
    inv = DeviceInventory(
        devices=[InventoryDevice(name="SW1", host="10.0.0.1", password="x")]
    )
    mgr = BatchSSHManager(inv)
    with pytest.raises(ValueError):
        mgr.command_all("   ")


def test_batch_filter_by_names(tmp_path: Path):
    inv = DeviceInventory(
        devices=[
            InventoryDevice(name="SW1", host="10.0.0.1", password="x"),
            InventoryDevice(name="SW2", host="10.0.0.2", password="y"),
        ]
    )
    mgr = BatchSSHManager(inv, backup_base_dir=str(tmp_path / "backups"))
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "ok"

    with patch("src.ssh.batch.ConnectHandler", return_value=mock_conn) as ch:
        report = mgr.backup_all(names=["SW2"])

    assert report.success_count == 1
    assert report.results[0].name == "SW2"
    assert ch.call_count == 1


def test_batch_report_summary():
    report = BatchReport(
        results=[
            DeviceResult(name="a", host="1", success=True),
            DeviceResult(name="b", host="2", success=False, error="x"),
        ]
    )
    s = report.summary()
    assert "1" in s and "1" in s  # success/fail counts appear
    assert "success" in s.lower() or "成功" in s
