"""Client wrapper for Vertex AI Agent Engine API."""

from typing import Any

import vertexai
from vertexai import agent_engines
from vertexai import types


class AgentEngineClient:
    """Client for interacting with Vertex AI Agent Engine."""

    def __init__(self, project: str, location: str):
        """Initialize the client with project and location.

        Args:
            project: Google Cloud project ID
            location: Google Cloud region
        """
        self.project = project
        self.location = location
        vertexai.init(project=project, location=location)

        self._client = vertexai.Client(
            project=project,
            location=location,
            http_options={"api_version": "v1beta1"},
        )

    def list_agents(self) -> list[Any]:
        """List all agents in the project.

        Returns:
            List of AgentEngine instances
        """
        return list(agent_engines.list())

    def get_agent(self, agent_id: str) -> Any:
        """Get details for a specific agent.

        Args:
            agent_id: The agent resource ID or full resource name

        Returns:
            AgentEngine instance with agent details
        """
        if "/" not in agent_id:
            resource_name = (
                f"projects/{self.project}/locations/{self.location}/"
                f"reasoningEngines/{agent_id}"
            )
        else:
            resource_name = agent_id

        return agent_engines.get(resource_name)

    def create_agent(self, display_name: str, identity_type: str) -> Any:
        """Create a new agent without deploying code.

        Args:
            display_name: Human-readable name for the agent
            identity_type: Identity type ('agent_identity' or 'default')

        Returns:
            The created agent's api_resource
        """
        config = {
            "display_name": display_name,
        }

        if identity_type == "agent_identity":
            config["identity_type"] = types.IdentityType.AGENT_IDENTITY

        result = self._client.agent_engines.create(config=config)
        return result.api_resource
