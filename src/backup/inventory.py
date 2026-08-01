# -*- coding: utf-8 -*-
"""
设备清单模块 - Inventory。

管理已知设备信息和备份历史。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class DeviceInventory:
    """设备清单管理。"""

    def __init__(self, inventory_file: str = "configs/inventory.json") -> None:
        self.inventory_file = Path(inventory_file)
        self.inventory_file.parent.mkdir(parents=True, exist_ok=True)
        self.devices: Dict[str, Dict] = self._load()

    def _load(self) -> Dict[str, Dict]:
        if self.inventory_file.exists():
            try:
                return json.loads(self.inventory_file.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save(self) -> None:
        self.inventory_file.write_text(
            json.dumps(self.devices, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def add_device(
        self,
        name: str,
        port: str,
        model: str = "",
        ip: str = "",
        password: str = "",
        notes: str = "",
    ) -> None:
        """添加或更新设备信息。"""
        self.devices[name] = {
            "name": name,
            "port": port,
            "model": model,
            "ip": ip,
            "password": password,
            "notes": notes,
            "last_backup": None,
            "added_at": datetime.now().isoformat(),
        }
        self._save()

    def update_last_backup(self, name: str, backup_path: str) -> None:
        """更新设备最后备份时间。"""
        if name in self.devices:
            self.devices[name]["last_backup"] = {
                "time": datetime.now().isoformat(),
                "path": backup_path,
            }
            self._save()

    def get_device(self, name: str) -> Optional[Dict]:
        return self.devices.get(name)

    def list_devices(self) -> List[Dict]:
        return list(self.devices.values())

    def remove_device(self, name: str) -> bool:
        if name in self.devices:
            del self.devices[name]
            self._save()
            return True
        return False
