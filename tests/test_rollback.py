# -*- coding: utf-8 -*-
"""
回滚模块测试
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.deploy.rollback import RollbackManager, RollbackReport


def test_rollback_report_summary():
    """测试 RollbackReport 的摘要输出"""
    report = RollbackReport(
        success=True,
        success_count=10,
        failed_count=2,
        backup_path="backups/SW-01/20260801-143022"
    )
    summary = report.summary()
    assert "成功: 10" in summary
    assert "失败: 2" in summary
    assert "backups/SW-01/20260801-143022" in summary


def test_rollback_report_dry_run_summary():
    """测试 dry_run 模式的摘要"""
    report = RollbackReport(
        success=True,
        success_count=5,
        failed_count=0,
        backup_path="backups/SW-01/20260801-143022",
        dry_run=True
    )
    summary = report.summary()
    assert "【Dry Run】" in summary


def test_rollback_file_not_exist(tmp_path):
    """测试备份文件不存在的情况"""
    mgr = RollbackManager()
    fake_conn = MagicMock()

    non_exist_path = str(tmp_path / "non_exist_backup")
    report = mgr.rollback(fake_conn, non_exist_path)

    assert report.success is False
    assert report.failed_count == 0
    assert any("不存在" in err for err in report.errors)


def test_rollback_dry_run(tmp_path):
    """测试 dry_run 模式"""
    mgr = RollbackManager()

    # 创建一个临时备份目录和文件
    backup_dir = tmp_path / "backup_test"
    backup_dir.mkdir()
    config_file = backup_dir / "current-configuration.txt"
    config_file.write_text("interface Vlanif10\nip address 192.168.10.1 24\n", encoding="utf-8")

    fake_conn = MagicMock()
    report = mgr.rollback(fake_conn, str(backup_dir), dry_run=True)

    assert report.success is True
    assert report.dry_run is True
    assert report.success_count > 0
    # dry_run 模式下不应该调用 send_command
    fake_conn.send_command.assert_not_called()


def test_rollback_with_mock_connection_success(tmp_path):
    """测试使用 Mock 连接成功执行回滚"""
    mgr = RollbackManager()

    backup_dir = tmp_path / "backup_success"
    backup_dir.mkdir()
    config_file = backup_dir / "current-configuration.txt"
    config_file.write_text("vlan 10\n", encoding="utf-8")

    fake_conn = MagicMock()
    report = mgr.rollback(fake_conn, str(backup_dir))

    assert report.success is True
    assert report.success_count == 1
    fake_conn.send_command.assert_called_once_with("vlan 10")


def test_rollback_with_mock_connection_partial_failure(tmp_path):
    """测试部分命令失败的情况"""
    mgr = RollbackManager()

    backup_dir = tmp_path / "backup_partial"
    backup_dir.mkdir()
    config_file = backup_dir / "current-configuration.txt"
    config_file.write_text("vlan 10\nvlan 20\n", encoding="utf-8")

    fake_conn = MagicMock()
    # 让第二次调用抛出异常
    fake_conn.send_command.side_effect = [None, Exception("命令失败")]

    report = mgr.rollback(fake_conn, str(backup_dir))

    assert report.success is False
    assert report.success_count == 1
    assert report.failed_count == 1
    assert len(report.errors) == 1
