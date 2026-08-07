# -*- coding: utf-8 -*-
"""
Skill 统一调用入口（AgentAdapter）

本模块提供 huawei-switch-skill Skill 的推荐调用方式。
上层系统（Claude Code、Hermes、自定义 Agent 等）应优先通过
AgentAdapter.execute() 来使用本 Skill 的各项能力。

支持的操作（action）：
    - backup   : 配置备份
    - deploy   : 模板化部署
    - command  : 单条命令执行
    - validate : 配置校验

示例用法见 examples/03_using_agent_adapter.py
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import paramiko
from jinja2 import TemplateNotFound, UndefinedError
from netmiko import ConnectHandler

from src.console import (
    Connection,
    ConsoleDisconnect,
    ConsoleTimeout,
    AuthenticationError,
)
from src.agent.error_codes import (
    APT001,
    APT002,
    CMD001,
    CON003,
    CON004,
    DEP001,
    TPL001,
    TPL002,
    VAL001,
)
from src.agent.request import AgentRequest, AgentResponse
from src.agent.utils import as_bool
from src.console.logger import get_logger
from src.command import CommandExecutor, ErrorDetector
from src.command.exceptions import CommandExecutionError
from src.deploy.deployer import (
    DEFAULT_DANGEROUS_KEYWORDS,
    _line_is_dangerous,
    configs_intent_differs,
)
from src.deploy.planner import DeploymentPlanner
from src.template import TemplateRenderer

logger = get_logger("agent")

_SUCCESS_STATUSES = frozenset({"success", "skipped", "dry_run"})


def _resolve_allow_dangerous(request: AgentRequest) -> bool:
    if request.allow_dangerous:
        return True
    return as_bool(request.variables.get("allow_dangerous", False), default=False)


def _resolve_save(request: AgentRequest) -> bool:
    if "save" in request.variables:
        return as_bool(request.variables.get("save"), default=request.save)
    return request.save


def _resolve_verify(request: AgentRequest) -> bool:
    if "verify" in request.variables:
        return as_bool(request.variables.get("verify"), default=request.verify)
    return request.verify


def _resolve_auto_rollback(request: AgentRequest) -> bool:
    if request.auto_rollback_on_failure:
        return True
    return as_bool(
        request.variables.get("auto_rollback_on_failure", False), default=False
    )


def _blocked_dangerous_response(cmd: str) -> AgentResponse:
    return AgentResponse(
        success=False,
        code=DEP001.code,
        message=(
            "dangerous command blocked; pass allow_dangerous=True to override"
        ),
        error="dangerous command blocked",
        data={
            "status": "blocked",
            "command": cmd,
            "reason": "dangerous command blocked",
        },
    )


def _map_exception_code(exc: BaseException) -> str:
    """将异常映射到统一错误码。"""
    if isinstance(exc, AuthenticationError):
        return CON003.code
    if isinstance(exc, (ConsoleDisconnect, ConsoleTimeout)):
        return CON004.code
    if isinstance(exc, paramiko.AuthenticationException):
        return CON003.code
    if isinstance(exc, CommandExecutionError):
        return CMD001.code
    if isinstance(exc, TemplateNotFound):
        return TPL001.code
    if isinstance(exc, UndefinedError):
        return TPL002.code
    if isinstance(exc, (PermissionError, FileNotFoundError, ValueError)):
        return APT001.code
    return DEP001.code


def _response_from_deploy_report(report: Dict[str, Any]) -> AgentResponse:
    status = report.get("status")
    ok = status in _SUCCESS_STATUSES
    code = None
    if not ok:
        if status == "blocked":
            code = DEP001.code
        else:
            code = DEP001.code
    return AgentResponse(
        success=ok,
        code=code,
        data=report,
        message=report.get("reason") or report.get("error") or "",
        error=None if ok else (report.get("error") or report.get("reason")),
    )


class AgentAdapter:
    """
    Skill 统一调用入口。

    这是使用 huawei-switch-skill Skill 的推荐方式。
    所有操作都通过 AgentRequest / AgentResponse 进行标准化交互，
    便于上层 Agent 系统集成。
    """

    SUPPORTED_ACTIONS = {"deploy", "backup", "command", "validate"}

    def execute(self, request: AgentRequest) -> AgentResponse:
        """
        执行 Skill 请求（推荐调用方式）。

        使用上下文管理器确保连接始终关闭（修复资源泄漏）。
        """
        if request.action not in self.SUPPORTED_ACTIONS:
            return AgentResponse(
                success=False,
                code=APT002.code,
                message=f"不支持的操作: {request.action}",
            )

        is_ssh = request.device.is_ssh()
        password_value = request.device.password.get_secret_value()

        if is_ssh:
            if not password_value:
                return AgentResponse(
                    success=False,
                    code=APT001.code,
                    message="缺少必要的设备连接信息 (password)",
                )
            if not (request.device.host or request.device.port):
                return AgentResponse(
                    success=False,
                    code=APT001.code,
                    message="SSH 模式需要 host 或 port",
                )
        else:
            if not request.device.port or not password_value:
                return AgentResponse(
                    success=False,
                    code=APT001.code,
                    message="缺少必要的设备连接信息 (port/password)",
                )

        device_name = request.variables.get("device_name", "unknown")

        if request.action == "validate":
            return self._execute_validate(request)

        if is_ssh:
            return self._execute_via_ssh(request, device_name)

        try:
            with Connection(
                port=request.device.port,
                password=password_value,
            ) as conn:
                if request.action == "backup":
                    from src.backup import ConfigCollector, ConfigExporter

                    collector = ConfigCollector(conn)
                    data = collector.collect_all()
                    exporter = ConfigExporter()
                    path = exporter.export_backup(device_name, data)
                    return AgentResponse(success=True, data={"backup_path": str(path)})

                if request.action == "deploy":
                    from src.deploy import DeploymentEngine

                    allow_dangerous = _resolve_allow_dangerous(request)
                    auto_rollback = _resolve_auto_rollback(request)
                    save = _resolve_save(request)
                    verify = _resolve_verify(request)
                    engine = DeploymentEngine()
                    report = engine.deploy(
                        connection=conn,
                        template=request.template or "access_switch.j2",
                        variables=request.variables,
                        backup=request.backup,
                        device_name=device_name,
                        dry_run=request.dry_run,
                        allow_dangerous=allow_dangerous,
                        auto_rollback_on_failure=auto_rollback,
                        save=save,
                        verify=verify,
                    )
                    return _response_from_deploy_report(report)

                if request.action == "command":
                    cmd = request.variables.get("command", "")
                    if not cmd:
                        return AgentResponse(
                            success=False,
                            code=APT001.code,
                            message="command action 缺少 command 参数",
                        )
                    if (
                        _line_is_dangerous(str(cmd), DEFAULT_DANGEROUS_KEYWORDS)
                        and not _resolve_allow_dangerous(request)
                    ):
                        return _blocked_dangerous_response(str(cmd))
                    executor = CommandExecutor(conn)
                    output = executor.send_command(cmd)
                    return AgentResponse(success=True, data={"output": output})

                return AgentResponse(success=True)

        except (ConsoleDisconnect, ConsoleTimeout, AuthenticationError) as e:
            logger.error(f"Agent 执行失败（连接异常）: {e}")
            return AgentResponse(
                success=False,
                code=_map_exception_code(e),
                message=str(e),
                error=str(e),
            )
        except CommandExecutionError as e:
            logger.error(f"Agent 命令执行失败: {e}")
            return AgentResponse(
                success=False,
                code=CMD001.code,
                message=str(e),
                error=str(e),
            )
        except (TemplateNotFound, UndefinedError) as e:
            logger.error(f"Agent 模板错误: {e}")
            return AgentResponse(
                success=False,
                code=_map_exception_code(e),
                message=str(e),
                error=str(e),
            )
        except Exception as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            logger.error(f"Agent 执行失败: {e}")
            return AgentResponse(
                success=False,
                code=_map_exception_code(e),
                message=str(e),
                error=str(e),
            )

    def _execute_validate(self, request: AgentRequest) -> AgentResponse:
        from pathlib import Path

        from src.verify import ConfigVerifier

        verifier = ConfigVerifier()
        before = request.variables.get("before_config", "")
        after = request.variables.get("after_config", "")
        expected = request.variables.get("expected", {})
        before_path = request.variables.get("before_config_path")
        after_path = request.variables.get("after_config_path")

        def _safe_read_config(path_str: str) -> str:
            p = Path(path_str).expanduser().resolve(strict=False)
            cwd = Path.cwd().resolve()
            allowed_roots = [cwd, (cwd / "backups").resolve()]

            def _is_relative_to(path: Path, root: Path) -> bool:
                try:
                    path.relative_to(root)
                    return True
                except ValueError:
                    return False

            if not any(_is_relative_to(p, root) for root in allowed_roots):
                raise PermissionError(f"不允许访问该路径: {path_str}")
            if not p.exists() or not p.is_file():
                raise FileNotFoundError(f"配置文件不存在或不是文件: {path_str}")

            with open(p, "r", encoding="utf-8") as f:
                return f.read()

        try:
            if before_path:
                before = _safe_read_config(before_path)
            if after_path:
                after = _safe_read_config(after_path)
        except Exception as e:
            return AgentResponse(
                success=False,
                code=APT001.code,
                message=f"配置文件读取失败: {e}",
            )

        if before or after:
            report = verifier.verify(before, after, expected)
        else:
            report = {"status": "skipped", "reason": "no config provided for validation"}

        ok = report.get("status") != "fail"
        return AgentResponse(
            success=ok,
            code=None if ok else VAL001.code,
            data={"validation_report": report},
            message="" if ok else "validation failed",
            error=None if ok else "validation failed",
        )

    def _execute_via_ssh(self, request: AgentRequest, device_name: str) -> AgentResponse:
        """
        通过 SSH 执行 Skill 请求。

        deploy 路径对齐 Console 安全默认：
        - 危险命令默认 blocked
        - 意图子集幂等
        - 输出 Error 检测
        - 连接始终在 finally 中关闭
        """
        host = request.device.host or request.device.port
        port = request.device.port_number
        username = request.device.username
        password = request.device.password.get_secret_value()

        # command：连接前校验参数与危险命令（避免无谓登录）
        if request.action == "command":
            cmd = str(request.variables.get("command", "") or "").strip()
            if not cmd:
                return AgentResponse(
                    success=False,
                    code=APT001.code,
                    message="SSH command action 缺少 command 参数",
                )
            if (
                _line_is_dangerous(cmd, DEFAULT_DANGEROUS_KEYWORDS)
                and not _resolve_allow_dangerous(request)
            ):
                return _blocked_dangerous_response(cmd)

        logger.info(f"SSH 模式执行 action={request.action}，目标: {host}:{port}")

        # netmiko 4.x：ConnectHandler 无 read_timeout 参数；读超时在 send_command 上传
        ssh_device = {
            "device_type": "huawei_vrp",
            "host": host,
            "username": username,
            "password": password,
            "port": port,
            "conn_timeout": 30,
        }

        conn = None
        try:
            conn = ConnectHandler(**ssh_device)
            conn.send_command("screen-length 0 temporary")

            if request.action == "command":
                cmd = str(request.variables.get("command", "") or "").strip()
                output = conn.send_command(cmd, read_timeout=30)
                detector = ErrorDetector()
                err = detector.detect(output or "")
                if err:
                    return AgentResponse(
                        success=False,
                        code=CMD001.code,
                        message=err,
                        error=err,
                        data={"output": output, "transport": "ssh"},
                    )
                return AgentResponse(
                    success=True,
                    data={
                        "output": output,
                        "transport": "ssh",
                        "note": "SSH transport is experimental for full deploy features",
                    },
                )

            if request.action == "backup":
                from src.backup import ConfigExporter

                config = conn.send_command(
                    "display current-configuration", read_timeout=120
                )
                exporter = ConfigExporter()
                path = exporter.export_backup(
                    device_name, {"display current-configuration": config}
                )
                return AgentResponse(
                    success=True,
                    data={
                        "backup_path": str(path),
                        "transport": "ssh",
                        "note": "SSH transport is experimental for full deploy features",
                    },
                )

            if request.action == "deploy":
                return self._ssh_deploy(conn, request)

            return AgentResponse(
                success=False,
                code=APT002.code,
                message=f"SSH 模式不支持的操作: {request.action}",
            )

        except paramiko.AuthenticationException as e:
            logger.error(f"SSH 认证失败: {e}")
            return AgentResponse(
                success=False,
                code=CON003.code,
                message=f"SSH 认证失败: {e}",
                error=str(e),
            )
        except (TemplateNotFound, UndefinedError) as e:
            logger.error(f"SSH 模板错误: {e}")
            return AgentResponse(
                success=False,
                code=_map_exception_code(e),
                message=str(e),
                error=str(e),
            )
        except Exception as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            logger.error(f"SSH 执行失败: {e}")
            return AgentResponse(
                success=False,
                code=_map_exception_code(e),
                message=str(e),
                error=str(e),
            )
        finally:
            if conn is not None:
                try:
                    conn.disconnect()
                except Exception as disconnect_err:
                    logger.warning(f"SSH 连接关闭异常: {disconnect_err}")

    def _ssh_deploy(self, conn: Any, request: AgentRequest) -> AgentResponse:
        """SSH deploy：对齐 Console 的 blocked / 子集幂等 / Error 检测。"""
        template_name = request.template or "access_switch.j2"
        renderer = TemplateRenderer()
        target_config = renderer.render(template_name, request.variables)

        allow_dangerous = _resolve_allow_dangerous(request)

        # 危险命令默认阻断
        dangerous_commands = [
            line.strip()
            for line in target_config.splitlines()
            if _line_is_dangerous(line, DEFAULT_DANGEROUS_KEYWORDS)
        ]
        if dangerous_commands and not allow_dangerous:
            return _response_from_deploy_report(
                {
                    "status": "blocked",
                    "reason": (
                        "dangerous commands detected; pass allow_dangerous=True to override"
                    ),
                    "dangerous_commands": dangerous_commands[:20],
                    "transport": "ssh",
                }
            )

        # 采集当前配置 + 意图子集匹配
        current_config: Optional[str] = None
        try:
            current_config = conn.send_command(
                "display current-configuration", read_timeout=120
            )
        except Exception as e:
            logger.warning(f"SSH deploy 采集当前配置失败，跳过幂等性检查: {e}")

        if current_config is not None:
            is_different, diff_summary = configs_intent_differs(
                target_config, current_config
            )
            if not is_different:
                return _response_from_deploy_report(
                    {
                        "status": "skipped",
                        "reason": (
                            "target intent already satisfied "
                            "(interface-aware intent match)"
                        ),
                        "diff_summary": diff_summary,
                        "transport": "ssh",
                    }
                )

        if request.dry_run:
            return _response_from_deploy_report(
                {
                    "status": "dry_run",
                    "reason": "SSH deploy dry_run 模式，未下发配置",
                    "planned_config_length": len(target_config),
                    "transport": "ssh",
                }
            )

        lines = DeploymentPlanner().plan(target_config)
        detector = ErrorDetector()
        success_count = 0
        failed_lines: List[str] = []
        errors: List[str] = []

        for line in lines:
            try:
                output = conn.send_command(line, read_timeout=30)
                err = detector.detect(output or "")
                if err:
                    logger.warning(f"SSH deploy 设备报错: {line} -> {err}")
                    failed_lines.append(line)
                    errors.append(err)
                    break
                success_count += 1
            except Exception as e:
                logger.warning(f"SSH deploy 命令执行失败: {line} -> {e}")
                failed_lines.append(line)
                errors.append(str(e))
                break

        if failed_lines:
            return _response_from_deploy_report(
                {
                    "status": "failed",
                    "error": errors[0] if errors else "command failed",
                    "deployed_lines": success_count,
                    "failed_lines": failed_lines,
                    "total_lines": len(lines),
                    "transport": "ssh",
                    "note": "SSH deploy uses ErrorDetector; full planner/rollback via Console",
                }
            )

        # 成功后默认 save（与 Console 对齐）
        do_save = _resolve_save(request)
        if do_save and not request.dry_run:
            try:
                # netmiko 下 save 确认因平台而异；尽力发送
                conn.send_command_timing("save")
                try:
                    conn.send_command_timing("Y")
                except Exception:
                    pass
                saved = True
            except Exception as e:
                logger.warning(f"SSH deploy save failed: {e}")
                return _response_from_deploy_report(
                    {
                        "status": "failed",
                        "error": f"deploy succeeded but save failed: {e}",
                        "deployed_lines": success_count,
                        "total_lines": len(lines),
                        "saved": False,
                        "transport": "ssh",
                    }
                )
        else:
            saved = False

        return _response_from_deploy_report(
            {
                "status": "success",
                "deployed_lines": success_count,
                "total_lines": len(lines),
                "saved": saved if do_save else False,
                "transport": "ssh",
                "note": "SSH deploy simplified path; Console DeploymentEngine recommended for rollback",
            }
        )
