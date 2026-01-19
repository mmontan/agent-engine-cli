from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from agent_engine_cli.main import app

runner = CliRunner()

@patch("agent_engine_cli.main.AgentEngineClient")
def test_get_agent_shows_effective_identity(mock_client_class):
    """Test get command shows effective identity."""
    mock_spec = MagicMock()
    mock_spec.effective_identity = "service-account@test.iam.gserviceaccount.com"

    mock_agent = MagicMock()
    mock_agent.name = None  # Explicitly set to None so it falls through to resource_name
    mock_agent.resource_name = "projects/test/locations/us-central1/reasoningEngines/agent1"
    mock_agent.display_name = "Test Agent"
    mock_agent.description = "A test agent"
    mock_agent.create_time = "2024-01-01T00:00:00Z"
    mock_agent.update_time = "2024-01-02T00:00:00Z"
    
    # Mock api_resource structure
    mock_api_resource = MagicMock()
    mock_api_resource.spec = mock_spec
    mock_agent.api_resource = mock_api_resource
    
    mock_agent.spec = mock_spec

    mock_client = MagicMock()
    mock_client.get_agent.return_value = mock_agent
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app, ["get", "agent1", "--project", "test-project", "--location", "us-central1"]
    )
    
    print(result.stdout)
    assert result.exit_code == 0
    assert "Effective Identity" in result.stdout
    assert "service-account@test.iam.gserviceaccount.com" in result.stdout

if __name__ == "__main__":
    # Manually run the test function if executed directly (though pytest is preferred)
    try:
        # We need to manually patch if running as script, but easier to use pytest
        pass
    except Exception as e:
        print(e)
