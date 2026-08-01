# 07 - 配置校验模块

## 目标
验证配置正确性。

## 已实现
- ConfigVerifier（主校验逻辑）
- VerificationRules（VLAN、Trunk、SSH 等规则）
- ReportGenerator（Markdown / HTML 报告）

## 文件
- verifier.py / rules.py / report.py

## 核心 API

### ConfigVerifier

```python
class ConfigVerifier:
    def __init__(self, rules: Optional[List[Rule]] = None) -> None:
        ...

    def verify(
        self,
        actual_config: Dict[str, Any],
        expected_config: Dict[str, Any]
    ) -> VerificationReport:
        ...

    def generate_report(
        self,
        report: VerificationReport,
        format: str = "markdown"
    ) -> str:
        ...
```

### 主要参数

| 参数            | 类型                | 默认值     | 说明                     |
|-----------------|---------------------|------------|--------------------------|
| actual_config   | Dict[str, Any]      | -          | 实际解析后的配置         |
| expected_config | Dict[str, Any]      | -          | 期望配置（或模板变量）   |
| format          | str                 | "markdown" | 报告格式（markdown/html）|

## 典型用法示例

### 配置一致性校验
```python
from src.parser import ConfigParser
from src.verify import ConfigVerifier

parser = ConfigParser()
verifier = ConfigVerifier()

actual = parser.parse(open("current-config.txt").read())
expected = {"sysname": "SW-01", "vlans": [10, 20, 30]}

report = verifier.verify(actual, expected)
print(verifier.generate_report(report, format="markdown"))
```

## 验收
自动输出校验报告（支持 Markdown/HTML）。

**相关文档**：
- `08-agent.md`：通过 `AgentAdapter` 统一调用校验（validate action）
- `06-deploy.md`：部署后自动校验集成
