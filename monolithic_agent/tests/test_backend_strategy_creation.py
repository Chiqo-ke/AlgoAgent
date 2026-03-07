"""
Test strategy generation from backend with actual API call.

This simulates what happens when the Django backend receives a strategy creation request.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from Backtest.gemini_strategy_generator import GeminiStrategyGenerator

def test_strategy_generation():
    """Test generating the EMA crossover strategy."""
    
    print("=" * 80)
    print("BACKEND STRATEGY GENERATION TEST")
    print("=" * 80)
    
    strategy_description = """
make a simple EMA crossover strategy that uses 30 and 70 periods crossing each other for entry. 
Open long positions when 30 ema crosses above 70 ema and enter short position when 70 ema crosses below 30 ema. 
The stop loss should be set 15 pips from entry and take profit should be 70 pips from entry
"""
    
    strategy_name = "Algo_EMA_30_70_Crossover"
    
    print(f"\nStrategy Name: {strategy_name}")
    print(f"Description: {strategy_description.strip()}")
    print("\n" + "=" * 80)
    print("Initializing GeminiStrategyGenerator...")
    print("=" * 80)
    
    try:
        # Initialize generator with key rotation
        generator = GeminiStrategyGenerator(
            use_key_rotation=True
        )
        
        print(f"\n✓ Generator initialized")
        print(f"  Key rotation: {generator.use_key_rotation}")
        print(f"  Selected key: {generator.selected_key_id}")
        
        # Generate strategy
        print("\n" + "=" * 80)
        print("Generating strategy code...")
        print("=" * 80)
        
        code = generator.generate_strategy(
            description=strategy_description,
            strategy_name=strategy_name,
            parameters={
                'ema_fast': 30,
                'ema_slow': 70,
                'stop_loss_pips': 15,
                'take_profit_pips': 70
            }
        )
        
        print("\n" + "=" * 80)
        print("✅ SUCCESS: Strategy code generated!")
        print("=" * 80)
        
        # Show first 1000 characters of code
        print(f"\nGenerated code preview (first 1000 chars):")
        print("-" * 80)
        print(code[:1000])
        print("-" * 80)
        
        # Count lines
        lines = code.split('\n')
        print(f"\n📊 Code Statistics:")
        print(f"  Total lines: {len(lines)}")
        print(f"  Total characters: {len(code)}")
        
        # Check for key components
        print(f"\n🔍 Code Validation:")
        checks = {
            'Strategy class': 'class' in code and strategy_name in code,
            'EMA 30': 'ema' in code.lower() and '30' in code,
            'EMA 70': '70' in code,
            'Long entry': 'long' in code.lower() or 'buy' in code.lower(),
            'Short entry': 'short' in code.lower() or 'sell' in code.lower(),
            'Stop loss': 'stop' in code.lower() and 'loss' in code.lower(),
            'Take profit': 'take' in code.lower() and 'profit' in code.lower(),
        }
        
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check}")
        
        # Save to file
        output_file = Path(__file__).parent / 'Backtest' / 'codes' / f'{strategy_name.lower()}.py'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(code)
        
        print(f"\n💾 Code saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ FAILED: Strategy generation error")
        print("=" * 80)
        print(f"\nError: {e}")
        
        # Show detailed error
        import traceback
        print("\nFull traceback:")
        print("-" * 80)
        traceback.print_exc()
        print("-" * 80)
        
        return False

if __name__ == '__main__':
    try:
        success = test_strategy_generation()
        
        if success:
            print("\n" + "=" * 80)
            print("✅ TEST PASSED: Backend can generate strategies!")
            print("=" * 80)
            print("\nKey rotation system is working correctly.")
            print("Strategy code has been generated and saved.")
            sys.exit(0)
        else:
            print("\n" + "=" * 80)
            print("❌ TEST FAILED: Check errors above")
            print("=" * 80)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
