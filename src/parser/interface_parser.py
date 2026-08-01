# -*- coding: utf-8 -*-
"""
接口配置解析器。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


class InterfaceParser:
    """解析接口配置（GigabitEthernet、Eth-Trunk、Vlanif 等）。"""

    def parse(self, text: str) -> List[Dict[str, Any]]:
        interfaces = []
        # 简单正则匹配接口块
        pattern = r"interface\s+(GigabitEthernet|Eth-Trunk|Vlanif)\s*([\d/]+)"
        for match in re.finditer(pattern, text, re.IGNORECASE):
            if_name = f"{match.group(1)}{match.group(2)}"
            interfaces.append({
                "name": if_name,
                "type": match.group(1),
                "raw": match.group(0),
            })
        return interfaces
