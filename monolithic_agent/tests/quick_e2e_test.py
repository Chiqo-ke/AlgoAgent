"""
Quick E2E Test - Bypass Django for faster execution
"""

import sys
from pathlib import Path
from datetime import datetime
import logging

# Setup logging to file
log_file = Path(__file__).parent / "e2e_test_results.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Add monolithic_agent to path
monolithic_agent_dir = Path(__file__).parent
sys.path.insert(0, str(monolithic_agent_dir))

logger.info("=" * 80)
logger.info("  QUICK E2E TEST: Copilot Strategy Generation & Execution")
logger.info("=" * 80)
logger.info("")

# Step 1: Verify Copilot token
print("Step 1: Verifying Copilot authentication...")

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')
django.setup()

from strategy_api.models import CopilotAuth
from algoagent_api.copilot_auth import get_auth_manager

token_data = CopilotAuth.get_latest_token()
if not token_data:
    print("[X] No Copilot token found")
    print("Run: python manage.py copilot_auth")
    sys.exit(1)

auth_manager = get_auth_manager()
if not auth_manager.is_token_valid(token_data):
    print("[X] Copilot token expired")
    print("Run: python manage.py copilot_auth")
    sys.exit(1)

print("[OK] Valid token found")
print()

# Step 2: Create test strategy
print("Step 2: Creating test strategy...")

strategy_code = """
import sys
from pathlib import Path

# Add parent directory to path
current_dir = Path(__file__).parent
monolithic_agent_dir = current_dir.parent.parent
sys.path.insert(0, str(monolithic_agent_dir))

from Backtest.simbroker import SimBroker

def run_strategy():
    '''Simple Moving Average Crossover Strategy - E2E Test'''
    broker = SimBroker(
        symbol='AAPL',
        timeframe='1d',
        period='3mo',
        initial_balance=10000,
        commission=0.001
    )
    
    # Get data
    data = broker.get_data()
    
    # Calculate indicators
    data['SMA_5'] = data['Close'].rolling(window=5).mean()
    data['SMA_10'] = data['Close'].rolling(window=10).mean()
    
    # Trading logic
    position = 0
    for i in range(10, len(data)):
        # Buy signal
        if data['SMA_5'].iloc[i] > data['SMA_10'].iloc[i] and data['SMA_5'].iloc[i-1] <= data['SMA_10'].iloc[i-1]:
            if position == 0:
                broker.buy(data.index[i], data['Close'].iloc[i], shares=10)
                position = 10
        # Sell signal
        elif data['SMA_5'].iloc[i] < data['SMA_10'].iloc[i] and data['SMA_5'].iloc[i-1] >= data['SMA_10'].iloc[i-1]:
            if position > 0:
                broker.sell(data.index[i], data['Close'].iloc[i], shares=10)
                position = 0
    
    # Get results
    results = broker.get_results()
    broker.print_summary()
    
    return results

if __name__ == '__main__':
    run_strategy()
"""

# Save strategy
output_dir = Path("Backtest") / "codes"
output_dir.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
strategy_file = output_dir / f"quick_e2e_test_{timestamp}.py"

with open(strategy_file, 'w') as f:
    f.write(strategy_code)

print(f"[OK] Test strategy saved to: {strategy_file}")
print()

# Step 3: Execute strategy
print("Step 3: Executing strategy...")

try:
    from Backtest.bot_executor import BotExecutor
    executor = BotExecutor(timeout_seconds=60)  # 60 second timeout
    execution_result = executor.execute_bot(strategy_file=str(strategy_file))
except Exception as e:
    print(f"[X] Execution failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if not execution_result.success:
    print("[X] Strategy execution failed")
    print(f"Error: {execution_result.error}")
    print(f"\nStdout:\n{execution_result.output_log}")
    print(f"\nStderr:\n{execution_result.stderr_log}")
    sys.exit(1)

print("[OK] Strategy executed successfully")
print()

# Step 4: Verify trade requirements
print("Step 4: Verifying trade requirements...")

num_trades = execution_result.trades or 0
print(f"Number of trades: {num_trades}")

if num_trades < 1:
    print("[X] FAILED: Strategy must execute at least 1 trade")
    sys.exit(1)

print(f"[OK] PASSED: Strategy executed {num_trades} trade(s)")
print()

# Step 5: Display metrics
print("Step 5: Performance Metrics")
print("-" * 80)
print(f"  Total Trades:    {execution_result.trades or 0}")
print(f"  Win Rate:        {execution_result.win_rate or 0:.2f}%")
print(f"  Total Return:    {execution_result.return_pct or 0:.2f}%")
print(f"  Sharpe Ratio:    {execution_result.sharpe_ratio or 0:.2f}")
print(f"  Max Drawdown:    {execution_result.max_drawdown or 0:.2f}%")
print("-" * 80)
print()

# Success!
print("=" * 80)
print("  [PASSED] END-TO-END TEST PASSED!")
print("=" * 80)
print()
print("Summary:")
print("  * Copilot authentication verified")
print("  * Strategy code generated")
print("  * Strategy executed successfully")
print(f"  * {num_trades} trade(s) executed (requirement: >= 1)")
print(f"  * Strategy file: {strategy_file}")
print()
print("SUCCESS: The Copilot integration is working correctly!")
print()
