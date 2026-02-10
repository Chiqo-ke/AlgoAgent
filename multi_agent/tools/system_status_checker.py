#!/usr/bin/env python3
"""
Trading System Status Checker
Comprehensive diagnostic tool for the TradingView + MT5 Python trading system
"""

import os
import sys
import subprocess
import importlib.util
from datetime import datetime
import json

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_status(item, status, details=""):
    """Print status with formatting"""
    status_symbol = "[OK]" if status else "[FAIL]"
    print(f"{status_symbol} {item:<40} {details}")

def check_python_environment():
    """Check Python version and basic environment"""
    print_header("PYTHON ENVIRONMENT")
    
    # Python version
    python_version = sys.version.split()[0]
    print_status("Python Version", True, f"v{python_version}")
    
    # Python executable
    print_status("Python Executable", True, sys.executable)
    
    # Current working directory
    print_status("Working Directory", True, os.getcwd())
    
    return True

def check_required_packages():
    """Check if required packages are installed"""
    print_header("PYTHON PACKAGES")
    
    packages = {
        'MetaTrader5': 'MetaTrader5 SDK for trading',
        'pandas': 'Data manipulation library',
        'numpy': 'Numerical computing library',
        'matplotlib': 'Plotting library for charts'
    }
    
    installed_packages = {}
    
    for package, description in packages.items():
        try:
            spec = importlib.util.find_spec(package)
            if spec is not None:
                print_status(f"{package}", True, "Installed")
                installed_packages[package] = True
            else:
                print_status(f"{package}", False, "Not found")
                installed_packages[package] = False
        except Exception as e:
            print_status(f"{package}", False, f"Error: {str(e)}")
            installed_packages[package] = False
    
    return installed_packages

def check_system_files():
    """Check if all system files exist"""
    print_header("SYSTEM FILES")
    
    files_to_check = {
        'MT5 Framework': 'C:\\Users\\nyaga\\Documents\\AlgoAgent\\multi_agent\\frameworks\\mt5_trading_framework.py',
        'TradingView Scraper': 'C:\\Users\\nyaga\\Documents\\AlgoAgent\\multi_agent\\scrapers\\tradingview-scraper.js',
        'AAPL Strategy Main': 'C:\\Users\\nyaga\\Documents\\AlgoAgent\\multi_agent\\strategies\\aapl_momentum_trader\\main.py',
        'Strategy Config': 'C:\\Users\\nyaga\\Documents\\AlgoAgent\\multi_agent\\strategies\\aapl_momentum_trader\\config.py',
        'Data Manager': 'C:\\Users\\nyaga\\Documents\\AlgoAgent\\multi_agent\\strategies\\aapl_momentum_trader\\data_manager.py',
        'Risk Manager': 'C:\\Users\\nyaga\\Documents\\AlgoAgent\\multi_agent\\strategies\\aapl_momentum_trader\\risk_management.py',
        'MT5 Trader': 'C:\\Users\\nyaga\\Documents\\AlgoAgent\\multi_agent\\strategies\\aapl_momentum_trader\\mt5_trader.py',
        'Backtester': 'C:\\Users\\nyaga\\Documents\\AlgoAgent\\multi_agent\\strategies\\aapl_momentum_trader\\backtester.py',
        'Indicators': 'C:\\Users\\nyaga\\Documents\\AlgoAgent\\multi_agent\\strategies\\aapl_momentum_trader\\indicators.py'
    }
    
    file_status = {}
    
    for name, filepath in files_to_check.items():
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print_status(name, True, f"Size: {size:,} bytes")
            file_status[name] = True
        else:
            print_status(name, False, "File not found")
            file_status[name] = False
    
    return file_status

def check_mt5_availability():
    """Check if MetaTrader 5 is available"""
    print_header("METATRADER 5 STATUS")
    
    # Check if MT5 terminal is installed
    mt5_paths = [
        "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
        "C:\\Program Files (x86)\\MetaTrader 5\\terminal64.exe"
    ]
    
    mt5_found = False
    for path in mt5_paths:
        if os.path.exists(path):
            print_status("MT5 Terminal", True, f"Found at {path}")
            mt5_found = True
            break
    
    if not mt5_found:
        print_status("MT5 Terminal", False, "Not found in standard locations")
    
    # Try to import and test MT5 connection
    try:
        import MetaTrader5 as mt5
        print_status("MT5 Python SDK", True, "Import successful")
        
        # Try to initialize
        if mt5.initialize():
            print_status("MT5 Connection Test", True, "Connection successful")
            
            # Get terminal info
            terminal_info = mt5.terminal_info()
            if terminal_info:
                print_status("Terminal Info", True, f"Build: {terminal_info.build}")
            
            mt5.shutdown()
        else:
            print_status("MT5 Connection Test", False, "Connection failed - MT5 not running")
            
    except ImportError:
        print_status("MT5 Python SDK", False, "Package not installed")
    except Exception as e:
        print_status("MT5 Connection Test", False, f"Error: {str(e)}")
    
    return mt5_found

def test_framework_import():
    """Test importing our trading framework"""
    print_header("FRAMEWORK IMPORT TEST")
    
    try:
        # Try to import the framework
        sys.path.append('C:\\Users\\nyaga')
        
        # Test importing without running
        with open('C:\\Users\\nyaga\\mt5_trading_framework.py', 'r') as f:
            content = f.read()
            if 'class MT5TradingFramework' in content:
                print_status("Framework Class", True, "MT5TradingFramework found")
            else:
                print_status("Framework Class", False, "Class not found")
                
        if 'def __init__' in content:
            print_status("Framework Methods", True, "Constructor found")
        
        return True
        
    except Exception as e:
        print_status("Framework Import", False, f"Error: {str(e)}")
        return False

def generate_installation_commands():
    """Generate installation commands for missing packages"""
    print_header("INSTALLATION COMMANDS")
    
    print("If packages are missing, run these commands:")
    print()
    print("# Install MT5 and dependencies")
    print("pip install MetaTrader5")
    print("pip install pandas numpy matplotlib")
    print()
    print("# Alternative: Install all at once")
    print("pip install MetaTrader5 pandas numpy matplotlib")
    print()
    print("# If you have connection issues:")
    print("pip install --user MetaTrader5 pandas numpy matplotlib")

def check_agent_configuration():
    """Check if OpenCode agents are configured"""
    print_header("OPENCODE AGENT STATUS")
    
    agent_files = {
        'Trading Strategy Analyst': 'C:\\Users\\nyaga\\.config\\opencode\\agents\\trading-strategy-analyst.json',
        'Algorithmic Trading Dev': 'C:\\Users\\nyaga\\.config\\opencode\\agents\\algorithmic-trading-dev-agent.json',
        'OpenCode Config': 'C:\\Users\\nyaga\\.config\\opencode\\opencode.json'
    }
    
    for name, filepath in agent_files.items():
        if os.path.exists(filepath):
            print_status(name, True, "Configured")
        else:
            print_status(name, False, "Not found")

def main():
    """Main diagnostic function"""
    print(f"Trading System Status Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all checks
    env_ok = check_python_environment()
    packages = check_required_packages()
    files = check_system_files()
    mt5_ok = check_mt5_availability()
    framework_ok = test_framework_import()
    check_agent_configuration()
    
    # Generate commands if needed
    if not all(packages.values()):
        generate_installation_commands()
    
    # Summary
    print_header("SYSTEM SUMMARY")
    
    total_checks = len(packages) + len(files) + 3  # 3 for env, mt5, framework
    passed_checks = sum(packages.values()) + sum(files.values()) + sum([env_ok, mt5_ok, framework_ok])
    
    print(f"System Readiness: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print("\nSYSTEM FULLY OPERATIONAL!")
        print("Ready for live trading deployment")
    elif passed_checks > total_checks * 0.7:
        print("\nSYSTEM MOSTLY READY")
        print("Minor issues to resolve before trading")
    else:
        print("\nSYSTEM NEEDS SETUP")
        print("Follow installation commands above")
    
    print(f"\nNext Steps:")
    if not all(packages.values()):
        print("1. Install missing Python packages")
    if not mt5_ok:
        print("2. Install and configure MetaTrader 5")
    if all(packages.values()) and mt5_ok:
        print("1. Test live trading with demo account")
        print("2. Configure TradingView integration")
        print("3. Deploy AAPL momentum strategy")

if __name__ == "__main__":
    main()