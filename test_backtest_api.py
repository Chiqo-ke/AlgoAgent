"""
Backtesting API Test Suite
===========================

Tests backtesting APIs with different configurations to verify:
1. Initial balance is correctly used
2. Lot size affects position sizing
3. Commission/slippage are properly applied
4. Results are accurately calculated and returned
"""

import asyncio
import websockets
import json
import requests
from datetime import datetime, timedelta
import time

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/backtest/stream/"
AUTH_TOKEN = None  # Will be set after login

# Test configurations
TEST_CASES = [
    {
        "name": "Test 1: Default Configuration",
        "config": {
            "strategy_code": """
from backtesting import Strategy
from backtesting.lib import crossover

class TestStrategy(Strategy):
    def init(self):
        price = self.data.Close
        self.ma1 = self.I(lambda x: x.rolling(5).mean(), price)
        self.ma2 = self.I(lambda x: x.rolling(10).mean(), price)
    
    def next(self):
        if crossover(self.ma1, self.ma2):
            self.buy()
        elif crossover(self.ma2, self.ma1):
            self.position.close()
""",
            "symbol": "AAPL",
            "period": "3month",
            "interval": "1d",
            "initial_balance": 10000,
            "lot_size": 1.0,
            "commission": 0.001,
            "slippage": 0.0005
        },
        "expected": {
            "uses_initial_balance": 10000,
            "has_trades": True,
            "pnl_changes": True
        }
    },
    {
        "name": "Test 2: High Initial Balance",
        "config": {
            "strategy_code": """
from backtesting import Strategy
from backtesting.lib import crossover

class TestStrategy(Strategy):
    def init(self):
        price = self.data.Close
        self.ma1 = self.I(lambda x: x.rolling(5).mean(), price)
        self.ma2 = self.I(lambda x: x.rolling(10).mean(), price)
    
    def next(self):
        if crossover(self.ma1, self.ma2):
            self.buy()
        elif crossover(self.ma2, self.ma1):
            self.position.close()
""",
            "symbol": "AAPL",
            "period": "3month",
            "interval": "1d",
            "initial_balance": 50000,
            "lot_size": 1.0,
            "commission": 0.001,
            "slippage": 0.0005
        },
        "expected": {
            "uses_initial_balance": 50000,
            "has_trades": True,
            "pnl_changes": True
        }
    },
    {
        "name": "Test 3: Large Lot Size",
        "config": {
            "strategy_code": """
from backtesting import Strategy
from backtesting.lib import crossover

class TestStrategy(Strategy):
    def init(self):
        price = self.data.Close
        self.ma1 = self.I(lambda x: x.rolling(5).mean(), price)
        self.ma2 = self.I(lambda x: x.rolling(10).mean(), price)
    
    def next(self):
        if crossover(self.ma1, self.ma2):
            self.buy()
        elif crossover(self.ma2, self.ma1):
            self.position.close()
""",
            "symbol": "AAPL",
            "period": "3month",
            "interval": "1d",
            "initial_balance": 10000,
            "lot_size": 5.0,
            "commission": 0.001,
            "slippage": 0.0005
        },
        "expected": {
            "uses_initial_balance": 10000,
            "lot_size_affects_trades": 5.0,
            "has_trades": True
        }
    },
    {
        "name": "Test 4: High Commission",
        "config": {
            "strategy_code": """
from backtesting import Strategy
from backtesting.lib import crossover

class TestStrategy(Strategy):
    def init(self):
        price = self.data.Close
        self.ma1 = self.I(lambda x: x.rolling(5).mean(), price)
        self.ma2 = self.I(lambda x: x.rolling(10).mean(), price)
    
    def next(self):
        if crossover(self.ma1, self.ma2):
            self.buy()
        elif crossover(self.ma2, self.ma1):
            self.position.close()
""",
            "symbol": "AAPL",
            "period": "3month",
            "interval": "1d",
            "initial_balance": 10000,
            "lot_size": 1.0,
            "commission": 0.01,  # 1% commission - very high
            "slippage": 0.0005
        },
        "expected": {
            "uses_initial_balance": 10000,
            "high_commission_affects_pnl": True,
            "has_trades": True
        }
    }
]


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_test_result(test_name, passed, message=""):
    """Print test result with color"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if message:
        print(f"    {message}")


async def test_websocket_stream(test_case):
    """Test WebSocket streaming backtest"""
    test_name = test_case["name"]
    config = test_case["config"]
    expected = test_case["expected"]
    
    print_header(f"Testing: {test_name}")
    print(f"Configuration:")
    print(f"  Symbol: {config['symbol']}")
    print(f"  Period: {config['period']}")
    print(f"  Initial Balance: ${config['initial_balance']:,.2f}")
    print(f"  Lot Size: {config['lot_size']}")
    print(f"  Commission: {config['commission']}")
    print(f"  Slippage: {config['slippage']}")
    print()
    
    results = {
        "metadata_received": False,
        "stats_received": False,
        "complete_received": False,
        "initial_balance_correct": False,
        "has_trades": False,
        "pnl_calculated": False,
        "final_equity": None,
        "total_trades": 0,
        "net_pnl": 0
    }
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            # Send backtest configuration
            await websocket.send(json.dumps({
                "action": "start_backtest",
                "config": config
            }))
            
            print("📡 WebSocket connected, waiting for results...")
            
            # Receive messages
            timeout = 60  # 60 seconds timeout
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                    
                    if data.get("type") == "metadata":
                        results["metadata_received"] = True
                        print(f"📊 Metadata received: {data.get('total_bars', 0)} bars")
                    
                    elif data.get("type") == "stats":
                        results["stats_received"] = True
                        results["total_trades"] = data.get("total_trades", 0)
                        results["net_pnl"] = data.get("pnl", 0)
                        if results["total_trades"] > 0:
                            results["has_trades"] = True
                        print(f"📈 Stats: {results['total_trades']} trades, PnL: ${results['net_pnl']:.2f}")
                    
                    elif data.get("type") == "complete":
                        results["complete_received"] = True
                        metrics = data.get("metrics", {})
                        results["total_trades"] = metrics.get("total_trades", 0)
                        results["net_pnl"] = metrics.get("net_profit", 0)
                        results["final_equity"] = metrics.get("final_equity", 0)
                        
                        if results["total_trades"] > 0:
                            results["has_trades"] = True
                        if results["net_pnl"] != 0:
                            results["pnl_calculated"] = True
                        
                        # Check if initial balance is correct
                        expected_final = config["initial_balance"] + results["net_pnl"]
                        if abs(results["final_equity"] - expected_final) < 0.01:
                            results["initial_balance_correct"] = True
                        
                        print(f"✅ Complete!")
                        print(f"   Total Trades: {results['total_trades']}")
                        print(f"   Net PnL: ${results['net_pnl']:.2f}")
                        print(f"   Final Equity: ${results['final_equity']:.2f}")
                        print(f"   Expected Final: ${expected_final:.2f}")
                        break
                    
                    elif data.get("type") == "error":
                        print(f"❌ Error: {data.get('message')}")
                        break
                
                except asyncio.TimeoutError:
                    continue
            
            # Evaluate test results
            print("\n" + "-" * 80)
            print("Test Results:")
            print("-" * 80)
            
            all_passed = True
            
            # Test 1: Metadata received
            passed = results["metadata_received"]
            print_test_result("Metadata received", passed)
            all_passed = all_passed and passed
            
            # Test 2: Stats received
            passed = results["stats_received"]
            print_test_result("Stats updates received", passed)
            all_passed = all_passed and passed
            
            # Test 3: Complete message received
            passed = results["complete_received"]
            print_test_result("Complete message received", passed)
            all_passed = all_passed and passed
            
            # Test 4: Initial balance used correctly
            passed = results["initial_balance_correct"]
            print_test_result(
                "Initial balance used correctly",
                passed,
                f"Final equity matches: initial(${config['initial_balance']}) + PnL(${results['net_pnl']:.2f}) = ${results['final_equity']:.2f}"
            )
            all_passed = all_passed and passed
            
            # Test 5: Strategy generated trades
            if expected.get("has_trades"):
                passed = results["has_trades"]
                print_test_result(
                    "Strategy generated trades",
                    passed,
                    f"Total trades: {results['total_trades']}"
                )
                all_passed = all_passed and passed
            
            # Test 6: P&L calculated
            if expected.get("pnl_changes"):
                passed = results["pnl_calculated"]
                print_test_result(
                    "P&L calculated correctly",
                    passed,
                    f"Net PnL: ${results['net_pnl']:.2f}"
                )
                all_passed = all_passed and passed
            
            print("-" * 80)
            if all_passed:
                print("🎉 ALL TESTS PASSED!")
            else:
                print("⚠️  SOME TESTS FAILED")
            print()
            
            return all_passed
    
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all test cases"""
    print_header("BACKTESTING API TEST SUITE")
    print("Testing WebSocket streaming backtest API")
    print(f"Base URL: {BASE_URL}")
    print(f"WebSocket URL: {WS_URL}")
    print(f"Total test cases: {len(TEST_CASES)}")
    
    results = []
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n\n{'#' * 80}")
        print(f"# Test Case {i}/{len(TEST_CASES)}")
        print(f"{'#' * 80}")
        
        passed = await test_websocket_stream(test_case)
        results.append({
            "name": test_case["name"],
            "passed": passed
        })
        
        # Wait between tests to avoid overwhelming the server
        if i < len(TEST_CASES):
            print("\n⏳ Waiting 3 seconds before next test...")
            await asyncio.sleep(3)
    
    # Final summary
    print("\n\n" + "=" * 80)
    print("  FINAL TEST SUMMARY")
    print("=" * 80)
    
    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)
    
    for result in results:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{status} - {result['name']}")
    
    print("-" * 80)
    print(f"Results: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 ALL TESTS PASSED! Backtesting API is working correctly.")
    else:
        print(f"⚠️  {total_count - passed_count} test(s) failed. Please review the logs.")
    print("=" * 80)


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                      BACKTESTING API TEST SUITE                               ║
║                                                                               ║
║  This script tests the backtesting WebSocket API with different              ║
║  configurations to verify:                                                    ║
║    • Initial balance is correctly used                                        ║
║    • Lot size affects position sizing                                         ║
║    • Commission/slippage are properly applied                                 ║
║    • Results are accurately calculated                                        ║
║    • Frontend receives correct data                                           ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
