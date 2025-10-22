"""
Validate Interactive Backtest Setup
===================================

Quick validation script to check if all files are in place
and basic functionality is working.

This doesn't require external dependencies and just validates structure.

Version: 1.0.0
"""

import sys
from pathlib import Path as PathLib


def check_file_exists(file_path: PathLib, description: str) -> bool:
    """Check if a file exists."""
    if file_path.exists():
        print(f"✓ {description}: {file_path.name}")
        return True
    else:
        print(f"✗ {description}: {file_path.name} (NOT FOUND)")
        return False


def validate_setup():
    """Validate the interactive backtest setup."""
    print("\n" + "=" * 70)
    print("INTERACTIVE BACKTEST SETUP VALIDATION")
    print("=" * 70)
    print()
    
    backtest_dir = PathLib(__file__).parent
    data_dir = backtest_dir.parent / "Data"
    
    checks = []
    
    # Check core files
    print("Core Files:")
    checks.append(check_file_exists(
        backtest_dir / "interactive_backtest_runner.py",
        "Interactive runner"
    ))
    checks.append(check_file_exists(
        backtest_dir / "quick_interactive_backtest.py",
        "Quick runner"
    ))
    checks.append(check_file_exists(
        backtest_dir / "test_interactive_backtest.py",
        "Test suite"
    ))
    
    print()
    
    # Check batch files
    print("Batch Files:")
    checks.append(check_file_exists(
        backtest_dir / "run_interactive_backtest.bat",
        "Interactive launcher"
    ))
    checks.append(check_file_exists(
        backtest_dir / "run_quick_backtest.bat",
        "Quick launcher"
    ))
    
    print()
    
    # Check documentation
    print("Documentation:")
    checks.append(check_file_exists(
        backtest_dir / "INTERACTIVE_BACKTEST_README.md",
        "Interactive README"
    ))
    checks.append(check_file_exists(
        backtest_dir / "SETUP_GUIDE.md",
        "Setup guide"
    ))
    
    print()
    
    # Check dependencies
    print("Dependencies:")
    checks.append(check_file_exists(
        backtest_dir / "sim_broker.py",
        "SimBroker module"
    ))
    checks.append(check_file_exists(
        backtest_dir / "config.py",
        "Config module"
    ))
    checks.append(check_file_exists(
        backtest_dir / "example_strategy.py",
        "Example strategy"
    ))
    
    print()
    
    # Check Data module
    print("Data Module:")
    checks.append(check_file_exists(
        data_dir / "data_fetcher.py",
        "Data fetcher"
    ))
    
    print()
    
    # Check results directory
    print("Output Directories:")
    results_dir = backtest_dir / "results"
    if not results_dir.exists():
        results_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created results directory: {results_dir}")
    else:
        print(f"✓ Results directory exists: {results_dir}")
    
    print()
    
    # Test basic imports (without external dependencies)
    print("Basic Import Tests:")
    try:
        from datetime import datetime
        print("✓ datetime import")
        checks.append(True)
    except ImportError:
        print("✗ datetime import (FAILED)")
        checks.append(False)
    
    try:
        import pathlib
        print("✓ pathlib import")
        checks.append(True)
    except ImportError:
        print("✗ pathlib import (FAILED)")
        checks.append(False)
    
    try:
        # Test if we can import our validate_date function
        sys.path.insert(0, str(backtest_dir.parent))
        from Backtest.interactive_backtest_runner import validate_date
        
        # Test it
        is_valid, date_obj = validate_date("2024-01-01")
        if is_valid and date_obj is not None:
            print("✓ validate_date function works")
            checks.append(True)
        else:
            print("✗ validate_date function (returned unexpected result)")
            checks.append(False)
    except Exception as e:
        print(f"✗ validate_date function ({e})")
        checks.append(False)
    
    print()
    
    # Summary
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"Checks passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All checks passed!")
        print("\nNext steps:")
        print("1. Install yfinance: pip install yfinance pandas numpy")
        print("2. Run: python quick_interactive_backtest.py")
        print("   OR double-click: run_quick_backtest.bat")
        return True
    else:
        print(f"\n⚠️  {total - passed} check(s) failed")
        print("\nPlease ensure all files are in place before running.")
        return False


if __name__ == "__main__":
    success = validate_setup()
    sys.exit(0 if success else 1)
