# AGENT.md（历史文档，已归档）

> ⚠️ **本路线图已完成第 1-7 阶段**
>
> 当前项目状态请参考：
> - `CLAUDE.md` — 开发环境与工程实践
> - `README.md` — 项目概览与快速开始
> - `SKILL.md` — Skill 元数据与调用指南
>
> 本文档保留作为历史记录，记录项目的完整开发路线图与设计思考。

---

# AGENT.md

## 项目名称

Huawei Switch Skill

## 项目目标

开发一个基于 Python 的华为交换机自动化运维工具，通过 Console 口（后续支持 SSH）实现：

* 自动连接交换机
* 自动备份配置
* 自动解析配置
* 模板化生成配置
* 自动部署配置
* 配置一致性校验
* 日志记录与审计追踪

项目采用模块化架构设计，每个阶段均可独立测试、独立交付。

---

# 总体架构

```text
Console/SSH
     │
     ▼
Connection Layer
     │
     ▼
Command Engine
     │
     ▼
Configuration Collector
     │
     ▼
Configuration Parser
     │
     ▼
Template Engine
     │
     ▼
Deployment Engine
     │
     ▼
Verification Engine
```

---

# 开发路线图

## 第一阶段：基础串口通信层

### 目标

建立稳定可靠的 Console 通信能力。

### 功能

* 自动扫描 COM 端口
* 自动连接串口
* 自动重连
* 提示符识别
* 自动关闭分页

支持：

```shell
screen-length 0 temporary
```

* 输出日志记录
* 收发数据缓存管理

### 输出文件

```text
src/console/
├── serial_manager.py
├── connection.py
├── prompt_detector.py
└── pager_handler.py
```

### 验收标准

能够自动连接交换机并执行：

```shell
display version
```

正确返回结果。

---

## 第二阶段：命令执行引擎

### 目标

实现稳定的命令下发能力。

### 功能

* send_command()
* send_commands()
* 回显等待
* 超时控制
* 错误识别

识别：

```text
Error:
Failed:
Incomplete command
Unrecognized command
```

* save 自动确认

支持：

```shell
save
Y
```

* 命令执行日志

### 输出文件

```text
src/command/
├── executor.py
├── response_parser.py
├── error_detector.py
└── save_handler.py
```

### 验收标准

能够自动执行：

```shell
system-view
vlan batch 10
save
```

并成功保存配置。

---

## 第三阶段：配置采集模块

### 目标

自动获取设备配置并归档。

### 功能

采集：

```shell
display current-configuration
display version
display vlan
display interface brief
display stp brief
display device
```

自动备份：

```text
backups/
└── 设备名/
    └── YYYYMMDD-HHMMSS/
```

生成：

* 配置文件
* 设备信息
* 元数据

### 输出文件

```text
src/backup/
├── collector.py
├── exporter.py
└── inventory.py
```

### 验收标准

一键生成完整设备备份目录。

---

## 第四阶段：配置解析器

### 目标

将华为配置转换为结构化数据。

### 解析内容

#### 系统信息

```text
sysname
timezone
clock
```

#### VLAN

```text
vlan
vlan batch
```

#### 接口

```text
GigabitEthernet
10GE
Eth-Trunk
```

#### 二层配置

```text
access
trunk
hybrid
```

#### 三层配置

```text
Vlanif
IP地址
```

#### 安全配置

```text
AAA
SSH
Telnet
ACL
```

#### 网络协议

```text
STP
RSTP
MSTP
LLDP
SNMP
NTP
```

### 输出

统一对象模型：

```python
Device
 ├── VLAN
 ├── Interface
 ├── STP
 ├── SSH
 └── AAA
```

### 输出文件

```text
src/parser/
├── parser.py
├── interface_parser.py
├── vlan_parser.py
├── stp_parser.py
└── aaa_parser.py
```

### 验收标准

配置文件能够完整转换为 Python 对象。

---

## 第五阶段：模板系统

### 目标

实现配置模板化。

### 技术方案

* Jinja2
* YAML

### 示例

模板：

```jinja2
sysname {{ hostname }}

vlan batch {{ vlan_list }}
```

参数：

```yaml
hostname: SW-01
vlan_list: 10 20 30
```

生成：

```shell
sysname SW-01

vlan batch 10 20 30
```

### 输出文件

```text
src/template/
├── renderer.py
├── validator.py
└── variables.py
```

### 验收标准

能够通过参数自动生成完整配置。

---

## 第六阶段：自动部署模块

### 目标

自动下发配置。

### 功能

* 配置预检查
* 配置下发
* 分步执行
* 失败回滚
* 执行记录

### 输出文件

```text
src/deploy/
├── deployer.py
├── rollback.py
└── planner.py
```

### 验收标准

能够自动完成新交换机初始化部署。

---

## 第七阶段：配置校验模块

### 目标

验证配置正确性。

### 功能

检查：

* VLAN一致性
* Trunk一致性
* Eth-Trunk成员状态
* STP状态
* SSH状态
* 管理IP状态

生成：

```text
reports/
```

输出：

* HTML
* Markdown

### 输出文件

```text
src/verify/
├── verifier.py
├── rules.py
└── report.py
```

### 验收标准

自动输出校验报告。

---

## 第八阶段：图形界面（可选）

### 目标

降低使用门槛。

### 技术方案

* PySide6

或

* Web UI（FastAPI + Vue）

### 功能

* 串口选择
* 配置备份
* 配置生成
* 配置部署
* 校验报告查看

---

# 推荐仓库结构

```text
huawei-switch-skill/
│
├── AGENT.md
├── README.md
├── ROADMAP.md
├── ARCHITECTURE.md
├── requirements.txt
├── pyproject.toml
│
├── src/
│   ├── console/
│   ├── command/
│   ├── backup/
│   ├── parser/
│   ├── template/
│   ├── deploy/
│   ├── verify/
│   ├── utils/
│   └── cli/
│
├── templates/
│
├── configs/
│
├── backups/
│
├── reports/
│
├── logs/
│
├── tests/
│
└── docs/
    ├── 01-console.md
    ├── 02-command-engine.md
    ├── 03-backup.md
    ├── 04-parser.md
    ├── 05-template.md
    ├── 06-deploy.md
    ├── 07-verify.md
    └── 08-gui.md
```

---

# 当前开发优先级

P1：

1. 串口通信层
2. 命令执行引擎
3. 配置采集模块

P2：

4. 配置解析器
5. 模板系统

P3：

6. 自动部署
7. 配置校验

P4：

8. 图形界面

---

# 第一版目标（MVP）

第一版仅实现：

* Console连接
* 自动登录
* 自动关闭分页
* 执行命令
* 获取 current-configuration
* 自动备份配置

达到可替代 SecureCRT 手工备份的能力。

---

# 后续维护与质量改进（2026-08 更新）

## 已完成的质量改进

- **AgentAdapter 重构**：使用上下文管理器彻底解决连接泄漏，`validate` action 完整实现，错误处理优化。
- **示例与文档同步**：统一为 `DeviceInfo` 现代用法。
- **部署脚本改进**：迁移至推荐的 `with Connection(...) as conn:` 模式。
- **测试覆盖**：扩展至 13 个测试用例。
- **依赖管理**：补全 paramiko / netmiko。
- **错误处理**：关键模块（connection、deployer）增加具体异常捕获与日志。

## 当前状态

- 1-7 阶段核心功能已完成
- Skill 化程度高，可被 Claude Code 等上层系统直接调用
- 代码质量与可维护性显著提升

建议后续优先级：
- 完善回滚逻辑
- 增加更多模块单元测试
- 实现日志敏感信息脱敏
- 支持更多华为命令解析器
