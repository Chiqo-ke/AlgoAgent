"""
Seed script to populate the Symbol table with common securities.
Run from the monolithic_agent directory:
    python scripts/seed_symbols.py
"""
import os
import sys
import django

# Setup Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')
django.setup()

from data_api.models import Symbol

SYMBOLS = [
    # ── Major Forex Pairs ──────────────────────────────────────────────────
    {"symbol": "EURUSD", "name": "Euro / US Dollar",          "exchange": "FOREX", "sector": "Forex"},
    {"symbol": "GBPUSD", "name": "British Pound / US Dollar", "exchange": "FOREX", "sector": "Forex"},
    {"symbol": "USDJPY", "name": "US Dollar / Japanese Yen",  "exchange": "FOREX", "sector": "Forex"},
    {"symbol": "USDCHF", "name": "US Dollar / Swiss Franc",   "exchange": "FOREX", "sector": "Forex"},
    {"symbol": "AUDUSD", "name": "Australian Dollar / US Dollar", "exchange": "FOREX", "sector": "Forex"},
    {"symbol": "USDCAD", "name": "US Dollar / Canadian Dollar",   "exchange": "FOREX", "sector": "Forex"},
    {"symbol": "NZDUSD", "name": "New Zealand Dollar / US Dollar","exchange": "FOREX", "sector": "Forex"},
    {"symbol": "EURGBP", "name": "Euro / British Pound",      "exchange": "FOREX", "sector": "Forex"},
    {"symbol": "EURJPY", "name": "Euro / Japanese Yen",       "exchange": "FOREX", "sector": "Forex"},
    {"symbol": "GBPJPY", "name": "British Pound / Japanese Yen","exchange": "FOREX", "sector": "Forex"},
    {"symbol": "EURCHF", "name": "Euro / Swiss Franc",        "exchange": "FOREX", "sector": "Forex"},
    {"symbol": "AUDJPY", "name": "Australian Dollar / Japanese Yen","exchange": "FOREX", "sector": "Forex"},
    {"symbol": "CADJPY", "name": "Canadian Dollar / Japanese Yen","exchange": "FOREX", "sector": "Forex"},
    {"symbol": "CHFJPY", "name": "Swiss Franc / Japanese Yen","exchange": "FOREX", "sector": "Forex"},
    {"symbol": "GBPAUD", "name": "British Pound / Australian Dollar","exchange": "FOREX", "sector": "Forex"},
    {"symbol": "GBPCHF", "name": "British Pound / Swiss Franc","exchange": "FOREX", "sector": "Forex"},
    {"symbol": "EURCAD", "name": "Euro / Canadian Dollar",    "exchange": "FOREX", "sector": "Forex"},
    {"symbol": "AUDCAD", "name": "Australian Dollar / Canadian Dollar","exchange": "FOREX", "sector": "Forex"},
    {"symbol": "AUDCHF", "name": "Australian Dollar / Swiss Franc","exchange": "FOREX", "sector": "Forex"},
    {"symbol": "AUDNZD", "name": "Australian Dollar / New Zealand Dollar","exchange": "FOREX", "sector": "Forex"},
    {"symbol": "USDZAR", "name": "US Dollar / South African Rand","exchange": "FOREX", "sector": "Forex"},
    {"symbol": "USDMXN", "name": "US Dollar / Mexican Peso",  "exchange": "FOREX", "sector": "Forex"},
    {"symbol": "USDSEK", "name": "US Dollar / Swedish Krona", "exchange": "FOREX", "sector": "Forex"},
    {"symbol": "USDNOK", "name": "US Dollar / Norwegian Krone","exchange": "FOREX", "sector": "Forex"},
    {"symbol": "USDDKK", "name": "US Dollar / Danish Krone",  "exchange": "FOREX", "sector": "Forex"},

    # ── Crypto ────────────────────────────────────────────────────────────
    {"symbol": "BTCUSD",  "name": "Bitcoin / US Dollar",      "exchange": "CRYPTO", "sector": "Cryptocurrency"},
    {"symbol": "ETHUSD",  "name": "Ethereum / US Dollar",     "exchange": "CRYPTO", "sector": "Cryptocurrency"},
    {"symbol": "BNBUSD",  "name": "Binance Coin / US Dollar", "exchange": "CRYPTO", "sector": "Cryptocurrency"},
    {"symbol": "SOLUSD",  "name": "Solana / US Dollar",       "exchange": "CRYPTO", "sector": "Cryptocurrency"},
    {"symbol": "XRPUSD",  "name": "XRP / US Dollar",          "exchange": "CRYPTO", "sector": "Cryptocurrency"},
    {"symbol": "ADAUSD",  "name": "Cardano / US Dollar",      "exchange": "CRYPTO", "sector": "Cryptocurrency"},
    {"symbol": "DOTUSD",  "name": "Polkadot / US Dollar",     "exchange": "CRYPTO", "sector": "Cryptocurrency"},
    {"symbol": "DOGEUSD", "name": "Dogecoin / US Dollar",     "exchange": "CRYPTO", "sector": "Cryptocurrency"},
    {"symbol": "MATICUSD","name": "Polygon / US Dollar",      "exchange": "CRYPTO", "sector": "Cryptocurrency"},
    {"symbol": "LINKUSD", "name": "Chainlink / US Dollar",    "exchange": "CRYPTO", "sector": "Cryptocurrency"},
    {"symbol": "AVAXUSD", "name": "Avalanche / US Dollar",    "exchange": "CRYPTO", "sector": "Cryptocurrency"},
    {"symbol": "LTCUSD",  "name": "Litecoin / US Dollar",     "exchange": "CRYPTO", "sector": "Cryptocurrency"},
    {"symbol": "UNIUSD",  "name": "Uniswap / US Dollar",      "exchange": "CRYPTO", "sector": "Cryptocurrency"},
    {"symbol": "ATOMUSD", "name": "Cosmos / US Dollar",       "exchange": "CRYPTO", "sector": "Cryptocurrency"},
    {"symbol": "ETCUSD",  "name": "Ethereum Classic / US Dollar","exchange": "CRYPTO", "sector": "Cryptocurrency"},

    # ── US Technology Stocks ──────────────────────────────────────────────
    {"symbol": "AAPL",  "name": "Apple Inc.",               "exchange": "NASDAQ", "sector": "Technology", "industry": "Consumer Electronics"},
    {"symbol": "MSFT",  "name": "Microsoft Corporation",    "exchange": "NASDAQ", "sector": "Technology", "industry": "Software"},
    {"symbol": "GOOGL", "name": "Alphabet Inc. Class A",    "exchange": "NASDAQ", "sector": "Technology", "industry": "Internet Services"},
    {"symbol": "GOOG",  "name": "Alphabet Inc. Class C",    "exchange": "NASDAQ", "sector": "Technology", "industry": "Internet Services"},
    {"symbol": "AMZN",  "name": "Amazon.com Inc.",          "exchange": "NASDAQ", "sector": "Consumer Discretionary", "industry": "E-Commerce"},
    {"symbol": "META",  "name": "Meta Platforms Inc.",      "exchange": "NASDAQ", "sector": "Technology", "industry": "Social Media"},
    {"symbol": "TSLA",  "name": "Tesla Inc.",               "exchange": "NASDAQ", "sector": "Consumer Discretionary", "industry": "Electric Vehicles"},
    {"symbol": "NVDA",  "name": "NVIDIA Corporation",       "exchange": "NASDAQ", "sector": "Technology", "industry": "Semiconductors"},
    {"symbol": "NFLX",  "name": "Netflix Inc.",             "exchange": "NASDAQ", "sector": "Technology", "industry": "Streaming"},
    {"symbol": "INTC",  "name": "Intel Corporation",        "exchange": "NASDAQ", "sector": "Technology", "industry": "Semiconductors"},
    {"symbol": "AMD",   "name": "Advanced Micro Devices",   "exchange": "NASDAQ", "sector": "Technology", "industry": "Semiconductors"},
    {"symbol": "AVGO",  "name": "Broadcom Inc.",            "exchange": "NASDAQ", "sector": "Technology", "industry": "Semiconductors"},
    {"symbol": "QCOM",  "name": "Qualcomm Inc.",            "exchange": "NASDAQ", "sector": "Technology", "industry": "Semiconductors"},
    {"symbol": "CSCO",  "name": "Cisco Systems Inc.",       "exchange": "NASDAQ", "sector": "Technology", "industry": "Networking"},
    {"symbol": "ORCL",  "name": "Oracle Corporation",       "exchange": "NYSE",   "sector": "Technology", "industry": "Enterprise Software"},
    {"symbol": "CRM",   "name": "Salesforce Inc.",          "exchange": "NYSE",   "sector": "Technology", "industry": "Cloud Software"},
    {"symbol": "ADBE",  "name": "Adobe Inc.",               "exchange": "NASDAQ", "sector": "Technology", "industry": "Software"},
    {"symbol": "IBM",   "name": "IBM Corporation",          "exchange": "NYSE",   "sector": "Technology", "industry": "IT Services"},
    {"symbol": "NOW",   "name": "ServiceNow Inc.",          "exchange": "NYSE",   "sector": "Technology", "industry": "Cloud Software"},
    {"symbol": "SNOW",  "name": "Snowflake Inc.",           "exchange": "NYSE",   "sector": "Technology", "industry": "Cloud Data"},
    {"symbol": "PLTR",  "name": "Palantir Technologies",    "exchange": "NYSE",   "sector": "Technology", "industry": "Data Analytics"},
    {"symbol": "UBER",  "name": "Uber Technologies Inc.",   "exchange": "NYSE",   "sector": "Technology", "industry": "Ride-Sharing"},
    {"symbol": "LYFT",  "name": "Lyft Inc.",                "exchange": "NASDAQ", "sector": "Technology", "industry": "Ride-Sharing"},
    {"symbol": "ABNB",  "name": "Airbnb Inc.",              "exchange": "NASDAQ", "sector": "Technology", "industry": "Travel"},
    {"symbol": "SPOT",  "name": "Spotify Technology SA",   "exchange": "NYSE",   "sector": "Technology", "industry": "Streaming"},

    # ── US Finance Stocks ─────────────────────────────────────────────────
    {"symbol": "JPM",   "name": "JPMorgan Chase & Co.",    "exchange": "NYSE", "sector": "Financials", "industry": "Banking"},
    {"symbol": "BAC",   "name": "Bank of America Corp.",   "exchange": "NYSE", "sector": "Financials", "industry": "Banking"},
    {"symbol": "WFC",   "name": "Wells Fargo & Company",   "exchange": "NYSE", "sector": "Financials", "industry": "Banking"},
    {"symbol": "GS",    "name": "Goldman Sachs Group Inc.","exchange": "NYSE", "sector": "Financials", "industry": "Investment Banking"},
    {"symbol": "MS",    "name": "Morgan Stanley",          "exchange": "NYSE", "sector": "Financials", "industry": "Investment Banking"},
    {"symbol": "V",     "name": "Visa Inc.",               "exchange": "NYSE", "sector": "Financials", "industry": "Payments"},
    {"symbol": "MA",    "name": "Mastercard Inc.",         "exchange": "NYSE", "sector": "Financials", "industry": "Payments"},
    {"symbol": "PYPL",  "name": "PayPal Holdings Inc.",    "exchange": "NASDAQ","sector": "Financials", "industry": "Payments"},
    {"symbol": "BRK-B", "name": "Berkshire Hathaway B",   "exchange": "NYSE", "sector": "Financials", "industry": "Conglomerate"},
    {"symbol": "AXP",   "name": "American Express Company","exchange": "NYSE", "sector": "Financials", "industry": "Financial Services"},
    {"symbol": "C",     "name": "Citigroup Inc.",          "exchange": "NYSE", "sector": "Financials", "industry": "Banking"},
    {"symbol": "BLK",   "name": "BlackRock Inc.",          "exchange": "NYSE", "sector": "Financials", "industry": "Asset Management"},

    # ── Healthcare ────────────────────────────────────────────────────────
    {"symbol": "JNJ",   "name": "Johnson & Johnson",       "exchange": "NYSE", "sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "UNH",   "name": "UnitedHealth Group Inc.", "exchange": "NYSE", "sector": "Healthcare", "industry": "Health Insurance"},
    {"symbol": "PFE",   "name": "Pfizer Inc.",             "exchange": "NYSE", "sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "ABBV",  "name": "AbbVie Inc.",             "exchange": "NYSE", "sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "MRK",   "name": "Merck & Co. Inc.",        "exchange": "NYSE", "sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "LLY",   "name": "Eli Lilly and Company",   "exchange": "NYSE", "sector": "Healthcare", "industry": "Pharmaceuticals"},
    {"symbol": "TMO",   "name": "Thermo Fisher Scientific","exchange": "NYSE", "sector": "Healthcare", "industry": "Medical Instruments"},
    {"symbol": "AMGN",  "name": "Amgen Inc.",              "exchange": "NASDAQ","sector": "Healthcare", "industry": "Biotechnology"},
    {"symbol": "GILD",  "name": "Gilead Sciences Inc.",    "exchange": "NASDAQ","sector": "Healthcare", "industry": "Biotechnology"},
    {"symbol": "MRNA",  "name": "Moderna Inc.",            "exchange": "NASDAQ","sector": "Healthcare", "industry": "Biotechnology"},

    # ── Energy ────────────────────────────────────────────────────────────
    {"symbol": "XOM",  "name": "Exxon Mobil Corporation", "exchange": "NYSE", "sector": "Energy", "industry": "Oil & Gas"},
    {"symbol": "CVX",  "name": "Chevron Corporation",     "exchange": "NYSE", "sector": "Energy", "industry": "Oil & Gas"},
    {"symbol": "COP",  "name": "ConocoPhillips",          "exchange": "NYSE", "sector": "Energy", "industry": "Oil & Gas"},
    {"symbol": "SLB",  "name": "Schlumberger Ltd.",       "exchange": "NYSE", "sector": "Energy", "industry": "Oil Services"},
    {"symbol": "EOG",  "name": "EOG Resources Inc.",      "exchange": "NYSE", "sector": "Energy", "industry": "Oil & Gas"},

    # ── Consumer / Retail ─────────────────────────────────────────────────
    {"symbol": "WMT",  "name": "Walmart Inc.",            "exchange": "NYSE",   "sector": "Consumer Staples", "industry": "Retail"},
    {"symbol": "COST", "name": "Costco Wholesale Corp.",  "exchange": "NASDAQ", "sector": "Consumer Staples", "industry": "Retail"},
    {"symbol": "TGT",  "name": "Target Corporation",     "exchange": "NYSE",   "sector": "Consumer Staples", "industry": "Retail"},
    {"symbol": "HD",   "name": "Home Depot Inc.",         "exchange": "NYSE",   "sector": "Consumer Discretionary", "industry": "Home Improvement"},
    {"symbol": "NKE",  "name": "Nike Inc.",               "exchange": "NYSE",   "sector": "Consumer Discretionary", "industry": "Apparel"},
    {"symbol": "MCD",  "name": "McDonald's Corporation",  "exchange": "NYSE",   "sector": "Consumer Discretionary", "industry": "Restaurants"},
    {"symbol": "SBUX", "name": "Starbucks Corporation",   "exchange": "NASDAQ", "sector": "Consumer Discretionary", "industry": "Restaurants"},
    {"symbol": "DIS",  "name": "The Walt Disney Company", "exchange": "NYSE",   "sector": "Consumer Discretionary", "industry": "Media"},
    {"symbol": "KO",   "name": "Coca-Cola Company",       "exchange": "NYSE",   "sector": "Consumer Staples", "industry": "Beverages"},
    {"symbol": "PEP",  "name": "PepsiCo Inc.",            "exchange": "NASDAQ", "sector": "Consumer Staples", "industry": "Beverages"},

    # ── Indices / ETFs ────────────────────────────────────────────────────
    {"symbol": "SPY",  "name": "SPDR S&P 500 ETF",        "exchange": "NYSE", "sector": "ETF", "industry": "Index Fund"},
    {"symbol": "QQQ",  "name": "Invesco QQQ Trust",        "exchange": "NASDAQ","sector": "ETF", "industry": "Index Fund"},
    {"symbol": "DIA",  "name": "SPDR Dow Jones ETF",       "exchange": "NYSE", "sector": "ETF", "industry": "Index Fund"},
    {"symbol": "IWM",  "name": "iShares Russell 2000 ETF", "exchange": "NYSE", "sector": "ETF", "industry": "Index Fund"},
    {"symbol": "GLD",  "name": "SPDR Gold Shares ETF",     "exchange": "NYSE", "sector": "ETF", "industry": "Commodities"},
    {"symbol": "SLV",  "name": "iShares Silver Trust ETF", "exchange": "NYSE", "sector": "ETF", "industry": "Commodities"},
    {"symbol": "USO",  "name": "US Oil Fund ETF",          "exchange": "NYSE", "sector": "ETF", "industry": "Commodities"},

    # ── Commodities (spot) ────────────────────────────────────────────────
    {"symbol": "XAUUSD", "name": "Gold / US Dollar",       "exchange": "COMMODITY", "sector": "Commodities"},
    {"symbol": "XAGUSD", "name": "Silver / US Dollar",     "exchange": "COMMODITY", "sector": "Commodities"},
    {"symbol": "WTICOUSD","name": "WTI Crude Oil / US Dollar","exchange": "COMMODITY","sector": "Commodities"},
    {"symbol": "NATGASUSD","name":"Natural Gas / US Dollar","exchange": "COMMODITY", "sector": "Commodities"},
]


def seed():
    created = 0
    skipped = 0
    for s in SYMBOLS:
        # Normalise symbol key to uppercase, set is_active
        symbol_code = s["symbol"].upper()
        obj, was_created = Symbol.objects.get_or_create(
            symbol=symbol_code,
            defaults={
                "name":     s.get("name", symbol_code),
                "exchange": s.get("exchange", ""),
                "sector":   s.get("sector", ""),
                "industry": s.get("industry", ""),
                "is_active": True,
            },
        )
        if was_created:
            created += 1
        else:
            skipped += 1

    print(f"Done — {created} symbols created, {skipped} already existed.")
    print(f"Total symbols in database: {Symbol.objects.count()}")


if __name__ == "__main__":
    seed()
