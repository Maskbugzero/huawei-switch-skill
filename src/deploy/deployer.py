# -*- coding: utf-8 -*-
"""
部署引擎 - Deployer。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.console import Connection
from src.console.exceptions import ConsoleDisconnect, ConsoleTimeout, AuthenticationError
from src.console.logger import get_logger
from src.template import TemplateRenderer
from src.backup import ConfigCollector, ConfigExporter

logger = get_logger("deploy")


class DeploymentEngine:
    """自动部署引擎。"""

    def __init__(self) -> None:
        self.renderer = TemplateRenderer()
        self.collector = None
        self.exporter = ConfigExporter()

    def deploy(
        self,
        connection: Connection,
        template: str,
        variables: Dict[str, Any],
        backup: bool = True,
        device_name: str = "unknown",
    ) -> Dict[str, Any]:
        """执行部署流程。"""
        report = {"status": "success", "steps": []}

        # 1. 备份（可选）
        if backup:
            self.collector = ConfigCollector(connection)
            old_config = self.collector.collect_current_config()
            backup_path = self.exporter.export_backup(
                device_name, {"display current-configuration": old_config}
            )
            report["backup_path"] = str(backup_path)
            report["steps"].append("backup")

        # 2. 渲染配置
        config_text = self.renderer.render(template, variables)
        report["steps"].append("render")

        # 3. 下发配置（简化版：逐行执行）
        for line in config_text.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                try:
                    connection.send_command(line)
                except (ConsoleDisconnect, ConsoleTimeout, AuthenticationError) as e:
                    logger.error(f"部署命令执行失败（特定异常）: {line} -> {e}")
                    report["status"] = "failed"
                    report["error"] = str(e)
                    return report
                except Exception as e:
                    logger.warning(f"部署命令执行失败（其他异常）: {line} -> {e}")
                    report["status"] = "failed"
                    report["error"] = str(e)
                    return report

        report["steps"].append("deploy")
        logger.info("部署完成")
        return report
