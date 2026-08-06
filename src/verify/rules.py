# -*- coding: utf-8 -*-
"""
校验规则定义。
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List


def _parse_vlan_list(raw: Any) -> List[int]:
    if raw is None:
        return []
    if isinstance(raw, list):
        out: List[int] = []
        for v in raw:
            try:
                out.append(int(v))
            except (TypeError, ValueError):
                continue
        return out
    if isinstance(raw, int):
        return [raw]
    if isinstance(raw, str):
        return [int(x) for x in re.findall(r"\d+", raw)]
    return []


def vlan_present(config: str, vlan: int) -> bool:
    """判断配置中是否声明了指定 VLAN（支持 vlan N / vlan batch ...）。"""
    text = config.lower()
    v = int(vlan)
    if re.search(rf"\bvlan\s+batch\b[^\n#]*\b{v}\b", text):
        return True
    if re.search(rf"\bvlan\s+{v}\b", text):
        return True
    return False


def build_expected_from_variables(variables: Dict[str, Any]) -> Dict[str, Any]:
    """从部署 variables 构造浅层校验 expected。"""
    expected: Dict[str, Any] = {"require_ssh": True}
    host = variables.get("hostname") or variables.get("sysname")
    if host:
        expected["hostname"] = str(host)
    vlans = _parse_vlan_list(variables.get("vlan_list"))
    if vlans:
        expected["vlan_list"] = vlans
    return expected


class VerificationRules:
    """配置校验规则集合。"""

    def __init__(self) -> None:
        self._rules: Dict[str, Callable] = {
            "sysname": self._check_sysname,
            "vlan_consistency": self._check_vlan,
            "trunk_consistency": self._check_trunk,
            "ssh_status": self._check_ssh,
        }

    def get_rules(self) -> Dict[str, Callable]:
        return self._rules

    def _check_sysname(self, before: str, after: str, expected: Dict) -> Dict:
        hostname = expected.get("hostname") or expected.get("sysname")
        if not hostname:
            return {"status": "skipped", "message": "未提供 hostname 预期"}
        # 整词匹配 sysname <name>
        pattern = re.compile(
            rf"^\s*sysname\s+{re.escape(str(hostname))}\s*$",
            re.IGNORECASE | re.MULTILINE,
        )
        if pattern.search(after or ""):
            return {"status": "pass", "message": f"sysname={hostname}"}
        return {
            "status": "fail",
            "message": f"sysname 未匹配预期 {hostname!r}",
        }

    def _check_vlan(self, before: str, after: str, expected: Dict) -> Dict:
        """检查 VLAN 是否存在（基于 expected 中的 vlan_list）"""
        expected_vlans = _parse_vlan_list(expected.get("vlan_list", []))
        if not expected_vlans:
            return {"status": "skipped", "message": "未提供 VLAN 预期"}

        missing = [v for v in expected_vlans if not vlan_present(after or "", v)]
        if missing:
            return {"status": "fail", "message": f"缺少 VLAN: {missing}"}
        return {"status": "pass", "message": "VLAN 一致"}

    def _check_trunk(self, before: str, after: str, expected: Dict) -> Dict:
        """简单检查 trunk 接口是否存在"""
        if "port link-type trunk" in (after or "").lower() or "interface" in (
            after or ""
        ).lower():
            return {"status": "pass", "message": "接口/Trunk 配置存在"}
        return {"status": "fail", "message": "配置中未发现接口配置"}

    def _check_ssh(self, before: str, after: str, expected: Dict) -> Dict:
        if expected.get("require_ssh") is False:
            return {"status": "skipped", "message": "未要求检查 SSH"}
        if "ssh server enable" in (after or "").lower():
            return {"status": "pass", "message": "SSH 已启用"}
        # 未显式要求时：若 expected 无 require_ssh 键，保持旧行为（检查）
        if "require_ssh" not in expected and not expected:
            if "ssh server enable" in (after or "").lower():
                return {"status": "pass", "message": "SSH 已启用"}
            return {"status": "fail", "message": "SSH 未启用"}
        return {"status": "fail", "message": "SSH 未启用"}
