# -*- coding: utf-8 -*-
"""
统一错误码定义。

错误码格式：前缀 + 3位数字

完整矩阵见 SKILL.md「错误码矩阵」章节。
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
CON005 = ErrorCode("CON005", "connection", "SSH 主机密钥不受信任")

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

# 模板相关
TPL001 = ErrorCode("TPL001", "template", "模板不存在")
TPL002 = ErrorCode("TPL002", "template", "模板渲染失败")
TPL003 = ErrorCode("TPL003", "template", "模板变量缺失")

# 部署相关
DEP001 = ErrorCode("DEP001", "deploy", "部署命令执行失败")
DEP002 = ErrorCode("DEP002", "deploy", "部署前配置采集失败")
DEP003 = ErrorCode("DEP003", "deploy", "部署后配置校验失败")
DEP004 = ErrorCode("DEP004", "deploy", "危险命令被阻断")
DEP005 = ErrorCode("DEP005", "deploy", "上联/保护口变更被阻断")
DEP006 = ErrorCode("DEP006", "deploy", "SSH 真下发被禁用")

# 命令执行相关
CMD001 = ErrorCode("CMD001", "command", "命令执行失败")
CMD002 = ErrorCode("CMD002", "command", "命令超时")
CMD003 = ErrorCode("CMD003", "command", "命令返回错误")

# Agent 适配器相关
APT001 = ErrorCode("APT001", "adapter", "无效请求")
APT002 = ErrorCode("APT002", "adapter", "不支持的操作")
APT003 = ErrorCode("APT003", "adapter", "请求验证失败")
APT004 = ErrorCode("APT004", "adapter", "执行超时")


def code_for_deploy_status(status: Optional[str], reason: str = "") -> Optional[str]:
    """根据 deploy report status/reason 选择错误码。"""
    st = (status or "").lower()
    r = (reason or "").lower()
    if st in {"success", "skipped", "dry_run"}:
        return None
    if st == "verify_failed":
        return DEP003.code
    if st == "blocked":
        if "ssh_deploy" in r or "ssh deploy" in r:
            return DEP006.code
        if "uplink" in r or "protected" in r:
            return DEP005.code
        if "dangerous" in r:
            return DEP004.code
        return DEP001.code
    if st == "failed":
        return DEP001.code
    return DEP001.code
