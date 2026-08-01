# 04 - 配置解析器

> **注意**：请使用项目 `.venv` 虚拟环境运行本模块（详见 `SKILL.md`）。

## 目标
将华为配置转换为结构化数据。

## 已实现
- 主解析器：sysname、VLAN、Interface、STP、AAA
- 子解析器：interface_parser、vlan_parser、stp_parser、aaa_parser

## 文件
- parser.py（主入口）
- interface_parser.py / vlan_parser.py / stp_parser.py / aaa_parser.py

## 核心 API

### ConfigParser

```python
class ConfigParser:
    def __init__(self) -> None:
        ...

    def parse(self, config_text: str) -> Dict[str, Any]:
        """解析完整配置文本"""

    def parse_interface(self, text: str) -> List[Dict]:
        ...

    def parse_vlan(self, text: str) -> List[Dict]:
        ...
```

### 主要参数

| 参数       | 类型 | 默认值 | 说明               |
|------------|------|--------|--------------------|
| config_text| str  | -      | 配置文件内容       |

返回示例结构：
```python
{
    "sysname": "SW-01",
    "vlans": [...],
    "interfaces": [...],
    ...
}
```

## 典型用法示例

### 解析备份文件
```python
from src.parser import ConfigParser

parser = ConfigParser()
with open("backups/SW-01/20260730-120000/current-configuration.txt") as f:
    config = f.read()

result = parser.parse(config)
print(result["sysname"])
print(result["vlans"])
print(result.get("interfaces", [])[0])
```

## 验收
配置文件能够完整转换为 Python 对象（dict）。
