#!/usr/bin/env python3
"""
Skill Example 06: 配置一致性校验与报告生成

展示如何使用 Skill 进行部署后或日常的配置校验。
"""

from src.console import Connection
from src.verify import ConfigVerifier

def main():
    print("=== Skill Example: 配置校验 ===")

    with Connection(port="COM4", password="your_password") as conn:
        verifier = ConfigVerifier(conn)

        # 执行校验
        report = verifier.verify(
            rules=["vlan", "interface", "stp", "ssh"],
            device_name="SW-01"
        )

        print("校验报告:")
        print(report.to_markdown())   # 或 report.to_html()

        if report.has_issues():
            print("\n⚠️ 发现配置问题，建议修复")
        else:
            print("\n✅ 配置符合预期")

if __name__ == "__main__":
    main()
