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



def cmd_deploy(args):
    """执行配置部署（已弃用，推荐使用 AgentAdapter）"""
    print("⚠️  警告：deploy 子命令已弃用！")
    print("推荐使用 AgentAdapter（Skill 统一入口）：")
    print("""
from src.agent import AgentAdapter, AgentRequest, DeviceInfo

adapter = AgentAdapter()
request = AgentRequest(
    action="deploy",
    device=DeviceInfo(port="COM4", password="xxx"),
    template="access_switch.j2",           # 或其他模板
    variables={"hostname": "SW-01", ...},
    backup=True
)
response = adapter.execute(request)
""")
    print("详细用法请参考 README.md 和 examples/03_using_agent_adapter.py")
    sys.exit(0)


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


    # deploy 子命令（已弃用，推荐使用 AgentAdapter）
    p_deploy = subparsers.add_parser(
        "deploy",
        help="【已弃用】部署配置到交换机 - 推荐使用 AgentAdapter"
    )
    p_deploy.add_argument("--script", choices=["admin", "poe"], required=False, help="（已弃用）部署脚本类型")
    p_deploy.add_argument("--port", default="COM4", help="串口号")
    p_deploy.add_argument("--password", "-p", required=False, help="Console 密码")
    p_deploy.add_argument("--config-dir", default=".", help="配置目录")
    p_deploy.add_argument("--config-file", "-c", default="config.txt", help="配置文件名")
    p_deploy.add_argument("--device-name", required=False, help="设备名称")
    p_deploy.add_argument("--no-backup", action="store_true", help="跳过备份")
    p_deploy.set_defaults(func=cmd_deploy)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
