"""
Quick Strategy Generator
========================

Simplified wrapper for gemini_strategy_generator.py
No need to worry about PowerShell syntax!
"""

import sys
import subprocess
from pathlib import Path

# Example strategies
EXAMPLES = {
    '1': {
        'name': 'RSI Oversold/Overbought',
        'description': 'Buy AAPL when RSI < 30, sell when RSI > 70',
        'output': 'rsi_strategy.py'
    },
    '2': {
        'name': 'EMA Crossover',
        'description': 'Buy AAPL when 50 EMA crosses above 200 EMA, sell when crosses below',
        'output': 'ema_crossover_strategy.py'
    },
    '3': {
        'name': 'MACD Momentum',
        'description': 'Buy when MACD crosses above signal line and histogram positive, sell when crosses below',
        'output': 'macd_strategy.py'
    },
    '4': {
        'name': 'Bollinger Bands',
        'description': 'Buy when price touches lower Bollinger Band, sell when price reaches middle band',
        'output': 'bb_strategy.py'
    },
    '5': {
        'name': 'Moving Average Trend',
        'description': 'Buy when price crosses above 20 SMA, sell when crosses below',
        'output': 'sma_trend_strategy.py'
    }
}


def generate_strategy(description: str, output_file: str, validate: bool = True):
    """Generate a strategy using gemini_strategy_generator.py"""
    
    # Build command
    python_exe = sys.executable
    generator_script = Path(__file__).parent / "gemini_strategy_generator.py"
    
    # Ensure output file is just the filename (will be saved to codes/ automatically)
    output_file = Path(output_file).name
    
    cmd = [python_exe, str(generator_script), description, "-o", output_file]
    if validate:
        cmd.append("--validate")
    
    print(f"\n{'='*60}")
    print(f"Generating: codes/{output_file}")
    print(f"{'='*60}")
    print(f"Description: {description}")
    print()
    
    # Run command
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        codes_dir = Path(__file__).parent / "codes"
        full_path = codes_dir / output_file
        print(f"\n✅ Success! Strategy saved to: {full_path}")
        print(f"\nTo run it:")
        print(f"  python {full_path}")
        print(f"\nOr from codes directory:")
        print(f"  cd codes")
        print(f"  python {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to generate strategy")
        return False


def interactive_mode():
    """Interactive menu for generating strategies"""
    
    print("=" * 60)
    print("QUICK STRATEGY GENERATOR")
    print("=" * 60)
    print("\nChoose an option:")
    print()
    print("  [1-5] Generate example strategy")
    print("  [c]   Custom strategy (enter your own description)")
    print("  [q]   Quit")
    print()
    
    # Show examples
    print("Example Strategies:")
    for num, info in EXAMPLES.items():
        print(f"  {num}. {info['name']}")
    print()
    
    choice = input("Your choice: ").strip().lower()
    
    if choice == 'q':
        print("Goodbye!")
        return False
    
    elif choice in EXAMPLES:
        # Generate example strategy
        info = EXAMPLES[choice]
        print(f"\nGenerating: {info['name']}")
        generate_strategy(info['description'], info['output'])
        return True
    
    elif choice == 'c':
        # Custom strategy
        print("\n" + "=" * 60)
        print("CUSTOM STRATEGY")
        print("=" * 60)
        print("\nTips for good descriptions:")
        print("  - Be specific about entry and exit conditions")
        print("  - Mention which indicators to use (RSI, SMA, EMA, MACD, etc.)")
        print("  - Specify the ticker (e.g., AAPL, SPY, TSLA)")
        print()
        print("Example:")
        print('  "Buy AAPL when RSI < 30 and price above 200 SMA, sell when RSI > 70"')
        print()
        
        description = input("Enter strategy description: ").strip()
        if not description:
            print("❌ No description provided")
            return True
        
        output_file = input("Output filename (e.g., my_strategy.py): ").strip()
        if not output_file:
            output_file = "custom_strategy.py"
        if not output_file.endswith('.py'):
            output_file += '.py'
        
        generate_strategy(description, output_file)
        return True
    
    else:
        print(f"❌ Invalid choice: {choice}")
        return True


def main():
    """Main entry point"""
    
    # Check if description provided as command-line argument
    if len(sys.argv) > 1:
        description = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "generated_strategy.py"
        generate_strategy(description, output_file)
    else:
        # Interactive mode
        while interactive_mode():
            print("\n" + "=" * 60)
            print()
            again = input("Generate another? (y/n): ").strip().lower()
            if again != 'y':
                print("\nGoodbye!")
                break
            print()


if __name__ == "__main__":
    main()
