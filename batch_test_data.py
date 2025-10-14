#!/usr/bin/env python3
"""
AlgoAgent Batch System Test
===========================

Quick batch testing script for multiple scenarios.
Saves all results to CSV files with timestamps.

Usage:
    python batch_test.py
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Add Data directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Data'))

def run_batch_tests():
    """Run predefined batch tests"""
    
    # Change to Data directory
    os.chdir(os.path.join(os.path.dirname(__file__), 'Data'))
    
    from main import DataIngestionModel
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Daily AAPL with Basic Indicators",
            "symbol": "AAPL",
            "period": "1mo",
            "interval": "1d",
            "indicators": [
                {"name": "SMA", "timeperiod": 20},
                {"name": "RSI", "timeperiod": 14}
            ]
        },
        {
            "name": "Hourly SPY with MACD",
            "symbol": "SPY", 
            "period": "5d",
            "interval": "1h",
            "indicators": [
                {"name": "MACD", "fastperiod": 12, "slowperiod": 26, "signalperiod": 9},
                {"name": "SMA", "timeperiod": 10}
            ]
        },
        {
            "name": "Daily TSLA with Advanced Indicators",
            "symbol": "TSLA",
            "period": "3mo", 
            "interval": "1d",
            "indicators": [
                {"name": "RSI", "timeperiod": 14},
                {"name": "BOLLINGER", "timeperiod": 20, "nbdevup": 2, "nbdevdn": 2},
                {"name": "ATR", "timeperiod": 14}
            ]
        }
    ]
    
    print("="*60)
    print(" ALGOAGENT BATCH SYSTEM TEST")
    print("="*60)
    
    model = DataIngestionModel()
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n[Test {i}/3] {scenario['name']}")
        print("-" * 50)
        
        try:
            # Run the test
            df = model.ingest_and_process(
                ticker=scenario['symbol'],
                required_indicators=scenario['indicators'],
                period=scenario['period'],
                interval=scenario['interval']
            )
            
            # Create data directory and filename
            data_dir = "data"
            os.makedirs(data_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"batch_{scenario['symbol']}_{scenario['period']}_{scenario['interval']}_{timestamp}.csv"
            filepath = os.path.join(data_dir, filename)
            
            # Save to CSV
            df.to_csv(filepath)
            
            # Results
            print(f"✅ Success!")
            print(f"   Data shape: {df.shape[0]} rows × {df.shape[1]} columns")
            print(f"   Date range: {df.index[0].date()} to {df.index[-1].date()}")
            print(f"   Saved to: {filepath}")
            
            results.append({
                "test": scenario['name'],
                "status": "SUCCESS",
                "rows": df.shape[0],
                "columns": df.shape[1],
                "filename": filepath
            })
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            results.append({
                "test": scenario['name'],
                "status": "FAILED",
                "error": str(e),
                "filename": None
            })
    
    # Summary
    print("\n" + "="*60)
    print(" BATCH TEST SUMMARY")
    print("="*60)
    
    successful = sum(1 for r in results if r['status'] == 'SUCCESS')
    total = len(results)
    
    print(f"Tests completed: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    
    print(f"\nDetailed Results:")
    for result in results:
        status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
        print(f"{status_icon} {result['test']}")
        if result['status'] == 'SUCCESS':
            print(f"     Rows: {result['rows']}, Columns: {result['columns']}")
            print(f"     File: {result['filename']}")
        else:
            print(f"     Error: {result.get('error', 'Unknown error')}")
    
    if successful == total:
        print(f"\n🎉 All tests passed! AlgoAgent system is working perfectly!")
    else:
        print(f"\n⚠️  {total - successful} test(s) failed. Check errors above.")
    
    return successful == total

if __name__ == "__main__":
    success = run_batch_tests()
    sys.exit(0 if success else 1)