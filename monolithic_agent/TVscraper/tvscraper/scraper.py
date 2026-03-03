"""
Main TradingView Scraper class using Chrome DevTools Protocol
"""

import time
from typing import Dict, List, Optional, Union
import json


class TradingViewScraper:
    """
    Scraper for TradingView charts using Chrome DevTools Protocol.
    
    This scraper assumes TradingView is already open in a Chrome browser
    with an active session. Manual login is required.
    """
    
    # TradingView element UIDs (based on page structure analysis)
    ELEMENTS = {
        "symbol_button": "1_2",           # Symbol search button
        "timeframe_menu": "1_10",         # Chart interval dropdown
        "indicators_button": "1_12",      # Indicators button
        "chart_canvas": "1_103",          # Chart canvas
    }
    
    # Available timeframes and their button UIDs
    TIMEFRAMES = {
        "1m": "1_5",
        "3m": "1_6", 
        "5m": "1_7",
        "30m": "1_8",
        "1h": "1_9",
        # Extended timeframes via menu:
        "1D": None,   # Accessible via timeframe menu
        "1W": None,
        "1M": None,
    }
    
    def __init__(self, page_id: Optional[int] = None):
        """
        Initialize the scraper.
        
        Args:
            page_id: Chrome DevTools page ID. If None, will use current active page.
        """
        self.page_id = page_id
        self.current_symbol = None
        self.current_timeframe = None
        self.active_indicators = []
        self._max_indicators = 2
        
    def _take_snapshot(self) -> str:
        """
        Take a snapshot of the current page state.
        Returns the snapshot text for parsing.
        """
        # This will be called via the MCP interface
        # For now, this is a placeholder that would use the MCP tools
        pass
    
    def _click_element(self, uid: str, wait_time: float = 1.0):
        """
        Click an element by its UID.
        
        Args:
            uid: Element UID from the page snapshot
            wait_time: Time to wait after clicking (seconds)
        """
        # This will be called via the MCP interface
        pass
    
    def _fill_input(self, uid: str, value: str):
        """
        Fill an input field with a value.
        
        Args:
            uid: Element UID from the page snapshot
            value: Text value to input
        """
        # This will be called via the MCP interface  
        pass
    
    def _execute_script(self, script: str) -> Dict:
        """
        Execute JavaScript on the page.
        
        Args:
            script: JavaScript code to execute
            
        Returns:
            Result of the script execution
        """
        # This will be called via the MCP interface
        pass
    
    def set_symbol(self, symbol: str) -> bool:
        """
        Change the chart symbol/security.
        
        Args:
            symbol: Symbol ticker (e.g., "AAPL", "EURUSD", "BTCUSD")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Click symbol search button
            self._click_element(self.ELEMENTS["symbol_button"])
            
            # Type symbol (need to find search input UID after click)
            # This will require taking a new snapshot after the dialog opens
            time.sleep(0.5)
            
            # Search and select symbol
            # Implementation will depend on the search dialog structure
            
            self.current_symbol = symbol
            print(f"Symbol changed to: {symbol}")
            return True
            
        except Exception as e:
            print(f"Error changing symbol: {e}")
            return False
    
    def set_timeframe(self, timeframe: str) -> bool:
        """
        Change the chart timeframe.
        
        Args:
            timeframe: Timeframe string (e.g., "1m", "5m", "1h", "1D")
            
        Returns:
            True if successful, False otherwise
        """
        if timeframe not in self.TIMEFRAMES:
            print(f"Invalid timeframe: {timeframe}")
            print(f"Available timeframes: {list(self.TIMEFRAMES.keys())}")
            return False
        
        try:
            uid = self.TIMEFRAMES[timeframe]
            
            if uid:
                # Direct button click for common timeframes
                self._click_element(uid)
            else:
                # Use dropdown menu for extended timeframes
                self._click_element(self.ELEMENTS["timeframe_menu"])
                time.sleep(0.5)
                # Select from menu (requires finding menu item UID)
                
            self.current_timeframe = timeframe
            print(f"Timeframe changed to: {timeframe}")
            return True
            
        except Exception as e:
            print(f"Error changing timeframe: {e}")
            return False
    
    def add_indicator(self, indicator_name: str, parameters: Optional[Dict] = None) -> bool:
        """
        Add an indicator to the chart.
        Maximum of 2 indicators at a time.
        
        Args:
            indicator_name: Name of the indicator (e.g., "EMA", "RSI", "MACD")
            parameters: Optional dict of indicator parameters
            
        Returns:
            True if successful, False otherwise
        """
        if len(self.active_indicators) >= self._max_indicators:
            print(f"Maximum {self._max_indicators} indicators allowed. Remove one first.")
            return False
        
        try:
            # Click indicators button
            self._click_element(self.ELEMENTS["indicators_button"])
            time.sleep(0.5)
            
            # Search and add indicator
            # Implementation depends on indicators dialog structure
            
            self.active_indicators.append({
                "name": indicator_name,
                "parameters": parameters or {}
            })
            print(f"Added indicator: {indicator_name}")
            return True
            
        except Exception as e:
            print(f"Error adding indicator: {e}")
            return False
    
    def remove_indicator(self, indicator_name: str) -> bool:
        """
        Remove an indicator from the chart.
        
        Args:
            indicator_name: Name of the indicator to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find indicator in legend and click remove button
            # Implementation depends on finding the indicator's remove button
            
            self.active_indicators = [
                i for i in self.active_indicators if i["name"] != indicator_name
            ]
            print(f"Removed indicator: {indicator_name}")
            return True
            
        except Exception as e:
            print(f"Error removing indicator: {e}")
            return False
    
    def get_market_data(self, bars: int = 100) -> Dict:
        """
        Extract OHLC market data and indicator values from the chart.
        
        Args:
            bars: Number of bars/candlesticks to retrieve
            
        Returns:
            Dictionary containing OHLC data and indicator values
        """
        try:
            # Execute JavaScript to extract chart data
            script = """
            () => {
                // Access TradingView's internal chart data
                // This will require reverse engineering TradingView's data structures
                
                const chartData = {
                    symbol: null,
                    timeframe: null,
                    ohlc: [],
                    indicators: {},
                    timestamp: new Date().toISOString()
                };
                
                // Try to extract symbol from page
                const symbolButton = document.querySelector('[data-name="legend-source-item"]');
                if (symbolButton) {
                    chartData.symbol = symbolButton.textContent.trim();
                }
                
                // Extract OHLC values from legend
                const ohlcElements = {
                    open: document.evaluate("//StaticText[contains(text(), 'O')]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue,
                    high: document.evaluate("//StaticText[contains(text(), 'H')]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue,
                    low: document.evaluate("//StaticText[contains(text(), 'L')]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue,
                    close: document.evaluate("//StaticText[contains(text(), 'C')]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue
                };
                
                // Note: This is a simplified version. 
                // Full implementation requires deeper analysis of TradingView's data layer
                
                return chartData;
            }
            """
            
            result = self._execute_script(script)
            
            return {
                "symbol": self.current_symbol,
                "timeframe": self.current_timeframe,
                "data": result,
                "indicators": self.active_indicators
            }
            
        except Exception as e:
            print(f"Error extracting market data: {e}")
            return {}
    
    def get_current_price(self) -> Optional[Dict]:
        """
        Get the current price OHLC values displayed on the chart.
        
        Returns:
            Dictionary with O, H, L, C values or None if failed
        """
        try:
            # Extract visible OHLC from the chart legend
            script = """
            () => {
                const ohlc = {
                    open: null,
                    high: null,
                    low: null,
                    close: null,
                    change: null,
                    changePercent: null
                };
                
                // Find OHLC values in the legend area
                // Based on the snapshot structure we saw earlier
                
                return ohlc;
            }
            """
            
            return self._execute_script(script)
            
        except Exception as e:
            print(f"Error getting current price: {e}")
            return None
    
    def wait_for_data_load(self, timeout: int = 10):
        """
        Wait for chart data to load after making changes.
        
        Args:
            timeout: Maximum time to wait in seconds
        """
        time.sleep(2)  # Basic wait - can be improved with proper load detection
        
    def save_data(self, data: Dict, filepath: Optional[str] = None, format: str = 'json', append: bool = False) -> str:
        """
        Save market data to file.
        
        Args:
            data: Market data dictionary to save
            filepath: Custom file path. If None, generates default path.
            format: Output format ('json', 'csv', 'xlsx')
            append: If True, append to existing file (CSV only)
            
        Returns:
            Path where file was saved
        """
        from .utils import ensure_directory_exists, get_default_export_path
        import json
        import csv
        from datetime import datetime
        
        # Generate filepath if not provided
        if not filepath:
            symbol = data.get('symbol', 'unknown')
            filepath = get_default_export_path(symbol, format)
        else:
            filepath = ensure_directory_exists(filepath)
        
        try:
            if format.lower() == 'json':
                self._save_json(data, filepath, append)
            elif format.lower() == 'csv':
                self._save_csv(data, filepath, append)
            elif format.lower() in ['xlsx', 'excel']:
                self._save_excel(data, filepath)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            print(f"✅ Data saved to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error saving data: {e}")
            raise
    
    def _save_json(self, data: Dict, filepath: str, append: bool = False):
        """Save data as JSON."""
        import json
        import os
        
        if append and os.path.exists(filepath):
            # Load existing data
            with open(filepath, 'r') as f:
                existing = json.load(f)
            
            # Append new data
            if isinstance(existing, list):
                existing.append(data)
                data_to_save = existing
            else:
                data_to_save = [existing, data]
        else:
            data_to_save = data
        
        with open(filepath, 'w') as f:
            json.dump(data_to_save, f, indent=2)
    
    def _save_csv(self, data: Dict, filepath: str, append: bool = False):
        """Save data as CSV."""
        import csv
        import os
        
        # Flatten data structure for CSV
        flat_data = self._flatten_dict(data)
        
        # Check if file exists for append mode
        file_exists = os.path.exists(filepath)
        mode = 'a' if (append and file_exists) else 'w'
        
        with open(filepath, mode, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=flat_data.keys())
            
            if not file_exists or not append:
                writer.writeheader()
            
            writer.writerow(flat_data)
    
    def _save_excel(self, data: Dict, filepath: str):
        """Save data as Excel file."""
        try:
            import pandas as pd
        except ImportError:
            print("⚠️  pandas required for Excel export. Install with: pip install pandas openpyxl")
            raise
        
        # Convert to DataFrame
        flat_data = self._flatten_dict(data)
        df = pd.DataFrame([flat_data])
        
        # Save to Excel
        df.to_excel(filepath, index=False, engine='openpyxl')
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Flatten nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def reset(self):
        """Reset the scraper state."""
        self.current_symbol = None
        self.current_timeframe = None
        self.active_indicators = []
        print("Scraper reset")
