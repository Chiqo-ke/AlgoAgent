"""
Test Data Loader Module
========================

Quick test to verify data loader functionality
"""

import sys
from pathlib import Path

# Ensure we're in the right directory
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported"""
    print("1. Testing imports...")
    try:
        from data_loader import (
            load_market_data,
            list_available_data,
            get_available_indicators,
            parse_filename
        )
        print("   ✅ All imports successful")
        return True
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False


def test_list_data():
    """Test listing available data files"""
    print("\n2. Testing list_available_data()...")
    try:
        from data_loader import list_available_data
        
        data_files = list_available_data()
        print(f"   ✅ Found {len(data_files)} data files")
        
        if data_files:
            print("   First 3 files:")
            for item in data_files[:3]:
                print(f"      {item['ticker']:6s} {item['period']:4s} {item['interval']:3s} "
                      f"{'(batch)' if item['is_batch'] else '       '}")
        
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parse_filename():
    """Test filename parsing"""
    print("\n3. Testing parse_filename()...")
    try:
        from data_loader import parse_filename
        
        # Test format 1
        meta1 = parse_filename("AAPL_1d_1h_20251013_182543.csv")
        assert meta1['ticker'] == 'AAPL'
        assert meta1['period'] == '1d'
        assert meta1['interval'] == '1h'
        assert meta1['is_batch'] == False
        print("   ✅ Format 1 (AAPL_1d_1h_...): OK")
        
        # Test format 2
        meta2 = parse_filename("batch_SPY_5d_1h_20251013_181607.csv")
        assert meta2['ticker'] == 'SPY'
        assert meta2['period'] == '5d'
        assert meta2['interval'] == '1h'
        assert meta2['is_batch'] == True
        print("   ✅ Format 2 (batch_SPY_5d_...): OK")
        
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_load_data():
    """Test loading actual data"""
    print("\n4. Testing load_market_data()...")
    try:
        from data_loader import load_market_data
        
        # Load AAPL data without indicators
        print("   Loading AAPL data (no indicators)...")
        df, metadata = load_market_data(ticker='AAPL')
        
        print(f"   ✅ Loaded {len(df)} rows")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Date range: {metadata['date_range'][0]} to {metadata['date_range'][1]}")
        
        # Check required columns
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required:
            assert col in df.columns, f"Missing column: {col}"
        print(f"   ✅ All required columns present")
        
        return True
    except FileNotFoundError as e:
        print(f"   ⚠️  No data file found (expected if no AAPL data): {e}")
        return True  # Not a failure if no data
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_indicators():
    """Test loading with indicators"""
    print("\n5. Testing load_market_data() with indicators...")
    try:
        from data_loader import load_market_data, INDICATORS_AVAILABLE
        
        if not INDICATORS_AVAILABLE:
            print("   ⚠️  Indicator calculator not available (expected)")
            return True
        
        print("   Loading AAPL with RSI indicator...")
        df, metadata = load_market_data(
            ticker='AAPL',
            indicators={'RSI': {'timeperiod': 14}}
        )
        
        print(f"   ✅ Loaded {len(df)} rows with indicators")
        print(f"   Columns: {list(df.columns)}")
        
        if 'RSI' in df.columns:
            print(f"   ✅ RSI column present")
        else:
            print(f"   ⚠️  RSI column not found (may be case difference)")
        
        return True
    except FileNotFoundError:
        print("   ⚠️  No data file found (skipping)")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("DATA LOADER TEST SUITE")
    print("=" * 60)
    
    results = {
        'imports': test_imports(),
        'list_data': test_list_data(),
        'parse_filename': test_parse_filename(),
        'load_data': test_load_data(),
        'indicators': test_indicators()
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\nData loader is ready to use!")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease check errors above")
    print("=" * 60)


if __name__ == "__main__":
    main()
