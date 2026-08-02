# -*- coding: utf-8 -*-
"""
命令执行相关异常定义。
"""

from __future__ import annotations


class CommandExecutionError(Exception):
    """
    命令执行失败异常。

    当命令执行返回错误（如 Error:、Failed:、Incomplete command 等）时抛出。

    Attributes:
        error_type: 错误类型（如 "Error", "Failed", "Incomplete command"）
        output: 命令的完整输出
        command: 执行失败的命令（可选）
    """

    def __init__(
        self,
        error_type: str,
        output: str,
        command: str | None = None,
    ) -> None:
        self.error_type = error_type
        self.output = output
        self.command = command

        # 构建错误消息
        msg_parts = [f"Command failed: {error_type}"]
        if command:
            msg_parts.append(f"(command: {command})")
        msg_parts.append(f"\nOutput: {output[:200]}...")

        super().__init__(" ".join(msg_parts))

    def __str__(self) -> str:
        return (
            f"CommandExecutionError("
            f"error_type={self.error_type!r}, "
            f"command={self.command!r})"
        )
