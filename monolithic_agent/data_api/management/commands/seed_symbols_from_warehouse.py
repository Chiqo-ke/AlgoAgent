"""
Management command: seed_symbols_from_warehouse
================================================
Scans the Data/data folder, extracts unique ticker symbols from CSV filenames,
and upserts them into the Symbol table. Safe to run multiple times (idempotent).

Usage:
    python manage.py seed_symbols_from_warehouse
    python manage.py seed_symbols_from_warehouse --data-dir /custom/path
"""

import re
from pathlib import Path

from django.core.management.base import BaseCommand

# ------------------------------------------------------------------
# Static metadata for known symbols
# Format: ticker -> (full_name, exchange, sector, industry)
# ------------------------------------------------------------------
SYMBOL_META = {
    # Equities
    "AAPL":   ("Apple Inc.",           "NASDAQ", "Technology",       "Consumer Electronics"),
    "AMZN":   ("Amazon.com Inc.",      "NASDAQ", "Consumer Cyclical", "Internet Retail"),
    "GOOGL":  ("Alphabet Inc.",        "NASDAQ", "Technology",       "Internet Content & Information"),
    "MSFT":   ("Microsoft Corporation","NASDAQ", "Technology",       "Software - Infrastructure"),
    "NVDA":   ("NVIDIA Corporation",   "NASDAQ", "Technology",       "Semiconductors"),
    "TSLA":   ("Tesla Inc.",           "NASDAQ", "Consumer Cyclical", "Auto Manufacturers"),
    # ETFs
    "SPY":    ("SPDR S&P 500 ETF Trust","NYSE",  "ETF",              "Large-Cap Blend"),
    "QQQ":    ("Invesco QQQ Trust",    "NASDAQ", "ETF",              "Large-Cap Growth"),
    # Forex
    "EURUSD": ("Euro / US Dollar",     "FOREX",  "Forex",            "Major Pair"),
    "GBPUSD": ("British Pound / US Dollar","FOREX","Forex",          "Major Pair"),
    "USDJPY": ("US Dollar / Japanese Yen","FOREX","Forex",           "Major Pair"),
    # Crypto
    "BTCUSD": ("Bitcoin / US Dollar",  "CRYPTO", "Cryptocurrency",   "Digital Currency"),
    "ETHUSD": ("Ethereum / US Dollar", "CRYPTO", "Cryptocurrency",   "Digital Currency"),
    # Commodities
    "XAUUSD": ("Gold / US Dollar",     "COMEX",  "Commodity",        "Precious Metals"),
}

# Regex: filename is  <symbol>_<interval>.csv
_FILENAME_RE = re.compile(r"^([a-zA-Z0-9]+)_[0-9]+[hdwm]\.csv$", re.IGNORECASE)


def _default_data_dir() -> Path:
    """Return the default Data/data directory relative to manage.py."""
    base = Path(__file__).resolve().parents[4]   # monolithic_agent/
    return base / "Data" / "data"


def discover_symbols(data_dir: Path) -> list[str]:
    """Return sorted unique ticker strings found in CSV filenames."""
    tickers: set[str] = set()
    for csv_file in data_dir.glob("*.csv"):
        m = _FILENAME_RE.match(csv_file.name)
        if m:
            tickers.add(m.group(1).upper())
    return sorted(tickers)


class Command(BaseCommand):
    help = "Seed the Symbol table from CSV filenames in the data warehouse"

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-dir",
            type=str,
            default=None,
            help="Path to the data warehouse folder (defaults to Data/data/)",
        )
        parser.add_argument(
            "--deactivate-missing",
            action="store_true",
            default=False,
            help="Mark symbols as inactive if their data files are no longer present",
        )

    def handle(self, *args, **options):
        from data_api.models import Symbol

        data_dir = Path(options["data_dir"]) if options["data_dir"] else _default_data_dir()

        if not data_dir.exists():
            self.stderr.write(self.style.ERROR(f"Data directory not found: {data_dir}"))
            return

        tickers = discover_symbols(data_dir)
        if not tickers:
            self.stderr.write(self.style.WARNING(f"No CSV files found in {data_dir}"))
            return

        self.stdout.write(f"Found {len(tickers)} unique symbol(s) in {data_dir}")

        created_count = 0
        updated_count = 0

        for ticker in tickers:
            meta = SYMBOL_META.get(ticker, None)
            defaults = {
                "name":     meta[0] if meta else ticker,
                "exchange": meta[1] if meta else "",
                "sector":   meta[2] if meta else "",
                "industry": meta[3] if meta else "",
                "is_active": True,
            }
            obj, created = Symbol.objects.get_or_create(symbol=ticker, defaults=defaults)

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  [+] Created  {ticker} – {defaults['name']}"))
            else:
                # Ensure is_active is True and name/exchange are up-to-date if we have metadata
                changed = False
                if not obj.is_active:
                    obj.is_active = True
                    changed = True
                if meta and obj.name != meta[0]:
                    obj.name = meta[0]
                    obj.exchange = meta[1]
                    obj.sector = meta[2]
                    obj.industry = meta[3]
                    changed = True
                if changed:
                    obj.save()
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"  [~] Updated  {ticker} – {obj.name}"))
                else:
                    self.stdout.write(f"  [=] Exists   {ticker} – {obj.name}")

        if options["deactivate_missing"]:
            active_symbols = Symbol.objects.filter(is_active=True)
            deactivated = 0
            for sym in active_symbols:
                if sym.symbol not in tickers:
                    sym.is_active = False
                    sym.save()
                    deactivated += 1
                    self.stdout.write(self.style.WARNING(f"  [-] Deactivated {sym.symbol}"))
            self.stdout.write(f"Deactivated {deactivated} symbol(s) no longer in warehouse")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone — {created_count} created, {updated_count} updated, "
                f"{len(tickers) - created_count - updated_count} already up to date."
            )
        )
