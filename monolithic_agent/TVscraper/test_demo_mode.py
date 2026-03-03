"""
Demo Mode: Multi-Symbol Data Fetcher (No MCP Required)
======================================================
Creates sample CSV files for MSFT, AAPL, and TSLA with EMA data.
This demo shows the expected output structure without requiring TradingView or MCP.

Use this to:
- Understand the output format
- Test CSV processing scripts
- Verify the DataTV folder structure
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_sample_data(symbol, base_price, num_candles=20):
    """
    Generate sample OHLCV data with EMA indicators.
    
    Args:
        symbol: Stock ticker (e.g., "MSFT")
        base_price: Starting price
        num_candles: Number of 5-minute candles to generate
        
    Returns:
        List of dictionaries with candle and indicator data
    """
    data = []
    current_time = datetime.now()
    price = base_price
    
    # EMA calculation (simplified)
    ema_20_values = []
    ema_50_values = []
    
    for i in range(num_candles):
        # Generate realistic price movement
        change_pct = random.uniform(-0.5, 0.5) / 100  # ±0.5%
        price = price * (1 + change_pct)
        
        # OHLC for 5-minute bar
        open_price = round(price, 2)
        high_price = round(price * (1 + random.uniform(0, 0.3) / 100), 2)
        low_price = round(price * (1 - random.uniform(0, 0.3) / 100), 2)
        close_price = round(price * (1 + random.uniform(-0.2, 0.2) / 100), 2)
        volume = random.randint(500000, 2000000)
        
        # Simple EMA calculation
        if len(ema_20_values) < 20:
            ema_20 = close_price  # Not enough data yet
        else:
            multiplier_20 = 2 / (20 + 1)
            ema_20 = (close_price * multiplier_20) + (ema_20_values[-1] * (1 - multiplier_20))
        
        if len(ema_50_values) < 50:
            ema_50 = close_price  # Not enough data yet
        else:
            multiplier_50 = 2 / (50 + 1)
            ema_50 = (close_price * multiplier_50) + (ema_50_values[-1] * (1 - multiplier_50))
        
        ema_20_values.append(ema_20)
        ema_50_values.append(ema_50)
        
        # Create candle data
        candle = {
            'timestamp': (current_time - timedelta(minutes=5 * (num_candles - i))).strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': symbol,
            'timeframe': '5m',
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume,
            'ema_20': round(ema_20, 2),
            'ema_50': round(ema_50, 2)
        }
        
        data.append(candle)
        price = close_price  # Update for next iteration
    
    return data


def save_to_csv(data, filepath):
    """Save data to CSV file."""
    if not data:
        return
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


def main():
    """Main demo function."""
    print("=" * 70)
    print("Demo Mode: Multi-Symbol Data Fetcher")
    print("=" * 70)
    print()
    print("ℹ️  This demo generates sample CSV files without requiring MCP/TradingView")
    print()
    
    # Configuration
    symbols_config = [
        ("MSFT", 425.50),
        ("AAPL", 185.75),
        ("TSLA", 245.30)
    ]
    
    # Create DataTV folder
    data_folder = Path(__file__).parent / "DataTV"
    data_folder.mkdir(exist_ok=True)
    print(f"✓ Data folder created: {data_folder}")
    print()
    
    # Process each symbol
    created_files = []
    
    for i, (symbol, base_price) in enumerate(symbols_config, 1):
        print(f"[{i}/{len(symbols_config)}] Generating {symbol} data")
        print("-" * 50)
        
        # Generate sample data
        print(f"  → Generating 20 candles with EMA indicators...")
        data = generate_sample_data(symbol, base_price, num_candles=20)
        
        # Display summary
        latest = data[-1]
        print(f"  ✓ Data generated")
        print(f"    - Latest Price: ${latest['close']:.2f}")
        print(f"    - Latest Volume: {latest['volume']:,}")
        print(f"    - EMA(20): ${latest['ema_20']:.2f}")
        print(f"    - EMA(50): ${latest['ema_50']:.2f}")
        
        # Calculate price change
        first_price = data[0]['open']
        last_price = data[-1]['close']
        change_pct = ((last_price - first_price) / first_price) * 100
        change_symbol = "▲" if change_pct >= 0 else "▼"
        print(f"    - Change: {change_symbol} {change_pct:+.2f}%")
        
        # Save to CSV
        csv_filename = data_folder / f"{symbol}_5m_ema.csv"
        save_to_csv(data, csv_filename)
        
        file_size = csv_filename.stat().st_size
        print(f"  ✓ Saved to: {csv_filename.name} ({file_size:,} bytes)")
        print()
        
        created_files.append((csv_filename.name, file_size, len(data)))
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✓ Successfully created {len(created_files)} CSV files:")
    for filename, size, rows in created_files:
        print(f"  • {filename} ({size:,} bytes, {rows} rows)")
    print()
    print(f"Data folder: {data_folder.absolute()}")
    print()
    
    # Show sample from first file
    if created_files:
        sample_file = data_folder / created_files[0][0]
        print("📊 Sample data from", created_files[0][0])
        print("-" * 70)
        
        with open(sample_file, 'r') as f:
            lines = f.readlines()[:4]  # Header + 3 rows
            for line in lines:
                print("   ", line.rstrip())
        
        print()
        print("💡 Tip: Open the CSV files in Excel or use pandas to analyze:")
        print("   import pandas as pd")
        print(f"   df = pd.read_csv('{sample_file}')")
        print("   print(df.head())")
        print()


if __name__ == "__main__":
    main()
