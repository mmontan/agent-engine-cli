import asyncio
import json
from collections.abc import MutableMapping
from typing import Annotated, Literal

import typer
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from agent_engine_cli import __version__
from agent_engine_cli.chat import run_chat
from agent_engine_cli.config import ConfigurationError, resolve_project
from agent_engine_cli.dependencies import get_client

console = Console()

app = typer.Typer(
    help="Agent Engine CLI - Manage your agents with ease.",
    no_args_is_help=True,
    add_completion=False,
)


@app.command()
def version():
    """Show the CLI version."""
    print(f"Agent Engine CLI v{__version__}")


@app.command("list")
def list_agents(
    location: Annotated[str, typer.Option("--location", "-l", help="Google Cloud region")],
    project: Annotated[str | None, typer.Option("--project", "-p", help="Google Cloud project ID (defaults to ADC project)")] = None,
    base_url: Annotated[str | None, typer.Option("--base-url", help="Override the Vertex AI base URL")] = None,
    api_version: Annotated[str | None, typer.Option("--api-version", help="Override the API version")] = None,
) -> None:
    """List all agents in the project."""
    try:
        project = resolve_project(project)
    except ConfigurationError as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        raise typer.Exit(code=1)

    try:
        client = get_client(project=project, location=location, base_url=base_url, api_version=api_version)
        agents = list(client.list_agents())

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
        console.print(f"[red]Error listing agents: {escape(str(e))}[/red]")
        raise typer.Exit(code=1)


@app.command("get")
def get_agent(
    agent_id: Annotated[str, typer.Argument(help="Agent ID or full resource name")],
    location: Annotated[str, typer.Option("--location", "-l", help="Google Cloud region")],
    project: Annotated[str | None, typer.Option("--project", "-p", help="Google Cloud project ID (defaults to ADC project)")] = None,
    full: Annotated[bool, typer.Option("--full", "-f", help="Show full JSON output")] = False,
    base_url: Annotated[str | None, typer.Option("--base-url", help="Override the Vertex AI base URL")] = None,
    api_version: Annotated[str | None, typer.Option("--api-version", help="Override the API version")] = None,
) -> None:
    """Get details for a specific agent."""
    try:
        project = resolve_project(project)
    except ConfigurationError as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        raise typer.Exit(code=1)

    try:
        client = get_client(project=project, location=location, base_url=base_url, api_version=api_version)
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
            agent_framework = "N/A"
            class_methods = "N/A"
            agent_card = "N/A"

            # Try to read from api_resource.spec first
            spec = None
            api_resource = getattr(agent, "api_resource", None)
            if api_resource and hasattr(api_resource, "spec") and api_resource.spec:
                spec = api_resource.spec
            elif hasattr(agent, "spec") and agent.spec:
                spec = agent.spec

            if spec:
                effective_identity = getattr(spec, "effective_identity", "N/A")
                agent_framework = getattr(spec, "agent_framework", "N/A")

                raw_methods = getattr(spec, "class_methods", []) or []
                method_names = []
                for m in raw_methods:
                    try:
                        m_name = (getattr(m, "name", None) or 
                                  getattr(m, "method", None) or 
                                  (m.get("name") if hasattr(m, "get") else None) or
                                  (m.get("method") if hasattr(m, "get") else None))
                        if not m_name:
                            continue

                        # Extract parameters and their types
                        m_params = (getattr(m, "parameters", None) or 
                                   (m.get("parameters") if hasattr(m, "get") else None))
                        
                        if m_params and isinstance(m_params, dict):
                            properties = m_params.get("properties", {})
                            required = m_params.get("required", [])
                            p_list = []
                            for p, p_info in properties.items():
                                p_type = ""
                                if isinstance(p_info, dict):
                                    p_type = p_info.get("type", "")
                                    if not p_type and "anyOf" in p_info:
                                        types = [t.get("type", "any") for t in p_info["anyOf"] if isinstance(t, dict)]
                                        p_type = "|".join(types)
                                
                                p_str = f"{p}: {p_type}" if p_type else p
                                if p in required:
                                    p_list.append(f"{p_str}*")
                                else:
                                    p_list.append(p_str)
                            method_names.append(f"{m_name}({', '.join(p_list)})")
                        else:
                            method_names.append(str(m_name))

                        # Extract and add description
                        m_desc = (getattr(m, "description", None) or 
                                  (m.get("description") if hasattr(m, "get") else None))
                        if m_desc:
                            # Clean up description and take only the first line/paragraph
                            m_desc_clean = m_desc.strip().split("\n")[0]
                            method_names.append(f"    {m_desc_clean}")

                        if agent_card == "N/A":
                            m_metadata = getattr(m, "metadata", None) or (m.get("metadata") if hasattr(m, "get") else None)
                            if m_metadata:
                                card = (getattr(m_metadata, "get", lambda k, d: None)("a2a_agent_card", None) or
                                        getattr(m_metadata, "get", lambda k, d: None)("agent_card", None))
                                if card:
                                    agent_card = card
                    except Exception:
                        pass

                if method_names:
                    class_methods = "\n  " + "\n  ".join(method_names)

            content = (
                f"[bold]Name:[/bold] {escape(name)}\n"
                f"[bold]Display Name:[/bold] {escape(display_name)}\n"
                f"[bold]Description:[/bold] {escape(description)}\n"
                f"[bold]Created:[/bold] {create_time}\n"
                f"[bold]Updated:[/bold] {update_time}\n"
                f"[bold]Effective Identity:[/bold] {escape(effective_identity)}\n"
                f"[bold]Agent Framework:[/bold] {escape(str(agent_framework))}\n"
                f"[bold]Class Methods:[/bold] {escape(class_methods)}\n"
                f"[bold]Agent Card:[/bold] {escape(str(agent_card))}"
            )
            console.print(Panel(content, title="Agent Details"))
    except Exception as e:
        console.print(f"[red]Error getting agent: {escape(str(e))}[/red]")
        raise typer.Exit(code=1)


@app.command("create")
def create_agent(
    display_name: Annotated[str, typer.Argument(help="Display name for the agent")],
    location: Annotated[str, typer.Option("--location", "-l", help="Google Cloud region")],
    project: Annotated[str | None, typer.Option("--project", "-p", help="Google Cloud project ID (defaults to ADC project)")] = None,
    identity: Annotated[
        Literal["agent_identity", "service_account"],
        typer.Option("--identity", "-i", help="Identity type for the agent"),
    ] = "agent_identity",
    service_account: Annotated[
        str | None,
        typer.Option("--service-account", "-s", help="Service account email (only used with --identity service_account)"),
    ] = None,
    base_url: Annotated[str | None, typer.Option("--base-url", help="Override the Vertex AI base URL")] = None,
    api_version: Annotated[str | None, typer.Option("--api-version", help="Override the API version")] = None,
) -> None:
    """Create a new agent (without deploying code)."""
    try:
        project = resolve_project(project)
    except ConfigurationError as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        raise typer.Exit(code=1)

    try:
        client = get_client(project=project, location=location, base_url=base_url, api_version=api_version)
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
        console.print(f"[red]Error creating agent: {escape(str(e))}[/red]")
        raise typer.Exit(code=1)


@app.command("delete")
def delete_agent(
    agent_id: Annotated[str, typer.Argument(help="Agent ID or full resource name")],
    location: Annotated[str, typer.Option("--location", "-l", help="Google Cloud region")],
    project: Annotated[str | None, typer.Option("--project", "-p", help="Google Cloud project ID (defaults to ADC project)")] = None,
    force: Annotated[bool, typer.Option("--force", "-f", help="Force deletion of agents with sessions/memory")] = False,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False,
    base_url: Annotated[str | None, typer.Option("--base-url", help="Override the Vertex AI base URL")] = None,
    api_version: Annotated[str | None, typer.Option("--api-version", help="Override the API version")] = None,
) -> None:
    """Delete an agent."""
    try:
        project = resolve_project(project)
    except ConfigurationError as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        raise typer.Exit(code=1)

    if not yes:
        confirm = typer.confirm(f"Are you sure you want to delete agent '{agent_id}'?")
        if not confirm:
            console.print("Aborted.")
            raise typer.Exit()

    try:
        client = get_client(project=project, location=location, base_url=base_url, api_version=api_version)
        client.delete_agent(agent_id, force=force)
        console.print(f"[red]Agent '{escape(agent_id)}' deleted.[/red]")
    except Exception as e:
        console.print(f"[red]Error deleting agent: {escape(str(e))}[/red]")
        raise typer.Exit(code=1)


# Create sessions subcommand group
sessions_app = typer.Typer(help="Manage agent sessions.")
app.add_typer(sessions_app, name="sessions")


@sessions_app.command("list")
def list_sessions(
    agent_id: Annotated[str, typer.Argument(help="Agent ID or full resource name")],
    location: Annotated[str, typer.Option("--location", "-l", help="Google Cloud region")],
    project: Annotated[str | None, typer.Option("--project", "-p", help="Google Cloud project ID (defaults to ADC project)")] = None,
    base_url: Annotated[str | None, typer.Option("--base-url", help="Override the Vertex AI base URL")] = None,
    api_version: Annotated[str | None, typer.Option("--api-version", help="Override the API version")] = None,
) -> None:
    """List all sessions for an agent."""
    try:
        project = resolve_project(project)
    except ConfigurationError as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        raise typer.Exit(code=1)

    try:
        client = get_client(project=project, location=location, base_url=base_url, api_version=api_version)
        sessions = list(client.list_sessions(agent_id))

        if not sessions:
            console.print("No sessions found.")
            return

        table = Table(title="Sessions")
        table.add_column("Session ID", style="cyan")
        table.add_column("Display Name", style="green")
        table.add_column("User ID")
        table.add_column("Created")
        table.add_column("Expires")

        for session in sessions:
            # Extract session ID from full resource name
            session_name = getattr(session, "name", "") or ""
            session_id = session_name.split("/")[-1] if session_name else ""

            display_name = getattr(session, "display_name", "") or ""
            user_id = getattr(session, "user_id", "") or ""

            # Format timestamps compactly (YYYY-MM-DD HH:MM)
            create_time_raw = getattr(session, "create_time", None)
            if create_time_raw:
                create_time = create_time_raw.strftime("%Y-%m-%d %H:%M")
            else:
                create_time = ""

            expire_time_raw = getattr(session, "expire_time", None)
            if expire_time_raw:
                expire_time = expire_time_raw.strftime("%Y-%m-%d %H:%M")
            else:
                expire_time = ""

            table.add_row(
                escape(session_id),
                escape(display_name),
                escape(user_id),
                create_time,
                expire_time,
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing sessions: {escape(str(e))}[/red]")
        raise typer.Exit(code=1)


# Create sandboxes subcommand group
sandboxes_app = typer.Typer(help="Manage agent sandboxes.")
app.add_typer(sandboxes_app, name="sandboxes")


@sandboxes_app.command("list")
def list_sandboxes(
    agent_id: Annotated[str, typer.Argument(help="Agent ID or full resource name")],
    location: Annotated[str, typer.Option("--location", "-l", help="Google Cloud region")],
    project: Annotated[str | None, typer.Option("--project", "-p", help="Google Cloud project ID (defaults to ADC project)")] = None,
    base_url: Annotated[str | None, typer.Option("--base-url", help="Override the Vertex AI base URL")] = None,
    api_version: Annotated[str | None, typer.Option("--api-version", help="Override the API version")] = None,
) -> None:
    """List all sandboxes for an agent."""
    try:
        project = resolve_project(project)
    except ConfigurationError as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        raise typer.Exit(code=1)

    try:
        client = get_client(project=project, location=location, base_url=base_url, api_version=api_version)
        sandboxes = list(client.list_sandboxes(agent_id))

        if not sandboxes:
            console.print("No sandboxes found.")
            return

        table = Table(title="Sandboxes")
        table.add_column("Sandbox ID", style="cyan")
        table.add_column("Display Name", style="green")
        table.add_column("State")
        table.add_column("Created")
        table.add_column("Expires")

        for sandbox in sandboxes:
            # Extract sandbox ID from full resource name
            sandbox_name = getattr(sandbox, "name", "") or ""
            sandbox_id = sandbox_name.split("/")[-1] if sandbox_name else ""

            display_name = getattr(sandbox, "display_name", "") or ""

            # Format state (remove STATE_ prefix if present)
            state_raw = getattr(sandbox, "state", None)
            if state_raw:
                state = str(state_raw.value).replace("STATE_", "") if hasattr(state_raw, "value") else str(state_raw)
            else:
                state = ""

            # Format timestamps compactly (YYYY-MM-DD HH:MM)
            create_time_raw = getattr(sandbox, "create_time", None)
            if create_time_raw:
                create_time = create_time_raw.strftime("%Y-%m-%d %H:%M")
            else:
                create_time = ""

            expire_time_raw = getattr(sandbox, "expire_time", None)
            if expire_time_raw:
                expire_time = expire_time_raw.strftime("%Y-%m-%d %H:%M")
            else:
                expire_time = ""

            table.add_row(
                escape(sandbox_id),
                escape(display_name),
                state,
                create_time,
                expire_time,
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing sandboxes: {escape(str(e))}[/red]")
        raise typer.Exit(code=1)


# Create memories subcommand group
memories_app = typer.Typer(help="Manage agent memories.")
app.add_typer(memories_app, name="memories")


@memories_app.command("list")
def list_memories(
    agent_id: Annotated[str, typer.Argument(help="Agent ID or full resource name")],
    location: Annotated[str, typer.Option("--location", "-l", help="Google Cloud region")],
    project: Annotated[str | None, typer.Option("--project", "-p", help="Google Cloud project ID (defaults to ADC project)")] = None,
    base_url: Annotated[str | None, typer.Option("--base-url", help="Override the Vertex AI base URL")] = None,
    api_version: Annotated[str | None, typer.Option("--api-version", help="Override the API version")] = None,
) -> None:
    """List all memories for an agent."""
    try:
        project = resolve_project(project)
    except ConfigurationError as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        raise typer.Exit(code=1)

    try:
        client = get_client(project=project, location=location, base_url=base_url, api_version=api_version)
        memories = list(client.list_memories(agent_id))

        table = Table(title="Memories")
        table.add_column("Memory ID", style="cyan")
        table.add_column("Display Name", style="green")
        table.add_column("Scope")
        table.add_column("Fact", max_width=40, overflow="ellipsis")
        table.add_column("Created")
        table.add_column("Expires")

        has_items = False
        for memory in memories:
            has_items = True
            # Extract memory ID from full resource name
            memory_name = getattr(memory, "name", "") or ""
            memory_id = memory_name.split("/")[-1] if memory_name else ""

            display_name = getattr(memory, "display_name", "") or ""
            fact = getattr(memory, "fact", "") or ""

            # Format scope dict as key=value pairs
            scope_raw = getattr(memory, "scope", None)
            if scope_raw and isinstance(scope_raw, (dict, MutableMapping)):
                scope = ", ".join(f"{k}={v}" for k, v in scope_raw.items())
            else:
                scope = ""

            # Format timestamps compactly (YYYY-MM-DD HH:MM)
            create_time_raw = getattr(memory, "create_time", None)
            if create_time_raw:
                create_time = create_time_raw.strftime("%Y-%m-%d %H:%M")
            else:
                create_time = ""

            expire_time_raw = getattr(memory, "expire_time", None)
            if expire_time_raw:
                expire_time = expire_time_raw.strftime("%Y-%m-%d %H:%M")
            else:
                expire_time = ""

            table.add_row(
                escape(memory_id),
                escape(display_name),
                escape(scope),
                escape(fact),
                create_time,
                expire_time,
            )

        if not has_items:
            console.print("No memories found.")
            return

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing memories: {escape(str(e))}[/red]")
        raise typer.Exit(code=1)


@app.command("chat")
def chat(
    agent_id: Annotated[str, typer.Argument(help="Agent ID or full resource name")],
    location: Annotated[str, typer.Option("--location", "-l", help="Google Cloud region")],
    project: Annotated[str | None, typer.Option("--project", "-p", help="Google Cloud project ID (defaults to ADC project)")] = None,
    user: Annotated[str, typer.Option("--user", "-u", help="User ID for the chat session")] = "cli-user",
    debug: Annotated[bool, typer.Option("--debug", "-d", help="Enable verbose HTTP debug logging")] = False,
    base_url: Annotated[str | None, typer.Option("--base-url", help="Override the Vertex AI base URL")] = None,
    api_version: Annotated[str | None, typer.Option("--api-version", help="Override the API version")] = None,
) -> None:
    """Start an interactive chat session with an agent."""
    try:
        project = resolve_project(project)
    except ConfigurationError as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        raise typer.Exit(code=1)

    try:
        asyncio.run(run_chat(
            project=project,
            location=location,
            agent_id=agent_id,
            user_id=user,
            debug=debug,
            base_url=base_url,
            api_version=api_version,
        ))
    except KeyboardInterrupt:
        console.print("\n[yellow]Chat session ended.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error in chat session: {escape(str(e))}[/red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()