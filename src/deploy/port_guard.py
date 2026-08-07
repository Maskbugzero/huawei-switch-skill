# -*- coding: utf-8 -*-
"""
端口角色 / 上联口保护。

防止模板或 Agent 误改 trunk 上联（S1730 等机型上 GE 口常作 uplink）。
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


_IF_RE = re.compile(r"^\s*interface\s+(\S+)", re.IGNORECASE)
_EXIT_RE = re.compile(r"^\s*(quit|return|system-view)\b", re.IGNORECASE)


def normalize_if_name(name: str) -> str:
    return re.sub(r"\s+", "", (name or "").strip().lower())


def _coerce_port_list(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        # space / comma separated
        parts = re.split(r"[\s,;]+", raw.strip())
        return [p for p in parts if p]
    if isinstance(raw, (list, tuple, set)):
        out: List[str] = []
        for item in raw:
            out.extend(_coerce_port_list(item))
        return out
    return [str(raw)]


def resolve_explicit_protected_ports(variables: Optional[Dict[str, Any]]) -> Set[str]:
    """
    从 variables 收集显式保护口。

    使用 uplink_ports / protected_ports（及 uplink1/2）。
    不把单独的 `uplink` 算作禁止修改——接入模板会合法配置该 trunk 上联。
    """
    variables = variables or {}
    names: List[str] = []
    names.extend(_coerce_port_list(variables.get("uplink_ports")))
    names.extend(_coerce_port_list(variables.get("protected_ports")))
    for key in ("uplink1", "uplink2", "uplink_a", "uplink_b"):
        names.extend(_coerce_port_list(variables.get(key)))
    return {normalize_if_name(n) for n in names if n}


def detect_uplink_like_interfaces(current_config: str) -> Set[str]:
    """
    从 running-config 启发式识别上联口：

    - description 含 uplink
    - port link-type trunk 且 allow-pass 覆盖极宽（如 2 to 4094 或大量 vlan）
    """
    protected: Set[str] = set()
    current_if: Optional[str] = None
    body: List[str] = []
    is_trunk = False
    desc = ""
    allow = ""

    def _flush() -> None:
        nonlocal current_if, body, is_trunk, desc, allow
        if current_if:
            hit = False
            if "uplink" in desc.lower():
                hit = True
            if is_trunk and (
                "2 to 4094" in allow
                or "2 to 4094" in allow.replace(" ", "")
                or re.search(r"2\s*to\s*4094", allow, re.I)
            ):
                hit = True
            if hit:
                protected.add(normalize_if_name(current_if))
        current_if = None
        body = []
        is_trunk = False
        desc = ""
        allow = ""

    for raw in (current_config or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _IF_RE.match(line)
        if m:
            _flush()
            current_if = m.group(1)
            continue
        if current_if is None:
            continue
        if _EXIT_RE.match(line):
            _flush()
            continue
        low = line.lower()
        if low.startswith("description"):
            desc = line
        if "link-type trunk" in low:
            is_trunk = True
        if "allow-pass vlan" in low:
            allow = line
        body.append(line)
    _flush()
    return protected


def interfaces_in_config(config_text: str) -> Dict[str, List[str]]:
    """解析目标配置中的 interface -> 子命令列表（不含 interface 行本身）。"""
    result: Dict[str, List[str]] = {}
    current: Optional[str] = None
    for raw in (config_text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _IF_RE.match(line)
        if m:
            current = normalize_if_name(m.group(1))
            result.setdefault(current, [])
            continue
        if current is None:
            continue
        if _EXIT_RE.match(line):
            current = None
            continue
        result[current].append(line)
    return result


def _is_access_like_body(body: Sequence[str]) -> bool:
    """判断子命令是否像「把口改成接入口」——这是上联误伤的主场景。"""
    text = "\n".join(body).lower()
    if "link-type access" in text:
        return True
    if "port-security" in text:
        return True
    if "port default vlan" in text and "link-type trunk" not in text:
        return True
    return False


def find_protected_touches(
    config_text: str,
    *,
    protected_auto: Set[str],
    protected_explicit: Set[str],
) -> List[str]:
    """
    返回应阻断的受保护接口。

    - explicit：任意配置触及即阻断
    - auto（当前配置像上联）：仅当目标写成 access 类配置时阻断
      （允许模板继续写 trunk 上联）
    """
    touched: List[str] = []
    for if_name, body in interfaces_in_config(config_text).items():
        if if_name in protected_explicit:
            touched.append(if_name)
            continue
        if if_name in protected_auto and _is_access_like_body(body):
            touched.append(if_name)
    return sorted(set(touched))


def check_uplink_protection(
    config_text: str,
    variables: Optional[Dict[str, Any]] = None,
    current_config: Optional[str] = None,
    allow_uplink_change: bool = False,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    上联/保护口检查。

    Returns:
        (ok, reason, details)
        ok=False 表示应阻断部署。
    """
    if allow_uplink_change:
        return True, "", {"skipped": True, "reason": "allow_uplink_change=True"}

    explicit = resolve_explicit_protected_ports(variables)
    detected = detect_uplink_like_interfaces(current_config or "")
    touches = find_protected_touches(
        config_text,
        protected_auto=detected,
        protected_explicit=explicit,
    )

    details = {
        "explicit_protected": sorted(explicit),
        "detected_uplink_like": sorted(detected),
        "protected_union": sorted(set(explicit) | set(detected)),
        "touched_protected": touches,
    }
    if not touches:
        return True, "", details

    reason = (
        "protected/uplink interfaces would be modified; "
        "pass allow_uplink_change=True to override or exclude them from template. "
        f"touched={touches}"
    )
    return False, reason, details
