#!/usr/bin/env python3
"""
Skill Example 01: 最简 Console 连接与命令执行

这是使用 huawei-switch-skill Skill 的最基础示例。
"""

from src.console import Connection

def main():
    print("=== Skill Example: 连接交换机并执行命令 ===")

    # 使用上下文管理器自动连接和断开
    with Connection(port="COM4", password="your_password") as conn:
        # 执行单条命令
        version = conn.send_command("display version")
        print("设备版本信息:")
        print(version[:300])  # 只打印前300字符

        # 执行多条命令
        print("\n--- 执行系统视图命令 ---")
        conn.send_command("system-view")
        conn.send_command("display current-configuration | include sysname")

if __name__ == "__main__":
    main()
