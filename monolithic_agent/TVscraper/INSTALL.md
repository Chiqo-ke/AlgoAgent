# Installation Guide

## Making TVScraper a Pip Package

This guide shows you how to install TVScraper as a proper Python package in your virtual environment.

## 📦 Installation Methods

### Method 1: Editable Installation (Development Mode) ⭐ RECOMMENDED

This installs the package in "editable" mode, meaning changes to the code are immediately reflected without reinstalling:

```bash
# Navigate to the TVscraper directory
cd C:\Users\nyaga\Documents\TVscraper

# Activate your virtual environment
& C:\Users\nyaga\Documents\.venv\Scripts\Activate.ps1

# Install in editable mode
pip install -e .
```

**Benefits:**
- ✅ Import from anywhere: `from tvscraper import MCPTradingViewScraper`
- ✅ Code changes take effect immediately
- ✅ No need to reinstall after updates
- ✅ CLI command available: `tvscraper --symbol AAPL`

### Method 2: Standard Installation

For production use or when you don't need to modify the code:

```bash
cd C:\Users\nyaga\Documents\TVscraper
pip install .
```

### Method 3: Install from GitHub (Future)

Once published to GitHub:

```bash
pip install git+https://github.com/yourusername/tvscraper.git
```

### Method 4: Install from PyPI (Future)

Once published to PyPI:

```bash
pip install tvscraper
```

## ✅ Verify Installation

After installation, test that it works:

```python
# Test import
python -c "from tvscraper import MCPTradingViewScraper; print('✓ Import successful')"

# Check version
python -c "import tvscraper; print(f'Version: {tvscraper.__version__}')"

# Test CLI
tvscraper --help
```

## 🚀 Usage After Installation

### Using in Python Scripts

Once installed, you can use it from **any directory** in your projects:

```python
# File: C:\Users\nyaga\Documents\MyProject\trading_bot.py
from tvscraper import MCPTradingViewScraper

scraper = MCPTradingViewScraper()
scraper.init_browser()
scraper.navigate_to_tradingview()
scraper.change_symbol("AAPL")
data = scraper.get_historical_data(bars_count=100)
print(f"Fetched {len(data)} bars")
```

### Using Short Aliases

```python
# Use convenient aliases
from tvscraper import Scraper, TVScraper

# Both are the same as MCPTradingViewScraper
scraper = Scraper()
scraper = TVScraper()
```

### Using the CLI

```bash
# Fetch AAPL data
tvscraper --symbol AAPL --timeframe 1h --bars 100

# Fetch MSFT with date range
tvscraper --symbol MSFT --from 2026-01-01 --to 2026-02-01 --output msft_data.csv

# Fetch with indicators
tvscraper --symbol TSLA --indicator RSI --indicator EMA --bars 200
```

## 🔄 Updating the Package

### If Installed in Editable Mode

No action needed! Changes are automatically reflected.

### If Installed Normally

```bash
cd C:\Users\nyaga\Documents\TVscraper
pip install --upgrade .
```

## 🗑️ Uninstalling

```bash
pip uninstall tvscraper
```

## 📁 Package Structure

After installation, your package is structured as:

```
tvscraper/
├── __init__.py          # Exports MCPTradingViewScraper, Scraper, etc.
├── mcp_scraper.py       # Main scraper class
├── scraper.py           # Legacy scraper
├── indicators.py        # Indicator management
├── cli.py               # Command-line interface
├── config.py            # Configuration
└── utils.py             # Utility functions
```

## 🎯 Development Workflow

For developers modifying the package:

```bash
# 1. Clone/navigate to repo
cd C:\Users\nyaga\Documents\TVscraper

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# 3. Install in editable mode with dev dependencies
pip install -e ".[dev]"

# 4. Make changes to code
# Changes are immediately available!

# 5. Test your changes
python examples/mcp_live_demo.py

# 6. Run tests (if you add them later)
pytest tests/
```

## 🐛 Troubleshooting

### Import Error After Installation

```python
# Error: ModuleNotFoundError: No module named 'tvscraper'

# Solution: Verify installation
pip list | grep tvscraper

# Reinstall if needed
pip install -e .
```

### CLI Command Not Found

```bash
# Error: tvscraper: command not found

# Solution 1: Reinstall
pip uninstall tvscraper
pip install -e .

# Solution 2: Use python -m
python -m tvscraper.cli --help
```

### Changes Not Reflected

```python
# If installed normally (not editable), reinstall:
pip install --upgrade --force-reinstall .

# Or switch to editable mode:
pip uninstall tvscraper
pip install -e .
```

## 📚 Next Steps

1. **Install the package**: `pip install -e .`
2. **Test it**: `python -c "from tvscraper import MCPTradingViewScraper"`
3. **Use it anywhere**: Import in any Python file in your venv
4. **Try the CLI**: `tvscraper --symbol AAPL --bars 50`

---

**You're all set!** The scraper is now a proper pip package that behaves like any other Python library. 🎉
