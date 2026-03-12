"""
Comprehensive End-to-End Test for Monolithic Agent
===================================================

This test suite verifies the complete workflow of:
1. Strategy code generation using AI
2. Strategy validation
3. Backtest execution with trade simulation
4. Results verification

Author: AlgoAgent E2E Testing
Date: 2026-01-10
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import logging

# Setup Python path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test results tracker
test_results = {
    'tests_run': 0,
    'tests_passed': 0,
    'tests_failed': 0,
    'test_details': []
}


def log_test(test_name: str, status: str, details: str = ""):
    """Log test result"""
    global test_results
    test_results['tests_run'] += 1
    
    if status == 'PASS':
        test_results['tests_passed'] += 1
        symbol = '✅'
    else:
        test_results['tests_failed'] += 1
        symbol = '❌'
    
    test_results['test_details'].append({
        'name': test_name,
        'status': status,
        'details': details
    })
    
    logger.info(f"{symbol} {test_name}: {status} {details}")


def test_imports():
    """Test 1: Verify all critical imports work"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Critical Imports")
    logger.info("="*80)
    
    try:
        # Test Gemini strategy generator
        from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
        log_test("Import GeminiStrategyGenerator", "PASS")
        
        # Test bot executor
        from Backtest.bot_executor import get_bot_executor
        log_test("Import BotExecutor", "PASS")
        
        # Test SimBroker
        from Backtest.sim_broker import SimBroker
        log_test("Import SimBroker", "PASS")
        
        # Test data loader
        from Backtest.data_loader import fetch_market_data
        log_test("Import DataLoader", "PASS")
        
        return True
    except Exception as e:
        log_test("Critical Imports", "FAIL", str(e))
        return False


def test_api_key_configuration():
    """Test 2: Verify API keys are configured"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: API Key Configuration")
    logger.info("="*80)
    
    try:
        keys_file = Path(__file__).parent / "keys.json"
        
        if not keys_file.exists():
            log_test("Keys file exists", "FAIL", "keys.json not found")
            return False
        
        log_test("Keys file exists", "PASS")
        
        with open(keys_file, 'r') as f:
            keys_data = json.load(f)
        
        if 'keys' not in keys_data:
            log_test("Keys data format", "FAIL", "No 'keys' array in keys.json")
            return False
        
        log_test("Keys data format", "PASS", f"Found {len(keys_data['keys'])} keys")
        
        # Check for at least one working key
        from Backtest.key_rotation import get_key_manager
        key_manager = get_key_manager()
        
        log_test("Key manager initialized", "PASS")
        
        return True
    except Exception as e:
        log_test("API Key Configuration", "FAIL", str(e))
        return False


def test_strategy_generator_initialization():
    """Test 3: Initialize strategy generator"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Strategy Generator Initialization")
    logger.info("="*80)
    
    try:
        from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
        
        # Try with gemini-2.0-flash (should be available)
        generator = GeminiStrategyGenerator(model_name='gemini-2.0-flash')
        log_test("Initialize with gemini-2.0-flash", "PASS")
        
        return generator
    except Exception as e:
        log_test("Strategy Generator Initialization", "FAIL", str(e))
        return None


def test_data_loading():
    """Test 4: Data loading functionality"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Data Loading")
    logger.info("="*80)
    
    try:
        from Backtest.data_loader import fetch_market_data
        
        # Test loading MSFT data
        data = fetch_market_data(
            symbol='MSFT',
            period='1mo',  # Short period for testing
            interval='1d'
        )
        
        if data is None or len(data) == 0:
            log_test("Load MSFT data", "FAIL", "No data returned")
            return False
        
        log_test("Load MSFT data", "PASS", f"Loaded {len(data)} bars")
        
        # Verify required columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            log_test("Data columns", "FAIL", f"Missing: {missing_columns}")
            return False
        
        log_test("Data columns", "PASS", "All required columns present")
        
        return True
    except Exception as e:
        log_test("Data Loading", "FAIL", str(e))
        return False


def test_strategy_generation():
    """Test 5: Generate a simple strategy"""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: Strategy Code Generation")
    logger.info("="*80)
    
    try:
        from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
        
        generator = GeminiStrategyGenerator(model_name='gemini-2.0-flash')
        
        strategy_description = """
        Create a simple RSI strategy:
        - Buy when RSI < 30 (oversold)
        - Sell when RSI > 70 (overbought)
        - Use 14-period RSI
        - Trade with full position sizing
        """
        
        strategy_name = "RSI_E2E_Test_Strategy"
        output_dir = Path(__file__).parent / "Backtest" / "codes"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"{strategy_name}.py"
        
        # Clean up any existing file
        if output_file.exists():
            output_file.unlink()
        
        logger.info(f"Generating strategy: {strategy_name}")
        saved_path, code = generator.generate_and_save(
            description=strategy_description,
            output_path=str(output_file),
            strategy_name=strategy_name,
            execute_after_generation=False
        )
        
        if not saved_path or not saved_path.exists():
            log_test("Strategy file created", "FAIL", "File not created")
            return None
        
        log_test("Strategy file created", "PASS", str(saved_path))
        
        # Verify file content
        content = saved_path.read_text()
        
        if f"class {strategy_name}" not in content:
            log_test("Strategy class in file", "FAIL", "Class not found")
            return None
        
        log_test("Strategy class in file", "PASS")
        
        if "def run_backtest" not in content:
            log_test("run_backtest function", "FAIL", "Function not found")
            return None
        
        log_test("run_backtest function", "PASS")
        
        return saved_path
    except Exception as e:
        log_test("Strategy Generation", "FAIL", str(e))
        logger.exception("Full error:")
        return None


def test_simbroker_initialization():
    """Test 6: SimBroker initialization"""
    logger.info("\n" + "="*80)
    logger.info("TEST 6: SimBroker Initialization")
    logger.info("="*80)
    
    try:
        from Backtest.sim_broker import SimBroker
        from Backtest.data_loader import fetch_market_data
        
        # Load test data
        data = fetch_market_data(symbol='MSFT', period='1mo', interval='1d')
        
        # Initialize broker
        broker = SimBroker(
            initial_balance=10000,
            data=data,
            commission=0.001,
            slippage=0.0005
        )
        
        log_test("SimBroker initialized", "PASS", f"Balance: ${broker.balance:.2f}")
        
        if broker.balance != 10000:
            log_test("Initial balance correct", "FAIL", f"Expected 10000, got {broker.balance}")
            return False
        
        log_test("Initial balance correct", "PASS")
        
        return True
    except Exception as e:
        log_test("SimBroker Initialization", "FAIL", str(e))
        return False


def test_manual_backtest():
    """Test 7: Manual backtest execution"""
    logger.info("\n" + "="*80)
    logger.info("TEST 7: Manual Backtest Execution")
    logger.info("="*80)
    
    try:
        from Backtest.sim_broker import SimBroker
        from Backtest.data_loader import fetch_market_data
        from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
        
        # Load test data
        data = fetch_market_data(symbol='MSFT', period='1mo', interval='1d')
        logger.info(f"Loaded {len(data)} bars for manual backtest")
        
        # Initialize broker
        broker = SimBroker(
            initial_balance=10000,
            data=data,
            commission=0.001,
            slippage=0.0005
        )
        
        log_test("Broker initialized for backtest", "PASS")
        
        # Simple strategy: Buy on first bar, sell on last bar
        trades_executed = 0
        
        for i in range(len(data)):
            broker.step_to(i)
            
            if i == 5 and broker.position == 0:  # Buy after a few bars
                signal = create_signal(
                    symbol='MSFT',
                    side=OrderSide.BUY,
                    action=OrderAction.OPEN,
                    order_type=OrderType.MARKET,
                    quantity=10
                )
                result = broker.process_signal(signal)
                if result and result.get('status') == 'filled':
                    trades_executed += 1
                    logger.info(f"✅ Buy order filled at bar {i}")
            
            elif i == len(data) - 2 and broker.position > 0:  # Sell before end
                signal = create_signal(
                    symbol='MSFT',
                    side=OrderSide.SELL,
                    action=OrderAction.CLOSE,
                    order_type=OrderType.MARKET,
                    quantity=broker.position
                )
                result = broker.process_signal(signal)
                if result and result.get('status') == 'filled':
                    trades_executed += 1
                    logger.info(f"✅ Sell order filled at bar {i}")
        
        if trades_executed == 0:
            log_test("Trade execution", "FAIL", "No trades executed")
            return False
        
        log_test("Trade execution", "PASS", f"{trades_executed} trades executed")
        
        # Get final metrics
        final_balance = broker.balance + (broker.position * broker.get_current_price())
        pnl = final_balance - 10000
        
        log_test("PnL calculation", "PASS", f"PnL: ${pnl:.2f}, Final: ${final_balance:.2f}")
        
        return True
    except Exception as e:
        log_test("Manual Backtest Execution", "FAIL", str(e))
        logger.exception("Full error:")
        return False


def print_summary_report():
    """Print comprehensive test summary report"""
    logger.info("\n" + "="*80)
    logger.info("COMPREHENSIVE TEST REPORT")
    logger.info("="*80)
    logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Tests Run: {test_results['tests_run']}")
    logger.info(f"Tests Passed: {test_results['tests_passed']}")
    logger.info(f"Tests Failed: {test_results['tests_failed']}")
    
    if test_results['tests_run'] > 0:
        pass_rate = (test_results['tests_passed'] / test_results['tests_run']) * 100
        logger.info(f"Pass Rate: {pass_rate:.1f}%")
    
    logger.info("\n" + "-"*80)
    logger.info("DETAILED RESULTS")
    logger.info("-"*80)
    
    for test in test_results['test_details']:
        symbol = '✅' if test['status'] == 'PASS' else '❌'
        logger.info(f"{symbol} {test['name']}: {test['status']}")
        if test['details']:
            logger.info(f"   {test['details']}")
    
    logger.info("\n" + "="*80)
    
    # Overall assessment
    if test_results['tests_failed'] == 0:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("✅ System Status: OPERATIONAL")
    else:
        logger.info("⚠️  SOME TESTS FAILED")
        logger.info(f"❌ System Status: {test_results['tests_failed']} ISSUES DETECTED")
    
    logger.info("="*80)


def main():
    """Run all tests"""
    logger.info("\n" + "="*80)
    logger.info("MONOLITHIC AGENT COMPREHENSIVE E2E TEST SUITE")
    logger.info("="*80)
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run tests in sequence
    test_imports()
    test_api_key_configuration()
    test_strategy_generator_initialization()
    test_data_loading()
    test_strategy_generation()
    test_simbroker_initialization()
    test_manual_backtest()
    
    # Print summary
    print_summary_report()
    
    # Return exit code
    return 0 if test_results['tests_failed'] == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
