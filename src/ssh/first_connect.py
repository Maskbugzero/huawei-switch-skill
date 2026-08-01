# -*- coding: utf-8 -*-
"""
SSH 首次连接 + 强制修改密码模块。

参考实机使用脚本封装，支持：
- 自动接受主机指纹
- 处理“需要修改密码”交互流程
- 改密成功后重新验证
- 改密后自动备份配置（可选）
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import paramiko
from paramiko import SSHClient, AutoAddPolicy
from netmiko import ConnectHandler

from src.console.logger import get_logger

logger = get_logger("ssh.first_connect")


@dataclass
class SSHDevice:
    """SSH 设备连接信息。"""
    host: str
    username: str = "admin"
    old_password: str = ""
    new_password: str = ""
    port: int = 22


class SSHFirstConnect:
    """SSH 首次连接 + 强制改密工具。"""

    def __init__(self, device: SSHDevice, timeout: int = 15):
        self.device = device
        self.timeout = timeout
        self.client: Optional[SSHClient] = None

    def _wait_for_output(self, shell, timeout: int = 8) -> str:
        """等待 shell 输出直到出现提示符。"""
        output = ""
        end_time = time.time() + timeout
        prompts = [">", "#", "]:", "password:", "Password:", "continue?"]

        while time.time() < end_time:
            if shell.recv_ready():
                chunk = shell.recv(4096).decode("utf-8", errors="ignore")
                output += chunk
                if any(p in output for p in prompts):
                    break
            time.sleep(0.2)
        return output

    def change_password_and_verify(self) -> bool:
        """
        执行 SSH 首次连接 + 改密 + 验证流程。

        Returns:
            bool: 改密并验证是否成功
        """
        print(f"\n=== 连接交换机 {self.device.host} ===")
        print(f"用户名: {self.device.username}")
        logger.debug("初始密码和新密码已设置（已掩码，不在日志中明文显示）\n")

        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy())

        try:
            # 第一次连接
            self.client.connect(
                hostname=self.device.host,
                port=self.device.port,
                username=self.device.username,
                password=self.device.old_password,
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False,
            )
            print("[+] 第一次 SSH 连接成功")

            shell = self.client.invoke_shell()
            shell.settimeout(20)
            time.sleep(1)

            initial_output = self._wait_for_output(shell, timeout=6)
            print("[*] 初始输出:\n" + initial_output)

            # 判断是否进入改密流程
            if "The password needs to be changed" in initial_output or "Continue? [Y/N]" in initial_output:
                print("\n[!] 检测到需要修改密码，开始处理...")

                # 确认改密
                shell.send("y\n")
                time.sleep(1.5)
                output = self._wait_for_output(shell)
                print(output)

                # 输入旧密码
                print("[*] 输入旧密码...")
                shell.send(self.device.old_password + "\n")
                time.sleep(1.5)
                output = self._wait_for_output(shell)
                print(output)

                # 输入新密码
                print("[*] 输入新密码...")
                logger.debug("新密码已发送（已掩码）")
                shell.send(self.device.new_password + "\n")
                time.sleep(1.5)
                output = self._wait_for_output(shell)
                print(output)

                # 确认新密码
                print("[*] 再次确认新密码...")
                shell.send(self.device.new_password + "\n")
                time.sleep(2)
                output = self._wait_for_output(shell, timeout=10)
                print(output)

                if "changed successfully" in output.lower():
                    print("\n[+] 密码修改成功！")
                else:
                    print("\n[-] 密码修改可能未成功，请检查输出。")

                shell.close()
                self.client.close()
                time.sleep(1)

                # 用新密码重新登录验证
                return self._verify_with_new_password()

            else:
                print("[*] 未检测到强制改密提示，可能已经修改过密码。")
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
        print("\n=== 使用新密码重新登录验证 ===")
        client2 = SSHClient()
        client2.set_missing_host_key_policy(AutoAddPolicy())

        try:
            client2.connect(
                hostname=self.device.host,
                port=self.device.port,
                username=self.device.username,
                password=self.device.new_password,
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False,
            )
            print("[+] 使用新密码登录成功！")
            shell2 = client2.invoke_shell()
            time.sleep(1)
            verify_output = self._wait_for_output(shell2, timeout=5)
            print(verify_output)

            print("\n[成功] 新密码已生效，可以正常使用。")

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
                "password": self.device.new_password,
                "port": self.device.port,
            }
            conn = ConnectHandler(**device)
            conn.send_command("screen-length 0 temporary")
            config = conn.send_command("display current-configuration", read_timeout=120)

            exporter = ConfigExporter()
            backup_path = exporter.export_backup(
                f"ssh-{self.device.host}", {"display current-configuration": config}
            )
            print(f"[+] 配置备份已保存: {backup_path}")
            conn.disconnect()
            return True

        except Exception as e:
            logger.warning(f"备份过程中出现错误: {e}")
            return False
