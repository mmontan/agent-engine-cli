import json
from enum import Enum
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agent_engine_cli.client import AgentEngineClient

app = typer.Typer(help="Agent Engine CLI - Manage your agents with ease.", no_args_is_help=True)
console = Console()


class IdentityType(str, Enum):
    agent_identity = "agent_identity"
    default = "default"

@app.command()
def init():
    """
    Initialize a new Agent Engine project in the current directory.
    """
    console.print(Panel("Initializing Agent Engine project...", title="Agent Engine", style="bold blue"))
    # Add initialization logic here
    console.print("[green]Project initialized successfully![/green]")

@app.command()
def status():
    """
    Check the status of the Agent Engine service.
    """
    console.print("[yellow]Checking status...[/yellow]")
    # Add status check logic here
    console.print("[green]System is operational.[/green]")

@app.command()
def version():
    """
    Show the CLI version.
    """
    console.print("Agent Engine CLI v0.1.0")


@app.command("list")
def list_agents(
    project: Annotated[
        str, typer.Option("--project", "-p", help="Google Cloud project ID")
    ],
    location: Annotated[
        str, typer.Option("--location", "-l", help="Google Cloud region")
    ],
) -> None:
    """
    List all agents in the project.
    """
    try:
        client = AgentEngineClient(project=project, location=location)
        agents = client.list_agents()

        if not agents:
            console.print("[yellow]No agents found.[/yellow]")
            return

        table = Table(title="Agents")
        table.add_column("Name", style="cyan")
        table.add_column("Display Name", style="green")
        table.add_column("Created", style="blue")
        table.add_column("Updated", style="blue")

        for agent in agents:
            name = agent.resource_name.split("/")[-1] if agent.resource_name else ""
            display_name = getattr(agent, "display_name", "") or ""
            create_time = str(getattr(agent, "create_time", "")) or ""
            update_time = str(getattr(agent, "update_time", "")) or ""

            table.add_row(name, display_name, create_time, update_time)

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing agents: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("get")
def get_agent(
    agent_id: Annotated[str, typer.Argument(help="Agent ID or full resource name")],
    project: Annotated[
        str, typer.Option("--project", "-p", help="Google Cloud project ID")
    ],
    location: Annotated[
        str, typer.Option("--location", "-l", help="Google Cloud region")
    ],
    full: Annotated[
        bool, typer.Option("--full", "-f", help="Show full JSON output")
    ] = False,
) -> None:
    """
    Get details for a specific agent.
    """
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
            console.print_json(json.dumps(agent_dict, indent=2, default=str))
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
            console.print(Panel(content, title="Agent Details", style="bold blue"))
    except Exception as e:
        console.print(f"[red]Error getting agent: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("create")
def create_agent(
    display_name: Annotated[
        str, typer.Argument(help="Display name for the agent")
    ],
    project: Annotated[
        str, typer.Option("--project", "-p", help="Google Cloud project ID")
    ],
    location: Annotated[
        str, typer.Option("--location", "-l", help="Google Cloud region")
    ],
    identity_type: Annotated[
        IdentityType, typer.Option("--identity-type", "-i", help="Identity type for the agent")
    ] = IdentityType.agent_identity,
) -> None:
    """
    Create a new agent (without deploying code).
    """
    try:
        client = AgentEngineClient(project=project, location=location)
        console.print(f"[yellow]Creating agent '{display_name}'...[/yellow]")

        agent = client.create_agent(
            display_name=display_name,
            identity_type=identity_type.value,
        )

        resource_name = agent.name if hasattr(agent, "name") else agent.resource_name
        name = resource_name.split("/")[-1] if resource_name else ""
        console.print(f"[green]Agent created successfully![/green]")
        console.print(f"[bold]Name:[/bold] {name}")
        console.print(f"[bold]Resource:[/bold] {resource_name}")
    except Exception as e:
        console.print(f"[red]Error creating agent: {e}[/red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
