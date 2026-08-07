# -*- coding: utf-8 -*-
"""
SSH 模块：

- SSHFirstConnect：首次登录强制改密
- BatchSSHManager：已纳管设备批量 backup / command（配置主路径仍是 Console）
"""

from __future__ import annotations

from src.ssh.first_connect import SSHFirstConnect, SSHDevice
from src.ssh.batch import BatchSSHManager, BatchReport, DeviceResult
from src.ssh.inventory import DeviceInventory, InventoryDevice, load_inventory
from src.ssh.hostkeys import configure_paramiko_client, netmiko_hostkey_kwargs

__all__ = [
    "SSHFirstConnect",
    "SSHDevice",
    "BatchSSHManager",
    "BatchReport",
    "DeviceResult",
    "DeviceInventory",
    "InventoryDevice",
    "load_inventory",
    "configure_paramiko_client",
    "netmiko_hostkey_kwargs",
]
