# -*- coding: utf-8 -*-
"""
配置解析器主模块。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.console.logger import get_logger
from src.parser.interface_parser import InterfaceParser
from src.parser.vlan_parser import VlanParser
from src.parser.stp_parser import StpParser
from src.parser.aaa_parser import AAAParser

logger = get_logger("parser")


class ConfigParser:
    """华为配置统一解析器。"""

    def __init__(self) -> None:
        self.interface_parser = InterfaceParser()
        self.vlan_parser = VlanParser()
        self.stp_parser = StpParser()
        self.aaa_parser = AAAParser()

    def parse(self, config_text: str) -> Dict[str, Any]:
        """将配置文本解析为结构化对象。"""
        result = {
            "sysname": self._parse_sysname(config_text),
            "vlans": self.vlan_parser.parse(config_text),
            "interfaces": self.interface_parser.parse(config_text),
            "stp": self.stp_parser.parse(config_text),
            "aaa": self.aaa_parser.parse(config_text),
            "raw_config": config_text,
        }
        logger.info("配置解析完成")
        return result

    def _parse_sysname(self, text: str) -> Optional[str]:
        import re
        match = re.search(r"sysname\s+(\S+)", text)
        return match.group(1) if match else None
