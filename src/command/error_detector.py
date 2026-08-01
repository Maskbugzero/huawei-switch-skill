# -*- coding: utf-8 -*-
"""
错误检测模块。
"""

from __future__ import annotations

import re
from typing import Optional


class ErrorDetector:
    """命令错误检测器。"""

    ERROR_PATTERNS = [
        r"Error:",
        r"Failed:",
        r"Incomplete command",
        r"Unrecognized command",
        r"Invalid input",
        r"Syntax error",
    ]

    def __init__(self) -> None:
        self.compiled = [re.compile(p, re.IGNORECASE) for p in self.ERROR_PATTERNS]

    def detect(self, output: str) -> Optional[str]:
        """检测输出中的错误。"""
        for pattern in self.compiled:
            if pattern.search(output):
                # 提取错误行
                for line in output.splitlines():
                    if pattern.search(line):
                        return line.strip()
        return None

    def is_error(self, output: str) -> bool:
        return self.detect(output) is not None
