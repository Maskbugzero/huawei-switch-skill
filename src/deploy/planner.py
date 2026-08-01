# -*- coding: utf-8 -*-
"""
部署规划器。
"""

from __future__ import annotations

from typing import List


class DeploymentPlanner:
    """部署步骤规划器。"""

    def plan(self, config_text: str) -> List[str]:
        """生成部署步骤列表。"""
        steps = []
        for line in config_text.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                steps.append(line)
        return steps
