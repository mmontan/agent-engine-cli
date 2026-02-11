# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2026-02-10

### Security

- Escape all dynamic values in Rich `console.print()` calls to prevent markup injection from agent responses and API errors.
- Add credential exposure warning when `--debug` mode is enabled.
- Remove unused `requests` dependency to reduce attack surface.
- Validate agent IDs to reject empty, whitespace-only, and control-character inputs.
- Narrow exception handling in ADC config resolution to avoid swallowing unexpected errors.

### Changed

- Minimum Python version bumped from 3.10 to 3.11.
- Deduplicated resource name construction into a shared `_resolve_resource_name()` helper.

## [0.1.3] - 2026-01-25

### Added

- `ae get` now includes class method parameters with types and descriptions in the output.

### Changed

- Updated author information in `pyproject.toml`.
- Version bumped to 0.1.3 to resolve tagging conflicts with 0.1.2.

## [0.1.1] - 2026-01-19

### Added

- `ae sessions list` - List active sessions for an agent
- `ae sandboxes list` - List active sandboxes
- `ae memories list` - List agent memories
- Support for automatic project detection from Application Default Credentials (ADC)

### Changed

- Improved PyPI package metadata

## [0.1.0] - 2025-01-19

### Added

- Initial release of Agent Engine CLI (`ae`)
- `ae list` - List all agents in a Google Cloud project
- `ae get` - Get details for a specific agent
- `ae create` - Create a new agent with configurable identity type
- `ae delete` - Delete an agent with optional force flag
- `ae chat` - Interactive chat session with an agent (streaming support)
- `ae version` - Display CLI version
- Rich terminal output with tables and panels
- Support for Google Cloud authentication via ADC
