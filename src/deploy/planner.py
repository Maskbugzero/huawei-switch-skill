# -*- coding: utf-8 -*-
"""
部署规划器。
"""

from __future__ import annotations

from typing import List


class DeploymentPlanner:
    """部署步骤规划器。"""

    def plan(self, config_text: str) -> List[str]:
        """生成部署步骤列表（去重 + 过滤注释）。"""
        steps = []
        seen = set()
        for line in config_text.splitlines():
            # 去除行内注释
            clean_line = line.split("#")[0].strip()
            if clean_line and clean_line not in seen:
                seen.add(clean_line)
                steps.append(clean_line)
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
        """基于当前配置生成简单的回滚计划（将配置命令转为 undo 命令）。"""
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
