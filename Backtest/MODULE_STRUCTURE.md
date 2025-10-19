# Backtest Module - Clean Structure

## 📁 Module Overview

The Backtest module provides a complete algorithmic trading backtesting framework with MT5 integration capabilities.

---

## 🏗️ Core Components

### Broker & Execution
- **`sim_broker.py`** - Simulation broker with stable API (IMMUTABLE)
- **`order_manager.py`** - Order lifecycle management
- **`execution_simulator.py`** - Realistic order fills with slippage
- **`account_manager.py`** - Portfolio and position tracking

### Data & Configuration
- **`data_loader.py`** - Historical data loading and preprocessing
- **`config.py`** - Backtest configuration settings
- **`canonical_schema.py`** - Immutable data structure definitions
- **`validators.py`** - Signal and configuration validation

### Metrics & Analysis
- **`metrics_engine.py`** - Performance metrics calculation

---

## 🔌 MT5 Integration (NEW)

### Python Components
- **`signal_exporter.py`** - Export signals to MT5 format
- **`mt5_connector.py`** - MetaTrader5 API integration
- **`mt5_reconciliation.py`** - Compare Python vs MT5 results

### MQL5 Component
- **`PythonSignalExecutor.mq5`** - Expert Advisor for MT5

### Examples & Tests
- **`example_mt5_integration.py`** - Complete workflow demonstration
- **`test_mt5_integration.py`** - Integration tests

---

## 🤖 AI Strategy Generation

### Gemini Integration
- **`gemini_strategy_generator.py`** - AI-powered strategy generation
- **`example_gemini_strategy.py`** - Example of AI-generated strategy
- **`quick_generate.py`** - Quick strategy generation script
- **`test_gemini_integration.py`** - Gemini integration tests

---

## 📚 Documentation

### MT5 Integration Docs
- **`MT5_INTEGRATION_GUIDE.md`** - Comprehensive MT5 guide (1,200+ lines)
- **`MT5_QUICK_REFERENCE.md`** - Quick lookup and troubleshooting
- **`README_MT5_INTEGRATION.md`** - Executive summary
- **`MQL5_SETUP_GUIDE.md`** - Step-by-step setup procedure
- **`MQL5_CODE_SPECIFICATION.md`** - AI-friendly code generation spec

### Reference Docs
- **`API_REFERENCE.md`** - SimBroker API documentation
- **`QUICK_START_GUIDE.md`** - Getting started guide
- **`STRATEGY_TEMPLATE.md`** - Template for creating strategies
- **`SYSTEM_PROMPT.md`** - AI system prompt for strategy generation
- **`GEMINI_INTEGRATION_GUIDE.md`** - Gemini AI integration guide
- **`README.md`** - Main module documentation

---

## 📝 Example Strategies

### Reference Examples (KEEP)
- **`example_strategy.py`** - Well-documented MA crossover strategy
- **`example_mt5_integration.py`** - MT5 integration workflow

### AI-Generated Examples
- **`example_gemini_strategy.py`** - Example from Gemini AI

---

## 🧪 Test Files

- **`test_mt5_integration.py`** - MT5 integration tests ✓
- **`test_gemini_integration.py`** - Gemini tests
- **`test_data_loader.py`** - Data loader tests

---

## 🗂️ Data Directories

- **`data/`** - Historical market data
- **`mt5_signals/`** - Exported MT5 signal files
- **`results/`** - Backtest results (trades, metrics)
- **`test_output/`** - Test outputs
- **`codes/`** - Generated strategy code storage

---

## 🛠️ Utilities

- **`cleanup_old_files.py`** - Module cleanup script
- **`generate.bat`** - Windows batch file for generation
- **`__init__.py`** - Package initialization

---

## 📊 Current Status

✅ **Clean** - Removed 8 outdated documentation files (74 KB)  
✅ **Organized** - Clear separation of concerns  
✅ **Documented** - Comprehensive guides and references  
✅ **Tested** - All integration tests passing  
✅ **Production Ready** - MT5 integration fully functional  

---

## 🚀 Quick Start

### Basic Backtest
```python
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig

config = BacktestConfig(start_cash=10000)
broker = SimBroker(config)

# Your strategy code here
# ...

metrics = broker.compute_metrics()
```

### With MT5 Export
```python
broker = SimBroker(
    config=config,
    enable_mt5_export=True,
    mt5_symbol="XAUUSD",
    mt5_timeframe="H1"
)

# Run backtest
# ...

# Export signals
broker.export_mt5_signals(format="csv")
```

### Generate AI Strategy
```python
from Backtest.gemini_strategy_generator import GeminiStrategyGenerator

generator = GeminiStrategyGenerator(api_key="your_key")
code = generator.generate_strategy(
    description="RSI strategy with MA confirmation"
)
```

---

## 📦 Dependencies

### Core
- pandas >= 1.5.0
- numpy >= 1.20.0

### Optional
- MetaTrader5 >= 5.0.0 (for MT5 integration)
- google-generativeai (for Gemini AI)
- yfinance (for data fetching)
- talib (for technical indicators)

---

## 🔗 Key Documentation

- **Getting Started**: See `QUICK_START_GUIDE.md`
- **MT5 Integration**: See `MT5_QUICK_REFERENCE.md` (5-min guide)
- **API Reference**: See `API_REFERENCE.md`
- **Strategy Template**: See `STRATEGY_TEMPLATE.md`

---

## 📝 Notes

- The `SimBroker` API is **immutable** and should not be modified
- All data structures follow the canonical schema
- MT5 integration is backward compatible (optional)
- Old summary files have been cleaned up (see `DELETED_FILES_*.txt`)

---

## 🎯 Next Steps

1. Review `QUICK_START_GUIDE.md` for basic usage
2. Try `example_strategy.py` to understand the pattern
3. For MT5 validation, see `MT5_QUICK_REFERENCE.md`
4. For AI generation, check `GEMINI_INTEGRATION_GUIDE.md`

---

**Last Updated**: October 19, 2025  
**Status**: Production Ready ✓  
**Version**: 1.0.0
