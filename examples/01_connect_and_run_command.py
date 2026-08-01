#!/usr/bin/env python3
"""
Skill Example 01: 执行单条命令（推荐使用 AgentAdapter）

这是使用 huawei-switch-skill Skill 的最基础示例。
推荐通过 AgentAdapter 调用。
"""

from src.agent import AgentAdapter, AgentRequest, DeviceInfo


def main():
    print("=== Skill Example: 通过 AgentAdapter 执行命令 ===")

    adapter = AgentAdapter()

    request = AgentRequest(
        action="command",
        device=DeviceInfo(port="COM4", password="your_password"),
        variables={"command": "display version"}
    )

    response = adapter.execute(request)

    if response.success:
        print("命令执行成功:")
        print(response.data.get("output", "")[:300])
    else:
        print("执行失败:", response.message)


if __name__ == "__main__":
    main()


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
