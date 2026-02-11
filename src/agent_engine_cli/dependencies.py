"""Dependency injection for AgentEngineClient."""

from agent_engine_cli.client import AgentEngineClient


def get_client(project: str, location: str) -> AgentEngineClient:
    """Create a new AgentEngineClient instance.

    This function serves as a dependency injection point for the CLI.
    Tests can patch this function to return a fake client.

    Args:
        project: Google Cloud project ID
        location: Google Cloud region

    Returns:
        An instance of AgentEngineClient
    """
    return AgentEngineClient(project=project, location=location)
