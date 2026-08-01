# 05 - 模板系统

## 目标
实现配置模板化（Jinja2 + YAML）。

## 已实现
- TemplateRenderer（Jinja2 渲染）
- TemplateValidator（变量校验）
- TemplateVariables（变量管理）

## 文件
- renderer.py / validator.py / variables.py

## 核心 API

### TemplateRenderer

```python
class TemplateRenderer:
    def __init__(self, template_dir: str = "templates") -> None:
        ...

    def render(
        self,
        template_name: str,
        variables: Dict[str, Any]
    ) -> str:
        """渲染模板文件"""

    def render_string(
        self,
        template_str: str,
        variables: Dict[str, Any]
    ) -> str:
        """直接渲染字符串模板"""
```

### 主要参数

| 参数          | 类型             | 默认值      | 说明                     |
|---------------|------------------|-------------|--------------------------|
| template_dir  | str              | "templates" | 模板存放目录             |
| template_name | str              | -           | 模板文件名（如 base.j2） |
| variables     | Dict[str, Any]   | -           | 渲染变量                 |

## 典型用法示例

### 渲染模板文件
```python
from src.template import TemplateRenderer

renderer = TemplateRenderer(template_dir="templates")
config = renderer.render(
    "base_switch.j2",
    {
        "hostname": "SW-01",
        "vlan_list": [10, 20, 30],
        "mgmt_ip": "192.168.1.1"
    }
)
print(config)
```

### 直接渲染字符串
```python
tpl = "hostname {{ hostname }}\n"
result = renderer.render_string(tpl, {"hostname": "TestSW"})
```

## 验收
能够通过参数自动生成完整配置。
