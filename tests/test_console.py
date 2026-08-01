# -*- coding: utf-8 -*-
"""
Console 模块 Mock 测试。
"""

import pytest
from unittest.mock import patch, MagicMock

from src.console import (
    Connection,
    PromptDetector,
    PagerHandler,
    SerialTransport,
)
from src.console.exceptions import PromptNotFound, ConsoleTimeout


class TestPromptDetector:
    """提示符检测器测试。"""

    def test_detect_prompt(self):
        detector = PromptDetector()
        text = "display version\n<SW-01>"
        prompt = detector.detect(text)
        assert prompt == "<SW-01>"

    def test_is_prompt(self):
        detector = PromptDetector()
        assert detector.is_prompt("<SW-01>") is True
        assert detector.is_prompt("Password:") is True
        assert detector.is_prompt("random text") is False


class TestPagerHandler:
    """分页处理器测试。"""

    def test_handle_pagination_no_more(self):
        handler = PagerHandler()
        mock_transport = MagicMock()
        text = "Some output without more"
        result = handler.handle_pagination(text, mock_transport)
        assert result == text
        mock_transport.write.assert_not_called()


class TestConnection:
    """Connection 类 Mock 测试。"""

    def test_send_command_with_mock(self, mock_connection):
        """测试使用模拟 transport 发送命令。"""
        mock_connection.transport.read.return_value = b"display version\n<SW-01>"

        result = mock_connection.send_command("display version")
        assert "display version" not in result or result.strip() == ""

    def test_connection_context_manager(self, mock_transport):
        """测试上下文管理器。"""
        mock_transport.read.side_effect = [b"<SW-01>"] * 5

        with patch.object(Connection, '_disable_pager'):
            with Connection(transport=mock_transport) as conn:
                assert conn._connected is True
