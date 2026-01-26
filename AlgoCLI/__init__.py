"""
AlgoCLI - Multi-Agent Workflow Manager
A stunning Textual-based CLI for managing AI-driven trading strategy workflows
"""

__version__ = "1.0.0"
__author__ = "AlgoAgent Team"
__description__ = "CLI interface for multi-agent workflow management"

from .app import AlgoCLIApp, main
from .api_client import APIClient
from .config import config

__all__ = [
    "AlgoCLIApp",
    "main",
    "APIClient",
    "config",
]
