"""
Utility functions for AlgoCLI
Helper functions for formatting, validation, and common operations
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import re


def format_timestamp(iso_timestamp: str, format: str = "short") -> str:
    """
    Format ISO timestamp to readable format
    
    Args:
        iso_timestamp: ISO 8601 timestamp string
        format: 'short', 'medium', 'long', or 'relative'
    
    Returns:
        Formatted timestamp string
    """
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        
        if format == "short":
            return dt.strftime("%H:%M:%S")
        elif format == "medium":
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        elif format == "long":
            return dt.strftime("%B %d, %Y at %I:%M:%S %p")
        elif format == "relative":
            return get_relative_time(dt)
        else:
            return dt.isoformat()
    except Exception:
        return iso_timestamp[:19]  # Fallback to first 19 chars


def get_relative_time(dt: datetime) -> str:
    """
    Get relative time string (e.g., '5 minutes ago')
    
    Args:
        dt: datetime object
    
    Returns:
        Relative time string
    """
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to readable string
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_progress(current: int, total: int, width: int = 20) -> str:
    """
    Format progress as text-based progress bar
    
    Args:
        current: Current progress
        total: Total items
        width: Width of progress bar
    
    Returns:
        Progress bar string
    """
    if total == 0:
        return "[" + " " * width + "] 0%"
    
    percentage = current / total
    filled = int(width * percentage)
    bar = "█" * filled + "░" * (width - filled)
    
    return f"[{bar}] {int(percentage * 100)}%"


def parse_workflow_id(workflow_id: str) -> Dict[str, str]:
    """
    Parse workflow ID into components
    
    Expected format: wf_YYYYMMDD_HHMMSS_random
    
    Args:
        workflow_id: Workflow ID string
    
    Returns:
        Dictionary with parsed components
    """
    parts = workflow_id.split("_")
    
    if len(parts) >= 4 and parts[0] == "wf":
        try:
            date = parts[1]
            time = parts[2]
            random = "_".join(parts[3:])
            
            return {
                "date": f"{date[:4]}-{date[4:6]}-{date[6:8]}",
                "time": f"{time[:2]}:{time[2:4]}:{time[4:6]}",
                "random": random,
                "full": workflow_id
            }
        except:
            pass
    
    return {"full": workflow_id}


def validate_request(request: str) -> tuple[bool, Optional[str]]:
    """
    Validate workflow request
    
    Args:
        request: User's workflow request
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not request or not request.strip():
        return False, "Request cannot be empty"
    
    if len(request) < 10:
        return False, "Request is too short (minimum 10 characters)"
    
    if len(request) > 1000:
        return False, "Request is too long (maximum 1000 characters)"
    
    return True, None


def get_status_icon(status: str) -> str:
    """
    Get emoji icon for status
    
    Args:
        status: Status string
    
    Returns:
        Emoji icon
    """
    status_icons = {
        "created": "🔵",
        "running": "🟢",
        "paused": "🟡",
        "completed": "✅",
        "failed": "❌",
        "cancelled": "⛔",
        "pending": "⚪",
        "in-progress": "🔄",
        "in_progress": "🔄",
        "blocked": "🚫",
    }
    return status_icons.get(status.lower(), "⚪")


def get_agent_icon(agent: str) -> str:
    """
    Get emoji icon for agent type
    
    Args:
        agent: Agent name
    
    Returns:
        Emoji icon
    """
    agent_icons = {
        "planner": "🧠",
        "coder": "💻",
        "tester": "🧪",
        "debugger": "🔧",
        "architect": "🏗️",
    }
    return agent_icons.get(agent.lower(), "🤖")


def format_file_size(bytes: int) -> str:
    """
    Format file size in bytes to human-readable format
    
    Args:
        bytes: Size in bytes
    
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system use
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename or "unnamed"


def calculate_eta(progress: float, elapsed_seconds: float) -> Optional[str]:
    """
    Calculate estimated time remaining
    
    Args:
        progress: Progress as float (0.0 to 1.0)
        elapsed_seconds: Seconds elapsed so far
    
    Returns:
        ETA string or None if cannot calculate
    """
    if progress <= 0 or progress >= 1:
        return None
    
    total_time = elapsed_seconds / progress
    remaining = total_time - elapsed_seconds
    
    return format_duration(remaining)


def extract_error_message(error: Exception) -> str:
    """
    Extract user-friendly error message from exception
    
    Args:
        error: Exception object
    
    Returns:
        Formatted error message
    """
    error_str = str(error)
    
    # Extract specific error patterns
    if "Connection refused" in error_str or "Failed to connect" in error_str:
        return "Cannot connect to API server. Is it running?"
    elif "Timeout" in error_str:
        return "Request timed out. Server may be overloaded."
    elif "404" in error_str:
        return "Resource not found."
    elif "401" in error_str or "403" in error_str:
        return "Authentication failed."
    elif "500" in error_str:
        return "Server error. Check server logs."
    else:
        return error_str[:200]  # Truncate long errors


def create_table_row(
    columns: List[str],
    widths: List[int],
    separator: str = " | "
) -> str:
    """
    Create formatted table row
    
    Args:
        columns: Column values
        widths: Column widths
        separator: Column separator
    
    Returns:
        Formatted row string
    """
    formatted = []
    for col, width in zip(columns, widths):
        formatted.append(col[:width].ljust(width))
    return separator.join(formatted)
