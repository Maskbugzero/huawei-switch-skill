#!/usr/bin/env python3
"""
Skill Example 05: SSH 首次连接 + 强制修改密码（特殊场景）

本示例展示如何处理交换机首次 SSH 登录时强制修改密码的场景。
属于进阶/特殊能力示例，目前不通过 AgentAdapter 调用。

注意：大多数场景推荐使用 Console + AgentAdapter（见其他示例）。
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
