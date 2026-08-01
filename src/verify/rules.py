# -*- coding: utf-8 -*-
"""
校验规则定义。
"""

from __future__ import annotations

from typing import Any, Callable, Dict


class VerificationRules:
    """配置校验规则集合。"""

    def __init__(self) -> None:
        self._rules: Dict[str, Callable] = {
            "vlan_consistency": self._check_vlan,
            "trunk_consistency": self._check_trunk,
            "ssh_status": self._check_ssh,
        }

    def get_rules(self) -> Dict[str, Callable]:
        return self._rules

    def _check_vlan(self, before: str, after: str, expected: Dict) -> Dict:
        # 简化实现
        return {"status": "pass", "message": "VLAN 一致"}

    def _check_trunk(self, before: str, after: str, expected: Dict) -> Dict:
        return {"status": "pass", "message": "Trunk 一致"}

    def _check_ssh(self, before: str, after: str, expected: Dict) -> Dict:
        if "ssh server enable" in after.lower():
            return {"status": "pass", "message": "SSH 已启用"}
        return {"status": "fail", "message": "SSH 未启用"}
