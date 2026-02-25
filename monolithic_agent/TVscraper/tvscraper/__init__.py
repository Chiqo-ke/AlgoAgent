"""
TradingView Scraper - Extract market data from TradingView charts using MCP Chrome DevTools
"""

from .mcp_scraper import MCPTradingViewScraper
from .scraper import TradingViewScraper
from .indicators import IndicatorManager

__version__ = "1.0.0"
__all__ = ["MCPTradingViewScraper", "TradingViewScraper", "IndicatorManager"]

# Convenience aliases
Scraper = MCPTradingViewScraper
TVScraper = MCPTradingViewScraper
