"""
Test the bot using the backtest executor
"""
import sys
from pathlib import Path

# Add monolithic_agent to path
sys.path.insert(0, str(Path(__file__).parent / "monolithic_agent"))

from Backtest.bot_executor import BotExecutor

# Initialize executor
executor = BotExecutor(
    results_dir=Path(__file__).parent / "monolithic_agent" / "Backtest" / "codes" / "results",
    timeout=300
)

# Execute the bot
bot_file = Path(__file__).parent / "monolithic_agent" / "Backtest" / "codes" / "algoema.py"

print("=" * 70)
print("TESTING ALGOEMA BOT")
print("=" * 70)
print(f"Bot file: {bot_file}")
print()

if not bot_file.exists():
    print(f"ERROR: Bot file not found!")
else:
    result = executor.execute(
        bot_file=str(bot_file),
        symbol="AAPL",
        period="3mo"  # Use 3 months to have more data
    )
    
    print("\n" + "=" * 70)
    print("EXECUTION RESULT")
    print("=" * 70)
    print(f"Success: {result['success']}")
    print(f"Error: {result.get('error', 'None')}")
    print(f"Execution Time: {result.get('execution_time', 0):.2f}s")
    print(f"Trades: {result.get('num_trades', 0)}")
    print("=" * 70)
