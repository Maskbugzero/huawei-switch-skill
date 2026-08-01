# Huawei Switch Skill 使用指南

本指南详细说明如何在 Claude Code、Hermes 或自定义 Agent 系统中正确调用 `huawei-switch-skill` Skill。

## 环境要求（重要）

使用本 Skill 时，**必须**通过项目自带的 `.venv` 虚拟环境执行所有 Python 命令。

**规则**：
- 如果 `.venv` 不存在，需先创建
- 所有命令使用 `.venv\Scripts\python.exe`（Windows）或等效路径
- 禁止直接使用系统全局 `python`

**示例**：

```powershell
# 安装依赖
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 运行测试
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

---

## 1. Skill 概述

`huawei-switch-skill` 是一个专注于华为 VRP 交换机的 **Console 优先** 自动化 Skill，提供从连接到部署的全生命周期能力。

**推荐调用方式**：通过 `AgentAdapter` + `AgentRequest` 进行标准化交互。

## 2. 快速集成

### 安装

```bash
pip install -r requirements.txt
```

### 基础调用示例

```python
from src.agent import AgentAdapter, AgentRequest, DeviceInfo

adapter = AgentAdapter()

device = DeviceInfo(port="COM4", password="your_password")

# 执行备份
request = AgentRequest(
    action="backup",
    device=device,
    variables={"device_name": "SW-01"}
)
response = adapter.execute(request)

if response.success:
    print("备份成功:", response.data)
```

## 3. 支持的操作（Action）

| Action     | 说明               | 必需参数                          | 可选参数                     |
|------------|--------------------|-----------------------------------|------------------------------|
| `backup`   | 配置备份           | device                            | device_name                  |
| `deploy`   | 模板化部署         | device, template, variables       | backup, dry_run              |
| `command`  | 单条命令执行       | device, variables["command"]      | -                            |
| `validate` | 配置一致性校验     | device                            | config_path, rules           |

## 4. 完整请求示例

### 备份示例

```python
request = AgentRequest(
    action="backup",
    device=DeviceInfo(port="COM4", password="xxx"),
    variables={"device_name": "SW-01"}
)
```

### 部署示例

```python
request = AgentRequest(
    action="deploy",
    device=DeviceInfo(port="COM4", password="xxx"),
    template="access_switch.j2",
    variables={
        "hostname": "SW-01",
        "vlan_list": "10 20 30",
        "management_ip": "192.168.1.10/24"
    },
    backup=True,
    dry_run=False
)
```

### 执行命令示例

```python
request = AgentRequest(
    action="command",
    device=DeviceInfo(port="COM4", password="xxx"),
    variables={"command": "display interface brief"}
)
```

## 5. 响应处理

`AgentResponse` 结构：

```python
{
    "success": True,
    "code": None,
    "message": "",
    "data": { ... },      # 操作返回的具体数据
    "error": None
}
```

推荐处理方式：

```python
response = adapter.execute(request)
if response.success:
    print(response.data)
else:
    print("失败:", response.error)
```

## 6. 最佳实践

1. **始终使用 `AgentAdapter`** 作为入口
2. **部署操作务必开启 `backup=True`**
3. **敏感信息（密码）通过参数传入，绝不硬编码**
4. **使用 `dry_run=True` 先验证模板渲染结果**
5. **生产环境建议先在测试设备上验证**

## 7. 示例代码

项目提供了完整的示例集合，位于 `examples/` 目录：

- `01_connect_and_run_command.py`
- `02_backup_config.py`
- `03_using_agent_adapter.py`（**强烈推荐**）
- `04_template_deploy.py`
- `05_ssh_first_connect.py`
- `06_config_verify.py`

## 8. 调试与日志

- 设置日志级别为 DEBUG 可查看详细交互过程
- 所有密码相关操作均已做掩码处理

## 9. 常见问题

**Q: 如何支持 SSH？**  
A: 使用 `DeviceInfo` 的 `host` 字段，并参考 `examples/05_ssh_first_connect.py`。

**Q: 部署失败如何回滚？**  
A: `DeploymentEngine` 默认支持回滚，失败时会自动尝试恢复。

**Q: 是否支持并发多设备？**  
A: 当前版本为单设备串行，未来版本将支持。

---

**Skill 版本**：1.0.0  
**最后更新**：2026-08-01
