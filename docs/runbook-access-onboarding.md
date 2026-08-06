# Runbook：接入交换机开局（Console + access_switch）

> **版本**：配合 Skill **0.3.0+**  
> **环境**：必须使用项目 `.venv`（见 `SKILL.md`）  
> **路径**：Console = 配置主路径；SSH 仅用于事后批量/改密，**开局改配不要默认走 SSH deploy**

本文给出一条可照着做的 **楼层/办公接入交换机（access）开局** 标准流程，对应模板 `templates/access_switch.j2`。

---

## 0. 适用与前置

### 适用

- 新机或重置后的华为 VRP 接入交换机（如 S5735 等）
- 已用 Console 线连到维护机（Windows 常见 `COMx`）
- 波特率默认 **9600 8N1**（与 Skill 默认一致）

### 不适用（请换流程）

| 场景 | 去哪 |
|------|------|
| 出厂首次登录强制改密 | `SSHFirstConnect` / `docs/09-ssh.md`（有管理 IP 之后） |
| 已纳管多机只备份/巡检 | `docs/10-batch.md` + `BatchSSHManager` |
| 汇聚/核心模板 | `aggregation_switch.j2` / `core_switch.j2`（流程相同，变量不同） |

### 开局前准备清单

- [ ] Console 线已通，设备上电，能看到登录/提示符
- [ ] 已知当前 Console 密码（或空/默认，以现场为准）
- [ ] 确定逻辑名：`device_name` / `hostname`（仅 `字母数字_-.`，禁 `..` 与路径符）
- [ ] 确定 VLAN、管理地址、上行接口名、接入 VLAN
- [ ] 准备强口令：`admin_password`（**无默认值，必填**）
- [ ] 维护机已创建并安装依赖：

```powershell
cd C:\work\0730\huawei-switch-skill   # 按实际路径
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## 1. 标准流程（必须按序）

```
连接冒烟 →（可选）单独备份 → Dry-Run → 人工看 diff
    → 真实部署（backup + save + verify）→ 现场抽查 → 纳入 SSH 清单
```

**原则**：

1. 先 `dry_run`，再真实下发  
2. 真实部署默认：`backup=True`、`save=True`、`verify=True`  
3. **改密不要指望 deploy 幂等**（密钥行不参与 skip 比较）  
4. 危险命令默认阻断；开局模板不应包含 `reboot`/`reset`/`format` 等  

---

## 2. 步骤 A — 连接冒烟

确认串口与密码可用：

```powershell
.\.venv\Scripts\python.exe main.py connect --port COM4 --password "<console_password>"
```

或 Python：

```python
from src.console import Connection

with Connection(port="COM4", password="<console_password>") as conn:
    print(conn.send_command("display version")[:500])
    print(conn.send_command("display current-configuration | include sysname"))
```

**通过标准**：能稳定回显、无反复认证失败、提示符可识别。

失败时检查：COM 口号、线序、是否被其它终端占用、密码、是否卡在 `[Y/N]` 分页（Skill 会尝试关分页）。

---

## 3. 步骤 B — 准备变量（示例）

按现场改写；**不要把真实密码写进仓库或提交 git**。

```python
DEVICE_NAME = "SW-ACCESS-01"          # 备份目录名
PORT = "COM4"
CONSOLE_PASSWORD = "..."              # 当前 console 登录密码

VARIABLES = {
    "device_name": DEVICE_NAME,       # AgentAdapter backup 路径用
    "hostname": "SW-ACCESS-01",
    "admin_password": "YourStrongPass@2026",  # 必填；写入设备 local-user
    "vlan_list": "10 20 30 100",
    "mgmt_ip": "192.168.100.10",
    "mgmt_mask": "255.255.255.0",
    "uplink": "Eth-Trunk1",           # 或实际上行口
    "uplink_vlans": "10 20 30 100",
    "access_vlan": "20",
    "floor": "3",
    "room": "01",
    "max_mac": "2",
    "monitor_port": "GigabitEthernet0/0/25",
}
```

模板要点（`access_switch.j2`）：

- 关 telnet、开 SSH、配置 `admin` 本地用户  
- `vlan batch`、管理 `Vlanif100`、上行 trunk、**24 个 GE 接入口**（含 port-security / PoE 相关）  
- 默认会下发较多接口行；幂等按 **interface 块** 比较，且 **忽略 password/cipher 行**

---

## 4. 步骤 C — Dry-Run（强烈建议）

**推荐用 `AgentAdapter`：**

```python
from src.agent import AgentAdapter, AgentRequest, DeviceInfo

adapter = AgentAdapter()

req = AgentRequest(
    action="deploy",
    device=DeviceInfo(
        port=PORT,
        password=CONSOLE_PASSWORD,
        connection_type="console",
    ),
    template="access_switch.j2",
    variables=VARIABLES,
    backup=True,
    dry_run=True,
    save=True,      # dry_run 不会真正 save
    verify=True,    # dry_run 不会跑设备后校验
    allow_dangerous=False,
)
resp = adapter.execute(req)
print(resp.success, resp.message)
print(resp.data)   # 关注 status / diff_summary / planned_steps_count / dangerous_commands
```

### 如何解读 `status`

| status | success | 含义 | 下一步 |
|--------|---------|------|--------|
| `dry_run` | True | 仅规划 | 人工确认 diff 后去掉 dry_run |
| `skipped` | True | 意图已满足（密钥行忽略） | 一般无需再部署；**改密请另走流程** |
| `blocked` | False | 含危险命令且未放行 | 改模板或显式 `allow_dangerous=True`（慎） |
| `success` | True | 已下发且（默认）verify 通过 | 现场抽查 |
| `verify_failed` | False | 已下发但浅层校验未过 | **优先人工上看板**，勿盲目重跑 |
| `failed` | False | 下发/save/连接失败 | 查 `error`、串口、备份 |

Dry-Run 时请至少确认：

- [ ] `planned_steps_count` 合理（24 口模板应明显大于几十行）  
- [ ] `diff_summary` 符合预期（不是「整机被误 skip」）  
- [ ] 无意外 `dangerous_commands`  
- [ ] `hostname` / VLAN / 管理 IP 变量没有写错  

---

## 5. 步骤 D — 真实部署

确认 Dry-Run 无误后：

```python
req = AgentRequest(
    action="deploy",
    device=DeviceInfo(
        port=PORT,
        password=CONSOLE_PASSWORD,
        connection_type="console",
    ),
    template="access_switch.j2",
    variables=VARIABLES,
    backup=True,
    dry_run=False,
    save=True,
    verify=True,
    allow_dangerous=False,
    auto_rollback_on_failure=False,  # 保持默认；逐行回放不可靠
)
resp = adapter.execute(req)
print(resp.success, resp.data.get("status"), resp.data.get("backup_path"))
print(resp.data.get("saved"), resp.data.get("verification"))
```

等价底层写法（调试时可用）：

```python
from src.console import Connection
from src.deploy import DeploymentEngine

engine = DeploymentEngine()
with Connection(port=PORT, password=CONSOLE_PASSWORD) as conn:
    report = engine.deploy(
        connection=conn,
        template="access_switch.j2",
        variables=VARIABLES,
        device_name=DEVICE_NAME,
        backup=True,
        dry_run=False,
        save=True,
        verify=True,
    )
    print(report)
```

### 成功时你应看到

- `status == "success"`（或意图已在则 `skipped`）  
- `backup_path` 指向 `backups/<device_name>/<timestamp>/`（采集失败时会 `backup_skipped`，需警惕）  
- `saved is True`（若未关 save）  
- `verification.status == "pass"`（浅层：sysname / vlan / ssh）  
- `steps` 中含 `backup` → `render` → `compare` → `deploy` → `save` → `verify`（skip/dry_run 会短一些）  

---

## 6. 步骤 E — 现场抽查（不要只信自动 verify）

自动 verify 是**浅层**门禁，开局仍建议人工：

```text
display current-configuration | include sysname
display vlan
display ip interface brief
display interface brief
display ssh server status
display local-user
```

核对：

- [ ] sysname  
- [ ] 管理 Vlanif 地址与掩码  
- [ ] 上行 trunk 与 allow-pass VLAN  
- [ ] 抽样 2～3 个接入口：access VLAN、未误 shutdown  
- [ ] SSH 已 enable；本地 admin 可后续登录（密码为本次 `admin_password`）  

备份目录保留：`backups/SW-ACCESS-01/<时间戳>/current-configuration.txt`。

---

## 7. 步骤 F — 开局后纳入批量管理（可选）

管理 IP 与 SSH 可用后：

1. 复制清单模板：

```powershell
copy configs\devices.example.yaml configs\devices.yaml
```

2. 编辑 `configs/devices.yaml`（**勿提交真实密码**），优先：

```yaml
devices:
  - name: SW-ACCESS-01
    host: 192.168.100.10
    password_env: SW_ACCESS_01_PASS
```

3. 批量备份冒烟：

```powershell
$env:SW_ACCESS_01_PASS = "..."
.\.venv\Scripts\python.exe -m src.ssh.batch -i configs/devices.yaml backup --name SW-ACCESS-01
```

详见 `docs/10-batch.md`。

---

## 8. 改密说明（易错）

| 做法 | 结果 |
|------|------|
| 只改模板 `admin_password` 再 deploy | 其它意图已满足时可能 **`skipped`，密码不会更新**（密钥行不参与幂等） |
| 需要轮换业务/SSH 密码 | 用 **`SSHFirstConnect`** 或登录后手工/专用 command（并 `allow_dangerous` 仅在必要时） |
| 首次上线强制改密 | `docs/09-ssh.md` |

---

## 9. 常见问题

### `status=blocked`

模板或变量渲染出了危险命令。检查是否误含 `reboot` / `reset` / `delete` / `format` / 裸 `shutdown`。  
`undo shutdown` **不会**被拦。

### `status=skipped` 但现场仍缺配置

- 是否看错设备/VLAN  
- 接口短名与全名不一致（如 `GE` vs `GigabitEthernet`）可能导致 diff 语义偏差——以 `display current-configuration` 全名为准  
- 密钥行被忽略属预期  

### `status=verify_failed`

配置可能已部分或全部下发且已 save。  
**先** `display` 核对，再决定补线或二次部署；不要无限自动重试。  
可临时 `verify=False` 仅用于排障，生产默认保持 `True`。

### `backup_skipped`

采集 running-config 失败或为空。部署仍可能继续，但**没有可靠备份**。应先修好采集再开局。

### 串口中途失败

- 查看 `resp.error` / 日志  
- 用备份目录中的 `current-configuration.txt` 对照  
- `auto_rollback_on_failure` 默认关闭且为实验性，**不能**当正式回退方案  

### 描述行被截断？

0.3.0+ planner 会保留 `description ## ... ##`。若使用旧版本请升级到 **v0.3.0+**。

---

## 10. 安全与合规摘要

- 密码不进 git、不进截图仓库；CLI `--password` 可能进 shell history，生产优先代码/环境变量  
- `device_name` 勿用路径字符  
- 默认拒绝危险命令；需要时显式 `allow_dangerous=True` 并人工双人确认  
- 开局变更窗口内保留 Console 物理访问，直到 SSH 与管理网验证完毕  

---

## 11. 相关文档

| 文档 | 内容 |
|------|------|
| `SKILL.md` | Skill 契约与安全默认 |
| `docs/06-deploy.md` | deploy 参数与 status |
| `docs/07-verify.md` | 浅层校验闭环 |
| `docs/09-ssh.md` | 首次改密 |
| `docs/10-batch.md` | 纳管后批量 |
| `examples/03_using_agent_adapter.py` | Adapter 综合示例 |
| `examples/04_template_deploy.py` | 模板部署示例 |
| `tests/test_golden_access_switch.py` | 24 口模板金样例（无真机） |

---

## 12. 一页检查表（可打印）

```
[ ] .venv 依赖已装
[ ] COM 口 + 密码冒烟通过
[ ] VARIABLES 已按现场填写（含 admin_password）
[ ] dry_run → status=dry_run，diff 已人工确认
[ ] 真实 deploy → success，saved=True，verify=pass
[ ] 备份目录存在且非空
[ ] display 抽查 sysname / vlan / 管理 IP / 上行 / 接入口
[ ] SSH 可达后写入 devices.yaml（password_env）
[ ] 备份一次 SSH batch backup 作基线
[ ] 本单变更与口令交付已登记（按公司流程）
```
