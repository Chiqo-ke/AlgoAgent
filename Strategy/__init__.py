"""
AlgoAgent Strategy Module
=========================

AI-powered strategy validation, canonicalization, and analysis.
"""

__version__ = "1.0.0"
__all__ = [
    "StrategyValidatorBot",
    "CanonicalStrategy",
    "InputParser",
    "GeminiStrategyIntegrator",
]

# Make key classes easily importable
try:
    from .strategy_validator import StrategyValidatorBot, validate_strategy
except ImportError:
    pass

try:
    from .canonical_schema import CanonicalStrategy, CANONICAL_STRATEGY_SCHEMA
except ImportError:
    pass

try:
    from .input_parser import InputParser, parse_strategy_input
except ImportError:
    pass

try:
    from .gemini_strategy_integrator import GeminiStrategyIntegrator
except ImportError:
    pass
