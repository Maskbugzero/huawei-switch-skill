# -*- coding: utf-8 -*-
"""ConfigExporter 路径安全测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.backup.exporter import ConfigExporter


def test_export_backup_rejects_path_traversal(tmp_path: Path):
    exporter = ConfigExporter(base_dir=str(tmp_path / "backups"))
    with pytest.raises(ValueError, match="device_name|invalid"):
        exporter.export_backup("../../evil", {"display current-configuration": "cfg"})


def test_export_backup_rejects_slash_in_name(tmp_path: Path):
    exporter = ConfigExporter(base_dir=str(tmp_path / "backups"))
    with pytest.raises(ValueError):
        exporter.export_backup("sw/../x", {"display current-configuration": "cfg"})


def test_export_backup_accepts_safe_name(tmp_path: Path):
    exporter = ConfigExporter(base_dir=str(tmp_path / "backups"))
    path = exporter.export_backup("SW-01", {"display current-configuration": "sysname X\n"})
    assert path.exists()
    assert "SW-01" in path.parts
    # 必须落在 base_dir 下
    path.resolve().relative_to((tmp_path / "backups").resolve())
