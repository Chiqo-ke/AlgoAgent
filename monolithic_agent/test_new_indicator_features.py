"""
Test script for new indicator features
========================================
Tests validation, multi-period support, and dynamic indicators
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from Backtest.data_loader import load_market_data, validate_indicator_requests
from Data import registry
import logging

logging.basicConfig(level=logging.INFO)

print("=" * 70)
print("Testing New Indicator Features")
print("=" * 70)

# Test 1: List available indicators
print("\n1. Available Indicators:")
indicators = registry.list_indicators()
print(f"   Total: {len(indicators)} indicators")
print(f"   Sample: {', '.join(indicators[:20])}")

# Test 2: Validation - Invalid indicator name
print("\n2. Testing Validation - Invalid Indicator Name:")
invalid_request = {'SMA_SLOW': {'timeperiod': 50}}
is_valid, errors = validate_indicator_requests(invalid_request)
print(f"   Valid: {is_valid}")
if errors:
    for err in errors:
        print(f"   Error: {err}")

# Test 3: Validation - Duplicate base names
print("\n3. Testing Validation - Duplicate Base Names:")
duplicate_request = {
    'SMA': {'timeperiod': 20},
    'sma': {'timeperiod': 50}  # Lowercase, but same base name
}
# Note: Python dict will only keep one, but let's test anyway
test_dict = {'SMA_20': {}, 'SMA_50': {}}
is_valid, errors = validate_indicator_requests(test_dict)
print(f"   Valid: {is_valid}")
if errors:
    for err in errors:
        print(f"   Error: {err}")

# Test 4: Multi-period support
print("\n4. Testing Multi-Period Support:")
print("   Loading AAPL data with SMA[20, 50, 200]...")
try:
    df, metadata = load_market_data(
        ticker='AAPL',
        indicators={
            'SMA': {'periods': [20, 50, 200]},
            'EMA': {'periods': [12, 26]},
            'RSI': {'timeperiod': 14}
        },
        period='3mo',
        interval='1d',
        use_cache=False
    )
    
    print(f"   ✓ Success! Loaded {len(df)} rows")
    print(f"   Columns: {list(df.columns)}")
    
    # Check that all expected columns are present
    expected_cols = ['SMA_20', 'SMA_50', 'SMA_200', 'EMA_12', 'EMA_26', 'RSI_14']
    for col in expected_cols:
        if col in df.columns:
            print(f"   ✓ {col} present")
        else:
            print(f"   ✗ {col} MISSING!")
    
    print(f"\n   Last 5 rows:")
    print(df[['Close'] + expected_cols].tail())
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Dynamic indicator (one not manually defined)
print("\n5. Testing Dynamic Indicator (WILLR - Williams %R):")
try:
    df, metadata = load_market_data(
        ticker='MSFT',
        indicators={
            'WILLR': {'timeperiod': 14},  # This is dynamically loaded
            'MOM': {'timeperiod': 10}     # Momentum - also dynamic
        },
        period='1mo',
        interval='1d',
        use_cache=False
    )
    
    print(f"   ✓ Success! Loaded {len(df)} rows")
    print(f"   Columns: {list(df.columns)}")
    
    if 'WILLR_14' in df.columns:
        print(f"   ✓ WILLR_14 present (dynamic indicator working!)")
        print(f"   Sample values: {df['WILLR_14'].tail().values}")
    
    if 'MOM_10' in df.columns:
        print(f"   ✓ MOM_10 present (dynamic indicator working!)")
        print(f"   Sample values: {df['MOM_10'].tail().values}")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("✓ All tests completed!")
print("=" * 70)
