from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from agent_engine_cli.main import app

runner = CliRunner()

@patch("agent_engine_cli.main.AgentEngineClient")
def test_get_agent_missing_resource_name_attribute(mock_client_class):
    """Test get command when agent object has 'name' but no 'resource_name'."""
    class MockAgent:
        name = "projects/test/locations/us-central1/reasoningEngines/agent1"
        display_name = "Test Agent"
        description = "A test agent"
        create_time = "2024-01-01T00:00:00Z"
        update_time = "2024-01-02T00:00:00Z"
        spec = None
        # resource_name is intentionally missing

    mock_client = MagicMock()
    mock_client.get_agent.return_value = MockAgent()
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app, ["get", "agent1", "--project", "test-project", "--location", "us-central1"]
    )
    
    assert result.exit_code == 0
    assert "Test Agent" in result.stdout
    assert "agent1" in result.stdout

@patch("agent_engine_cli.main.AgentEngineClient")
def test_get_agent_full_missing_resource_name_attribute(mock_client_class):
    """Test get --full command when agent object has 'name' but no 'resource_name'."""
    class MockAgent:
        name = "projects/test/locations/us-central1/reasoningEngines/agent1"
        display_name = "Test Agent"
        description = "A test agent"
        create_time = "2024-01-01T00:00:00Z"
        update_time = "2024-01-02T00:00:00Z"
        spec = None
        # resource_name is intentionally missing

    mock_client = MagicMock()
    mock_client.get_agent.return_value = MockAgent()
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app, ["get", "agent1", "--project", "test-project", "--location", "us-central1", "--full"]
    )
    
    assert result.exit_code == 0
    assert "resource_name" in result.stdout
    assert "projects/test/locations/us-central1/reasoningEngines/agent1" in result.stdout
