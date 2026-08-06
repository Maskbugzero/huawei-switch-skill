#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: SSH batch backup / command (no real devices required if you only read the code).

Usage (with a real inventory):

  copy configs\\devices.example.yaml configs\\devices.yaml
  # edit passwords or use password_env

  .\\.venv\\Scripts\\python.exe examples\\09_ssh_batch.py
  .\\.venv\\Scripts\\python.exe -m src.ssh.batch -i configs/devices.yaml backup
"""

from __future__ import annotations

from pathlib import Path

from src.ssh.batch import BatchSSHManager


def main() -> None:
    inv = Path("configs/devices.yaml")
    if not inv.is_file():
        inv = Path("configs/devices.example.yaml")
        print(f"Using example inventory: {inv}")
        print("Copy to configs/devices.yaml for real runs.\n")

    # NOTE: example file has placeholder passwords — real connect will fail.
    # This example shows the API shape for batch management.
    try:
        mgr = BatchSSHManager.from_yaml(inv)
    except Exception as e:
        print(f"Load inventory failed: {e}")
        return

    print(f"Loaded {len(mgr.inventory.devices)} devices")
    print("API demo (will attempt SSH — expect failure with placeholders):\n")

    report = mgr.command_all("display version")
    print(report.summary())
    for r in report.results:
        print(f"  {r.name}: success={r.success} err={r.error}")


if __name__ == "__main__":
    main()
