# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agent Engine CLI (`ae`) is a command-line interface for managing Agent Engine. Built with Python using Typer for CLI framework and Rich for terminal output.

## Development Commands

```bash
# Install dependencies and project in development mode
uv sync

# Run the CLI
uv run ae --help

# Run all tests
uv run pytest

# Run a specific test
uv run pytest tests/test_main.py::test_version
```

## Architecture

- **Entry point**: `src/agent_engine_cli/main.py` - Contains the Typer app instance and all CLI commands
- **CLI binary**: Installed as `ae` via `[project.scripts]` in pyproject.toml
- **Testing**: Uses Typer's `CliRunner` for CLI command testing
