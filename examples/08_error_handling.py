#!/usr/bin/env python3
"""
Skill Example 08: 错误处理与异常场景（推荐使用 AgentAdapter）

展示如何正确处理 AgentAdapter 调用中的各种错误场景。
这是生产环境健壮性的关键。

核心原则：
- 始终检查 response.success
- 通过 response.code 识别错误类型
- 通过 response.message 获取人类可读的错误信息
- 通过 response.error 获取详细错误信息（可选）
"""

from src.agent import AgentAdapter, AgentRequest, DeviceInfo
from src.agent.error_codes import APT001, APT002, CON003


def main():
    print("=== Skill Example: 错误处理与异常场景 ===")

    adapter = AgentAdapter()

    # ============================================================
    # 场景 1: 缺少必要参数（port/password）
    # ============================================================
    print("\n[场景 1] 缺少必要参数")
    invalid_request = AgentRequest(
        action="backup",
        device=DeviceInfo(port="COM4", password=""),  # 密码为空
        variables={"device_name": "SW-01"}
    )
    response = adapter.execute(invalid_request)
    if not response.success:
        print(f"  ❌ 失败: {response.message}")
        print(f"  错误码: {response.code}")  # APT001
        print(f"  预期: APT001 - 缺少必要的设备连接信息")

    # ============================================================
    # 场景 2: 不支持的操作
    # ============================================================
    print("\n[场景 2] 不支持的操作")
    unsupported_request = AgentRequest(
        action="reboot",  # 不支持的 action
        device=DeviceInfo(port="COM4", password="xxx"),
        variables={}
    )
    response = adapter.execute(unsupported_request)
    if not response.success:
        print(f"  ❌ 失败: {response.message}")
        print(f"  错误码: {response.code}")  # APT002
        print(f"  预期: APT002 - 不支持的操作")

    # ============================================================
    # 场景 3: SSH 认证失败
    # ============================================================
    print("\n[场景 3] SSH 认证失败（错误密码）")
    auth_fail_request = AgentRequest(
        action="command",
        device=DeviceInfo(
            host="192.168.1.10",
            port="192.168.1.10",
            username="admin",
            password="wrong_password",  # 错误密码
            port_number=22
        ),
        variables={"command": "display version"}
    )
    response = adapter.execute(auth_fail_request)
    if not response.success:
        print(f"  ❌ 失败: {response.message}")
        print(f"  错误码: {response.code}")  # CON003
        print(f"  详细错误: {response.error}")
        print(f"  预期: CON003 - SSH 认证失败或连接异常")

    # ============================================================
    # 场景 4: Console 连接失败（串口不存在或被占用）
    # ============================================================
    print("\n[场景 4] Console 连接失败（串口问题）")
    console_fail_request = AgentRequest(
        action="backup",
        device=DeviceInfo(port="COM999", password="xxx"),  # 不存在的串口
        variables={"device_name": "SW-01"}
    )
    response = adapter.execute(console_fail_request)
    if not response.success:
        print(f"  ❌ 失败: {response.message}")
        print(f"  错误码: {response.code}")  # CON003
        print(f"  提示: 检查串口号是否正确、串口是否被占用")

    # ============================================================
    # 场景 5: 模板不存在
    # ============================================================
    print("\n[场景 5] 模板不存在")
    template_fail_request = AgentRequest(
        action="deploy",
        device=DeviceInfo(port="COM4", password="xxx"),
        template="nonexistent_template.j2",  # 不存在的模板
        variables={"hostname": "SW-01"},
        backup=False
    )
    response = adapter.execute(template_fail_request)
    if not response.success:
        print(f"  ❌ 失败: {response.message}")
        print(f"  错误码: {response.code}")  # CON003（模板渲染异常）
        print(f"  提示: 检查模板文件名和 templates/ 目录")

    # ============================================================
    # 场景 6: 成功场景 - 如何正确处理响应
    # ============================================================
    print("\n[场景 6] 成功场景 - 正确处理响应")
    success_request = AgentRequest(
        action="command",
        device=DeviceInfo(port="COM4", password="your_password"),
        variables={"command": "display version"}
    )
    response = adapter.execute(success_request)
    if response.success:
        print(f"  ✅ 成功!")
        print(f"  数据: {response.data.get('output', 'N/A')[:100]}...")
    else:
        print(f"  ❌ 失败: {response.message}")

    # ============================================================
    # 最佳实践总结
    # ============================================================
    print("\n" + "="*60)
    print("错误处理最佳实践")
    print("="*60)
    print("""
1. 始终检查 response.success
   ```python
   response = adapter.execute(request)
   if response.success:
       # 处理成功
       print(response.data)
   else:
       # 处理失败
       print(f"错误: {response.message}")
   ```

2. 使用 response.code 识别错误类型
   - APT001: 缺少必要参数（port/password）
   - APT002: 不支持的操作
   - CON003: 连接/认证异常

3. 区分 response.message 和 response.error
   - message: 人类可读的简短描述
   - error: 详细的异常信息（可选）

4. SSH 模式下的特殊错误
   - 认证失败: 检查用户名/密码
   - 连接超时: 检查网络连通性和防火墙

5. 生产环境建议
   - 包装 AgentAdapter 调用，统一错误处理
   - 记录详细日志（含 response.code）
   - 对敏感操作（deploy）启用 dry_run 先行验证
""")


if __name__ == "__main__":
    main()
