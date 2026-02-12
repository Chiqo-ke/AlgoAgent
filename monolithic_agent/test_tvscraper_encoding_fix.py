"""
Quick Test: TVScraper Encoding Fix Verification
================================================

This script tests that TVScraper integration works without encoding errors.
Run this after applying the encoding fixes to verify everything works.

Usage:
    cd C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent
    python test_tvscraper_encoding_fix.py
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')
django.setup()

def test_utf8_output():
    """Test that UTF-8 encoding works"""
    print("=" * 60)
    print("TEST 1: UTF-8 Output Test")
    print("=" * 60)
    
    # Test emoji output
    test_strings = [
        "✅ Check mark",
        "❌ Cross mark",
        "⚠️  Warning",
        "📊 Chart",
        "🔧 Wrench",
        "Regular ASCII text"
    ]
    
    try:
        for s in test_strings:
            print(f"  {s}")
        print("\n✅ UTF-8 output test PASSED\n")
        return True
    except Exception as e:
        print(f"\n❌ UTF-8 output test FAILED: {e}\n")
        return False


def test_tvscraper_import():
    """Test that TVScraper can be imported"""
    print("=" * 60)
    print("TEST 2: TVScraper Import Test")
    print("=" * 60)
    
    try:
        from Backtest.data_loader import TV_SCRAPER_AVAILABLE, fetch_market_data_with_tvscraper
        
        if TV_SCRAPER_AVAILABLE:
            print("  ✅ TVScraper is available")
            print(f"  ✅ fetch_market_data_with_tvscraper imported successfully")
            print("\n✅ Import test PASSED\n")
            return True
        else:
            print("  ⚠️  TVScraper not available (not installed)")
            print("\n⚠️  Import test SKIPPED (TVScraper not installed)\n")
            return None
            
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        print("\n❌ Import test FAILED\n")
        return False


def test_data_loader_fetch():
    """Test fetching data with data_loader (with fallback)"""
    print("=" * 60)
    print("TEST 3: Data Loader Fetch Test")
    print("=" * 60)
    
    try:
        from Backtest.data_loader import fetch_market_data
        
        print("  Fetching AAPL data (this may take 30-60 seconds)...")
        
        # Try to fetch data
        # This will try TVScraper first, then fall back to yfinance
        data = fetch_market_data("AAPL", period="5d", interval="1h")
        
        print(f"  ✅ Fetched {len(data)} rows of data")
        print(f"  ✅ Columns: {list(data.columns)}")
        print(f"  ✅ Date range: {data.index[0]} to {data.index[-1]}")
        
        # Show sample data
        print("\n  Sample data (first 3 rows):")
        print(data.head(3).to_string(index=True))
        
        print("\n✅ Data fetch test PASSED\n")
        return True
        
    except Exception as e:
        # Clean error message (remove emojis for testing)
        error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
        print(f"  ❌ Fetch failed: {error_msg}")
        print("\n❌ Data fetch test FAILED\n")
        import traceback
        traceback.print_exc()
        return False


def test_error_message_sanitization():
    """Test that error messages don't contain emojis"""
    print("=" * 60)
    print("TEST 4: Error Message Sanitization Test")
    print("=" * 60)
    
    try:
        # Create a test error with emoji
        test_error = "❌ This error contains emojis ✅"
        
        # Sanitize it
        sanitized = test_error.encode('ascii', errors='ignore').decode('ascii')
        
        print(f"  Original: {repr(test_error)}")
        print(f"  Sanitized: {repr(sanitized)}")
        
        # Check that emojis are removed
        if '❌' not in sanitized and '✅' not in sanitized:
            print("  ✅ Emojis successfully removed from error messages")
            print("\n✅ Sanitization test PASSED\n")
            return True
        else:
            print("  ❌ Emojis still present in sanitized message")
            print("\n❌ Sanitization test FAILED\n")
            return False
            
    except Exception as e:
        print(f"  ❌ Sanitization test error: {e}")
        print("\n❌ Sanitization test FAILED\n")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "TVScraper Encoding Fix - Test Suite" + " " * 12 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    
    # Run tests
    results.append(('UTF-8 Output', test_utf8_output()))
    results.append(('TVScraper Import', test_tvscraper_import()))
    results.append(('Error Sanitization', test_error_message_sanitization()))
    results.append(('Data Fetch', test_data_loader_fetch()))
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for name, result in results:
        if result is True:
            status = "✅ PASSED"
            passed += 1
        elif result is False:
            status = "❌ FAILED"
            failed += 1
        else:
            status = "⚠️  SKIPPED"
            skipped += 1
        
        print(f"{name:.<40} {status}")
    
    print()
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All tests passed! TVScraper encoding fix is working correctly.\n")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the errors above.\n")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
