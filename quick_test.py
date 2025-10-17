#!/usr/bin/env python3
"""Simple end-to-end test of the AlgoAgent system"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Data'))

from Data.main import DataIngestionModel

print("="*60)
print(" ALGOAGENT END-TO-END TEST")
print("="*60)

# Initialize model
print("\n1. Initializing DataIngestionModel...")
model = DataIngestionModel()
print("   ✅ Model initialized")

# Test with simple indicator
print("\n2. Fetching SPY data with SMA indicator...")
df = model.ingest_and_process(
    ticker="SPY",
    required_indicators=[{"name": "SMA", "timeperiod": 20}],
    period="5d",
    interval="1d"
)

print(f"   ✅ Data fetched: {df.shape[0]} rows × {df.shape[1]} columns")
print(f"   📊 Columns: {list(df.columns)}")

if 'SMA_20' in df.columns:
    print(f"   ✅ SMA indicator calculated successfully!")
    print(f"   Latest SMA value: {df['SMA_20'].iloc[-1]:.2f}")
else:
    print(f"   ❌ SMA indicator not found in columns")

print(f"\n{'='*60}")
print(" TEST COMPLETE")
print(f"{'='*60}\n")
