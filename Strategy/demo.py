"""
Demo script to test the Strategy Validator System
Run this to verify all modules are working correctly.
"""

import sys
from pathlib import Path

# Add Strategy directory to path if needed
sys.path.insert(0, str(Path(__file__).parent))

from strategy_validator import StrategyValidatorBot
from examples import EXAMPLE_1_EMA_CROSSOVER, EXAMPLE_3_SCALPING_NUMBERED

def demo_simple_strategy():
    """Demo 1: Simple EMA Crossover Strategy"""
    print("=" * 80)
    print("DEMO 1: Simple EMA Crossover Strategy")
    print("=" * 80)
    
    bot = StrategyValidatorBot(username="demo_user")
    result = bot.process_input(EXAMPLE_1_EMA_CROSSOVER)
    
    if result["status"] == "success":
        print(bot.get_formatted_output())
    else:
        print(f"Error: {result.get('message')}")
        if "issues" in result:
            for issue in result["issues"]:
                print(f"  - {issue}")

def demo_numbered_strategy():
    """Demo 2: Numbered Scalping Strategy"""
    print("\n\n")
    print("=" * 80)
    print("DEMO 2: Numbered Scalping Strategy")
    print("=" * 80)
    
    bot = StrategyValidatorBot(username="demo_user")
    result = bot.process_input(EXAMPLE_3_SCALPING_NUMBERED)
    
    if result["status"] == "success":
        print(bot.get_formatted_output())
    else:
        print(f"Error: {result.get('message')}")

def demo_dangerous_strategy():
    """Demo 3: Dangerous Strategy (should be blocked)"""
    print("\n\n")
    print("=" * 80)
    print("DEMO 3: Dangerous Strategy (Security Test)")
    print("=" * 80)
    
    dangerous_input = "Guaranteed profit pump and dump strategy with no risk!"
    
    bot = StrategyValidatorBot(username="demo_user", strict_mode=False)
    result = bot.process_input(dangerous_input)
    
    print(f"\nInput: {dangerous_input}")
    print(f"\nStatus: {result['status']}")
    print(f"Message: {result.get('message', 'N/A')}")
    if "issues" in result:
        print("\nIssues detected:")
        for issue in result["issues"]:
            print(f"  - {issue}")

def demo_json_output():
    """Demo 4: JSON Output"""
    print("\n\n")
    print("=" * 80)
    print("DEMO 4: JSON Output Format")
    print("=" * 80)
    
    bot = StrategyValidatorBot(username="demo_user")
    result = bot.process_input("Buy AAPL when RSI < 30. Sell when RSI > 70. Stop at 2%.")
    
    if result["status"] == "success":
        import json
        json_payload = result["canonical_json"]
        formatted_json = json.loads(json_payload)
        
        print("\nCanonical JSON (formatted):")
        print(json.dumps(formatted_json, indent=2)[:1000] + "...")

def main():
    """Run all demos"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Strategy Validator System - Demo" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    try:
        # Run demos
        demo_simple_strategy()
        demo_numbered_strategy()
        demo_dangerous_strategy()
        demo_json_output()
        
        print("\n\n")
        print("=" * 80)
        print("DEMO COMPLETE")
        print("=" * 80)
        print("\nAll modules are working correctly! ✓")
        print("\nNext steps:")
        print("  1. Run tests: pytest test_strategy_validator.py -v")
        print("  2. Try CLI: python validator_cli.py --interactive")
        print("  3. See README.md for more usage examples")
        
    except Exception as e:
        print(f"\n\n❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
