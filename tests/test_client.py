"""Tests for the AgentEngineClient."""

from unittest.mock import MagicMock, patch

import pytest

from agent_engine_cli.client import AgentEngineClient


@pytest.fixture
def mock_vertexai():
    """Mock vertexai module."""
    with patch("agent_engine_cli.client.vertexai") as mock_v:
        yield mock_v


@pytest.fixture
def mock_agent_engines():
    """Mock agent_engines module."""
    with patch("agent_engine_cli.client.agent_engines") as mock_ae:
        yield mock_ae


@pytest.fixture
def mock_types():
    """Mock types module."""
    with patch("agent_engine_cli.client.types") as mock_t:
        yield mock_t


class TestAgentEngineClient:
    def test_init(self, mock_vertexai, mock_agent_engines, mock_types):
        """Test that client initializes correctly."""
        client = AgentEngineClient(project="test-project", location="us-central1")

        assert client.project == "test-project"
        assert client.location == "us-central1"
        mock_vertexai.init.assert_called_once_with(project="test-project", location="us-central1")
        mock_vertexai.Client.assert_called_once()

    def test_init_custom_location(self, mock_vertexai, mock_agent_engines, mock_types):
        """Test that client uses custom location."""
        client = AgentEngineClient(project="test-project", location="europe-west1")

        assert client.location == "europe-west1"

    def test_list_agents(self, mock_vertexai, mock_agent_engines, mock_types):
        """Test listing agents."""
        mock_api_resource1 = MagicMock()
        mock_api_resource1.name = "projects/test/locations/us-central1/reasoningEngines/agent1"
        mock_api_resource1.display_name = "Agent 1"

        mock_api_resource2 = MagicMock()
        mock_api_resource2.name = "projects/test/locations/us-central1/reasoningEngines/agent2"
        mock_api_resource2.display_name = "Agent 2"

        mock_agent1 = MagicMock()
        mock_agent1.api_resource = mock_api_resource1
        mock_agent2 = MagicMock()
        mock_agent2.api_resource = mock_api_resource2

        mock_vertexai.Client.return_value.agent_engines.list.return_value = [mock_agent1, mock_agent2]

        client = AgentEngineClient(project="test-project", location="us-central1")
        agents = client.list_agents()

        assert len(list(agents)) == 2
        mock_vertexai.Client.return_value.agent_engines.list.assert_called_once()

    def test_list_agents_empty(self, mock_vertexai, mock_agent_engines, mock_types):
        """Test listing agents when none exist."""
        mock_agent_engines.list.return_value = []

        client = AgentEngineClient(project="test-project", location="us-central1")
        agents = client.list_agents()

        assert len(list(agents)) == 0

    def test_get_agent_with_id(self, mock_vertexai, mock_agent_engines, mock_types):
        """Test getting agent by short ID."""
        mock_agent = MagicMock()
        mock_vertexai.Client.return_value.agent_engines.get.return_value = mock_agent

        client = AgentEngineClient(project="test-project", location="us-central1")
        agent = client.get_agent("agent123")

        expected_name = "projects/test-project/locations/us-central1/reasoningEngines/agent123"
        mock_vertexai.Client.return_value.agent_engines.get.assert_called_with(name=expected_name)

    def test_get_agent_with_full_name(self, mock_vertexai, mock_agent_engines, mock_types):
        """Test getting agent by full resource name."""
        mock_agent = MagicMock()
        mock_vertexai.Client.return_value.agent_engines.get.return_value = mock_agent

        full_name = "projects/other-project/locations/europe-west1/reasoningEngines/agent456"
        client = AgentEngineClient(project="test-project", location="us-central1")
        agent = client.get_agent(full_name)

        mock_vertexai.Client.return_value.agent_engines.get.assert_called_with(name=full_name)

    def test_create_agent_service_account_identity(self, mock_vertexai, mock_agent_engines, mock_types):
        """Test creating agent with service_account identity."""
        mock_result = MagicMock()
        mock_result.resource_name = "projects/test-project/locations/us-central1/reasoningEngines/new-agent"
        mock_vertexai.Client.return_value.agent_engines.create.return_value = mock_result

        client = AgentEngineClient(project="test-project", location="us-central1")
        agent = client.create_agent(display_name="Test Agent", identity_type="service_account")

        mock_vertexai.Client.return_value.agent_engines.create.assert_called_once()
        call_kwargs = mock_vertexai.Client.return_value.agent_engines.create.call_args[1]
        assert call_kwargs["config"]["display_name"] == "Test Agent"
        assert call_kwargs["config"]["identity_type"] == mock_types.IdentityType.SERVICE_ACCOUNT
        assert "service_account" not in call_kwargs["config"]

    def test_create_agent_with_custom_service_account(self, mock_vertexai, mock_agent_engines, mock_types):
        """Test creating agent with a specific service account."""
        mock_result = MagicMock()
        mock_result.resource_name = "projects/test-project/locations/us-central1/reasoningEngines/new-agent"
        mock_vertexai.Client.return_value.agent_engines.create.return_value = mock_result

        client = AgentEngineClient(project="test-project", location="us-central1")
        agent = client.create_agent(
            display_name="Test Agent",
            identity_type="service_account",
            service_account="my-sa@test-project.iam.gserviceaccount.com",
        )

        mock_vertexai.Client.return_value.agent_engines.create.assert_called_once()
        call_kwargs = mock_vertexai.Client.return_value.agent_engines.create.call_args[1]
        assert call_kwargs["config"]["display_name"] == "Test Agent"
        assert call_kwargs["config"]["identity_type"] == mock_types.IdentityType.SERVICE_ACCOUNT
        assert call_kwargs["config"]["service_account"] == "my-sa@test-project.iam.gserviceaccount.com"

    def test_create_agent_with_agent_identity(self, mock_vertexai, mock_agent_engines, mock_types):
        """Test creating agent with agent_identity type."""
        mock_result = MagicMock()
        mock_result.resource_name = "projects/test-project/locations/us-central1/reasoningEngines/new-agent"
        mock_vertexai.Client.return_value.agent_engines.create.return_value = mock_result

        client = AgentEngineClient(project="test-project", location="us-central1")
        agent = client.create_agent(display_name="Test Agent", identity_type="agent_identity")

        mock_vertexai.Client.return_value.agent_engines.create.assert_called_once()
        call_kwargs = mock_vertexai.Client.return_value.agent_engines.create.call_args[1]
        assert call_kwargs["config"]["display_name"] == "Test Agent"
        assert call_kwargs["config"]["identity_type"] == mock_types.IdentityType.AGENT_IDENTITY

    def test_delete_agent_with_id(self, mock_vertexai, mock_agent_engines, mock_types):
        """Test deleting agent by short ID."""
        client = AgentEngineClient(project="test-project", location="us-central1")
        client.delete_agent("agent123")

        expected_name = "projects/test-project/locations/us-central1/reasoningEngines/agent123"
        mock_agent_engines.delete.assert_called_with(expected_name, force=False)

    def test_delete_agent_with_full_name(self, mock_vertexai, mock_agent_engines, mock_types):
        """Test deleting agent by full resource name."""
        full_name = "projects/other-project/locations/europe-west1/reasoningEngines/agent456"
        client = AgentEngineClient(project="test-project", location="us-central1")
        client.delete_agent(full_name)

        mock_agent_engines.delete.assert_called_with(full_name, force=False)

    def test_delete_agent_with_force(self, mock_vertexai, mock_agent_engines, mock_types):
        """Test deleting agent with force option."""
        client = AgentEngineClient(project="test-project", location="us-central1")
        client.delete_agent("agent123", force=True)

        expected_name = "projects/test-project/locations/us-central1/reasoningEngines/agent123"
        mock_agent_engines.delete.assert_called_with(expected_name, force=True)
