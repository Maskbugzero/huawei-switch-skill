import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import tempfile
import os
from src.agent import AgentAdapter, AgentRequest, DeviceInfo

def test_validate_with_direct_content():
    print("=== 测试 1: 直接传入配置内容 ===")
    adapter = AgentAdapter()
    request = AgentRequest(
        action="validate",
        device=DeviceInfo(port="COM4", password="dummy"),
        variables={
            "before_config": "interface Vlanif10",
            "after_config": "interface Vlanif10\nip address 192.168.10.1 24",
            "expected": {"vlan": "10"}
        }
    )
    response = adapter.execute(request)
    print(f"Success: {response.success}")
    print(f"Report: {response.data.get('validation_report')}")
    assert response.success is True
    print("✅ 测试 1 通过\n")

def test_validate_with_file_paths():
    print("=== 测试 2: 通过文件路径传入配置 ===")
    # 创建临时文件
    with tempfile.TemporaryDirectory() as tmpdir:
        before_file = os.path.join(tmpdir, "before.txt")
        after_file = os.path.join(tmpdir, "after.txt")

        with open(before_file, "w", encoding="utf-8") as f:
            f.write("interface Vlanif20")

        with open(after_file, "w", encoding="utf-8") as f:
            f.write("interface Vlanif20\nip address 192.168.20.1 24")

        adapter = AgentAdapter()
        request = AgentRequest(
            action="validate",
            device=DeviceInfo(port="COM4", password="dummy"),
            variables={
                "before_config_path": before_file,
                "after_config_path": after_file,
                "expected": {"vlan": "20"}
            }
        )
        response = adapter.execute(request)
        print(f"Success: {response.success}")
        print(f"Report: {response.data.get('validation_report')}")
        assert response.success is True
        print("✅ 测试 2 通过\n")

def test_validate_skipped():
    print("=== 测试 3: 无配置时跳过 ===")
    adapter = AgentAdapter()
    request = AgentRequest(
        action="validate",
        device=DeviceInfo(port="COM4", password="dummy"),
        variables={}
    )
    response = adapter.execute(request)
    report = response.data.get("validation_report", {})
    print(f"Status: {report.get('status')}")
    assert report.get("status") == "skipped"
    print("✅ 测试 3 通过\n")

if __name__ == "__main__":
    print("开始验证 AgentAdapter.validate 新功能...\n")
    test_validate_with_direct_content()
    test_validate_with_file_paths()
    test_validate_skipped()
    print("🎉 所有验证测试通过！")