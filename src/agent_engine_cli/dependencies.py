"""Dependency injection for AgentEngineClient."""

from agent_engine_cli.client import AgentEngineClient


def get_client(
    project: str,
    location: str,
    *,
    base_url: str | None = None,
    api_version: str | None = None,
) -> AgentEngineClient:
    """Create a new AgentEngineClient instance.

    This function serves as a dependency injection point for the CLI.
    Tests can patch this function to return a fake client.

    Args:
        project: Google Cloud project ID
        location: Google Cloud region
        base_url: Optional override for the Vertex AI base URL
        api_version: Optional API version override

    Returns:
        An instance of AgentEngineClient
    """
    return AgentEngineClient(project=project, location=location, base_url=base_url, api_version=api_version)
