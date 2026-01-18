from typer.testing import CliRunner
from agent_engine_cli.main import app

runner = CliRunner()

def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Agent Engine CLI v0.1.0" in result.stdout
