# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
