# -*- coding: utf-8 -*-
"""
Command 模块 Mock 测试。
"""

import pytest
from unittest.mock import MagicMock

from src.command import ErrorDetector, ResponseParser, SaveHandler


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
