# -*- coding: utf-8 -*-
"""
SSH 主机密钥策略。

默认拒绝未知主机密钥（防 MITM）；仅在显式 accept_unknown_host_key=True
或环境变量 HUAWEI_SSH_ACCEPT_UNKNOWN=1 时自动添加。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import paramiko
from paramiko import AutoAddPolicy, RejectPolicy, SSHClient
from paramiko.client import MissingHostKeyPolicy

from src.console.logger import get_logger

logger = get_logger("ssh.hostkeys")

_DEFAULT_KNOWN_HOSTS = Path.home() / ".ssh" / "known_hosts"


def resolve_accept_unknown(explicit: Optional[bool] = None) -> bool:
    if explicit is not None:
        return bool(explicit)
    env = os.environ.get("HUAWEI_SSH_ACCEPT_UNKNOWN", "").strip().lower()
    return env in {"1", "true", "yes", "on"}


def resolve_known_hosts_path(path: Optional[Union[str, Path]] = None) -> Path:
    if path:
        return Path(path).expanduser()
    env = os.environ.get("HUAWEI_SSH_KNOWN_HOSTS", "").strip()
    if env:
        return Path(env).expanduser()
    return _DEFAULT_KNOWN_HOSTS


def host_key_policy(accept_unknown: bool = False) -> MissingHostKeyPolicy:
    if accept_unknown:
        logger.warning(
            "SSH accept_unknown_host_key=True: unknown host keys will be auto-added (MITM risk)"
        )
        return AutoAddPolicy()
    return RejectPolicy()


def load_host_keys(client: SSHClient, known_hosts: Optional[Union[str, Path]] = None) -> Path:
    """加载 known_hosts；文件不存在则确保父目录可写。"""
    kh = resolve_known_hosts_path(known_hosts)
    try:
        client.load_system_host_keys()
    except Exception as e:
        logger.debug(f"load_system_host_keys: {e}")
    if kh.is_file():
        try:
            client.load_host_keys(str(kh))
            logger.debug(f"loaded host keys from {kh}")
        except Exception as e:
            logger.warning(f"failed to load host keys {kh}: {e}")
    else:
        # 确保目录存在，便于 AutoAdd 时写入
        try:
            kh.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    return kh


def configure_paramiko_client(
    client: SSHClient,
    *,
    accept_unknown: bool = False,
    known_hosts: Optional[Union[str, Path]] = None,
) -> Path:
    kh = load_host_keys(client, known_hosts)
    client.set_missing_host_key_policy(host_key_policy(accept_unknown))
    return kh


def netmiko_hostkey_kwargs(
    *,
    accept_unknown: Optional[bool] = None,
    known_hosts: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    供 netmiko ConnectHandler 使用的主机密钥相关参数。

    - ssh_strict=True  => RejectPolicy（默认）
    - ssh_strict=False => AutoAddPolicy
    - system_host_keys=True 加载系统 known_hosts
    - alt_key_file 指向项目/用户 known_hosts（若存在）
    """
    accept = resolve_accept_unknown(accept_unknown)
    kh = resolve_known_hosts_path(known_hosts)
    kwargs: Dict[str, Any] = {
        "ssh_strict": not accept,
        "system_host_keys": True,
    }
    if kh.is_file():
        kwargs["alt_host_keys"] = True
        kwargs["alt_key_file"] = str(kh)
    return kwargs
