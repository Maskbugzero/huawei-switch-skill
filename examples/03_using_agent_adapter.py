#!/usr/bin/env python3
"""
Skill Example 03: 使用 AgentAdapter 统一调用（推荐方式）

展示如何通过 Skill 的统一入口 AgentAdapter 来执行不同操作。
这是 Skill 被上层 Agent 系统调用的推荐方式。

更新说明：
- 已迁移至 DeviceInfo + 顶层字段的现代用法
- 内部使用上下文管理器，资源安全
- 支持 validate action
"""

from src.agent import AgentAdapter, AgentRequest
from src.agent.request import DeviceInfo

def main():
    print("=== Skill Example: 通过 AgentAdapter 调用 ===")

    adapter = AgentAdapter()

    # 示例1: 执行备份
    print("\n[1] 执行备份操作")
    backup_request = AgentRequest(
        action="backup",
        device=DeviceInfo(port="COM4", password="your_password"),
        variables={"device_name": "SW-01"}
    )
    backup_response = adapter.execute(backup_request)
    print(f"备份结果: {backup_response}")

    # 示例2: 执行部署
    print("\n[2] 执行部署操作")
    deploy_request = AgentRequest(
        action="deploy",
        device=DeviceInfo(port="COM4", password="your_password"),
        template="access_switch.j2",
        variables={
            "hostname": "SW-01",
            "vlan_list": "10 20 30",
            "management_ip": "192.168.1.10",
            "device_name": "SW-01"
        },
        backup=True
    )
    deploy_response = adapter.execute(deploy_request)
    print(f"部署结果: {deploy_response}")

    # 示例3: 执行单条命令
    print("\n[3] 执行单条命令")
    command_request = AgentRequest(
        action="command",
        device=DeviceInfo(port="COM4", password="your_password"),
        variables={"command": "display interface brief"}
    )
    command_response = adapter.execute(command_request)
    print(f"命令执行结果: {command_response}")

if __name__ == "__main__":
    main()
