# -*- coding: utf-8 -*-
"""
配置校验器 - Verifier。
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.console.logger import get_logger
from src.verify.rules import VerificationRules

logger = get_logger("verify")


class ConfigVerifier:
    """配置一致性校验器。"""

    def __init__(self) -> None:
        self.rules = VerificationRules()

    def verify(
        self,
        before_config: str,
        after_config: str,
        expected: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行校验并生成报告。"""
        report = {
            "status": "pass",
            "checks": [],
            "details": {},
        }

        for rule_name, rule_func in self.rules.get_rules().items():
            result = rule_func(before_config, after_config, expected)
            report["checks"].append({
                "rule": rule_name,
                "result": result["status"],
            })
            report["details"][rule_name] = result

            if result["status"] == "fail":
                report["status"] = "fail"

        logger.info(f"校验完成: {report['status']}")
        return report
