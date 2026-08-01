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
from src.deploy.rollback import RollbackManager
from src.deploy.planner import DeploymentPlanner

logger = get_logger("deploy")


def _normalize_config(text: str) -> list[str]:
    """配置规范化处理（用于幂等性比较）"""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            lines.append(stripped)
    return lines


class DeploymentEngine:
    """自动部署引擎。"""

    def __init__(self) -> None:
        self.renderer = TemplateRenderer()
        self.collector = None
        self.exporter = ConfigExporter()
        self.planner = DeploymentPlanner()

    def deploy(
        self,
        connection: Connection,
        template: str,
        variables: Dict[str, Any],
        backup: bool = True,
        device_name: str = "unknown",
        auto_rollback_on_failure: bool = True,
        dry_run: bool = False,
        dangerous_keywords: list[str] = None,
    ) -> Dict[str, Any]:
        """
        执行部署流程（支持幂等性和 Dry-Run）。

        核心行为：
        - 自动采集当前配置并与渲染后的目标配置进行比对
        - 若配置无差异 → 直接返回 status="skipped"，不执行任何命令
        - dry_run=True 时仅模拟，不下发配置
        - 支持失败自动回滚
        - 自动检测危险命令

        Args:
            connection: 已建立的 Connection 对象
            template: Jinja2 模板文件名
            variables: 模板变量
            backup: 是否在部署前备份当前配置
            device_name: 设备名称（用于备份目录）
            auto_rollback_on_failure: 失败时是否自动回滚
            dry_run: 是否仅模拟执行（不真正下发命令）
            dangerous_keywords: 自定义危险命令关键词列表

        Returns:
            dict: 包含 status、steps、reason、changes_detected 等信息的报告
        """
        if dangerous_keywords is None:
            dangerous_keywords = ["reboot", "reset", "delete", "format", "shutdown"]

        report: Dict[str, Any] = {"status": "success", "steps": []}
        backup_path = None
        current_config = None

        # 1. 备份 + 配置采集（即使不备份也尽量采集当前配置用于幂等性检查）
        self.collector = ConfigCollector(connection)
        try:
            current_config = self.collector.collect_current_config()
        except Exception as e:
            logger.warning(f"采集当前配置失败，跳过幂等性检查: {e}")
            current_config = None

        if backup:
            backup_path = self.exporter.export_backup(
                device_name, {"display current-configuration": current_config or ""}
            )
            report["backup_path"] = str(backup_path)
            report["steps"].append("backup")

        # 2. 渲染配置
        config_text = self.renderer.render(template, variables)
        report["steps"].append("render")

        # 安全检查：检测危险命令
        dangerous_commands = [line for line in config_text.splitlines() if any(kw in line.lower() for kw in dangerous_keywords)]
        if dangerous_commands:
            report["warnings"] = report.get("warnings", [])
            report["warnings"].append(f"检测到 {len(dangerous_commands)} 条潜在危险命令")
            logger.warning(f"检测到潜在危险命令: {dangerous_commands[:3]}")

        # 使用 planner 生成部署步骤
        deploy_steps = self.planner.plan(config_text)
        report["planned_steps_count"] = len(deploy_steps)

        # 3. 幂等性检查（核心改进）
        if current_config is not None:
            is_different, diff_summary = self._configs_differ(config_text, current_config)
            if not is_different:
                report["status"] = "skipped"
                report["reason"] = "no configuration changes detected"
                report["steps"].append("compare")
                logger.info("配置无差异，跳过部署（幂等性保护）")
                return report
            report["steps"].append("compare")
            report["changes_detected"] = True
            report["diff_summary"] = diff_summary
        else:
            report["changes_detected"] = "unknown (no current config for comparison)"

        # 4. Dry-run 模式：仅模拟，不下发
        if dry_run:
            report["status"] = "dry_run"
            report["reason"] = "dry_run=True, no commands were executed"
            report["steps"].append("dry_run")
            report["planned_steps_count"] = len(deploy_steps)

            # 在 dry_run 模式下也提供差异信息
            if current_config is not None:
                is_different, diff_summary = self._configs_differ(config_text, current_config)
                report["diff_summary"] = diff_summary
                report["changes_detected"] = is_different

            logger.info("[DryRun] 部署计划完成，未执行任何命令")
            return report

        # 5. 下发配置
        rollback_mgr = RollbackManager()
        deploy_failed = False

        # 使用 planner 生成部署步骤
        deploy_steps = self.planner.plan(config_text)

        for line in deploy_steps:
            try:
                connection.send_command(line)
            except (ConsoleDisconnect, ConsoleTimeout, AuthenticationError) as e:
                logger.error(f"部署命令执行失败（特定异常）: {line} -> {e}")
                report["status"] = "failed"
                report["error"] = str(e)
                deploy_failed = True
                break
            except Exception as e:
                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    raise
                logger.warning(f"部署命令执行失败（其他异常）: {line} -> {e}")
                report["status"] = "failed"
                report["error"] = str(e)
                deploy_failed = True
                break

        if deploy_failed:
            # 自动回滚
            if auto_rollback_on_failure and backup_path:
                logger.warning("部署失败，尝试自动回滚...")
                rollback_report = rollback_mgr.rollback(connection, str(backup_path))
                report["rollback"] = {
                    "attempted": True,
                    "success": rollback_report.success,
                    "success_count": rollback_report.success_count,
                    "failed_count": rollback_report.failed_count,
                }

                # 生成回滚计划建议
                try:
                    rollback_plan = self.planner.generate_rollback_plan(config_text)
                    report["rollback"]["suggested_undo_commands"] = rollback_plan[:5]  # 只显示前5条
                except Exception:
                    pass

                if rollback_report.success:
                    logger.info("自动回滚成功")
                else:
                    logger.error("自动回滚失败，请手动检查设备状态")
            else:
                report["rollback"] = {"attempted": False}

            return report

        report["steps"].append("deploy")
        logger.info("部署完成")
        if "diff_summary" in report:
            logger.info(f"部署差异摘要: {report['diff_summary']}")
        return report

    def _configs_differ(self, rendered: str, current: str) -> tuple[bool, str]:
        """
        配置差异检测（幂等性核心）。

        Returns:
            (is_different, diff_summary)
        """
        rendered_lines = _normalize_config(rendered)
        current_lines = _normalize_config(current)

        if rendered_lines == current_lines:
            return False, "配置一致"

        added = [line for line in rendered_lines if line not in current_lines]
        removed = [line for line in current_lines if line not in rendered_lines]

        summary_parts = []
        if added:
            sample = "; ".join(added[:2])
            if len(added) > 2:
                sample += f" ... (+{len(added)-2} more)"
            summary_parts.append(f"新增 {len(added)} 行 ({sample})")
        if removed:
            sample = "; ".join(removed[:2])
            if len(removed) > 2:
                sample += f" ... (+{len(removed)-2} more)"
            summary_parts.append(f"删除 {len(removed)} 行 ({sample})")

        diff_summary = " | ".join(summary_parts) if summary_parts else "存在差异"
        return True, diff_summary

