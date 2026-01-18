"""Client wrapper for Vertex AI Agent Engine API."""

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

import vertexai
from vertexai import agent_engines
from vertexai import types


@runtime_checkable
class AgentSpec(Protocol):
    """Agent specification with identity information."""

    effective_identity: str


@runtime_checkable
class AgentResource(Protocol):
    """Agent resource from Vertex AI API."""

    name: str
    display_name: str
    create_time: datetime
    update_time: datetime
    spec: AgentSpec | None


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

    def list_agents(self) -> list[AgentResource]:
        """List all agents in the project.

        Returns:
            List of AgentEngine api_resource instances (v1beta1)
        """
        return [agent.api_resource for agent in self._client.agent_engines.list()]

    def get_agent(self, agent_id: str) -> AgentResource:
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

    def create_agent(
        self,
        display_name: str,
        identity_type: str,
        service_account: str | None = None,
    ) -> AgentResource:
        """Create a new agent without deploying code.

        Args:
            display_name: Human-readable name for the agent
            identity_type: Identity type ('agent_identity' or 'service_account')
            service_account: Service account email (only used with service_account identity)

        Returns:
            The created agent's api_resource
        """
        config = {
            "display_name": display_name,
        }

        if identity_type == "agent_identity":
            config["identity_type"] = types.IdentityType.AGENT_IDENTITY
        elif identity_type == "service_account":
            config["identity_type"] = types.IdentityType.SERVICE_ACCOUNT
            if service_account:
                config["service_account"] = service_account

        result = self._client.agent_engines.create(config=config)
        return result.api_resource

    def delete_agent(self, agent_id: str, force: bool = False) -> None:
        """Delete an agent.

        Args:
            agent_id: The agent resource ID or full resource name
            force: Force deletion even if agent has associated resources
        """
        if "/" not in agent_id:
            resource_name = (
                f"projects/{self.project}/locations/{self.location}/"
                f"reasoningEngines/{agent_id}"
            )
        else:
            resource_name = agent_id

        agent_engines.delete(resource_name, force=force)
