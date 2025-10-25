"""
Interactive Backtest Runner
===========================

This module provides an interactive command-line interface for running backtests
with user-specified parameters including symbol selection and date range.

Features:
- Interactive symbol selection
- Custom date range input (From: {date}, To: {date})
- Strategy validation and generation from Strategy module
- Data fetching from Data module using fetch_data_by_date_range
- Automatic indicator loading
- Full backtest execution with results

Version: 2.0.0
Last Updated: 2025-10-22
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
import logging
import json
import importlib.util

# Add parent directory to path for imports
PARENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PARENT_DIR))

from Data.data_fetcher import DataFetcher
from Backtest.config import get_realistic_config, BacktestConfig
from Backtest.sim_broker import SimBroker

# Import Strategy module components
# Try multiple import strategies: plain import, package import, then load from file path.
STRATEGY_VALIDATOR_AVAILABLE = False
try:
    sys.path.insert(0, str(PARENT_DIR / "Strategy"))
    try:
        # Try direct import if the Strategy directory is on sys.path
        from strategy_validator import StrategyValidatorBot  # type: ignore
        STRATEGY_VALIDATOR_AVAILABLE = True
    except ImportError:
        try:
            # Try package-qualified import (if Strategy is a package)
            from Strategy.strategy_validator import StrategyValidatorBot  # type: ignore
            STRATEGY_VALIDATOR_AVAILABLE = True
        except Exception:
            # Fallback: load the file directly if it exists
            validator_path = PARENT_DIR / "Strategy" / "strategy_validator.py"
            if validator_path.exists():
                spec = importlib.util.spec_from_file_location("strategy_validator", str(validator_path))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)  # type: ignore
                StrategyValidatorBot = getattr(module, "StrategyValidatorBot", None)
                if StrategyValidatorBot is not None:
                    STRATEGY_VALIDATOR_AVAILABLE = True
            if not STRATEGY_VALIDATOR_AVAILABLE:
                logging.warning("Strategy validator not available: could not import strategy_validator module")
except Exception as e:
    STRATEGY_VALIDATOR_AVAILABLE = False
    logging.warning(f"Strategy validator not available: {e}")

# Import Gemini strategy generator
try:
    from gemini_strategy_generator import GeminiStrategyGenerator
    GEMINI_GENERATOR_AVAILABLE = True
except ImportError as e:
    GEMINI_GENERATOR_AVAILABLE = False
    logging.warning(f"Gemini generator not available: {e}")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_date(date_string: str) -> Tuple[bool, Optional[datetime]]:
    """
    Validate date string format.
    
    Args:
        date_string: Date in YYYY-MM-DD format
        
    Returns:
        Tuple of (is_valid, datetime_object or None)
    """
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        return True, date_obj
    except ValueError:
        return False, None


def get_user_symbol() -> str:
    """
    Prompt user to enter stock symbol.
    
    Returns:
        Stock symbol in uppercase
    """
    print("\n" + "=" * 70)
    print("STOCK SYMBOL SELECTION")
    print("=" * 70)
    
    while True:
        symbol = input("\nEnter stock symbol (e.g., AAPL, MSFT, GOOGL): ").strip().upper()
        
        if not symbol:
            print("❌ Symbol cannot be empty. Please try again.")
            continue
            
        if not symbol.replace("^", "").replace(".", "").isalnum():
            print("❌ Invalid symbol format. Please use alphanumeric characters only.")
            continue
            
        print(f"✓ Selected symbol: {symbol}")
        return symbol


def get_user_date_range() -> Tuple[str, str]:
    """
    Prompt user to enter backtest date range.
    
    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    print("\n" + "=" * 70)
    print("DATE RANGE SELECTION")
    print("=" * 70)
    print("Please enter dates in YYYY-MM-DD format (e.g., 2024-01-01)")
    
    # Get start date
    while True:
        start_input = input("\nFrom (start date): ").strip()
        
        if not start_input:
            print("❌ Start date cannot be empty.")
            continue
            
        is_valid, start_date = validate_date(start_input)
        if not is_valid:
            print("❌ Invalid date format. Please use YYYY-MM-DD (e.g., 2024-01-01)")
            continue
            
        if start_date > datetime.now():
            print("❌ Start date cannot be in the future.")
            continue
            
        print(f"✓ Start date: {start_input}")
        break
    
    # Get end date
    while True:
        end_input = input("To (end date): ").strip()
        
        if not end_input:
            print("❌ End date cannot be empty.")
            continue
            
        is_valid, end_date = validate_date(end_input)
        if not is_valid:
            print("❌ Invalid date format. Please use YYYY-MM-DD (e.g., 2025-01-01)")
            continue
            
        if end_date > datetime.now():
            print("❌ End date cannot be in the future.")
            continue
            
        if end_date <= start_date:
            print(f"❌ End date must be after start date ({start_input}).")
            continue
            
        print(f"✓ End date: {end_input}")
        break
    
    # Calculate duration
    duration = (end_date - start_date).days
    print(f"\n📅 Backtest period: {duration} days ({start_input} to {end_input})")
    
    return start_input, end_input


def get_user_interval() -> str:
    """
    Prompt user to select data interval.
    
    Returns:
        Interval string (e.g., '1d', '1h', '30m')
    """
    print("\n" + "=" * 70)
    print("DATA INTERVAL SELECTION")
    print("=" * 70)
    print("Available intervals:")
    print("  1. 1d  - Daily")
    print("  2. 1h  - Hourly")
    print("  3. 30m - 30 minutes")
    print("  4. 15m - 15 minutes")
    print("  5. 5m  - 5 minutes")
    
    intervals = {
        '1': '1d',
        '2': '1h',
        '3': '30m',
        '4': '15m',
        '5': '5m'
    }
    
    while True:
        choice = input("\nSelect interval (1-5) or enter custom (e.g., 2m, 1wk): ").strip()
        
        if choice in intervals:
            interval = intervals[choice]
            print(f"✓ Selected interval: {interval}")
            return interval
        elif choice and any(choice.endswith(suffix) for suffix in ['m', 'h', 'd', 'wk', 'mo']):
            print(f"✓ Custom interval: {choice}")
            return choice
        else:
            print("❌ Invalid selection. Please choose 1-5 or enter a valid interval.")


def get_user_strategy_choice() -> str:
    """
    Prompt user to select strategy source.
    
    Returns:
        Choice string ('new', 'existing', 'example')
    """
    print("\n" + "=" * 70)
    print("STRATEGY SELECTION")
    print("=" * 70)
    print("How would you like to provide your trading strategy?")
    print("  1. Enter a new strategy (will be validated and generated)")
    print("  2. Use existing strategy from Backtest/codes/")
    print("  3. Use example strategy")
    
    choice_map = {
        '1': 'new',
        '2': 'existing',
        '3': 'example'
    }
    
    while True:
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice in choice_map:
            return choice_map[choice]
        else:
            print("❌ Invalid selection. Please choose 1-3.")


def enter_new_strategy() -> Optional[str]:
    """
    Allow user to enter a new strategy description.
    
    Returns:
        Strategy description text or None if cancelled
    """
    print("\n" + "=" * 70)
    print("ENTER NEW STRATEGY")
    print("=" * 70)
    print("\nDescribe your trading strategy in plain English.")
    print("Include entry rules, exit rules, position sizing, and risk management.")
    print("\n⚠️  IMPORTANT: Do NOT specify a particular symbol (e.g., AAPL, MSFT).")
    print("   Your strategy will work with ANY symbol from the data module.")
    print("\n✅ GOOD Example:")
    print("  'Buy when 50 EMA crosses above 200 EMA. Set stop loss at 2%.")
    print("   Take profit at 5%. Risk 1% of account per trade.'")
    print("\n❌ AVOID:")
    print("  'Buy AAPL when...' (Don't mention specific symbols)")
    print("\nEnter your strategy (press Enter twice when done):")
    print("-" * 70)
    
    lines = []
    empty_count = 0
    while empty_count < 2:
        line = input()
        if line.strip():
            lines.append(line)
            empty_count = 0
        else:
            empty_count += 1
    
    strategy_text = "\n".join(lines).strip()
    
    if not strategy_text:
        print("\n⚠ No strategy entered.")
        return None
    
    return strategy_text


def validate_and_canonicalize_strategy(strategy_text: str) -> Optional[Dict[str, Any]]:
    """
    Validate strategy and generate canonical JSON.
    
    Args:
        strategy_text: User's strategy description
        
    Returns:
        Validation result dictionary or None if failed
    """
    if not STRATEGY_VALIDATOR_AVAILABLE:
        print("\n❌ Strategy validator not available.")
        print("   Please ensure Strategy module is accessible.")
        return None
    
    print("\n" + "=" * 70)
    print("VALIDATING STRATEGY")
    print("=" * 70)
    print("\n⏳ Analyzing strategy with AI assistance...")
    
    try:
        # Initialize validator bot
        validator = StrategyValidatorBot(
            username="backtest_user",
            strict_mode=False,
            use_gemini=True
        )
        
        # Process the strategy
        result = validator.process_input(strategy_text, "auto")
        
        # Check status
        if result.get("status") == "success":
            print("✓ Strategy validated successfully!")
            
            # Display canonicalized steps
            print("\n" + "-" * 70)
            print("CANONICALIZED STRATEGY")
            print("-" * 70)
            steps = result.get("canonicalized_steps", "")
            print(steps if steps else "No steps generated")
            
            # Display classification
            classification = result.get("classification", {})
            if classification:
                print("\n" + "-" * 70)
                print("CLASSIFICATION")
                print("-" * 70)
                print(f"  Type: {classification.get('type', 'unknown')}")
                print(f"  Risk Tier: {classification.get('risk_tier', 'unknown')}")
            
            return result
        else:
            print(f"\n❌ Validation failed: {result.get('message', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"\n❌ Validation error: {e}")
        logger.error(f"Strategy validation failed: {e}", exc_info=True)
        return None


def generate_strategy_code(canonical_json: str, strategy_name: str) -> Optional[Path]:
    """
    Generate Python strategy code from canonical JSON.
    
    Args:
        canonical_json: Canonical strategy JSON string
        strategy_name: Name for the strategy class
        
    Returns:
        Path to generated Python file or None if failed
    """
    if not GEMINI_GENERATOR_AVAILABLE:
        print("\n❌ Gemini generator not available.")
        print("   Please ensure gemini_strategy_generator is accessible.")
        return None
    
    print("\n" + "=" * 70)
    print("GENERATING STRATEGY CODE")
    print("=" * 70)
    print("\n⏳ Generating Python code with Gemini AI...")
    
    try:
        # Parse canonical JSON
        strategy_data = json.loads(canonical_json)
        
        # Extract description for code generation
        title = strategy_data.get('title', 'Strategy')
        description = strategy_data.get('description', '')
        steps = strategy_data.get('steps', [])
        
        # Build full description with symbol-agnostic instructions
        full_desc = f"{title}\n{description}\n\nSteps:\n"
        for step in steps:
            step_title = step.get('title', '')
            trigger = step.get('trigger', '')
            if trigger:
                full_desc += f"- {step_title}: {trigger}\n"
        
        # Add symbol-agnostic instructions
        full_desc += "\n\nIMPORTANT INSTRUCTIONS FOR CODE GENERATION:"
        full_desc += "\n- Strategy should work with ANY symbol (do not hardcode symbols)"
        full_desc += "\n- Symbol will be provided dynamically through market_data parameter"
        full_desc += "\n- Use market_data dictionary to access OHLCV data for any symbol"
        full_desc += "\n- Constructor should only accept broker and trading parameters (no symbol parameter)"
        
        # Initialize generator
        generator = GeminiStrategyGenerator()
        
        # Generate code
        code = generator.generate_strategy(
            description=full_desc,
            strategy_name=strategy_name
        )
        
        # Save to codes directory
        codes_dir = Path(__file__).parent / "codes"
        codes_dir.mkdir(exist_ok=True)
        
        # Create safe filename
        safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in strategy_name.lower())
        python_file = codes_dir / f"{safe_name}.py"
        
        # Save Python code
        with open(python_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Also save the canonical JSON
        json_file = codes_dir / f"{safe_name}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            f.write(canonical_json)
        
        print(f"✓ Strategy code generated!")
        print(f"  Python: {python_file}")
        print(f"  JSON: {json_file}")
        
        return python_file
        
    except Exception as e:
        print(f"\n❌ Code generation error: {e}")
        logger.error(f"Strategy code generation failed: {e}", exc_info=True)
        return None


def list_existing_strategies() -> List[Path]:
    """
    List existing strategy files in codes directory.
    
    Returns:
        List of Python strategy file paths
    """
    codes_dir = Path(__file__).parent / "codes"
    if not codes_dir.exists():
        return []
    
    py_files = list(codes_dir.glob("*.py"))
    # Filter out __init__.py and README files
    py_files = [f for f in py_files if f.name not in ['__init__.py', 'README.py']]
    return sorted(py_files)


def select_existing_strategy() -> Optional[Path]:
    """
    Allow user to select an existing strategy.
    
    Returns:
        Path to selected strategy file or None
    """
    strategies = list_existing_strategies()
    
    if not strategies:
        print("\n⚠ No existing strategies found in Backtest/codes/")
        return None
    
    print("\n" + "=" * 70)
    print("EXISTING STRATEGIES")
    print("=" * 70)
    
    for i, strategy_file in enumerate(strategies, 1):
        print(f"  {i}. {strategy_file.stem}")
    
    while True:
        choice = input(f"\nSelect strategy (1-{len(strategies)}) or 'b' to go back: ").strip()
        
        if choice.lower() == 'b':
            return None
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(strategies):
                selected = strategies[idx]
                print(f"✓ Selected: {selected.name}")
                return selected
            else:
                print(f"❌ Please enter a number between 1 and {len(strategies)}")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")


def load_strategy_class_from_file(python_file: Path):
    """
    Dynamically load a strategy class from a Python file.
    
    Args:
        python_file: Path to Python strategy file
        
    Returns:
        Strategy class or None if failed
    """
    try:
        # Load module
        spec = importlib.util.spec_from_file_location(
            f"strategy_{python_file.stem}",
            python_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find strategy class (look for class that's not SimBroker)
        strategy_class = None
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and 
                name not in ['SimBroker', 'BacktestConfig', 'Path', 'Dict', 'Any', 'Optional'] and
                not name.startswith('_')):
                strategy_class = obj
                break
        
        if strategy_class:
            print(f"✓ Strategy class loaded: {strategy_class.__name__}")
            return strategy_class
        else:
            print(f"❌ No strategy class found in {python_file.name}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to load {python_file.name}: {e}")
        logger.error(f"Strategy loading failed: {e}", exc_info=True)
        return None


def get_strategy_parameters(strategy_class) -> Dict[str, Any]:
    """
    Get strategy parameters from user or use defaults.
    
    Args:
        strategy_class: Strategy class to inspect
        
    Returns:
        Dictionary of strategy parameters
    """
    print("\n" + "=" * 70)
    print("STRATEGY PARAMETERS")
    print("=" * 70)
    
    # Try to get default parameters from class
    params = {}
    
    # Check if class has __init__ signature
    try:
        import inspect
        sig = inspect.signature(strategy_class.__init__)
        
        # Filter and collect valid parameters
        valid_params = []
        for param_name, param in sig.parameters.items():
            # Filter out common parameters and symbol (symbol should come from data module)
            if param_name in ['self', 'broker', 'symbol']:
                continue
            valid_params.append((param_name, param))
        
        if not valid_params:
            print("\n✓ Strategy has no configurable parameters.")
            print("  The strategy will work with any symbol from the data module.")
            return params
        
        print("\nAvailable parameters:")
        print("ℹ️  Note: Symbol is automatically provided by the data module")
        
        for param_name, param in valid_params:
            default_val = param.default if param.default != inspect.Parameter.empty else None
            print(f"  {param_name}: {default_val}")
            
            # Ask user for value
            user_input = input(f"    Enter value for {param_name} (or press Enter for default): ").strip()
            if user_input:
                # Try to convert to appropriate type
                try:
                    if default_val is not None:
                        param_type = type(default_val)
                        params[param_name] = param_type(user_input)
                    else:
                        # Try int first, then float, then str
                        try:
                            params[param_name] = int(user_input)
                        except ValueError:
                            try:
                                params[param_name] = float(user_input)
                            except ValueError:
                                params[param_name] = user_input
                except ValueError:
                    print(f"  ⚠️  Invalid value, using default")
    except Exception as e:
        print(f"\n⚠️  Could not inspect parameters: {e}")
        print("Using default parameters")
    
    return params


def fetch_data_for_backtest(
    symbol: str,
    start_date: str,
    end_date: str,
    interval: str = '1d'
) -> pd.DataFrame:
    """
    Fetch market data using DataFetcher with date range.
    
    Args:
        symbol: Stock ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        interval: Data interval (default: '1d')
        
    Returns:
        DataFrame with OHLCV data
    """
    print("\n" + "=" * 70)
    print("FETCHING MARKET DATA")
    print("=" * 70)
    print(f"Symbol: {symbol}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Interval: {interval}")
    print("\nFetching data from Yahoo Finance...")
    
    fetcher = DataFetcher()
    df = fetcher.fetch_data_by_date_range(
        ticker=symbol,
        start_date=start_date,
        end_date=end_date,
        interval=interval
    )
    
    if df.empty:
        raise ValueError(f"No data returned for {symbol} in the specified date range")
    
    # Flatten MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Sort by datetime
    df = df.sort_index()
    
    # Convert to numeric
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows with NaN values
    initial_rows = len(df)
    df = df.dropna()
    dropped_rows = initial_rows - len(df)
    
    print(f"✓ Data fetched successfully!")
    print(f"  Total bars: {len(df)}")
    if dropped_rows > 0:
        print(f"  Dropped {dropped_rows} rows with missing data")
    print(f"  Date range: {df.index[0]} to {df.index[-1]}")
    print(f"  Columns: {list(df.columns)}")
    
    return df


def get_backtest_config() -> BacktestConfig:
    """
    Get backtest configuration from user or use defaults.
    
    Returns:
        BacktestConfig object
    """
    print("\n" + "=" * 70)
    print("BACKTEST CONFIGURATION")
    print("=" * 70)
    
    # Ask if user wants to customize config
    customize = input("\nUse default configuration? (Y/n): ").strip().lower()
    
    if customize == 'n' or customize == 'no':
        # Get custom parameters
        config = get_realistic_config()
        
        try:
            cash_input = input(f"\nStarting cash (default ${config.start_cash:,.0f}): ").strip()
            if cash_input:
                config.start_cash = float(cash_input)
            
            print("\nFee structure:")
            fee_pct_input = input(f"  Fee percentage (default {config.fee_pct*100:.3f}%): ").strip()
            if fee_pct_input:
                config.fee_pct = float(fee_pct_input) / 100
                
            fee_flat_input = input(f"  Flat fee per order (default ${config.fee_flat}): ").strip()
            if fee_flat_input:
                config.fee_flat = float(fee_flat_input)
            
            slippage_input = input(f"\nSlippage percentage (default {config.slippage_pct*100:.4f}%): ").strip()
            if slippage_input:
                config.slippage_pct = float(slippage_input) / 100
                
        except ValueError as e:
            print(f"⚠️  Invalid input: {e}. Using defaults.")
    else:
        config = get_realistic_config()
    
    # Display configuration
    print("\n✓ Configuration set:")
    print(f"  Starting Cash: ${config.start_cash:,.2f}")
    print(f"  Fee: ${config.fee_flat} + {config.fee_pct*100:.3f}%")
    print(f"  Slippage: {config.slippage_pct*100:.4f}%")
    
    return config


def convert_to_broker_format(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Convert DataFrame to SimBroker expected format.
    
    Args:
        df: DataFrame with OHLCV data
        symbol: Stock symbol
        
    Returns:
        DataFrame in broker format with required columns
    """
    # Create a copy to avoid modifying original
    broker_df = pd.DataFrame()
    broker_df['timestamp'] = df.index
    broker_df['symbol'] = symbol
    broker_df['open'] = df['Open'].values
    broker_df['high'] = df['High'].values
    broker_df['low'] = df['Low'].values
    broker_df['close'] = df['Close'].values
    broker_df['volume'] = df['Volume'].values
    
    return broker_df


def run_backtest_simulation(
    broker: SimBroker,
    df: pd.DataFrame,
    symbol: str,
    strategy_class,
    strategy_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run the backtest simulation.
    
    Args:
        broker: SimBroker instance
        df: Market data DataFrame
        symbol: Stock symbol
        strategy_class: Strategy class to instantiate
        strategy_params: Parameters for strategy initialization
        
    Returns:
        Dictionary of metrics
    """
    print("\n" + "=" * 70)
    print("RUNNING BACKTEST SIMULATION")
    print("=" * 70)
    
    # Initialize strategy (symbol-agnostic - no symbol passed to constructor)
    strategy = strategy_class(broker=broker, **strategy_params)
    print(f"✓ Strategy initialized: {strategy_class.__name__}")
    print(f"✓ Strategy is symbol-agnostic and will work with: {symbol}")
    
    # Convert data to broker format
    broker_df = convert_to_broker_format(df, symbol)
    
    # Run simulation
    print(f"\nSimulating {len(broker_df)} bars...")
    progress_interval = max(1, len(broker_df) // 20)  # Update every 5%
    
    for idx, row in broker_df.iterrows():
        timestamp = row['timestamp']
        
        market_data = {
            row['symbol']: {
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume']
            }
        }
        
        # Strategy analyzes and may emit signals
        strategy.on_bar(timestamp, market_data)
        
        # Broker processes signals and updates state
        broker.step_to(timestamp, market_data)
        
        # Progress update
        if idx % progress_interval == 0:
            progress = (idx / len(broker_df)) * 100
            print(f"  Progress: {progress:.0f}%", end='\r')
    
    print("  Progress: 100% ✓")
    print("\n✓ Simulation complete!")
    
    # Compute metrics
    print("\nComputing performance metrics...")
    metrics = broker.compute_metrics()
    
    return metrics


def display_results(metrics: Dict[str, Any], broker: SimBroker):
    """
    Display backtest results in a formatted manner.
    
    Args:
        metrics: Dictionary of computed metrics
        broker: SimBroker instance for additional stats
    """
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70)
    print(f"Period: {metrics['start_date']} to {metrics['end_date']}")
    print(f"Duration: {metrics['duration_days']} days")
    print()
    print(f"Starting Capital: ${metrics['start_cash']:,.2f}")
    print(f"Final Equity: ${metrics['final_equity']:,.2f}")
    print(f"Net Profit: ${metrics['net_profit']:,.2f} ({metrics['total_return_pct']:.2f}%)")
    print()
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Winning Trades: {metrics['winning_trades']}")
    print(f"Losing Trades: {metrics['losing_trades']}")
    print(f"Win Rate: {metrics['win_rate']*100:.1f}%")
    print()
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"Average Trade: ${metrics['average_trade']:.2f}")
    print(f"Average Win: ${metrics['average_win']:.2f}")
    print(f"Average Loss: ${metrics['average_loss']:.2f}")
    print()
    print(f"Max Drawdown: ${metrics['max_drawdown_abs']:,.2f} ({metrics['max_drawdown_pct']*100:.2f}%)")
    print(f"Recovery Factor: {metrics['recovery_factor']:.2f}")
    print()
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio: {metrics['sortino_ratio']:.2f}")
    print(f"Calmar Ratio: {metrics['calmar_ratio']:.2f}")
    print()
    print(f"Max Consecutive Wins: {metrics['max_consecutive_wins']}")
    print(f"Max Consecutive Losses: {metrics['max_consecutive_losses']}")
    print()
    print(f"Total Commission: ${metrics['total_commission']:,.2f}")
    print(f"Total Slippage: ${metrics['total_slippage']:,.2f}")
    print("=" * 70)
    
    # Component statistics
    stats = broker.get_statistics()
    print("\nComponent Statistics:")
    print(f"  Orders Created: {stats['orders']['orders_created']}")
    print(f"  Orders Filled: {stats['orders']['orders_filled']}")
    print(f"  Fills Executed: {stats['execution']['fills_executed']}")
    print(f"  Partial Fills: {stats['execution']['partial_fills']}")


def save_results(broker: SimBroker, metrics: Dict[str, Any], symbol: str):
    """
    Save backtest results to files.
    
    Args:
        broker: SimBroker instance
        metrics: Metrics dictionary
        symbol: Stock symbol
    """
    print("\n" + "=" * 70)
    print("SAVING RESULTS")
    print("=" * 70)
    
    import os
    import json
    
    # Create results directory
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save trades
    trades_file = results_dir / f"{symbol}_trades_{timestamp}.csv"
    broker.export_trades(str(trades_file))
    print(f"✓ Trades saved to: {trades_file}")
    
    # Save metrics
    metrics_file = results_dir / f"{symbol}_metrics_{timestamp}.json"
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"✓ Metrics saved to: {metrics_file}")
    
    print("\n✓ All results saved successfully!")


def main():
    """
    Main entry point for interactive backtest runner.
    """
    print("\n" + "=" * 70)
    print("INTERACTIVE BACKTEST RUNNER")
    print("=" * 70)
    print("Welcome! This tool will guide you through setting up and running")
    print("a backtest with your custom parameters.")
    
    try:
        # Step 1: Get symbol
        symbol = get_user_symbol()
        
        # Step 2: Get date range
        start_date, end_date = get_user_date_range()
        
        # Step 3: Get interval
        interval = get_user_interval()
        
        # Step 4: Fetch data
        df = fetch_data_for_backtest(symbol, start_date, end_date, interval)
        
        # Step 5: Get configuration
        config = get_backtest_config()
        
        # Step 6: Initialize broker
        print("\n" + "=" * 70)
        print("INITIALIZING BROKER")
        print("=" * 70)
        broker = SimBroker(config)
        print(f"✓ SimBroker initialized (API v{broker.API_VERSION})")
        
        # Step 7: Strategy Selection and Setup
        strategy_class = None
        strategy_params = {}
        
        while strategy_class is None:
            strategy_choice = get_user_strategy_choice()
            
            if strategy_choice == 'new':
                # Enter and validate new strategy
                strategy_text = enter_new_strategy()
                if not strategy_text:
                    continue
                
                # Validate and canonicalize
                validation_result = validate_and_canonicalize_strategy(strategy_text)
                if not validation_result:
                    retry = input("\nTry again? (Y/n): ").strip().lower()
                    if retry == 'n' or retry == 'no':
                        print("Exiting...")
                        sys.exit(0)
                    continue
                
                # Get canonical JSON
                canonical_json = validation_result.get('canonical_json', '{}')
                
                # Generate strategy name
                strategy_data = json.loads(canonical_json)
                strategy_title = strategy_data.get('title', 'CustomStrategy')
                strategy_name = ''.join(word.capitalize() for word in strategy_title.split()[:3])
                
                # Generate code
                python_file = generate_strategy_code(canonical_json, strategy_name)
                if not python_file:
                    retry = input("\nTry again? (Y/n): ").strip().lower()
                    if retry == 'n' or retry == 'no':
                        print("Exiting...")
                        sys.exit(0)
                    continue
                
                # Load generated strategy
                strategy_class = load_strategy_class_from_file(python_file)
                if not strategy_class:
                    retry = input("\nTry again? (Y/n): ").strip().lower()
                    if retry == 'n' or retry == 'no':
                        print("Exiting...")
                        sys.exit(0)
                    continue
                
            elif strategy_choice == 'existing':
                # Select existing strategy
                python_file = select_existing_strategy()
                if not python_file:
                    continue
                
                # Load strategy
                strategy_class = load_strategy_class_from_file(python_file)
                if not strategy_class:
                    retry = input("\nTry again? (Y/n): ").strip().lower()
                    if retry == 'n' or retry == 'no':
                        print("Exiting...")
                        sys.exit(0)
                    continue
                
            elif strategy_choice == 'example':
                # Use example strategy
                print("\n⚠️  Using example Simple MA Crossover strategy")
                try:
                    from Backtest.example_strategy import SimpleMAStrategy
                    strategy_class = SimpleMAStrategy
                    
                    # Default params for example strategy
                    strategy_params = {
                        'fast_period': 10,
                        'slow_period': 30,
                        'size': 100
                    }
                    
                    # Ask if user wants to customize
                    customize = input("\nCustomize strategy parameters? (y/N): ").strip().lower()
                    if customize == 'y' or customize == 'yes':
                        try:
                            fast = input(f"Fast MA period (default {strategy_params['fast_period']}): ").strip()
                            if fast:
                                strategy_params['fast_period'] = int(fast)
                                
                            slow = input(f"Slow MA period (default {strategy_params['slow_period']}): ").strip()
                            if slow:
                                strategy_params['slow_period'] = int(slow)
                                
                            size = input(f"Position size (default {strategy_params['size']}): ").strip()
                            if size:
                                strategy_params['size'] = int(size)
                        except ValueError as e:
                            print(f"⚠️  Invalid input: {e}. Using defaults.")
                    
                    print(f"\n✓ Strategy parameters:")
                    print(f"  Fast MA: {strategy_params['fast_period']}")
                    print(f"  Slow MA: {strategy_params['slow_period']}")
                    print(f"  Position Size: {strategy_params['size']}")
                    
                except ImportError as e:
                    print(f"\n❌ Could not load example strategy: {e}")
                    continue
        
        # Get strategy parameters if not already set
        if not strategy_params:
            strategy_params = get_strategy_parameters(strategy_class)
        
        print(f"\n✓ Strategy ready: {strategy_class.__name__}")
        
        # Step 8: Run backtest
        metrics = run_backtest_simulation(
            broker=broker,
            df=df,
            symbol=symbol,
            strategy_class=strategy_class,
            strategy_params=strategy_params
        )
        
        # Step 9: Display results
        display_results(metrics, broker)
        
        # Step 10: Save results
        save_option = input("\nSave results to files? (Y/n): ").strip().lower()
        if save_option != 'n' and save_option != 'no':
            save_results(broker, metrics, symbol)
        
        print("\n" + "=" * 70)
        print("BACKTEST COMPLETE")
        print("=" * 70)
        print("Thank you for using the Interactive Backtest Runner!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Backtest cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
