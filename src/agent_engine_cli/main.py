import json
from typing import Annotated, Literal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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
    print("Agent Engine CLI v0.1.0")


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

            table.add_row(name, display_name, create_time, update_time)

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

        if full:
            agent_dict = {
                "resource_name": agent.resource_name,
                "display_name": getattr(agent, "display_name", None),
                "description": getattr(agent, "description", None),
                "create_time": str(getattr(agent, "create_time", None)),
                "update_time": str(getattr(agent, "update_time", None)),
            }
            if hasattr(agent, "spec") and agent.spec:
                agent_dict["spec"] = str(agent.spec)
            console.print(json.dumps(agent_dict, indent=2, default=str))
        else:
            name = agent.resource_name.split("/")[-1] if agent.resource_name else ""
            display_name = getattr(agent, "display_name", "") or "N/A"
            description = getattr(agent, "description", "") or "N/A"
            create_time = str(getattr(agent, "create_time", "")) or "N/A"
            update_time = str(getattr(agent, "update_time", "")) or "N/A"

            content = (
                f"[bold]Name:[/bold] {name}\n"
                f"[bold]Display Name:[/bold] {display_name}\n"
                f"[bold]Description:[/bold] {description}\n"
                f"[bold]Created:[/bold] {create_time}\n"
                f"[bold]Updated:[/bold] {update_time}"
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
        console.print(f"Creating agent '{display_name}'...")

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
        console.print(f"[red]Agent '{agent_id}' deleted.[/red]")
    except Exception as e:
        console.print(f"[red]Error deleting agent: {e}[/red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
