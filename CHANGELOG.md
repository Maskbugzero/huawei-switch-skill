# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-08-06

Production-hardening release: multi-interface deploy correctness, safe defaults, SSH batch skeleton, post-deploy shallow verify, golden fixtures.

### Security
- Template `admin_password` has no weak defaults; Jinja2 `StrictUndefined`
- Dangerous commands blocked by default on deploy **and** command (Console/SSH/batch): `reboot/reset/delete/format/shutdown` (`undo shutdown` excluded)
- Auto-rollback defaults **off**
- Validate path reads via `Path.relative_to`; `device_name` sanitized against traversal
- `as_bool` for variables so `"false"` is not truthy
- Inventory passwords as `SecretStr`; prefer `password_env`

### Added
- **Scenario positioning**: Console = config primary; SSH = batch ops for managed fleets
- **SSH batch**: inventory YAML, `BatchSSHManager.backup_all` / `command_all`, CLI, docs/examples
- Interface-aware intent idempotency + secret-line ignore (password/cipher)
- Deploy defaults: `save=True`, `verify=True` (sysname / vlan / ssh shallow checks)
- `AgentRequest.save` / `verify` / `allow_dangerous` / `auto_rollback_on_failure`
- Golden fixtures: `tests/fixtures/running_config_access_partial.txt` + `test_golden_access_switch.py`
- `src.__version__ = "0.3.0"`

### Fixed
- **P0** Planner no longer globally dedupes — 24-port templates keep per-port subcommands
- Planner no longer strips `description ## ... ##` as comments
- False idempotent skip across interface context
- Empty backup no longer written for rollback
- SSH connection leak on early return; batch ErrorDetector

### Changed
- `AgentResponse.success` only for deploy statuses `{success, skipped, dry_run}`
- Post-deploy verify fail → `status=verify_failed` (`success=False`)
- Documentation aligned (SKILL/README/docs 00/06/09/10)

### Tests
- **110 passed** (Mock + golden fixtures; no live device required)

### Notes for operators
- **Password rotation**: idempotency ignores secret lines — do not rely on deploy skip/non-skip to change passwords; use `SSHFirstConnect` or explicit change-password flow
- Prefer `dry_run=True` then real deploy; default `backup=True` + `save=True` + `verify=True`

## [0.2.0] - 2026-08-02

### Added
- Parser robustness and verify rule basics
- Documentation and SSH SecretStr consistency

### Tests
- 56 tests passing

## [0.1.0] - Initial Release

- Core modules (console through verify) and AgentAdapter

[0.3.0]: https://github.com/Maskbugzero/huawei-switch-skill/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Maskbugzero/huawei-switch-skill/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Maskbugzero/huawei-switch-skill/releases/tag/v0.1.0
