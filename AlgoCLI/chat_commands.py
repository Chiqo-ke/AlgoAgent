"""
Command Handler for AlgoCLI Chat Interface
Parses and executes commands from the user input
"""

import asyncio
from typing import Dict, Any
from rich.markdown import Markdown
from rich.table import Table
from rich.syntax import Syntax

from api_client import APIClient

HELP_TEXT = Markdown("""
# 🤖 AlgoAgent Command Help

Here are the available commands. Commands are case-insensitive.

| Command               | Alias      | Description                                             |
|-----------------------|------------|---------------------------------------------------------|
| `\\help`                | `\\h`        | Shows this help message.                                |
| `\\examples`            | `\\ex`       | Shows usage examples for creating workflows.            |
| `\\create <request>`    | `\\c`        | Creates a new workflow from a description.              |
| `\\status <id>`         | `\\s`        | Gets the status of a specific workflow.                 |
| `\\list [status]`       | `\\ls`       | Lists workflows. Optionally filter by status.           |
| `\\stop <id>`           |            | Stops a running workflow.                               |
| `\\logs <id>`           | `\\l`        | Retrieves logs for a specific workflow.                 |
| `\\details <id>`        | `\\d`        | Shows detailed information about a workflow.            |
| `\\health`              |            | Checks the health of the backend API service.           |
| `\\clear`               |            | Clears the chat screen.                                 |

**Example:**
`\\create Create a simple RSI strategy for BTC/USDT`
""")

EXAMPLES_TEXT = Markdown("""
# 💡 Workflow Creation Examples

You can create workflows by using the `\\create` command or by just typing a description of what you want.

## Using the `\\create` command:
- `\\create a simple moving average crossover strategy for ETH/USD`
- `\\c build a mean-reversion strategy using Bollinger Bands on the 1-hour timeframe`
- `\\create an arbitrage bot for triangular pairs: BTC, ETH, USDT`

## Using Natural Language:
- `I want a strategy that buys when RSI is below 30 and sells when it's above 70.`
- `Make a grid trading bot for a volatile asset.`
- `Design a multi-timeframe analysis workflow using MACD and Stochastic oscillators.`

The more detailed your description, the better the agent can build the workflow.
""")


class CommandHandler:
    """Handles parsing and execution of chat commands"""

    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.commands = {
            "\\help": self.show_help,
            "\\h": self.show_help,
            "\\examples": self.show_examples,
            "\\ex": self.show_examples,
            "\\create": self.create_workflow,
            "\\c": self.create_workflow,
            "\\status": self.get_status,
            "\\s": self.get_status,
            "\\list": self.list_workflows,
            "\\ls": self.list_workflows,
            "\\stop": self.stop_workflow,
            "\\logs": self.get_logs,
            "\\l": self.get_logs,
            "\\details": self.get_details,
            "\\d": self.get_details,
            "\\health": self.check_health,
        }

    async def handle_command(self, user_input: str) -> Dict[str, Any]:
        """
        Parse and execute a command.
        Returns a dictionary with 'role' and 'content'.
        """
        parts = user_input.strip().split(" ")
        command = parts[0].lower()
        args = parts[1:]

        if command in self.commands:
            try:
                return await self.commands[command](args)
            except Exception as e:
                return {"role": "error", "content": f"Failed to execute '{command}': {e}"}
        
        return {"role": "error", "content": f"Unknown command: `{command}`. Type `\\help` for a list of commands."}

    async def create_workflow_nl(self, request: str) -> Dict[str, Any]:
        """Handle natural language request for workflow creation"""
        return await self.create_workflow([request])

    async def show_help(self, args: list) -> Dict[str, Any]:
        """Return the help text"""
        return {"role": "assistant", "content": HELP_TEXT}

    async def show_examples(self, args: list) -> Dict[str, Any]:
        """Return the examples text"""
        return {"role": "assistant", "content": EXAMPLES_TEXT}

    async def create_workflow(self, args: list) -> Dict[str, Any]:
        """Create a new workflow"""
        if not args:
            return {"role": "error", "content": "Usage: `\\create <description>`"}
        
        request = " ".join(args)
        async with self.api_client as client:
            result = await client.create_workflow(request)
        
        if "workflow_id" in result:
            wf_id = result["workflow_id"]
            return {
                "role": "assistant",
                "content": f"✅ Workflow `{wf_id}` created successfully! Monitor its progress with `\\status {wf_id[:8]}`."
            }
        return {"role": "error", "content": f"Failed to create workflow: {result.get('detail', 'Unknown error')}"}

    async def get_status(self, args: list) -> Dict[str, Any]:
        """Get workflow status"""
        if not args:
            return {"role": "error", "content": "Usage: `\\status <workflow_id>`"}
        
        wf_id = args[0]
        async with self.api_client as client:
            status = await client.get_workflow_status(wf_id)
        
        if not status:
            return {"role": "error", "content": f"Could not find workflow `{wf_id}`."}

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column()
        table.add_column()
        
        table.add_row("[bold cyan]ID[/]", status.get('workflow_id', 'N/A'))
        table.add_row("[bold cyan]Status[/]", f"[bold green]{status.get('status', 'N/A').upper()}[/]")
        table.add_row("[bold cyan]Progress[/]", f"{status.get('progress', 0.0) * 100:.1f}%")
        table.add_row("[bold cyan]Tasks[/]", f"{status.get('completed_tasks', 0)}/{status.get('task_count', 0)}")
        
        return {"role": "assistant", "content": table}

    async def list_workflows(self, args: list) -> Dict[str, Any]:
        """List all workflows"""
        status_filter = args[0] if args else None
        async with self.api_client as client:
            workflows = await client.list_workflows(status=status_filter)

        if not workflows:
            return {"role": "assistant", "content": "No workflows found."}

        table = Table(title="Workflows", header_style="bold magenta", border_style="cyan")
        table.add_column("ID", style="dim")
        table.add_column("Status")
        table.add_column("Progress")
        table.add_column("Created At")

        for wf in workflows[:15]:  # Limit to 15 for display
            progress = f"{wf.get('progress', 0.0) * 100:.1f}%"
            table.add_row(
                wf.get('workflow_id', 'N/A')[:8],
                f"[green]{wf.get('status', 'N/A').upper()}[/]",
                progress,
                wf.get('created_at', 'N/A').split('T')[0]
            )
        
        return {"role": "assistant", "content": table}

    async def stop_workflow(self, args: list) -> Dict[str, Any]:
        """Stop a workflow"""
        if not args:
            return {"role": "error", "content": "Usage: `\\stop <workflow_id>`"}
        
        wf_id = args[0]
        async with self.api_client as client:
            result = await client.stop_workflow(wf_id)
        
        if result.get("status") == "stopped":
            return {"role": "assistant", "content": f"🛑 Workflow `{wf_id}` stopped."}
        return {"role": "error", "content": f"Could not stop workflow `{wf_id}`. Reason: {result.get('detail', 'Unknown')}"}

    async def get_logs(self, args: list) -> Dict[str, Any]:
        """Get workflow logs"""
        if not args:
            return {"role": "error", "content": "Usage: `\\logs <workflow_id>`"}
        
        wf_id = args[0]
        async with self.api_client as client:
            logs = await client.get_workflow_logs(wf_id)

        if not logs or not logs.get("logs"):
            return {"role": "assistant", "content": f"No logs found for workflow `{wf_id}`."}

        log_content = "\n".join(logs["logs"][-50:]) # Show last 50 lines
        syntax = Syntax(log_content, "log", theme="monokai", line_numbers=True)
        return {"role": "assistant", "content": syntax}

    async def get_details(self, args: list) -> Dict[str, Any]:
        """Get detailed workflow information"""
        if not args:
            return {"role": "error", "content": "Usage: `\\details <workflow_id>`"}
        
        wf_id = args[0]
        async with self.api_client as client:
            details = await client.get_workflow_details(wf_id)

        if not details:
            return {"role": "error", "content": f"Could not find workflow `{wf_id}`."}

        # This can be expanded to a more detailed view
        return {"role": "assistant", "content": f"Details for `{wf_id}`:\n{details}"}

    async def check_health(self, args: list) -> Dict[str, Any]:
        """Check API health"""
        async with self.api_client as client:
            health = await client.health_check()
        
        status = health.get("status", "unhealthy")
        if status == "healthy":
            return {"role": "assistant", "content": f"✅ API is healthy!"}
        return {"role": "error", "content": f"API is unhealthy: {health.get('error', 'No details')}"}
