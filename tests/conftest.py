# -*- coding: utf-8 -*-
"""
测试通用配置和 fixtures。
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from src.console.serial_manager import SerialTransport
from src.console.connection import Connection


@pytest.fixture
def mock_transport():
    """创建一个模拟的 SerialTransport。"""
    transport = MagicMock(spec=SerialTransport)
    transport.is_connected.return_value = True
    transport.port_name = "COM4"
    return transport


@pytest.fixture
def mock_connection(mock_transport):
    """创建一个已连接的模拟 Connection。"""
    conn = Connection(transport=mock_transport)
    conn._connected = True
    conn.current_prompt = "<SW-01>"
    return conn
