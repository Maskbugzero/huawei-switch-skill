# -*- coding: utf-8 -*-
"""
分页处理模块。
"""

from __future__ import annotations

import re
import time
from typing import Optional

from src.console.logger import get_logger

logger = get_logger("pager_handler")


class PagerHandler:
    """More 分页自动处理。"""

    MORE_PATTERN = re.compile(r"---- More ----", re.IGNORECASE)
    SPACE = b" "
    ENTER = b"\r\n"

    def __init__(self, max_pages: int = 100) -> None:
        self.max_pages = max_pages

    def handle_pagination(self, text: str, transport) -> str:
        """处理分页，自动发送空格继续。"""
        if not self.MORE_PATTERN.search(text):
            return text

        logger.info("检测到分页，自动处理...")
        full_output = text
        pages = 0

        while self.MORE_PATTERN.search(full_output) and pages < self.max_pages:
            pages += 1
            # 发送空格继续
            transport.write(self.SPACE)
            time.sleep(0.2)

            # 读取更多
            try:
                more = transport.read(4096)
                if more:
                    more_text = more.decode("utf-8", errors="replace")
                    full_output += more_text
            except Exception as e:
                logger.warning(f"读取分页失败: {e}")
                break

        # 去除 More 标记
        full_output = self.MORE_PATTERN.sub("", full_output)
        logger.info(f"分页处理完成，共 {pages} 页")
        return full_output.strip()
