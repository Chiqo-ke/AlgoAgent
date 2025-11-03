"""
Sequential Data Processing Configuration
=========================================

This module controls how generated strategies process market data:
- STREAMING mode: Sequential row-by-row processing (realistic, prevents look-ahead)
- BATCH mode: Bulk processing (faster, allows vectorization)

Version: 1.0.0
Created: 2025-11-03
"""

# Default mode for generated strategies
DEFAULT_MODE = "streaming"  # Options: "streaming" or "batch"

# Progress reporting interval (percentage)
PROGRESS_INTERVAL = 10

# Streaming buffer size (for optimization)
STREAM_BUFFER_SIZE = 100


def get_backtest_runner_template(mode: str = None) -> str:
    """
    Returns the appropriate run_backtest() template based on mode.
    
    Args:
        mode: "streaming" or "batch" (uses DEFAULT_MODE if None)
        
    Returns:
        String containing the run_backtest() function code
    """
    
    if mode is None:
        mode = DEFAULT_MODE
    
    if mode == "streaming":
        return STREAMING_TEMPLATE
    elif mode == "batch":
        return BATCH_TEMPLATE
    else:
        raise ValueError(f"Invalid mode: {mode}. Must be 'streaming' or 'batch'")


# Template for streaming mode (sequential processing)
STREAMING_TEMPLATE = '''
def run_backtest():
    """Runs the backtest in STREAMING mode (sequential row-by-row processing)"""
    
    # 1. Configure backtest
    config = BacktestConfig(
        start_cash=100000,
        fee_flat=1.0,
        fee_pct=0.001,
        slippage_pct=0.0005
    )
    
    # 2. Initialize broker
    broker = SimBroker(config)
    
    # 3. Initialize strategy
    strategy = {STRATEGY_CLASS_NAME}(broker, strategy_id="strategy_001")
    print(f"✓ Strategy initialized: {{strategy.__class__.__name__}}")
    
    # 4. Define indicators
    indicators = {INDICATORS_DICT}
    
    # 5. Load data in STREAMING mode
    print(f"🔄 Loading data in STREAMING mode (sequential)...")
    data_stream = load_market_data(
        ticker=strategy.symbol,
        indicators=indicators,
        period='6mo',
        interval='1d',
        stream=True  # ✅ Enable streaming
    )
    
    print(f"✓ Data stream initialized")
    print(f"✓ Processing bars sequentially...")
    
    # 6. Process each bar sequentially
    bar_count = 0
    for timestamp, market_data, progress_pct in data_stream:
        bar_count += 1
        strategy.on_bar(timestamp, market_data)
        broker.step_to(timestamp, market_data)
        
        # Show progress every 10%
        if int(progress_pct) % 10 == 0 and int(progress_pct) != 0:
            if int(progress_pct) % 10 == int((progress_pct - 0.1)) % 10:  # Only print once per 10%
                pass
            else:
                print(f"  Progress: {{progress_pct:.1f}}% ({{bar_count}} bars)")
    
    print(f"✓ Processed {{bar_count}} bars sequentially")
    
    # 7. Finalize strategy (close loggers)
    strategy.finalize()
    
    # 8. Get metrics
    metrics = broker.compute_metrics()
    
    # 9. Export results
    results_dir = Path(__file__).parent / "results"
    trades_dir = Path(__file__).parent / "trades"
    results_dir.mkdir(exist_ok=True)
    trades_dir.mkdir(exist_ok=True)
    
    broker.export_trades(str(trades_dir / "trades.csv"))
    
    # 10. Print results
    print("=" * 70)
    print("BACKTEST RESULTS (STREAMING MODE)")
    print("=" * 70)
    print(f"Period: {{metrics['start_date']}} to {{metrics['end_date']}}")
    print(f"Duration: {{metrics['duration_days']}} days")
    print()
    print(f"Starting Capital: ${{metrics['start_cash']:,.2f}}")
    print(f"Final Equity: ${{metrics['final_equity']:,.2f}}")
    print(f"Net Profit: ${{metrics['net_profit']:,.2f}} ({{metrics['total_return_pct']:.2f}}%)")
    print()
    print(f"Total Trades: {{metrics['total_trades']}}")
    print(f"Win Rate: {{metrics['win_rate'] * 100:.1f}}%")
    print(f"Profit Factor: {{metrics['profit_factor']:.2f}}")
    print()
    print(f"Max Drawdown: {{metrics['max_drawdown_pct'] * 100:.2f}}%")
    print(f"Sharpe Ratio: {{metrics['sharpe_ratio']:.2f}}")
    print(f"Sortino Ratio: {{metrics['sortino_ratio']:.2f}}")
    print("=" * 70)
    
    return metrics
'''


# Template for batch mode (bulk processing)
BATCH_TEMPLATE = '''
def run_backtest():
    """Runs the backtest in BATCH mode (bulk processing)"""
    
    # 1. Configure backtest
    config = BacktestConfig(
        start_cash=100000,
        fee_flat=1.0,
        fee_pct=0.001,
        slippage_pct=0.0005
    )
    
    # 2. Initialize broker
    broker = SimBroker(config)
    
    # 3. Initialize strategy
    strategy = {STRATEGY_CLASS_NAME}(broker, strategy_id="strategy_001")
    print(f"✓ Strategy initialized: {{strategy.__class__.__name__}}")
    
    # 4. Define indicators
    indicators = {INDICATORS_DICT}
    
    # 5. Load all data at once (BATCH mode)
    print(f"⚡ Loading data in BATCH mode...")
    df, metadata = load_market_data(
        ticker=strategy.symbol,
        indicators=indicators,
        period='6mo',
        interval='1d',
        stream=False  # Batch mode
    )
    
    print(f"✓ Loaded {{len(df)}} bars")
    print(f"✓ Columns: {{list(df.columns)}}")
    
    # 6. Process all bars
    for i, (timestamp, row) in enumerate(df.iterrows()):
        market_data = {{
            strategy.symbol: {{
                'open': row.get('Open', row.get('open')),
                'high': row.get('High', row.get('high')),
                'low': row.get('Low', row.get('low')),
                'close': row.get('Close', row.get('close')),
                'volume': row.get('Volume', row.get('volume')),
                **{{col.lower(): row[col] for col in df.columns 
                   if col.lower() not in ['open', 'high', 'low', 'close', 'volume']}}
            }}
        }}
        strategy.on_bar(timestamp, market_data)
        broker.step_to(timestamp, market_data)
        
        # Show progress every 10%
        if i % (len(df) // 10 or 1) == 0:
            progress = (i / len(df)) * 100
            print(f"  Progress: {{progress:.1f}}%")
    
    # 7. Finalize strategy (close loggers)
    strategy.finalize()
    
    # 8. Get metrics
    metrics = broker.compute_metrics()
    
    # 9. Export results
    results_dir = Path(__file__).parent / "results"
    trades_dir = Path(__file__).parent / "trades"
    results_dir.mkdir(exist_ok=True)
    trades_dir.mkdir(exist_ok=True)
    
    broker.export_trades(str(trades_dir / "trades.csv"))
    
    # 10. Print results
    print("=" * 70)
    print("BACKTEST RESULTS (BATCH MODE)")
    print("=" * 70)
    print(f"Period: {{metrics['start_date']}} to {{metrics['end_date']}}")
    print(f"Duration: {{metrics['duration_days']}} days")
    print()
    print(f"Starting Capital: ${{metrics['start_cash']:,.2f}}")
    print(f"Final Equity: ${{metrics['final_equity']:,.2f}}")
    print(f"Net Profit: ${{metrics['net_profit']:,.2f}} ({{metrics['total_return_pct']:.2f}}%)")
    print()
    print(f"Total Trades: {{metrics['total_trades']}}")
    print(f"Win Rate: {{metrics['win_rate'] * 100:.1f}}%")
    print(f"Profit Factor: {{metrics['profit_factor']:.2f}}")
    print()
    print(f"Max Drawdown: {{metrics['max_drawdown_pct'] * 100:.2f}}%")
    print(f"Sharpe Ratio: {{metrics['sharpe_ratio']:.2f}}")
    print(f"Sortino Ratio: {{metrics['sortino_ratio']:.2f}}")
    print("=" * 70)
    
    return metrics
'''


# Configuration metadata
CONFIG = {
    "mode": DEFAULT_MODE,
    "description": {
        "streaming": "Sequential row-by-row processing (realistic, prevents look-ahead bias)",
        "batch": "Bulk processing (faster, allows vectorization, may have look-ahead)"
    },
    "use_cases": {
        "streaming": [
            "Simulating real-time trading",
            "Strict sequential processing",
            "Preventing look-ahead bias",
            "Testing production-like behavior"
        ],
        "batch": [
            "Rapid prototyping",
            "Vectorized calculations",
            "Performance-critical testing",
            "Historical analysis with future data"
        ]
    }
}


def get_mode_info() -> dict:
    """
    Get information about the current mode and available modes.
    
    Returns:
        Dictionary with mode information
    """
    return {
        "current_mode": DEFAULT_MODE,
        "available_modes": ["streaming", "batch"],
        "current_description": CONFIG["description"][DEFAULT_MODE],
        "all_descriptions": CONFIG["description"],
        "use_cases": CONFIG["use_cases"]
    }


def validate_mode(mode: str) -> bool:
    """
    Validate if a mode is supported.
    
    Args:
        mode: Mode to validate
        
    Returns:
        True if mode is valid, False otherwise
    """
    return mode in ["streaming", "batch"]


if __name__ == "__main__":
    print("=" * 70)
    print("Sequential Data Processing Configuration")
    print("=" * 70)
    
    info = get_mode_info()
    
    print(f"\nCurrent Mode: {info['current_mode'].upper()}")
    print(f"Description: {info['current_description']}")
    
    print(f"\nUse Cases for {info['current_mode'].upper()} mode:")
    for use_case in info['use_cases'][info['current_mode']]:
        print(f"  • {use_case}")
    
    print("\nAvailable Modes:")
    for mode in info['available_modes']:
        print(f"  • {mode.upper()}: {info['all_descriptions'][mode]}")
    
    print("\n" + "=" * 70)
