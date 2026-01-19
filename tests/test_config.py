"""Tests for configuration utilities."""

from unittest.mock import patch

import pytest

from agent_engine_cli.config import ConfigurationError, resolve_project


class TestResolveProject:
    def test_explicit_project_returned_directly(self):
        """Test that an explicit project is returned without ADC lookup."""
        result = resolve_project("my-explicit-project")
        assert result == "my-explicit-project"

    @patch("agent_engine_cli.config.console")
    @patch("google.auth.default")
    def test_adc_project_used_when_none_provided(self, mock_auth_default, mock_console):
        """Test that ADC project is used when no project is provided."""
        mock_auth_default.return_value = (None, "adc-default-project")

        result = resolve_project(None)

        assert result == "adc-default-project"
        mock_auth_default.assert_called_once()
        mock_console.print.assert_called_once_with(
            "[dim]Using project from ADC: adc-default-project[/dim]"
        )

    @patch("google.auth.default")
    def test_error_when_no_project_available(self, mock_auth_default):
        """Test that ConfigurationError is raised when no project is available."""
        mock_auth_default.return_value = (None, None)

        with pytest.raises(ConfigurationError) as exc_info:
            resolve_project(None)

        assert "No project specified" in str(exc_info.value)
        assert "gcloud auth application-default set-quota-project" in str(exc_info.value)

    @patch("google.auth.default")
    def test_error_when_adc_raises_exception(self, mock_auth_default):
        """Test that ConfigurationError is raised when ADC fails."""
        mock_auth_default.side_effect = Exception("ADC not configured")

        with pytest.raises(ConfigurationError) as exc_info:
            resolve_project(None)

        assert "No project specified" in str(exc_info.value)
