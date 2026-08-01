# -*- coding: utf-8 -*-
"""
回滚模块。
"""

from __future__ import annotations

from pathlib import Path

from src.console import Connection
from src.console.logger import get_logger

logger = get_logger("deploy.rollback")


class RollbackManager:
    """配置回滚管理器。"""

    def rollback(
        self,
        connection: Connection,
        backup_path: str,
        config_file: str = "current-configuration.txt",
    ) -> bool:
        """
        从备份恢复配置。

        Args:
            connection: 已建立的 Connection 对象
            backup_path: 备份目录路径（如 backups/SW-01/20260801-143022）
            config_file: 备份中的配置文件名（默认 current-configuration.txt）

        Returns:
            bool: 回滚是否成功
        """
        backup_dir = Path(backup_path)
        config_file_path = backup_dir / config_file

        if not config_file_path.exists():
            logger.error(f"备份文件不存在: {config_file_path}")
            return False

        try:
            config_text = config_file_path.read_text(encoding="utf-8")
            logger.info(f"开始从备份恢复配置: {config_file_path}")
            logger.info(f"配置大小: {len(config_text)} 字符")

            success_count = 0
            failed_count = 0

            for line in config_text.splitlines():
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith("#"):
                    continue

                try:
                    connection.send_command(line)
                    success_count += 1
                except Exception as e:
                    logger.warning(f"回滚命令执行失败: {line} -> {e}")
                    failed_count += 1

            logger.info(f"回滚完成: 成功 {success_count} 条，失败 {failed_count} 条")
            return failed_count == 0

        except Exception as e:
            logger.error(f"回滚过程发生异常: {e}")
            return False

