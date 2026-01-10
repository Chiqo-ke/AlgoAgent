"""
Configuration settings for AlgoCLI
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class APIConfig(BaseModel):
    """API configuration settings"""
    base_url: str = Field(
        default_factory=lambda: os.getenv("API_BASE_URL", "http://localhost:8000")
    )
    timeout: int = Field(
        default_factory=lambda: int(os.getenv("API_TIMEOUT", "30"))
    )
    websocket_url: str = Field(
        default_factory=lambda: os.getenv("WEBSOCKET_URL", "ws://localhost:8000/ws")
    )


class UIConfig(BaseModel):
    """UI configuration settings"""
    theme: str = "luminous"
    refresh_interval: int = 5  # seconds
    max_workflows_display: int = 50
    max_log_lines: int = 100
    animation_enabled: bool = True


class Config(BaseModel):
    """Main configuration"""
    api: APIConfig = Field(default_factory=APIConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    
    # Application metadata
    app_name: str = "AlgoCLI"
    app_version: str = "1.0.0"
    app_description: str = "Multi-Agent Workflow Manager"
    
    # Paths
    config_dir: Path = Field(default_factory=lambda: Path.home() / ".algocli")
    log_dir: Path = Field(default_factory=lambda: Path.home() / ".algocli" / "logs")
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


# Global configuration instance
config = Config()
config.ensure_directories()
