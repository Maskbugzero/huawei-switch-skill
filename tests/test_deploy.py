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
        assert "success_count" in report["rollback"]
        assert "failed_count" in report["rollback"]


def test_deploy_failure_without_auto_rollback():
    """测试部署失败但关闭自动回滚"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()

    # 使用一个更稳定的方式：通过 backup_path 是否存在来判断阶段
    backup_done = [False]

    def send_side_effect(cmd, timeout=None):
        if not backup_done[0]:
            # 备份阶段（采集 current-configuration）成功
            if "current-configuration" in cmd:
                backup_done[0] = True
            return None
        else:
            # 部署阶段失败
            raise Exception("部署失败")

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


def test_deploy_idempotent_skip_when_no_change():
    """测试配置无差异时自动跳过部署（幂等性保护）"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()

    same_config = "interface Vlanif10\n ip address 192.168.10.1 24\n# comment"

    with patch.object(engine, "renderer") as mock_renderer, \
         patch.object(engine.exporter, "export_backup") as mock_export:

        mock_renderer.render.return_value = same_config
        mock_export.return_value = "backups/SW-01/20260801-test"

        with patch("src.deploy.deployer.ConfigCollector") as mock_collector_cls:
            mock_collector = MagicMock()
            mock_collector.collect_current_config.return_value = same_config
            mock_collector_cls.return_value = mock_collector

            report = engine.deploy(
                connection=mock_conn,
                template="access_switch.j2",
                variables={"hostname": "SW-01"},
                device_name="SW-01",
                backup=True,
            )

            assert report["status"] == "skipped"
            assert "no configuration changes detected" in report.get("reason", "")
            mock_conn.send_command.assert_not_called()


def test_normalize_config_function():
    """测试配置规范化函数"""
    from src.deploy.deployer import _normalize_config

    raw = """
    # 这是一条注释
    interface Vlanif10
        ip address 192.168.10.1 24

    # 另一条注释
    vlan 10
    """

    normalized = _normalize_config(raw)
    assert "interface Vlanif10" in normalized
    assert "ip address 192.168.10.1 24" in normalized
    assert "vlan 10" in normalized
    assert "# 这是一条注释" not in normalized


def test_deployment_planner():
    """测试 DeploymentPlanner 增强功能"""
    from src.deploy.planner import DeploymentPlanner

    planner = DeploymentPlanner()
    config = """
    # 注释
    interface Vlanif10
    ip address 192.168.10.1 24
    interface Vlanif10          # 重复
    vlan 100
    """

    steps = planner.plan(config)
    assert len(steps) == 3
    assert "interface Vlanif10" in steps
    assert steps.count("interface Vlanif10") == 1

    categories = planner.plan_with_categories(config)
    assert "interface Vlanif10" in categories["config"]
    assert "vlan 100" in categories["other"]


def test_deployment_planner_rollback_plan():
    """测试 DeploymentPlanner 生成回滚计划"""
    from src.deploy.planner import DeploymentPlanner

    planner = DeploymentPlanner()
    config = "interface Vlanif10\nip address 192.168.10.1 24\nvlan 100"

    rollback = planner.generate_rollback_plan(config)
    assert len(rollback) == 3
    assert rollback[0].startswith("undo interface")
    assert rollback[1].startswith("undo ip address")


def test_deploy_current_config_collection_failure():
    """测试采集当前配置失败时的行为"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()

    with patch("src.deploy.deployer.ConfigCollector") as mock_collector_cls:
        mock_collector = MagicMock()
        mock_collector.collect_current_config.side_effect = Exception("连接超时")
        mock_collector_cls.return_value = mock_collector

        with patch.object(engine, "renderer") as mock_renderer:
            mock_renderer.render.return_value = "interface Vlanif10"

            report = engine.deploy(
                connection=mock_conn,
                template="access_switch.j2",
                variables={"hostname": "SW-01"},
                device_name="SW-01",
                backup=False,
            )

            # 即使采集失败，也应该继续执行（不跳过）
            assert report["status"] in ["success", "failed", "dry_run"]
            assert report.get("changes_detected") == "unknown (no current config for comparison)"


def test_deploy_failure_with_suggested_undo():
    """测试部署失败时是否生成 suggested_undo_commands"""
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
        # 检查是否生成了建议的 undo 命令
        assert "suggested_undo_commands" in report["rollback"]


def test_deploy_dangerous_command_detection():
    """测试危险命令检测功能"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()

    with patch.object(engine, "renderer") as mock_renderer:
        mock_renderer.render.return_value = "reboot\ninterface Vlanif10"

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables={"hostname": "SW-01"},
            device_name="SW-01",
            backup=False,
        )

        assert "warnings" in report
        assert any("危险命令" in w for w in report["warnings"])
