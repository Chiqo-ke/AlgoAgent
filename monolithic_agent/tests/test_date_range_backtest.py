"""
Test Custom Date Range Backtesting Implementation
==================================================

This script tests the new custom date range functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_data_loader():
    """Test that fetch_market_data_by_date_range works correctly"""
    print("\n" + "="*70)
    print("TEST 1: Data Loader - fetch_market_data_by_date_range")
    print("="*70)
    
    try:
        from Backtest.data_loader import fetch_market_data_by_date_range
        
        # Test fetching data for a specific date range
        print("\nFetching AAPL data from 2024-01-01 to 2024-12-31...")
        df = fetch_market_data_by_date_range(
            ticker='AAPL',
            start_date='2024-01-01',
            end_date='2024-12-31',
            interval='1d'
        )
        
        print(f"✓ Successfully fetched {len(df)} rows")
        print(f"✓ Date range: {df.index[0].date()} to {df.index[-1].date()}")
        print(f"✓ Columns: {list(df.columns)}")
        print("\nFirst 3 rows:")
        print(df.head(3))
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bot_executor_signature():
    """Test that BotExecutor accepts start_date and end_date parameters"""
    print("\n" + "="*70)
    print("TEST 2: BotExecutor - Method Signature Update")
    print("="*70)
    
    try:
        from Backtest.bot_executor import BotExecutor
        import inspect
        
        # Check if execute_bot has the new parameters
        sig = inspect.signature(BotExecutor.execute_bot)
        params = list(sig.parameters.keys())
        
        print(f"\nBotExecutor.execute_bot parameters: {params}")
        
        has_start_date = 'start_date' in params
        has_end_date = 'end_date' in params
        
        if has_start_date and has_end_date:
            print("✓ start_date parameter found")
            print("✓ end_date parameter found")
            return True
        else:
            print(f"✗ FAILED: Missing parameters")
            print(f"  start_date present: {has_start_date}")
            print(f"  end_date present: {has_end_date}")
            return False
            
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_integration():
    """Test that the API view is updated"""
    print("\n" + "="*70)
    print("TEST 3: API Integration - views.py execute method")
    print("="*70)
    
    try:
        # Read the views.py file and check for date parameter extraction
        views_path = Path(__file__).parent / 'strategy_api' / 'views.py'
        
        with open(views_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the execute method extracts start_date and end_date
        has_start_extraction = "start_date = request.data.get('start_date')" in content
        has_end_extraction = "end_date = request.data.get('end_date')" in content
        has_executor_call = "start_date=start_date" in content and "end_date=end_date" in content
        
        if has_start_extraction and has_end_extraction and has_executor_call:
            print("✓ API extracts start_date from request")
            print("✓ API extracts end_date from request")
            print("✓ API passes dates to BotExecutor")
            return True
        else:
            print(f"✗ FAILED: API integration incomplete")
            print(f"  Extracts start_date: {has_start_extraction}")
            print(f"  Extracts end_date: {has_end_extraction}")
            print(f"  Passes to executor: {has_executor_call}")
            return False
            
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("CUSTOM DATE RANGE BACKTESTING - IMPLEMENTATION TESTS")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Data Loader", test_data_loader()))
    results.append(("BotExecutor Signature", test_bot_executor_signature()))
    results.append(("API Integration", test_api_integration()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:.<40} {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED - Custom date range backtesting is ready!")
        print("\nYou can now use the API with:")
        print("  POST /api/strategies/strategies/{id}/execute/")
        print("  Body: {")
        print('    "test_symbol": "AAPL",')
        print('    "start_date": "2024-01-01",')
        print('    "end_date": "2024-12-31"')
        print("  }")
    else:
        print("✗ SOME TESTS FAILED - Please review the errors above")
    print("="*70)
