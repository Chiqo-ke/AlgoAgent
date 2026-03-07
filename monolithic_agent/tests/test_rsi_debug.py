"""
Debug test to see why RSI isn't being added to data
"""
import sys
from pathlib import Path
parent_dir = Path(__file__).parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from Backtest.data_loader import load_market_data

# Request RSI exactly as bot does
indicators = {
    'rsi': {'timeperiod': 14}
}

print("=" * 70)
print("DEBUG: Testing RSI indicator addition")
print("=" * 70)

# Load data in batch mode (easier to debug)
print("\n1. Loading data with RSI indicator...")
df = load_market_data(
    ticker='AAPL',
    indicators=indicators,
    period='6mo',
    interval='1d',
    stream=False  # Batch mode for easier debugging
)

print(f"\n2. Data shape: {df.shape}")
print(f"\n3. Columns in DataFrame:")
for col in df.columns:
    print(f"   - {col}")

print(f"\n4. Checking for RSI-related columns:")
rsi_cols = [col for col in df.columns if 'rsi' in col.lower()]
print(f"   RSI columns found: {rsi_cols}")

if rsi_cols:
    print(f"\n5. RSI values (first 20 rows):")
    for col in rsi_cols:
        print(f"\n   {col}:")
        print(df[col].head(20))
else:
    print("\n5. NO RSI COLUMNS FOUND!")
    print("\n   This explains why bot has no trades - RSI is missing")
    
print("\n" + "=" * 70)
