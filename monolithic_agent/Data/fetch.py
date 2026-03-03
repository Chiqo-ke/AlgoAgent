"""
Warehouse data fetcher — fetches all required symbol/interval combinations
and saves them in warehouse format: data/<symbol_lower>_<interval>.csv

Skips files that already exist in the warehouse.
Run from the Data/ directory:
    python fetch.py
"""
import os
from pathlib import Path
from tvDatafeed import TvDatafeed, Interval
import pandas as pd

tv = TvDatafeed()

WAREHOUSE_DIR = Path(__file__).parent / "data"
WAREHOUSE_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Master fetch list: (symbol, exchange, Interval, filename_suffix)
# filename will be: data/<symbol_lower>_<suffix>.csv
#
# Intervals used:
#   Interval.in_1_hour  -> 1h
#   Interval.in_2_hour  -> 2h
#   Interval.in_4_hour  -> 4h
#   Interval.in_daily   -> 1d
# ---------------------------------------------------------------------------
FETCH_LIST = [
    # ── Equities ─────────────────────────────────────────────────────────────
    # AAPL (missing: 1h, 2h, 4h)
    ('AAPL',   'NASDAQ',    Interval.in_1_hour,  'aapl_1h.csv'),
    ('AAPL',   'NASDAQ',    Interval.in_2_hour,  'aapl_2h.csv'),
    ('AAPL',   'NASDAQ',    Interval.in_4_hour,  'aapl_4h.csv'),

    # MSFT (missing: 1h, 2h)
    ('MSFT',   'NASDAQ',    Interval.in_1_hour,  'msft_1h.csv'),
    ('MSFT',   'NASDAQ',    Interval.in_2_hour,  'msft_2h.csv'),

    # TSLA — all intervals already present, kept here for reference (will be skipped)
    # ('TSLA', 'NASDAQ', Interval.in_daily,   'tsla_1d.csv'),   # exists

    # NVDA (all missing)
    ('NVDA',   'NASDAQ',    Interval.in_1_hour,  'nvda_1h.csv'),
    ('NVDA',   'NASDAQ',    Interval.in_2_hour,  'nvda_2h.csv'),
    ('NVDA',   'NASDAQ',    Interval.in_4_hour,  'nvda_4h.csv'),
    ('NVDA',   'NASDAQ',    Interval.in_daily,   'nvda_1d.csv'),

    # GOOGL (all missing)
    ('GOOGL',  'NASDAQ',    Interval.in_1_hour,  'googl_1h.csv'),
    ('GOOGL',  'NASDAQ',    Interval.in_2_hour,  'googl_2h.csv'),
    ('GOOGL',  'NASDAQ',    Interval.in_4_hour,  'googl_4h.csv'),
    ('GOOGL',  'NASDAQ',    Interval.in_daily,   'googl_1d.csv'),

    # AMZN (all missing)
    ('AMZN',   'NASDAQ',    Interval.in_1_hour,  'amzn_1h.csv'),
    ('AMZN',   'NASDAQ',    Interval.in_2_hour,  'amzn_2h.csv'),
    ('AMZN',   'NASDAQ',    Interval.in_4_hour,  'amzn_4h.csv'),
    ('AMZN',   'NASDAQ',    Interval.in_daily,   'amzn_1d.csv'),

    # SPY (all missing)
    ('SPY',    'AMEX',      Interval.in_1_hour,  'spy_1h.csv'),
    ('SPY',    'AMEX',      Interval.in_2_hour,  'spy_2h.csv'),
    ('SPY',    'AMEX',      Interval.in_4_hour,  'spy_4h.csv'),
    ('SPY',    'AMEX',      Interval.in_daily,   'spy_1d.csv'),

    # QQQ (all missing)
    ('QQQ',    'NASDAQ',    Interval.in_1_hour,  'qqq_1h.csv'),
    ('QQQ',    'NASDAQ',    Interval.in_2_hour,  'qqq_2h.csv'),
    ('QQQ',    'NASDAQ',    Interval.in_4_hour,  'qqq_4h.csv'),
    ('QQQ',    'NASDAQ',    Interval.in_daily,   'qqq_1d.csv'),

    # ── Forex ─────────────────────────────────────────────────────────────────
    # EURUSD (missing: 1d)
    ('EURUSD', 'FX',        Interval.in_daily,   'eurusd_1d.csv'),

    # GBPUSD (all missing)
    ('GBPUSD', 'FX',        Interval.in_1_hour,  'gbpusd_1h.csv'),
    ('GBPUSD', 'FX',        Interval.in_2_hour,  'gbpusd_2h.csv'),
    ('GBPUSD', 'FX',        Interval.in_4_hour,  'gbpusd_4h.csv'),
    ('GBPUSD', 'FX',        Interval.in_daily,   'gbpusd_1d.csv'),

    # USDJPY (all missing)
    ('USDJPY', 'FX',        Interval.in_1_hour,  'usdjpy_1h.csv'),
    ('USDJPY', 'FX',        Interval.in_2_hour,  'usdjpy_2h.csv'),
    ('USDJPY', 'FX',        Interval.in_4_hour,  'usdjpy_4h.csv'),
    ('USDJPY', 'FX',        Interval.in_daily,   'usdjpy_1d.csv'),

    # ── Commodities ───────────────────────────────────────────────────────────
    # XAUUSD (missing: 1d — the file that broke XAUUSD backtests)
    ('XAUUSD', 'TVC',       Interval.in_daily,   'xauusd_1d.csv'),

    # ── Crypto ────────────────────────────────────────────────────────────────
    ('BTCUSD', 'BITSTAMP',  Interval.in_1_hour,  'btcusd_1h.csv'),
    ('BTCUSD', 'BITSTAMP',  Interval.in_2_hour,  'btcusd_2h.csv'),
    ('BTCUSD', 'BITSTAMP',  Interval.in_4_hour,  'btcusd_4h.csv'),
    ('BTCUSD', 'BITSTAMP',  Interval.in_daily,   'btcusd_1d.csv'),

    ('ETHUSD', 'BITSTAMP',  Interval.in_1_hour,  'ethusd_1h.csv'),
    ('ETHUSD', 'BITSTAMP',  Interval.in_2_hour,  'ethusd_2h.csv'),
    ('ETHUSD', 'BITSTAMP',  Interval.in_4_hour,  'ethusd_4h.csv'),
    ('ETHUSD', 'BITSTAMP',  Interval.in_daily,   'ethusd_1d.csv'),
]

# ---------------------------------------------------------------------------
# Fetch loop
# ---------------------------------------------------------------------------
total   = len(FETCH_LIST)
skipped = 0
fetched = 0
failed  = 0

for i, (symbol, exchange, interval, filename) in enumerate(FETCH_LIST, 1):
    output_file = WAREHOUSE_DIR / filename

    # Skip if already in warehouse
    if output_file.exists():
        print(f"[{i}/{total}] SKIP  {filename} — already in warehouse")
        skipped += 1
        continue

    print(f"[{i}/{total}] FETCH {symbol} ({exchange}) {interval.value} -> {filename} ...")
    try:
        data = tv.get_hist(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            n_bars=4000,
        )
    except Exception as e:
        print(f"  [ERROR] API call failed: {e}")
        failed += 1
        continue

    if data is None or data.empty:
        print(f"  [WARN] No data returned — skipping.")
        failed += 1
        continue

    # Flatten tvDatafeed MultiIndex (symbol, datetime)
    df = data.reset_index()

    # Normalise column names to warehouse schema
    df = df.rename(columns={
        'datetime': 'datetime',
        'symbol':   'symbol',
        'open':     'open',
        'high':     'high',
        'low':      'low',
        'close':    'close',
        'volume':   'volume',
    })

    # Keep only required columns
    available_cols = [c for c in ['datetime', 'symbol', 'open', 'high', 'low', 'close', 'volume'] if c in df.columns]
    df = df[available_cols]

    # Normalise symbol column value
    df['symbol'] = symbol

    df.to_csv(output_file, index=False)
    print(f"  [OK]  {len(df)} bars -> {output_file}")
    fetched += 1

print(f"\nDone. Fetched: {fetched}  Skipped: {skipped}  Failed: {failed}  Total: {total}")

