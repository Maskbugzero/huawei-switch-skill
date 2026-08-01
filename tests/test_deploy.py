# -*- coding: utf-8 -*-
"""
部署引擎测试
"""

from unittest.mock import MagicMock, patch

from src.deploy.deployer import DeploymentEngine


def test_deploy_success():
    """测试部署成功场景"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()

    with patch.object(engine.exporter, "export_backup") as mock_export:
        mock_export.return_value = "backups/SW-01/20260801-test"

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables={"hostname": "SW-01"},
            device_name="SW-01",
            backup=True,
        )

        assert report["status"] == "success"
        assert "backup" in report["steps"]
        assert "render" in report["steps"]
        assert "deploy" in report["steps"]
        assert "backup_path" in report


def test_deploy_failure_with_auto_rollback():
    """测试部署失败时自动触发回滚"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()

    # 模拟第三条命令失败
    call_count = [0]

    def send_side_effect(cmd, timeout=None):
        call_count[0] += 1
        if call_count[0] >= 3:
            raise Exception("部署失败")
        return None

    mock_conn.send_command.side_effect = send_side_effect

    with patch.object(engine.exporter, "export_backup") as mock_export:
        mock_export.return_value = "backups/SW-01/20260801-test"

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables={"hostname": "SW-01"},
            device_name="SW-01",
            backup=True,
            auto_rollback_on_failure=True,
        )

        assert report["status"] == "failed"
        assert "rollback" in report
        assert report["rollback"]["attempted"] is True


def test_deploy_failure_without_auto_rollback():
    """测试部署失败但关闭自动回滚"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()

    call_count = [0]

    def send_side_effect(cmd, timeout=None):
        call_count[0] += 1
        # 备份阶段（第1次大配置采集）成功，部署阶段失败
        if call_count[0] > 5:   # 假设备份后第6次开始是部署
            raise Exception("部署失败")
        return None

    mock_conn.send_command.side_effect = send_side_effect

    with patch.object(engine.exporter, "export_backup") as mock_export:
        mock_export.return_value = "backups/SW-01/20260801-test"

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables={"hostname": "SW-01"},
            device_name="SW-01",
            backup=True,
            auto_rollback_on_failure=False,
        )

        assert report["status"] == "failed"
        assert report.get("rollback", {}).get("attempted") is False


def test_deploy_no_backup_no_rollback():
    """测试不备份的情况下失败不会尝试回滚"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = Exception("部署失败")

    report = engine.deploy(
        connection=mock_conn,
        template="access_switch.j2",
        variables={"hostname": "SW-01"},
        backup=False,
        auto_rollback_on_failure=True,
    )

    assert report["status"] == "failed"
    assert "backup_path" not in report
    assert report.get("rollback", {}).get("attempted") is False
