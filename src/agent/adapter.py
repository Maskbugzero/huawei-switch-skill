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

        # 基本参数校验
        if not request.device or not request.device.port or not request.device.password:
            return AgentResponse(
                success=False,
                code=APT001.code,
                message="缺少必要的设备连接信息 (port/password)",
            )

        device_name = request.variables.get("device_name", "unknown")

        # validate 不需要真实连接，可提前处理
        if request.action == "validate":
            from src.verify import ConfigVerifier
            verifier = ConfigVerifier()

            before = request.variables.get("before_config", "")
            after = request.variables.get("after_config", "")
            expected = request.variables.get("expected", {})

            before_path = request.variables.get("before_config_path")
            after_path = request.variables.get("after_config_path")

            if before_path:
                with open(before_path, "r", encoding="utf-8") as f:
                    before = f.read()
            if after_path:
                with open(after_path, "r", encoding="utf-8") as f:
                    after = f.read()

            if before or after:
                report = verifier.verify(before, after, expected)
            else:
                report = {"status": "skipped", "reason": "no config provided for validation"}

            return AgentResponse(success=True, data={"validation_report": report})

        try:
            # 使用上下文管理器确保自动 disconnect（即使异常也安全）
            with Connection(
                port=request.device.port,
                password=request.device.password
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
                    )
                    return AgentResponse(success=True, data=report)

                elif request.action == "command":
                    output = conn.send_command(request.variables.get("command", ""))
                    return AgentResponse(success=True, data={"output": output})

                # 理论上不会到达这里
                return AgentResponse(success=True)

        except Exception as e:
            logger.error(f"Agent 执行失败: {e}")
            return AgentResponse(
                success=False,
                code=CON003.code,
                message=str(e),
                error=str(e),
            )
