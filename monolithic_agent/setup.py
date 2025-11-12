#!/usr/bin/env python3
"""
AlgoAgent Setup Script
======================

This script helps you set up the AlgoAgent environment and validate the installation.

Usage:
    python setup.py
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_step(step, description):
    print(f"\n[{step}] {description}")
    print("-" * 40)

def check_file_exists(filepath, description):
    """Check if a file exists and print status."""
    if os.path.exists(filepath):
        print(f"  ✓ {description}")
        return True
    else:
        print(f"  ✗ {description} (Missing: {filepath})")
        return False

def create_env_file():
    """Create .env file from .env.example if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print(f"  Creating .env file from .env.example...")
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            content = src.read()
            dst.write(content)
        print(f"  ✓ .env file created")
        print(f"  📝 Please edit .env and add your GEMINI_API_KEY")
        return True
    elif env_file.exists():
        print(f"  ✓ .env file already exists")
        return True
    else:
        print(f"  ✗ Could not create .env file (.env.example missing)")
        return False

def check_python_packages():
    """Check if required packages are installed."""
    print_step("2", "Checking Python Dependencies")
    
    required_packages = [
        'pandas', 'numpy', 'yfinance', 'scikit-learn', 
        'pytest', 'ta', 'python-dotenv'
    ]
    
    missing_packages = []
    
    # Package mapping for imports that differ from pip names
    import_mapping = {
        'scikit-learn': 'sklearn',
        'python-dotenv': 'dotenv'
    }
    
    for package in required_packages:
        import_name = import_mapping.get(package, package.replace('-', '_'))
        try:
            __import__(import_name)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (Missing)")
            missing_packages.append(package)
    
    # Check TA-Lib separately
    try:
        import talib
        print(f"  ✓ TA-Lib (High performance mode available)")
    except ImportError:
        print(f"  ⚠ TA-Lib (Will use fallback - install for better performance)")
    
    if missing_packages:
        print(f"\n  💡 Install missing packages with:")
        print(f"     pip install {' '.join(missing_packages)}")
        return False
    
    return True

def validate_file_structure():
    """Check if all required files are present."""
    print_step("1", "Validating File Structure")
    
    required_files = [
        ("Data/registry.py", "Indicator registry"),
        ("Data/indicator_calculator.py", "Indicator calculator"),
        ("Data/data_fetcher.py", "Data fetcher"),
        ("Data/main.py", "Main data ingestion model"),
        ("Data/requirements.txt", "Requirements file"),
        (".env.example", "Environment template"),
    ]
    
    all_present = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_present = False
    
    return all_present

def run_basic_tests():
    """Run basic functionality tests."""
    print_step("4", "Running Basic Tests")
    
    try:
        # Test imports
        sys.path.insert(0, 'Data')
        import registry
        import indicator_calculator
        from main import DataIngestionModel
        
        print("  ✓ Core modules import successfully")
        
        # Test model initialization
        model = DataIngestionModel()
        print("  ✓ DataIngestionModel initializes")
        
        # Test registry
        indicators = registry.list_indicators()
        print(f"  ✓ Registry loaded ({len(indicators)} indicators available)")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Basic tests failed: {e}")
        return False

def main():
    print_header("ALGOAGENT SETUP & VALIDATION")
    
    # Change to project root directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print(f"Working directory: {os.getcwd()}")
    
    # Step 1: Validate file structure
    structure_ok = validate_file_structure()
    
    # Step 2: Check dependencies
    deps_ok = check_python_packages()
    
    # Step 3: Setup environment
    print_step("3", "Setting Up Environment")
    env_ok = create_env_file()
    
    # Step 4: Run basic tests
    if structure_ok and deps_ok:
        tests_ok = run_basic_tests()
    else:
        tests_ok = False
        print("  ⚠ Skipping tests due to missing dependencies")
    
    # Summary
    print_header("SETUP SUMMARY")
    
    print(f"File Structure: {'✓ PASS' if structure_ok else '✗ FAIL'}")
    print(f"Dependencies:   {'✓ PASS' if deps_ok else '✗ FAIL'}")
    print(f"Environment:    {'✓ PASS' if env_ok else '✗ FAIL'}")
    print(f"Basic Tests:    {'✓ PASS' if tests_ok else '✗ FAIL'}")
    
    if all([structure_ok, deps_ok, env_ok, tests_ok]):
        print(f"\n🎉 AlgoAgent is ready to use!")
        print(f"\nNext steps:")
        print(f"1. Edit .env file and add your GEMINI_API_KEY")
        print(f"2. Run full tests: cd Data && python -m pytest tests/ -v")
        print(f"3. Try the demo: cd Data && python final_demo.py")
    else:
        print(f"\n⚠ Setup incomplete. Please resolve the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())