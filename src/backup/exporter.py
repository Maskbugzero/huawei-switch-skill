# -*- coding: utf-8 -*-
"""
配置导出模块 - Exporter。

负责将采集到的配置写入文件系统（按时间戳目录结构备份）。
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.console.logger import get_logger

logger = get_logger("backup.exporter")


class ConfigExporter:
    """配置导出器。"""

    def __init__(self, base_dir: str = "backups") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def export_backup(
        self,
        device_name: str,
        collected_data: Dict[str, str],
        metadata: Optional[Dict] = None,
    ) -> Path:
        """
        导出备份到指定目录结构：
        backups/设备名/YYYYMMDD-HHMMSS/
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = self.base_dir / device_name / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"导出备份到: {backup_dir}")

        # 1. 写入主配置文件
        config_file = backup_dir / "current-configuration.txt"
        if "display current-configuration" in collected_data:
            config_file.write_text(
                collected_data["display current-configuration"],
                encoding="utf-8"
            )
            logger.info(f"已保存配置文件: {config_file}")

        # 2. 写入各命令输出
        for cmd, output in collected_data.items():
            safe_name = cmd.replace(" ", "_").replace("-", "_") + ".txt"
            (backup_dir / safe_name).write_text(output, encoding="utf-8")

        # 3. 写入元数据
        meta = metadata or {}
        meta.update({
            "timestamp": timestamp,
            "device_name": device_name,
            "backup_time": datetime.now().isoformat(),
            "commands_collected": list(collected_data.keys()),
        })
        meta_file = backup_dir / "metadata.json"
        meta_file.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # 4. 写入设备信息摘要
        info_file = backup_dir / "device-info.txt"
        info_content = "\n".join(
            [f"{k}: {v[:200]}..." if len(str(v)) > 200 else f"{k}: {v}"
             for k, v in collected_data.items()]
        )
        info_file.write_text(info_content, encoding="utf-8")

        logger.info(f"备份完成: {backup_dir}")
        return backup_dir

    def list_backups(self, device_name: Optional[str] = None) -> List[Path]:
        """列出所有备份目录。"""
        if device_name:
            device_dir = self.base_dir / device_name
            if device_dir.exists():
                return sorted(device_dir.iterdir(), reverse=True)
            return []
        return sorted(self.base_dir.rglob("*"), reverse=True)
