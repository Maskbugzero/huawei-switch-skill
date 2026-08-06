# -*- coding: utf-8 -*-
"""
SSH 批量管理 — 设备清单加载。

清单 YAML 示例见 configs/devices.example.yaml。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_serializer, model_validator

from src.backup.exporter import sanitize_device_name


class InventoryDevice(BaseModel):
    """清单中的单台设备（已与 defaults 合并）。"""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Logical device name used in backup paths")
    host: str = Field(..., description="SSH hostname or IP")
    password: SecretStr = Field(
        default=SecretStr(""),
        description="SSH password (prefer password_env)",
    )
    username: str = Field(default="admin")
    port: int = Field(default=22)
    device_type: str = Field(default="huawei_vrp")
    password_env: Optional[str] = Field(
        default=None,
        description="If set, password is read from this environment variable",
    )

    @model_validator(mode="before")
    @classmethod
    def _coerce_password(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        # name 路径安全
        if "name" in data and data["name"] is not None:
            data["name"] = sanitize_device_name(str(data["name"]))
        return data

    @model_validator(mode="after")
    def _resolve_password_env(self) -> "InventoryDevice":
        if self.password_env:
            env_val = os.environ.get(self.password_env)
            if not env_val:
                raise ValueError(
                    f"device {self.name}: env var {self.password_env!r} is not set"
                )
            self.password = SecretStr(env_val)
        secret = self.password.get_secret_value() if self.password else ""
        if not secret:
            raise ValueError(
                f"device {self.name}: password or password_env is required"
            )
        return self

    @field_serializer("password", when_used="json")
    def _mask_password(self, v: SecretStr) -> str:
        return "***"


class DeviceInventory(BaseModel):
    """完整设备清单。"""

    model_config = ConfigDict(extra="ignore")

    devices: List[InventoryDevice] = Field(default_factory=list)

    def get(self, name: str) -> Optional[InventoryDevice]:
        for d in self.devices:
            if d.name == name:
                return d
        return None

    def select(self, names: Optional[List[str]] = None) -> List[InventoryDevice]:
        if not names:
            return list(self.devices)
        wanted = set(names)
        selected = [d for d in self.devices if d.name in wanted]
        missing = wanted - {d.name for d in selected}
        if missing:
            raise KeyError(f"unknown device names: {sorted(missing)}")
        return selected


def load_inventory(path: str | Path) -> DeviceInventory:
    """
    从 YAML 加载设备清单。

    支持顶层 defaults 与 devices 列表合并。
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"inventory not found: {p}")

    raw: Dict[str, Any] = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    defaults = dict(raw.get("defaults") or {})
    devices_raw = raw.get("devices") or []
    if not isinstance(devices_raw, list) or not devices_raw:
        raise ValueError("inventory must contain a non-empty devices list")

    merged: List[Dict[str, Any]] = []
    for item in devices_raw:
        if not isinstance(item, dict):
            raise ValueError("each device entry must be a mapping")
        row = {**defaults, **item}
        merged.append(row)

    return DeviceInventory(devices=[InventoryDevice.model_validate(m) for m in merged])
