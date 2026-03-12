"""
Test GeminiStrategyGenerator with detailed logging
"""
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent / "Backtest"))

# Configure logging FIRST
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)8s | %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

# Now import
from dotenv import load_dotenv
load_dotenv()

from gemini_strategy_generator import GeminiStrategyGenerator

print("=" * 80)
print("TESTING GEMINI STRATEGY GENERATOR WITH KEY ROTATION")
print("=" * 80)

print("\nCreating generator with use_key_rotation=True...")
try:
    generator = GeminiStrategyGenerator(use_key_rotation=True)
    print(f"\n✓ Generator created successfully")
    print(f"  use_key_rotation: {generator.use_key_rotation}")
    print(f"  selected_key_id: {generator.selected_key_id}")
    print(f"  key_manager: {generator.key_manager}")
except Exception as e:
    print(f"\n✗ Generator creation failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
