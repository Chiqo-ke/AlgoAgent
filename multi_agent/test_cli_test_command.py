"""
Test script to demonstrate the new CLI test command.

This shows how to use the Tester Agent to validate generated strategies.
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Test the CLI test command."""
    print("="*70)
    print("   CLI TEST COMMAND DEMONSTRATION")
    print("="*70)
    print()
    
    # Check if there are any generated strategies
    artifacts_dir = Path(__file__).parent / "Backtest" / "codes"
    
    if not artifacts_dir.exists():
        print("❌ No artifacts directory found")
        print(f"   Expected: {artifacts_dir}")
        print("\n💡 First generate a strategy:")
        print("   python cli.py --request \"Create RSI strategy\" --run")
        return 1
    
    strategy_files = list(artifacts_dir.glob("ai_strategy_*.py"))
    
    if not strategy_files:
        print("⚠️  No generated strategy files found")
        print(f"   Looking in: {artifacts_dir}")
        print("\n💡 First generate a strategy:")
        print("   python cli.py --request \"Create RSI strategy\" --run")
        return 1
    
    print(f"✓ Found {len(strategy_files)} generated strategy file(s):")
    for sf in strategy_files:
        print(f"  - {sf.name}")
    print()
    
    # Test the strategies
    print("Testing generated strategies...")
    print()
    
    # Example 1: Interactive mode
    print("="*70)
    print("Example 1: Interactive Mode")
    print("="*70)
    print()
    print("Run: python cli.py")
    print("Then type: test wf_<your_workflow_id>")
    print()
    
    # Example 2: Command-line mode
    print("="*70)
    print("Example 2: Command-Line Mode")
    print("="*70)
    print()
    print("Run: python cli.py --test wf_<your_workflow_id>")
    print()
    
    # Example 3: Full workflow (submit → execute → test)
    print("="*70)
    print("Example 3: Full Workflow (Submit → Execute → Test)")
    print("="*70)
    print()
    print("Step 1: Submit and execute")
    print('  python cli.py --request "Create EMA crossover strategy" --run')
    print()
    print("Step 2: Test the generated code")
    print('  python cli.py --test wf_<workflow_id_from_step_1>')
    print()
    
    # Show test output format
    print("="*70)
    print("Expected Test Output")
    print("="*70)
    print()
    print("🧪 Testing workflow: wf_abc123")
    print()
    print("📁 Found 4 strategy file(s):")
    print("   - ai_strategy_data_loading.py")
    print("   - ai_strategy_indicator_ema.py")
    print("   - ai_strategy_entry_ema_cross.py")
    print("   - ai_strategy_exit_sl_tp.py")
    print()
    print("🧪 Testing: ai_strategy_data_loading")
    print("   Strategy: ai_strategy_data_loading.py")
    print("   Test: test_ai_strategy_data_loading.py")
    print("   ⏳ Running tests...")
    print("   ✅ PASSED (2.34s)")
    print("      Total Trades: 42")
    print("      Win Rate: 57.1%")
    print("      Net PnL: $1,234.56")
    print()
    print("🧪 Testing: ai_strategy_indicator_ema")
    print("   Strategy: ai_strategy_indicator_ema.py")
    print("   Test: test_ai_strategy_indicator_ema.py")
    print("   ⏳ Running tests...")
    print("   ✅ PASSED (1.89s)")
    print()
    print("="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print("   Total: 4")
    print("   Passed: 4 ✅")
    print("   Failed: 0 ❌")
    print("   Success Rate: 100%")
    print()
    print("💾 Detailed report saved: test_report_wf_abc123_20251120_143022.json")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
