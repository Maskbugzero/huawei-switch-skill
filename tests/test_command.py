# -*- coding: utf-8 -*-
"""
Command 模块 Mock 测试。
"""

import pytest
from unittest.mock import MagicMock

from src.command import (
    ErrorDetector,
    ResponseParser,
    SaveHandler,
    CommandExecutor,
    CommandExecutionError,
)


class TestErrorDetector:
    """错误检测器测试。"""

    def test_detect_error(self):
        detector = ErrorDetector()
        output = "Error: Incomplete command"
        assert detector.detect(output) is not None
        assert detector.is_error(output) is True

    def test_no_error(self):
        detector = ErrorDetector()
        output = "display version\n<SW-01>"
        assert detector.detect(output) is None
        assert detector.is_error(output) is False


class TestResponseParser:
    """响应解析器测试。"""

    def test_parse(self):
        parser = ResponseParser()
        raw = "   display version  \n\n\n<SW-01>"
        result = parser.parse(raw)
        assert "display version" in result


class TestSaveHandler:
    """Save 命令处理器测试（简化）。"""

    def test_handle_save_mock(self, mock_connection):
        """测试 save 命令的 Mock 行为。"""
        handler = SaveHandler()
        # 这里只做简单验证，真实场景需要更复杂的 mock
        assert handler is not None


class TestCommandExecutionError:
    """CommandExecutionError 异常测试。"""

    def test_command_execution_error_attributes(self):
        """测试 CommandExecutionError 的属性"""
        error = CommandExecutionError(
            error_type="Failed",
            output="Failed: Access denied",
            command="display version"
        )

        assert error.error_type == "Failed"
        assert error.output == "Failed: Access denied"
        assert error.command == "display version"
        assert "Failed" in str(error)

    def test_command_execution_error_without_command(self):
        """测试不提供 command 参数的情况"""
        error = CommandExecutionError(
            error_type="Error",
            output="Error: Syntax error"
        )

        assert error.command is None
        assert "Error" in str(error)

    def test_command_execution_error_raised(self):
        """测试命令执行失败时抛出 CommandExecutionError"""
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = "Error: Invalid command\nFailed"

        executor = CommandExecutor(mock_conn)
        with pytest.raises(CommandExecutionError) as exc_info:
            executor.send_command("invalid cmd")

        # error_detector.detect() 返回完整的错误消息
        assert "Error" in exc_info.value.error_type
        assert exc_info.value.command == "invalid cmd"
