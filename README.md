# Agent Engine CLI

A command-line interface to manage Agent Engine.

## Installation with uv

This project is set up to work seamlessly with `uv`.

1.  **Install uv** (if you haven't already):
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Create a virtual environment and install dependencies**:
    ```bash
    uv venv
    source .venv/bin/activate
    uv pip install -e .
    ```

3.  **Run the CLI**:
    ```bash
    ae --help
    ```

## Running Without Installation

You can run the CLI directly without installing it:

```bash
# Using uv (recommended)
uv run python -m agent_engine_cli.main --help

# Or with plain Python (after installing dependencies)
python -m agent_engine_cli.main --help
```

Example commands:
```bash
uv run python -m agent_engine_cli.main list -p PROJECT_ID -l us-central1
uv run python -m agent_engine_cli.main get AGENT_ID -p PROJECT_ID -l us-central1
```

## Development

To run tests:

```bash
uv pip install -e ".[dev]" # or just use the dev-dependencies if using a uv-managed lockfile workflow
# If using pure uv sync:
uv sync
uv run pytest
```
