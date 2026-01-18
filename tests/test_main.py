"""Tests for CLI commands."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from agent_engine_cli.main import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Agent Engine CLI v0.1.0" in result.stdout


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
        mock_spec = MagicMock()
        mock_spec.effective_identity = "agents.global.proj-123.system.id.goog/resources/test"

        # v1beta1 api_resource uses 'name' instead of 'resource_name'
        mock_agent = MagicMock()
        mock_agent.name = "projects/test/locations/us-central1/reasoningEngines/agent1"
        mock_agent.display_name = "Test Agent"
        mock_agent.create_time = datetime(2024, 1, 1, 12, 30, 0)
        mock_agent.update_time = datetime(2024, 1, 2, 14, 45, 0)
        mock_agent.spec = mock_spec

        mock_client = MagicMock()
        mock_client.list_agents.return_value = [mock_agent]
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["list", "--project", "test-project", "--location", "us-central1"])
        assert result.exit_code == 0
        assert "agent1" in result.stdout
        assert "Test Agent" in result.stdout
        assert "2024-01-01 12:30" in result.stdout


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
        assert "--identity" in result.stdout

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
            service_account=None,
        )

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_create_agent_with_service_account_identity(self, mock_client_class):
        """Test create command with service_account identity type."""
        mock_agent = MagicMock()
        mock_agent.name = "projects/test/locations/us-central1/reasoningEngines/new-agent"
        mock_agent.resource_name = None

        mock_client = MagicMock()
        mock_client.create_agent.return_value = mock_agent
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["create", "My Agent", "--project", "test-project", "--location", "us-central1", "--identity", "service_account"]
        )
        assert result.exit_code == 0
        mock_client.create_agent.assert_called_once_with(
            display_name="My Agent",
            identity_type="service_account",
            service_account=None,
        )

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_create_agent_with_custom_service_account(self, mock_client_class):
        """Test create command with a specific service account."""
        mock_agent = MagicMock()
        mock_agent.name = "projects/test/locations/us-central1/reasoningEngines/new-agent"
        mock_agent.resource_name = None

        mock_client = MagicMock()
        mock_client.create_agent.return_value = mock_agent
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["create", "My Agent", "--project", "test-project", "--location", "us-central1",
                  "--identity", "service_account", "--service-account", "my-sa@proj.iam.gserviceaccount.com"]
        )
        assert result.exit_code == 0
        mock_client.create_agent.assert_called_once_with(
            display_name="My Agent",
            identity_type="service_account",
            service_account="my-sa@proj.iam.gserviceaccount.com",
        )


class TestDeleteCommand:
    def test_delete_help(self):
        """Test delete command help."""
        result = runner.invoke(app, ["delete", "--help"])
        assert result.exit_code == 0
        assert "--project" in result.stdout
        assert "--location" in result.stdout
        assert "--force" in result.stdout
        assert "--yes" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_delete_agent_with_confirmation(self, mock_client_class):
        """Test delete command with confirmation prompt."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app,
            ["delete", "agent123", "--project", "test-project", "--location", "us-central1"],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "deleted" in result.stdout
        mock_client.delete_agent.assert_called_once_with("agent123", force=False)

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_delete_agent_abort(self, mock_client_class):
        """Test delete command when user aborts."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app,
            ["delete", "agent123", "--project", "test-project", "--location", "us-central1"],
            input="n\n",
        )
        assert result.exit_code == 0
        assert "Aborted" in result.stdout
        mock_client.delete_agent.assert_not_called()

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_delete_agent_with_yes_flag(self, mock_client_class):
        """Test delete command with --yes flag to skip confirmation."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app,
            ["delete", "agent123", "--project", "test-project", "--location", "us-central1", "--yes"],
        )
        assert result.exit_code == 0
        assert "deleted" in result.stdout
        mock_client.delete_agent.assert_called_once_with("agent123", force=False)

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_delete_agent_with_force(self, mock_client_class):
        """Test delete command with --force flag."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app,
            ["delete", "agent123", "--project", "test-project", "--location", "us-central1", "--yes", "--force"],
        )
        assert result.exit_code == 0
        mock_client.delete_agent.assert_called_once_with("agent123", force=True)

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_delete_agent_error(self, mock_client_class):
        """Test delete command when an error occurs."""
        mock_client = MagicMock()
        mock_client.delete_agent.side_effect = Exception("Not found")
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app,
            ["delete", "agent123", "--project", "test-project", "--location", "us-central1", "--yes"],
        )
        assert result.exit_code == 1
        assert "Error deleting agent" in result.stdout
