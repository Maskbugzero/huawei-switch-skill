# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-08-02

### Added
- **Error codes** (`src/agent/error_codes.py`):
  - Template errors: `TPL001` (not found), `TPL002` (render failed), `TPL003` (missing variables)
  - Deploy errors: `DEP001` (command failed), `DEP002` (pre-deploy collection failed), `DEP003` (post-deploy verification failed)
  - Command errors: `CMD001` (execution failed), `CMD002` (timeout), `CMD003` (error response)
- **CommandExecutionError** exception (`src/command/exceptions.py`):
  - Dedicated exception for command execution failures with `error_type`, `output`, `command` attributes
  - Exported from `src/command/__init__.py`
- **New examples**:
  - `examples/07_ssh_via_agent_adapter.py`: SSH mode usage with `DeviceInfo`, backup/command/deploy over SSH
  - `examples/08_error_handling.py`: Comprehensive error scenarios and best practices
- **New template**: `templates/minimal_switch.j2` for quick testing and prototyping
- **Documentation**: `templates/VARIABLES.md` - Complete variable naming standards and usage guide
- **Tests**: Increased from 48 to 51 tests with `CommandExecutionError` coverage

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
