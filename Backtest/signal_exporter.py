"""
Signal Exporter for MT5 Integration
====================================

Exports trading signals from Python backtests to MT5-compatible formats.
Enables Python-based strategy generation with MT5 execution validation.

References:
- MetaTrader5 Python API: https://www.mql5.com/en/docs/python_metatrader5
- MQL5 File Operations: https://www.mql5.com/en/docs/files

Last updated: 2025-10-18
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pathlib import Path
import json
import csv
import logging
from dataclasses import dataclass, asdict

from .canonical_schema import Signal, OrderSide, OrderAction


logger = logging.getLogger(__name__)


@dataclass
class MT5Signal:
    """
    MT5-compatible signal format
    
    Fields optimized for MT5 Expert Advisor consumption:
    - timestamp: ISO 8601 format with timezone
    - symbol: MT5 symbol name (e.g., "XAUUSD")
    - signal: BUY/SELL/EXIT/HOLD
    - lot_size: MT5 lot size (not shares/contracts)
    - stop_loss: Absolute price level (0 = no SL)
    - take_profit: Absolute price level (0 = no TP)
    - signal_id: Unique identifier for tracking
    - metadata: Additional context (JSON string)
    """
    timestamp: str
    symbol: str
    signal: str
    lot_size: float
    stop_loss: float
    take_profit: float
    signal_id: str
    metadata: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_csv_row(self) -> List[str]:
        """Convert to CSV row"""
        return [
            self.timestamp,
            self.symbol,
            self.signal,
            f"{self.lot_size:.2f}",
            f"{self.stop_loss:.5f}",
            f"{self.take_profit:.5f}",
            self.signal_id,
            self.metadata
        ]


class SignalExporter:
    """
    Exports trading signals to MT5-compatible formats
    
    Supports:
    - CSV export (simple, fast parsing in MQL5)
    - JSON export (flexible, rich metadata)
    - Automatic lot size conversion
    - Timestamp formatting for MT5
    """
    
    # Symbol-specific lot size conversions
    # Format: {symbol: shares_per_lot}
    LOT_SIZE_CONVERSIONS = {
        "XAUUSD": 100,      # 1 lot = 100 oz of gold
        "XAGUSD": 5000,     # 1 lot = 5000 oz of silver
        "EURUSD": 100000,   # 1 lot = 100,000 EUR
        "GBPUSD": 100000,   # 1 lot = 100,000 GBP
        "USDJPY": 100000,   # 1 lot = 100,000 USD
        "BTCUSD": 1,        # 1 lot = 1 BTC
    }
    
    def __init__(
        self,
        output_dir: Path,
        backtest_id: str,
        symbol: str = "XAUUSD",
        timeframe: str = "H1",
        default_lot_size: float = 0.1,
        include_hold_signals: bool = False
    ):
        """
        Initialize signal exporter
        
        Args:
            output_dir: Directory to save signal files
            backtest_id: Unique identifier for this backtest
            symbol: Trading symbol (MT5 format)
            timeframe: MT5 timeframe (M1, M5, M15, M30, H1, H4, D1, etc.)
            default_lot_size: Default lot size if not specified in signal
            include_hold_signals: Whether to export HOLD signals (or omit)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.backtest_id = backtest_id
        self.symbol = symbol
        self.timeframe = timeframe
        self.default_lot_size = default_lot_size
        self.include_hold_signals = include_hold_signals
        
        # Storage
        self.signals: List[MT5Signal] = []
        self.signal_count = 0
        
        # Get lot conversion factor
        self.shares_per_lot = self.LOT_SIZE_CONVERSIONS.get(symbol, 100000)
        
        logger.info(
            f"SignalExporter initialized: {backtest_id} | "
            f"{symbol} {timeframe} | "
            f"Lot conversion: {self.shares_per_lot} shares/lot"
        )
    
    def add_signal(
        self,
        signal: Signal,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> None:
        """
        Add a signal for export
        
        Args:
            signal: Signal object from strategy
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
        """
        # Convert signal to MT5 format
        mt5_signal = self._convert_signal(signal, stop_loss, take_profit)
        
        # Filter HOLD signals if requested
        if not self.include_hold_signals and mt5_signal.signal == "HOLD":
            return
        
        self.signals.append(mt5_signal)
        self.signal_count += 1
    
    def _convert_signal(
        self,
        signal: Signal,
        stop_loss: Optional[float],
        take_profit: Optional[float]
    ) -> MT5Signal:
        """
        Convert canonical signal to MT5 format
        
        Args:
            signal: Canonical signal
            stop_loss: Stop loss price
            take_profit: Take profit price
        
        Returns:
            MT5Signal object
        """
        # Determine signal type
        mt5_signal_type = self._get_mt5_signal_type(signal)
        
        # Convert lot size
        lot_size = self._convert_to_lots(signal.size)
        
        # Format timestamp (ISO 8601 with UTC)
        timestamp_str = signal.timestamp.replace(tzinfo=timezone.utc).isoformat()
        
        # Prepare metadata
        metadata = {
            "strategy_id": signal.strategy_id,
            "action": signal.action,
            "order_type": signal.order_type,
            **signal.meta
        }
        metadata_str = json.dumps(metadata, default=str)
        
        return MT5Signal(
            timestamp=timestamp_str,
            symbol=self.symbol,
            signal=mt5_signal_type,
            lot_size=lot_size,
            stop_loss=stop_loss or 0.0,
            take_profit=take_profit or 0.0,
            signal_id=signal.signal_id,
            metadata=metadata_str
        )
    
    def _get_mt5_signal_type(self, signal: Signal) -> str:
        """
        Convert canonical signal to MT5 signal type
        
        Args:
            signal: Canonical signal
        
        Returns:
            MT5 signal type: BUY/SELL/EXIT/HOLD
        """
        if signal.action == OrderAction.EXIT:
            return "EXIT"
        
        if signal.action == OrderAction.ENTRY:
            if signal.side == OrderSide.BUY:
                return "BUY"
            elif signal.side == OrderSide.SELL:
                return "SELL"
        
        # Default to HOLD for other actions
        return "HOLD"
    
    def _convert_to_lots(self, size: float) -> float:
        """
        Convert shares/contracts to MT5 lots
        
        Args:
            size: Position size in shares/contracts
        
        Returns:
            Lot size for MT5
        """
        if size <= 0:
            return self.default_lot_size
        
        # Convert shares to lots
        lots = size / self.shares_per_lot
        
        # Round to 2 decimal places (standard MT5 precision)
        lots = round(lots, 2)
        
        # Ensure minimum lot size
        if lots < 0.01:
            lots = 0.01
        
        return lots
    
    def export_csv(self, filename: Optional[str] = None) -> Path:
        """
        Export signals to CSV file
        
        CSV format is optimal for fast parsing in MQL5.
        
        Args:
            filename: Output filename (auto-generated if None)
        
        Returns:
            Path to exported file
        """
        if filename is None:
            filename = f"{self.backtest_id}_{self.symbol}_{self.timeframe}_signals.csv"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Timestamp',
                'Symbol',
                'Signal',
                'LotSize',
                'StopLoss',
                'TakeProfit',
                'SignalID',
                'Metadata'
            ])
            
            # Write signals
            for signal in self.signals:
                writer.writerow(signal.to_csv_row())
        
        logger.info(f"Exported {len(self.signals)} signals to CSV: {filepath}")
        return filepath
    
    def export_json(self, filename: Optional[str] = None) -> Path:
        """
        Export signals to JSON file
        
        JSON format provides more flexibility and richer metadata.
        
        Args:
            filename: Output filename (auto-generated if None)
        
        Returns:
            Path to exported file
        """
        if filename is None:
            filename = f"{self.backtest_id}_{self.symbol}_{self.timeframe}_signals.json"
        
        filepath = self.output_dir / filename
        
        export_data = {
            "backtest_id": self.backtest_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "export_timestamp": datetime.utcnow().isoformat(),
            "signal_count": len(self.signals),
            "shares_per_lot": self.shares_per_lot,
            "signals": [signal.to_dict() for signal in self.signals]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported {len(self.signals)} signals to JSON: {filepath}")
        return filepath
    
    def export_both(self) -> tuple[Path, Path]:
        """
        Export to both CSV and JSON formats
        
        Returns:
            Tuple of (csv_path, json_path)
        """
        csv_path = self.export_csv()
        json_path = self.export_json()
        return csv_path, json_path
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get export summary statistics
        
        Returns:
            Dictionary with summary information
        """
        signal_types = {}
        for signal in self.signals:
            signal_types[signal.signal] = signal_types.get(signal.signal, 0) + 1
        
        return {
            "backtest_id": self.backtest_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "total_signals": len(self.signals),
            "signal_types": signal_types,
            "shares_per_lot": self.shares_per_lot,
            "default_lot_size": self.default_lot_size
        }
    
    def validate_signals(self) -> List[str]:
        """
        Validate exported signals for common issues
        
        Returns:
            List of validation warnings (empty if all OK)
        """
        warnings = []
        
        if len(self.signals) == 0:
            warnings.append("No signals to export")
            return warnings
        
        # Check for duplicate timestamps
        timestamps = [s.timestamp for s in self.signals]
        if len(timestamps) != len(set(timestamps)):
            warnings.append("Duplicate timestamps detected")
        
        # Check chronological order
        for i in range(1, len(self.signals)):
            if self.signals[i].timestamp < self.signals[i-1].timestamp:
                warnings.append("Signals not in chronological order")
                break
        
        # Check for invalid lot sizes
        for signal in self.signals:
            if signal.lot_size < 0.01:
                warnings.append(f"Invalid lot size: {signal.lot_size}")
                break
        
        # Check for signals without symbol match
        for signal in self.signals:
            if signal.symbol != self.symbol:
                warnings.append(f"Signal symbol mismatch: {signal.symbol}")
                break
        
        return warnings
