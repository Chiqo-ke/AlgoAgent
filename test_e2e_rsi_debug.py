"""
Debug version of E2E test with verbose error fixing logging
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

# Load environment variables from .env
env_path = Path(__file__).parent / "monolithic_agent" / ".env"
load_dotenv(env_path)

# Add monolithic_agent to path
sys.path.insert(0, str(Path(__file__).parent / "monolithic_agent"))

# Ensure key rotation is enabled
os.environ['ENABLE_KEY_ROTATION'] = 'true'
os.environ['SECRET_STORE_TYPE'] = 'env'

from monolithic_agent.Backtest.gemini_strategy_generator import (
    GeminiStrategyGenerator, 
    BOT_ERROR_FIXER_AVAILABLE,
    BOT_EXECUTOR_AVAILABLE
)
from monolithic_agent.Backtest.bot_executor import BotExecutor
from monolithic_agent.Backtest.bot_error_fixer import BotErrorFixer


print("=" * 80)
print("DEBUG: Module Availability Check")
print("=" * 80)
print(f"BOT_ERROR_FIXER_AVAILABLE: {BOT_ERROR_FIXER_AVAILABLE}")
print(f"BOT_EXECUTOR_AVAILABLE: {BOT_EXECUTOR_AVAILABLE}")
print()

# Use the pre-generated RSI strategy
strategy_file = Path(__file__).parent / "monolithic_agent" / "Backtest" / "generated_strategies" / "rsi_strategy_test.py"

if not strategy_file.exists():
    print(f"Strategy file not found: {strategy_file}")
    sys.exit(1)

print(f"Testing with strategy: {strategy_file}")
print()

# Test 1: Initial execution
print("=" * 80)
print("TEST 1: Initial Execution")
print("=" * 80)
executor = BotExecutor()
result = executor.execute_bot(
    strategy_file=strategy_file,
    test_symbol="GOOG",
    test_period_days=365
)

print(f"Execution Result:")
print(f"  Success: {result.success}")
print(f"  Error: {result.error}")
print()

# Test 2: Error fixing
print("=" * 80)
print("TEST 2: Error Fixing with Debug Output")
print("=" * 80)

gen = GeminiStrategyGenerator()
print(f"✓ GeminiStrategyGenerator initialized")
print(f"  Calling fix_bot_errors_iteratively()...")
print()

try:
    success, final_path, fix_history = gen.fix_bot_errors_iteratively(
        strategy_file=strategy_file,
        max_iterations=3,
        test_symbol="GOOG",
        test_period_days=365
    )
    
    print(f"\nResult from fix_bot_errors_iteratively():")
    print(f"  Success: {success}")
    print(f"  Final Path: {final_path}")
    print(f"  Fix History Length: {len(fix_history)}")
    print(f"  Fix History Type: {type(fix_history)}")
    
    if fix_history:
        print(f"\n  Fix History Details:")
        for i, fix in enumerate(fix_history, 1):
            print(f"    {i}. {fix}")
    else:
        print(f"\n  ❌ No fix history returned!")
        
except Exception as e:
    print(f"✗ Exception during error fixing:")
    print(f"  {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("DEBUG TEST COMPLETE")
print("=" * 80)
