# 项目概览

`huawei-switch-skill` 是一个企业级的华为 VRP 交换机 Console 自动化 Skill。

它封装了从串口连接、命令执行、配置备份、解析、模板渲染、部署到校验的完整生命周期能力，可被 Claude Code、Hermes 或其他上层 Agent 系统直接调用。

## 核心定位

- **Skill 而非 Agent**：提供标准化能力封装，供上层 Agent 调用
- **Console 优先**：最稳定可靠的接入方式
- **模块化设计**：每个模块可独立使用

## 主要能力

| 能力模块       | 对应目录     | 核心功能                     |
|----------------|--------------|------------------------------|
| 串口通信       | `console/`   | 连接、登录、关闭分页         |
| 命令执行       | `command/`   | 错误检测、自动 save          |
| 配置备份       | `backup/`    | 采集 + 结构化归档            |
| 配置解析       | `parser/`    | 转换为结构化 Python 对象     |
| 模板渲染       | `template/`  | Jinja2 模板                  |
| 自动部署       | `deploy/`    | 渲染 + 下发 + 回滚           |
| 配置校验       | `verify/`    | 一致性检查 + 报告生成        |
| SSH 首次改密   | `ssh/`       | 首次连接强制修改密码         |
| 统一入口       | `agent/`     | `AgentAdapter` 调用接口      |

## 推荐调用方式

```python
from src.agent import AgentAdapter, AgentRequest, DeviceInfo

adapter = AgentAdapter()
request = AgentRequest(
    action="backup",
    device=DeviceInfo(port="COM4", password="xxx"),
    variables={"device_name": "SW-01"}
)
response = adapter.execute(request)
```

## 项目结构

```
huawei-switch-skill/
├── src/
│   ├── console/      # 串口通信核心
│   ├── command/      # 命令执行引擎
│   ├── backup/       # 配置采集与导出
│   ├── parser/       # 配置解析器
│   ├── template/     # Jinja2 模板
│   ├── deploy/       # 部署与回滚
│   ├── verify/       # 配置校验
│   ├── agent/        # Skill 统一入口
│   └── ssh/          # SSH 首次改密（实验）
├── examples/         # 使用示例
├── docs/             # 详细文档
├── templates/        # Jinja2 模板文件
└── tests/            # Mock 测试
```

## 相关文档

- `SKILL.md` — Skill 元数据与快速开始
- `README.md` — 项目介绍
- `agent.md` — 开发路线图
- `docs/01-console.md` ~ `docs/09-ssh.md` — 各模块详细说明
- `CHANGELOG.md` — 变更历史

## 当前状态

- 1~7 阶段核心功能已完成
- Skill 化程度高，可直接被上层系统调用
- 支持 Mock 测试，无硬件环境可用
