"""
AlgoCLI - Chat-Based Multi-Agent Workflow Manager
A conversational interface for managing AI-driven trading strategy workflows
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.binding import Binding
from textual.reactive import reactive
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.syntax import Syntax
from datetime import datetime
import asyncio
import re

from api_client import APIClient
from chat_commands import CommandHandler, HELP_TEXT
from theme import LUMINOUS_CHAT_CSS


class ChatMessage(Static):
    """A single chat message widget"""
    
    def __init__(self, role: str, content: str, timestamp: str = None):
        super().__init__()
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now().strftime("%H:%M:%S")
    
    def render(self) -> Panel:
        """Render the message as a Rich panel"""
        if self.role == "user":
            style = "bold cyan"
            title = f"[bold cyan]You[/] [dim]{self.timestamp}[/]"
            border_style = "cyan"
        elif self.role == "system":
            style = "bold yellow"
            title = f"[bold yellow]System[/] [dim]{self.timestamp}[/]"
            border_style = "yellow"
        elif self.role == "error":
            style = "bold red"
            title = f"[bold red]Error[/] [dim]{self.timestamp}[/]"
            border_style = "red"
        else:  # assistant
            style = "bold green"
            title = f"[bold green]AlgoAgent[/] [dim]{self.timestamp}[/]"
            border_style = "green"
        
        return Panel(
            self.content,
            title=title,
            title_align="left",
            border_style=border_style,
            padding=(0, 1)
        )


class ChatInterface(ScrollableContainer):
    """Scrollable chat message container"""
    
    can_focus = False
    
    def add_message(self, role: str, content: str):
        """Add a new message to the chat"""
        message = ChatMessage(role, content)
        self.mount(message)
        self.scroll_end(animate=False)


class AlgoChatApp(App):
    """Main chat-based application"""
    
    CSS = LUMINOUS_CHAT_CSS
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("ctrl+l", "clear_chat", "Clear Chat"),
        Binding("ctrl+h", "show_help", "Help"),
        Binding("f1", "show_help", "Help"),
    ]
    
    def __init__(self):
        super().__init__()
        self.api_client = APIClient()
        self.command_handler = CommandHandler(self.api_client)
        self.processing = False
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header(show_clock=True)
        
        with Container(id="app-container"):
            # Title banner
            yield Static(
                "[bold cyan]🤖 AlgoAgent Chat Interface[/]\n"
                "[dim]Type [cyan]\\help[/] for commands, [cyan]\\examples[/] for usage examples[/]",
                id="banner"
            )
            
            # Chat container
            yield ChatInterface(id="chat-container")
            
            # Input container
            with Horizontal(id="input-container"):
                yield Input(
                    placeholder="Type a command (\\help) or describe your workflow...",
                    id="chat-input"
                )
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app starts"""
        self.title = "AlgoCLI - Chat Interface"
        
        # Focus input
        self.query_one("#chat-input", Input).focus()
        
        # Welcome message
        chat = self.query_one("#chat-container", ChatInterface)
        chat.add_message(
            "assistant",
            "👋 Welcome to AlgoAgent Multi-Agent Workflow Manager!\n\n"
            "I can help you:\n"
            "• Create trading strategy workflows\n"
            "• Monitor workflow execution\n"
            "• Manage and control workflows\n"
            "• View workflow details and logs\n\n"
            "Type [cyan]\\help[/] to see all available commands or just describe what you want to create!"
        )
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission"""
        if self.processing:
            return
        
        user_input = event.value.strip()
        if not user_input:
            return
        
        # Clear input
        event.input.value = ""
        
        # Add user message
        chat = self.query_one("#chat-container", ChatInterface)
        chat.add_message("user", user_input)
        
        # Process command
        self.processing = True
        
        try:
            # Check if it's a command
            if user_input.startswith("\\"):
                response = await self.command_handler.handle_command(user_input)
            else:
                # Natural language workflow creation
                response = await self.command_handler.create_workflow_nl(user_input)
            
            # Add response
            chat.add_message(response["role"], response["content"])
            
        except Exception as e:
            chat.add_message("error", f"Error: {str(e)}")
        
        finally:
            self.processing = False
            self.query_one("#chat-input", Input).focus()
    
    def action_clear_chat(self) -> None:
        """Clear chat history"""
        chat = self.query_one("#chat-container", ChatInterface)
        chat.remove_children()
        chat.add_message(
            "system",
            "Chat cleared. Type [cyan]\\help[/] for commands."
        )
    
    def action_show_help(self) -> None:
        """Show help message"""
        chat = self.query_one("#chat-container", ChatInterface)
        chat.add_message("assistant", HELP_TEXT)


def run():
    """Run the chat application"""
    app = AlgoChatApp()
    app.run()


if __name__ == "__main__":
    run()
