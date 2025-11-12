"""
Backtest Configuration
======================

Defines all configurable parameters for backtesting runs.
These are the ONLY parameters that can vary between backtests.

Last updated: 2025-10-16
Version: 1.0.0
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Literal
from datetime import datetime


@dataclass
class BacktestConfig:
    """
    Canonical Backtest Configuration
    
    All parameters that control execution behavior but do NOT
    change the SimBroker API or internal logic.
    """
    
    # ===== Account Parameters =====
    start_cash: float = 100000.0
    currency: str = "USD"
    leverage: float = 1.0  # Max leverage allowed
    
    # ===== Fee Structure =====
    fee_flat: float = 0.0  # Flat fee per order (in currency)
    fee_pct: float = 0.001  # Percentage fee (0.1% = 0.001)
    
    # ===== Slippage Model =====
    slippage_pct: float = 0.0001  # % slippage (0.01% = 0.0001)
    slippage_const: float = 0.0  # Fixed slippage (in price units)
    slippage_model: Literal["fixed", "volatility", "spread"] = "fixed"
    
    # ===== Execution Parameters =====
    liquidity_limit_pct: float = 0.1  # Max % of bar volume that can be filled
    latency_ms: int = 0  # Simulated latency in milliseconds
    bar_type: Literal["OHLC", "tick"] = "OHLC"
    fill_policy: Literal["aggressive", "conservative", "realistic"] = "realistic"
    
    # ===== Partial Fill Settings =====
    allow_partial_fills: bool = True
    min_fill_size: float = 1.0  # Minimum fill size (for partial fills)
    
    # ===== Market Data =====
    use_bid_ask: bool = False  # Use bid/ask spread if available
    use_volume: bool = True  # Use volume data for liquidity constraints
    
    # ===== Asset-Specific Settings =====
    min_lot_size: float = 1.0  # Minimum tradeable size
    tick_size: float = 0.01  # Minimum price increment
    
    # ===== Risk Controls =====
    max_position_size: Optional[float] = None  # Max size per position
    max_leverage_per_position: Optional[float] = None
    require_stop_loss: bool = False  # Warn if no stop loss
    max_drawdown_stop: Optional[float] = None  # Auto-stop at % drawdown
    
    # ===== Corporate Actions =====
    dividend_handling: Literal["reinvest", "cash", "ignore"] = "cash"
    split_handling: Literal["adjust", "ignore"] = "adjust"
    
    # ===== Margin Settings (for futures/forex) =====
    margin_requirement: float = 0.0  # % margin required per position
    maintenance_margin: float = 0.0  # % maintenance margin
    
    # ===== Time Settings =====
    timezone: str = "UTC"
    
    # ===== Randomness Control =====
    random_seed: Optional[int] = 42  # For reproducibility
    
    # ===== Output Settings =====
    output_dir: str = "backtest_results"
    save_trades: bool = True
    save_orders: bool = True
    save_equity_curve: bool = True
    save_metrics: bool = True
    save_html_report: bool = True
    save_debug_log: bool = False
    
    # ===== Performance Tracking =====
    track_metrics_every_n_bars: int = 1  # Calculate metrics frequency
    log_every_n_bars: int = 100  # Progress logging
    
    # ===== Advanced Settings =====
    benchmark_symbol: Optional[str] = None  # For comparative metrics
    risk_free_rate: float = 0.0  # Annual risk-free rate for Sharpe
    
    # ===== Metadata =====
    name: str = "backtest"
    description: str = ""
    tags: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration"""
        self._validate()
    
    def _validate(self):
        """Run validation checks"""
        if self.start_cash <= 0:
            raise ValueError("start_cash must be positive")
        
        if self.leverage < 1.0:
            raise ValueError("leverage must be >= 1.0")
        
        if not 0 <= self.fee_pct < 1:
            raise ValueError("fee_pct must be in [0, 1)")
        
        if not 0 <= self.slippage_pct < 1:
            raise ValueError("slippage_pct must be in [0, 1)")
        
        if not 0 < self.liquidity_limit_pct <= 1:
            raise ValueError("liquidity_limit_pct must be in (0, 1]")
        
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be non-negative")
        
        if self.min_lot_size <= 0:
            raise ValueError("min_lot_size must be positive")
        
        if self.tick_size <= 0:
            raise ValueError("tick_size must be positive")
        
        if self.max_drawdown_stop is not None:
            if not 0 < self.max_drawdown_stop <= 1:
                raise ValueError("max_drawdown_stop must be in (0, 1]")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestConfig':
        """Create from dictionary"""
        return cls(**data)
    
    def copy(self) -> 'BacktestConfig':
        """Create a copy of the configuration"""
        return BacktestConfig.from_dict(self.to_dict())


# ============================================================================
# PRESET CONFIGURATIONS
# ============================================================================

def get_default_config() -> BacktestConfig:
    """Get default configuration"""
    return BacktestConfig()


def get_realistic_config() -> BacktestConfig:
    """Get realistic configuration with typical fees and slippage"""
    return BacktestConfig(
        fee_flat=1.0,
        fee_pct=0.001,  # 0.1%
        slippage_pct=0.0005,  # 0.05%
        fill_policy="realistic",
        allow_partial_fills=True
    )


def get_zero_cost_config() -> BacktestConfig:
    """Get configuration with no fees or slippage (optimistic)"""
    return BacktestConfig(
        fee_flat=0.0,
        fee_pct=0.0,
        slippage_pct=0.0,
        slippage_const=0.0,
        fill_policy="aggressive"
    )


def get_high_cost_config() -> BacktestConfig:
    """Get configuration with high fees and slippage (conservative)"""
    return BacktestConfig(
        fee_flat=5.0,
        fee_pct=0.003,  # 0.3%
        slippage_pct=0.002,  # 0.2%
        fill_policy="conservative",
        allow_partial_fills=True
    )


def get_futures_config(margin_requirement: float = 0.1) -> BacktestConfig:
    """Get configuration for futures trading"""
    return BacktestConfig(
        leverage=10.0,
        margin_requirement=margin_requirement,
        maintenance_margin=margin_requirement * 0.75,
        fee_flat=2.50,  # Typical futures commission
        fee_pct=0.0,
        slippage_pct=0.0002
    )


def get_forex_config() -> BacktestConfig:
    """Get configuration for forex trading"""
    return BacktestConfig(
        leverage=50.0,
        fee_flat=0.0,
        fee_pct=0.0,  # Fees in spread
        slippage_model="spread",
        tick_size=0.0001,  # Pip
        min_lot_size=1000  # Micro lot
    )


def get_crypto_config() -> BacktestConfig:
    """Get configuration for crypto trading"""
    return BacktestConfig(
        fee_pct=0.001,  # 0.1% maker/taker
        slippage_pct=0.001,
        tick_size=0.01,
        min_lot_size=0.001,  # Fractional coins
        dividend_handling="ignore",
        split_handling="ignore"
    )


# ============================================================================
# CONFIG PRESETS REGISTRY
# ============================================================================

CONFIG_PRESETS = {
    "default": get_default_config,
    "realistic": get_realistic_config,
    "zero_cost": get_zero_cost_config,
    "high_cost": get_high_cost_config,
    "futures": get_futures_config,
    "forex": get_forex_config,
    "crypto": get_crypto_config
}


def get_preset_config(preset_name: str) -> BacktestConfig:
    """
    Get a preset configuration by name
    
    Args:
        preset_name: One of 'default', 'realistic', 'zero_cost', 'high_cost',
                     'futures', 'forex', 'crypto'
    
    Returns:
        BacktestConfig instance
    """
    if preset_name not in CONFIG_PRESETS:
        raise ValueError(
            f"Unknown preset '{preset_name}'. "
            f"Available: {list(CONFIG_PRESETS.keys())}"
        )
    return CONFIG_PRESETS[preset_name]()


# ============================================================================
# CONFIGURATION UTILITIES
# ============================================================================

def merge_configs(base: BacktestConfig, overrides: Dict[str, Any]) -> BacktestConfig:
    """
    Merge override values into a base configuration
    
    Args:
        base: Base configuration
        overrides: Dictionary of values to override
    
    Returns:
        New BacktestConfig with merged values
    """
    config_dict = base.to_dict()
    config_dict.update(overrides)
    return BacktestConfig.from_dict(config_dict)


if __name__ == "__main__":
    # Example usage
    print("Default Config:")
    default = get_default_config()
    print(f"  Start Cash: ${default.start_cash:,.2f}")
    print(f"  Fee: {default.fee_pct*100:.2f}%")
    
    print("\nRealistic Config:")
    realistic = get_realistic_config()
    print(f"  Fee Flat: ${realistic.fee_flat:.2f}")
    print(f"  Fee %: {realistic.fee_pct*100:.2f}%")
    print(f"  Slippage: {realistic.slippage_pct*100:.3f}%")
    
    print("\nFutures Config:")
    futures = get_futures_config()
    print(f"  Leverage: {futures.leverage}x")
    print(f"  Margin Req: {futures.margin_requirement*100:.1f}%")
    
    print("\nAll Presets:", list(CONFIG_PRESETS.keys()))
