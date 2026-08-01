#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
华为交换机配置备份脚本（参考你提供的成功脚本优化版）
使用 Netmiko + screen-length 0 temporary + 高 read_timeout

使用示例：
python backup_switch_config.py --ip 10.0.0.1 --password "your_password"
"""

import argparse
import os
from datetime import datetime
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException


def backup_switch_config(ip: str, username: str, password: str, port: int = 22):
    backup_dir = r"D:\work\switchconfig"
    os.makedirs(backup_dir, exist_ok=True)

    filename = os.path.join(backup_dir, f"{ip}.cfg")
    print(f"\n=== 开始备份交换机 {ip} ===")
    print(f"备份文件: {filename}")

    device = {
        "device_type": "huawei_vrp",
        "host": ip,
        "username": username,
        "password": password,
        "port": port,
    }

    try:
        print("[*] 正在连接交换机...")
        conn = ConnectHandler(**device)
        print("[+] SSH连接成功")

        # 关闭分页
        print("[*] 执行 screen-length 0 temporary ...")
        conn.send_command("screen-length 0 temporary")

        # 获取配置（关键：高 read_timeout）
        print("[*] 正在获取完整配置...")
        config = conn.send_command(
            "display current-configuration",
            read_timeout=120
        )

        # 保存文件
        with open(filename, "w", encoding="utf-8") as f:
            f.write(config)

        print(f"[+] 备份完成: {filename}")
        print(f"[+] 配置大小: {len(config)} 字符")

        conn.disconnect()
        return True

    except NetmikoAuthenticationException:
        print("[-] 认证失败！请检查用户名或密码。")
        return False
    except NetmikoTimeoutException:
        print("[-] 连接超时。")
        return False
    except Exception as e:
        print(f"[-] 错误: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="华为交换机配置备份工具（参考成功脚本）")
    parser.add_argument("--ip", required=True, help="交换机 IP 地址")
    parser.add_argument("--username", default="admins", help="用户名")
    parser.add_argument("--password", required=True, help="密码")
    parser.add_argument("--port", type=int, default=22, help="SSH 端口")

    args = parser.parse_args()

    print("=" * 60)
    print("华为交换机配置备份工具（参考你提供的成功脚本）")
    print("=" * 60)

    success = backup_switch_config(
        ip=args.ip,
        username=args.username,
        password=args.password,
        port=args.port
    )

    if success:
        print("\n[成功] 配置备份完成！")
    else:
        print("\n[失败] 请检查日志。")
