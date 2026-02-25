"""
Advanced Indicator Management Examples

This module demonstrates:
1. Adding indicators with custom parameters
2. Modifying indicator parameters after adding
3. Removing indicators from the chart
4. Managing multiple indicators

Requirements:
- Chrome browser with TradingView open
- MCP Chrome server running
"""

import time


def example_1_basic_indicator_removal():
    """Example: Add and remove indicators."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Indicator Add/Remove")
    print("="*70 + "\n")
    
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    
    scraper = MCPTradingViewScraper()
    
    # Add RSI indicator
    print("Step 1: Adding RSI indicator...")
    scraper.add_indicator("RSI")
    time.sleep(2)
    
    # Add MACD indicator
    print("\nStep 2: Adding MACD indicator...")
    scraper.add_indicator("MACD")
    time.sleep(2)
    
    # Remove RSI
    print("\nStep 3: Removing RSI indicator...")
    scraper.remove_indicator("RSI")
    time.sleep(1)
    
    # Remove MACD
    print("\nStep 4: Removing MACD indicator...")
    scraper.remove_indicator("MACD")
    
    print("\n✅ Example complete!")


def example_2_custom_parameters():
    """Example: Add indicators with custom parameters."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Indicators with Custom Parameters")
    print("="*70 + "\n")
    
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    
    scraper = MCPTradingViewScraper()
    
    # RSI with custom period
    print("Step 1: Adding RSI with period 21 (instead of default 14)...")
    scraper.add_indicator("RSI", parameters={"length": 21})
    time.sleep(2)
    
    # EMA with custom length
    print("\nStep 2: Adding EMA with length 50...")
    scraper.add_indicator("EMA", parameters={"length": 50})
    time.sleep(2)
    
    # EMA with different length
    print("\nStep 3: Adding another EMA with length 200...")
    scraper.add_indicator("EMA", parameters={"length": 200})
    time.sleep(2)
    
    # Bollinger Bands with custom parameters
    print("\nStep 4: Adding Bollinger Bands with custom settings...")
    scraper.add_indicator("Bollinger Bands", parameters={
        "length": 20,
        "multiplier": 2.5
    })
    
    print("\n✅ Example complete!")


def example_3_reconfigure_indicator():
    """Example: Modify indicator parameters after adding."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Reconfiguring Indicator Parameters")
    print("="*70 + "\n")
    
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    
    scraper = MCPTradingViewScraper()
    
    # Add RSI with default settings
    print("Step 1: Adding RSI with default settings (14)...")
    scraper.add_indicator("RSI")
    time.sleep(2)
    
    # Reconfigure to use period 21
    print("\nStep 2: Reconfiguring RSI to period 21...")
    scraper.configure_indicator("RSI", {"length": 21})
    time.sleep(1)
    
    # Reconfigure with different source
    print("\nStep 3: Changing RSI source to hl2...")
    scraper.configure_indicator("RSI", {
        "length": 21,
        "source": "hl2"
    })
    
    print("\n✅ Example complete!")


def example_4_indicator_cycling():
    """Example: Cycle through different indicator configurations."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Indicator Configuration Cycling")
    print("="*70 + "\n")
    
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    
    scraper = MCPTradingViewScraper()
    
    # Test different RSI periods
    rsi_periods = [7, 14, 21, 30]
    
    for period in rsi_periods:
        print(f"\nTesting RSI with period {period}...")
        
        # Add with specific period
        scraper.add_indicator("RSI", parameters={"length": period})
        time.sleep(2)
        
        # Extract data to see values
        data = scraper.get_market_data()
        print(f"   Symbol: {data.get('symbol')}")
        print(f"   Close: {data['ohlc'].get('close')}")
        
        # Remove before adding next one
        scraper.remove_indicator("RSI")
        time.sleep(1)
    
    print("\n✅ Example complete!")


def example_5_multiple_indicator_management():
    """Example: Manage multiple indicators together."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Multiple Indicator Management")
    print("="*70 + "\n")
    
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    
    scraper = MCPTradingViewScraper()
    
    # Define indicator setup
    indicators_to_add = [
        {"name": "RSI", "params": {"length": 14}},
        {"name": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}},
        {"name": "EMA", "params": {"length": 20}},
        {"name": "EMA", "params": {"length": 50}},
        {"name": "Volume", "params": {}}
    ]
    
    # Add all indicators
    print("Adding all indicators...")
    for ind in indicators_to_add:
        print(f"\n   Adding {ind['name']} with params {ind['params']}...")
        scraper.add_indicator(ind['name'], parameters=ind['params'])
        time.sleep(1.5)
    
    print(f"\n✅ Added {len(indicators_to_add)} indicators")
    
    # Extract data with all indicators
    print("\nExtracting data with all indicators...")
    data = scraper.get_market_data()
    scraper.print_summary(data)
    
    # Remove all indicators
    print("\nRemoving all indicators...")
    for ind in indicators_to_add:
        print(f"   Removing {ind['name']}...")
        scraper.remove_indicator(ind['name'])
        time.sleep(0.5)
    
    print("\n✅ Example complete!")


def example_6_parameter_comparison():
    """Example: Compare different parameter settings."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Parameter Comparison Analysis")
    print("="*70 + "\n")
    
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    import json
    
    scraper = MCPTradingViewScraper()
    
    # Change to a specific symbol
    scraper.change_symbol("AAPL")
    scraper.change_timeframe("1h")
    
    results = []
    
    # Test RSI with different parameters
    test_configs = [
        {"length": 7, "source": "close"},
        {"length": 14, "source": "close"},
        {"length": 21, "source": "close"},
        {"length": 14, "source": "hl2"},
        {"length": 14, "source": "hlc3"}
    ]
    
    for config in test_configs:
        print(f"\nTesting RSI: length={config['length']}, source={config['source']}")
        
        # Add indicator with config
        scraper.add_indicator("RSI", parameters=config)
        time.sleep(2)
        
        # Extract data
        data = scraper.get_market_data()
        
        # Store result
        result = {
            "config": config,
            "price": data['ohlc']['close'],
            "timestamp": data['timestamp']
        }
        results.append(result)
        
        print(f"   Price: ${data['ohlc']['close']:.2f}")
        
        # Remove before next test
        scraper.remove_indicator("RSI")
        time.sleep(1)
    
    # Save comparison results
    with open('rsi_parameter_comparison.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Tested {len(test_configs)} configurations")
    print("   Results saved to: rsi_parameter_comparison.json")


def example_7_advanced_ema_strategy():
    """Example: Multi-EMA crossover setup."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Multi-EMA Crossover Strategy Setup")
    print("="*70 + "\n")
    
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    
    scraper = MCPTradingViewScraper()
    
    # Setup chart
    scraper.change_symbol("BTCUSD")
    scraper.change_timeframe("5m")
    
    # Add multiple EMAs for crossover strategy
    ema_periods = [9, 21, 50, 100, 200]
    
    print("Setting up multi-EMA crossover strategy...")
    print(f"Periods: {ema_periods}\n")
    
    for period in ema_periods:
        print(f"   Adding EMA({period})...")
        scraper.add_indicator("EMA", parameters={"length": period})
        time.sleep(1)
    
    print("\n✅ Strategy setup complete!")
    print(f"   Symbol: BTCUSD")
    print(f"   Timeframe: 5m")
    print(f"   EMAs: {', '.join(map(str, ema_periods))}")
    
    # Extract and save data
    data = scraper.get_market_data()
    filename = scraper.save_data(data, format='json')
    print(f"\n   Data saved to: {filename}")


def example_8_indicator_cleanup():
    """Example: Clean up all indicators from chart."""
    print("\n" + "="*70)
    print("EXAMPLE 8: Remove All Indicators")
    print("="*70 + "\n")
    
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    
    scraper = MCPTradingViewScraper()
    
    # Show current indicators
    if scraper.active_indicators:
        print(f"Current indicators ({len(scraper.active_indicators)}):")
        for ind in scraper.active_indicators:
            print(f"   • {ind['name']} - {ind.get('parameters', {})}")
        
        print(f"\nRemoving all {len(scraper.active_indicators)} indicators...\n")
        
        # Remove all
        indicators_to_remove = list(scraper.active_indicators)  # Copy list
        for ind in indicators_to_remove:
            print(f"   Removing {ind['name']}...")
            scraper.remove_indicator(ind['name'])
            time.sleep(0.5)
        
        print("\n✅ All indicators removed!")
    else:
        print("No indicators to remove.")


# Menu system
def show_menu():
    """Display example menu."""
    print("\n" + "="*70)
    print(" "*15 + "INDICATOR MANAGEMENT EXAMPLES")
    print("="*70)
    print("\n1. Basic Add/Remove")
    print("2. Custom Parameters")
    print("3. Reconfigure Indicator")
    print("4. Indicator Cycling")
    print("5. Multiple Indicator Management")
    print("6. Parameter Comparison")
    print("7. Advanced EMA Strategy")
    print("8. Remove All Indicators")
    print("0. Exit")
    print("\n" + "="*70)


if __name__ == "__main__":
    import sys
    
    # Command line argument handling
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        
        examples = {
            "1": example_1_basic_indicator_removal,
            "2": example_2_custom_parameters,
            "3": example_3_reconfigure_indicator,
            "4": example_4_indicator_cycling,
            "5": example_5_multiple_indicator_management,
            "6": example_6_parameter_comparison,
            "7": example_7_advanced_ema_strategy,
            "8": example_8_indicator_cleanup
        }
        
        if example_num in examples:
            examples[example_num]()
        else:
            print(f"Unknown example: {example_num}")
            print("Valid options: 1-8")
    else:
        # Interactive menu
        while True:
            show_menu()
            choice = input("\nEnter your choice: ").strip()
            
            if choice == "0":
                print("\nGoodbye!")
                break
            elif choice == "1":
                example_1_basic_indicator_removal()
            elif choice == "2":
                example_2_custom_parameters()
            elif choice == "3":
                example_3_reconfigure_indicator()
            elif choice == "4":
                example_4_indicator_cycling()
            elif choice == "5":
                example_5_multiple_indicator_management()
            elif choice == "6":
                example_6_parameter_comparison()
            elif choice == "7":
                example_7_advanced_ema_strategy()
            elif choice == "8":
                example_8_indicator_cleanup()
            else:
                print("\n❌ Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")
