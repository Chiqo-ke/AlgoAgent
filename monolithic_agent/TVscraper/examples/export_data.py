"""
Data Export Examples - TradingView Scraper
Demonstrates various ways to save scraped data
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from demo import CompleteTVScraper
import time


def example_1_save_json():
    """Save data as JSON to default location."""
    print("\n" + "="*70)
    print("Example 1: Save as JSON (Default Location)")
    print("="*70)
    
    scraper = CompleteTVScraper()
    data = scraper.extract_market_data()
    
    # Save to default exports folder
    filepath = scraper.save_data(data, format='json')
    print(f"✅ Saved to: {filepath}")


def example_2_save_csv():
    """Save data as CSV to custom location."""
    print("\n" + "="*70)
    print("Example 2: Save as CSV (Custom Location)")
    print("="*70)
    
    scraper = CompleteTVScraper()
    data = scraper.extract_market_data()
    
    # Save to custom path
    custom_path = "C:/Users/nyaga/Documents/TVscraper/my_data/eurusd_data.csv"
    filepath = scraper.save_data(data, filepath=custom_path, format='csv')
    print(f"✅ Saved to: {filepath}")


def example_3_save_excel():
    """Save data as Excel file."""
    print("\n" + "="*70)
    print("Example 3: Save as Excel")
    print("="*70)
    
    scraper = CompleteTVScraper()
    data = scraper.extract_market_data()
    
    # Save as Excel
    filepath = scraper.save_data(data, format='xlsx')
    print(f"✅ Saved to: {filepath}")
    print("📊 Open in Excel to view formatted data")


def example_4_append_csv():
    """Append multiple data points to same CSV file."""
    print("\n" + "="*70)
    print("Example 4: Append Multiple Data Points to CSV")
    print("="*70)
    
    scraper = CompleteTVScraper()
    csv_file = "exports/eurusd_continuous.csv"
    
    print(f"Collecting data every 10 seconds...")
    print(f"Target file: {csv_file}\n")
    
    for i in range(5):
        data = scraper.extract_market_data()
        
        # Append to same file
        append_mode = i > 0  # First write creates file, rest append
        filepath = scraper.save_data(data, filepath=csv_file, format='csv', append=append_mode)
        
        print(f"📝 Entry {i+1}/5: Close={data['ohlc']['close']:.5f}")
        
        if i < 4:
            time.sleep(10)
    
    print(f"\n✅ Collected 5 data points in: {filepath}")


def example_5_multiple_timeframes():
    """Save data from multiple timeframes."""
    print("\n" + "="*70)
    print("Example 5: Save Multiple Timeframes")
    print("="*70)
    
    scraper = CompleteTVScraper()
    timeframes = ['1m', '5m', '30m', '1h']
    
    for tf in timeframes:
        print(f"\n⏱️  Fetching {tf} data...")
        scraper.change_timeframe(tf)
        time.sleep(2)  # Wait for chart to load
        
        data = scraper.extract_market_data()
        
        # Save with timeframe in filename
        filename = f"exports/eurusd_{tf}_{data['timestamp'][:10]}.json"
        filepath = scraper.save_data(data, filepath=filename, format='json')
        
        print(f"   Close: {data['ohlc']['close']:.5f}")


def example_6_organized_export():
    """Save with organized folder structure."""
    print("\n" + "="*70)
    print("Example 6: Organized Export Structure")
    print("="*70)
    
    scraper = CompleteTVScraper()
    data = scraper.extract_market_data()
    
    symbol = data['symbol']
    timeframe = data['timeframe'].replace(' ', '_')
    
    # Create organized structure: exports/SYMBOL/TIMEFRAME/date.json
    from datetime import datetime
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    organized_path = f"exports/{symbol}/{timeframe}/{date_str}.json"
    filepath = scraper.save_data(data, filepath=organized_path, format='json')
    
    print(f"📁 Organized structure created:")
    print(f"   {filepath}")


def example_7_batch_export():
    """Export data in all formats at once."""
    print("\n" + "="*70)
    print("Example 7: Batch Export (All Formats)")
    print("="*70)
    
    scraper = CompleteTVScraper()
    data = scraper.extract_market_data()
    
    symbol = data['symbol']
    
    print(f"📦 Exporting {symbol} data in all formats...\n")
    
    # Export JSON
    json_path = scraper.save_data(data, format='json')
    
    # Export CSV
    csv_path = scraper.save_data(data, format='csv')
    
    # Export Excel (if pandas installed)
    try:
        xlsx_path = scraper.save_data(data, format='xlsx')
    except ImportError:
        print("⚠️  Excel export skipped (pandas not installed)")
        xlsx_path = None
    
    print(f"\n📊 Batch export complete!")
    print(f"   JSON: {json_path}")
    print(f"   CSV:  {csv_path}")
    if xlsx_path:
        print(f"   XLSX: {xlsx_path}")


def example_8_custom_data_structure():
    """Save data with custom structure."""
    print("\n" + "="*70)
    print("Example 8: Custom Data Structure")
    print("="*70)
    
    scraper = CompleteTVScraper()
    raw_data = scraper.extract_market_data()
    
    # Create custom structure
    custom_data = {
        "metadata": {
            "symbol": raw_data['symbol'],
            "timeframe": raw_data['timeframe'],
            "timestamp": raw_data['timestamp'],
            "source": "TradingView"
        },
        "price": raw_data['ohlc'],
        "volume": raw_data.get('volume'),
        "change": raw_data.get('change'),
        "indicators": raw_data.get('indicators', [])
    }
    
    filepath = scraper.save_data(custom_data, format='json')
    print(f"✅ Custom structure saved to: {filepath}")


def run_all_examples():
    """Run all export examples."""
    print("\n" + "="*80)
    print(" "*20 + "📊 DATA EXPORT EXAMPLES 📊")
    print("="*80)
    
    examples = [
        ("Save JSON (Default)", example_1_save_json),
        ("Save CSV (Custom)", example_2_save_csv),
        ("Save Excel", example_3_save_excel),
        ("Append to CSV", example_4_append_csv),
        ("Multiple Timeframes", example_5_multiple_timeframes),
        ("Organized Structure", example_6_organized_export),
        ("Batch Export", example_7_batch_export),
        ("Custom Structure", example_8_custom_data_structure)
    ]
    
    for name, func in examples:
        try:
            func()
            print(f"\n✅ {name} - COMPLETED")
        except Exception as e:
            print(f"\n❌ {name} - ERROR: {e}")
        
        print("\n" + "-"*80)
        time.sleep(1)
    
    print("\n" + "="*80)
    print(" "*25 + "🎉 ALL EXAMPLES COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        example_map = {
            '1': example_1_save_json,
            '2': example_2_save_csv,
            '3': example_3_save_excel,
            '4': example_4_append_csv,
            '5': example_5_multiple_timeframes,
            '6': example_6_organized_export,
            '7': example_7_batch_export,
            '8': example_8_custom_data_structure
        }
        
        if example_num in example_map:
            example_map[example_num]()
        else:
            print(f"Example {example_num} not found!")
            print("Available: 1-8 or run without args for all")
    else:
        run_all_examples()
