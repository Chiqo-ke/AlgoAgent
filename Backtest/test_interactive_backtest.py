"""
Test Interactive Backtest Components
====================================

Tests the interactive backtest runner functions without user input.
Uses mock inputs to verify all components work correctly.

Version: 1.0.0
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
PARENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PARENT_DIR))

from Backtest.interactive_backtest_runner import (
    validate_date,
    fetch_data_for_backtest,
    convert_to_broker_format,
    get_realistic_config
)
from Data.data_fetcher import DataFetcher


def test_validate_date():
    """Test date validation function."""
    print("\n" + "=" * 70)
    print("TEST: Date Validation")
    print("=" * 70)
    
    test_cases = [
        ("2024-01-01", True, "Valid date"),
        ("2023-12-31", True, "Valid date"),
        ("2024/01/01", False, "Invalid format (slashes)"),
        ("01-01-2024", False, "Invalid format (wrong order)"),
        ("2024-13-01", False, "Invalid month"),
        ("2024-01-32", False, "Invalid day"),
        ("not-a-date", False, "Invalid format"),
    ]
    
    passed = 0
    failed = 0
    
    for date_str, expected_valid, description in test_cases:
        is_valid, date_obj = validate_date(date_str)
        
        if is_valid == expected_valid:
            print(f"✓ PASS: {description} - '{date_str}'")
            passed += 1
        else:
            print(f"✗ FAIL: {description} - '{date_str}' (expected {expected_valid}, got {is_valid})")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_data_fetcher():
    """Test DataFetcher integration."""
    print("\n" + "=" * 70)
    print("TEST: Data Fetcher Integration")
    print("=" * 70)
    
    try:
        fetcher = DataFetcher()
        print("✓ DataFetcher instantiated")
        
        # Test with recent data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        print(f"\nFetching AAPL data from {start_str} to {end_str}...")
        df = fetcher.fetch_data_by_date_range(
            ticker="AAPL",
            start_date=start_str,
            end_date=end_str,
            interval="1d"
        )
        
        if df.empty:
            print("✗ FAIL: No data returned")
            return False
        
        print(f"✓ Data fetched: {len(df)} rows")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Date range: {df.index[0]} to {df.index[-1]}")
        
        # Check for required columns
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required:
            if col not in df.columns:
                print(f"✗ FAIL: Missing required column: {col}")
                return False
        
        print(f"✓ All required columns present")
        return True
        
    except Exception as e:
        print(f"✗ FAIL: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fetch_for_backtest():
    """Test the fetch_data_for_backtest function."""
    print("\n" + "=" * 70)
    print("TEST: Fetch Data for Backtest")
    print("=" * 70)
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        print(f"\nTesting with MSFT from {start_str} to {end_str}...")
        df = fetch_data_for_backtest(
            symbol="MSFT",
            start_date=start_str,
            end_date=end_str,
            interval="1d"
        )
        
        if df.empty:
            print("✗ FAIL: No data returned")
            return False
        
        print(f"✓ Data processed successfully")
        print(f"  Rows: {len(df)}")
        print(f"  Date range: {df.index[0]} to {df.index[-1]}")
        
        # Verify data quality
        if df.isnull().any().any():
            print("✗ FAIL: Data contains NaN values")
            return False
        
        print("✓ No NaN values in data")
        
        # Verify datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            print("✗ FAIL: Index is not DatetimeIndex")
            return False
        
        print("✓ Proper DatetimeIndex")
        return True
        
    except Exception as e:
        print(f"✗ FAIL: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_convert_to_broker_format():
    """Test data format conversion."""
    print("\n" + "=" * 70)
    print("TEST: Convert to Broker Format")
    print("=" * 70)
    
    try:
        import pandas as pd
        
        # Create sample data
        dates = pd.date_range('2024-01-01', periods=5, freq='D')
        df = pd.DataFrame({
            'Open': [100, 101, 102, 103, 104],
            'High': [102, 103, 104, 105, 106],
            'Low': [99, 100, 101, 102, 103],
            'Close': [101, 102, 103, 104, 105],
            'Volume': [1000, 1100, 1200, 1300, 1400]
        }, index=dates)
        
        print("✓ Sample data created")
        
        # Convert to broker format
        broker_df = convert_to_broker_format(df, "AAPL")
        
        print(f"✓ Converted to broker format")
        print(f"  Rows: {len(broker_df)}")
        print(f"  Columns: {list(broker_df.columns)}")
        
        # Verify required columns
        required = ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']
        for col in required:
            if col not in broker_df.columns:
                print(f"✗ FAIL: Missing required column: {col}")
                return False
        
        print("✓ All required columns present")
        
        # Verify symbol
        if not (broker_df['symbol'] == 'AAPL').all():
            print("✗ FAIL: Symbol not correctly set")
            return False
        
        print("✓ Symbol correctly set")
        
        # Verify data matches
        if not (broker_df['open'].values == df['Open'].values).all():
            print("✗ FAIL: Open prices don't match")
            return False
        
        print("✓ Data values match original")
        return True
        
    except Exception as e:
        print(f"✗ FAIL: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Test configuration loading."""
    print("\n" + "=" * 70)
    print("TEST: Configuration Loading")
    print("=" * 70)
    
    try:
        config = get_realistic_config()
        print("✓ Config loaded")
        
        # Verify key attributes
        attributes = [
            'start_cash',
            'fee_flat',
            'fee_pct',
            'slippage_pct',
            'currency'
        ]
        
        for attr in attributes:
            if not hasattr(config, attr):
                print(f"✗ FAIL: Missing attribute: {attr}")
                return False
        
        print("✓ All required attributes present")
        print(f"  Start Cash: ${config.start_cash:,.2f}")
        print(f"  Fee: ${config.fee_flat} + {config.fee_pct*100:.3f}%")
        print(f"  Slippage: {config.slippage_pct*100:.4f}%")
        
        return True
        
    except Exception as e:
        print(f"✗ FAIL: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_broker_initialization():
    """Test SimBroker initialization."""
    print("\n" + "=" * 70)
    print("TEST: SimBroker Initialization")
    print("=" * 70)
    
    try:
        from Backtest.sim_broker import SimBroker
        
        config = get_realistic_config()
        broker = SimBroker(config)
        
        print(f"✓ SimBroker initialized (API v{broker.API_VERSION})")
        
        # Check basic functionality
        equity = broker.get_equity()
        print(f"✓ Initial equity: ${equity:,.2f}")
        
        positions = broker.get_positions()
        print(f"✓ Initial positions: {len(positions)}")
        
        return True
        
    except Exception as e:
        print(f"✗ FAIL: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all component tests."""
    print("\n" + "=" * 70)
    print("INTERACTIVE BACKTEST COMPONENT TESTS")
    print("=" * 70)
    print("Testing all components without user interaction...\n")
    
    tests = [
        ("Date Validation", test_validate_date),
        ("Data Fetcher", test_data_fetcher),
        ("Fetch for Backtest", test_fetch_for_backtest),
        ("Broker Format Conversion", test_convert_to_broker_format),
        ("Configuration", test_config),
        ("Broker Initialization", test_broker_initialization),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            passed = test_func()
            results[name] = passed
        except Exception as e:
            print(f"\n✗ TEST CRASHED: {name}")
            print(f"   Error: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed_count = sum(1 for v in results.values() if v)
    failed_count = len(results) - passed_count
    
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed_count}/{len(results)} tests passed")
    
    if failed_count == 0:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠️  {failed_count} test(s) failed")
        return False


if __name__ == "__main__":
    import pandas as pd  # Import here for convert test
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
