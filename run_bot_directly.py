"""
Test the actual bot script to understand why no trades are made
"""
import sys
from pathlib import Path

# Execute the bot directly
bot_file = Path(r"C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent\Backtest\codes\algoema.py")

if bot_file.exists():
    print(f"Executing bot: {bot_file}")
    print("=" * 70)
    exec(open(bot_file).read())
else:
    print(f"ERROR: Bot file not found at {bot_file}")
