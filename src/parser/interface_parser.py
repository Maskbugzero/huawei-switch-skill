# -*- coding: utf-8 -*-
"""
接口配置解析器。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from src.console.logger import get_logger

logger = get_logger("parser.interface")


class InterfaceParser:
    """解析接口配置（GigabitEthernet、Eth-Trunk、Vlanif 等）。"""

    # 防止正则在超大配置下回溯性能爆炸或内存问题
    MAX_CONFIG_LENGTH = 500_000

    def parse(self, text: str) -> List[Dict[str, Any]]:
        interfaces = []
        if len(text) > self.MAX_CONFIG_LENGTH:
            text = text[:self.MAX_CONFIG_LENGTH]

        # 匹配 interface 块（支持多行）
        pattern = r"interface\s+(GigabitEthernet|Eth-Trunk|Vlanif)\s*([\d/]+)([\s\S]*?)(?=^interface|\Z)"
        try:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                if_name = f"{match.group(1)}{match.group(2)}"
                block = match.group(3) or ""

                ip_match = re.search(r"ip address\s+([\d.]+)\s+([\d.]+)", block, re.IGNORECASE)
                desc_match = re.search(r"description\s+(.+)", block, re.IGNORECASE)
                shutdown = "shutdown" in block.lower() and "undo shutdown" not in block.lower()

                interfaces.append({
                    "name": if_name,
                    "type": match.group(1),
                    "ip_address": ip_match.group(1) if ip_match else None,
                    "description": desc_match.group(1).strip() if desc_match else None,
                    "shutdown": shutdown,
                    "raw": match.group(0)[:200],
                })
        except re.error as e:
            logger.warning(f"InterfaceParser 正则匹配失败，已返回空结果: {e}")
            return []

        return interfaces
