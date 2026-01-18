"""Tests for the AgentEngineClient."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agent_engine_cli.client import AgentEngineClient
from agent_engine_cli.main import app

runner = CliRunner()


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
        mock_agent1 = MagicMock()
        mock_agent1.resource_name = "projects/test/locations/us-central1/reasoningEngines/agent1"
        mock_agent1.display_name = "Agent 1"

        mock_agent2 = MagicMock()
        mock_agent2.resource_name = "projects/test/locations/us-central1/reasoningEngines/agent2"
        mock_agent2.display_name = "Agent 2"

        mock_agent_engines.list.return_value = [mock_agent1, mock_agent2]

        client = AgentEngineClient(project="test-project", location="us-central1")
        agents = client.list_agents()

        assert len(agents) == 2
        mock_agent_engines.list.assert_called_once()

    def test_list_agents_empty(self, mock_vertexai, mock_agent_engines, mock_types):
        """Test listing agents when none exist."""
        mock_agent_engines.list.return_value = []

        client = AgentEngineClient(project="test-project", location="us-central1")
        agents = client.list_agents()

        assert len(agents) == 0

    def test_get_agent_with_id(self, mock_vertexai, mock_agent_engines, mock_types):
        """Test getting agent by short ID."""
        mock_agent = MagicMock()
        mock_agent_engines.get.return_value = mock_agent

        client = AgentEngineClient(project="test-project", location="us-central1")
        agent = client.get_agent("agent123")

        expected_name = "projects/test-project/locations/us-central1/reasoningEngines/agent123"
        mock_agent_engines.get.assert_called_with(expected_name)

    def test_get_agent_with_full_name(self, mock_vertexai, mock_agent_engines, mock_types):
        """Test getting agent by full resource name."""
        mock_agent = MagicMock()
        mock_agent_engines.get.return_value = mock_agent

        full_name = "projects/other-project/locations/europe-west1/reasoningEngines/agent456"
        client = AgentEngineClient(project="test-project", location="us-central1")
        agent = client.get_agent(full_name)

        mock_agent_engines.get.assert_called_with(full_name)

    def test_create_agent_default_identity(self, mock_vertexai, mock_agent_engines, mock_types):
        """Test creating agent with default identity."""
        mock_result = MagicMock()
        mock_result.resource_name = "projects/test-project/locations/us-central1/reasoningEngines/new-agent"
        mock_vertexai.Client.return_value.agent_engines.create.return_value = mock_result

        client = AgentEngineClient(project="test-project", location="us-central1")
        agent = client.create_agent(display_name="Test Agent", identity_type="default")

        mock_vertexai.Client.return_value.agent_engines.create.assert_called_once()
        call_kwargs = mock_vertexai.Client.return_value.agent_engines.create.call_args[1]
        assert call_kwargs["config"]["display_name"] == "Test Agent"
        assert "identity_type" not in call_kwargs["config"]

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


class TestListCommand:
    def test_list_help(self):
        """Test list command help."""
        result = runner.invoke(app, ["list", "--help"])
        assert result.exit_code == 0
        assert "--project" in result.stdout
        assert "--location" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_list_no_agents(self, mock_client_class):
        """Test list command with no agents."""
        mock_client = MagicMock()
        mock_client.list_agents.return_value = []
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["list", "--project", "test-project", "--location", "us-central1"])
        assert result.exit_code == 0
        assert "No agents found" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_list_with_agents(self, mock_client_class):
        """Test list command with agents."""
        mock_agent = MagicMock()
        mock_agent.resource_name = "projects/test/locations/us-central1/reasoningEngines/agent1"
        mock_agent.display_name = "Test Agent"
        mock_agent.create_time = "2024-01-01T00:00:00Z"
        mock_agent.update_time = "2024-01-02T00:00:00Z"

        mock_client = MagicMock()
        mock_client.list_agents.return_value = [mock_agent]
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["list", "--project", "test-project", "--location", "us-central1"])
        assert result.exit_code == 0
        assert "agent1" in result.stdout
        assert "Test Agent" in result.stdout


class TestGetCommand:
    def test_get_help(self):
        """Test get command help."""
        result = runner.invoke(app, ["get", "--help"])
        assert result.exit_code == 0
        assert "--project" in result.stdout
        assert "--location" in result.stdout
        assert "--full" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_get_agent(self, mock_client_class):
        """Test get command."""
        mock_agent = MagicMock()
        mock_agent.resource_name = "projects/test/locations/us-central1/reasoningEngines/agent1"
        mock_agent.display_name = "Test Agent"
        mock_agent.description = "A test agent"
        mock_agent.create_time = "2024-01-01T00:00:00Z"
        mock_agent.update_time = "2024-01-02T00:00:00Z"

        mock_client = MagicMock()
        mock_client.get_agent.return_value = mock_agent
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["get", "agent1", "--project", "test-project", "--location", "us-central1"]
        )
        assert result.exit_code == 0
        assert "Test Agent" in result.stdout
        assert "A test agent" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_get_agent_full_output(self, mock_client_class):
        """Test get command with --full flag."""
        mock_agent = MagicMock()
        mock_agent.resource_name = "projects/test/locations/us-central1/reasoningEngines/agent1"
        mock_agent.display_name = "Test Agent"
        mock_agent.description = "A test agent"
        mock_agent.create_time = "2024-01-01T00:00:00Z"
        mock_agent.update_time = "2024-01-02T00:00:00Z"
        mock_agent.spec = None

        mock_client = MagicMock()
        mock_client.get_agent.return_value = mock_agent
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["get", "agent1", "--project", "test-project", "--location", "us-central1", "--full"]
        )
        assert result.exit_code == 0
        assert "resource_name" in result.stdout


class TestCreateCommand:
    def test_create_help(self):
        """Test create command help."""
        result = runner.invoke(app, ["create", "--help"])
        assert result.exit_code == 0
        assert "--project" in result.stdout
        assert "--location" in result.stdout
        assert "--identity-type" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_create_agent(self, mock_client_class):
        """Test create command with default agent_identity type."""
        mock_agent = MagicMock()
        mock_agent.name = "projects/test/locations/us-central1/reasoningEngines/new-agent"
        mock_agent.resource_name = None  # api_resource uses name, not resource_name

        mock_client = MagicMock()
        mock_client.create_agent.return_value = mock_agent
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["create", "My Agent", "--project", "test-project", "--location", "us-central1"]
        )
        assert result.exit_code == 0
        assert "Agent created successfully" in result.stdout
        assert "new-agent" in result.stdout
        mock_client.create_agent.assert_called_once_with(
            display_name="My Agent",
            identity_type="agent_identity",
        )

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_create_agent_with_default_identity(self, mock_client_class):
        """Test create command with default (service account) identity type."""
        mock_agent = MagicMock()
        mock_agent.name = "projects/test/locations/us-central1/reasoningEngines/new-agent"
        mock_agent.resource_name = None

        mock_client = MagicMock()
        mock_client.create_agent.return_value = mock_agent
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["create", "My Agent", "--project", "test-project", "--location", "us-central1", "--identity-type", "default"]
        )
        assert result.exit_code == 0
        mock_client.create_agent.assert_called_once_with(
            display_name="My Agent",
            identity_type="default",
        )
