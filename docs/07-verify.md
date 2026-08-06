# 07 - 配置校验模块

> **注意**：请使用项目 `.venv` 虚拟环境运行本模块（详见 `SKILL.md`）。

## 目标
验证配置正确性；并与 **deploy 成功路径闭环**（浅层）。

## 已实现
- ConfigVerifier（主校验逻辑）
- VerificationRules：`sysname` / `vlan_consistency` / `trunk_consistency` / `ssh_status`
- `build_expected_from_variables()`：从 deploy variables 生成 expected
- VLAN 匹配支持 `vlan N` 与 `vlan batch ...`（避免 `vlan 1` 误匹配 `vlan 10`）
- ReportGenerator（Markdown / HTML 报告）
- **DeploymentEngine**：`verify=True`（默认）时在 save 后重采 running-config 并校验；失败 → `status=verify_failed`

## 文件
- verifier.py / rules.py / report.py

## 与 deploy 闭环

```python
report = engine.deploy(..., verify=True)  # 默认
# report["verification"] -> {status, checks, details}
# status == "verify_failed" 表示下发成功但校验未通过
```

也可独立调用：

```python
from src.verify import ConfigVerifier
from src.verify.rules import build_expected_from_variables

expected = build_expected_from_variables({"hostname": "SW-01", "vlan_list": "10 20"})
report = ConfigVerifier().verify(before, after, expected)
```

**相关**：`06-deploy.md`、`08-agent.md`、`SKILL.md`
