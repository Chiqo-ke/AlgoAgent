"""
End-to-End Test: RSI Strategy Generation and Auto-Fix
======================================================
Tests whether the agent can:
1. Generate an RSI strategy with specified parameters
2. Execute the generated bot
3. Automatically detect and fix any errors that occur
4. Successfully iterate to a working solution

Parameters:
- RSI Period: 30
- Take Profit: 40 pips from entry
- Stop Loss: 10 pips from entry

Hands-off test: Agent must solve problems without manual intervention.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env
env_path = Path(__file__).parent / "monolithic_agent" / ".env"
load_dotenv(env_path)

# Add monolithic_agent to path
sys.path.insert(0, str(Path(__file__).parent / "monolithic_agent"))

# Ensure key rotation is enabled
os.environ['ENABLE_KEY_ROTATION'] = 'true'
os.environ['SECRET_STORE_TYPE'] = 'env'

from monolithic_agent.Backtest.gemini_strategy_generator import GeminiStrategyGenerator
from monolithic_agent.Backtest.bot_executor import BotExecutor
from monolithic_agent.Backtest.bot_error_fixer import BotErrorFixer


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_rsi_strategy_generation():
    """Test 1: Agent generates RSI strategy."""
    print_section("TEST 1: RSI STRATEGY GENERATION")
    
    try:
        gen = GeminiStrategyGenerator()
        print("\n✓ GeminiStrategyGenerator initialized")
        
        # Prompt for RSI strategy
        prompt = """
        Create a trading strategy using RSI (Relative Strength Index) with these specifications:
        
        STRATEGY REQUIREMENTS:
        - Indicator: RSI with 30 periods
        - Buy Signal: RSI crosses above 30 (oversold territory)
        - Sell Signal: RSI crosses below 70 (overbought territory)
        - Stop Loss: 10 pips from entry price
        - Take Profit: 40 pips from entry price
        - Trading asset: GOOG (Google stock data)
        
        The strategy should:
        1. Calculate RSI with period=30
        2. Generate buy signals when RSI > 30 (uptrend)
        3. Generate sell signals when RSI < 70 (downtrend)
        4. Use fixed 10 pip stop loss and 40 pip take profit
        5. Be compatible with backtesting framework
        
        Use the bt (Backtest.py) library for implementation.
        """
        
        print("\n📝 Generating strategy with prompt...")
        strategy_code = gen.generate_strategy(prompt)
        
        # Save strategy
        output_dir = Path(__file__).parent / "monolithic_agent" / "Backtest" / "generated_strategies"
        output_dir.mkdir(parents=True, exist_ok=True)
        strategy_file = output_dir / "rsi_strategy_test.py"
        
        strategy_file.write_text(strategy_code)
        print(f"✓ Strategy saved to: {strategy_file}")
        print(f"\n✓ GENERATED CODE ({len(strategy_code)} chars):")
        print("-" * 80)
        print(strategy_code[:500] + "..." if len(strategy_code) > 500 else strategy_code)
        print("-" * 80)
        
        return strategy_file
        
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {str(e)}")
        return None


def test_strategy_execution(strategy_file):
    """Test 2: Execute generated strategy and monitor for errors."""
    print_section("TEST 2: INITIAL STRATEGY EXECUTION")
    
    if not strategy_file or not strategy_file.exists():
        print("✗ Strategy file not found")
        return None
    
    try:
        executor = BotExecutor()
        print(f"\n✓ BotExecutor initialized")
        print(f"  Executing: {strategy_file.name}")
        
        # Execute the generated strategy
        result = executor.execute_bot(
            strategy_file=strategy_file,
            test_symbol="GOOG",
            test_period_days=365
        )
        
        print(f"\n✓ Strategy executed!")
        print(f"  Status: {'SUCCESS' if result.success else 'FAILED'}")
        
        if result.success:
            print(f"  Return: {result.return_pct}%")
            print(f"  Trades: {result.trades}")
            return strategy_file
        else:
            print(f"  Error: {result.error}")
            return strategy_file
        
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {str(e)}")
        return strategy_file


def test_auto_error_fixing(strategy_file):
    """Test 3: Auto-fix any errors that occurred."""
    print_section("TEST 3: AUTOMATED ERROR FIXING (IF NEEDED)")
    
    if not strategy_file or not strategy_file.exists():
        print("✗ Strategy file not found")
        return None
    
    try:
        gen = GeminiStrategyGenerator()
        print(f"\n✓ Using automated error fixing system")
        print(f"  Max iterations: 3")
        print(f"  Target: Make strategy executable and profitable\n")
        
        # Use the integrated error fixing method
        success, final_path, fix_history = gen.fix_bot_errors_iteratively(
            strategy_file=strategy_file,
            max_iterations=3,
            test_symbol="GOOG",
            test_period_days=365
        )
        
        print(f"\n{'✓' if success else '✗'} ERROR FIXING RESULT")
        print(f"  Status: {'SUCCESS' if success else 'FAILED'}")
        print(f"  Final Path: {final_path}")
        print(f"  Fix Attempts: {len(fix_history)}")
        
        if fix_history:
            print(f"\n  Fix History:")
            for i, fix in enumerate(fix_history, 1):
                print(f"    {i}. [{fix.get('error_type', 'unknown')}] - "
                      f"Success: {fix.get('success', False)}")
                if fix.get('fix_description'):
                    print(f"       Fix: {fix['fix_description'][:60]}...")
        
        return final_path if success else strategy_file
        
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return strategy_file


def test_final_execution(strategy_file):
    """Test 4: Final verification that strategy works."""
    print_section("TEST 4: FINAL VERIFICATION")
    
    if not strategy_file or not strategy_file.exists():
        print("✗ Strategy file not found")
        return False
    
    try:
        executor = BotExecutor()
        print(f"\n✓ Final execution of: {strategy_file.name}")
        
        result = executor.execute_bot(
            strategy_file=strategy_file,
            test_symbol="GOOG",
            test_period_days=365
        )
        
        if result.success:
            print(f"\n✅ STRATEGY EXECUTION SUCCESSFUL")
            print(f"  Return: {result.return_pct}%")
            print(f"  Trades: {result.trades}")
            print(f"  Win Rate: {result.win_rate}")
            print(f"  Sharpe Ratio: {result.sharpe_ratio}")
            return True
        else:
            print(f"\n❌ EXECUTION FAILED")
            print(f"  Error: {result.error}")
            return False
        
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {str(e)}")
        return False


def main():
    """Run the complete end-to-end test."""
    print_section("END-TO-END TEST: RSI STRATEGY GENERATION & AUTO-FIX")
    print("\nTest Configuration:")
    print("  - Strategy Type: RSI (Relative Strength Index)")
    print("  - RSI Period: 30")
    print("  - Stop Loss: 10 pips")
    print("  - Take Profit: 40 pips")
    print("  - Test Asset: GOOG")
    print("  - Hands-off: Agent must solve problems automatically")
    print(f"  - Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Generate strategy
    strategy_file = test_rsi_strategy_generation()
    if not strategy_file:
        print_section("TEST FAILED AT GENERATION")
        return False
    
    # Step 2: Try initial execution
    strategy_file = test_strategy_execution(strategy_file)
    if not strategy_file:
        print_section("TEST FAILED AT EXECUTION")
        return False
    
    # Step 3: Auto-fix any errors
    strategy_file = test_auto_error_fixing(strategy_file)
    if not strategy_file:
        print_section("TEST FAILED AT ERROR FIXING")
        return False
    
    # Step 4: Final verification
    success = test_final_execution(strategy_file)
    
    # Summary
    print_section("TEST SUMMARY")
    if success:
        print("\n✅ END-TO-END TEST PASSED")
        print("  Agent successfully:")
        print("  1. Generated RSI strategy")
        print("  2. Executed it with proper setup")
        print("  3. Automatically fixed any errors")
        print("  4. Verified working solution")
    else:
        print("\n❌ END-TO-END TEST FAILED")
        print("  Agent could not achieve working solution")
    
    print(f"\n  Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
