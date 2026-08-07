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

    # 常见华为提示符模式（使用行尾锚点避免误判）
    # 注意：接口视图如 [GigabitEthernet0/0/24] 含 /，\w 不够
    PROMPT_PATTERNS = [
        r"<[\w\-./:]+>\s*$",           # <hostname>（用户视图）
        r"\[[\w\-./:]+(?:-[^\]]+)?\]\s*$",  # [hostname] / [GigabitEthernet0/0/1] / [hostname-aaa]
        r"[\w\-./:]+>\s*$",            # hostname>（兼容，无尖括号）
        r"[\w\-./:]+\]\s*$",           # hostname]（兼容；尽量靠后匹配完整后缀）
        r"[Pp]assword[:：]\s*$",       # 密码提示（支持中英文冒号）
        r"Confirm [Pp]assword[:：]\s*$",  # 确认密码
        r"Continue\?\s*\[Y/N\]",       # Continue? [Y/N]
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
        """检查文本是否以 CLI 提示符结束（读命令输出时使用）。

        注意：Password: / Continue? 等登录交互提示不应作为命令结束条件，
        否则登录后的命令读取可能被误截断。
        """
        cli_patterns = self.compiled_patterns[:4]
        for pattern in cli_patterns:
            if pattern.search(text):
                return True
        return False

    def extract_hostname(self, prompt: str) -> Optional[str]:
        """从提示符中提取主机名。"""
        match = re.search(r"[<[]?([\w\-]+)[>\]]?", prompt)
        if match:
            return match.group(1)
        return None
