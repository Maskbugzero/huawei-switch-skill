# -*- coding: utf-8 -*-
"""
部署引擎 - Deployer。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from src.console import Connection
from src.console.exceptions import ConsoleDisconnect, ConsoleTimeout, AuthenticationError
from src.console.logger import get_logger
from src.template import TemplateRenderer
from src.backup import ConfigCollector, ConfigExporter
from src.deploy.rollback import RollbackManager
from src.deploy.planner import DeploymentPlanner
from src.deploy.port_guard import check_uplink_protection
from src.command.executor import CommandExecutor
from src.command.exceptions import CommandExecutionError
from src.verify import ConfigVerifier
from src.verify.rules import build_expected_from_variables
from src.agent.utils import as_bool

logger = get_logger("deploy")

DEFAULT_DANGEROUS_KEYWORDS = [
    "reboot",
    "reset",
    "delete",
    "format",
    "shutdown",
]

# 退出 interface 视图的命令（VRP）
_EXIT_INTERFACE_VIEWS = frozenset(
    {
        "quit",
        "return",
        "system-view",
    }
)


def _normalize_config(text: str) -> list[str]:
    """配置规范化处理（用于幂等性比较）"""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            # description 中的 ## 不能当注释截断
            if stripped.lower().startswith("description"):
                lines.append(stripped)
                continue
            # 去掉行尾单 # 注释；保留 ##
            if " #" in stripped:
                head, tail = stripped.split(" #", 1)
                if not tail.startswith("#"):
                    stripped = head.rstrip()
            lines.append(stripped)
    return lines


def _normalize_if_name(name: str) -> str:
    """接口名规范化，便于匹配。"""
    return re.sub(r"\s+", "", name.strip().lower())


def _is_secret_config_line(line: str) -> bool:
    """
    判断是否为密钥/口令类配置行。

    幂等比较时应忽略：设备 display 多为密文或 ******，与模板明文永不相等。
    """
    low = line.strip().lower()
    if not low:
        return False
    # 常见 VRP 密钥形态
    markers = (
        "password",
        "irreversible-cipher",
        "pre-shared-key",
        "authentication-key",
        "private-key",
        "server-key",
        "shared-key",
    )
    if any(m in low for m in markers):
        return True
    # snmp-agent community ... cipher <secret>
    if re.search(r"\bcipher\s+\S+", low):
        return True
    # 独立 secret <value>
    if re.search(r"\bsecret\s+\S+", low):
        return True
    return False


def _filter_secret_lines(lines: List[str]) -> List[str]:
    return [ln for ln in lines if not _is_secret_config_line(ln)]


def _parse_config_sections(
    text: str,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    将配置拆成全局行 + interface 块。

    新 interface 行自动结束上一个 interface 上下文（符合 VRP 行为）。
    quit / return / system-view 结束 interface 上下文。
    """
    global_lines: List[str] = []
    interfaces: Dict[str, List[str]] = {}
    current_if: Optional[str] = None

    for raw in _normalize_config(text):
        lower = raw.lower()
        if lower.startswith("interface ") or lower == "interface":
            # interface Name
            parts = raw.split(None, 1)
            if_name = parts[1].strip() if len(parts) > 1 else ""
            key = _normalize_if_name(if_name) if if_name else ""
            current_if = key or None
            if current_if is not None and current_if not in interfaces:
                interfaces[current_if] = []
            continue

        if lower in _EXIT_INTERFACE_VIEWS or lower.startswith("return "):
            current_if = None
            # system-view / return 本身记入全局（意图比较时 system-view 可忽略）
            if lower not in {"quit"}:
                if lower not in {"return"} and not lower.startswith("return "):
                    global_lines.append(raw)
            continue

        if current_if is not None:
            interfaces[current_if].append(raw)
        else:
            global_lines.append(raw)

    return global_lines, interfaces


def _line_is_dangerous(line: str, keywords: List[str]) -> bool:
    """
    判断单行是否包含危险命令。

    注意：`undo shutdown`（启用接口）不算危险；裸 `shutdown` 算。
    """
    lower = line.strip().lower()
    if not lower:
        return False
    for kw in keywords:
        kw_l = kw.lower().strip()
        if not kw_l:
            continue
        if kw_l == "shutdown":
            # 仅裸 shutdown / shutdown xxx；排除 undo shutdown
            if lower == "shutdown" or lower.startswith("shutdown "):
                return True
            continue
        if re.search(rf"\b{re.escape(kw_l)}\b", lower):
            return True
    return False


def configs_intent_differs(rendered: str, current: str) -> Tuple[bool, str]:
    """
    配置意图差异检测（interface 感知）。

    - 目标中的每个 interface 块：当前必须存在同名接口，且块内每行 ⊆ 该接口块
    - 目标全局行：须出现在当前全局行中（不把其它接口下的行算作全局满足）
    - 忽略纯 system-view / return 噪声
    - **忽略密钥/口令行**（password / cipher 等），避免密文导致永不 skip

    Returns:
        (is_different, diff_summary)
    """
    t_global, t_ifs = _parse_config_sections(rendered)
    c_global, c_ifs = _parse_config_sections(current)

    def _ignore_global(line: str) -> bool:
        low = line.lower()
        return low in {"system-view", "return"} or low.startswith("return ")

    missing: List[str] = []

    c_global_set = {
        g
        for g in _filter_secret_lines(c_global)
        if not _ignore_global(g)
    }
    for line in _filter_secret_lines(t_global):
        if _ignore_global(line):
            continue
        if line not in c_global_set:
            missing.append(line)

    for if_name, body in t_ifs.items():
        t_body = _filter_secret_lines(body)
        if if_name not in c_ifs:
            missing.append(f"interface {if_name}")
            for line in t_body:
                missing.append(f"  [{if_name}] {line}")
            continue
        c_body = set(_filter_secret_lines(c_ifs[if_name]))
        for line in t_body:
            if line not in c_body:
                missing.append(f"[{if_name}] {line}")

    if not missing:
        return False, "目标配置意图已满足（interface 感知子集匹配）"

    sample = "; ".join(missing[:2])
    if len(missing) > 2:
        sample += f" ... (+{len(missing)-2} more)"
    return True, f"缺少 {len(missing)} 项目标配置 ({sample})"


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
        auto_rollback_on_failure: bool = False,
        dry_run: bool = False,
        dangerous_keywords: Optional[list[str]] = None,
        allow_dangerous: bool = False,
        save: bool = True,
        verify: bool = True,
        allow_uplink_change: bool = False,
    ) -> Dict[str, Any]:
        """
        执行部署流程（支持幂等性和 Dry-Run）。

        核心行为：
        - 采集当前配置，用「interface 感知意图子集匹配」判断是否需要下发
        - dry_run=True 时仅模拟，不下发配置
        - 危险命令默认阻断（allow_dangerous=True 才放行）
        - 上联/保护口默认阻断（allow_uplink_change=True 才放行）
        - 自动回滚默认关闭（running-config 逐行重放不安全）
        - 通过 CommandExecutor 下发，带错误检测
        - 成功后默认 save=True 落盘
        - 成功后默认 verify=True 浅层校验（sysname/vlan/ssh）
        """
        if dangerous_keywords is None:
            dangerous_keywords = list(DEFAULT_DANGEROUS_KEYWORDS)

        # variables 也可覆盖 allow_uplink_change（字符串布尔安全解析）
        if not allow_uplink_change:
            allow_uplink_change = as_bool(
                (variables or {}).get("allow_uplink_change", False), default=False
            )

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
            report["idempotency_check_skipped"] = True
            report["warnings"] = report.get("warnings", [])
            report["warnings"].append("当前配置采集失败，幂等性检查已跳过")

        if backup:
            if current_config and str(current_config).strip():
                try:
                    backup_path = self.exporter.export_backup(
                        device_name,
                        {"display current-configuration": current_config},
                    )
                    report["backup_path"] = str(backup_path)
                    report["steps"].append("backup")
                except ValueError as e:
                    # device_name 非法等
                    logger.error(f"备份失败: {e}")
                    report["warnings"] = report.get("warnings", [])
                    report["warnings"].append(f"备份失败: {e}")
                    report["backup_skipped"] = True
            else:
                report["backup_skipped"] = True
                report["warnings"] = report.get("warnings", [])
                report["warnings"].append(
                    "backup skipped: empty or missing current configuration"
                )
                logger.warning("跳过备份：当前配置为空或采集失败")

        # 2. 渲染配置
        config_text = self.renderer.render(template, variables)
        report["steps"].append("render")

        # 2b. 上联/保护口检查（在危险命令检查之前，尽早失败）
        uplink_ok, uplink_reason, uplink_details = check_uplink_protection(
            config_text,
            variables=variables,
            current_config=current_config,
            allow_uplink_change=allow_uplink_change,
        )
        report["uplink_guard"] = uplink_details
        if not uplink_ok:
            report["status"] = "blocked"
            report["reason"] = uplink_reason
            report["steps"].append("uplink_guard")
            logger.warning(f"上联保护阻断: {uplink_reason}")
            return report

        # 安全检查：检测危险命令（默认阻断）
        dangerous_commands = [
            line.strip()
            for line in config_text.splitlines()
            if _line_is_dangerous(line, dangerous_keywords)
        ]
        if dangerous_commands:
            report["dangerous_commands"] = dangerous_commands[:20]
            report["warnings"] = report.get("warnings", [])
            report["warnings"].append(f"检测到 {len(dangerous_commands)} 条潜在危险命令")
            logger.warning(f"检测到潜在危险命令: {dangerous_commands[:3]}")
            if not allow_dangerous:
                report["status"] = "blocked"
                report["reason"] = (
                    "dangerous commands detected; pass allow_dangerous=True to override"
                )
                report["steps"].append("safety_check")
                return report

        # 使用 planner 生成部署步骤
        deploy_steps = self.planner.plan(config_text)
        report["planned_steps_count"] = len(deploy_steps)

        # 3. 幂等性检查（interface 感知意图子集匹配）
        if current_config is not None:
            is_different, diff_summary = self._configs_differ(config_text, current_config)
            if not is_different:
                report["status"] = "skipped"
                report["reason"] = (
                    "no configuration changes detected (interface-aware intent match)"
                )
                report["steps"].append("compare")
                logger.info("目标配置意图已满足，跳过部署（幂等性保护）")
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
            report["saved"] = False

            if current_config is not None:
                is_different, diff_summary = self._configs_differ(
                    config_text, current_config
                )
                report["diff_summary"] = diff_summary
                report["changes_detected"] = is_different

            logger.info("[DryRun] 部署计划完成，未执行任何命令")
            return report

        # 5. 下发配置（经 CommandExecutor，带错误检测）
        rollback_mgr = RollbackManager()
        deploy_failed = False
        executor = CommandExecutor(connection)

        deploy_steps = self.planner.plan(config_text)

        for line in deploy_steps:
            try:
                executor.send_command(line)
            except (ConsoleDisconnect, ConsoleTimeout, AuthenticationError) as e:
                logger.error(f"部署命令执行失败（连接异常）: {line} -> {e}")
                report["status"] = "failed"
                report["error"] = str(e)
                deploy_failed = True
                break
            except CommandExecutionError as e:
                logger.error(f"部署命令执行失败（设备报错）: {line} -> {e}")
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
            report["saved"] = False
            # 自动回滚（默认关闭；开启时仍属实验性）
            if auto_rollback_on_failure and backup_path:
                logger.warning(
                    "部署失败，尝试自动回滚（实验性：逐行重放备份，可能不完整）..."
                )
                rollback_report = rollback_mgr.rollback(connection, str(backup_path))
                report["rollback"] = {
                    "attempted": True,
                    "success": rollback_report.success,
                    "success_count": rollback_report.success_count,
                    "failed_count": rollback_report.failed_count,
                    "experimental": True,
                    "note": "running-config line replay is best-effort only",
                }

                try:
                    rollback_plan = self.planner.generate_rollback_plan(config_text)
                    report["rollback"]["suggested_undo_commands"] = rollback_plan[:5]
                except Exception:
                    pass

                if rollback_report.success:
                    logger.info("自动回滚成功")
                else:
                    logger.error("自动回滚失败，请手动检查设备状态")
            else:
                report["rollback"] = {
                    "attempted": False,
                    "note": "auto_rollback_on_failure is False by default",
                }
                if backup_path:
                    try:
                        rollback_plan = self.planner.generate_rollback_plan(config_text)
                        report["rollback"]["suggested_undo_commands"] = rollback_plan[:5]
                    except Exception:
                        pass

            return report

        report["steps"].append("deploy")

        # 6. 成功后默认 save
        if save:
            try:
                executor.send_command("save")
                report["saved"] = True
                report["steps"].append("save")
                logger.info("配置已 save")
            except Exception as e:
                logger.error(f"部署成功但 save 失败: {e}")
                report["status"] = "failed"
                report["error"] = f"deploy succeeded but save failed: {e}"
                report["saved"] = False
                return report
        else:
            report["saved"] = False

        # 7. 浅层校验闭环（sysname / vlan / ssh）
        if verify:
            try:
                after_config = self.collector.collect_current_config()
                expected = build_expected_from_variables(variables)
                vreport = ConfigVerifier().verify(
                    before_config=current_config or "",
                    after_config=after_config or "",
                    expected=expected,
                )
                report["verification"] = vreport
                report["steps"].append("verify")
                if vreport.get("status") == "fail":
                    report["status"] = "verify_failed"
                    report["error"] = "post-deploy verification failed"
                    report["reason"] = vreport.get("status")
                    logger.error("部署后校验失败: %s", vreport)
                    return report
                logger.info("部署后校验通过: %s", vreport.get("status"))
            except Exception as e:
                logger.warning(f"部署后校验异常（不阻断 success）: {e}")
                report["warnings"] = report.get("warnings", [])
                report["warnings"].append(f"verify error: {e}")
                report["verification"] = {
                    "status": "error",
                    "message": str(e),
                }

        logger.info("部署完成")
        if "diff_summary" in report:
            logger.info(f"部署差异摘要: {report['diff_summary']}")
        return report

    def _configs_differ(self, rendered: str, current: str) -> tuple[bool, str]:
        """配置差异检测（interface 感知意图子集匹配）。"""
        return configs_intent_differs(rendered, current)
