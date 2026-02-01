"""
Quick diagnostic script to test EMA data loading and indicator keys
"""
import sys
from pathlib import Path

# Add monolithic_agent to path
monolithic_path = Path(__file__).parent / "monolithic_agent"
sys.path.insert(0, str(monolithic_path))

from Backtest.data_loader import load_market_data
from datetime import datetime, timedelta

# Test configuration
symbol = "AAPL"
indicators = {
    'EMA': {'periods': [12, 26]}
}

print("=" * 70)
print("TESTING EMA DATA LOADING")
print("=" * 70)
print(f"Symbol: {symbol}")
print(f"Indicators: {indicators}")
print()

# Try to load data
try:
    print("[INFO] Attempting to load 1 month of data...")
    data_stream = load_market_data(
        ticker=symbol,
        indicators=indicators,
        period='1mo',
        interval='1d',
        stream=True,
        use_cache=False  # Force fresh data
    )
    
    print("[OK] Data stream created successfully")
    print()
    
    # Process first 5 bars to see the data structure
    print("=" * 70)
    print("FIRST 5 BARS DATA STRUCTURE")
    print("=" * 70)
    
    bar_count = 0
    for timestamp, market_data, progress_pct in data_stream:
        bar_count += 1
        
        if bar_count <= 5:
            print(f"\nBar {bar_count}: {timestamp}")
            print(f"Progress: {progress_pct:.1f}%")
            
            # Show what's in market_data
            if symbol in market_data:
                symbol_data = market_data[symbol]
                print(f"\nKeys in market_data['{symbol}']:")
                for key in sorted(symbol_data.keys()):
                    value = symbol_data[key]
                    print(f"  '{key}': {value}")
        
        if bar_count >= 5:
            break
    
    print("\n" + "=" * 70)
    print(f"[OK] Processed {bar_count} bars successfully")
    print("=" * 70)

except Exception as e:
    print(f"[ERROR] Failed to load data: {e}")
    import traceback
    traceback.print_exc()
