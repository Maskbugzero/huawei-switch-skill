#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S5735R Admin 配置部署脚本 - 针对 COM4 口
参考 D:\work\0731\S5735R admin.txt（多业务VLAN场景）
自动从 .txt 文件读取最新配置
自动备份 + 部署 + save
"""

import sys
import time
import argparse
from pathlib import Path

# 添加 skill 路径
sys.path.insert(0, str(Path(__file__).parent))

from src.console import Connection
from src.console.logger import get_logger
from src.backup import ConfigCollector, ConfigExporter
from src.command import CommandExecutor

logger = get_logger("deploy_admin_com4")


def load_config_from_txt(file_path: str) -> list:
    """从参考的 .txt 文件中加载配置命令"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {file_path}")

    lines = []
    started = False

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()

            # 跳过空行和纯注释行
            if not stripped or stripped.startswith("#"):
                continue

            # 找到 system-view 后开始记录
            if stripped == "system-view":
                started = True

            if started:
                lines.append(stripped)

    if not lines:
        raise ValueError(f"未在 {file_path} 中找到有效配置（缺少 system-view）")

    logger.info(f"从 {file_path} 加载了 {len(lines)} 行配置")
    return lines


def deploy_admin_to_com4(password: str, config_file: str, backup_first: bool = True):
    """部署 Admin 配置到 COM4（自动读取最新 .txt 文件）"""
    device_name = "S5735R-COM4-Admin"

    # 动态加载最新配置
    try:
        config_lines = load_config_from_txt(config_file)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return False

    logger.info("=== 开始 S5735R Admin 配置部署 (COM4) ===")
    logger.info(f"目标设备: {device_name}")
    logger.info(f"配置来源: {config_file} (自动读取最新版本)")

    try:
        # 重构：使用上下文管理器（自动 connect/disconnect，匹配 Connection 模式）
        # 核心逻辑可迁移至 DeploymentEngine（保留 [Y/N] + save 以兼容 txt 配置）
        logger.info("正在连接 COM4 ...")
        with Connection(port=port, password=password, timeout=60) as conn:
            logger.info("Console 连接成功")

            # 2. 备份（推荐）
            if backup_first:
                logger.info("执行配置备份...")
                collector = ConfigCollector(conn)
                old_config = collector.collect_current_config()
                exporter = ConfigExporter()
                backup_path = exporter.export_backup(device_name, {"display current-configuration": old_config})
                logger.info(f"备份已保存: {backup_path}")

            # 3. 部署配置（保留 executor 处理确认提示）
            logger.info(f"开始下发配置（共 {len(config_lines)} 行）...")

            executor = CommandExecutor(conn)

            for i, line in enumerate(config_lines, 1):
                line = line.strip()
                if not line:
                    continue

                logger.info(f"[{i}/{len(config_lines)}] 发送: {line}")

                try:
                    result = executor.send_command(line)

                    if result and ("[Y/N]" in result or "continue?" in result.lower() or "y/n" in result.lower()):
                        logger.info("检测到确认提示，自动发送 y")
                        executor.send_command("y")

                    time.sleep(0.3)

                except Exception as e:
                    logger.error(f"命令执行失败: {line} -> {e}")
                    continue

            logger.info("配置下发完成！")

            # 4. 最后执行 save
            logger.info("执行最终 save...")
            try:
                executor.send_command("save")
            except Exception:
                pass

            logger.info("=== 部署成功完成 ===")
            logger.info("请检查交换机状态（多业务VLAN + Admin 场景已配置）")
            return True

    except Exception as e:
        logger.error(f"部署失败: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="S5735R Admin 配置部署工具 (COM4) - 自动读取 .txt 文件"
    )
    parser.add_argument("--password", "-p", required=True, help="当前 Console 登录密码")
    parser.add_argument("--port", default="COM4", help="串口号 (默认: COM4)")
    parser.add_argument(
        "--config-dir",
        default=".",
        help="配置文件所在目录（相对路径推荐）"
    )
    parser.add_argument("--device-name", default="S5735R-COM4-Admin", help="设备名称")
    parser.add_argument(
        "--config-file",
        "-c",
        default="S5735R admin.txt",
        help="配置文件路径（默认: D:\\work\\0731\\S5735R admin.txt）"
    )
    parser.add_argument("--no-backup", action="store_true", help="跳过备份步骤")
    parser.add_argument("--yes", action="store_true", help="跳过二次确认")

    args = parser.parse_args()

    print("=" * 60)
    print("S5735R Admin 配置部署工具 (COM4)")
    print("配置内容自动从 .txt 文件读取（最新版本）")
    print("=" * 60)
    print()
    print(f"配置文件: {args.config_file}")
    print("警告：此操作将完全覆盖当前配置！")
    print()

    if not args.yes:
        confirm = input("确认开始部署？(yes/no): ").strip().lower()
        if confirm != "yes":
            print("已取消")
            sys.exit(0)

    success = deploy_admin_to_com4(
        password=args.password,
        config_file=args.config_file,
        backup_first=not args.no_backup
    )

    if success:
        print("\n部署成功！")
    else:
        print("\n部署失败，请检查日志和连接")
        sys.exit(1)
