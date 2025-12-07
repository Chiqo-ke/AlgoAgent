"""
Test Stop Loss / Take Profit Detection with Pips
=================================================

This script tests that the system correctly detects stop loss and take profit
specified in pips (not just % or $).
"""

import sys
from pathlib import Path

# Add Strategy to path
strategy_dir = Path(__file__).parent / 'monolithic_agent' / 'Strategy'
sys.path.insert(0, str(strategy_dir))

from strategy_parser import StrategyParser
from recommendation_engine import RecommendationEngine

def test_pip_detection():
    """Test that pips are correctly detected in stop loss and take profit"""
    
    print("=" * 80)
    print("TESTING PIP DETECTION IN STOP LOSS / TAKE PROFIT")
    print("=" * 80)
    
    # Test case: Your exact strategy
    strategy_text = """
    Buy when the 30 EMA crosses above the 60 EMA, and sell when the 30 EMA 
    crosses below the 60 EMA. For every trade, set a stop loss 10 pips from 
    entry and a take profit 50 pips from entry
    """
    
    print("\nStrategy Text:")
    print(strategy_text)
    
    # Parse the strategy
    parser = StrategyParser()
    parsed_steps = parser.parse_strategy_text(strategy_text)
    
    print("\n" + "-" * 80)
    print("PARSED STEPS:")
    print("-" * 80)
    
    for i, step in enumerate(parsed_steps, 1):
        print(f"\nStep {i}:")
        print(f"  Title: {step.title}")
        print(f"  Trigger: {step.trigger}")
        print(f"  Action: {step.action_type.value}")
        if step.exit_conditions:
            print(f"  Exit Conditions:")
            for key, value in step.exit_conditions.items():
                print(f"    - {key}: {value}")
    
    # Convert to canonical format
    canonical_steps = parser.to_canonical_steps(parsed_steps)
    
    print("\n" + "-" * 80)
    print("CANONICAL STEPS:")
    print("-" * 80)
    
    import json
    for step in canonical_steps:
        print(json.dumps(step, indent=2))
    
    # Check with recommendation engine
    print("\n" + "-" * 80)
    print("RISK CONTROL DETECTION:")
    print("-" * 80)
    
    strategy_data = {
        "title": "EMA Crossover with Pips",
        "steps": canonical_steps
    }
    
    rec_engine = RecommendationEngine()
    rec_engine._analyze_risk_controls(strategy_data)
    
    # Check if stop loss warning appears
    stop_loss_warnings = [
        r for r in rec_engine.recommendations 
        if 'stop' in r.title.lower()
    ]
    
    take_profit_warnings = [
        r for r in rec_engine.recommendations 
        if 'profit' in r.title.lower()
    ]
    
    print(f"\nStop Loss Warnings: {len(stop_loss_warnings)}")
    if stop_loss_warnings:
        print("  ❌ FAILED - System still thinks stop loss is missing!")
        for warning in stop_loss_warnings:
            print(f"     {warning.title}: {warning.rationale}")
    else:
        print("  ✅ PASSED - Stop loss detected correctly!")
    
    print(f"\nTake Profit Warnings: {len(take_profit_warnings)}")
    if take_profit_warnings:
        print("  ❌ FAILED - System still thinks take profit is missing!")
        for warning in take_profit_warnings:
            print(f"     {warning.title}: {warning.rationale}")
    else:
        print("  ✅ PASSED - Take profit detected correctly!")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if not stop_loss_warnings and not take_profit_warnings:
        print("✅ SUCCESS - Both stop loss and take profit in pips detected!")
        print("\nThe system should now:")
        print("  ✓ Recognize '10 pips from entry' as valid stop loss")
        print("  ✓ Recognize '50 pips from entry' as valid take profit")
        print("  ✓ NOT warn about missing risk management")
        return True
    else:
        print("❌ FAILED - System not detecting pips correctly")
        print("\nIssues:")
        if stop_loss_warnings:
            print("  ✗ Stop loss in pips not recognized")
        if take_profit_warnings:
            print("  ✗ Take profit in pips not recognized")
        return False


if __name__ == "__main__":
    success = test_pip_detection()
    sys.exit(0 if success else 1)
