# -*- coding: utf-8 -*-
"""
回滚模块。
"""

from __future__ import annotations

from src.console.logger import get_logger

logger = get_logger("deploy.rollback")


class RollbackManager:
    """配置回滚管理器。"""

    def rollback(self, connection, backup_path: str) -> bool:
        """从备份恢复配置（基础实现）。

        注意：完整回滚应结合 DeploymentEngine + 备份文件。
        当前版本为占位实现，后续可扩展为：
        - 读取备份目录中的 current-configuration.txt
        - 逐行下发恢复
        """
        logger.warning("回滚功能待完善（当前为占位实现）")
        # TODO: 实现真实回滚逻辑
        return True
