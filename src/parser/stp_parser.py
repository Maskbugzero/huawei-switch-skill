# -*- coding: utf-8 -*-
"""
STP 配置解析器。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


class StpParser:
    """解析 STP/RSTP/MSTP 配置。"""

    def parse(self, text: str) -> Dict[str, Any]:
        stp = {"enabled": False, "mode": None}
        if re.search(r"stp\s+enable", text, re.IGNORECASE):
            stp["enabled"] = True
        mode_match = re.search(r"stp\s+mode\s+(\S+)", text, re.IGNORECASE)
        if mode_match:
            stp["mode"] = mode_match.group(1)
        return stp
