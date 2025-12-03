"""
Indicator Registry - Catalog of all available pre-built indicators
Allows the AI agent to reference existing indicator implementations
instead of re-implementing them in every bot.
"""

INDICATOR_REGISTRY = {
    'ema': {
        'name': 'Exponential Moving Average',
        'module': 'data_api.indicators',
        'function': 'calculate_ema',
        'params': {
            'data': 'price series (OHLCV)',
            'period': 'lookback period (e.g., 30, 50)'
        },
        'returns': 'Series of EMA values',
        'import': 'from data_api.indicators import calculate_ema',
        'example': 'ema_30 = self.I(calculate_ema, self.data.Close, 30)',
        'available': True
    },
    
    'sma': {
        'name': 'Simple Moving Average',
        'module': 'data_api.indicators',
        'function': 'calculate_sma',
        'params': {
            'data': 'price series',
            'period': 'lookback period'
        },
        'returns': 'Series of SMA values',
        'import': 'from data_api.indicators import calculate_sma',
        'example': 'sma_50 = self.I(calculate_sma, self.data.Close, 50)',
        'available': True
    },
    
    'rsi': {
        'name': 'Relative Strength Index',
        'module': 'data_api.indicators',
        'function': 'calculate_rsi',
        'params': {
            'data': 'price series',
            'period': 'lookback period (typically 14)'
        },
        'returns': 'Series of RSI values (0-100)',
        'import': 'from data_api.indicators import calculate_rsi',
        'example': 'rsi = self.I(calculate_rsi, self.data.Close, 14)',
        'available': True
    },
    
    'macd': {
        'name': 'MACD (Moving Average Convergence Divergence)',
        'module': 'data_api.indicators',
        'function': 'calculate_macd',
        'params': {
            'data': 'price series',
            'fast': 'fast EMA period (typically 12)',
            'slow': 'slow EMA period (typically 26)',
            'signal': 'signal line period (typically 9)'
        },
        'returns': 'Tuple of (macd, signal, histogram)',
        'import': 'from data_api.indicators import calculate_macd',
        'example': 'macd, signal, hist = self.I(calculate_macd, self.data.Close)',
        'available': True
    },
    
    'bollinger_bands': {
        'name': 'Bollinger Bands',
        'module': 'data_api.indicators',
        'function': 'calculate_bollinger_bands',
        'params': {
            'data': 'price series',
            'period': 'lookback period (typically 20)',
            'std_dev': 'standard deviation multiplier (typically 2)'
        },
        'returns': 'Tuple of (upper, middle, lower)',
        'import': 'from data_api.indicators import calculate_bollinger_bands',
        'example': 'upper, middle, lower = self.I(calculate_bollinger_bands, self.data.Close)',
        'available': True
    },
    
    'atr': {
        'name': 'Average True Range',
        'module': 'data_api.indicators',
        'function': 'calculate_atr',
        'params': {
            'high': 'high prices',
            'low': 'low prices',
            'close': 'close prices',
            'period': 'lookback period (typically 14)'
        },
        'returns': 'Series of ATR values',
        'import': 'from data_api.indicators import calculate_atr',
        'example': 'atr = self.I(calculate_atr, self.data.High, self.data.Low, self.data.Close, 14)',
        'available': True
    },
    
    'stochastic': {
        'name': 'Stochastic Oscillator',
        'module': 'data_api.indicators',
        'function': 'calculate_stochastic',
        'params': {
            'high': 'high prices',
            'low': 'low prices',
            'close': 'close prices',
            'period': 'lookback period (typically 14)',
            'smooth': 'smoothing period (typically 3)'
        },
        'returns': 'Tuple of (%K, %D)',
        'import': 'from data_api.indicators import calculate_stochastic',
        'example': 'k, d = self.I(calculate_stochastic, self.data.High, self.data.Low, self.data.Close)',
        'available': True
    }
}


def get_available_indicators():
    """Return list of available indicator names"""
    return [name for name, info in INDICATOR_REGISTRY.items() if info['available']]


def get_indicator_info(indicator_name):
    """Get detailed info about a specific indicator"""
    return INDICATOR_REGISTRY.get(indicator_name.lower())


def get_indicator_import(indicator_name):
    """Get the import statement for an indicator"""
    info = get_indicator_info(indicator_name)
    return info['import'] if info else None


def get_indicator_example(indicator_name):
    """Get usage example for an indicator"""
    info = get_indicator_info(indicator_name)
    return info['example'] if info else None


def format_registry_for_prompt():
    """Format the entire registry as a string for the AI prompt"""
    output = "# Available Pre-Built Indicators\n\n"
    output += "The following indicators are pre-built and available for use. ALWAYS use these instead of implementing custom indicator logic:\n\n"
    
    for name, info in INDICATOR_REGISTRY.items():
        if info['available']:
            output += f"## {name.upper()}\n"
            output += f"**Name:** {info['name']}\n"
            output += f"**Import:** `{info['import']}`\n"
            output += f"**Example:** `{info['example']}`\n"
            output += f"**Parameters:** {', '.join(info['params'].keys())}\n"
            output += f"**Returns:** {info['returns']}\n\n"
    
    return output


# Test the registry
if __name__ == '__main__':
    print("Available Indicators:", get_available_indicators())
    print("\nRegistry formatted for prompt:")
    print(format_registry_for_prompt())
