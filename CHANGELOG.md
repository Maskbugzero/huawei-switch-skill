# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-08-07

Medium-term hardening: uplink guard, SSH host keys, packaging/CI, error-code matrix, baudrate.

### Security
- **Uplink/port-role guard**: block turning auto-detected or explicit protected ports into access ports unless `allow_uplink_change=True`
- **SSH host keys**: default reject unknown keys (`ssh_strict` / `RejectPolicy`); opt-in `accept_unknown_host_key` or `HUAWEI_SSH_ACCEPT_UNKNOWN=1`
- SSH real deploy remains disabled by default (`allow_ssh_deploy`)

### Added
- `src/deploy/port_guard.py` + deploy integration
- `src/ssh/hostkeys.py`; wired into AgentAdapter / BatchSSHManager / SSHFirstConnect
- `AgentRequest.allow_uplink_change`, `DeviceInfo.accept_unknown_host_key`
- Error codes: `CON005`, `DEP004`–`DEP006` + `code_for_deploy_status()` mapping
- `pyproject.toml`, `requirements-dev.txt`, GitHub Actions CI (pytest on 3.10–3.12)
- access_switch template: `port_prefix` / `access_port_start` / `access_port_end` (default 1–16)

### Fixed
- `DeviceInfo.baudrate` now passed into `SerialConfig` / `Connection`

### Tests
- **129 passed**

## [0.3.2] - 2026-08-07

Short-term hardening: version alignment, SSH deploy guard, license, regression tests.

### Security
- **SSH real deploy disabled by default** (`allow_ssh_deploy=False`); only `dry_run=True` or explicit `allow_ssh_deploy=True` may proceed. Prefer Console for config changes.

### Added
- `AgentRequest.allow_ssh_deploy` field (default False)
- `LICENSE` (MIT)
- Regression tests: planner `description ##`, interface-view prompts, netmiko ConnectHandler kwargs, SSH deploy default block

### Changed
- Version docs aligned to **0.3.2** (`SKILL.md` / `README.md` / `src.__version__`)
- `.gitignore` ignores local live-test artifacts (`_live_partial_results.json`)

### Tests
- **119 passed** (added live-hardening + SSH deploy guard cases)

## [0.3.1] - 2026-08-07

Live-device hardening from COM4 / SSH batch validation on S1730S.

### Fixed
- Console prompt detection no longer treats `Password:` as the device prompt after login
- `is_prompt()` only matches CLI prompts so command reads are not truncated on auth banners
- Interface-view prompts such as `[host-GigabitEthernet0/0/24]` are recognized; connect returns to user view
- Planner/deployer no longer strip `description ##...##` into a bare incomplete `description`
- netmiko 4.x: drop invalid `read_timeout` on `ConnectHandler` (use `send_command(read_timeout=...)`)

### Added
- `scripts/live_full_module_test.py` and `templates/_live_test_safe.j2` for optional live soak tests (env-based secrets)

### Tests
- **110 passed** (prompt semantics updated)

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

[0.4.0]: https://github.com/Maskbugzero/huawei-switch-skill/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/Maskbugzero/huawei-switch-skill/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/Maskbugzero/huawei-switch-skill/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/Maskbugzero/huawei-switch-skill/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Maskbugzero/huawei-switch-skill/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Maskbugzero/huawei-switch-skill/releases/tag/v0.1.0
