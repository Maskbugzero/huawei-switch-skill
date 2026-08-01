#!/usr/bin/env python3
"""
Skill Example 05: SSH 首次连接 + 强制修改密码

展示如何使用 Skill 处理交换机首次 SSH 登录强制改密场景。
"""

from src.ssh.first_connect import SSHFirstConnect, SSHDevice

def main():
    print("=== Skill Example: SSH 首次改密 ===")

    device = SSHDevice(
        host="10.207.8.117",
        username="admin",
        old_password="initial_password",
        new_password="New@StrongPass123",
        port=22
    )

    ssh_tool = SSHFirstConnect(device)

    success = ssh_tool.change_password_and_verify()

    if success:
        print("\n✅ 密码修改成功并已验证！")
    else:
        print("\n❌ 改密流程失败，请检查日志")

if __name__ == "__main__":
    main()
