# -*- coding: utf-8 -*-
"""
统一错误码定义。

错误码格式：前缀 + 3位数字
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ErrorCode:
    code: str
    category: str
    message: str


# 连接相关
CON001 = ErrorCode("CON001", "connection", "串口未找到")
CON002 = ErrorCode("CON002", "connection", "串口打开失败")
CON003 = ErrorCode("CON003", "connection", "登录失败")
CON004 = ErrorCode("CON004", "connection", "设备无响应")

# 配置相关
CFG001 = ErrorCode("CFG001", "configuration", "命令执行失败")
CFG002 = ErrorCode("CFG002", "configuration", "VRP 语法错误")
CFG003 = ErrorCode("CFG003", "configuration", "参数错误")
CFG004 = ErrorCode("CFG004", "configuration", "配置未生效")

# 校验相关
VAL001 = ErrorCode("VAL001", "validation", "主机名不匹配")
VAL002 = ErrorCode("VAL002", "validation", "VLAN 缺失")
VAL003 = ErrorCode("VAL003", "validation", "接口配置不一致")
VAL004 = ErrorCode("VAL004", "validation", "IP 地址不匹配")

# 备份相关
BKP001 = ErrorCode("BKP001", "backup", "备份失败")

# 回滚相关
RBK001 = ErrorCode("RBK001", "rollback", "回滚失败")

# Agent 适配器相关
APT001 = ErrorCode("APT001", "adapter", "无效请求")
APT002 = ErrorCode("APT002", "adapter", "不支持的操作")
APT003 = ErrorCode("APT003", "adapter", "请求验证失败")
APT004 = ErrorCode("APT004", "adapter", "执行超时")
