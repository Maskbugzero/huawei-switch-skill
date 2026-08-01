#!/usr/bin/env python3
"""
Skill Example 04: 模板化自动部署（推荐使用 AgentAdapter）

展示如何通过 AgentAdapter 进行模板化部署。
这是 Skill 的推荐调用方式。
"""

from src.agent import AgentAdapter, AgentRequest, DeviceInfo


def main():
    print("=== Skill Example: 通过 AgentAdapter 进行模板化部署 ===")

    adapter = AgentAdapter()

    deploy_request = AgentRequest(
        action="deploy",
        device=DeviceInfo(port="COM4", password="your_password"),
        template="access_switch.j2",
        variables={
            "hostname": "SW-01",
            "vlan_list": "10 20 30",
            "management_vlan": 1,
            "management_ip": "192.168.1.10/24",
            "snmp_community": "public",
            "device_name": "SW-01",
        },
        backup=True,  # 部署前自动备份
    )

    response = adapter.execute(deploy_request)

    print("部署结果:")
    print(response)


if __name__ == "__main__":
    main()

