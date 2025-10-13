#!/usr/bin/env python3
"""
AlgoAgent Interactive System Test
=================================

This script allows you to test the main AlgoAgent system with custom parameters:
- Enter security symbol, interval, and period
- Choose technical indicators to compute
- Save results to CSV file

Usage:
    python interactive_test.py
"""

from __future__ import annotations
import os
from pathlib import Path
import sys
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

# Add Data directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Data'))
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "Data"
sys.path.insert(0, str(DATA_DIR))

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print formatted section"""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")

def get_user_input():
    """Get user input for testing parameters"""
    print_header("ALGOAGENT INTERACTIVE SYSTEM TEST")
    
    # Get security symbol
    print("\n📈 Security Symbol:")
    print("Examples: AAPL, GOOGL, MSFT, TSLA, SPY, QQQ")
    symbol = input("Enter symbol: ").strip().upper()
    
    if not symbol:
        symbol = "AAPL"
        print(f"Using default: {symbol}")
    
    # Get time period
    print_section("Time Period")
    print("Examples: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max")
    period = input("Enter period (default: 1mo): ").strip()
    
    if not period:
        period = "1mo"
    
    # Get interval
    print_section("Data Interval")
    print("Valid intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo")
    print("Note: Minute intervals only work with periods <= 60 days")
    interval = input("Enter interval (default: 1d): ").strip()
    
    if not interval:
        interval = "1d"
    
    # Get indicators
    print_section("Technical Indicators")
    print("Available indicators:")
    available_indicators = [
        "SMA (Simple Moving Average)",
        "EMA (Exponential Moving Average)", 
        "RSI (Relative Strength Index)",
        "MACD (Moving Average Convergence Divergence)",
        "BOLLINGER (Bollinger Bands)",
        "ADX (Average Directional Index)",
        "ATR (Average True Range)",
        "STOCH (Stochastic Oscillator)",
        "CCI (Commodity Channel Index)",
        "OBV (On Balance Volume)",
        "SAR (Parabolic SAR)",
        "VWAP (Volume Weighted Average Price)"
    ]
    
    for i, indicator in enumerate(available_indicators, 1):
        print(f"{i:2d}. {indicator}")
    
    print("\nChoose indicators (comma-separated numbers, e.g., 1,3,4):")
    print("Or press Enter for default set (SMA, RSI, MACD)")
    choice = input("Your choice: ").strip()
    
    # Parse indicator choices
    selected_indicators = []
    if not choice:
        # Default indicators
        selected_indicators = [
            {"name": "SMA", "timeperiod": 20},
            {"name": "RSI", "timeperiod": 14},
            {"name": "MACD", "fastperiod": 12, "slowperiod": 26, "signalperiod": 9}
        ]
    else:
        try:
            choices = [int(x.strip()) for x in choice.split(',')]
            indicator_mapping = {
                1: {"name": "SMA", "timeperiod": 20},
                2: {"name": "EMA", "timeperiod": 20},
                3: {"name": "RSI", "timeperiod": 14},
                4: {"name": "MACD", "fastperiod": 12, "slowperiod": 26, "signalperiod": 9},
                5: {"name": "BOLLINGER", "timeperiod": 20, "nbdevup": 2, "nbdevdn": 2},
                6: {"name": "ADX", "timeperiod": 14},
                7: {"name": "ATR", "timeperiod": 14},
                8: {"name": "STOCH", "fastk_period": 5, "slowk_period": 3, "slowd_period": 3},
                9: {"name": "CCI", "timeperiod": 14},
                10: {"name": "OBV"},
                11: {"name": "SAR", "acceleration": 0.02, "maximum": 0.2},
                12: {"name": "VWAP"}
            }
            
            for num in choices:
                if 1 <= num <= 12:
                    selected_indicators.append(indicator_mapping[num])
                else:
                    print(f"Warning: Invalid choice {num} ignored")
        except ValueError:
            print("Invalid input, using default indicators")
            selected_indicators = [
                {"name": "SMA", "timeperiod": 20},
                {"name": "RSI", "timeperiod": 14},
                {"name": "MACD", "fastperiod": 12, "slowperiod": 26, "signalperiod": 9}
            ]
    
    return symbol, period, interval, selected_indicators

def run_system_test():
    """Run the actual system test"""
    try:
        # Import the main system
        from main import DataIngestionModel
        
        # Get user parameters
        symbol, period, interval, indicators = get_user_input()
        
        print_header("RUNNING SYSTEM TEST")
        print(f"Symbol: {symbol}")
        print(f"Period: {period}")
        print(f"Interval: {interval}")
        print(f"Indicators: {[ind['name'] for ind in indicators]}")
        
        # Initialize the model
        print(f"\n🔧 Initializing AlgoAgent DataIngestionModel...")
        model = DataIngestionModel()
        
        # Process the data
        print(f"📊 Fetching data and computing indicators...")
        df = model.ingest_and_process(
            ticker=symbol,
            required_indicators=indicators,
            period=period,
            interval=interval
        )
        
        # Display results
        print_section("DATA PROCESSING RESULTS")
        print(f"Data shape: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"Date range: {df.index[0]} to {df.index[-1]}")
        print(f"Columns: {list(df.columns)}")
        
        # Show sample data
        print(f"\nFirst 5 rows:")
        print(df.head().to_string())
        
        print(f"\nLast 5 rows:")
        print(df.tail().to_string())
        
        # Save to CSV in data folder
        output_dir = SCRIPT_DIR / "data"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol}_{period}_{interval}_{timestamp}.csv"
        filepath = output_dir / filename
        
        print_section("SAVING DATA")
        df.to_csv(filepath)
        print(f"✅ Data saved to: {filepath}")
        print(f"📁 File size: {os.path.getsize(filepath)} bytes")
        
        # Summary statistics
        print_section("SUMMARY STATISTICS")
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            print("Basic statistics for numeric columns:")
            print(df[numeric_cols].describe().round(2))
        
        print_section("TEST COMPLETED SUCCESSFULLY")
        print(f"✅ System test passed!")
        print(f"📁 Results saved in: {filepath}")
        print(f"🎯 AlgoAgent main system is working correctly!")
        
        return True, filepath
        
    except Exception as e:
        print(f"\n❌ System test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    """Main function"""
    print("Starting AlgoAgent Interactive System Test...")
        
    success, filename = run_system_test()
    
    if success:
        print(f"\n🎉 Test completed successfully!")
        print(f"Check your CSV file: {filename}")
    else:
        print(f"\n💥 Test failed. Check the error messages above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())