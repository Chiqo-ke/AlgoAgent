"""
SimBroker - Stable Backtesting Execution Engine
================================================

A production-ready, immutable backtesting framework with a stable API
for AI-generated trading strategies.

Version: 1.0.0
License: MIT
"""

# Initialize global RequestRouter for key rotation
from .request_router import get_request_router
request_router = get_request_router()

# Core API exports
from .sim_broker import SimBroker, __version__
from .config import (
    BacktestConfig,
    get_default_config,
    get_realistic_config,
    get_zero_cost_config,
    get_high_cost_config,
    get_futures_config,
    get_forex_config,
    get_crypto_config,
    get_preset_config
)
from .canonical_schema import (
    Signal,
    Order,
    Fill,
    Position,
    AccountSnapshot,
    OrderSide,
    OrderAction,
    OrderType,
    OrderStatus,
    SizeType,
    create_signal,
    validate_signal,
    generate_id
)

# Version
__version__ = "1.0.0"
__api_version__ = "1.0.0"

# Data loader (stable module)
from .data_loader import (
    load_market_data,
    load_stock_data,
    get_available_indicators,
    describe_indicator_params
)

# Optional: Gemini strategy generator (requires google-generativeai)
try:
    from .gemini_strategy_generator import GeminiStrategyGenerator, generate_strategy_from_description
    GEMINI_AVAILABLE = True
except ImportError:
    GeminiStrategyGenerator = None
    generate_strategy_from_description = None
    GEMINI_AVAILABLE = False

# Stable API
__all__ = [
    # Main broker
    'SimBroker',
    
    # Configuration
    'BacktestConfig',
    'get_default_config',
    'get_realistic_config',
    'get_zero_cost_config',
    'get_high_cost_config',
    'get_futures_config',
    'get_forex_config',
    'get_crypto_config',
    'get_preset_config',
    
    # Canonical schemas
    'Signal',
    'Order',
    'Fill',
    'Position',
    'AccountSnapshot',
    
    # Enums
    'OrderSide',
    'OrderAction',
    'OrderType',
    'OrderStatus',
    'SizeType',
    
    # Helpers
    'create_signal',
    'validate_signal',
    'generate_id',
    
    # Data loader
    'load_market_data',
    'load_stock_data',
    'get_available_indicators',
    'describe_indicator_params',
    
    # Gemini integration (optional)
    'GeminiStrategyGenerator',
    'generate_strategy_from_description',
    'GEMINI_AVAILABLE',
    
    # Version
    '__version__',
    '__api_version__',
]


def get_info():
    """Get module information"""
    return {
        'name': 'SimBroker',
        'version': __version__,
        'api_version': __api_version__,
        'description': 'Stable backtesting execution engine',
        'components': [
            'SimBroker - Main execution engine',
            'OrderManager - Order lifecycle management',
            'ExecutionSimulator - Fill simulation',
            'AccountManager - Position and P&L tracking',
            'MetricsEngine - Performance metrics',
            'Validators - Risk guardrails'
        ],
        'stable_api': [
            'submit_signal(signal: dict) -> str',
            'get_order(order_id: str) -> dict',
            'cancel_order(order_id: str) -> bool',
            'step_to(timestamp: datetime, market_data: dict)',
            'get_account_snapshot() -> dict',
            'get_equity_curve() -> List[dict]',
            'export_trades(path: str)',
            'compute_metrics() -> dict'
        ]
    }


if __name__ == "__main__":
    # Print module info
    info = get_info()
    print(f"{info['name']} v{info['version']}")
    print(f"API Version: {info['api_version']}")
    print(f"\n{info['description']}")
    print("\nComponents:")
    for component in info['components']:
        print(f"  - {component}")
    print("\nStable API:")
    for method in info['stable_api']:
        print(f"  - {method}")
