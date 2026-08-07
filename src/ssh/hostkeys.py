# -*- coding: utf-8 -*-
"""
SSH 主机密钥策略。

默认场景：机房/新开箱交换机，**自动接受未知主机密钥**（AutoAdd）。
若需严格校验，设置：
  - DeviceInfo/SSHDevice(accept_unknown_host_key=False)
  - 或环境变量 HUAWEI_SSH_STRICT=1
  - 或 HUAWEI_SSH_ACCEPT_UNKNOWN=0
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from paramiko import AutoAddPolicy, RejectPolicy, SSHClient
from paramiko.client import MissingHostKeyPolicy

from src.console.logger import get_logger

logger = get_logger("ssh.hostkeys")

_DEFAULT_KNOWN_HOSTS = Path.home() / ".ssh" / "known_hosts"


def resolve_accept_unknown(explicit: Optional[bool] = None) -> bool:
    """
    是否接受未知 host key。

    优先级：显式参数 > 环境变量 > 默认 True（新机器友好）。
    """
    if explicit is not None:
        return bool(explicit)

    strict = os.environ.get("HUAWEI_SSH_STRICT", "").strip().lower()
    if strict in {"1", "true", "yes", "on"}:
        return False

    env = os.environ.get("HUAWEI_SSH_ACCEPT_UNKNOWN", "").strip().lower()
    if env in {"0", "false", "no", "off"}:
        return False
    if env in {"1", "true", "yes", "on"}:
        return True

    # 默认：新开箱/确认设备，直接接受
    return True


def resolve_known_hosts_path(path: Optional[Union[str, Path]] = None) -> Path:
    if path:
        return Path(path).expanduser()
    env = os.environ.get("HUAWEI_SSH_KNOWN_HOSTS", "").strip()
    if env:
        return Path(env).expanduser()
    return _DEFAULT_KNOWN_HOSTS


def host_key_policy(accept_unknown: bool = True) -> MissingHostKeyPolicy:
    if accept_unknown:
        logger.debug("SSH host key policy: AutoAdd (accept unknown)")
        return AutoAddPolicy()
    logger.info("SSH host key policy: Reject unknown keys (strict)")
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
        try:
            kh.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    return kh


def configure_paramiko_client(
    client: SSHClient,
    *,
    accept_unknown: bool = True,
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

    - 默认 accept_unknown=True => ssh_strict=False (AutoAdd)
    - accept_unknown=False => ssh_strict=True (Reject)
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
