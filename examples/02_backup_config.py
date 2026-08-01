#!/usr/bin/env python3
"""
Skill Example 02: 一键配置备份（推荐使用 AgentAdapter）

展示如何通过 Skill 的统一入口 AgentAdapter 执行配置备份。
"""

from src.agent import AgentAdapter, AgentRequest, DeviceInfo


def main():
    print("=== Skill Example: 通过 AgentAdapter 执行配置备份 ===")

    adapter = AgentAdapter()

    request = AgentRequest(
        action="backup",
        device=DeviceInfo(port="COM4", password="your_password"),
        variables={"device_name": "SW-01"}
    )

    response = adapter.execute(request)

    if response.success:
        print("备份成功！")
        print("备份路径:", response.data.get("backup_path"))
    else:
        print("备份失败:", response.message)


if __name__ == "__main__":
    main()

