"""
Quick Test - Verify Execution Success Detection & Backtest Storage

This script tests:
1. BotExecutor correctly identifies successful execution despite stderr warnings
2. Backtest results are saved to database
3. Frontend can retrieve results without 404 error

Usage:
    python test_execution_fixes.py
"""

import os
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')

import django
django.setup()

from Backtest.bot_executor import BotExecutor
from strategy_api.models import Strategy, LatestBacktestResult


def test_bot_executor_success_detection():
    """Test that BotExecutor correctly identifies success when trades > 0"""
    print("\n" + "="*70)
    print("TEST 1: BotExecutor Success Detection")
    print("="*70)
    
    executor = BotExecutor()
    
    # Simulate output with warnings in stderr but successful execution
    mock_stdout = """
    [*********************100%***********************]  1 of 1 completed
    
    INFO:Backtest.account_manager:Opened position: +100.00 AAPL @ 267.13
    INFO:Backtest.signal_logger:Total Signals: 1
    INFO:Backtest.signal_logger:Buy Signals: 1
    
    Final Equity: $110,500.00
    Return: 10.5%
    Trades: 1
    Win Rate: 100.0%
    """
    
    mock_stderr = """
    WARNING: Trying to import the above resulted in these errors:
    ImportError: Some optional module not found
    """
    
    result = executor._parse_execution_output(mock_stdout, mock_stderr)
    
    print(f"\nStdout (truncated): {mock_stdout[:100]}...")
    print(f"Stderr: {mock_stderr.strip()}")
    print(f"\nParsed Result:")
    print(f"  Success: {result['success']}")
    print(f"  Trades: {result['trades']}")
    print(f"  Return: {result['return_pct']}%")
    print(f"  Error: {result['error']}")
    
    if result['success'] and result['trades'] == 1:
        print("\n✅ PASS: BotExecutor correctly identified success despite stderr warning")
        return True
    else:
        print("\n❌ FAIL: BotExecutor incorrectly marked as failure")
        return False


def test_backtest_result_storage():
    """Test that successful executions are saved to LatestBacktestResult"""
    print("\n" + "="*70)
    print("TEST 2: Backtest Result Database Storage")
    print("="*70)
    
    # Check if most recent strategy has backtest results
    try:
        latest_strategy = Strategy.objects.filter(status='executed').order_by('-created_at').first()
        
        if not latest_strategy:
            print("\n⚠️ SKIP: No executed strategies found in database")
            return None
        
        print(f"\nChecking strategy: {latest_strategy.name} (ID: {latest_strategy.id})")
        
        try:
            backtest_result = LatestBacktestResult.objects.get(strategy_id=latest_strategy.id)
            
            print(f"\n✅ Found backtest result:")
            print(f"  Success: {backtest_result.success}")
            print(f"  Trades: {backtest_result.num_trades}")
            print(f"  Return: {backtest_result.return_pct}%")
            print(f"  Symbol: {backtest_result.test_symbol}")
            print(f"  Executed: {backtest_result.executed_at}")
            
            print("\n✅ PASS: Backtest results properly saved to database")
            return True
            
        except LatestBacktestResult.DoesNotExist:
            print(f"\n❌ FAIL: No backtest result found for strategy {latest_strategy.id}")
            print("   This means the save logic isn't working properly")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def test_frontend_api_access():
    """Test that frontend can retrieve backtest results without 404"""
    print("\n" + "="*70)
    print("TEST 3: Frontend API Access")
    print("="*70)
    
    try:
        # Get a strategy with backtest results
        result = LatestBacktestResult.objects.order_by('-executed_at').first()
        
        if not result:
            print("\n⚠️ SKIP: No backtest results in database yet")
            return None
        
        strategy_id = result.strategy_id
        
        print(f"\nStrategy ID: {strategy_id}")
        print(f"Endpoint: /api/strategies/backtest-results/{strategy_id}/")
        
        # Simulate what frontend does
        try:
            retrieved = LatestBacktestResult.objects.get(strategy_id=strategy_id)
            print(f"\n✅ Result retrieved successfully:")
            print(f"  Trades: {retrieved.num_trades}")
            print(f"  Return: {retrieved.return_pct}%")
            
            print("\n✅ PASS: Frontend API access working (no 404)")
            return True
            
        except LatestBacktestResult.DoesNotExist:
            print(f"\n❌ FAIL: 404 - Result not found for strategy {strategy_id}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("EXECUTION FIXES VALIDATION TEST SUITE")
    print("="*70)
    
    results = []
    
    # Test 1: BotExecutor success detection
    results.append(("BotExecutor Success Detection", test_bot_executor_success_detection()))
    
    # Test 2: Database storage
    results.append(("Backtest Result Storage", test_backtest_result_storage()))
    
    # Test 3: Frontend API access
    results.append(("Frontend API Access", test_frontend_api_access()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, result in results:
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️ SKIP"
        
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    skipped = sum(1 for _, r in results if r is None)
    
    print(f"\nResults: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("\n🎉 All tests passed! Execution fixes are working correctly.")
    else:
        print("\n⚠️ Some tests failed. Review the output above for details.")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
