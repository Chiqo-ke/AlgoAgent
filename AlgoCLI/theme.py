"""
Luminous Theme for AlgoCLI
A stunning glowing theme with vibrant colors and high contrast
"""

from textual.theme import Theme

# Define the luminous color palette
LUMINOUS_THEME = Theme(
    name="luminous",
    primary="#00FFFF",          # Bright cyan
    secondary="#FF00FF",        # Bright magenta
    accent="#FFFF00",           # Bright yellow
    warning="#FF6B35",          # Bright orange
    error="#FF1744",            # Bright red
    success="#00FF88",          # Bright green
    background="#0A0E27",       # Dark blue-black
    surface="#1A1F3A",          # Slightly lighter dark blue
    panel="#252A48",            # Panel background
    dark=True,
    variables={
        # Primary colors
        "primary": "#00FFFF",
        "primary-background": "#003B3F",
        "primary-lighten-1": "#33FFFF",
        "primary-lighten-2": "#66FFFF",
        "primary-lighten-3": "#99FFFF",
        "primary-darken-1": "#00CCCC",
        "primary-darken-2": "#009999",
        "primary-darken-3": "#006666",
        
        # Secondary colors
        "secondary": "#FF00FF",
        "secondary-background": "#3F003F",
        "secondary-lighten-1": "#FF33FF",
        "secondary-lighten-2": "#FF66FF",
        "secondary-lighten-3": "#FF99FF",
        "secondary-darken-1": "#CC00CC",
        "secondary-darken-2": "#990099",
        "secondary-darken-3": "#660066",
        
        # Accent colors
        "accent": "#FFFF00",
        "accent-lighten-1": "#FFFF33",
        "accent-lighten-2": "#FFFF66",
        "accent-lighten-3": "#FFFF99",
        "accent-darken-1": "#CCCC00",
        "accent-darken-2": "#999900",
        "accent-darken-3": "#666600",
        
        # Status colors
        "success": "#00FF88",
        "success-background": "#003F22",
        "info": "#00BBFF",
        "warning": "#FF6B35",
        "warning-background": "#3F1A0D",
        "error": "#FF1744",
        "error-background": "#3F0511",
        
        # Background colors
        "background": "#0A0E27",
        "surface": "#1A1F3A",
        "surface-lighten-1": "#252A48",
        "surface-lighten-2": "#303556",
        "surface-lighten-3": "#3B4064",
        "surface-darken-1": "#15192E",
        "surface-darken-2": "#0F1322",
        "surface-darken-3": "#0A0E27",
        
        # Border colors
        "border": "#00FFFF",
        "border-blurred": "#006666",
        
        # Text colors
        "text": "#FFFFFF",
        "text-muted": "#9EAAB8",
        "text-disabled": "#4A5568",
        
        # Progress colors
        "progress-bar": "#00FFFF",
        "progress-bar-background": "#1A1F3A",
        
        # Special effects
        "glow": "#00FFFF80",
        "shadow": "#00000080",
        
        # Component-specific
        "input": "#00FFFF",
        "input-background": "#252A48",
        "button": "#FF00FF",
        "button-hover": "#FF33FF",
        "scrollbar": "#00FFFF",
        "scrollbar-background": "#252A48",
        
        # Workflow status colors
        "status-created": "#00BBFF",
        "status-running": "#00FF88",
        "status-paused": "#FFFF00",
        "status-completed": "#00FF88",
        "status-failed": "#FF1744",
        "status-cancelled": "#FF6B35",
        
        # Task colors
        "task-pending": "#9EAAB8",
        "task-in-progress": "#00FFFF",
        "task-completed": "#00FF88",
        "task-failed": "#FF1744",
        "task-blocked": "#FF6B35",
        
        # Agent colors
        "agent-planner": "#FF00FF",
        "agent-coder": "#00FFFF",
        "agent-tester": "#FFFF00",
        "agent-debugger": "#FF6B35",
    }
)

# CSS stylesheet for the luminous theme
LUMINOUS_CSS = """
/* Global styling */
Screen {
    background: $background;
    color: $text;
}

/* Containers and panels */
Container {
    background: $surface;
    border: tall $border;
}

Static {
    background: $surface;
}

/* Headers */
Header {
    background: $primary;
    color: $background;
    text-style: bold;
}

/* Footer */
Footer {
    background: $surface-lighten-1;
    color: $text-muted;
}

/* Buttons */
Button {
    background: $button;
    color: $text;
    border: tall $primary;
    text-style: bold;
}

Button:hover {
    background: $button-hover;
    color: $text;
    border: tall $primary-lighten-1;
    text-style: bold;
}

Button:focus {
    background: $button-hover;
    border: tall $primary-lighten-2;
    text-style: bold;
}

Button.-primary {
    background: $primary;
    color: $background;
    border: tall $primary-lighten-1;
}

Button.-warning {
    background: $warning;
    color: $background;
    border: tall $warning;
}

Button.-error {
    background: $error;
    color: $text;
    border: tall $error;
}

/* Input fields */
Input {
    background: $input-background;
    color: $input;
    border: tall $border;
}

Input:focus {
    background: $input-background;
    color: $input;
    border: tall $primary-lighten-1;
}

/* Lists and DataTables */
ListView {
    background: $surface;
    border: tall $border-blurred;
}

ListItem {
    background: $surface;
    color: $text;
}

ListItem:hover {
    background: $surface-lighten-1;
    color: $primary;
}

DataTable {
    background: $surface;
    border: tall $border;
}

DataTable > .datatable--header {
    background: $surface-lighten-1;
    color: $primary;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: $primary-background;
    color: $primary;
}

/* Progress bars */
ProgressBar {
    background: $progress-bar-background;
}

ProgressBar > .bar--bar {
    background: $progress-bar;
    color: $background;
}

ProgressBar > .bar--complete {
    background: $success;
}

/* Log and text areas */
RichLog {
    background: $surface-darken-1;
    border: tall $border-blurred;
    color: $text;
}

TextArea {
    background: $surface;
    border: tall $border;
    color: $text;
}

/* Scrollbars */
Vertical {
    background: $scrollbar-background;
}

Horizontal {
    background: $scrollbar-background;
}

VerticalScroll > .scrollbar--thumb {
    background: $scrollbar;
}

HorizontalScroll > .scrollbar--thumb {
    background: $scrollbar;
}

/* Tree */
Tree {
    background: $surface;
    border: tall $border-blurred;
}

Tree > .tree--cursor {
    background: $surface-lighten-1;
    color: $primary;
}

/* Tabs */
TabbedContent {
    background: $surface;
}

Tabs {
    background: $surface-lighten-1;
}

Tab {
    background: $surface-lighten-1;
    color: $text-muted;
}

Tab:hover {
    background: $surface-lighten-2;
    color: $primary;
}

Tab.-active {
    background: $primary-background;
    color: $primary;
    text-style: bold;
}

/* Placeholder */
Placeholder {
    background: $surface-darken-1;
    border: tall $border-blurred;
    color: $text-muted;
}

/* Custom status indicators */
.status-created {
    color: $status-created;
    text-style: bold;
}

.status-running {
    color: $status-running;
    text-style: bold;
}

.status-paused {
    color: $status-paused;
    text-style: bold;
}

.status-completed {
    color: $status-completed;
    text-style: bold;
}

.status-failed {
    color: $status-failed;
    text-style: bold;
}

.status-cancelled {
    color: $status-cancelled;
    text-style: bold;
}

/* Agent indicators */
.agent-planner {
    color: $agent-planner;
    text-style: bold;
}

.agent-coder {
    color: $agent-coder;
    text-style: bold;
}

.agent-tester {
    color: $agent-tester;
    text-style: bold;
}

.agent-debugger {
    color: $agent-debugger;
    text-style: bold;
}

/* Glow effects */
.glow {
    text-style: bold;
}

.glow-primary {
    color: $primary;
    text-style: bold;
}

.glow-secondary {
    color: $secondary;
    text-style: bold;
}

.glow-accent {
    color: $accent;
    text-style: bold;
}

/* Workflow card */
.workflow-card {
    background: $surface-lighten-1;
    border: tall $border;
    padding: 1;
}

.workflow-card:hover {
    background: $surface-lighten-2;
    border: tall $primary-lighten-1;
}

/* Task item */
.task-item {
    background: $surface;
    padding: 0 1;
}

.task-pending {
    color: $task-pending;
}

.task-in-progress {
    color: $task-in-progress;
    text-style: bold;
}

.task-completed {
    color: $task-completed;
}

.task-failed {
    color: $task-failed;
}
"""


def get_status_color(status: str) -> str:
    """Get color for workflow status"""
    status_colors = {
        "created": "#00BBFF",
        "running": "#00FF88",
        "paused": "#FFFF00",
        "completed": "#00FF88",
        "failed": "#FF1744",
        "cancelled": "#FF6B35",
    }
    return status_colors.get(status.lower(), "#9EAAB8")


def get_agent_color(agent: str) -> str:
    """Get color for agent type"""
    agent_colors = {
        "planner": "#FF00FF",
        "coder": "#00FFFF",
        "tester": "#FFFF00",
        "debugger": "#FF6B35",
    }
    return agent_colors.get(agent.lower(), "#9EAAB8")


def get_task_color(status: str) -> str:
    """Get color for task status"""
    task_colors = {
        "pending": "#9EAAB8",
        "in-progress": "#00FFFF",
        "in_progress": "#00FFFF",
        "completed": "#00FF88",
        "failed": "#FF1744",
        "blocked": "#FF6B35",
    }
    return task_colors.get(status.lower(), "#9EAAB8")
