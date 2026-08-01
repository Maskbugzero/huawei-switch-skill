# -*- coding: utf-8 -*-
"""
变量管理模块。
"""

from __future__ import annotations

from typing import Any, Dict


class TemplateVariables:
    """模板变量管理。"""

    def __init__(self) -> None:
        self.vars: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self.vars[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.vars.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        return self.vars.copy()
