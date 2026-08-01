# -*- coding: utf-8 -*-
"""
Console 模块初始化。
"""

from __future__ import annotations

from src.console.serial_manager import (
    PortInfo,
    SerialConfig,
    Transport,
    SerialTransport,
)
from src.console.connection import Connection
from src.console.prompt_detector import PromptDetector
from src.console.pager_handler import PagerHandler
from src.console.exceptions import (
    ConsoleError,
    PortNotFoundError,
    ConsoleDisconnect,
    PromptNotFound,
    ConsoleTimeout,
    AuthenticationError,
    CommandError,
)
from src.console.logger import get_logger

__all__ = [
    "PortInfo",
    "SerialConfig",
    "Transport",
    "SerialTransport",
    "Connection",
    "PromptDetector",
    "PagerHandler",
    "ConsoleError",
    "PortNotFoundError",
    "ConsoleDisconnect",
    "PromptNotFound",
    "ConsoleTimeout",
    "AuthenticationError",
    "CommandError",
    "get_logger",
]
