"""
TradingView Element Configuration
Maps TradingView UI elements for automation
"""

# Main navigation and controls
MAIN_ELEMENTS = {
    "symbol_button": "1_2",
    "data_type_switch": "1_3",
    "compare_symbol": "1_4",
    "chart_interval_menu": "1_10",
    "chart_type_menu": "1_11",
    "indicators_button": "1_12",
    "favorites_menu": "1_13",
    "indicator_templates": "1_14",
    "create_alert": "1_15",
    "bar_replay": "1_16",
    "layout_setup": "1_19",
    "manage_layouts": "1_21",
    "quick_search": "1_22",
    "settings": "1_23",
    "fullscreen": "1_24",
    "take_snapshot": "1_25"
}

# Timeframe radio buttons (direct access)
TIMEFRAME_RADIOS = {
    "1m": "1_5",
    "3m": "1_6",
    "5m": "1_7",
    "30m": "1_8",
    "1h": "1_9"
}

# Extended timeframe buttons (via quick access bar)
TIMEFRAME_QUICK_ACCESS = {
    "1D_1m": "1_104",    # 1 day in 1 minute intervals
    "5D_5m": "1_105",    # 5 days in 5 minutes intervals
    "1M_30m": "1_106",   # 1 month in 30 minutes intervals
    "3M_1h": "1_107",    # 3 months in 1 hour intervals
    "6M_2h": "1_108",    # 6 months in 2 hours intervals
    "YTD_1D": "1_109",   # Year to date in 1 day intervals
    "1Y_1D": "1_110",    # 1 year in 1 day intervals
    "5Y_1W": "1_111",    # 5 years in 1 week intervals
    "ALL_1M": "1_112"    # All data in 1 month intervals
}

# Chart region OHLC legend elements
OHLC_LEGEND = {
    "open_label": "1_64",
    "open_value": "1_65",
    "high_label": "1_66",
    "high_value": "1_67",
    "low_label": "1_68",
    "low_value": "1_69",
    "close_label": "1_70",
    "close_value": "1_71",
    "change_value": "1_72",
    "bid_price": "1_73",
    "bid_volume": "1_74",
    "bid_label": "1_75",
    "ask_volume": "1_76",
    "ask_price": "1_77",
    "ask_volume_2": "1_78",
    "ask_label": "1_79"
}

# Chart region controls
CHART_REGION = {
    "container": "1_55",
    "symbol_link": "1_57",
    "interval_link": "1_59",
    "exchange_label": "1_60",
    "flag_symbol": "1_61",
    "more_options": "1_62",
    "market_status": "1_63",
    "chart_canvas": "1_103"
}

# Drawing tools
DRAWING_TOOLS = {
    "cross": "1_28",
    "cursors": "1_29",
    "trend_line": "1_30",
    "trend_tools_menu": "1_31",
    "fib_retracement": "1_32",
    "fib_tools_menu": "1_33",
    "xabcd_pattern": "1_34",
    "patterns_menu": "1_35",
    "long_position": "1_36",
    "forecast_tools": "1_37",
    "brush": "1_38",
    "shapes_menu": "1_39",
    "text": "1_40",
    "annotation_tools": "1_41",
    "icon": "1_42",
    "icons_menu": "1_43",
    "measure": "1_44",
    "zoom_in": "1_45",
    "magnet_mode": "1_46",
    "magnets_menu": "1_47",
    "keep_drawing": "1_48",
    "lock_drawings": "1_49",
    "hide_drawings": "1_50",
    "hide_options": "1_51",
    "remove_objects": "1_52",
    "remove_options": "1_53",
    "show_favorites": "1_54"
}

# Side panel buttons
SIDE_PANELS = {
    "watchlist": "1_115",
    "alerts": "1_116",
    "object_tree": "1_117",
    "chats": "1_118",
    "screeners": "1_119",
    "pine_editor": "1_120",
    "calendars": "1_121",
    "community": "1_122",
    "notifications": "1_123",
    "products": "1_124",
    "help_center": "1_125",
    "trading_panel": "1_126"
}

# TradingView API endpoints (observed from network requests)
API_ENDPOINTS = {
    "ping": "https://data.tradingview.com/ping",
    "chart_token": "https://www.tradingview.com/chart-token/",
    "scanner_backend": "https://scanner-backend.tradingview.com/",
    "telemetry": "https://telemetry.tradingview.com/",
    "analytics": "https://analytics.google.com/g/collect"
}

# WebSocket patterns (for real-time data)
WEBSOCKET_PATTERNS = [
    "wss://data.tradingview.com/socket.io/",
    "wss://widgetdata.tradingview.com/",
    "wss://prodata.tradingview.com/"
]

# JavaScript window objects
JAVASCRIPT_OBJECTS = {
    "chart_widget": "window.tvWidget",
    "active_chart": "window.tvWidget.activeChart()",
    "chart_symbol": "window.tvWidget.chart().symbol()",
    "chart_resolution": "window.tvWidget.chart().resolution()",
    "chart_studies": "window.tvWidget.chart().getAllStudies()",
    "chart_series": "window.tvWidget.chart().getSeries()"
}

# Common indicator names in TradingView
INDICATOR_NAMES = {
    "EMA": "Moving Average Exponential",
    "SMA": "Moving Average",
    "WMA": "Moving Average Weighted",
    "HMA": "Hull Moving Average",
    "VWMA": "Volume Weighted Moving Average",
    "RSI": "Relative Strength Index",
    "MACD": "MACD",
    "Stoch": "Stochastic",
    "BB": "Bollinger Bands",
    "ATR": "Average True Range",
    "ADX": "Average Directional Index",
    "CCI": "Commodity Channel Index",
    "OBV": "On Balance Volume",
    "Volume": "Volume",
    "SAR": "Parabolic SAR",
    "Ichimoku": "Ichimoku Cloud",
    "SuperTrend": "SuperTrend",
    "VWAP": "Volume Weighted Average Price"
}

# Chart types
CHART_TYPES = {
    "bars": "Bars",
    "candles": "Candles",
    "hollow_candles": "Hollow Candles",
    "heikin_ashi": "Heikin Ashi",
    "line": "Line",
    "area": "Area",
    "baseline": "Baseline",
    "renko": "Renko",
    "kagi": "Kagi",
    "point_figure": "Point & Figure",
    "line_break": "Line Break",
    "range": "Range"
}

# Common symbols by market type
SYMBOL_EXAMPLES = {
    "forex": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"],
    "stocks": ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"],
    "crypto": ["BTCUSD", "ETHUSD", "BNBUSD", "XRPUSD", "ADAUSD"],
    "indices": ["SPX", "DJI", "NDX", "VIX", "FTSE"],
    "futures": ["ES1!", "NQ1!", "GC1!", "CL1!", "ZB1!"],
    "bonds": ["US10Y", "US02Y", "DE10Y", "GB10Y"],
    "commodities": ["GOLD", "SILVER", "OIL", "NATGAS"]
}

# Timeframe resolution strings
TIMEFRAME_RESOLUTIONS = {
    "1": "1 minute",
    "3": "3 minutes",
    "5": "5 minutes",
    "15": "15 minutes",
    "30": "30 minutes",
    "60": "1 hour",
    "120": "2 hours",
    "180": "3 hours",
    "240": "4 hours",
    "1D": "1 day",
    "1W": "1 week",
    "1M": "1 month"
}
