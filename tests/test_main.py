"""Tests for CLI commands."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from agent_engine_cli.config import ConfigurationError
from agent_engine_cli.main import app

runner = CliRunner(env={"COLUMNS": "200", "NO_COLOR": "1", "TERM": "dumb"})


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Agent Engine CLI v0.1.3" in result.stdout


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
        assert "2024-01-01" in result.stdout


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
        mock_method = MagicMock()
        mock_method.name = "query"
        mock_method.metadata = {"agent_card": "{\"name\": \"test-card\"}"}

        mock_spec = MagicMock()
        mock_spec.effective_identity = "test-identity"
        mock_spec.agent_framework = "langchain"
        mock_spec.class_methods = [mock_method]

        mock_agent = MagicMock()
        mock_agent.name = None  # Explicitly set to None so it falls through to resource_name
        mock_agent.resource_name = "projects/test/locations/us-central1/reasoningEngines/agent1"
        mock_agent.display_name = "Test Agent"
        mock_agent.description = "A test agent"
        mock_agent.create_time = "2024-01-01T00:00:00Z"
        mock_agent.update_time = "2024-01-02T00:00:00Z"
        mock_agent.api_resource.spec = mock_spec
        mock_agent.spec = mock_spec

        mock_client = MagicMock()
        mock_client.get_agent.return_value = mock_agent
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["get", "agent1", "--project", "test-project", "--location", "us-central1"]
        )
        assert result.exit_code == 0
        assert "Test Agent" in result.stdout
        assert "A test agent" in result.stdout
        assert "Agent Framework: langchain" in result.stdout
        assert "Class Methods:" in result.stdout
        assert "query" in result.stdout
        assert "Agent Card: {\"name\": \"test-card\"}" in result.stdout

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


class TestChatCommand:
    def test_chat_help(self):
        """Test chat command help."""
        result = runner.invoke(app, ["chat", "--help"])
        assert result.exit_code == 0
        assert "--project" in result.stdout
        assert "--location" in result.stdout
        assert "--user" in result.stdout
        assert "--debug" in result.stdout

    @patch("agent_engine_cli.main.run_chat")
    def test_chat_invokes_run_chat(self, mock_run_chat):
        """Test chat command invokes run_chat with correct arguments."""
        mock_run_chat.return_value = AsyncMock()()

        result = runner.invoke(
            app,
            ["chat", "agent123", "--project", "test-project", "--location", "us-central1"],
        )
        assert result.exit_code == 0
        mock_run_chat.assert_called_once_with(
            project="test-project",
            location="us-central1",
            agent_id="agent123",
            user_id="cli-user",
            debug=False,
        )

    @patch("agent_engine_cli.main.run_chat")
    def test_chat_with_user_and_debug(self, mock_run_chat):
        """Test chat command with custom user and debug flag."""
        mock_run_chat.return_value = AsyncMock()()

        result = runner.invoke(
            app,
            ["chat", "agent123", "--project", "test-project", "--location", "us-central1",
             "--user", "my-user", "--debug"],
        )
        assert result.exit_code == 0
        mock_run_chat.assert_called_once_with(
            project="test-project",
            location="us-central1",
            agent_id="agent123",
            user_id="my-user",
            debug=True,
        )

    @patch("agent_engine_cli.main.run_chat")
    def test_chat_error_handling(self, mock_run_chat):
        """Test chat command handles errors gracefully."""
        mock_run_chat.side_effect = Exception("Connection failed")

        result = runner.invoke(
            app,
            ["chat", "agent123", "--project", "test-project", "--location", "us-central1"],
        )
        assert result.exit_code == 1
        assert "Error in chat session" in result.stdout


class TestADCFallback:
    """Tests for ADC (Application Default Credentials) project fallback."""

    @patch("agent_engine_cli.main.AgentEngineClient")
    @patch("agent_engine_cli.main.resolve_project")
    def test_list_uses_adc_project(self, mock_resolve, mock_client_class):
        """Test list command uses ADC project when --project not provided."""
        mock_resolve.return_value = "adc-project"
        mock_client = MagicMock()
        mock_client.list_agents.return_value = []
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["list", "--location", "us-central1"])
        assert result.exit_code == 0
        mock_resolve.assert_called_once_with(None)
        mock_client_class.assert_called_once_with(project="adc-project", location="us-central1")

    @patch("agent_engine_cli.main.resolve_project")
    def test_list_error_when_no_project(self, mock_resolve):
        """Test list command shows error when no project available."""
        mock_resolve.side_effect = ConfigurationError("No project specified")

        result = runner.invoke(app, ["list", "--location", "us-central1"])
        assert result.exit_code == 1
        assert "Error: No project specified" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    @patch("agent_engine_cli.main.resolve_project")
    def test_get_uses_adc_project(self, mock_resolve, mock_client_class):
        """Test get command uses ADC project when --project not provided."""
        mock_resolve.return_value = "adc-project"
        mock_agent = MagicMock()
        mock_agent.name = "projects/adc-project/locations/us-central1/reasoningEngines/agent1"
        mock_agent.display_name = "Test"
        mock_agent.description = "Test"
        mock_agent.create_time = "2024-01-01"
        mock_agent.update_time = "2024-01-01"
        mock_agent.api_resource = None
        mock_agent.spec = None

        mock_client = MagicMock()
        mock_client.get_agent.return_value = mock_agent
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["get", "agent1", "--location", "us-central1"])
        assert result.exit_code == 0
        mock_resolve.assert_called_once_with(None)

    @patch("agent_engine_cli.main.AgentEngineClient")
    @patch("agent_engine_cli.main.resolve_project")
    def test_create_uses_adc_project(self, mock_resolve, mock_client_class):
        """Test create command uses ADC project when --project not provided."""
        mock_resolve.return_value = "adc-project"
        mock_agent = MagicMock()
        mock_agent.name = "projects/adc-project/locations/us-central1/reasoningEngines/new-agent"

        mock_client = MagicMock()
        mock_client.create_agent.return_value = mock_agent
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["create", "Test Agent", "--location", "us-central1"])
        assert result.exit_code == 0
        mock_resolve.assert_called_once_with(None)

    @patch("agent_engine_cli.main.AgentEngineClient")
    @patch("agent_engine_cli.main.resolve_project")
    def test_delete_uses_adc_project(self, mock_resolve, mock_client_class):
        """Test delete command uses ADC project when --project not provided."""
        mock_resolve.return_value = "adc-project"
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["delete", "agent1", "--location", "us-central1", "--yes"])
        assert result.exit_code == 0
        mock_resolve.assert_called_once_with(None)

    @patch("agent_engine_cli.main.run_chat")
    @patch("agent_engine_cli.main.resolve_project")
    def test_chat_uses_adc_project(self, mock_resolve, mock_run_chat):
        """Test chat command uses ADC project when --project not provided."""
        mock_resolve.return_value = "adc-project"
        mock_run_chat.return_value = AsyncMock()()

        result = runner.invoke(app, ["chat", "agent1", "--location", "us-central1"])
        assert result.exit_code == 0
        mock_resolve.assert_called_once_with(None)
        mock_run_chat.assert_called_once_with(
            project="adc-project",
            location="us-central1",
            agent_id="agent1",
            user_id="cli-user",
            debug=False,
        )

    @patch("agent_engine_cli.main.AgentEngineClient")
    @patch("agent_engine_cli.main.resolve_project")
    def test_explicit_project_still_works(self, mock_resolve, mock_client_class):
        """Test that explicit --project still works and is passed to resolve_project."""
        mock_resolve.return_value = "explicit-project"
        mock_client = MagicMock()
        mock_client.list_agents.return_value = []
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["list", "--project", "explicit-project", "--location", "us-central1"])
        assert result.exit_code == 0
        mock_resolve.assert_called_once_with("explicit-project")


class TestSessionsListCommand:
    def test_sessions_list_help(self):
        """Test sessions list command help."""
        result = runner.invoke(app, ["sessions", "list", "--help"])
        assert result.exit_code == 0
        assert "--project" in result.stdout
        assert "--location" in result.stdout
        assert "AGENT_ID" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_sessions_list_no_sessions(self, mock_client_class):
        """Test sessions list with no sessions."""
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = []
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["sessions", "list", "agent123", "--project", "test-project", "--location", "us-central1"]
        )
        assert result.exit_code == 0
        assert "No sessions found" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_sessions_list_with_sessions(self, mock_client_class):
        """Test sessions list with sessions."""
        mock_session = MagicMock()
        mock_session.name = "projects/test/locations/us-central1/reasoningEngines/agent1/sessions/session123"
        mock_session.display_name = "my_session"
        mock_session.user_id = "user-456"
        mock_session.create_time = datetime(2024, 1, 15, 10, 30, 0)
        mock_session.expire_time = datetime(2024, 1, 16, 10, 30, 0)

        mock_client = MagicMock()
        mock_client.list_sessions.return_value = [mock_session]
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["sessions", "list", "agent1", "--project", "test-project", "--location", "us-central1"]
        )
        assert result.exit_code == 0
        assert "session123" in result.stdout
        assert "my_session" in result.stdout
        assert "user-456" in result.stdout
        assert "2024-01-15" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_sessions_list_error(self, mock_client_class):
        """Test sessions list when an error occurs."""
        mock_client = MagicMock()
        mock_client.list_sessions.side_effect = Exception("Agent not found")
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["sessions", "list", "agent123", "--project", "test-project", "--location", "us-central1"]
        )
        assert result.exit_code == 1
        assert "Error listing sessions" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    @patch("agent_engine_cli.main.resolve_project")
    def test_sessions_list_uses_adc_project(self, mock_resolve, mock_client_class):
        """Test sessions list uses ADC project when --project not provided."""
        mock_resolve.return_value = "adc-project"
        mock_client = MagicMock()
        mock_client.list_sessions.return_value = []
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["sessions", "list", "agent1", "--location", "us-central1"])
        assert result.exit_code == 0
        mock_resolve.assert_called_once_with(None)
        mock_client_class.assert_called_once_with(project="adc-project", location="us-central1")


class TestSandboxesListCommand:
    def test_sandboxes_list_help(self):
        """Test sandboxes list command help."""
        result = runner.invoke(app, ["sandboxes", "list", "--help"])
        assert result.exit_code == 0
        assert "--project" in result.stdout
        assert "--location" in result.stdout
        assert "AGENT_ID" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_sandboxes_list_no_sandboxes(self, mock_client_class):
        """Test sandboxes list with no sandboxes."""
        mock_client = MagicMock()
        mock_client.list_sandboxes.return_value = []
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["sandboxes", "list", "agent123", "--project", "test-project", "--location", "us-central1"]
        )
        assert result.exit_code == 0
        assert "No sandboxes found" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_sandboxes_list_with_sandboxes(self, mock_client_class):
        """Test sandboxes list with sandboxes."""
        mock_state = MagicMock()
        mock_state.value = "STATE_RUNNING"

        mock_sandbox = MagicMock()
        mock_sandbox.name = "projects/test/locations/us-central1/reasoningEngines/agent1/sandboxes/sandbox123"
        mock_sandbox.display_name = "my_sandbox"
        mock_sandbox.state = mock_state
        mock_sandbox.create_time = datetime(2024, 2, 20, 14, 30, 0)
        mock_sandbox.expire_time = datetime(2024, 2, 21, 14, 30, 0)

        mock_client = MagicMock()
        mock_client.list_sandboxes.return_value = [mock_sandbox]
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["sandboxes", "list", "agent1", "--project", "test-project", "--location", "us-central1"]
        )
        assert result.exit_code == 0
        assert "sandbox123" in result.stdout
        assert "my_sandbox" in result.stdout
        assert "RUNNING" in result.stdout
        assert "2024-02-20" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_sandboxes_list_error(self, mock_client_class):
        """Test sandboxes list when an error occurs."""
        mock_client = MagicMock()
        mock_client.list_sandboxes.side_effect = Exception("Agent not found")
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["sandboxes", "list", "agent123", "--project", "test-project", "--location", "us-central1"]
        )
        assert result.exit_code == 1
        assert "Error listing sandboxes" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    @patch("agent_engine_cli.main.resolve_project")
    def test_sandboxes_list_uses_adc_project(self, mock_resolve, mock_client_class):
        """Test sandboxes list uses ADC project when --project not provided."""
        mock_resolve.return_value = "adc-project"
        mock_client = MagicMock()
        mock_client.list_sandboxes.return_value = []
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["sandboxes", "list", "agent1", "--location", "us-central1"])
        assert result.exit_code == 0
        mock_resolve.assert_called_once_with(None)
        mock_client_class.assert_called_once_with(project="adc-project", location="us-central1")


class TestMemoriesListCommand:
    def test_memories_list_help(self):
        """Test memories list command help."""
        result = runner.invoke(app, ["memories", "list", "--help"])
        assert result.exit_code == 0
        assert "--project" in result.stdout
        assert "--location" in result.stdout
        assert "AGENT_ID" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_memories_list_no_memories(self, mock_client_class):
        """Test memories list with no memories."""
        mock_client = MagicMock()
        mock_client.list_memories.return_value = []
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["memories", "list", "agent123", "--project", "test-project", "--location", "us-central1"]
        )
        assert result.exit_code == 0
        assert "No memories found" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_memories_list_with_memories(self, mock_client_class):
        """Test memories list with memories."""
        mock_memory = MagicMock()
        mock_memory.name = "projects/test/locations/us-central1/reasoningEngines/agent1/memories/memory123"
        mock_memory.display_name = "user_preference"
        mock_memory.scope = {"user_id": "user-123"}
        mock_memory.fact = "User prefers dark mode"
        mock_memory.create_time = datetime(2024, 3, 10, 9, 15, 0)
        mock_memory.expire_time = datetime(2024, 4, 10, 9, 15, 0)

        mock_client = MagicMock()
        mock_client.list_memories.return_value = [mock_memory]
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["memories", "list", "agent1", "--project", "test-project", "--location", "us-central1"]
        )
        assert result.exit_code == 0
        assert "memory123" in result.stdout
        assert "user_id=" in result.stdout  # Scope key (value may be truncated)
        assert "dark mode" in result.stdout
        assert "2024-03-10" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    def test_memories_list_error(self, mock_client_class):
        """Test memories list when an error occurs."""
        mock_client = MagicMock()
        mock_client.list_memories.side_effect = Exception("Agent not found")
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["memories", "list", "agent123", "--project", "test-project", "--location", "us-central1"]
        )
        assert result.exit_code == 1
        assert "Error listing memories" in result.stdout

    @patch("agent_engine_cli.main.AgentEngineClient")
    @patch("agent_engine_cli.main.resolve_project")
    def test_memories_list_uses_adc_project(self, mock_resolve, mock_client_class):
        """Test memories list uses ADC project when --project not provided."""
        mock_resolve.return_value = "adc-project"
        mock_client = MagicMock()
        mock_client.list_memories.return_value = []
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["memories", "list", "agent1", "--location", "us-central1"])
        assert result.exit_code == 0
        mock_resolve.assert_called_once_with(None)
        mock_client_class.assert_called_once_with(project="adc-project", location="us-central1")
