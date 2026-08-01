#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Huawei Switch Skill CLI 入口
"""

import argparse
import sys

from src.console import Connection
from src.backup import ConfigCollector, ConfigExporter


def cmd_connect(args):
    """测试连接"""
    try:
        with Connection(port=args.port, password=args.password) as conn:
            print("连接成功！")
            version = conn.send_command("display version")
            print(version[:500])
    except Exception as e:
        print(f"连接失败: {e}")
        sys.exit(1)


def cmd_backup(args):
    """执行配置备份"""
    try:
        with Connection(port=args.port, password=args.password) as conn:
            collector = ConfigCollector(conn)
            data = collector.collect_all()

            exporter = ConfigExporter()
            path = exporter.export_backup(args.device, data)
            print(f"备份完成: {path}")
    except Exception as e:
        print(f"备份失败: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Huawei Switch Skill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # connect 子命令
    p_connect = subparsers.add_parser("connect", help="测试连接交换机")
    p_connect.add_argument("--port", required=True, help="串口号，如 COM4")
    p_connect.add_argument("--password", required=True, help="Console 密码")
    p_connect.set_defaults(func=cmd_connect)

    # backup 子命令
    p_backup = subparsers.add_parser("backup", help="备份交换机配置")
    p_backup.add_argument("--port", required=True, help="串口号")
    p_backup.add_argument("--password", required=True, help="Console 密码")
    p_backup.add_argument("--device", required=True, help="设备名称")
    p_backup.set_defaults(func=cmd_backup)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
