#!/usr/bin/env python3
"""
Skill Example 02: 一键配置备份

展示如何使用 Skill 进行配置备份和归档。
"""

from src.console import Connection
from src.backup import ConfigCollector, ConfigExporter

def main():
    print("=== Skill Example: 配置备份 ===")

    device_name = "SW-01"

    with Connection(port="COM4", password="your_password") as conn:
        # 采集配置
        collector = ConfigCollector(conn)
        config_data = collector.collect_all()

        # 导出备份
        exporter = ConfigExporter()
        backup_path = exporter.export_backup(device_name, config_data)

        print(f"备份完成！保存路径: {backup_path}")
        print("包含文件：current-configuration.txt、version.txt、vlan.txt 等")

if __name__ == "__main__":
    main()
