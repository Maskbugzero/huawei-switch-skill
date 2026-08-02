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
        """检查 VLAN 是否存在（基于 expected 中的 vlan_list）"""
        expected_vlans = expected.get("vlan_list", [])
        if not expected_vlans:
            return {"status": "skipped", "message": "未提供 VLAN 预期"}

        missing = []
        for vlan in expected_vlans:
            if f"vlan {vlan}" not in after.lower() and f"vlan{vlan}" not in after.lower():
                missing.append(vlan)

        if missing:
            return {"status": "fail", "message": f"缺少 VLAN: {missing}"}
        return {"status": "pass", "message": "VLAN 一致"}

    def _check_trunk(self, before: str, after: str, expected: Dict) -> Dict:
        """简单检查 trunk 接口是否存在"""
        if "interface" not in after.lower():
            return {"status": "fail", "message": "配置中未发现接口配置"}
        return {"status": "pass", "message": "Trunk 接口存在"}

    def _check_ssh(self, before: str, after: str, expected: Dict) -> Dict:
        if "ssh server enable" in after.lower():
            return {"status": "pass", "message": "SSH 已启用"}
        return {"status": "fail", "message": "SSH 未启用"}
