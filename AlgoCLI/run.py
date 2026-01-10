#!/usr/bin/env python3
"""
Startup script for AlgoCLI
Checks dependencies and launches the application
"""

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")


def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        "textual",
        "rich",
        "httpx",
        "pydantic",
        "dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} (missing)")
    
    if missing_packages:
        print("\n❌ Missing dependencies detected!")
        print("   Run: pip install -r requirements.txt")
        sys.exit(1)


def check_env_file():
    """Check if .env file exists, create from example if not"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠ .env file not found, creating from .env.example")
            env_file.write_text(env_example.read_text())
            print("✓ .env file created")
        else:
            print("⚠ No .env file found (using defaults)")
    else:
        print("✓ .env file exists")


def main():
    """Main startup function"""
    print("=" * 60)
    print("  🌟 AlgoCLI - Multi-Agent Workflow Manager 🌟")
    print("=" * 60)
    print("\nChecking system requirements...\n")
    
    # Check Python version
    check_python_version()
    
    # Check dependencies
    print("\nChecking dependencies...\n")
    check_dependencies()
    
    # Check environment
    print("\nChecking configuration...\n")
    check_env_file()
    
    print("\n" + "=" * 60)
    print("  All checks passed! Starting AlgoCLI...")
    print("=" * 60 + "\n")
    
    # Import and run the app
    try:
        from app import main as app_main
        app_main()
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
