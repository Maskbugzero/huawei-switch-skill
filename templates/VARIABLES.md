# 模板变量命名规范

本文档定义 huawei-switch-skill 模板库的变量命名规范和使用指南。

---

## 变量命名原则

1. **使用 snake_case**：所有变量使用小写字母 + 下划线（如 `mgmt_ip`）
2. **语义明确**：变量名应清晰表达其用途
3. **统一前缀**：相关变量使用相同前缀（如 `mgmt_*`、`uplink_*`）
4. **提供默认值**：模板中使用 `default()` 过滤器提供合理默认值

---

## 通用变量

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `hostname` | string | `Test-SW`（部分模板） | 设备主机名 |
| `admin_password` | string | **无默认，必填** | 管理员密码（StrictUndefined，漏传则渲染失败） |
| `vlan_list` | string | `"10 20 30"` | VLAN 列表（空格分隔） |

---

## 管理接口变量

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `mgmt_ip` | string | 各模板不同 | 管理 IP 地址 |
| `mgmt_mask` | string | `"255.255.255.0"` | 管理子网掩码 |
| `mgmt_vlan` | string | `"100"` | 管理 VLAN ID |

---

## 上行链路变量

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `uplink` | string | `"Eth-Trunk1"` | 上行链路接口名 |
| `uplink_vlans` | string | `vlan_list` | 上行允许通过的 VLAN |
| `uplink1`, `uplink2` | string | `"Eth-Trunk1"`, `"Eth-Trunk2"` | 核心交换机双上行 |

---

## 下行链路变量（汇聚层）

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `downlink1`, `downlink2` | string | `"Eth-Trunk10"`, `"Eth-Trunk20"` | 下行到接入层 |
| `downlink_vlans` | string | `"10 20 30 40 100"` | 下行允许通过的 VLAN |

---

## 接入端口变量

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `access_vlan` | string | `"20"` | 接入端口默认 VLAN |
| `floor` | string | `"1"` | 楼层号（用于端口描述） |
| `room` | string | `"01"` | 房间号（用于端口描述） |
| `max_mac` | string | `"2"` | 端口安全最大 MAC 数 |
| `access_ports` | list | - | 接入端口列表（minimal 模板专用） |

---

## 各模板变量对照表

### access_switch.j2（接入层）

**必需变量**：`admin_password`（以及业务所需的 hostname 等）

**常用变量**：
- `hostname`, `admin_password`
- `vlan_list`, `mgmt_ip`, `mgmt_mask`
- `uplink`, `uplink_vlans`
- `access_vlan`, `floor`, `room`, `max_mac`

**示例**：
```jinja2
{{ hostname | default('Access-SW') }}
{{ mgmt_ip | default('192.168.100.10') }}
```

---

### aggregation_switch.j2（汇聚层）

**必需变量**：`admin_password`（以及业务所需的 hostname 等）

**常用变量**：
- `hostname`, `admin_password`
- `vlan_list`, `mgmt_ip`, `mgmt_mask`
- `downlink1`, `downlink_vlans`

**示例**：
```jinja2
{{ downlink1 | default('Eth-Trunk10') }}
```

---

### core_switch.j2（核心层）

**必需变量**：`admin_password`（以及业务所需的 hostname 等）

**常用变量**：
- `hostname`, `admin_password`
- `vlan_list`, `mgmt_ip`, `mgmt_mask`
- `uplink1`, `uplink2`, `uplink_vlans`
- `current_time`（用于时钟设置）

**示例**：
```jinja2
{{ current_time | default('2026-07-31 10:00:00') }}
```

---

### minimal_switch.j2（快速测试）

**必需变量**：`admin_password`（以及业务所需的 hostname 等）

**常用变量**：
- `hostname`, `admin_password`
- `vlan_list`
- `mgmt_ip`, `mgmt_mask`, `mgmt_vlan`（可选）
- `uplink`, `uplink_vlans`（可选）
- `access_ports`, `access_vlan`（可选）

**示例**：
```python
# 最小配置
variables = {"hostname": "Test-SW"}

# 带管理 IP
variables = {
    "hostname": "Test-SW",
    "mgmt_ip": "192.168.1.10",
    "mgmt_vlan": "100"
}
```

---

## 最佳实践

### 1. 密码安全

**❌ 错误**：
```jinja2
local-user admin password irreversible-cipher MyPassword123
```

**✅ 正确**（使用变量 + 默认值）：
```jinja2
local-user admin password irreversible-cipher {{ admin_password | default('ChangeMe@2026') }}
```

**生产环境建议**：
```python
import os
from getpass import getpass

password = os.getenv("SWITCH_ADMIN_PASSWORD") or getpass("Enter password: ")
request = AgentRequest(
    action="deploy",
    variables={"admin_password": password, ...}
)
```

### 2. VLAN 配置

**VLAN 列表格式**：空格分隔的字符串
```jinja2
vlan batch {{ vlan_list | default('10 20 30 100') }}
```

### 3. 接口命名

**推荐格式**：
- 接入层：`GigabitEthernet0/0/X`
- 汇聚/核心：`Eth-TrunkN`（链路聚合）

---

## 变量类型约定

| 前缀 | 含义 | 示例 |
|------|------|------|
| `mgmt_*` | 管理接口相关 | `mgmt_ip`, `mgmt_mask` |
| `uplink_*` | 上行链路相关 | `uplink`, `uplink_vlans` |
| `downlink_*` | 下行链路相关 | `downlink1`, `downlink_vlans` |
| `access_*` | 接入端口相关 | `access_vlan`, `access_ports` |

---

## 迁移指南

### 从旧模板迁移

如果您有自定义模板，请参考以下映射：

| 旧变量名 | 新变量名 | 说明 |
|----------|----------|------|
| `ip` | `mgmt_ip` | 管理 IP |
| `mask` | `mgmt_mask` | 子网掩码 |
| `gw` | `mgmt_gateway` | 网关（暂未使用） |

---

## 贡献指南

添加新模板时，请：

1. 在模板顶部添加变量说明注释
2. 使用 `default()` 过滤器提供合理默认值
3. 更新本文档的变量对照表
4. 添加示例用法到对应 examples/ 文件

---

**最后更新**：2026-08-02
**维护者**：huawei-switch-skill 团队
