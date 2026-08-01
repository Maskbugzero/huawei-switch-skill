# -*- coding: utf-8 -*-
"""
AAA / 安全配置解析器。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


class AAAParser:
    """解析 AAA、SSH、Telnet、ACL 配置。"""

    def parse(self, text: str) -> Dict[str, Any]:
        aaa = {
            "ssh_enabled": bool(re.search(r"ssh\s+server\s+enable", text, re.IGNORECASE)),
            "telnet_enabled": bool(re.search(r"telnet\s+server\s+enable", text, re.IGNORECASE)),
            "aaa_enabled": bool(re.search(r"aaa", text, re.IGNORECASE)),
        }
        return aaa
