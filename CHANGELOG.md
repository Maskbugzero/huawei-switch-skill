# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
