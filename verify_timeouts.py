"""
Simple Timeout Verification Script
===================================

Verifies that timeout settings are correctly configured without requiring backend.

Author: GitHub Copilot CLI
Created: 2026-02-09
"""

import sys
from pathlib import Path

# Add monolithic_agent to path
sys.path.insert(0, str(Path(__file__).parent / 'monolithic_agent'))

def test_timeout_settings():
    """Verify timeout settings are correct"""
    print("\n" + "=" * 70)
    print("TIMEOUT SETTINGS VERIFICATION")
    print("=" * 70)
    
    errors = []
    
    try:
        print("\n[1/2] Checking BotExecutor...")
        from monolithic_agent.Backtest.bot_executor import BotExecutor
        
        # Test default timeout
        executor = BotExecutor()
        if executor.timeout_seconds == 900:
            print(f"  ✅ BotExecutor default timeout: {executor.timeout_seconds}s")
        else:
            error = f"BotExecutor timeout is {executor.timeout_seconds}s, expected 900s"
            print(f"  ❌ {error}")
            errors.append(error)
        
        # Test custom timeout
        executor_custom = BotExecutor(timeout_seconds=600)
        if executor_custom.timeout_seconds == 600:
            print(f"  ✅ BotExecutor custom timeout: {executor_custom.timeout_seconds}s")
        else:
            error = f"BotExecutor custom timeout failed"
            print(f"  ❌ {error}")
            errors.append(error)
        
    except Exception as e:
        error = f"BotExecutor import/test failed: {e}"
        print(f"  ❌ {error}")
        errors.append(error)
        import traceback
        traceback.print_exc()
    
    try:
        print("\n[2/2] Checking BotDryRunner...")
        from monolithic_agent.Backtest.bot_dry_runner import BotDryRunner
        
        # Test default timeout
        dry_runner = BotDryRunner()
        if dry_runner.timeout == 150:
            print(f"  ✅ BotDryRunner default timeout: {dry_runner.timeout}s")
        else:
            error = f"BotDryRunner timeout is {dry_runner.timeout}s, expected 150s"
            print(f"  ❌ {error}")
            errors.append(error)
        
        # Test custom timeout
        dry_runner_custom = BotDryRunner(timeout=60)
        if dry_runner_custom.timeout == 60:
            print(f"  ✅ BotDryRunner custom timeout: {dry_runner_custom.timeout}s")
        else:
            error = f"BotDryRunner custom timeout failed"
            print(f"  ❌ {error}")
            errors.append(error)
            
    except Exception as e:
        error = f"BotDryRunner import/test failed: {e}"
        print(f"  ❌ {error}")
        errors.append(error)
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    if not errors:
        print("✅ ALL TIMEOUT SETTINGS VERIFIED")
        print("=" * 70)
        print("\nTimeout Configuration:")
        print("  • Dry Run Timeout: 150 seconds (2.5 minutes)")
        print("  • Full Execution Timeout: 900 seconds (15 minutes)")
        print("\nChanges Summary:")
        print("  ✓ BotDryRunner default: 30s → 150s")
        print("  ✓ BotExecutor default: 300s → 900s")
        print("  ✓ Both support custom timeout override")
        return True
    else:
        print("❌ VERIFICATION FAILED")
        print("=" * 70)
        print(f"\n{len(errors)} error(s) found:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        return False

if __name__ == "__main__":
    success = test_timeout_settings()
    sys.exit(0 if success else 1)
