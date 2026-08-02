#!/usr/bin/env python3
"""
Skill Example 07: 通过 AgentAdapter 使用 SSH 模式（推荐方式）

展示如何通过 AgentAdapter 在 SSH 模式下执行操作。
这是生产环境中推荐的远程管理方式（无需 Console 串口）。

注意事项：
- SSH 模式下的 deploy 是简化实现（无完整 DeploymentEngine 功能）
- 建议优先使用 Console + AgentAdapter 获得完整特性（幂等性、planner、回滚）
- SSH 首次连接改密场景请参考 examples/05_ssh_first_connect.py

SSH 连接识别规则（DeviceInfo.is_ssh()）：
- host 字段不为空
- port 包含 ":"（如 "192.168.1.1:22"）
- port 以私有 IP 段开头（10., 172., 192.168.）
"""

from src.agent import AgentAdapter, AgentRequest, DeviceInfo


def main():
    print("=== Skill Example: SSH 模式下的 AgentAdapter 调用 ===")

    adapter = AgentAdapter()

    # ============================================================
    # 配置方式 1: 使用 host 字段明确指定 SSH 主机
    # ============================================================
    print("\n[配置方式 1] 使用 host 字段")
    ssh_device_1 = DeviceInfo(
        port="192.168.1.10",           # port 字段存储 IP（会被识别为 SSH）
        host="192.168.1.10",           # 明确指定 host（推荐）
        username="admin",
        password="your_ssh_password",
        port_number=22
    )
    print(f"  is_ssh() = {ssh_device_1.is_ssh()}")  # True

    # ============================================================
    # 配置方式 2: port 字段直接使用 IP（自动识别）
    # ============================================================
    print("\n[配置方式 2] port 字段使用私有 IP（自动识别为 SSH）")
    ssh_device_2 = DeviceInfo(
        port="10.0.0.5",               # 私有 IP 开头 → 自动识别为 SSH
        password="your_ssh_password",
        username="admin"
    )
    print(f"  is_ssh() = {ssh_device_2.is_ssh()}")  # True

    # ============================================================
    # 示例 1: SSH 模式 - 执行备份
    # ============================================================
    print("\n[1] SSH 模式 - 执行备份")
    backup_request = AgentRequest(
        action="backup",
        device=DeviceInfo(
            host="192.168.1.10",
            port="192.168.1.10",
            username="admin",
            password="your_ssh_password",
            port_number=22
        ),
        variables={"device_name": "SW-SSH-01"}
    )
    backup_response = adapter.execute(backup_request)
    print(f"备份结果: {backup_response}")
    # 预期返回: success=True, data={"backup_path": "...", "transport": "ssh"}

    # ============================================================
    # 示例 2: SSH 模式 - 执行单条命令
    # ============================================================
    print("\n[2] SSH 模式 - 执行单条命令")
    command_request = AgentRequest(
        action="command",
        device=DeviceInfo(
            host="192.168.1.10",
            port="192.168.1.10",
            username="admin",
            password="your_ssh_password",
            port_number=22
        ),
        variables={"command": "display version"}
    )
    command_response = adapter.execute(command_request)
    print(f"命令执行结果: {command_response}")
    # 预期返回: success=True, data={"output": "...", "transport": "ssh"}

    # ============================================================
    # 示例 3: SSH 模式 - 部署（简化实现）
    # ============================================================
    print("\n[3] SSH 模式 - 部署（简化实现，推荐 Dry-Run 验证）")
    deploy_request = AgentRequest(
        action="deploy",
        device=DeviceInfo(
            host="192.168.1.10",
            port="192.168.1.10",
            username="admin",
            password="your_ssh_password",
            port_number=22
        ),
        template="access_switch.j2",
        variables={
            "hostname": "SW-SSH-01",
            "vlan_list": "10 20 30",
            "device_name": "SW-SSH-01"
        },
        backup=True,
        dry_run=True  # 强烈推荐先 Dry-Run
    )
    deploy_response = adapter.execute(deploy_request)
    print(f"Dry-Run 部署结果: {deploy_response}")
    # 预期返回: success=True, data={"status": "dry_run", "transport": "ssh", ...}

    # ============================================================
    # 示例 4: SSH 模式 - 部署（实际下发，需谨慎）
    # ============================================================
    print("\n[4] SSH 模式 - 实际部署（⚠️  生产环境慎用）")
    # 注意：SSH deploy 是简化实现，缺少：
    #   - DeploymentPlanner 的智能规划
    #   - 完整的幂等性保护（虽有简单比对）
    #   - 自动回滚
    # 如需完整功能，请使用 Console 模式 + DeploymentEngine

    # deploy_request_real = AgentRequest(
    #     action="deploy",
    #     device=DeviceInfo(host="192.168.1.10", ...),
    #     template="access_switch.j2",
    #     variables={...},
    #     backup=True,
    #     dry_run=False
    # )
    # deploy_response_real = adapter.execute(deploy_request_real)

    # ============================================================
    # 对比：Console vs SSH 模式
    # ============================================================
    print("\n" + "="*60)
    print("Console vs SSH 模式对比")
    print("="*60)
    print("""
Console 模式（推荐用于生产部署）:
  - 优点: 支持完整 DeploymentEngine（planner、幂等性、回滚）
  - 缺点: 需要物理串口连接

SSH 模式（推荐用于远程管理、快速操作）:
  - 优点: 无需串口，远程管理方便
  - 缺点: deploy 为简化实现，功能受限
  - 适用场景: backup、command、Dry-Run deploy

建议:
  - 日常运维（backup、command）→ SSH 模式
  - 生产部署（deploy）→ Console 模式（完整功能）
  - SSH deploy 前务必 Dry-Run 验证
""")


if __name__ == "__main__":
    main()
