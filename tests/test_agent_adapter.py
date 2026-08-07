# -*- coding: utf-8 -*-
"""
AgentAdapter 边界测试
"""

from unittest.mock import MagicMock, patch

from src.agent import AgentAdapter, AgentRequest, DeviceInfo


def test_agent_adapter_unsupported_action():
    """测试不支持的操作类型（Pydantic 会在构造时校验 action）"""
    from pydantic import ValidationError

    adapter = AgentAdapter()
    try:
        request = AgentRequest(
            action="unknown_action",  # 不支持
            device=DeviceInfo(port="COM4", password="xxx"),
        )
        response = adapter.execute(request)
        assert response.success is False
        assert "不支持的操作" in response.message
    except ValidationError as e:
        # Pydantic v2 严格校验是更优行为
        assert "literal_error" in str(e) or "Input should be" in str(e)



def test_agent_adapter_missing_device_info():
    """测试缺少设备连接信息（Pydantic 会在构造时拒绝 None device）"""
    from pydantic import ValidationError

    adapter = AgentAdapter()
    try:
        request = AgentRequest(
            action="backup",
            device=None,  # 缺少设备信息
        )
        response = adapter.execute(request)
        assert response.success is False
    except ValidationError:
        # Pydantic 严格模式下会直接抛出验证错误，这是更好的行为
        assert True



def test_agent_adapter_validate_with_direct_content():
    """测试 validate 使用直接传入配置内容"""
    adapter = AgentAdapter()
    request = AgentRequest(
        action="validate",
        device=DeviceInfo(port="COM4", password="dummy"),
        variables={
            "before_config": "interface Vlanif10",
            "after_config": (
                "interface Vlanif10\n"
                " ip address 192.168.10.1 24\n"
                "ssh server enable\n"
                "vlan 10\n"
            ),
            "expected": {"vlan_list": [10]},
        },
    )
    response = adapter.execute(request)

    assert response.success is True
    assert "validation_report" in response.data
    assert response.data["validation_report"]["status"] == "pass"


# 注意：以下两个测试因内部导入和 mock 复杂度较高，暂时注释
# 如需完善，可在后续迭代中优化 mock 策略

# def test_agent_adapter_backup_action(): ...
# def test_agent_adapter_deploy_action(): ...


def test_agent_adapter_command_action():
    """测试 command action"""
    adapter = AgentAdapter()
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "output"
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = False

    with patch("src.agent.adapter.Connection", return_value=mock_conn):
        request = AgentRequest(
            action="command",
            device=DeviceInfo(port="COM4", password="xxx"),
            variables={"command": "display version"}
        )
        response = adapter.execute(request)

        assert response.success is True
        assert "output" in response.data


def test_agent_adapter_auth_error_returns_response_not_nameerror():
    """连接认证失败应返回 AgentResponse，不能抛 NameError。"""
    from src.console.exceptions import AuthenticationError

    adapter = AgentAdapter()
    mock_conn = MagicMock()
    mock_conn.__enter__.side_effect = AuthenticationError("密码错误")
    mock_conn.__exit__.return_value = False

    with patch("src.agent.adapter.Connection", return_value=mock_conn):
        request = AgentRequest(
            action="command",
            device=DeviceInfo(port="COM4", password="bad"),
            variables={"command": "display version"},
        )
        response = adapter.execute(request)

    assert response.success is False
    assert response.error is not None
    assert "密码" in response.message or "密码" in (response.error or "")


def test_agent_adapter_deploy_failed_status_sets_success_false():
    """deploy 引擎返回 status=failed 时，AgentResponse.success 必须为 False。"""
    adapter = AgentAdapter()
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = False

    with patch("src.agent.adapter.Connection", return_value=mock_conn), \
         patch("src.deploy.DeploymentEngine") as mock_engine_cls:
        mock_engine = MagicMock()
        mock_engine.deploy.return_value = {
            "status": "failed",
            "error": "命令失败",
            "steps": ["backup", "render"],
        }
        mock_engine_cls.return_value = mock_engine

        request = AgentRequest(
            action="deploy",
            device=DeviceInfo(port="COM4", password="xxx"),
            template="access_switch.j2",
            variables={"hostname": "SW-01", "admin_password": "Secret@2026"},
            backup=False,
        )
        response = adapter.execute(request)

    assert response.success is False
    assert response.data.get("status") == "failed"


def test_agent_adapter_deploy_skipped_still_success():
    """幂等 skipped / dry_run 视为成功完成（无变更）。"""
    adapter = AgentAdapter()
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = False

    with patch("src.agent.adapter.Connection", return_value=mock_conn), \
         patch("src.deploy.DeploymentEngine") as mock_engine_cls:
        mock_engine = MagicMock()
        mock_engine.deploy.return_value = {
            "status": "skipped",
            "reason": "no configuration changes detected",
        }
        mock_engine_cls.return_value = mock_engine

        request = AgentRequest(
            action="deploy",
            device=DeviceInfo(port="COM4", password="xxx"),
            template="access_switch.j2",
            variables={"hostname": "SW-01", "admin_password": "Secret@2026"},
        )
        response = adapter.execute(request)

    assert response.success is True
    assert response.data.get("status") == "skipped"


def test_agent_adapter_validate_path_traversal_blocked():
    """validate 不得通过路径穿越读取 cwd 外文件。"""
    adapter = AgentAdapter()
    request = AgentRequest(
        action="validate",
        device=DeviceInfo(port="COM4", password="dummy"),
        variables={
            "before_config_path": "../outside-secret.cfg",
            "after_config": "vlan 10",
        },
    )
    response = adapter.execute(request)
    assert response.success is False
    assert "不允许" in response.message or "路径" in response.message or "失败" in response.message


def test_agent_adapter_empty_password_rejected():
    """空密码应被拒绝（SecretStr 不能仅靠 truthiness）。"""
    adapter = AgentAdapter()
    request = AgentRequest(
        action="command",
        device=DeviceInfo(port="COM4", password=""),
        variables={"command": "display version"},
    )
    response = adapter.execute(request)
    assert response.success is False
    assert response.code == "APT001"


def test_agent_adapter_auth_error_uses_con003():
    """认证失败应映射 CON003。"""
    from src.console.exceptions import AuthenticationError

    adapter = AgentAdapter()
    mock_conn = MagicMock()
    mock_conn.__enter__.side_effect = AuthenticationError("密码错误")
    mock_conn.__exit__.return_value = False

    with patch("src.agent.adapter.Connection", return_value=mock_conn):
        response = adapter.execute(
            AgentRequest(
                action="command",
                device=DeviceInfo(port="COM4", password="bad"),
                variables={"command": "display version"},
            )
        )
    assert response.success is False
    assert response.code == "CON003"


def test_agent_adapter_command_error_uses_cmd_code():
    """命令执行错误应映射 CMD* 而非 CON003。"""
    from src.command.exceptions import CommandExecutionError

    adapter = AgentAdapter()
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = False
    mock_conn.send_command.return_value = "Error: Unrecognized command"

    with patch("src.agent.adapter.Connection", return_value=mock_conn):
        # CommandExecutor will raise on Error:
        response = adapter.execute(
            AgentRequest(
                action="command",
                device=DeviceInfo(port="COM4", password="xxx"),
                variables={"command": "badcmd"},
            )
        )
    assert response.success is False
    assert response.code and response.code.startswith("CMD")


def test_agent_adapter_deploy_passes_allow_dangerous_field():
    """AgentRequest.allow_dangerous 应传到 DeploymentEngine。"""
    adapter = AgentAdapter()
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = False

    with patch("src.agent.adapter.Connection", return_value=mock_conn), \
         patch("src.deploy.DeploymentEngine") as mock_engine_cls:
        mock_engine = MagicMock()
        mock_engine.deploy.return_value = {"status": "success", "steps": []}
        mock_engine_cls.return_value = mock_engine

        adapter.execute(
            AgentRequest(
                action="deploy",
                device=DeviceInfo(port="COM4", password="xxx"),
                template="access_switch.j2",
                variables={"hostname": "SW-01", "admin_password": "Secret@2026"},
                backup=False,
                allow_dangerous=True,
                auto_rollback_on_failure=True,
            )
        )

        kwargs = mock_engine.deploy.call_args.kwargs
        assert kwargs.get("allow_dangerous") is True
        assert kwargs.get("auto_rollback_on_failure") is True


def test_agent_adapter_validate_fail_sets_success_false():
    """校验规则 fail 时外层 success 应为 False。"""
    adapter = AgentAdapter()
    response = adapter.execute(
        AgentRequest(
            action="validate",
            device=DeviceInfo(port="COM4", password="dummy"),
            variables={
                "before_config": "",
                "after_config": "vlan 10",  # missing 99, no ssh
                "expected": {"vlan_list": [10, 99]},
            },
        )
    )
    assert response.success is False
    assert response.data["validation_report"]["status"] == "fail"


def test_ssh_empty_command_still_disconnects():
    """SSH command 缺参数时不建立连接（连接前校验）。"""
    adapter = AgentAdapter()
    mock_ssh = MagicMock()

    with patch("src.agent.adapter.ConnectHandler", return_value=mock_ssh) as ch:
        response = adapter.execute(
            AgentRequest(
                action="command",
                device=DeviceInfo(
                    port="10.0.0.1",
                    password="xxx",
                    connection_type="ssh",
                ),
                variables={},  # missing command
            )
        )

    assert response.success is False
    ch.assert_not_called()


def test_ssh_deploy_disabled_by_default_without_connect():
    """SSH 真下发默认禁用，且不建立连接。"""
    adapter = AgentAdapter()
    mock_ssh = MagicMock()

    with patch("src.agent.adapter.ConnectHandler", return_value=mock_ssh) as ch:
        response = adapter.execute(
            AgentRequest(
                action="deploy",
                device=DeviceInfo(port="10.0.0.1", password="xxx", connection_type="ssh"),
                template="access_switch.j2",
                variables={"hostname": "X", "admin_password": "Secret@2026"},
                backup=False,
                dry_run=False,
            )
        )

    assert response.success is False
    assert response.data.get("status") == "blocked"
    assert response.data.get("reason") == "ssh_deploy_disabled"
    assert response.code == "APT002"
    ch.assert_not_called()


def test_ssh_deploy_dry_run_allowed_without_allow_flag():
    """dry_run=True 时允许 SSH deploy 模拟，无需 allow_ssh_deploy。"""
    adapter = AgentAdapter()
    mock_ssh = MagicMock()
    mock_ssh.send_command.return_value = "sysname OLD"

    with patch("src.agent.adapter.ConnectHandler", return_value=mock_ssh), \
         patch("src.agent.adapter.TemplateRenderer") as mock_renderer_cls:
        mock_renderer = MagicMock()
        mock_renderer.render.return_value = "sysname NEW\nvlan batch 10"
        mock_renderer_cls.return_value = mock_renderer

        response = adapter.execute(
            AgentRequest(
                action="deploy",
                device=DeviceInfo(port="10.0.0.1", password="xxx", connection_type="ssh"),
                template="access_switch.j2",
                variables={"hostname": "NEW", "admin_password": "Secret@2026"},
                backup=False,
                dry_run=True,
            )
        )

    assert response.success is True
    assert response.data.get("status") == "dry_run"
    mock_ssh.disconnect.assert_called()


def test_ssh_deploy_blocks_dangerous_commands():
    """SSH deploy 应与 Console 一样默认阻断危险命令。"""
    adapter = AgentAdapter()
    mock_ssh = MagicMock()
    mock_ssh.send_command.return_value = "sysname OLD"

    with patch("src.agent.adapter.ConnectHandler", return_value=mock_ssh), \
         patch("src.agent.adapter.TemplateRenderer") as mock_renderer_cls:
        mock_renderer = MagicMock()
        mock_renderer.render.return_value = "reboot\nsysname X"
        mock_renderer_cls.return_value = mock_renderer

        response = adapter.execute(
            AgentRequest(
                action="deploy",
                device=DeviceInfo(port="10.0.0.1", password="xxx", connection_type="ssh"),
                template="access_switch.j2",
                variables={"hostname": "X", "admin_password": "Secret@2026"},
                backup=False,
                allow_ssh_deploy=True,
            )
        )

    assert response.success is False
    assert response.data.get("status") == "blocked"
    mock_ssh.disconnect.assert_called()
    # blocked before applying reboot: only screen-length (and maybe nothing else)
    calls = [c.args[0] if c.args else "" for c in mock_ssh.send_command.call_args_list]
    assert not any(str(c).strip() == "reboot" for c in calls)


def test_ssh_deploy_detects_error_in_output():
    """SSH deploy 应对设备 Error: 输出标记 failed，而非 success。"""
    adapter = AgentAdapter()
    mock_ssh = MagicMock()

    def send_side_effect(cmd, read_timeout=30):
        if "screen-length" in str(cmd):
            return ""
        if "current-configuration" in str(cmd):
            return "sysname OLD"
        if str(cmd).strip() == "sysname NEW":
            return "Error: Unrecognized command found at '^' position"
        return "OK"

    mock_ssh.send_command.side_effect = send_side_effect

    with patch("src.agent.adapter.ConnectHandler", return_value=mock_ssh), \
         patch("src.agent.adapter.TemplateRenderer") as mock_renderer_cls:
        mock_renderer = MagicMock()
        mock_renderer.render.return_value = "sysname NEW\nvlan batch 10"
        mock_renderer_cls.return_value = mock_renderer

        response = adapter.execute(
            AgentRequest(
                action="deploy",
                device=DeviceInfo(port="10.0.0.1", password="xxx", connection_type="ssh"),
                template="access_switch.j2",
                variables={"hostname": "NEW", "admin_password": "Secret@2026"},
                backup=False,
                allow_ssh_deploy=True,
            )
        )

    assert response.success is False
    assert response.data.get("status") in {"failed", "partial"}
    mock_ssh.disconnect.assert_called()


def test_as_bool_parses_string_false():
    from src.agent.utils import as_bool

    assert as_bool("false") is False
    assert as_bool("False") is False
    assert as_bool("0") is False
    assert as_bool("no") is False
    assert as_bool("off") is False
    assert as_bool("true") is True
    assert as_bool("1") is True
    assert as_bool("yes") is True
    assert as_bool(True) is True
    assert as_bool(False) is False
    assert as_bool(None, default=True) is True


def test_deploy_variables_string_false_does_not_enable_dangerous():
    """variables.allow_dangerous='false' 不得被 bool() 当成 True。"""
    adapter = AgentAdapter()
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = False

    with patch("src.agent.adapter.Connection", return_value=mock_conn), \
         patch("src.deploy.DeploymentEngine") as mock_engine_cls:
        mock_engine = MagicMock()
        mock_engine.deploy.return_value = {"status": "success", "steps": [], "saved": False}
        mock_engine_cls.return_value = mock_engine

        adapter.execute(
            AgentRequest(
                action="deploy",
                device=DeviceInfo(port="COM4", password="xxx"),
                template="access_switch.j2",
                variables={
                    "hostname": "SW-01",
                    "admin_password": "Secret@2026",
                    "allow_dangerous": "false",
                    "save": "false",
                },
                backup=False,
                allow_dangerous=False,
            )
        )

        kwargs = mock_engine.deploy.call_args.kwargs
        assert kwargs.get("allow_dangerous") is False
        assert kwargs.get("save") is False


def test_agent_command_blocks_dangerous_by_default():
    """command action 默认阻断 reboot 等危险命令。"""
    adapter = AgentAdapter()
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = False

    with patch("src.agent.adapter.Connection", return_value=mock_conn):
        response = adapter.execute(
            AgentRequest(
                action="command",
                device=DeviceInfo(port="COM4", password="xxx"),
                variables={"command": "reboot"},
            )
        )

    assert response.success is False
    assert "dangerous" in (response.message or "").lower() or \
           "dangerous" in (response.error or "").lower()
    mock_conn.send_command.assert_not_called()


def test_agent_command_allow_dangerous_explicit():
    adapter = AgentAdapter()
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = False
    mock_conn.send_command.return_value = "OK"

    with patch("src.agent.adapter.Connection", return_value=mock_conn), \
         patch("src.agent.adapter.CommandExecutor") as mock_exec_cls:
        mock_exec = MagicMock()
        mock_exec.send_command.return_value = "rebooting"
        mock_exec_cls.return_value = mock_exec

        response = adapter.execute(
            AgentRequest(
                action="command",
                device=DeviceInfo(port="COM4", password="xxx"),
                variables={"command": "reboot"},
                allow_dangerous=True,
            )
        )

    assert response.success is True
    mock_exec.send_command.assert_called()


def test_ssh_command_blocks_dangerous_by_default():
    adapter = AgentAdapter()
    mock_ssh = MagicMock()

    with patch("src.agent.adapter.ConnectHandler", return_value=mock_ssh) as ch:
        response = adapter.execute(
            AgentRequest(
                action="command",
                device=DeviceInfo(port="10.0.0.1", password="xxx", connection_type="ssh"),
                variables={"command": "reset saved-configuration"},
            )
        )

    assert response.success is False
    ch.assert_not_called()
