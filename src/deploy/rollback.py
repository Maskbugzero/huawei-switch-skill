# -*- coding: utf-8 -*-
"""
回滚模块。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from src.console import Connection
from src.console.logger import get_logger

logger = get_logger("deploy.rollback")


@dataclass
class RollbackReport:
    """回滚执行报告。"""
    success: bool
    success_count: int = 0
    failed_count: int = 0
    errors: List[str] = field(default_factory=list)
    backup_path: str = ""
    dry_run: bool = False

    def summary(self) -> str:
        status = "【Dry Run】" if self.dry_run else ""
        return (f"{status}回滚完成 | 成功: {self.success_count} | "
                f"失败: {self.failed_count} | 备份: {self.backup_path}")


class RollbackManager:
    """配置回滚管理器。"""

    def rollback(
        self,
        connection: Connection,
        backup_path: str,
        config_file: str = "current-configuration.txt",
        dry_run: bool = False,
    ) -> RollbackReport:
        """
        从备份恢复配置。

        Args:
            connection: 已建立的 Connection 对象
            backup_path: 备份目录路径（如 backups/SW-01/20260801-143022）
            config_file: 备份中的配置文件名（默认 current-configuration.txt）
            dry_run: 是否仅模拟执行（不真正下发命令）

        Returns:
            RollbackReport: 详细的回滚报告
        """
        report = RollbackReport(
            success=True,
            backup_path=backup_path,
            dry_run=dry_run
        )

        backup_dir = Path(backup_path)
        config_file_path = backup_dir / config_file

        if not config_file_path.exists():
            msg = f"备份文件不存在: {config_file_path}"
            logger.error(msg)
            report.success = False
            report.errors.append(msg)
            return report

        try:
            config_text = config_file_path.read_text(encoding="utf-8")
            logger.info(f"开始从备份恢复配置: {config_file_path}")
            logger.info(f"配置大小: {len(config_text)} 字符")

            for line in config_text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if dry_run:
                    logger.info(f"[DryRun] 将执行: {line}")
                    report.success_count += 1
                    continue

                try:
                    connection.send_command(line)
                    report.success_count += 1
                except Exception as e:
                    error_msg = f"命令执行失败: {line} -> {e}"
                    logger.warning(error_msg)
                    report.failed_count += 1
                    report.errors.append(error_msg)

            if report.failed_count > 0:
                report.success = False

            logger.info(report.summary())
            return report

        except Exception as e:
            logger.error(f"回滚过程发生异常: {e}")
            report.success = False
            report.errors.append(str(e))
            return report

