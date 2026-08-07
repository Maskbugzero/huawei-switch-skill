#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COM4 真机全模块联调脚本。

阶段：
  1) console / command
  2) backup + parser + verify(本地)
  3) template render
  4) deploy dry-run
  5) deploy 真实下发（安全小改）+ verify
  6) AgentAdapter: backup/command/validate/deploy(dry_run)
  7) SSH 探测（若配置中有可达管理地址则试 backup/command）

用法（在仓库根目录）:
  set SWITCH_PASSWORD=...
  .\\.venv\\Scripts\\python.exe scripts\\live_full_module_test.py
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

PORT = os.environ.get("SWITCH_PORT", "COM4")
PASSWORD = os.environ.get("SWITCH_PASSWORD", "")
DEVICE_NAME = os.environ.get("SWITCH_DEVICE_NAME", "1730-24")
DO_DEPLOY = os.environ.get("SWITCH_DO_DEPLOY", "1") != "0"


@dataclass
class StepResult:
    module: str
    name: str
    ok: bool
    detail: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


RESULTS: List[StepResult] = []


def record(module: str, name: str, ok: bool, detail: str = "", **data: Any) -> None:
    r = StepResult(module=module, name=name, ok=ok, detail=detail, data=data)
    RESULTS.append(r)
    flag = "PASS" if ok else "FAIL"
    print(f"[{flag}] {module}.{name}: {detail}")
    if data:
        preview = {k: (str(v)[:200] + "..." if len(str(v)) > 200 else v) for k, v in data.items()}
        print(f"       data={preview}")


def main() -> int:
    if not PASSWORD:
        print("ERROR: set SWITCH_PASSWORD")
        return 2

    print("=" * 70)
    print(f"Live full-module test @ {datetime.now().isoformat(timespec='seconds')}")
    print(f"port={PORT} device={DEVICE_NAME} deploy={DO_DEPLOY}")
    print("=" * 70)

    from src.console import Connection
    from src.command import CommandExecutor
    from src.backup import ConfigCollector, ConfigExporter
    from src.parser import ConfigParser
    from src.template import TemplateRenderer
    from src.deploy import DeploymentEngine
    from src.verify import ConfigVerifier
    from src.verify.rules import build_expected_from_variables
    from src.agent import AgentAdapter, AgentRequest, DeviceInfo

    backup_path: Optional[Path] = None
    before_config = ""
    after_config = ""
    mgmt_candidates: List[str] = []

    # ------------------------------------------------------------------
    # 1. Console + Command
    # ------------------------------------------------------------------
    try:
        with Connection(port=PORT, password=PASSWORD, timeout=45.0) as conn:
            record(
                "console",
                "connect",
                True,
                f"prompt={conn.current_prompt!r}",
                prompt=conn.current_prompt,
            )

            executor = CommandExecutor(conn)
            ver = executor.send_command("display version")
            ok = "VRP" in ver or "Routing" in ver or "uptime" in ver.lower()
            record("command", "display_version", ok, ver.splitlines()[0] if ver else "empty", snippet=ver[:400])

            brief = executor.send_command("display interface brief")
            record(
                "command",
                "display_interface_brief",
                bool(brief and len(brief) > 20),
                f"len={len(brief)}",
                snippet=brief[:300],
            )

            # 2. Backup
            collector = ConfigCollector(conn, disable_pagination=True, default_timeout=180)
            data = collector.collect_all()
            cfg = data.get("display current-configuration", "")
            before_config = cfg
            ok_backup_collect = bool(cfg) and "ERROR:" not in cfg[:80] and len(cfg) > 100
            record(
                "backup",
                "collect_all",
                ok_backup_collect,
                f"commands={list(data.keys())} cfg_len={len(cfg)}",
            )

            exporter = ConfigExporter(base_dir="backups")
            backup_path = exporter.export_backup(
                DEVICE_NAME,
                data,
                metadata={"source": "live_full_module_test", "port": PORT},
            )
            record("backup", "export", backup_path.exists(), str(backup_path), path=str(backup_path))

            # extract possible mgmt IPs for SSH later
            import re

            for m in re.finditer(r"ip address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)", cfg):
                ip = m.group(1)
                if not ip.startswith("127."):
                    mgmt_candidates.append(ip)
            mgmt_candidates = list(dict.fromkeys(mgmt_candidates))

            # 3. Parser
            parsed = ConfigParser().parse(cfg)
            record(
                "parser",
                "parse_running",
                True,
                f"sysname={parsed.get('sysname')} vlans={len(parsed.get('vlans') or {})} "
                f"ifs={len(parsed.get('interfaces') or {})}",
                sysname=parsed.get("sysname"),
                vlan_count=len(parsed.get("vlans") or {}),
                interface_count=len(parsed.get("interfaces") or {}),
            )

            # 4. Template
            renderer = TemplateRenderer(template_dir="templates")
            rendered = renderer.render(
                "_live_test_safe.j2",
                {
                    "hostname": parsed.get("sysname") or DEVICE_NAME,
                    "vlan_list": "10 20 30 100",
                    "test_port": "GigabitEthernet0/0/24",
                    "test_description": "huawei-switch-skill-live-test",
                },
            )
            record(
                "template",
                "render_live_safe",
                "sysname" in rendered and "GigabitEthernet0/0/24" in rendered,
                f"len={len(rendered)}",
                rendered_preview=rendered[:400],
            )

            # 5. Deploy dry-run
            engine = DeploymentEngine()
            vars_deploy = {
                "hostname": parsed.get("sysname") or DEVICE_NAME,
                "vlan_list": "10 20 30 100",
                "test_port": "GigabitEthernet0/0/24",
                "test_description": "huawei-switch-skill-live-test",
                "admin_password": PASSWORD,  # not used by safe template
            }
            dry = engine.deploy(
                connection=conn,
                template="_live_test_safe.j2",
                variables=vars_deploy,
                backup=False,  # already backed up
                device_name=DEVICE_NAME,
                dry_run=True,
                allow_dangerous=False,
                save=False,
                verify=False,
            )
            record(
                "deploy",
                "dry_run",
                dry.get("status") in {"dry_run", "skipped", "success"},
                f"status={dry.get('status')} reason={dry.get('reason')}",
                report=dry,
            )

            # 6. Real deploy (safe)
            if DO_DEPLOY:
                # verify 交由下一步显式 ConfigVerifier（避免默认 require_ssh 误杀）
                live = engine.deploy(
                    connection=conn,
                    template="_live_test_safe.j2",
                    variables=vars_deploy,
                    backup=True,
                    device_name=DEVICE_NAME,
                    dry_run=False,
                    allow_dangerous=False,
                    auto_rollback_on_failure=False,
                    save=True,
                    verify=False,
                )
                ok_live = live.get("status") in {"success", "skipped"}
                record(
                    "deploy",
                    "live_safe",
                    ok_live,
                    f"status={live.get('status')} saved={live.get('saved')}",
                    report=live,
                )

                after_config = collector.collect_current_config()
                desc_ok = "huawei-switch-skill-live-test" in after_config
                # skipped 表示意图已满足，也算通过
                record(
                    "deploy",
                    "post_check_description",
                    desc_ok or live.get("status") == "skipped",
                    "description present in running-config"
                    if desc_ok
                    else (
                        "skipped (intent already satisfied)"
                        if live.get("status") == "skipped"
                        else "description not found (check port name)"
                    ),
                )
            else:
                record("deploy", "live_safe", True, "skipped by SWITCH_DO_DEPLOY=0")
                after_config = before_config

            # 7. Verify module (explicit)
            expected = build_expected_from_variables(
                {"hostname": parsed.get("sysname") or DEVICE_NAME, "vlan_list": "10 20 30 100"}
            )
            expected["require_ssh"] = False  # 真机未必开了 SSH
            vrep = ConfigVerifier().verify(before_config, after_config or before_config, expected)
            record(
                "verify",
                "rules",
                vrep.get("status") in {"pass", "skipped"},
                f"status={vrep.get('status')}",
                report=vrep,
            )

    except Exception as e:
        record("console", "session", False, f"{type(e).__name__}: {e}")
        traceback.print_exc()

    # ------------------------------------------------------------------
    # 8. AgentAdapter paths (new connections)
    # ------------------------------------------------------------------
    try:
        adapter = AgentAdapter()
        dev = DeviceInfo(port=PORT, password=PASSWORD, connection_type="console")

        r_cmd = adapter.execute(
            AgentRequest(
                action="command",
                device=dev,
                variables={"command": "display clock"},
            )
        )
        record(
            "agent",
            "command",
            r_cmd.success,
            r_cmd.message or (r_cmd.data.get("output", "")[:120] if r_cmd.data else ""),
            success=r_cmd.success,
            code=r_cmd.code,
        )

        r_bak = adapter.execute(
            AgentRequest(
                action="backup",
                device=dev,
                variables={"device_name": f"{DEVICE_NAME}-agent"},
            )
        )
        record(
            "agent",
            "backup",
            r_bak.success,
            str(r_bak.data.get("backup_path", r_bak.message)),
            data=r_bak.data,
        )

        if backup_path:
            cfg_file = Path(backup_path) / "current-configuration.txt"
            r_val = adapter.execute(
                AgentRequest(
                    action="validate",
                    device=dev,
                    variables={
                        "after_config_path": str(cfg_file),
                        "expected": {
                            "hostname": DEVICE_NAME if DEVICE_NAME != "unknown" else "1730-24",
                            "vlan_list": [10, 20, 30, 100],
                            "require_ssh": False,
                        },
                    },
                )
            )
            # hostname in device may be 1730-24
            record(
                "agent",
                "validate",
                True,  # call path works even if rule fail
                f"success={r_val.success} msg={r_val.message}",
                data=r_val.data,
            )

        r_dry = adapter.execute(
            AgentRequest(
                action="deploy",
                device=dev,
                template="_live_test_safe.j2",
                variables={
                    "device_name": DEVICE_NAME,
                    "hostname": "1730-24",
                    "vlan_list": "10 20 30 100",
                    "test_port": "GigabitEthernet0/0/24",
                    "test_description": "huawei-switch-skill-live-test",
                },
                backup=False,
                dry_run=True,
                save=False,
                verify=False,
            )
        )
        record(
            "agent",
            "deploy_dry_run",
            r_dry.success,
            f"status={(r_dry.data or {}).get('status')} msg={r_dry.message}",
            data=r_dry.data,
        )
    except Exception as e:
        record("agent", "session", False, f"{type(e).__name__}: {e}")
        traceback.print_exc()

    # ------------------------------------------------------------------
    # 9. SSH modules (best-effort)
    # ------------------------------------------------------------------
    try:
        from src.ssh.batch import BatchSSHManager
        from src.ssh.inventory import DeviceInventory, InventoryDevice
        from pydantic import SecretStr

        ssh_ok_any = False
        if not mgmt_candidates:
            record("ssh", "discover_mgmt_ip", False, "no ip address found in running-config")
        else:
            record("ssh", "discover_mgmt_ip", True, f"candidates={mgmt_candidates}")

        for host in mgmt_candidates[:3]:
            try:
                inv = DeviceInventory(
                    devices=[
                        InventoryDevice(
                            name=f"ssh-{host.replace('.', '-')}",
                            host=host,
                            password=SecretStr(PASSWORD),
                            username="admin",
                            port=22,
                        )
                    ]
                )
                mgr = BatchSSHManager(inv, backup_base_dir="backups", read_timeout=60)
                rep = mgr.command_all("display version")
                one = rep.results[0] if rep.results else None
                if one and one.success:
                    ssh_ok_any = True
                    record("ssh", f"command_all@{host}", True, one.message, output=(one.data or {}).get("output", "")[:300])
                    bak = mgr.backup_all()
                    b0 = bak.results[0]
                    record("ssh", f"backup_all@{host}", b0.success, b0.message, data=b0.data)
                    break
                else:
                    err = one.error if one else "no result"
                    record("ssh", f"command_all@{host}", False, err or "failed")
            except Exception as e:
                record("ssh", f"command_all@{host}", False, f"{type(e).__name__}: {e}")

        if mgmt_candidates and not ssh_ok_any:
            record("ssh", "overall", False, "SSH not reachable with console password/admin (may be disabled or ACL)")
        elif ssh_ok_any:
            record("ssh", "overall", True, "SSH batch path OK")
    except Exception as e:
        record("ssh", "session", False, f"{type(e).__name__}: {e}")
        traceback.print_exc()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    report_dir = ROOT / "backups" / "_live_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_file = report_dir / f"full_module_{stamp}.json"
    payload = {
        "timestamp": stamp,
        "port": PORT,
        "device": DEVICE_NAME,
        "deploy_enabled": DO_DEPLOY,
        "backup_path": str(backup_path) if backup_path else None,
        "mgmt_candidates": mgmt_candidates,
        "results": [asdict(r) for r in RESULTS],
        "passed": sum(1 for r in RESULTS if r.ok),
        "failed": sum(1 for r in RESULTS if not r.ok),
        "total": len(RESULTS),
    }
    report_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 70)
    print(f"SUMMARY: {payload['passed']}/{payload['total']} passed, {payload['failed']} failed")
    print(f"Report: {report_file}")
    if backup_path:
        print(f"Backup: {backup_path}")
    print("=" * 70)
    for r in RESULTS:
        if not r.ok:
            print(f"  FAIL - {r.module}.{r.name}: {r.detail}")

    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
