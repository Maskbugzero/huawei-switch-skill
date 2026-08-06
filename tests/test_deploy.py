# -*- coding: utf-8 -*-
"""
部署引擎测试
"""

from unittest.mock import MagicMock, patch

from src.deploy.deployer import DeploymentEngine


def _vars(**extra):
    base = {"hostname": "SW-01", "admin_password": "Secret@2026"}
    base.update(extra)
    return base


def test_deploy_success():
    """测试部署成功场景"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "OK"

    with patch.object(engine.exporter, "export_backup") as mock_export:
        mock_export.return_value = "backups/SW-01/20260801-test"

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables=_vars(),
            device_name="SW-01",
            backup=True,
            save=False, verify=False)

        assert report["status"] == "success"
        assert "backup" in report["steps"]
        assert "render" in report["steps"]
        assert "deploy" in report["steps"]
        assert "backup_path" in report


def test_deploy_failure_with_auto_rollback():
    """测试部署失败时显式开启自动回滚"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()

    with patch.object(engine.exporter, "export_backup") as mock_export, \
         patch.object(engine, "renderer") as mock_renderer, \
         patch("src.deploy.deployer.ConfigCollector") as mock_collector_cls, \
         patch("src.deploy.deployer.CommandExecutor") as mock_exec_cls:
        mock_export.return_value = "backups/SW-01/20260801-test"
        mock_renderer.render.return_value = "sysname X\nvlan batch 10"
        mock_collector = MagicMock()
        mock_collector.collect_current_config.return_value = "sysname OLD\n"
        mock_collector_cls.return_value = mock_collector

        mock_executor = MagicMock()
        mock_executor.send_command.side_effect = Exception("部署失败")
        mock_exec_cls.return_value = mock_executor

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables=_vars(),
            device_name="SW-01",
            backup=True,
            auto_rollback_on_failure=True,
            save=False, verify=False)

        assert report["status"] == "failed"
        assert "rollback" in report
        assert report["rollback"]["attempted"] is True
        assert "success_count" in report["rollback"]
        assert "failed_count" in report["rollback"]


def test_deploy_auto_rollback_default_is_off():
    """默认不自动回滚（避免危险的 running-config 逐行重放）。"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()

    with patch.object(engine.exporter, "export_backup") as mock_export, \
         patch.object(engine, "renderer") as mock_renderer, \
         patch("src.deploy.deployer.ConfigCollector") as mock_collector_cls, \
         patch("src.deploy.deployer.CommandExecutor") as mock_exec_cls:
        mock_export.return_value = "backups/SW-01/20260801-test"
        mock_renderer.render.return_value = "sysname X\nvlan batch 10"
        mock_collector = MagicMock()
        mock_collector.collect_current_config.return_value = "sysname OLD\n"
        mock_collector_cls.return_value = mock_collector
        mock_executor = MagicMock()
        mock_executor.send_command.side_effect = Exception("部署失败")
        mock_exec_cls.return_value = mock_executor

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables=_vars(),
            device_name="SW-01",
            backup=True,
            save=False, verify=False)

    assert report["status"] == "failed"
    assert report.get("rollback", {}).get("attempted") is False


def test_deploy_failure_without_auto_rollback():
    """测试部署失败但关闭自动回滚"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()

    with patch.object(engine.exporter, "export_backup") as mock_export, \
         patch.object(engine, "renderer") as mock_renderer, \
         patch("src.deploy.deployer.ConfigCollector") as mock_collector_cls, \
         patch("src.deploy.deployer.CommandExecutor") as mock_exec_cls:
        mock_export.return_value = "backups/SW-01/20260801-test"
        mock_renderer.render.return_value = "sysname X"
        mock_collector = MagicMock()
        mock_collector.collect_current_config.return_value = "sysname OLD\n"
        mock_collector_cls.return_value = mock_collector
        mock_executor = MagicMock()
        mock_executor.send_command.side_effect = Exception("部署失败")
        mock_exec_cls.return_value = mock_executor

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables=_vars(),
            device_name="SW-01",
            backup=True,
            auto_rollback_on_failure=False,
            save=False, verify=False)

        assert report["status"] == "failed"
        assert report.get("rollback", {}).get("attempted") is False


def test_deploy_no_backup_no_rollback():
    """测试不备份的情况下失败不会尝试回滚"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()

    with patch.object(engine, "renderer") as mock_renderer, \
         patch("src.deploy.deployer.ConfigCollector") as mock_collector_cls, \
         patch("src.deploy.deployer.CommandExecutor") as mock_exec_cls:
        mock_renderer.render.return_value = "sysname X"
        mock_collector = MagicMock()
        mock_collector.collect_current_config.return_value = "sysname OLD\n"
        mock_collector_cls.return_value = mock_collector
        mock_executor = MagicMock()
        mock_executor.send_command.side_effect = Exception("部署失败")
        mock_exec_cls.return_value = mock_executor

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables=_vars(),
            backup=False,
            auto_rollback_on_failure=True,
            save=False, verify=False)

    assert report["status"] == "failed"
    assert "backup_path" not in report
    assert report.get("rollback", {}).get("attempted") is False


def test_deploy_idempotent_skip_when_no_change():
    """目标配置行已全部存在于当前配置时跳过（意图子集匹配）。"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()

    target = "interface Vlanif10\n ip address 192.168.10.1 24\n# comment"
    # 当前配置是超集（整机配置场景）
    current = (
        "sysname SW-01\n"
        "interface Vlanif10\n"
        " ip address 192.168.10.1 24\n"
        "vlan batch 10 20\n"
    )

    with patch.object(engine, "renderer") as mock_renderer, \
         patch.object(engine.exporter, "export_backup") as mock_export:

        mock_renderer.render.return_value = target
        mock_export.return_value = "backups/SW-01/20260801-test"

        with patch("src.deploy.deployer.ConfigCollector") as mock_collector_cls:
            mock_collector = MagicMock()
            mock_collector.collect_current_config.return_value = current
            mock_collector_cls.return_value = mock_collector

            report = engine.deploy(
                connection=mock_conn,
                template="access_switch.j2",
                variables=_vars(),
                device_name="SW-01",
                backup=True, verify=False)

            assert report["status"] == "skipped"
            reason = report.get("reason", "")
            assert (
                "no configuration changes detected" in reason
                or "意图" in reason
                or "intent" in reason
            )
            mock_conn.send_command.assert_not_called()


def test_deploy_idempotent_detects_missing_intent_lines():
    """目标中有当前配置没有的行时应继续部署。"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "OK"

    target = "sysname NEW-SW\nvlan batch 10 20 30"
    current = "sysname OLD-SW\nvlan batch 10 20"

    with patch.object(engine, "renderer") as mock_renderer:
        mock_renderer.render.return_value = target
        with patch("src.deploy.deployer.ConfigCollector") as mock_collector_cls:
            mock_collector = MagicMock()
            mock_collector.collect_current_config.return_value = current
            mock_collector_cls.return_value = mock_collector

            report = engine.deploy(
                connection=mock_conn,
                template="access_switch.j2",
                variables=_vars(),
                backup=False,
                save=False, verify=False)

    assert report["status"] == "success"
    assert report.get("changes_detected") is True


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
    """过滤注释/空行；连续完全相同的行可折叠；非连续重复必须保留。"""
    from src.deploy.planner import DeploymentPlanner

    planner = DeploymentPlanner()
    config = """
    # 注释
    interface Vlanif10
    ip address 192.168.10.1 24
    interface Vlanif10          # 非连续重复（中间有其他行）→ 必须保留
    vlan 100
    """

    steps = planner.plan(config)
    assert "interface Vlanif10" in steps
    assert steps.count("interface Vlanif10") == 2
    assert "ip address 192.168.10.1 24" in steps
    assert "vlan 100" in steps
    assert all(not s.startswith("#") for s in steps)

    categories = planner.plan_with_categories(config)
    assert "interface Vlanif10" in categories["config"]
    assert "vlan 100" in categories["other"]


def test_deployment_planner_preserves_repeated_interface_subcommands():
    """多接口模板中相同子命令不得被全局去重丢掉（P0）。"""
    from src.deploy.planner import DeploymentPlanner

    planner = DeploymentPlanner()
    config = """
system-view
interface GigabitEthernet0/0/1
 port link-type access
 port default vlan 20
 undo shutdown
interface GigabitEthernet0/0/2
 port link-type access
 port default vlan 20
 undo shutdown
return
"""
    steps = planner.plan(config)
    assert steps.count("port link-type access") == 2
    assert steps.count("port default vlan 20") == 2
    assert steps.count("undo shutdown") == 2
    assert steps.index("interface GigabitEthernet0/0/1") < steps.index(
        "interface GigabitEthernet0/0/2"
    )
    # 每个 interface 后都应跟齐子命令
    i1 = steps.index("interface GigabitEthernet0/0/1")
    i2 = steps.index("interface GigabitEthernet0/0/2")
    block1 = steps[i1:i2]
    block2 = steps[i2:]
    assert "port link-type access" in block1 and "undo shutdown" in block1
    assert "port link-type access" in block2 and "undo shutdown" in block2


def test_deployment_planner_collapses_only_consecutive_duplicates():
    """仅折叠连续完全相同的行，避免误粘贴放大。"""
    from src.deploy.planner import DeploymentPlanner

    planner = DeploymentPlanner()
    steps = planner.plan("vlan 10\nvlan 10\nvlan 20\nvlan 10\n")
    assert steps == ["vlan 10", "vlan 20", "vlan 10"]


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
    mock_conn.send_command.return_value = "OK"

    with patch("src.deploy.deployer.ConfigCollector") as mock_collector_cls:
        mock_collector = MagicMock()
        mock_collector.collect_current_config.side_effect = Exception("连接超时")
        mock_collector_cls.return_value = mock_collector

        with patch.object(engine, "renderer") as mock_renderer:
            mock_renderer.render.return_value = "interface Vlanif10"

            report = engine.deploy(
                connection=mock_conn,
                template="access_switch.j2",
                variables=_vars(),
                device_name="SW-01",
                backup=False,
                save=False, verify=False)

            # 即使采集失败，也应该继续执行（不跳过）
            assert report["status"] in ["success", "failed", "dry_run"]
            assert report.get("changes_detected") == "unknown (no current config for comparison)"


def test_deploy_failure_with_suggested_undo():
    """测试部署失败且显式回滚时是否生成 suggested_undo_commands"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()

    with patch.object(engine.exporter, "export_backup") as mock_export, \
         patch.object(engine, "renderer") as mock_renderer, \
         patch("src.deploy.deployer.ConfigCollector") as mock_collector_cls, \
         patch("src.deploy.deployer.CommandExecutor") as mock_exec_cls:
        mock_export.return_value = "backups/SW-01/20260801-test"
        mock_renderer.render.return_value = "sysname X\nvlan batch 10"
        mock_collector = MagicMock()
        mock_collector.collect_current_config.return_value = "sysname OLD\n"
        mock_collector_cls.return_value = mock_collector
        mock_executor = MagicMock()
        mock_executor.send_command.side_effect = Exception("部署失败")
        mock_exec_cls.return_value = mock_executor

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables=_vars(),
            device_name="SW-01",
            backup=True,
            auto_rollback_on_failure=True,
            save=False, verify=False)

        assert report["status"] == "failed"
        assert "rollback" in report
        assert report["rollback"]["attempted"] is True
        assert "suggested_undo_commands" in report["rollback"]


def test_deploy_dangerous_command_blocked_by_default():
    """危险命令默认阻断，不执行下发。"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()

    with patch.object(engine, "renderer") as mock_renderer:
        mock_renderer.render.return_value = "reboot\ninterface Vlanif10"

        with patch("src.deploy.deployer.ConfigCollector") as mock_collector_cls:
            mock_collector = MagicMock()
            mock_collector.collect_current_config.return_value = "sysname OLD"
            mock_collector_cls.return_value = mock_collector

            report = engine.deploy(
                connection=mock_conn,
                template="access_switch.j2",
                variables=_vars(),
                device_name="SW-01",
                backup=False, verify=False)

    assert report["status"] == "blocked"
    assert report.get("dangerous_commands")
    # 除可能的采集外，不应进入部署下发（collect 使用 ConfigCollector mock）
    mock_conn.send_command.assert_not_called()


def test_deploy_dangerous_command_allowed_when_explicit():
    """显式 allow_dangerous=True 时仅警告并继续。"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "OK"

    with patch.object(engine, "renderer") as mock_renderer:
        mock_renderer.render.return_value = "interface Vlanif10\n description safe"
        # 自定义关键词以便测试 allow 路径且命令本身可执行
        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables=_vars(),
            device_name="SW-01",
            backup=False,
            allow_dangerous=True,
            dangerous_keywords=["interface"],
            save=False, verify=False)

    assert report["status"] == "success"
    assert "warnings" in report
    assert any("危险命令" in w for w in report["warnings"])


def test_deploy_uses_command_executor_for_error_detection():
    """部署主路径应通过 CommandExecutor，设备回错时标记 failed。"""
    from src.command.exceptions import CommandExecutionError

    engine = DeploymentEngine()
    mock_conn = MagicMock()

    with patch.object(engine, "renderer") as mock_renderer, \
         patch("src.deploy.deployer.CommandExecutor") as mock_exec_cls, \
         patch("src.deploy.deployer.ConfigCollector") as mock_collector_cls:
        mock_renderer.render.return_value = "sysname X\nvlan batch 10"
        mock_collector = MagicMock()
        mock_collector.collect_current_config.return_value = "sysname OLD"
        mock_collector_cls.return_value = mock_collector

        mock_executor = MagicMock()
        mock_executor.send_command.side_effect = CommandExecutionError(
            error_type="Error: Unrecognized command",
            output="Error: Unrecognized command",
            command="sysname X",
        )
        mock_exec_cls.return_value = mock_executor

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables=_vars(),
            backup=False, verify=False)

    assert report["status"] == "failed"
    mock_exec_cls.assert_called_once()


def test_configs_differ_respects_interface_context():
    """同名配置行在错误接口下不算意图已满足（P1 结构化 diff）。"""
    engine = DeploymentEngine()
    target = (
        "interface GigabitEthernet0/0/1\n"
        " ip address 10.0.0.1 255.255.255.0\n"
    )
    current = (
        "interface GigabitEthernet0/0/2\n"
        " ip address 10.0.0.1 255.255.255.0\n"
        "interface GigabitEthernet0/0/1\n"
        " description empty\n"
    )
    is_diff, summary = engine._configs_differ(target, current)
    assert is_diff is True
    assert "GigabitEthernet0/0/1" in summary or "interface" in summary.lower() or "缺少" in summary


def test_configs_differ_same_interface_intent_satisfied():
    """目标接口块内行均已在同一接口下出现 → 无差异。"""
    engine = DeploymentEngine()
    target = (
        "interface Vlanif10\n"
        " ip address 192.168.10.1 24\n"
    )
    current = (
        "sysname SW-01\n"
        "interface Vlanif10\n"
        " ip address 192.168.10.1 24\n"
        " description mgmt\n"
        "vlan batch 10 20\n"
    )
    is_diff, summary = engine._configs_differ(target, current)
    assert is_diff is False
    assert "意图" in summary or "满足" in summary


def test_configs_differ_global_lines_still_checked():
    """全局行（非 interface 上下文）仍需出现在当前配置全局区。"""
    engine = DeploymentEngine()
    target = "sysname NEW-SW\nvlan batch 10 20 30\n"
    current = "sysname OLD-SW\nvlan batch 10 20\n"
    is_diff, _ = engine._configs_differ(target, current)
    assert is_diff is True


def test_configs_differ_ignores_password_and_cipher_lines():
    """幂等比较忽略密钥行：设备密文与模板明文不一致不应阻止 skip。"""
    engine = DeploymentEngine()
    target = (
        "sysname SW-01\n"
        "aaa\n"
        " local-user admin password irreversible-cipher Secret@2026\n"
        " local-user admin privilege level 15\n"
        " quit\n"
        "interface Vlanif10\n"
        " ip address 192.168.10.1 24\n"
    )
    current = (
        "sysname SW-01\n"
        "aaa\n"
        " local-user admin password irreversible-cipher ******\n"
        " local-user admin privilege level 15\n"
        " quit\n"
        "interface Vlanif10\n"
        " ip address 192.168.10.1 24\n"
    )
    is_diff, summary = engine._configs_differ(target, current)
    assert is_diff is False
    assert "意图" in summary or "满足" in summary


def test_configs_differ_still_detects_missing_after_ignoring_secrets():
    """忽略密钥后，其它缺失行仍应检出。"""
    engine = DeploymentEngine()
    target = (
        "sysname SW-01\n"
        " local-user admin password irreversible-cipher Secret@2026\n"
        "vlan batch 10 20 30\n"
    )
    current = (
        "sysname SW-01\n"
        " local-user admin password irreversible-cipher ******\n"
        "vlan batch 10 20\n"
    )
    is_diff, summary = engine._configs_differ(target, current)
    assert is_diff is True
    assert "vlan batch" in summary or "缺少" in summary


def test_deploy_saves_by_default_after_success():
    """部署成功后默认执行 save。"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "OK"

    with patch.object(engine, "renderer") as mock_renderer, \
         patch("src.deploy.deployer.CommandExecutor") as mock_exec_cls, \
         patch("src.deploy.deployer.ConfigCollector") as mock_collector_cls:
        mock_renderer.render.return_value = "sysname X\nvlan batch 10"
        mock_collector = MagicMock()
        mock_collector.collect_current_config.return_value = "sysname OLD"
        mock_collector_cls.return_value = mock_collector

        mock_executor = MagicMock()
        mock_executor.send_command.return_value = "OK"
        mock_exec_cls.return_value = mock_executor

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables=_vars(),
            backup=False, verify=False)

    assert report["status"] == "success"
    assert report.get("saved") is True
    cmds = [c.args[0] for c in mock_executor.send_command.call_args_list]
    assert "save" in cmds
    assert cmds[-1] == "save"


def test_deploy_save_can_be_disabled():
    """save=False 时不落盘。"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "OK"

    with patch.object(engine, "renderer") as mock_renderer, \
         patch("src.deploy.deployer.CommandExecutor") as mock_exec_cls, \
         patch("src.deploy.deployer.ConfigCollector") as mock_collector_cls:
        mock_renderer.render.return_value = "sysname X"
        mock_collector = MagicMock()
        mock_collector.collect_current_config.return_value = "sysname OLD"
        mock_collector_cls.return_value = mock_collector
        mock_executor = MagicMock()
        mock_executor.send_command.return_value = "OK"
        mock_exec_cls.return_value = mock_executor

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables=_vars(),
            backup=False,
            save=False, verify=False)

    assert report["status"] == "success"
    assert report.get("saved") is False
    cmds = [c.args[0] for c in mock_executor.send_command.call_args_list]
    assert "save" not in cmds


def test_deploy_skips_empty_backup_when_collect_fails():
    """采集失败时不得写出空备份供回滚使用。"""
    engine = DeploymentEngine()
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "OK"

    with patch("src.deploy.deployer.ConfigCollector") as mock_collector_cls, \
         patch.object(engine, "renderer") as mock_renderer, \
         patch.object(engine.exporter, "export_backup") as mock_export:
        mock_collector = MagicMock()
        mock_collector.collect_current_config.side_effect = Exception("timeout")
        mock_collector_cls.return_value = mock_collector
        mock_renderer.render.return_value = "sysname X"
        mock_export.return_value = "backups/should-not"

        report = engine.deploy(
            connection=mock_conn,
            template="access_switch.j2",
            variables=_vars(),
            device_name="SW-01",
            backup=True,
            save=False, verify=False)

    mock_export.assert_not_called()
    assert "backup_path" not in report or report.get("backup_skipped") is True
    assert report.get("backup_skipped") is True
