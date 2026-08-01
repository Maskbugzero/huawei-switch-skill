# -*- coding: utf-8 -*-
"""
连接管理模块。

负责建立连接、提示符识别、认证、命令发送等。
"""

from __future__ import annotations

import re
import time
from typing import Optional

from src.console.serial_manager import Transport, SerialTransport, SerialConfig
from src.console.exceptions import (
    PromptNotFound,
    AuthenticationError,
    ConsoleTimeout,
    ConsoleDisconnect,
)
from src.console.logger import get_logger
from src.console.prompt_detector import PromptDetector
from src.console.pager_handler import PagerHandler

logger = get_logger("connection")


class Connection:
    """Console 连接管理类。"""

    def __init__(
        self,
        port: Optional[str] = None,
        password: Optional[str] = None,
        transport: Optional[Transport] = None,
        config: Optional[SerialConfig] = None,
        timeout: float = 30.0,
    ) -> None:
        self.port = port
        self.password = password
        self.timeout = timeout
        self.transport = transport or SerialTransport(config)
        self.prompt_detector = PromptDetector()
        self.pager_handler = PagerHandler()
        self.current_prompt: Optional[str] = None
        self._connected = False

    def connect(self) -> None:
        """建立连接并自动登录。"""
        if self.port and isinstance(self.transport, SerialTransport):
            self.transport.connect(self.port)
        else:
            self.transport.connect()

        self._connected = True
        logger.info("开始自动登录流程...")

        # 清除初始输出
        time.sleep(0.5)
        try:
            initial = self.transport.read(4096)
            logger.debug(f"初始输出: {initial}")
        except Exception:
            pass

        # 发送回车同步
        self.transport.send_line("")

        # 检测提示符或密码提示
        output = self._read_until_prompt_or_password()
        logger.debug(f"连接后输出: {output}")

        if "Password:" in output or "password:" in output.lower():
            if self.password:
                self.transport.send_line(self.password)
                time.sleep(1)
                confirm_output = self._read_until_prompt()
                if "Error" in confirm_output or "invalid" in confirm_output.lower():
                    raise AuthenticationError("密码错误")
                logger.info("密码认证成功")
            else:
                raise AuthenticationError("需要密码但未提供")

        # 检测提示符
        self.current_prompt = self.prompt_detector.detect(output)
        if not self.current_prompt:
            # 尝试再次读取
            more = self._read_until_prompt()
            self.current_prompt = self.prompt_detector.detect(more)

        if not self.current_prompt:
            raise PromptNotFound("无法识别设备提示符")

        logger.info(f"连接成功，提示符: {self.current_prompt}")

        # 关闭分页
        self._disable_pager()

    def _read_until_prompt_or_password(self, timeout: Optional[float] = None) -> str:
        """读取直到提示符或密码提示。"""
        timeout = timeout or self.timeout
        start = time.time()
        buffer = b""
        while time.time() - start < timeout:
            try:
                chunk = self.transport.read(1024)
                if chunk:
                    buffer += chunk
                    text = buffer.decode("utf-8", errors="replace")
                    if "Password:" in text or "password:" in text.lower():
                        return text
                    if self.prompt_detector.is_prompt(text):
                        return text
            except Exception as e:
                logger.debug(f"读取过程中出现异常（可忽略的瞬时错误）: {e}")
                pass
            time.sleep(0.1)
        raise ConsoleTimeout("读取超时")

    def _read_until_prompt(self, timeout: Optional[float] = None) -> str:
        """读取直到提示符。"""
        timeout = timeout or self.timeout
        start = time.time()
        buffer = b""
        while time.time() - start < timeout:
            try:
                chunk = self.transport.read(1024)
                if chunk:
                    buffer += chunk
                    text = buffer.decode("utf-8", errors="replace")
                    if self.prompt_detector.is_prompt(text):
                        # 处理分页
                        text = self.pager_handler.handle_pagination(text, self.transport)
                        return text
            except Exception as e:
                logger.debug(f"读取提示符过程中出现异常（可忽略的瞬时错误）: {e}")
                pass
            time.sleep(0.1)
        raise ConsoleTimeout("读取提示符超时")

    def _disable_pager(self) -> None:
        """关闭分页显示。"""
        try:
            self.transport.send_line("screen-length 0 temporary")
            time.sleep(0.5)
            self.transport.read(1024)  # 丢弃响应
            logger.info("已关闭分页")
        except Exception as e:
            logger.warning(f"关闭分页失败: {e}")

    def send_command(self, command: str, timeout: Optional[float] = None) -> str:
        """发送命令并返回输出。"""
        if not self._connected or not self.transport.is_connected():
            raise ConsoleDisconnect("未连接到设备")

        logger.info(f"执行命令: {command}")
        self.transport.send_line(command)

        output = self._read_until_prompt(timeout)
        # 去除命令回显和提示符
        output = self._clean_output(command, output)
        return output

    def _clean_output(self, command: str, output: str) -> str:
        """清理输出，移除命令回显和提示符。"""
        lines = output.splitlines()
        cleaned = []
        skip_next = False
        for line in lines:
            if command in line:
                continue
            if self.prompt_detector.is_prompt(line):
                continue
            cleaned.append(line)
        return "\n".join(cleaned).strip()

    def disconnect(self) -> None:
        """断开连接。"""
        if self.transport:
            self.transport.disconnect()
        self._connected = False
        logger.info("已断开连接")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
