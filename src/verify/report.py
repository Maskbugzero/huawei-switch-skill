# -*- coding: utf-8 -*-
"""
报告生成器。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict


class ReportGenerator:
    """HTML / Markdown 报告生成器。"""

    def generate_markdown(self, report: Dict[str, Any]) -> str:
        """生成 Markdown 报告。"""
        md = f"# 配置校验报告\n\n"
        md += f"**时间**: {datetime.now().isoformat()}\n"
        md += f"**状态**: {report.get('status', 'unknown')}\n\n"

        md += "## 检查项\n\n"
        for check in report.get("checks", []):
            md += f"- {check['rule']}: {check['result']}\n"

        return md

    def generate_html(self, report: Dict[str, Any]) -> str:
        """生成简单 HTML 报告。"""
        html = f"<h1>配置校验报告</h1>"
        html += f"<p>状态: {report.get('status')}</p>"
        return html
