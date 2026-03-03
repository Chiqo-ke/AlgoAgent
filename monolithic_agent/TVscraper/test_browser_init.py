"""
Simple test to verify browser initialization and TradingView navigation.
"""
import sys
import os
import time

# Add the tvscraper module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tvscraper.mcp_scraper import MCPTradingViewScraper


def main():
    """Test browser initialization and navigation."""
    
    print("=" * 60)
    print("Browser Initialization Test")
    print("=" * 60)
    print()
    
    # Create scraper
    print("Creating scraper instance...")
    scraper = MCPTradingViewScraper()
    print("✓ Scraper created")
    print()
    
    # Test 1: Initialize browser
    print("[Test 1] Browser Initialization")
    print("-" * 60)
    if scraper.init_browser():
        print("✓ PASSED: Browser initialized successfully")
    else:
        print("✗ FAILED: Browser initialization failed")
        return
    print()
    
    # Test 2: Navigate to TradingView
    print("[Test 2] Navigate to TradingView")
    print("-" * 60)
    if scraper.navigate_to_tradingview():
        print("✓ PASSED: Successfully navigated to TradingView")
    else:
        print("✗ FAILED: Navigation failed")
        return
    print()
    
    # Wait a bit
    print("Waiting 5 seconds for page to fully load...")
    for i in range(5, 0, -1):
        print(f"  {i}...", end='\r')
        time.sleep(1)
    print("  Ready!   ")
    print()
    
    # Test 3: Change symbol
    print("[Test 3] Change Symbol")
    print("-" * 60)
    if scraper.change_symbol("AAPL"):
        print("✓ PASSED: Symbol changed to AAPL")
    else:
        print("✗ FAILED: Symbol change failed")
    print()
    
    # Test 4: Change timeframe
    print("[Test 4] Change Timeframe")
    print("-" * 60)
    if scraper.change_timeframe("5m"):
        print("✓ PASSED: Timeframe changed to 5 minutes")
    else:
        print("✗ FAILED: Timeframe change failed")
    print()
    
    # Test 5: Add indicator
    print("[Test 5] Add Indicator")
    print("-" * 60)
    if scraper.add_indicator("EMA"):
        print("✓ PASSED: EMA indicator added")
    else:
        print("✗ FAILED: Indicator add failed")
    print()
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
    print()
    print("Press Enter to close browser and exit...")
    input()
    
    # Cleanup
    print("\nCleaning up...")
    scraper.close_browser()
    print("✓ Browser closed")
    print("✓ Test completed successfully")


if __name__ == "__main__":
    main()
