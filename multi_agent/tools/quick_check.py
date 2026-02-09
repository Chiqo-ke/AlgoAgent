try:
    import MetaTrader5
    print("MT5 SDK: INSTALLED")
except:
    print("MT5 SDK: NOT INSTALLED")

try:
    import pandas
    print("Pandas: INSTALLED")
except:
    print("Pandas: NOT INSTALLED")

try:
    import numpy
    print("Numpy: INSTALLED")
except:
    print("Numpy: NOT INSTALLED")

print("\nSystem files check:")
import os

files = [
    "frameworks/mt5_trading_framework.py",
    "scrapers/tradingview-scraper.js",
    "strategies/aapl_momentum_trader/main.py"
]

for f in files:
    if os.path.exists(f):
        print(f"[OK] {f}")
    else:
        print(f"[MISSING] {f}")