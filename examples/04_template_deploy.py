#!/usr/bin/env python3
"""
Skill Example 04: 模板化自动部署 + 回滚

展示如何使用模板和变量进行安全部署。
"""

from src.console import Connection
from src.deploy import DeploymentEngine

def main():
    print("=== Skill Example: 模板化部署 ===")

    variables = {
        "hostname": "SW-01",
        "vlan_list": "10 20 30",
        "management_vlan": 1,
        "management_ip": "192.168.1.10/24",
        "snmp_community": "public"
    }

    engine = DeploymentEngine()

    with Connection(port="COM4", password="your_password") as conn:
        report = engine.deploy(
            connection=conn,
            template="access_switch.j2",
            variables=variables,
            device_name="SW-01",
            backup=True,           # 部署前自动备份
            verify_after=True      # 部署后自动校验
        )

        print("部署报告:")
        print(report)

if __name__ == "__main__":
    main()
