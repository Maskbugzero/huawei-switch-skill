# -*- coding: utf-8 -*-
"""
配置采集器测试
"""

from unittest.mock import MagicMock

from src.backup.collector import ConfigCollector


def test_collect_all_basic():
    """测试 collect_all 基本功能"""
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "mock output"

    collector = ConfigCollector(mock_conn, disable_pagination=False)
    results = collector.collect_all()

    # 验证是否调用了关键命令
    called_commands = [call[0][0] for call in mock_conn.send_command.call_args_list]
    assert "display current-configuration" in called_commands
    assert len(results) >= 6  # 至少包含标准采集命令


def test_collect_current_config():
    """测试仅采集当前配置"""
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = "current config content"

    collector = ConfigCollector(mock_conn, disable_pagination=False)
    config = collector.collect_current_config()

    assert config == "current config content"
    mock_conn.send_command.assert_called()


def test_collect_device_info():
    """测试采集设备信息"""
    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = ["version output", "device output"]

    collector = ConfigCollector(mock_conn, disable_pagination=False)
    info = collector.collect_device_info()

    assert "version" in info
    assert "device" in info


def test_collect_with_error():
    """测试单个命令采集失败的情况"""
    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = Exception("采集失败")

    collector = ConfigCollector(mock_conn, disable_pagination=False)
    results = collector.collect_all()

    # 验证失败的命令返回了错误信息
    current_config_result = results.get("display current-configuration", "")
    assert "ERROR" in str(current_config_result)
