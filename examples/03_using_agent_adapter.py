#!/usr/bin/env python3
"""
Skill Example 03: 使用 AgentAdapter 统一调用（推荐方式）

展示如何通过 Skill 的统一入口 AgentAdapter 来执行不同操作。
这是 Skill 被上层 Agent 系统调用的推荐方式。

更新说明：
- 已迁移至 DeviceInfo + 顶层字段的现代用法（Pydantic 模型）
- 支持 dry_run 模式和幂等性部署
- 内部使用上下文管理器，资源安全
- 支持 validate action
- 新增：错误处理最佳实践（try-except + response.success 检查）
"""

import logging
from src.agent import AgentAdapter, AgentRequest, DeviceInfo

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    print("=== Skill Example: 通过 AgentAdapter 调用 ===")

    adapter = AgentAdapter()

    # ============================================================
    # 示例1: 执行备份（带错误处理）
    # ============================================================
    print("\n[1] 执行备份操作")
    try:
        backup_request = AgentRequest(
            action="backup",
            device=DeviceInfo(port="COM4", password="your_password"),
            variables={"device_name": "SW-01"}
        )
        backup_response = adapter.execute(backup_request)

        if backup_response.success:
            backup_path = backup_response.data.get("backup_path", "N/A")
            print(f"✅ 备份成功: {backup_path}")
        else:
            logger.error(f"备份失败: {backup_response.code} - {backup_response.message}")
            print(f"❌ 备份失败: {backup_response.message}")

    except Exception as e:
        logger.exception("备份操作发生未捕获异常")
        print(f"❌ 异常: {e}")

    # ============================================================
    # 示例2: 执行部署（正常模式，带错误处理）
    # ============================================================
    print("\n[2] 执行部署操作（正常模式）")
    try:
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

        if deploy_response.success:
            status = deploy_response.data.get("status", "unknown")
            if status == "skipped":
                print("⏭️  跳过部署（配置无差异）")
            else:
                print(f"✅ 部署成功: {status}")
                if "diff_summary" in deploy_response.data:
                    print(f"   差异摘要: {deploy_response.data['diff_summary']}")
        else:
            logger.error(f"部署失败: {deploy_response.code} - {deploy_response.message}")
            print(f"❌ 部署失败: {deploy_response.message}")

    except Exception as e:
        logger.exception("部署操作发生未捕获异常")
        print(f"❌ 异常: {e}")

    # ============================================================
    # 示例2b: Dry-Run 模式（带错误处理）
    # ============================================================
    print("\n[2b] Dry-Run 部署（仅模拟，不实际下发）")
    try:
        dry_run_request = AgentRequest(
            action="deploy",
            device=DeviceInfo(port="COM4", password="your_password"),
            template="access_switch.j2",
            variables={
                "hostname": "SW-01",
                "vlan_list": "10 20 30",
                "management_ip": "192.168.1.10",
                "device_name": "SW-01"
            },
            backup=True,
            dry_run=True
        )
        dry_run_response = adapter.execute(dry_run_request)

        if dry_run_response.success:
            status = dry_run_response.data.get("status", "unknown")
            if status == "dry_run":
                print("✅ Dry-Run 成功（未实际下发）")
                if "planned_steps_count" in dry_run_response.data:
                    print(f"   计划步骤数: {dry_run_response.data['planned_steps_count']}")
            elif status == "skipped":
                print("⏭️  跳过部署（配置无差异）")
        else:
            logger.error(f"Dry-Run 失败: {dry_run_response.code} - {dry_run_response.message}")
            print(f"❌ Dry-Run 失败: {dry_run_response.message}")

    except Exception as e:
        logger.exception("Dry-Run 操作发生未捕获异常")
        print(f"❌ 异常: {e}")

    # ============================================================
    # 示例3: 执行单条命令（带错误处理）
    # ============================================================
    print("\n[3] 执行单条命令")
    try:
        command_request = AgentRequest(
            action="command",
            device=DeviceInfo(port="COM4", password="your_password"),
            variables={"command": "display interface brief"}
        )
        command_response = adapter.execute(command_request)

        if command_response.success:
            output = command_response.data.get("output", "")
            print(f"✅ 命令执行成功")
            print(f"输出预览: {output[:200]}...")
        else:
            logger.error(f"命令执行失败: {command_response.code} - {command_response.message}")
            print(f"❌ 命令执行失败: {command_response.message}")

    except Exception as e:
        logger.exception("命令执行发生未捕获异常")
        print(f"❌ 异常: {e}")


if __name__ == "__main__":
    main()
