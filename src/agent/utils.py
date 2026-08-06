# -*- coding: utf-8 -*-
"""Agent 通用小工具。"""

from __future__ import annotations

from typing import Any


def as_bool(value: Any, default: bool = False) -> bool:
    """
    安全解析布尔值。

    避免 bool("false") is True 的陷阱（LLM/JSON 常见字符串布尔）。
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value != 0
    if isinstance(value, str):
        s = value.strip().lower()
        if s in {"", "false", "0", "no", "off", "n", "null", "none"}:
            return False
        if s in {"true", "1", "yes", "on", "y"}:
            return True
        return default
    return bool(value)
