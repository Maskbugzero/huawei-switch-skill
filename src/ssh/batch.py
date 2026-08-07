# -*- coding: utf-8 -*-
"""
SSH 批量管理骨架。

定位：已纳管设备的多机 backup / command（配置主路径仍是 Console）。
VRP 命令与 Console 相同，此处仅使用 SSH transport。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from netmiko import ConnectHandler
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from src.backup import ConfigExporter
from src.command.error_detector import ErrorDetector
from src.console.logger import get_logger
from src.deploy.deployer import DEFAULT_DANGEROUS_KEYWORDS, _line_is_dangerous
from src.ssh.hostkeys import netmiko_hostkey_kwargs, resolve_accept_unknown
from src.ssh.inventory import DeviceInventory, InventoryDevice, load_inventory

logger = get_logger("ssh.batch")


class DeviceResult(BaseModel):
    """单台设备执行结果。"""

    model_config = ConfigDict(extra="ignore")

    name: str
    host: str
    success: bool
    message: str = ""
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class BatchReport(BaseModel):
    """批量执行汇总。"""

    model_config = ConfigDict(extra="ignore")

    action: str = ""
    results: List[DeviceResult] = Field(default_factory=list)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.success)

    def summary(self) -> str:
        return (
            f"batch {self.action}: 成功 {self.success_count} / "
            f"失败 {self.failed_count} / 合计 {len(self.results)}"
        )


def _device_password(device: InventoryDevice) -> str:
    pwd = device.password
    if isinstance(pwd, SecretStr):
        return pwd.get_secret_value()
    return str(pwd or "")


class BatchSSHManager:
    """
    基于设备清单的 SSH 批量运维。

    当前提供：
    - backup_all：逐台 display current-configuration 并写入 backups/
    - command_all：逐台执行同一条命令（建议只读；危险命令默认阻断）

    连接串行执行（骨架阶段）；后续可加线程池与速率限制。
    """

    def __init__(
        self,
        inventory: DeviceInventory,
        backup_base_dir: str = "backups",
        read_timeout: int = 120,
        accept_unknown_host_key: bool = False,
    ) -> None:
        self.inventory = inventory
        self.exporter = ConfigExporter(base_dir=backup_base_dir)
        self.read_timeout = read_timeout
        self.accept_unknown_host_key = resolve_accept_unknown(accept_unknown_host_key)
        self._error_detector = ErrorDetector()

    @classmethod
    def from_yaml(
        cls,
        path: str | Path,
        backup_base_dir: str = "backups",
        accept_unknown_host_key: bool = False,
    ) -> "BatchSSHManager":
        return cls(
            load_inventory(path),
            backup_base_dir=backup_base_dir,
            accept_unknown_host_key=accept_unknown_host_key,
        )

    def _connect(self, device: InventoryDevice):
        # netmiko 4.x：ConnectHandler 不接受 read_timeout；读超时用 send_command(read_timeout=...)
        params = {
            "device_type": device.device_type,
            "host": device.host,
            "username": device.username,
            "password": _device_password(device),
            "port": device.port,
            "conn_timeout": 30,
            **netmiko_hostkey_kwargs(accept_unknown=self.accept_unknown_host_key),
        }
        conn = ConnectHandler(**params)
        try:
            conn.send_command("screen-length 0 temporary", read_timeout=30)
        except Exception as e:
            logger.warning(f"{device.name}: screen-length failed: {e}")
        return conn

    def backup_all(self, names: Optional[List[str]] = None) -> BatchReport:
        """批量备份 running-config。"""
        report = BatchReport(action="backup")
        for device in self.inventory.select(names):
            report.results.append(self._backup_one(device))
        logger.info(report.summary())
        return report

    def command_all(
        self,
        command: str,
        names: Optional[List[str]] = None,
        allow_dangerous: bool = False,
    ) -> BatchReport:
        """
        批量执行同一条命令。

        默认阻断危险命令；设备 Error 输出记为失败。
        """
        cmd = (command or "").strip()
        if not cmd:
            raise ValueError("command must be non-empty")

        report = BatchReport(action="command")

        if _line_is_dangerous(cmd, DEFAULT_DANGEROUS_KEYWORDS) and not allow_dangerous:
            for device in self.inventory.select(names):
                report.results.append(
                    DeviceResult(
                        name=device.name,
                        host=device.host,
                        success=False,
                        message="blocked dangerous command",
                        error=(
                            "dangerous command blocked; "
                            "pass allow_dangerous=True to override"
                        ),
                        data={"command": cmd},
                    )
                )
            logger.warning(report.summary())
            return report

        for device in self.inventory.select(names):
            report.results.append(
                self._command_one(device, cmd, allow_dangerous=allow_dangerous)
            )
        logger.info(report.summary())
        return report

    def _backup_one(self, device: InventoryDevice) -> DeviceResult:
        conn = None
        try:
            conn = self._connect(device)
            config = conn.send_command(
                "display current-configuration",
                read_timeout=self.read_timeout,
            )
            if not (config or "").strip():
                return DeviceResult(
                    name=device.name,
                    host=device.host,
                    success=False,
                    message="backup failed",
                    error="empty configuration received",
                )
            path = self.exporter.export_backup(
                device.name,
                {"display current-configuration": config},
                metadata={"host": device.host, "transport": "ssh", "batch": True},
            )
            return DeviceResult(
                name=device.name,
                host=device.host,
                success=True,
                message="backup ok",
                data={"backup_path": str(path), "transport": "ssh"},
            )
        except Exception as e:
            logger.error(f"backup failed {device.name} ({device.host}): {e}")
            return DeviceResult(
                name=device.name,
                host=device.host,
                success=False,
                message="backup failed",
                error=str(e),
            )
        finally:
            if conn is not None:
                try:
                    conn.disconnect()
                except Exception as de:
                    logger.warning(f"{device.name}: disconnect error: {de}")

    def _command_one(
        self,
        device: InventoryDevice,
        command: str,
        allow_dangerous: bool = False,
    ) -> DeviceResult:
        conn = None
        try:
            conn = self._connect(device)
            output = conn.send_command(command, read_timeout=self.read_timeout)
            err = self._error_detector.detect(output or "")
            if err:
                return DeviceResult(
                    name=device.name,
                    host=device.host,
                    success=False,
                    message="command error",
                    error=err,
                    data={
                        "output": output,
                        "command": command,
                        "transport": "ssh",
                    },
                )
            return DeviceResult(
                name=device.name,
                host=device.host,
                success=True,
                message="command ok",
                data={"output": output, "command": command, "transport": "ssh"},
            )
        except Exception as e:
            logger.error(f"command failed {device.name} ({device.host}): {e}")
            return DeviceResult(
                name=device.name,
                host=device.host,
                success=False,
                message="command failed",
                error=str(e),
                data={"command": command},
            )
        finally:
            if conn is not None:
                try:
                    conn.disconnect()
                except Exception as de:
                    logger.warning(f"{device.name}: disconnect error: {de}")


def _main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Huawei SSH batch ops")
    parser.add_argument(
        "--inventory",
        "-i",
        default="configs/devices.yaml",
        help="path to devices YAML",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    p_backup = sub.add_parser("backup", help="backup all (or named) devices")
    p_backup.add_argument("--name", action="append", dest="names", default=None)

    p_cmd = sub.add_parser("command", help="run one command on devices")
    p_cmd.add_argument("--cmd", required=True, help="CLI command to run")
    p_cmd.add_argument("--name", action="append", dest="names", default=None)
    p_cmd.add_argument(
        "--allow-dangerous",
        action="store_true",
        default=False,
        help="allow reboot/reset/delete/format/shutdown",
    )

    args = parser.parse_args(argv)
    mgr = BatchSSHManager.from_yaml(args.inventory)

    if args.action == "backup":
        report = mgr.backup_all(names=args.names)
    else:
        report = mgr.command_all(
            args.cmd,
            names=args.names,
            allow_dangerous=bool(getattr(args, "allow_dangerous", False)),
        )

    print(report.summary())
    for r in report.results:
        status = "OK" if r.success else "FAIL"
        detail = r.data.get("backup_path") or r.data.get("output", "")[:120] or r.error
        print(f"  [{status}] {r.name} ({r.host}): {detail}")
    return 0 if report.failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(_main())
