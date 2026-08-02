# -*- coding: utf-8 -*-
"""
配置采集模块 - Collector。

负责从交换机采集各种配置和状态信息。
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, List, Optional

from src.console import Connection
from src.console.logger import get_logger
from src.console.exceptions import ConsoleTimeout, ConsoleDisconnect, CommandError

logger = get_logger("backup.collector")


class ConfigCollector:
    """配置采集器。

    自动在初始化时执行 screen-length 0 temporary 关闭分页，
    并对大配置命令使用较高超时（参考实机使用经验）。
    """

    # 标准采集命令列表（按 agent.md 要求）
    COLLECT_COMMANDS = [
        "display current-configuration",
        "display version",
        "display vlan",
        "display interface brief",
        "display stp brief",
        "display device",
    ]

    def __init__(
        self,
        connection: Connection,
        disable_pagination: bool = True,
        default_timeout: float = 120,
    ) -> None:
        self.connection = connection
        self.default_timeout = default_timeout

        if disable_pagination:
            try:
                logger.info("执行 screen-length 0 temporary 关闭分页...")
                self.connection.send_command("screen-length 0 temporary", timeout=10)
            except (ConsoleTimeout, ConsoleDisconnect, CommandError) as e:
                logger.warning(f"关闭分页失败（特定异常）: {e}")
            except Exception as e:
                logger.warning(f"关闭分页失败: {e}")

    def collect_all(self) -> Dict[str, str]:
        """采集所有标准命令的输出。"""
        results: Dict[str, str] = {}
        for cmd in self.COLLECT_COMMANDS:
            try:
                logger.info(f"采集命令: {cmd}")
                # 大配置命令使用更高超时
                timeout = 180 if "current-configuration" in cmd else self.default_timeout
                output = self.connection.send_command(cmd, timeout=timeout)
                results[cmd] = output
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"采集 {cmd} 失败: {e}")
                results[cmd] = f"ERROR: {str(e)}"
        return results

    def collect_current_config(self) -> str:
        """仅采集当前配置（最常用，大配置建议使用更高超时）。"""
        return self.connection.send_command(
            "display current-configuration",
            timeout=300  # 实测大配置需要较长时间
        )

    def collect_device_info(self) -> Dict[str, str]:
        """采集设备基本信息。"""
        info = {}
        try:
            version = self.connection.send_command("display version", timeout=self.default_timeout)
            info["version"] = version
        except Exception as e:
            info["version"] = f"ERROR: {e}"

        try:
            device = self.connection.send_command("display device", timeout=self.default_timeout)
            info["device"] = device
        except Exception as e:
            info["device"] = f"ERROR: {e}"

        return info
