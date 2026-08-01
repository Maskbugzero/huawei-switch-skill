# -*- coding: utf-8 -*-
"""
命令执行引擎模块。

提供 send_command, send_commands 等高级命令执行能力。
"""

from __future__ import annotations

from typing import List, Optional

from src.console import Connection
from src.console.logger import get_logger
from src.command.error_detector import ErrorDetector
from src.command.response_parser import ResponseParser
from src.command.save_handler import SaveHandler

logger = get_logger("command")


class CommandExecutor:
    """命令执行器。"""

    def __init__(self, connection: Connection) -> None:
        self.connection = connection
        self.error_detector = ErrorDetector()
        self.response_parser = ResponseParser()
        self.save_handler = SaveHandler()

    def send_command(
        self,
        command: str,
        timeout: Optional[float] = None,
        expect_prompt: Optional[str] = None,
    ) -> str:
        """发送单条命令。"""
        logger.info(f"发送命令: {command}")

        # 特殊处理 save 命令
        if command.strip().lower() == "save":
            return self.save_handler.handle_save(self.connection, timeout)

        output = self.connection.send_command(command, timeout)

        # 错误检测
        error = self.error_detector.detect(output)
        if error:
            logger.error(f"命令执行错误: {error}")
            raise Exception(f"Command failed: {error}")

        parsed = self.response_parser.parse(output)
        return parsed

    def send_commands(
        self,
        commands: List[str],
        timeout: Optional[float] = None,
    ) -> List[str]:
        """发送多条命令。"""
        results = []
        for cmd in commands:
            result = self.send_command(cmd, timeout)
            results.append(result)
        return results

    def execute_script(self, script: str) -> str:
        """执行脚本（多行命令）。"""
        commands = [line.strip() for line in script.splitlines() if line.strip()]
        results = self.send_commands(commands)
        return "\n".join(results)
