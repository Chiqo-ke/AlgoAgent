"""
Validators and Guardrails
==========================

Validation checks and risk guardrails for the backtesting system.

Last updated: 2025-10-16
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional
import logging

from .canonical_schema import Signal, validate_signal, OrderAction
from .config import BacktestConfig


logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Validation error exception"""
    pass


class ValidationWarning:
    """Validation warning (non-fatal)"""
    def __init__(self, message: str, severity: str = "WARNING"):
        self.message = message
        self.severity = severity


class Validators:
    """
    Signal validation and risk guardrails
    
    Responsibilities:
    - Validate signal schemas
    - Check risk parameters
    - Enforce position limits
    - Warn about risky configurations
    """
    
    def __init__(self, config: BacktestConfig):
        """
        Initialize validators
        
        Args:
            config: Backtest configuration
        """
        self.config = config
        self.warnings: List[ValidationWarning] = []
    
    def validate_signal(self, signal: Signal) -> List[str]:
        """
        Validate a signal against canonical schema
        
        Args:
            signal: Signal to validate
        
        Returns:
            List of error messages (empty if valid)
        """
        # Use canonical validation
        errors = validate_signal(signal.to_dict())
        
        # Additional business logic validation
        if signal.size <= 0:
            errors.append("Signal size must be positive")
        
        if signal.action == OrderAction.ENTRY:
            # Check for stop loss if required
            if self.config.require_stop_loss:
                if not signal.risk_params or not signal.risk_params.get('stop_loss_price'):
                    warning = ValidationWarning(
                        f"Entry signal for {signal.symbol} has no stop loss defined"
                    )
                    self.warnings.append(warning)
                    logger.warning(warning.message)
        
        return errors
    
    def check_position_size_limit(
        self,
        symbol: str,
        requested_size: float,
        current_size: float = 0.0
    ) -> bool:
        """
        Check if position size is within limits
        
        Args:
            symbol: Symbol to check
            requested_size: Requested position size
            current_size: Current position size
        
        Returns:
            True if within limits, False otherwise
        """
        if self.config.max_position_size is None:
            return True
        
        total_size = abs(current_size) + requested_size
        
        if total_size > self.config.max_position_size:
            logger.error(
                f"Position size limit exceeded for {symbol}: "
                f"{total_size} > {self.config.max_position_size}"
            )
            return False
        
        return True
    
    def check_leverage_limit(
        self,
        equity: float,
        portfolio_value: float
    ) -> bool:
        """
        Check if leverage is within limits
        
        Args:
            equity: Current equity
            portfolio_value: Total portfolio value
        
        Returns:
            True if within limits, False otherwise
        """
        if equity <= 0:
            return False
        
        current_leverage = portfolio_value / equity
        
        if current_leverage > self.config.leverage:
            logger.error(
                f"Leverage limit exceeded: "
                f"{current_leverage:.2f}x > {self.config.leverage}x"
            )
            return False
        
        return True
    
    def check_drawdown_stop(
        self,
        current_equity: float,
        peak_equity: float
    ) -> bool:
        """
        Check if max drawdown stop should be triggered
        
        Args:
            current_equity: Current equity
            peak_equity: Peak equity reached
        
        Returns:
            True if stop should be triggered, False otherwise
        """
        if self.config.max_drawdown_stop is None:
            return False
        
        if peak_equity <= 0:
            return False
        
        drawdown_pct = (peak_equity - current_equity) / peak_equity
        
        if drawdown_pct >= self.config.max_drawdown_stop:
            logger.error(
                f"Max drawdown stop triggered: "
                f"{drawdown_pct*100:.2f}% >= {self.config.max_drawdown_stop*100:.2f}%"
            )
            return True
        
        return False
    
    def check_margin_available(
        self,
        required_margin: float,
        available_margin: float
    ) -> bool:
        """
        Check if sufficient margin available
        
        Args:
            required_margin: Margin required for trade
            available_margin: Available margin
        
        Returns:
            True if sufficient, False otherwise
        """
        if required_margin > available_margin:
            logger.error(
                f"Insufficient margin: required {required_margin:.2f}, "
                f"available {available_margin:.2f}"
            )
            return False
        
        return True
    
    def validate_backtest_config(self) -> List[ValidationWarning]:
        """
        Validate backtest configuration for risky settings
        
        Returns:
            List of warnings (empty if no issues)
        """
        warnings = []
        
        # Check for zero fees
        if self.config.fee_flat == 0 and self.config.fee_pct == 0:
            warnings.append(ValidationWarning(
                "Zero fees configured - results may be overly optimistic",
                severity="WARNING"
            ))
        
        # Check for zero slippage
        if self.config.slippage_pct == 0 and self.config.slippage_const == 0:
            warnings.append(ValidationWarning(
                "Zero slippage configured - results may be overly optimistic",
                severity="WARNING"
            ))
        
        # Check for aggressive fill policy
        if self.config.fill_policy == "aggressive":
            warnings.append(ValidationWarning(
                "Aggressive fill policy may produce unrealistic results",
                severity="INFO"
            ))
        
        # Check for high leverage
        if self.config.leverage > 5:
            warnings.append(ValidationWarning(
                f"High leverage configured ({self.config.leverage}x) - "
                "results may be volatile",
                severity="WARNING"
            ))
        
        # Check if stop loss required but not enforced
        if self.config.require_stop_loss:
            logger.info("Stop loss requirement enabled - will warn on entry signals without stops")
        
        return warnings
    
    def get_warnings(self) -> List[ValidationWarning]:
        """Get all accumulated warnings"""
        return self.warnings
    
    def clear_warnings(self):
        """Clear accumulated warnings"""
        self.warnings.clear()
    
    def log_warnings(self):
        """Log all warnings"""
        if not self.warnings:
            return
        
        logger.info(f"=== Validation Warnings ({len(self.warnings)}) ===")
        for warning in self.warnings:
            if warning.severity == "ERROR":
                logger.error(warning.message)
            elif warning.severity == "WARNING":
                logger.warning(warning.message)
            else:
                logger.info(warning.message)


if __name__ == "__main__":
    # Example usage
    from canonical_schema import create_signal, OrderSide, OrderType, OrderAction
    from datetime import datetime
    
    logging.basicConfig(level=logging.INFO)
    
    config = BacktestConfig(
        require_stop_loss=True,
        max_position_size=1000,
        leverage=2.0
    )
    
    validators = Validators(config)
    
    # Validate config
    config_warnings = validators.validate_backtest_config()
    print(f"Config warnings: {len(config_warnings)}")
    for w in config_warnings:
        print(f"  [{w.severity}] {w.message}")
    
    # Validate a signal
    signal = create_signal(
        timestamp=datetime.utcnow(),
        symbol="AAPL",
        side=OrderSide.BUY,
        action=OrderAction.ENTRY,
        order_type=OrderType.MARKET,
        size=100
    )
    
    errors = validators.validate_signal(signal)
    print(f"\nSignal validation errors: {len(errors)}")
    for e in errors:
        print(f"  - {e}")
    
    validators.log_warnings()
