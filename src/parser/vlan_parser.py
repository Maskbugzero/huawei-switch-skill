# -*- coding: utf-8 -*-
"""
VLAN 配置解析器。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


class VlanParser:
    """解析 VLAN 配置。"""

    def parse(self, text: str) -> List[Dict[str, Any]]:
        vlans = []
        # 匹配 vlan batch 或单个 vlan
        batch_match = re.search(r"vlan\s+batch\s+(.+)", text, re.IGNORECASE)
        if batch_match:
            vlans.append({"type": "batch", "value": batch_match.group(1).strip()})

        for m in re.finditer(r"vlan\s+(\d+)", text, re.IGNORECASE):
            vlans.append({"type": "single", "id": int(m.group(1))})
        return vlans
