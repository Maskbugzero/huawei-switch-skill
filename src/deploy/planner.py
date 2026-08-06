# -*- coding: utf-8 -*-
"""
部署规划器。
"""

from __future__ import annotations

from typing import List


class DeploymentPlanner:
    """部署步骤规划器。"""

    def plan(self, config_text: str) -> List[str]:
        """
        生成部署步骤列表。

        - 去除空行与行内/整行注释
        - **保留**跨 interface 重复的子命令（禁止全局去重）
        - 仅折叠**连续**完全相同的行（防止误粘贴放大）
        """
        steps: List[str] = []
        prev: str | None = None
        for line in config_text.splitlines():
            clean_line = line.split("#")[0].strip()
            if not clean_line:
                continue
            if clean_line == prev:
                continue
            steps.append(clean_line)
            prev = clean_line
        return steps

    def plan_with_categories(self, config_text: str) -> dict:
        """将部署步骤分类（配置类 vs 其他）。"""
        steps = self.plan(config_text)
        categories = {"config": [], "other": []}
        config_keywords = ["interface", "vlanif", "ip address", "undo", "port"]
        for step in steps:
            lower = step.lower()
            if any(kw in lower for kw in config_keywords):
                categories["config"].append(step)
            else:
                categories["other"].append(step)
        return categories

    def generate_rollback_plan(self, config_text: str) -> List[str]:
        """
        基于当前配置生成简单的回滚计划（将配置命令转为 undo 命令）。

        注意：当前实现为简单前缀策略，仅对 interface/vlan/ip address 及普通命令
        统一添加 "undo " 前缀，并跳过 display/ping 等只读命令。
        对于复杂对象（ACL、路由策略、QoS 等），生成的 undo 命令可能不完整或无效。
        生产环境建议结合人工审核或使用完整 DeploymentEngine 的自动回滚机制。
        """
        steps = self.plan(config_text)
        rollback_steps = []
        skip_prefixes = ["display", "ping", "traceroute", "telnet"]
        for step in steps:
            lower = step.lower()
            if any(lower.startswith(p) for p in skip_prefixes):
                continue  # 跳过无需回滚的命令
            if lower.startswith("interface"):
                rollback_steps.append(f"undo {step}")
            elif lower.startswith("vlan"):
                rollback_steps.append(f"undo {step}")
            elif "ip address" in lower:
                rollback_steps.append(f"undo {step}")
            else:
                rollback_steps.append(f"undo {step}")
        return rollback_steps
