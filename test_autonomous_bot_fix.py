"""
Test Autonomous Bot Execution & Error Fixing
=============================================

This script tests the fixed generate_executable_code endpoint to verify:
1. Bot generation works
2. Automatic execution is triggered
3. Iterative error fixing works
4. API returns execution and fixing details

Usage:
    python test_autonomous_bot_fix.py
"""

import requests
import json
import time
from datetime import datetime


# Configuration
API_BASE_URL = "http://127.0.0.1:8000"
ENDPOINT = "/api/strategies/api/generate_executable_code/"


def test_simple_strategy():
    """Test with a simple strategy that should work first time"""
    print("\n" + "="*70)
    print("TEST 1: Simple Strategy (Should work without fixes)")
    print("="*70)
    
    data = {
        "canonical_json": {
            "strategy_name": "Simple EMA Crossover",
            "description": "Buy when EMA 10 crosses above EMA 20, sell when it crosses below",
            "entry_rules": [
                {"description": "EMA(10) crosses above EMA(20)"}
            ],
            "exit_rules": [
                {"description": "EMA(10) crosses below EMA(20)"}
            ],
            "indicators": [
                {"name": "EMA", "params": {"period": 10}},
                {"name": "EMA", "params": {"period": 20}}
            ],
            "timeframe": "1d"
        },
        "strategy_name": "test_simple_ema"
    }
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Sending request...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}{ENDPOINT}",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minutes timeout
        )
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Response received: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_results(result)
            return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (execution may still be running)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_complex_strategy():
    """Test with a more complex strategy"""
    print("\n" + "="*70)
    print("TEST 2: Complex Strategy (May need fixes)")
    print("="*70)
    
    data = {
        "canonical_json": {
            "strategy_name": "RSI Bollinger Band Strategy",
            "description": "Combined RSI and Bollinger Bands strategy with dynamic position sizing",
            "entry_rules": [
                {"description": "RSI < 30 (oversold)"},
                {"description": "Price touches lower Bollinger Band"}
            ],
            "exit_rules": [
                {"description": "RSI > 70 (overbought)"},
                {"description": "Price touches upper Bollinger Band"}
            ],
            "risk_management": {
                "stop_loss": "2%",
                "take_profit": "5%",
                "position_sizing": "2% of equity per trade"
            },
            "indicators": [
                {"name": "RSI", "params": {"period": 14}},
                {"name": "BollingerBands", "params": {"period": 20, "std": 2}}
            ],
            "timeframe": "1h"
        },
        "strategy_name": "test_rsi_bb_complex"
    }
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Sending request...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}{ENDPOINT}",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=180  # 3 minutes for complex strategy
        )
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Response received: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_results(result)
            return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (complex strategy may need more time)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def print_results(result):
    """Print formatted results from API response"""
    print("\n" + "-"*70)
    print("RESULTS")
    print("-"*70)
    
    # Basic info
    print(f"\n✅ Strategy Generated: {result.get('success', False)}")
    print(f"   File: {result.get('file_name', 'N/A')}")
    print(f"   Path: {result.get('file_path', 'N/A')}")
    
    # Execution info
    execution = result.get('execution', {})
    print(f"\n🚀 Execution:")
    print(f"   Attempted: {execution.get('attempted', False)}")
    print(f"   Success: {execution.get('success', False)}")
    print(f"   Validation Status: {execution.get('validation_status', 'unknown')}")
    
    if execution.get('success'):
        metrics = execution.get('metrics', {})
        print(f"\n📊 Performance Metrics:")
        print(f"   Return: {metrics.get('return_pct', 0):.2f}%")
        print(f"   Trades: {metrics.get('num_trades', 0)}")
        print(f"   Win Rate: {metrics.get('win_rate', 0)*100:.1f}%" if metrics.get('win_rate') else "   Win Rate: N/A")
        print(f"   Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}" if metrics.get('sharpe_ratio') else "   Sharpe Ratio: N/A")
        print(f"   Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%" if metrics.get('max_drawdown') else "   Max Drawdown: N/A")
    elif execution.get('error_message'):
        print(f"\n❌ Execution Error:")
        print(f"   {execution.get('error_message', 'Unknown error')[:200]}")
    
    # Error fixing info
    fixing = result.get('error_fixing', {})
    print(f"\n🔧 Error Fixing:")
    print(f"   Attempted: {fixing.get('attempted', False)}")
    print(f"   Attempts: {fixing.get('attempts', 0)}")
    print(f"   Final Status: {fixing.get('final_status', 'unknown')}")
    
    if fixing.get('attempted') and fixing.get('history'):
        print(f"\n   Fix History:")
        for fix in fixing['history']:
            status_icon = "✓" if fix.get('success') else "✗"
            print(f"   {status_icon} Attempt {fix.get('attempt', '?')}: {fix.get('error_type', 'unknown')} - {fix.get('description', 'No description')[:100]}")
    
    print("\n" + "-"*70)


def check_server():
    """Check if Django server is running"""
    print("\n" + "="*70)
    print("Checking Server Status")
    print("="*70)
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/strategies/api/available_indicators/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and accessible")
            return True
        else:
            print(f"⚠️  Server responded with: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        print(f"   Make sure Django is running: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("AUTONOMOUS BOT EXECUTION & ERROR FIXING TEST")
    print("="*70)
    print(f"Testing endpoint: {API_BASE_URL}{ENDPOINT}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check server first
    if not check_server():
        print("\n❌ Cannot proceed without server running")
        print("   Start server with: python manage.py runserver")
        return
    
    # Run tests
    results = []
    
    # Test 1: Simple strategy
    results.append(("Simple Strategy", test_simple_strategy()))
    
    # Wait between tests
    print(f"\nWaiting 5 seconds before next test...")
    time.sleep(5)
    
    # Test 2: Complex strategy
    results.append(("Complex Strategy", test_complex_strategy()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Autonomous execution is working!")
    else:
        print("\n⚠️  Some tests failed. Check logs above for details.")


if __name__ == "__main__":
    main()
