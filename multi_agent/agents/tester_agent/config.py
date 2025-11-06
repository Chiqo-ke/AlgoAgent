"""Configuration for Tester Agent."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TesterConfig:
    """Configuration for test execution."""
    
    # Timeouts
    default_timeout: int = 300  # seconds
    docker_build_timeout: int = 600  # seconds
    
    # Resource limits
    memory_limit: str = "1g"
    cpu_limit: str = "0.5"
    
    # Docker settings
    docker_image: str = "algo-sandbox"
    dockerfile_path: str = "sandbox_runner/Dockerfile.sandbox"
    network_mode: str = "none"  # Network isolation
    remove_container: bool = True  # Ephemeral containers
    
    # Security
    run_as_user: str = "runner"
    enable_secret_scanning: bool = True
    secret_patterns: list = None
    
    # Determinism
    determinism_tolerance: float = 0.01  # PnL tolerance
    determinism_runs: int = 2
    
    # Artifacts
    artifacts_base_dir: str = "artifacts"
    required_artifacts: list = None
    
    def __post_init__(self):
        """Set defaults for mutable fields."""
        if self.secret_patterns is None:
            self.secret_patterns = [
                r'(?i)(api[_-]?key|apikey)[\s:=]+[\'\"]?([a-zA-Z0-9_-]{20,})[\'\"]?',
                r'(?i)(secret[_-]?key|secretkey)[\s:=]+[\'\"]?([a-zA-Z0-9_-]{20,})[\'\"]?',
                r'(?i)(token)[\s:=]+[\'\"]?([a-zA-Z0-9_-]{20,})[\'\"]?',
                r'(?i)(password|passwd|pwd)[\s:=]+[\'\"]?([^\s\'\";]{8,})[\'\"]?',
            ]
        
        if self.required_artifacts is None:
            self.required_artifacts = [
                'test_report.json',
                'trades.csv',
                'equity_curve.csv',
                'events.log',
            ]


# Global config instance
config = TesterConfig()
