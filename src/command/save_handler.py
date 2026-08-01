# -*- coding: utf-8 -*-
"""
Save 命令处理模块。

自动处理 save 命令的 [Y/N] 确认提示。
"""

from __future__ import annotations

import time
from typing import Optional

from src.console.logger import get_logger

logger = get_logger("save_handler")


class SaveHandler:
    """Save 命令处理器。"""

    def handle_save(self, connection, timeout: Optional[float] = None) -> str:
        """执行 save 命令并自动确认。"""
        logger.info("执行 save 命令，自动确认...")

        # 发送 save
        connection.transport.send_line("save")

        # 读取直到 [Y/N] 或提示符
        start = time.time()
        timeout = timeout or 30.0
        buffer = b""
        while time.time() - start < timeout:
            try:
                chunk = connection.transport.read(1024)
                if chunk:
                    buffer += chunk
                    text = buffer.decode("utf-8", errors="replace")
                    if "[Y/N]" in text or "Are you sure" in text:
                        # 发送 Y
                        connection.transport.send_line("Y")
                        time.sleep(1)
                        # 继续读取结果
                        result = connection._read_until_prompt(timeout=10)
                        logger.info("配置已保存")
                        return result
                    if connection.prompt_detector.is_prompt(text):
                        return text
            except Exception:
                pass
            time.sleep(0.1)

        raise Exception("Save 命令超时")
