# -*- coding: utf-8 -*-
"""
响应解析模块。
"""

from __future__ import annotations

import re


class ResponseParser:
    """命令响应解析器。"""

    def parse(self, output: str) -> str:
        """解析并清理响应输出。"""
        # 去除多余空行
        lines = [line.rstrip() for line in output.splitlines() if line.strip()]
        return "\n".join(lines)
