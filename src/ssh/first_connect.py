# -*- coding: utf-8 -*-
"""
SSH 首次连接 + 强制修改密码模块。

参考实机使用脚本封装，支持：
- 主机密钥校验（默认拒绝未知；显式 accept_unknown_host_key 才 AutoAdd）
- 处理“需要修改密码”交互流程
- 改密成功后重新验证
- 改密后自动备份配置（可选）
"""

from __future__ import annotations

import re
import time
from typing import Optional

import paramiko
from paramiko import SSHClient
from netmiko import ConnectHandler
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from src.console.logger import get_logger
from src.ssh.hostkeys import configure_paramiko_client, netmiko_hostkey_kwargs, resolve_accept_unknown

logger = get_logger("ssh.first_connect")


class SSHChangePasswordResult(BaseModel):
    """SSH 改密结果。"""
    model_config = ConfigDict(extra="ignore")

    success: bool = Field(..., description="Whether password change succeeded")
    message: str = Field(default="", description="Result message")
    backup_path: Optional[str] = Field(default=None, description="Path to config backup if successful")


class SSHDevice(BaseModel):
    """SSH 设备连接信息。"""
    model_config = ConfigDict(extra="ignore")

    host: str = Field(..., description="SSH host address")
    username: str = Field(default="admin", description="SSH username")
    old_password: SecretStr = Field(default="", description="Old password for first connect")
    new_password: SecretStr = Field(default="", description="New password to set")
    port: int = Field(default=22, description="SSH port")
    accept_unknown_host_key: bool = Field(
        default=False,
        description="If True, auto-add unknown host keys (MITM risk). Default rejects unknown.",
    )


class SSHFirstConnect:
    """
    SSH 首次连接 + 强制改密工具（独立特殊场景）。

    注意：此模块与 AgentAdapter 中的常规 SSH 支持（netmiko）为两条并行路径。
    - SSHFirstConnect：仅用于设备首次 SSH 登录时强制修改密码。
    - AgentAdapter SSH 路径：用于常规 backup/command/deploy 操作。
    推荐大多数场景使用 Console + AgentAdapter。
    """

    def __init__(self, device: SSHDevice, timeout: int = 15):
        self.device = device
        self.timeout = timeout
        self.client: Optional[SSHClient] = None

    @property
    def is_connected(self) -> bool:
        """检查是否已连接。"""
        return self.client is not None and self.client.get_transport() is not None and self.client.get_transport().is_active()

    def get_connection_info(self) -> dict:
        """返回连接信息摘要。"""
        return {
            "host": self.device.host,
            "port": self.device.port,
            "username": self.device.username,
            "connected": self.is_connected
        }

    def get_summary(self) -> str:
        """返回操作摘要。"""
        return f"SSHFirstConnect for {self.device.host}:{self.device.port}"

    def _wait_for_output(self, shell, timeout: int = 8, custom_prompts: Optional[list] = None) -> tuple[str, bool]:
        """
        等待 shell 输出直到出现提示符或超时。

        Returns:
            tuple[str, bool]: (收集到的输出内容, 是否超时)
        """
        output = ""
        end_time = time.time() + timeout

        # 正则提示符模式（匹配行尾的典型 CLI 提示符）
        # 这些模式专门为华为 VRP CLI 设计
        prompt_patterns = [
            r'>\s*$',                    # 用户视图提示符 (例如 <SW-01>)
            r'#\s*$',                    # 某些 CLI 的系统视图提示符（兼容）
            r'\]\s*$',                   # 系统视图/交互提示符结尾 (例如 [SW-01], Continue? [Y/N])
            r'[Pp]assword[:：]\s*$',     # 密码提示
            r'[Cc]ontinue\?\s*\[Y/N\]',  # Continue 确认提示
        ]

        # 如果有自定义提示符，添加为字面匹配模式
        if custom_prompts:
            for p in custom_prompts:
                # 转义特殊字符并添加行尾锚点
                escaped = re.escape(p) + r'\s*$'
                if escaped not in prompt_patterns:
                    prompt_patterns.append(escaped)

        while time.time() < end_time:
            try:
                if shell.recv_ready():
                    chunk = shell.recv(4096).decode("utf-8", errors="ignore")
                    output += chunk
                    # 使用正则匹配提示符（多行模式，匹配行尾）
                    for pattern in prompt_patterns:
                        if re.search(pattern, output, re.MULTILINE | re.IGNORECASE):
                            return output, False  # 未超时
            except Exception as e:
                logger.warning(f"_wait_for_output 接收数据异常: {e}")
                break
            time.sleep(0.2)

        # 超时处理
        timed_out = time.time() >= end_time
        if timed_out:
            logger.warning(f"_wait_for_output 超时（{timeout}s），已收集 {len(output)} 字符")
            if output:
                logger.debug(f"超时时的部分输出: {output[-200:]}")

        return output, timed_out

    def change_password_and_verify(self) -> bool:
        """
        执行 SSH 首次连接 + 改密 + 验证流程。

        Returns:
            bool: 改密并验证是否成功
        """
        logger.info(f"=== 连接交换机 {self.device.host} ===")
        logger.info(f"用户名: {self.device.username}")

        self.client = SSHClient()
        accept = resolve_accept_unknown(self.device.accept_unknown_host_key)
        configure_paramiko_client(self.client, accept_unknown=accept)

        try:
            # 第一次连接
            self.client.connect(
                hostname=self.device.host,
                port=self.device.port,
                username=self.device.username,
                password=self.device.old_password.get_secret_value(),
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False,
            )
            logger.info("第一次 SSH 连接成功")

            shell = self.client.invoke_shell()
            shell.settimeout(20)
            time.sleep(1)

            initial_output, _ = self._wait_for_output(shell, timeout=6)
            logger.debug("初始输出:\n" + initial_output)

            # 判断是否进入改密流程
            if "The password needs to be changed" in initial_output or "Continue? [Y/N]" in initial_output:
                logger.info("检测到需要修改密码，开始处理...")

                # 确认改密
                shell.send("y\n")
                time.sleep(1.5)
                output, _ = self._wait_for_output(shell)
                logger.debug("改密确认输出:\n" + output)

                # 输入旧密码
                logger.info("输入旧密码...")
                shell.send(self.device.old_password.get_secret_value() + "\n")
                time.sleep(1.5)
                output, _ = self._wait_for_output(shell)
                logger.debug("旧密码输入后输出:\n" + output)

                # 输入新密码
                logger.info("输入新密码...")
                shell.send(self.device.new_password.get_secret_value() + "\n")
                time.sleep(1.5)
                output, _ = self._wait_for_output(shell)
                logger.debug("新密码输入后输出:\n" + output)

                # 确认新密码
                logger.info("再次确认新密码...")
                shell.send(self.device.new_password.get_secret_value() + "\n")
                time.sleep(2)
                output, _ = self._wait_for_output(shell, timeout=10)
                logger.debug("新密码确认后输出:\n" + output)

                if "changed successfully" in output.lower():
                    logger.info("密码修改成功！")
                else:
                    logger.warning("密码修改可能未成功，请检查输出。")

                shell.close()
                self.client.close()
                time.sleep(1)

                # 用新密码重新登录验证
                return self._verify_with_new_password()

            else:
                logger.info("未检测到强制改密提示，可能已经修改过密码。")
                shell.close()
                self.client.close()
                return True

        except paramiko.AuthenticationException:
            logger.error("认证失败，请检查初始密码是否正确。")
            return False
        except Exception as e:
            logger.error(f"发生错误: {e}")
            return False

    def _verify_with_new_password(self) -> bool:
        """使用新密码重新登录验证。"""
        logger.info("=== 使用新密码重新登录验证 ===")
        client2 = SSHClient()
        accept = resolve_accept_unknown(self.device.accept_unknown_host_key)
        configure_paramiko_client(client2, accept_unknown=accept)

        try:
            client2.connect(
                hostname=self.device.host,
                port=self.device.port,
                username=self.device.username,
                password=self.device.new_password.get_secret_value(),
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False,
            )
            logger.info("使用新密码登录成功！")
            shell2 = client2.invoke_shell()
            time.sleep(1)
            verify_output, _ = self._wait_for_output(shell2, timeout=5)
            logger.debug("验证输出:\n" + verify_output)

            logger.info("新密码已生效，可以正常使用。")

            # 改密成功后自动备份配置（使用 Netmiko）
            self._backup_config_after_change(client2)

            shell2.close()
            client2.close()
            return True

        except Exception as e:
            logger.error(f"使用新密码重新登录失败: {e}")
            return False

    def _backup_config_after_change(self, client) -> bool:
        """改密成功后使用 Netmiko 进行配置备份。"""
        try:
            from src.backup import ConfigCollector, ConfigExporter
            from src.console import Connection  # 这里可以后续替换为 SSHTransport

            # 暂时使用 Netmiko 直接备份（与原脚本一致）
            device = {
                "device_type": "huawei_vrp",
                "host": self.device.host,
                "username": self.device.username,
                "password": self.device.new_password.get_secret_value(),
                "port": self.device.port,
                **netmiko_hostkey_kwargs(
                    accept_unknown=self.device.accept_unknown_host_key
                ),
            }
            conn = ConnectHandler(**device)
            conn.send_command("screen-length 0 temporary")
            config = conn.send_command("display current-configuration", read_timeout=120)

            exporter = ConfigExporter()
            backup_path = exporter.export_backup(
                f"ssh-{self.device.host}", {"display current-configuration": config}
            )
            logger.info(f"配置备份已保存: {backup_path}")
            conn.disconnect()
            return True

        except Exception as e:
            logger.warning(f"备份过程中出现错误: {e}")
            return False
