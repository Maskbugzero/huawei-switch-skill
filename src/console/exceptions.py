# -*- coding: utf-8 -*-
"""
Console 模块异常定义。
"""

from __future__ import annotations


class ConsoleError(Exception):
    """Console 基础异常。"""
    pass


class PortNotFoundError(ConsoleError):
    """串口未找到。"""
    def __init__(self, message: str, port: str = ""):
        super().__init__(message)
        self.port = port


class ConsoleDisconnect(ConsoleError):
    """连接断开。"""
    pass


class PromptNotFound(ConsoleError):
    """未找到提示符。"""
    pass


class ConsoleTimeout(ConsoleError):
    """操作超时。"""
    pass


class AuthenticationError(ConsoleError):
    """认证失败。"""
    pass


class CommandError(ConsoleError):
    """命令执行错误。"""
    pass
