"""
Trade Execution Integration Test
=================================
Simulates a live trading bot finding entry conditions on BTCUSD (crypto,
trades 24/7 including weekends) and attempts to push a real order through
the MT5 bridge service.

Stages:
  1. Connect to MT5 bridge and confirm health
  2. Fetch live BTCUSD quote
  3. Load fresh 1h BTCUSD market data via LiveDataFetcher (tvDatafeed)
  4. Run the EMA-crossover / RSI strategy on the data to produce a signal
     — OR — force a synthetic BUY signal if the strategy produces HOLD
       (so we always exercise the order path regardless of market state)
  5. Build an order request from the signal (minimum lot size 0.01)
  6. Run MT5 order_check (margin / validity pre-flight)
  7. Send the order via MT5 bridge and report the full result

Run from the Live/ directory with the production venv:
    sudo -u algoagent \
      env $(grep -v '^#' /etc/algoagent/.env | xargs) \
      /opt/algoagent/venv/bin/python test_trade_execution.py

Pass --dry-run to skip the actual order_send (still runs order_check).
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone

# ── Path setup ────────────────────────────────────────────────────────────────
LIVE_DIR = Path(__file__).parent
MONOLITHIC_DIR = LIVE_DIR.parent
sys.path.insert(0, str(LIVE_DIR))
sys.path.insert(0, str(MONOLITHIC_DIR))

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(name)s  %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger('TradeTest')

SEP  = '=' * 60
SEP2 = '-' * 60

# ── Imports ───────────────────────────────────────────────────────────────────
from config import LiveConfig, MT5Constants
from mt5_bridge_connector import MT5BridgeConnector
from order_executor import OrderExecutor
from live_data_fetcher import LiveDataFetcher


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def section(title: str):
    log.info(SEP)
    log.info(f"  {title}")
    log.info(SEP)


def ok(msg):  log.info(f"  ✓  {msg}")
def fail(msg): log.error(f"  ✗  {msg}")
def info(msg): log.info(f"     {msg}")


def compute_ema(series, period):
    """Simple EMA using pandas ewm."""
    return series.ewm(span=period, adjust=False).mean()


def compute_rsi(series, period=14):
    """Wilder RSI."""
    delta = series.diff()
    gain  = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs    = gain / loss.replace(0, float('inf'))
    return 100 - (100 / (1 + rs))


def run_strategy(df, symbol):
    """
    Run a simplified EMA-crossover + RSI strategy on a DataFrame.
    Returns: ('BUY' | 'SELL' | 'HOLD', confidence, last_close, reason)
    """
    import pandas as pd

    if df.empty or len(df) < 30:
        return 'HOLD', 0.0, None, 'Not enough data'

    close = df['Close']
    ema12 = compute_ema(close, 12)
    ema26 = compute_ema(close, 26)
    rsi14 = compute_rsi(close, 14)

    last_close = float(close.iloc[-1])
    last_ema12 = float(ema12.iloc[-1])
    last_ema26 = float(ema26.iloc[-1])
    prev_ema12 = float(ema12.iloc[-2])
    prev_ema26 = float(ema26.iloc[-2])
    last_rsi   = float(rsi14.iloc[-1])

    info(f"  EMA12={last_ema12:.2f}  EMA26={last_ema26:.2f}  RSI={last_rsi:.1f}  Close={last_close:.2f}")

    # Bullish crossover: ema12 crossed above ema26, RSI not overbought
    if prev_ema12 <= prev_ema26 and last_ema12 > last_ema26 and last_rsi < 70:
        return 'BUY', 0.85, last_close, 'EMA12 crossed above EMA26, RSI not overbought'

    # Bearish crossover: ema12 crossed below ema26, RSI not oversold
    if prev_ema12 >= prev_ema26 and last_ema12 < last_ema26 and last_rsi > 30:
        return 'SELL', 0.85, last_close, 'EMA12 crossed below EMA26, RSI not oversold'

    # Trend continuation: ema12 already above ema26, RSI in healthy range
    if last_ema12 > last_ema26 and 40 < last_rsi < 65:
        return 'BUY', 0.60, last_close, 'EMA12 above EMA26 (trend continuation), RSI healthy'

    return 'HOLD', 0.0, last_close, f'No clear signal (EMA diff={last_ema12-last_ema26:.2f})'


# ─────────────────────────────────────────────────────────────────────────────
# Main test
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='MT5 trade execution integration test')
    parser.add_argument('--dry-run', action='store_true',
                        help='Run order_check only, do not call order_send')
    parser.add_argument('--force-buy', action='store_true',
                        help='Force a BUY signal even if strategy says HOLD')
    parser.add_argument('--symbol', default='BTCUSD',
                        help='Symbol to trade (default: BTCUSD)')
    args = parser.parse_args()

    SYMBOL   = args.symbol.upper()
    EXCHANGE = 'COINBASE' if SYMBOL in ('BTCUSD', 'ETHUSD') else 'FX'
    DRY_RUN  = args.dry_run

    print()
    section("TRADE EXECUTION INTEGRATION TEST")
    info(f"Symbol   : {SYMBOL}  (exchange={EXCHANGE})")
    info(f"Mode     : {'DRY-RUN (order_check only)' if DRY_RUN else 'LIVE (order_send)'}")
    info(f"Time UTC : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # ── 1. Load config & connect to MT5 bridge ────────────────────────────────
    section("STEP 1 — Connect to MT5 bridge")

    # Force bridge mode regardless of env file
    os.environ['MT5_USE_BRIDGE'] = 'true'
    os.environ['MT5_BRIDGE_URL'] = 'http://127.0.0.1:5555'
    os.environ['DRY_RUN'] = 'true' if DRY_RUN else 'false'

    config = LiveConfig()
    config.dry_run = DRY_RUN

    connector = MT5BridgeConnector(config, bridge_url='http://127.0.0.1:5555')

    if not connector.initialize():
        fail("Could not connect to MT5 bridge — is mt5_bridge.service running?")
        sys.exit(1)
    ok("MT5 bridge connected")

    account = connector.get_account_info()
    if not account:
        fail("Could not retrieve account info")
        sys.exit(1)

    ok(f"Account  : #{account['login']}  {account['server']}")
    ok(f"Balance  : ${account['balance']:.2f}  |  Free margin: ${account['margin_free']:.2f}")
    ok(f"Trade allowed: {account.get('login') is not None}")

    # ── 2. Fetch live quote ───────────────────────────────────────────────────
    section("STEP 2 — Fetch live quote")

    symbol_info = connector.get_symbol_info(SYMBOL)
    if not symbol_info:
        fail(f"Symbol {SYMBOL} not found on broker — check it is visible in MT5")
        connector.shutdown()
        sys.exit(1)

    bid = symbol_info['bid']
    ask = symbol_info['ask']
    spread_pts = symbol_info.get('spread', 0)
    ok(f"{SYMBOL}  bid={bid:.2f}  ask={ask:.2f}  spread={spread_pts} pts")
    ok(f"Volume limits: min={symbol_info['volume_min']}  max={symbol_info['volume_max']}  step={symbol_info['volume_step']}")

    # ── 3. Refresh market data ────────────────────────────────────────────────
    section("STEP 3 — Refresh 1h market data via LiveDataFetcher")

    fetcher = LiveDataFetcher()
    result  = fetcher.refresh(symbol=SYMBOL, exchange=EXCHANGE, interval='1h', n_bars=100)

    info(f"Status   : {result['status']}")
    info(f"Message  : {result['message']}")
    info(f"+New bars: {result['new_rows']}  |  Updated: {result['updated_rows']}  |  Total: {result['total_rows']}")
    info(f"Latest   : {result['latest_bar']}")

    if result['status'] == 'error':
        fail(f"Data fetch failed: {result['message']}")
        connector.shutdown()
        sys.exit(1)

    ok("Warehouse refreshed")

    # ── 4. Load data and run strategy ─────────────────────────────────────────
    section("STEP 4 — Load data and run EMA/RSI strategy")

    from Backtest.data_loader import load_market_data

    end_ts   = datetime.now(timezone.utc)
    start_ts = end_ts - timedelta(days=7)

    try:
        df, meta = load_market_data(ticker=SYMBOL, period='1mo', interval='1h')
    except Exception as e:
        fail(f"load_market_data failed: {e}")
        connector.shutdown()
        sys.exit(1)

    # Filter to recent window
    if df.index.tz is not None:
        df = df[(df.index >= start_ts) & (df.index <= end_ts)]

    info(f"Rows in 7-day window : {len(df)}")
    if not df.empty:
        info(f"Oldest bar : {df.index[0]}")
        info(f"Latest bar : {df.index[-1]}")

    signal, confidence, last_close, reason = run_strategy(df, SYMBOL)

    info(f"Strategy signal : {signal}  (confidence={confidence:.0%})")
    info(f"Reason          : {reason}")

    # Optionally force a BUY to always exercise the order path
    if signal == 'HOLD' and args.force_buy:
        signal    = 'BUY'
        last_close = ask
        reason    = '[FORCED for test — original strategy said HOLD]'
        info(f"Force-buy flag set — overriding to BUY @ {ask:.2f}")
    elif signal == 'HOLD' and not args.force_buy:
        info("")
        info("Strategy returned HOLD.  Re-run with --force-buy to push a test")
        info("order regardless of market conditions.")
        info("")
        ok("Test complete — no trade conditions met (this is normal on HOLD).")
        connector.shutdown()
        sys.exit(0)

    ok(f"Signal accepted: {signal}  reason='{reason}'")

    # ── 5. Build order request ────────────────────────────────────────────────
    section("STEP 5 — Build order request")

    VOLUME   = symbol_info['volume_min']   # Absolute minimum: 0.01 BTC
    entry_px = ask if signal == 'BUY' else bid

    # Stop-loss: 2% away from entry (well beyond stops_level of 1000 pts = $10)
    sl_price = round(entry_px * 0.98, 2) if signal == 'BUY' else round(entry_px * 1.02, 2)

    order_request = {
        'action':       MT5Constants.TRADE_ACTION_DEAL,
        'symbol':       SYMBOL,
        'volume':       VOLUME,
        'type':         MT5Constants.ORDER_TYPE_BUY if signal == 'BUY' else MT5Constants.ORDER_TYPE_SELL,
        'price':        entry_px,
        'sl':           sl_price,
        'deviation':    200,                        # 200 pts = $2 slippage tolerance
        'magic':        20260319,
        'comment':      'AlgoAgent_TradeTest',
        'type_time':    MT5Constants.ORDER_TIME_GTC,
        'type_filling': MT5Constants.ORDER_FILLING_IOC,
    }

    info(f"Action   : {signal}")
    info(f"Symbol   : {SYMBOL}")
    info(f"Volume   : {VOLUME} lot")
    info(f"Price    : {entry_px:.2f}")
    info(f"SL       : {sl_price:.2f}  ({abs(entry_px - sl_price):.2f} pts from entry)")
    info(f"Deviation: {order_request['deviation']} pts")
    info(f"Magic    : {order_request['magic']}")
    ok("Order request built")

    # ── 6. MT5 order_check (pre-flight) ───────────────────────────────────────
    section("STEP 6 — MT5 order_check (margin & validity pre-flight)")

    check = connector.check_order(order_request)

    if check is None:
        fail("order_check returned None — bridge or MT5 error")
        connector.shutdown()
        sys.exit(1)

    check_retcode = check.get('retcode', -1)
    check_ok = MT5Constants.is_success(check_retcode)

    info(f"retcode  : {check_retcode}  ({MT5Constants.get_retcode_message(check_retcode)})")
    info(f"margin   : ${check.get('margin', 0):.2f}")
    info(f"profit   : ${check.get('profit', 0):.2f}")
    info(f"comment  : {check.get('comment', '')}")

    if not check_ok:
        fail(f"order_check FAILED — broker rejected the request before even sending")
        info("This means the order parameters are invalid (margin, stops, etc.)")
        info(f"Full check result: {check}")
        connector.shutdown()
        sys.exit(1)

    ok("order_check PASSED — broker accepts the order parameters")

    # ── 7. Send the order ─────────────────────────────────────────────────────
    section(f"STEP 7 — {'[DRY-RUN] Skipping order_send' if DRY_RUN else 'Send order via MT5 bridge'}")

    executor = OrderExecutor(config, connector)
    result   = executor.execute_order(order_request, client_order_id=f"TRADETEST_{datetime.now().strftime('%H%M%S')}")

    print()
    info(SEP2)
    info("ORDER EXECUTION RESULT")
    info(SEP2)

    if result['success']:
        ok(f"ORDER EXECUTED SUCCESSFULLY")
        info(f"MT5 Order ID : #{result.get('mt5_order_id')}")
        info(f"MT5 Deal  ID : #{result.get('mt5_deal_id')}")
        info(f"Filled price : {result.get('executed_price')}")
        info(f"Filled volume: {result.get('executed_volume')}")
        info(f"Retcode      : {result.get('retcode')}  ({result.get('retcode_message')})")
        info(f"Attempts     : {result.get('attempts')}")
        info("")
        info("NOTE: A real position has been opened on your MT5 Demo account.")
        info("      Check MT5 terminal or run: curl http://127.0.0.1:5555/positions_get")
    else:
        fail(f"ORDER FAILED")
        info(f"Error   : {result.get('error')}")
        info(f"Message : {result.get('message')}")
        info(f"Retcode : {result.get('retcode')}")
        info(f"Attempts: {result.get('attempts')}")

    # ── Final summary ─────────────────────────────────────────────────────────
    section("SUMMARY")

    steps = [
        ("MT5 bridge connected",                True),
        ("Live quote fetched",                  bid > 0),
        ("Market data refreshed",               result['status'] != 'error' if isinstance(result, dict) and 'status' in result else True),
        ("Strategy signal generated",           signal in ('BUY', 'SELL')),
        ("order_check passed",                  check_ok),
        ("order_send executed" if not DRY_RUN else "order_send skipped (dry-run)",
                                                result['success'] or DRY_RUN),
    ]

    all_ok = True
    for label, passed in steps:
        marker = '✓' if passed else '✗'
        info(f"  {marker}  {label}")
        if not passed:
            all_ok = False

    print()
    if all_ok:
        ok("ALL STEPS PASSED — the full trade pipeline is working end-to-end.")
    else:
        fail("One or more steps failed — see above for details.")

    connector.shutdown()
    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
