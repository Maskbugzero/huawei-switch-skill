# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-08-06

### Fixed
- Idempotency ignores secret lines (`password` / `irreversible-cipher` / `cipher …`) so full templates can `skipped` against device ciphertext
- `variables` string booleans: `"false"` / `"0"` / `"no"` no longer treated as True (`as_bool`)
- `command` action (Console + SSH) blocks dangerous commands by default; SSH validates before connect

### Fixed (prior)
- **P0** `DeploymentPlanner.plan` no longer globally dedupes lines — multi-interface templates keep repeated subcommands (`port link-type access`, `undo shutdown`, …); only consecutive identical lines collapse
- **P1** Deploy idempotency is **interface-aware** (per-interface body subset + global lines); stops false `skipped` when the same line exists under another interface
- **P1** Successful deploy defaults to VRP `save` (`save=True`); report includes `saved`
- **P1** Empty/missing current config no longer writes empty backups used for rollback (`backup_skipped`)
- **P1** `ConfigExporter` sanitizes `device_name` (blocks `..` / path separators)
- **P1** SSH batch `command_all`: `ErrorDetector` + default dangerous-command block (`allow_dangerous=True` to override); CLI `--allow-dangerous`

### Changed
- `AgentRequest.save` first-class field (default True)
- SSH Adapter deploy uses `DeploymentPlanner` + interface-aware intent match + optional save
- `InventoryDevice.password` is `SecretStr`; inventory `name` sanitized

### Tests
- **101+ passed**

## [0.2.0] - 2026-08-02

### Added
- **Parser robustness**:
  - `InterfaceParser.MAX_CONFIG_LENGTH` constant with input size protection (500k chars)
  - `re.error` exception handling with clear warning log
  - Consistent use of project logger
- **Verify rules**:
  - `_check_vlan`: actual existence check based on `expected["vlan_list"]`
  - `_check_trunk`: basic interface presence check
  - Support for `pass` / `fail` / `skipped` states
- **Tests**:
  - Added `test_parser_interface_edge_cases` (empty input, large config, shutdown detection)
  - Added `test_verify_rules_edge_cases` (skipped case, missing VLAN)
  - Total tests increased to 56

### Changed
- **Documentation**:
  - `SKILL.md`: Updated Parser and Verify capability descriptions
  - Added SSH dual-path boundary clarification (`SSHFirstConnect` vs AgentAdapter netmiko)
  - Added role headers in `CLAUDE.md` and `README.md` to reduce documentation confusion
- **SSH**:
  - `SSHDevice.old_password` and `new_password` migrated to `SecretStr` for consistency

### Fixed
- Missing `return interfaces` in `InterfaceParser.parse()` after robustness changes
- Inconsistent logging in Parser module

### Tests
- All 56 tests passing

### Changed
- **AgentAdapter** (`src/agent/adapter.py`):
  - SSH connection now uses explicit `conn_timeout=30` and `read_timeout=30`
  - SSH deploy includes idempotency check before applying config
  - Disconnect exceptions now logged as warnings instead of silently swallowed
- **PromptDetector** (`src/console/prompt_detector.py`):
  - Enhanced regex patterns with line-end anchors (`\s*$`) for accurate prompt matching
  - Added support for Chinese colon (`：`) and `Continue? [Y/N]` prompts
- **Parser** (`src/parser/parser.py`):
  - Moved `import re` to module top level (removed function-level import)
  - Enhanced `parse()` logging with statistics (sysname, vlan count, interface count)
- **Backup** (`src/backup/collector.py`):
  - Improved exception handling: specific `ConsoleTimeout`/`ConsoleDisconnect`/`CommandError` + generic fallback
- **Examples**: All examples now use modern `DeviceInfo` pattern
- **Documentation**: `CLAUDE.md` and `README.md` updated to reference archived `docs/archive/agent.md`

### Fixed
- SSH parameter validation now correctly distinguishes SSH vs Console modes
- SSH deploy missing idempotency check (now performs config comparison before applying)
- Verbose output logs (`initial_output`, `verify_output`) downgraded from `info` to `debug` level
- `_wait_for_output` now returns `(output, timed_out)` tuple for timeout awareness

### Tests
- All 51 tests passing
- Added 3 unit tests for `CommandExecutionError`
- Test coverage expanded for error handling scenarios

## [Unreleased] - 2026-08-01

### Added
- `validate` action fully implemented in `AgentAdapter`
- New test case `test_agent_request_validate_action` in integration tests
- Cross-references added to module documentation (`03-backup.md`, `06-deploy.md`, `07-verify.md`)

### Changed
- **AgentAdapter** (`src/agent/adapter.py`):
  - Refactored to use `with Connection(...) as conn:` context manager (eliminates resource leaks)
  - Improved parameter handling using `DeviceInfo` model
  - Better error handling and input validation
- **Deployment scripts** (`deploy_s5735r_*.py`):
  - Migrated to recommended context manager pattern
  - Added comments referencing `DeploymentEngine` for future unification
- **Error handling** improved in `connection.py` and `deployer.py` (specific exceptions + logging)
- **RollbackManager** (`src/deploy/rollback.py`): Enhanced with implementation notes and TODO
- **Documentation**:
  - Updated `SKILL.md`, `README.md`, `docs/08-agent.md`, and example docstrings
  - Modernized all `AgentRequest` examples to use `DeviceInfo`
  - Added "Recent Improvements" section in README

### Fixed
- `AgentAdapter` connection resource leak (unreachable `disconnect()`)
- Inconsistency between `AgentRequest` model (`request.py`) and examples (`params` dict)
- Hardcoded device name in backup path within adapter
- Missing `paramiko` and `netmiko` in `requirements.txt`

### Tests
- All 13 tests passing (`pytest tests/`)
- Increased coverage for `AgentAdapter` and `validate` action

## [0.1.0] - Initial Release

- Core modules completed (stages 1-7):
  - Console communication
  - Command execution
  - Backup & export
  - Config parsing
  - Jinja2 templating
  - Deployment engine
  - Verification
- `AgentAdapter` as unified Skill entrypoint
- Basic Mock tests
- Documentation (`docs/`, `SKILL.md`, `agent.md`)

[Unreleased]: https://github.com/your-org/huawei-switch-skill/compare/v0.1.0...HEAD
