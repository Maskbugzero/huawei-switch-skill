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

from typing import Any, Dict, Optional

import paramiko
from netmiko import ConnectHandler

from src.console import Connection
from src.agent.error_codes import (
    APT001, APT002, CON001, CON003,
)
from src.agent.request import AgentRequest, AgentResponse
from src.console.logger import get_logger

logger = get_logger("agent")


class AgentAdapter:
    """
    Skill 统一调用入口。

    这是使用 huawei-switch-skill Skill 的推荐方式。
    所有操作都通过 AgentRequest / AgentResponse 进行标准化交互，
    便于上层 Agent 系统集成。

    支持的 action 及参数说明：
        backup:
            params: { port, password, device_name }
        deploy:
            params: { port, password, template, variables, device_name, backup_before_deploy }
        command:
            params: { port, password, command }
        validate:
            params: { port, password, config_path? }

    详细示例请参考：
        examples/03_using_agent_adapter.py
    """

    SUPPORTED_ACTIONS = {"deploy", "backup", "command", "validate"}

    def execute(self, request: AgentRequest) -> AgentResponse:
        """
        执行 Skill 请求（推荐调用方式）。

        使用上下文管理器确保连接始终关闭（修复资源泄漏）。
        支持所有 action，包括 validate。
        使用 request.device 统一处理连接信息（与 request.py / tests 一致）。

        Args:
            request: AgentRequest 对象（使用 DeviceInfo 而非旧 params 字典）

        Returns:
            AgentResponse: 标准化响应
        """
        if request.action not in self.SUPPORTED_ACTIONS:
            return AgentResponse(
                success=False,
                code=APT002.code,
                message=f"不支持的操作: {request.action}",
            )

        # 检测连接类型：SSH 或 Console
        is_ssh = request.device.is_ssh()

        # 基本参数校验（根据连接类型区分）
        if is_ssh:
            # SSH 模式：需要 password，host 或 port 至少有一个
            if not request.device.password.get_secret_value():
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
            # Console 模式：需要 port 和 password
            if not request.device.port or not request.device.password:
                return AgentResponse(
                    success=False,
                    code=APT001.code,
                    message="缺少必要的设备连接信息 (port/password)",
                )

        device_name = request.variables.get("device_name", "unknown")

        # validate 不需要真实连接，可提前处理
        if request.action == "validate":
            from pathlib import Path

            from src.verify import ConfigVerifier

            verifier = ConfigVerifier()

            before = request.variables.get("before_config", "")
            after = request.variables.get("after_config", "")
            expected = request.variables.get("expected", {})

            before_path = request.variables.get("before_config_path")
            after_path = request.variables.get("after_config_path")

            def _safe_read_config(path_str: str) -> str:
                """安全读取配置文件，防止路径遍历等安全问题。"""
                p = Path(path_str).resolve()
                # 限制只能读取当前工作目录下的文件，或 backups/ 目录下的文件
                cwd = Path.cwd().resolve()
                allowed_dirs = [cwd, cwd / "backups"]

                is_allowed = any(
                    str(p).startswith(str(d)) for d in allowed_dirs
                )

                if not p.exists() or not p.is_file():
                    raise FileNotFoundError(f"配置文件不存在或不是文件: {path_str}")
                if not is_allowed:
                    raise PermissionError(f"不允许访问该路径: {path_str}")

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

            return AgentResponse(success=True, data={"validation_report": report})

        # SSH 连接分支
        if is_ssh:
            return self._execute_via_ssh(request, device_name)

        # Console 连接分支
        try:
            # 使用上下文管理器确保自动 disconnect（即使异常也安全）
            with Connection(
                port=request.device.port,
                password=request.device.password.get_secret_value()
            ) as conn:
                if request.action == "backup":
                    from src.backup import ConfigCollector, ConfigExporter
                    collector = ConfigCollector(conn)
                    data = collector.collect_all()
                    exporter = ConfigExporter()
                    path = exporter.export_backup(device_name, data)
                    return AgentResponse(success=True, data={"backup_path": str(path)})

                elif request.action == "deploy":
                    from src.deploy import DeploymentEngine
                    engine = DeploymentEngine()
                    report = engine.deploy(
                        connection=conn,
                        template=request.template or "access_switch.j2",
                        variables=request.variables,
                        backup=request.backup,
                        device_name=device_name,
                        dry_run=request.dry_run,
                    )
                    return AgentResponse(success=True, data=report)

                elif request.action == "command":
                    output = conn.send_command(request.variables.get("command", ""))
                    return AgentResponse(success=True, data={"output": output})

                # 理论上不会到达这里
                return AgentResponse(success=True)

        except (ConsoleDisconnect, ConsoleTimeout, AuthenticationError) as e:
            logger.error(f"Agent 执行失败（连接异常）: {e}")
            return AgentResponse(
                success=False,
                code=CON003.code,
                message=str(e),
                error=str(e),
            )
        except Exception as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            logger.error(f"Agent 执行失败: {e}")
            return AgentResponse(
                success=False,
                code=CON003.code,
                message=str(e),
                error=str(e),
            )

    def _execute_via_ssh(self, request: AgentRequest, device_name: str) -> AgentResponse:
        """
        通过 SSH 执行 Skill 请求。

        支持的操作：
        - backup: 使用 netmiko 采集配置并备份
        - command: 直接执行单条命令
        - deploy: 简化支持（下发配置），完整 DeploymentEngine 需 Connection 对象
        - validate: 不应到达此分支（已在 execute 中提前处理）

        Args:
            request: AgentRequest 对象
            device_name: 设备名称

        Returns:
            AgentResponse: 标准化响应
        """

        host = request.device.host or request.device.port
        port = request.device.port_number
        username = request.device.username
        password = request.device.password.get_secret_value()

        logger.info(f"SSH 模式执行 action={request.action}，目标: {host}:{port}")

        ssh_device = {
            "device_type": "huawei_vrp",
            "host": host,
            "username": username,
            "password": password,
            "port": port,
            "conn_timeout": 30,      # 连接超时 30 秒
            "read_timeout": 30,      # 读取超时 30 秒
        }

        conn = None
        try:
            conn = ConnectHandler(**ssh_device)
            conn.send_command("screen-length 0 temporary")

            if request.action == "command":
                cmd = request.variables.get("command", "")
                if not cmd:
                    return AgentResponse(
                        success=False,
                        code=APT001.code,
                        message="SSH command action 缺少 command 参数",
                    )
                output = conn.send_command(cmd, read_timeout=30)
                conn.disconnect()
                return AgentResponse(success=True, data={"output": output, "transport": "ssh", "note": "SSH transport is experimental, Console mode is recommended for full features"})

            elif request.action == "backup":
                from src.backup import ConfigExporter

                config = conn.send_command("display current-configuration", read_timeout=120)
                exporter = ConfigExporter()
                path = exporter.export_backup(device_name, {"display current-configuration": config})
                conn.disconnect()
                return AgentResponse(
                    success=True,
                    data={"backup_path": str(path), "transport": "ssh", "note": "SSH transport is experimental, Console mode is recommended for full features"}
                )

            elif request.action == "deploy":
                # SSH deploy 的简化实现：直接下发 template 渲染后的配置
                # 完整功能（幂等性、Dry-Run、自动回滚）需使用 Console + DeploymentEngine
                from src.template import TemplateRenderer

                template_name = request.template or "access_switch.j2"
                renderer = TemplateRenderer()
                target_config = renderer.render(template_name, request.variables)

                # 1. 幂等性检查：采集当前配置并比对
                try:
                    current_config = conn.send_command("display current-configuration", read_timeout=120)
                except Exception as e:
                    logger.warning(f"SSH deploy 采集当前配置失败，跳过幂等性检查: {e}")
                    current_config = None
                    # 记录到响应中（通过后续构造的 response data）

                if current_config is not None:
                    # 简单的配置规范化比对
                    target_lines = [l.strip() for l in target_config.splitlines() if l.strip() and not l.strip().startswith("#")]
                    current_lines = [l.strip() for l in current_config.splitlines() if l.strip() and not l.strip().startswith("#")]

                    if target_lines == current_lines:
                        conn.disconnect()
                        return AgentResponse(
                            success=True,
                            data={
                                "status": "skipped",
                                "reason": "no configuration changes detected (idempotency check)",
                                "transport": "ssh",
                            },
                        )

                if request.dry_run:
                    conn.disconnect()
                    return AgentResponse(
                        success=True,
                        data={
                            "status": "dry_run",
                            "reason": "SSH deploy dry_run 模式，未下发配置",
                            "planned_config_length": len(target_config),
                            "transport": "ssh",
                        },
                    )

                # 2. 下发配置：逐行发送（不使用 DeploymentEngine 的 planner）
                lines = [l.strip() for l in target_config.splitlines() if l.strip() and not l.strip().startswith("#")]
                success_count = 0
                failed_lines = []
                for line in lines:
                    try:
                        conn.send_command(line, read_timeout=30)
                        success_count += 1
                    except Exception as e:
                        logger.warning(f"SSH deploy 命令执行失败: {line} -> {e}")
                        failed_lines.append(line)

                conn.disconnect()
                status = "success" if not failed_lines else "partial"
                return AgentResponse(
                    success=True,
                    data={
                        "status": status,
                        "deployed_lines": success_count,
                        "failed_lines": failed_lines,
                        "total_lines": len(lines),
                        "transport": "ssh",
                        "note": "SSH deploy 为简化实现，建议 Console 模式使用完整 DeploymentEngine（支持 planner、自动回滚）",
                    },
                )

            else:
                if conn:
                    conn.disconnect()
                return AgentResponse(
                    success=False,
                    code=APT002.code,
                    message=f"SSH 模式不支持的操作: {request.action}",
                )

        except paramiko.AuthenticationException as e:
            if conn:
                conn.disconnect()
            logger.error(f"SSH 认证失败: {e}")
            return AgentResponse(
                success=False,
                code=CON003.code,
                message=f"SSH 认证失败: {e}",
                error=str(e),
            )
        except Exception as e:
            if conn:
                try:
                    conn.disconnect()
                except Exception as disconnect_err:
                    logger.warning(f"SSH 连接关闭异常: {disconnect_err}")
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            logger.error(f"SSH 执行失败: {e}")
            return AgentResponse(
                success=False,
                code=CON003.code,
                message=str(e),
                error=str(e),
            )

