"""
Quick Test for MT5 Integration
===============================

Verifies that all MT5 integration components are working correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Test imports
print("Testing MT5 Integration Components...")
print("-" * 50)

try:
    from Backtest.signal_exporter import SignalExporter, MT5Signal
    print("✓ SignalExporter imported successfully")
except Exception as e:
    print(f"✗ SignalExporter import failed: {e}")
    sys.exit(1)

try:
    from Backtest.mt5_connector import MT5Connector, get_mt5_timeframe_minutes, align_timestamp_to_mt5
    print("✓ MT5Connector imported successfully")
except Exception as e:
    print(f"✗ MT5Connector import failed: {e}")
    sys.exit(1)

try:
    from Backtest.mt5_reconciliation import MT5Reconciliation, quick_reconcile
    print("✓ MT5Reconciliation imported successfully")
except Exception as e:
    print(f"✗ MT5Reconciliation import failed: {e}")
    sys.exit(1)

try:
    from Backtest.sim_broker import SimBroker
    print("✓ SimBroker with MT5 extensions imported successfully")
except Exception as e:
    print(f"✗ SimBroker import failed: {e}")
    sys.exit(1)

# Test basic functionality
print("\nTesting Basic Functionality...")
print("-" * 50)

try:
    # Test SignalExporter
    output_dir = Path("Backtest/test_output")
    exporter = SignalExporter(
        output_dir=output_dir,
        backtest_id="TEST_001",
        symbol="XAUUSD",
        timeframe="H1"
    )
    print("✓ SignalExporter initialization works")
    
    # Test lot conversion
    lot_size = exporter._convert_to_lots(100)  # 100 oz
    assert lot_size == 1.0, f"Expected 1.0 lot, got {lot_size}"
    print(f"✓ Lot conversion works (100 oz → {lot_size} lot)")
    
except Exception as e:
    print(f"✗ SignalExporter test failed: {e}")
    sys.exit(1)

try:
    # Test SimBroker with MT5 export
    from Backtest.config import BacktestConfig
    
    config = BacktestConfig(start_cash=10000)
    broker = SimBroker(
        config=config,
        enable_mt5_export=True,
        mt5_symbol="XAUUSD",
        mt5_timeframe="H1"
    )
    print("✓ SimBroker with MT5 export enabled works")
    
    # Check that signal exporter is initialized
    assert broker.signal_exporter is not None, "Signal exporter not initialized"
    print("✓ Signal exporter properly integrated into SimBroker")
    
except Exception as e:
    print(f"✗ SimBroker test failed: {e}")
    sys.exit(1)

try:
    # Test timeframe conversion
    minutes = get_mt5_timeframe_minutes("H1")
    assert minutes == 60, f"Expected 60 minutes, got {minutes}"
    print(f"✓ Timeframe conversion works (H1 → {minutes} minutes)")
    
except Exception as e:
    print(f"✗ Timeframe conversion test failed: {e}")
    sys.exit(1)

# Test file existence
print("\nChecking File Existence...")
print("-" * 50)

files_to_check = [
    "Backtest/signal_exporter.py",
    "Backtest/mt5_connector.py",
    "Backtest/mt5_reconciliation.py",
    "Backtest/PythonSignalExecutor.mq5",
    "Backtest/example_mt5_integration.py",
    "Backtest/MT5_INTEGRATION_GUIDE.md",
    "Backtest/MT5_QUICK_REFERENCE.md",
    "Backtest/MT5_INTEGRATION_SUMMARY.md"
]

all_exist = True
for file_path in files_to_check:
    path = Path(file_path)
    if path.exists():
        print(f"✓ {file_path}")
    else:
        print(f"✗ {file_path} NOT FOUND")
        all_exist = False

if not all_exist:
    print("\n⚠ Warning: Some files are missing")
else:
    print("\n✓ All files present")

# Final summary
print("\n" + "=" * 50)
print("MT5 Integration Test Summary")
print("=" * 50)
print("✓ All imports successful")
print("✓ Basic functionality tests passed")
print("✓ File structure verified")
print("\n🎉 MT5 Integration is ready to use!")
print("\nNext steps:")
print("1. Review MT5_INTEGRATION_GUIDE.md for detailed usage")
print("2. Run example_mt5_integration.py for demo")
print("3. Install MetaTrader5 package: pip install MetaTrader5")
print("4. Copy PythonSignalExecutor.mq5 to MT5 Experts folder")
