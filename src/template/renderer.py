# -*- coding: utf-8 -*-
"""
模板渲染器 - Renderer。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, Template

from src.console.logger import get_logger

logger = get_logger("template.renderer")


class TemplateRenderer:
    """基于 Jinja2 的模板渲染器。"""

    def __init__(self, template_dir: str = "templates") -> None:
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, variables: Dict[str, Any]) -> str:
        """渲染模板。"""
        template = self.env.get_template(template_name)
        result = template.render(**variables)
        logger.info(f"模板 {template_name} 渲染完成")
        return result

    def render_string(self, template_str: str, variables: Dict[str, Any]) -> str:
        """直接渲染字符串模板。"""
        template = self.env.from_string(template_str)
        return template.render(**variables)
