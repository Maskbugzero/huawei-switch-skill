# Examples 使用指南

本目录包含 `huawei-switch-skill` 的使用示例。

## 示例分类

### 推荐用法（强烈建议）

这些示例展示了通过 **AgentAdapter** 调用 Skill 的标准方式：

| 文件 | 说明 |
|------|------|
| `01_connect_and_run_command.py` | 最基础的命令执行示例 |
| `02_backup_config.py` | 配置备份示例 |
| `03_using_agent_adapter.py` | AgentAdapter 综合用法演示 |
| `04_template_deploy.py` | 模板化部署示例 |
| `06_config_verify.py` | 配置校验示例 |

**特点**：使用统一的 `AgentRequest` + `AgentAdapter` 接口，推荐在生产和 Agent 系统中使用。

### 特殊场景示例

| 文件 | 说明 |
|------|------|
| `05_ssh_first_connect.py` | SSH 首次连接强制改密（目前不通过 AgentAdapter） |

**说明**：此示例属于特殊能力，独立于 AgentAdapter，适用于需要 SSH 首次登录改密的场景。

---

## 快速开始

推荐从以下文件入手：

1. `03_using_agent_adapter.py` —— 了解 Skill 的推荐调用方式
2. `02_backup_config.py` —— 学习如何进行配置备份
3. `04_template_deploy.py` —— 学习模板化部署

---

## 注意事项

- 所有示例运行前请确保已激活或直接使用项目 `.venv` 虚拟环境
- 大多数示例需要真实串口（COM 口）或模拟环境
- 密码请勿硬编码，生产环境建议使用环境变量或交互式输入
