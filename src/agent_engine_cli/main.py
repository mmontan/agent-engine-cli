import asyncio
import json
from typing import Annotated, Literal

import typer
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from agent_engine_cli import __version__
from agent_engine_cli.chat import run_chat
from agent_engine_cli.client import AgentEngineClient

console = Console()

app = typer.Typer(
    help="Agent Engine CLI - Manage your agents with ease.",
    no_args_is_help=True,
    add_completion=False,
)


@app.command(rich_help_panel="Utility")
def version():
    """Show the CLI version."""
    print(f"Agent Engine CLI v{__version__}")


@app.command("list")
def list_agents(
    project: Annotated[str, typer.Option("--project", "-p", help="Google Cloud project ID")],
    location: Annotated[str, typer.Option("--location", "-l", help="Google Cloud region")],
) -> None:
    """List all agents in the project."""
    try:
        client = AgentEngineClient(project=project, location=location)
        agents = client.list_agents()

        if not agents:
            console.print("No agents found.")
            return

        table = Table(title="Agents")
        table.add_column("Name", style="cyan")
        table.add_column("Display Name", style="green")
        table.add_column("Created")
        table.add_column("Updated")
        table.add_column("Identity", overflow="fold")

        for agent in agents:
            # v1beta1 api_resource uses 'name' instead of 'resource_name'
            agent_name = getattr(agent, "name", None) or getattr(agent, "resource_name", "")
            name = agent_name.split("/")[-1] if agent_name else ""
            display_name = getattr(agent, "display_name", "") or ""

            # Format timestamps compactly (YYYY-MM-DD HH:MM)
            create_time_raw = getattr(agent, "create_time", None)
            if create_time_raw:
                create_time = create_time_raw.strftime("%Y-%m-%d %H:%M")
            else:
                create_time = ""

            update_time_raw = getattr(agent, "update_time", None)
            if update_time_raw:
                update_time = update_time_raw.strftime("%Y-%m-%d %H:%M")
            else:
                update_time = ""

            effective_identity = "N/A"
            if hasattr(agent, "spec") and agent.spec:
                effective_identity = getattr(agent.spec, "effective_identity", "N/A")

            table.add_row(
                escape(name),
                escape(display_name),
                create_time,
                update_time,
                escape(effective_identity),
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing agents: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("get")
def get_agent(
    agent_id: Annotated[str, typer.Argument(help="Agent ID or full resource name")],
    project: Annotated[str, typer.Option("--project", "-p", help="Google Cloud project ID")],
    location: Annotated[str, typer.Option("--location", "-l", help="Google Cloud region")],
    full: Annotated[bool, typer.Option("--full", "-f", help="Show full JSON output")] = False,
) -> None:
    """Get details for a specific agent."""
    try:
        client = AgentEngineClient(project=project, location=location)
        agent = client.get_agent(agent_id)

        # v1beta1 api_resource uses 'name' instead of 'resource_name'
        agent_resource_name = getattr(agent, "name", None) or getattr(agent, "resource_name", "")

        if full:
            agent_dict = {
                "resource_name": agent_resource_name,
                "display_name": getattr(agent, "display_name", None),
                "description": getattr(agent, "description", None),
                "create_time": str(getattr(agent, "create_time", None)),
                "update_time": str(getattr(agent, "update_time", None)),
            }
            api_resource = getattr(agent, "api_resource", None)
            if api_resource and hasattr(api_resource, "spec") and api_resource.spec:
                agent_dict["spec"] = str(api_resource.spec)
            elif hasattr(agent, "spec") and agent.spec:
                agent_dict["spec"] = str(agent.spec)
            console.print(json.dumps(agent_dict, indent=2, default=str))
        else:
            name = agent_resource_name.split("/")[-1] if agent_resource_name else ""
            display_name = getattr(agent, "display_name", "") or "N/A"
            description = getattr(agent, "description", "") or "N/A"
            create_time = str(getattr(agent, "create_time", "")) or "N/A"
            update_time = str(getattr(agent, "update_time", "")) or "N/A"

            effective_identity = "N/A"
            # Try to read from api_resource.spec.effective_identity first
            api_resource = getattr(agent, "api_resource", None)
            if api_resource and hasattr(api_resource, "spec") and api_resource.spec:
                effective_identity = getattr(api_resource.spec, "effective_identity", "N/A")
            elif hasattr(agent, "spec") and agent.spec and hasattr(agent.spec, "effective_identity"):
                effective_identity = agent.spec.effective_identity

            content = (
                f"[bold]Name:[/bold] {escape(name)}\n"
                f"[bold]Display Name:[/bold] {escape(display_name)}\n"
                f"[bold]Description:[/bold] {escape(description)}\n"
                f"[bold]Created:[/bold] {create_time}\n"
                f"[bold]Updated:[/bold] {update_time}\n"
                f"[bold]Effective Identity:[/bold] {escape(effective_identity)}"
            )
            console.print(Panel(content, title="Agent Details"))
    except Exception as e:
        console.print(f"[red]Error getting agent: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("create")
def create_agent(
    display_name: Annotated[str, typer.Argument(help="Display name for the agent")],
    project: Annotated[str, typer.Option("--project", "-p", help="Google Cloud project ID")],
    location: Annotated[str, typer.Option("--location", "-l", help="Google Cloud region")],
    identity: Annotated[
        Literal["agent_identity", "service_account"],
        typer.Option("--identity", "-i", help="Identity type for the agent"),
    ] = "agent_identity",
    service_account: Annotated[
        str | None,
        typer.Option("--service-account", "-s", help="Service account email (only used with --identity service_account)"),
    ] = None,
) -> None:
    """Create a new agent (without deploying code)."""
    try:
        client = AgentEngineClient(project=project, location=location)
        console.print(f"Creating agent '{escape(display_name)}'...")

        agent = client.create_agent(
            display_name=display_name,
            identity_type=identity,
            service_account=service_account,
        )

        resource_name = agent.name if hasattr(agent, "name") else agent.resource_name
        name = resource_name.split("/")[-1] if resource_name else ""
        console.print("[green]Agent created successfully![/green]")
        console.print(f"Name: {name}")
        console.print(f"Resource: {resource_name}")
    except Exception as e:
        console.print(f"[red]Error creating agent: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("delete")
def delete_agent(
    agent_id: Annotated[str, typer.Argument(help="Agent ID or full resource name")],
    project: Annotated[str, typer.Option("--project", "-p", help="Google Cloud project ID")],
    location: Annotated[str, typer.Option("--location", "-l", help="Google Cloud region")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Force deletion of agents with sessions/memory")] = False,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False,
) -> None:
    """Delete an agent."""
    if not yes:
        confirm = typer.confirm(f"Are you sure you want to delete agent '{agent_id}'?")
        if not confirm:
            console.print("Aborted.")
            raise typer.Exit()

    try:
        client = AgentEngineClient(project=project, location=location)
        client.delete_agent(agent_id, force=force)
        console.print(f"[red]Agent '{escape(agent_id)}' deleted.[/red]")
    except Exception as e:
        console.print(f"[red]Error deleting agent: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("chat", rich_help_panel="Interactive")
def chat(
    agent_id: Annotated[str, typer.Argument(help="Agent ID or full resource name")],
    project: Annotated[str, typer.Option("--project", "-p", help="Google Cloud project ID")],
    location: Annotated[str, typer.Option("--location", "-l", help="Google Cloud region")],
    user: Annotated[str, typer.Option("--user", "-u", help="User ID for the chat session")] = "cli-user",
    debug: Annotated[bool, typer.Option("--debug", "-d", help="Enable verbose HTTP debug logging")] = False,
) -> None:
    """Start an interactive chat session with an agent."""
    try:
        asyncio.run(run_chat(
            project=project,
            location=location,
            agent_id=agent_id,
            user_id=user,
            debug=debug,
        ))
    except KeyboardInterrupt:
        console.print("\n[yellow]Chat session ended.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error in chat session: {e}[/red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()