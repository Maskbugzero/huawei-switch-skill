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
        # 匹配 vlan batch
        batch_match = re.search(r"vlan\s+batch\s+(.+)", text, re.IGNORECASE)
        if batch_match:
            vlans.append({"type": "batch", "value": batch_match.group(1).strip()})

        # 匹配单个 vlan 并尝试提取名称
        for m in re.finditer(r"vlan\s+(\d+)(?:\s+name\s+(.+))?", text, re.IGNORECASE):
            vlan_id = int(m.group(1))
            name = m.group(2).strip() if m.group(2) else None
            vlans.append({"type": "single", "id": vlan_id, "name": name})
        return vlans
