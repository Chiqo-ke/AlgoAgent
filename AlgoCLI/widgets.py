"""
Custom Widgets for AlgoCLI
Reusable UI components with luminous theme styling
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, ProgressBar, Label, ListItem, ListView
from textual.reactive import reactive
from rich.text import Text
from rich.table import Table
from datetime import datetime
from typing import Optional, List, Dict, Any

from theme import get_status_color, get_agent_color, get_task_color


class WorkflowCard(Static):
    """A card displaying workflow summary information"""
    
    workflow_data = reactive({})
    
    def __init__(self, workflow_data: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.workflow_data = workflow_data
        self.add_class("workflow-card")
    
    def render(self) -> Text:
        """Render the workflow card"""
        if not self.workflow_data:
            return Text("No workflow data", style="dim")
        
        wf_id = self.workflow_data.get("workflow_id", "Unknown")
        status = self.workflow_data.get("status", "unknown")
        progress = self.workflow_data.get("progress", 0.0)
        created_at = self.workflow_data.get("created_at", "")
        task_count = self.workflow_data.get("task_count", 0)
        completed_tasks = self.workflow_data.get("completed_tasks", 0)
        
        # Format the output
        text = Text()
        
        # Workflow ID with glow effect
        text.append("🌟 ", style=get_status_color(status))
        text.append(f"{wf_id[:16]}...\n", style="bold " + get_status_color(status))
        
        # Status
        text.append("Status: ", style="dim")
        text.append(f"{status.upper()}\n", style="bold " + get_status_color(status))
        
        # Progress
        progress_pct = int(progress * 100)
        text.append("Progress: ", style="dim")
        text.append(f"{progress_pct}% ", style="bold cyan")
        text.append(f"({completed_tasks}/{task_count} tasks)\n", style="dim")
        
        # Created time
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                time_str = dt.strftime("%H:%M:%S")
                text.append(f"⏰ {time_str}", style="dim")
            except:
                text.append(f"⏰ {created_at[:19]}", style="dim")
        
        return text
    
    def watch_workflow_data(self, new_data: Dict[str, Any]) -> None:
        """React to workflow data changes"""
        self.refresh()


class TaskListWidget(Static):
    """Widget displaying task list with progress"""
    
    tasks = reactive([])
    
    def __init__(self, tasks: List[Dict[str, Any]] = None, **kwargs):
        super().__init__(**kwargs)
        self.tasks = tasks or []
    
    def render(self) -> Table:
        """Render task list as a table"""
        table = Table(
            show_header=True,
            header_style="bold cyan",
            border_style="cyan",
            title="📋 Tasks",
            title_style="bold magenta"
        )
        
        table.add_column("ID", style="dim", width=8)
        table.add_column("Agent", width=12)
        table.add_column("Description", ratio=1)
        table.add_column("Status", width=12)
        
        if not self.tasks:
            table.add_row("—", "—", "No tasks", "—")
            return table
        
        for task in self.tasks:
            task_id = task.get("task_id", "unknown")[:8]
            agent = task.get("agent", "unknown")
            description = task.get("description", "No description")[:50]
            status = task.get("status", "unknown")
            
            # Style based on status
            status_color = get_task_color(status)
            agent_color = get_agent_color(agent)
            
            table.add_row(
                task_id,
                f"[{agent_color}]{agent}[/]",
                description,
                f"[{status_color}]{status}[/]"
            )
        
        return table
    
    def watch_tasks(self, new_tasks: List[Dict[str, Any]]) -> None:
        """React to task list changes"""
        self.refresh()


class StatusIndicator(Static):
    """Animated status indicator"""
    
    status = reactive("unknown")
    
    def __init__(self, status: str = "unknown", **kwargs):
        super().__init__(**kwargs)
        self.status = status
    
    def render(self) -> Text:
        """Render status with icon"""
        status_icons = {
            "created": "🔵",
            "running": "🟢",
            "paused": "🟡",
            "completed": "✅",
            "failed": "❌",
            "cancelled": "⛔",
        }
        
        icon = status_icons.get(self.status.lower(), "⚪")
        color = get_status_color(self.status)
        
        text = Text()
        text.append(f"{icon} ", style=color)
        text.append(self.status.upper(), style=f"bold {color}")
        
        return text
    
    def watch_status(self, new_status: str) -> None:
        """React to status changes"""
        self.refresh()


class ProgressBarWidget(Container):
    """Custom progress bar with label"""
    
    progress = reactive(0.0)
    label_text = reactive("")
    
    def __init__(
        self,
        total: int = 100,
        progress: float = 0.0,
        label: str = "",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.total = total
        self.progress = progress
        self.label_text = label
    
    def compose(self) -> ComposeResult:
        """Compose the progress bar widget"""
        with Horizontal():
            yield Label(self.label_text, id="progress-label")
            yield ProgressBar(total=self.total, show_eta=False)
    
    def watch_progress(self, new_progress: float) -> None:
        """Update progress bar"""
        progress_bar = self.query_one(ProgressBar)
        progress_bar.update(progress=new_progress * self.total)
    
    def watch_label_text(self, new_label: str) -> None:
        """Update label"""
        label = self.query_one("#progress-label", Label)
        label.update(new_label)


class LogViewer(Static):
    """Scrollable log viewer with color coding"""
    
    logs = reactive([])
    max_logs = 100
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logs = []
    
    def add_log(self, message: str, level: str = "info") -> None:
        """Add a log message"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        level_colors = {
            "debug": "dim",
            "info": "cyan",
            "success": "green",
            "warning": "yellow",
            "error": "red",
        }
        
        color = level_colors.get(level.lower(), "white")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "color": color
        }
        
        self.logs.append(log_entry)
        
        # Keep only recent logs
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        
        self.refresh()
    
    def render(self) -> Text:
        """Render log messages"""
        text = Text()
        
        for log in self.logs[-20:]:  # Show last 20 logs
            ts = log["timestamp"]
            level = log["level"].upper()
            msg = log["message"]
            color = log["color"]
            
            text.append(f"[{ts}] ", style="dim")
            text.append(f"[{level:8}] ", style=f"bold {color}")
            text.append(f"{msg}\n", style=color)
        
        return text
    
    def watch_logs(self, new_logs: List[Dict]) -> None:
        """React to log changes"""
        self.refresh()


class MetricsPanel(Static):
    """Display system metrics"""
    
    metrics = reactive({})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metrics = {}
    
    def render(self) -> Table:
        """Render metrics table"""
        table = Table(
            show_header=False,
            border_style="cyan",
            title="📊 System Metrics",
            title_style="bold magenta"
        )
        
        table.add_column("Metric", style="bold cyan", width=20)
        table.add_column("Value", style="yellow")
        
        if not self.metrics:
            table.add_row("Status", "[dim]Loading...[/]")
            return table
        
        # Display metrics
        for key, value in self.metrics.items():
            formatted_key = key.replace("_", " ").title()
            formatted_value = str(value)
            
            if isinstance(value, float):
                formatted_value = f"{value:.2f}"
            elif isinstance(value, bool):
                formatted_value = "✓" if value else "✗"
            
            table.add_row(formatted_key, formatted_value)
        
        return table
    
    def watch_metrics(self, new_metrics: Dict) -> None:
        """React to metrics changes"""
        self.refresh()


class WorkflowDetailView(Container):
    """Detailed view of a single workflow"""
    
    workflow_id = reactive("")
    workflow_data = reactive({})
    
    def __init__(self, workflow_id: str = "", **kwargs):
        super().__init__(**kwargs)
        self.workflow_id = workflow_id
    
    def compose(self) -> ComposeResult:
        """Compose the detail view"""
        yield Static(f"Workflow: {self.workflow_id}", id="detail-title")
        yield StatusIndicator(status="loading")
        yield TaskListWidget()
        yield ProgressBarWidget(label="Overall Progress")
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """Update workflow data"""
        self.workflow_data = data
        
        # Update components
        if "status" in data:
            status_indicator = self.query_one(StatusIndicator)
            status_indicator.status = data["status"]
        
        if "tasks" in data:
            task_list = self.query_one(TaskListWidget)
            task_list.tasks = data["tasks"]
        
        if "progress" in data:
            progress_bar = self.query_one(ProgressBarWidget)
            progress_bar.progress = data["progress"]
            progress_bar.label_text = f"Progress: {int(data['progress'] * 100)}%"
