# -*- coding: utf-8 -*-
"""
日志模块。
"""

from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 logger。"""
    logger = logging.getLogger(f"huawei_switch_agent.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
