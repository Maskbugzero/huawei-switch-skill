# -*- coding: utf-8 -*-
"""
串口管理模块。

提供串口扫描、配置和传输抽象。
参考历史项目 jiaohuanji 的实现风格，使用 dataclasses、typing 和 logger。
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

import serial
import serial.tools.list_ports

from src.console.exceptions import (
    PortNotFoundError,
    ConsoleDisconnect,
)
from src.console.logger import get_logger

logger = get_logger("serial")


@dataclass(frozen=True)
class PortInfo:
    """系统串口描述信息。"""
    device: str
    description: str
    hwid: str = ""

    def __str__(self) -> str:
        return f"{self.device} - {self.description}"


@dataclass
class SerialConfig:
    """串口连接参数。"""
    baudrate: int = 9600
    bytesize: int = serial.EIGHTBITS
    stopbits: float = serial.STOPBITS_ONE
    parity: str = serial.PARITY_NONE
    timeout: float = 1.0
    write_timeout: float = 2.0

    def as_dict(self) -> dict[str, int | float | str]:
        return {
            "baudrate": self.baudrate,
            "bytesize": self.bytesize,
            "stopbits": self.stopbits,
            "parity": self.parity,
            "timeout": self.timeout,
            "write_timeout": self.write_timeout,
        }


class Transport(ABC):
    """传输层抽象基类。"""

    @abstractmethod
    def connect(self, **kwargs) -> None:
        ...

    @abstractmethod
    def disconnect(self) -> None:
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        ...

    @abstractmethod
    def read(self, size: int = 4096) -> bytes:
        ...

    @abstractmethod
    def write(self, data: bytes) -> int:
        ...

    def send_line(self, text: str) -> int:
        line = text.rstrip("\r\n") + "\r\n"
        logger.debug(f"TX: {line.rstrip()!r}")
        return self.write(line.encode("ascii", errors="replace"))


class SerialTransport(Transport):
    """基于 pyserial 的串口传输实现。"""

    def __init__(self, config: Optional[SerialConfig] = None) -> None:
        self.config: SerialConfig = config or SerialConfig()
        self._port: Optional[serial.Serial] = None
        self.port_name: str = ""

    @staticmethod
    def scan_ports() -> List[PortInfo]:
        """扫描系统所有可用串口。"""
        logger.info("扫描可用串口...")
        ports: List[PortInfo] = []
        try:
            for p in serial.tools.list_ports.comports():
                ports.append(PortInfo(
                    device=p.device,
                    description=p.description,
                    hwid=p.hwid or "",
                ))
        except Exception as e:
            logger.error(f"扫描串口异常: {e}")

        logger.info(f"发现 {len(ports)} 个串口")
        for p in ports:
            logger.info(f"  {p}")
        return ports

    @staticmethod
    def find_port(port_name: str) -> PortInfo:
        """按名称查找串口。"""
        for p in SerialTransport.scan_ports():
            if p.device.upper() == port_name.upper():
                return p
        raise PortNotFoundError(
            f"串口 {port_name} 不存在，请检查连接和驱动",
            port=port_name,
        )

    def connect(self, port: str, **kwargs) -> None:
        """连接指定串口。"""
        info = self.find_port(port)
        self.port_name = info.device
        self._port = serial.Serial(
            port=self.port_name,
            **self.config.as_dict(),
            **kwargs
        )
        logger.info(f"已连接串口 {self.port_name}")

    def disconnect(self) -> None:
        if self._port and self._port.is_open:
            self._port.close()
            logger.info(f"已断开串口 {self.port_name}")
        self._port = None

    def is_connected(self) -> bool:
        return self._port is not None and self._port.is_open

    def read(self, size: int = 4096) -> bytes:
        if not self.is_connected():
            raise ConsoleDisconnect("串口未连接")
        return self._port.read(size)

    def write(self, data: bytes) -> int:
        if not self.is_connected():
            raise ConsoleDisconnect("串口未连接")
        return self._port.write(data)
