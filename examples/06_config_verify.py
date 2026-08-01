#!/usr/bin/env python3
"""
Skill Example 06: 配置一致性校验（推荐使用 AgentAdapter）

展示如何通过 AgentAdapter 执行配置校验。
"""

from src.agent import AgentAdapter, AgentRequest, DeviceInfo


def main():
    print("=== Skill Example: 通过 AgentAdapter 执行配置校验 ===")

    adapter = AgentAdapter()

    request = AgentRequest(
        action="validate",
        device=DeviceInfo(port="COM4", password="your_password"),
        variables={
            "device_name": "SW-01",
            "before_config_path": "backups/SW-01/20260801-143022/current-configuration.txt",
            "after_config_path": "backups/SW-01/20260801-150000/current-configuration.txt",
            "expected": {
                "vlan": ["10", "20", "30"],
                "management_ip": "192.168.1.10"
            }
        }
    )

    response = adapter.execute(request)

    if response.success:
        report = response.data.get("validation_report", {})
        print("校验结果:", report)
    else:
        print("校验失败:", response.message)


if __name__ == "__main__":
    main()

