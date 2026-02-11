# Agent Engine CLI

A command-line interface to manage Agent Engine.

## Installation

```bash
# With uv (recommended)
uv tool install agent-engine-cli

# With pip
pip install agent-engine-cli
```

After installation, the `ae` command is available globally:

```bash
ae --help
```

## Run Without Installing

```bash
python -m agent_engine_cli --help
```

## Development Setup

1.  **Install uv** (if you haven't already):
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Clone the repo and install dependencies**:
    ```bash
    git clone https://github.com/mmontan/agent-engine-cli.git
    cd agent-engine-cli
    uv sync
    ```

3.  **Run the CLI locally**:
    ```bash
    uv run ae --help
    ```

## Chat with an Agent

Start an interactive chat session with a deployed agent:

```bash
# Basic usage
ae chat AGENT_ID -p PROJECT_ID -l us-central1

# With custom user ID
ae chat AGENT_ID -p PROJECT_ID -l us-central1 --user my-user-id

# With debug logging enabled
ae chat AGENT_ID -p PROJECT_ID -l us-central1 --debug
```

## Development

To run tests:

```bash
uv pip install -e ".[dev]" # or just use the dev-dependencies if using a uv-managed lockfile workflow
# If using pure uv sync:
uv sync
uv run pytest
```
