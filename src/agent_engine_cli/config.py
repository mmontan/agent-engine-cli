"""Configuration utilities for Agent Engine CLI."""

from rich.console import Console

console = Console()


class ConfigurationError(Exception):
    """Raised when configuration is missing or invalid."""


def resolve_project(project: str | None) -> str:
    """Resolve the project ID from the provided value or ADC.

    Args:
        project: Explicit project ID or None to use ADC default.

    Returns:
        The resolved project ID.

    Raises:
        ConfigurationError: If no project is provided and ADC has no default project.
    """
    if project is not None:
        return project

    # Try to get project from Application Default Credentials
    try:
        import google.auth

        _, adc_project = google.auth.default()
        if adc_project:
            console.print(f"[dim]Using project from ADC: {adc_project}[/dim]")
            return adc_project
    except Exception:
        pass

    raise ConfigurationError(
        "No project specified and no default project found in Application Default Credentials. "
        "Either provide --project or run 'gcloud auth application-default set-quota-project PROJECT_ID'"
    )
