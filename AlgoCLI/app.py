"""
AlgoCLI - Multi-Agent Workflow CLI
A stunning Textual-based interface for managing AI-driven trading strategy workflows
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import (
    Header, Footer, Button, Input, Static, Label, 
    DataTable, TabbedContent, TabPane, RichLog
)
from textual.binding import Binding
from textual.screen import Screen, ModalScreen
from textual.reactive import reactive
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from typing import Optional, List, Dict, Any
import asyncio

from api_client import APIClient
from widgets import (
    WorkflowCard, TaskListWidget, StatusIndicator,
    ProgressBarWidget, LogViewer, MetricsPanel, WorkflowDetailView
)
from theme import LUMINOUS_CSS, LUMINOUS_THEME, get_status_color


class CreateWorkflowModal(ModalScreen[Optional[str]]):
    """Modal dialog for creating a new workflow"""
    
    DEFAULT_CSS = """
    CreateWorkflowModal {
        align: center middle;
    }
    
    #modal-container {
        width: 80;
        height: 25;
        background: $surface;
        border: tall $primary;
        padding: 1 2;
    }
    
    #modal-title {
        text-align: center;
        color: $primary;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #request-input {
        margin: 1 0;
    }
    
    #button-container {
        align: center middle;
        margin-top: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Compose the modal dialog"""
        with Container(id="modal-container"):
            yield Static("✨ Create New Workflow ✨", id="modal-title")
            yield Label("Enter your strategy request:")
            yield Input(
                placeholder="e.g., Create RSI strategy with 30/70 levels",
                id="request-input"
            )
            yield Label("\nOptions:")
            with Horizontal(id="button-container"):
                yield Button("Create", variant="primary", id="create-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press"""
        if event.button.id == "create-btn":
            input_widget = self.query_one("#request-input", Input)
            request_text = input_widget.value.strip()
            if request_text:
                self.dismiss(request_text)
        else:
            self.dismiss(None)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input"""
        request_text = event.value.strip()
        if request_text:
            self.dismiss(request_text)


class WorkflowListScreen(Screen):
    """Main screen showing workflow list"""
    
    BINDINGS = [
        Binding("n", "new_workflow", "New Workflow"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
        Binding("enter", "view_details", "View Details"),
        Binding("p", "pause_workflow", "Pause"),
        Binding("ctrl+c", "resume_workflow", "Resume"),
        Binding("d", "delete_workflow", "Delete"),
    ]
    
    workflows = reactive([])
    selected_index = reactive(0)
    
    def compose(self) -> ComposeResult:
        """Compose the screen layout"""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            with Horizontal():
                # Left panel - Workflow list
                with Vertical(id="workflow-list-panel"):
                    yield Static("🌟 Active Workflows 🌟", id="panel-title")
                    yield DataTable(id="workflow-table")
                    
                    with Horizontal(id="action-buttons"):
                        yield Button("➕ New", id="new-btn", variant="primary")
                        yield Button("🔄 Refresh", id="refresh-btn")
                        yield Button("⏸️  Pause", id="pause-btn")
                        yield Button("▶️  Resume", id="resume-btn")
                        yield Button("🗑️  Delete", id="delete-btn", variant="error")
                
                # Right panel - Details and logs
                with Vertical(id="detail-panel"):
                    with TabbedContent(initial="details-tab"):
                        with TabPane("Details", id="details-tab"):
                            yield Static("Select a workflow to view details", id="detail-content")
                        
                        with TabPane("Tasks", id="tasks-tab"):
                            yield TaskListWidget(id="task-list")
                        
                        with TabPane("Logs", id="logs-tab"):
                            yield LogViewer(id="log-viewer")
                        
                        with TabPane("Metrics", id="metrics-tab"):
                            yield MetricsPanel(id="metrics-panel")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the screen"""
        # Setup DataTable
        table = self.query_one("#workflow-table", DataTable)
        table.add_columns("Status", "ID", "Progress", "Tasks", "Created")
        table.cursor_type = "row"
        
        # Load workflows
        self.refresh_workflows()
        
        # Start auto-refresh
        self.set_interval(5, self.refresh_workflows)
    
    async def refresh_workflows(self) -> None:
        """Refresh workflow list from API"""
        try:
            async with APIClient() as client:
                workflows = await client.list_workflows(limit=50)
                self.workflows = workflows
                self.update_table()
                
                # Update log
                log_viewer = self.query_one("#log-viewer", LogViewer)
                log_viewer.add_log(
                    f"Loaded {len(workflows)} workflows",
                    level="info"
                )
        except Exception as e:
            log_viewer = self.query_one("#log-viewer", LogViewer)
            log_viewer.add_log(
                f"Failed to load workflows: {str(e)}",
                level="error"
            )
    
    def update_table(self) -> None:
        """Update the workflow table"""
        table = self.query_one("#workflow-table", DataTable)
        table.clear()
        
        for wf in self.workflows:
            status = wf.get("status", "unknown")
            wf_id = wf.get("workflow_id", "unknown")[:16]
            progress = wf.get("progress", 0.0)
            task_count = wf.get("task_count", 0)
            completed = wf.get("completed_tasks", 0)
            created = wf.get("created_at", "")[:19]
            
            # Color-coded status
            status_text = Text(status.upper(), style=get_status_color(status))
            progress_text = Text(f"{int(progress * 100)}%", style="cyan")
            tasks_text = Text(f"{completed}/{task_count}", style="yellow")
            
            table.add_row(
                status_text,
                wf_id,
                progress_text,
                tasks_text,
                created
            )
    
    def action_new_workflow(self) -> None:
        """Create a new workflow"""
        self.app.push_screen(CreateWorkflowModal(), self.on_workflow_created)
    
    async def on_workflow_created(self, request: Optional[str]) -> None:
        """Handle workflow creation result"""
        if not request:
            return
        
        log_viewer = self.query_one("#log-viewer", LogViewer)
        log_viewer.add_log(f"Creating workflow: {request}", level="info")
        
        try:
            async with APIClient() as client:
                result = await client.create_workflow(
                    request=request,
                    auto_execute=True,
                    auto_fix_mode=True
                )
                
                workflow_id = result.get("workflow_id", "unknown")
                log_viewer.add_log(
                    f"✓ Workflow created: {workflow_id}",
                    level="success"
                )
                
                # Refresh list
                await self.refresh_workflows()
        except Exception as e:
            log_viewer.add_log(
                f"✗ Failed to create workflow: {str(e)}",
                level="error"
            )
    
    def action_refresh(self) -> None:
        """Refresh workflow list"""
        self.refresh_workflows()
    
    def action_quit(self) -> None:
        """Quit the application"""
        self.app.exit()
    
    async def action_view_details(self) -> None:
        """View selected workflow details"""
        table = self.query_one("#workflow-table", DataTable)
        
        if table.cursor_row < len(self.workflows):
            workflow = self.workflows[table.cursor_row]
            workflow_id = workflow.get("workflow_id")
            
            try:
                async with APIClient() as client:
                    details = await client.get_workflow_status(workflow_id)
                    
                    # Update detail content
                    detail_static = self.query_one("#detail-content", Static)
                    detail_text = self._format_workflow_details(details)
                    detail_static.update(detail_text)
                    
                    # Update task list
                    task_list = self.query_one("#task-list", TaskListWidget)
                    task_list.tasks = details.get("tasks", [])
                    
                    # Log
                    log_viewer = self.query_one("#log-viewer", LogViewer)
                    log_viewer.add_log(
                        f"Loaded details for {workflow_id}",
                        level="info"
                    )
            except Exception as e:
                log_viewer = self.query_one("#log-viewer", LogViewer)
                log_viewer.add_log(
                    f"Failed to load details: {str(e)}",
                    level="error"
                )
    
    def _format_workflow_details(self, details: Dict[str, Any]) -> Text:
        """Format workflow details for display"""
        text = Text()
        
        text.append("🌟 Workflow Details 🌟\n\n", style="bold magenta")
        
        wf_id = details.get("workflow_id", "unknown")
        status = details.get("status", "unknown")
        progress = details.get("progress", 0.0)
        created = details.get("created_at", "")
        
        text.append("ID: ", style="bold cyan")
        text.append(f"{wf_id}\n", style="cyan")
        
        text.append("Status: ", style="bold cyan")
        text.append(f"{status.upper()}\n", style=get_status_color(status))
        
        text.append("Progress: ", style="bold cyan")
        text.append(f"{int(progress * 100)}%\n", style="yellow")
        
        text.append("Created: ", style="bold cyan")
        text.append(f"{created}\n", style="dim")
        
        text.append("\nAuto-fix: ", style="bold cyan")
        auto_fix = details.get("auto_fix_mode", False)
        text.append(f"{'Enabled' if auto_fix else 'Disabled'}\n", 
                   style="green" if auto_fix else "red")
        
        return text
    
    async def action_pause_workflow(self) -> None:
        """Pause selected workflow"""
        table = self.query_one("#workflow-table", DataTable)
        
        if table.cursor_row < len(self.workflows):
            workflow = self.workflows[table.cursor_row]
            workflow_id = workflow.get("workflow_id")
            
            try:
                async with APIClient() as client:
                    await client.pause_workflow(workflow_id)
                    
                    log_viewer = self.query_one("#log-viewer", LogViewer)
                    log_viewer.add_log(
                        f"⏸️  Paused workflow {workflow_id}",
                        level="warning"
                    )
                    
                    await self.refresh_workflows()
            except Exception as e:
                log_viewer = self.query_one("#log-viewer", LogViewer)
                log_viewer.add_log(
                    f"Failed to pause workflow: {str(e)}",
                    level="error"
                )
    
    async def action_resume_workflow(self) -> None:
        """Resume selected workflow"""
        table = self.query_one("#workflow-table", DataTable)
        
        if table.cursor_row < len(self.workflows):
            workflow = self.workflows[table.cursor_row]
            workflow_id = workflow.get("workflow_id")
            
            try:
                async with APIClient() as client:
                    await client.resume_workflow(workflow_id)
                    
                    log_viewer = self.query_one("#log-viewer", LogViewer)
                    log_viewer.add_log(
                        f"▶️  Resumed workflow {workflow_id}",
                        level="success"
                    )
                    
                    await self.refresh_workflows()
            except Exception as e:
                log_viewer = self.query_one("#log-viewer", LogViewer)
                log_viewer.add_log(
                    f"Failed to resume workflow: {str(e)}",
                    level="error"
                )
    
    async def action_delete_workflow(self) -> None:
        """Delete/cancel selected workflow"""
        table = self.query_one("#workflow-table", DataTable)
        
        if table.cursor_row < len(self.workflows):
            workflow = self.workflows[table.cursor_row]
            workflow_id = workflow.get("workflow_id")
            
            try:
                async with APIClient() as client:
                    await client.cancel_workflow(workflow_id)
                    
                    log_viewer = self.query_one("#log-viewer", LogViewer)
                    log_viewer.add_log(
                        f"🗑️  Cancelled workflow {workflow_id}",
                        level="warning"
                    )
                    
                    await self.refresh_workflows()
            except Exception as e:
                log_viewer = self.query_one("#log-viewer", LogViewer)
                log_viewer.add_log(
                    f"Failed to cancel workflow: {str(e)}",
                    level="error"
                )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "new-btn":
            self.action_new_workflow()
        elif event.button.id == "refresh-btn":
            self.action_refresh()
        elif event.button.id == "pause-btn":
            asyncio.create_task(self.action_pause_workflow())
        elif event.button.id == "resume-btn":
            asyncio.create_task(self.action_resume_workflow())
        elif event.button.id == "delete-btn":
            asyncio.create_task(self.action_delete_workflow())


class AlgoCLIApp(App):
    """Main AlgoCLI Application"""
    
    CSS = LUMINOUS_CSS + """
    #main-container {
        height: 100%;
        background: $background;
    }
    
    #workflow-list-panel {
        width: 50%;
        height: 100%;
        border: tall $primary;
        padding: 1;
    }
    
    #detail-panel {
        width: 50%;
        height: 100%;
        border: tall $secondary;
        padding: 1;
    }
    
    #panel-title {
        text-align: center;
        color: $primary;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #workflow-table {
        height: 1fr;
        margin-bottom: 1;
    }
    
    #action-buttons {
        height: auto;
        align: center middle;
    }
    
    #action-buttons Button {
        margin: 0 1;
    }
    
    #detail-content {
        padding: 1;
    }
    
    #task-list {
        height: 100%;
    }
    
    #log-viewer {
        height: 100%;
        border: tall $border-blurred;
        padding: 1;
    }
    
    #metrics-panel {
        height: 100%;
        padding: 1;
    }
    """
    
    TITLE = "🌟 AlgoCLI - Multi-Agent Workflow Manager 🌟"
    
    # Register the luminous theme
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_theme(LUMINOUS_THEME)
        self.theme = "luminous"
    
    def on_mount(self) -> None:
        """Initialize the application"""
        self.push_screen(WorkflowListScreen())
        
        # Check API health
        asyncio.create_task(self.check_api_health())
    
    async def check_api_health(self) -> None:
        """Check if API is reachable"""
        try:
            async with APIClient() as client:
                health = await client.health_check()
                
                if health.get("status") == "healthy":
                    self.notify(
                        "✓ Connected to API server",
                        severity="information",
                        timeout=3
                    )
                else:
                    self.notify(
                        "⚠ API server unhealthy",
                        severity="warning",
                        timeout=5
                    )
        except Exception as e:
            self.notify(
                f"✗ Cannot connect to API: {str(e)}",
                severity="error",
                timeout=10
            )


def main():
    """Entry point for the CLI application"""
    app = AlgoCLIApp()
    app.run()


if __name__ == "__main__":
    main()
