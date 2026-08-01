# -*- coding: utf-8 -*-
"""
模板校验器。
"""

from __future__ import annotations

from typing import Any, Dict, List


class TemplateValidator:
    """模板变量校验器。"""

    REQUIRED_VARS = ["hostname"]

    def validate(self, variables: Dict[str, Any]) -> List[str]:
        """校验必要变量。"""
        errors = []
        for var in self.REQUIRED_VARS:
            if var not in variables:
                errors.append(f"缺少必要变量: {var}")
        return errors
