# -*- coding: utf-8 -*-
"""
提示符检测模块。
"""

from __future__ import annotations

import re
from typing import Optional

from src.console.logger import get_logger

logger = get_logger("prompt_detector")


class PromptDetector:
    """提示符自动识别器。"""

    # 常见华为提示符模式
    PROMPT_PATTERNS = [
        r"<[\w\-]+>",           # <hostname>
        r"\[[\w\-]+\]",         # [hostname]
        r"[\w\-]+>",            # hostname>
        r"[\w\-]+\]",           # hostname]
        r"Password:",           # 密码提示
        r"password:",           # 小写
        r"Confirm Password:",   # 确认密码
    ]

    def __init__(self) -> None:
        self.compiled_patterns = [re.compile(p) for p in self.PROMPT_PATTERNS]

    def detect(self, text: str) -> Optional[str]:
        """从文本中检测提示符。"""
        for pattern in self.compiled_patterns:
            match = pattern.search(text)
            if match:
                prompt = match.group(0)
                logger.debug(f"检测到提示符: {prompt}")
                return prompt
        return None

    def is_prompt(self, text: str) -> bool:
        """检查文本是否包含提示符。"""
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                return True
        return False

    def extract_hostname(self, prompt: str) -> Optional[str]:
        """从提示符中提取主机名。"""
        match = re.search(r"[<[]?([\w\-]+)[>\]]?", prompt)
        if match:
            return match.group(1)
        return None
