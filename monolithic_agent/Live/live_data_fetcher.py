"""
Live Data Fetcher — incremental warehouse refresh using tvDatafeed.

Fetches fresh OHLCV bars on demand and upserts them into the local warehouse.
Always strips the last (currently-forming, incomplete) bar from any fetch result.

Rules enforced:
  • The last returned bar is ALWAYS stripped — it represents the open/live period
    that has not yet closed (e.g. at 08:25, the 08:00 candle is still forming).
  • Deduplicates by datetime (keeps the latest fetched version of each bar).
  • Caps fetch at MAX_BARS (4000) which is the tvDatafeed hard limit.
  • Warehouse path per symbol/interval: Data/data/{symbol_lower}_{interval}.csv

Usage:
    from Live.live_data_fetcher import LiveDataFetcher
    result = LiveDataFetcher().refresh('EURUSD', 'FX', '1h')
"""

from __future__ import annotations

import logging
import fcntl
import os
import threading
from datetime import datetime, timezone as tz
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger('LiveTrader.DataFetcher')

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Interval → duration in minutes.
# Used to determine whether the last tvDatafeed bar is still open.
INTERVAL_MINUTES: dict[str, int] = {
    '1m':   1,
    '3m':   3,
    '5m':   5,
    '10m':  10,
    '15m':  15,
    '30m':  30,
    '45m':  45,
    '1h':   60,
    '2h':   120,
    '3h':   180,
    '4h':   240,
    '1d':   1440,
    '1w':   10080,
    '1mo':  43200,
}

MAX_BARS = 5000  # tvDatafeed supports up to 5000 bars
FETCH_TIMEOUT = 90  # seconds — tvDatafeed network call timeout

# Warehouse: monolithic_agent/Data/data/
WAREHOUSE_DIR = Path(__file__).parent.parent / 'Data' / 'data'


# ---------------------------------------------------------------------------
# Interval helpers  (mirrors Backtest/data_loader.py for consistency)
# ---------------------------------------------------------------------------

def _normalize_interval(interval: str) -> str:
    """Map any interval alias to the canonical warehouse filename suffix."""
    aliases: dict[str, str] = {
        '60m':   '1h',
        '1hr':   '1h',
        '1hour': '1h',
        '120m':  '2h',
        '2hr':   '2h',
        '2hour': '2h',
        '240m':  '4h',
        '4hr':   '4h',
        '4hour': '4h',
        '1wk':   '1w',
        '1week': '1w',
        'd':     '1d',
        'daily': '1d',
    }
    normalized = str(interval).strip().lower()
    return aliases.get(normalized, normalized)


def _interval_to_tvdatafeed(interval: str):
    """Convert a normalized interval string to the tvDatafeed Interval enum."""
    from tvDatafeed import Interval  # deferred import — only when tvDatafeed is needed

    mapping = {
        '1m':  Interval.in_1_minute,
        '3m':  Interval.in_3_minute,
        '5m':  Interval.in_5_minute,
        '15m': Interval.in_15_minute,
        '30m': Interval.in_30_minute,
        '45m': Interval.in_45_minute,
        '1h':  Interval.in_1_hour,
        '2h':  Interval.in_2_hour,
        '3h':  Interval.in_3_hour,
        '4h':  Interval.in_4_hour,
        '1d':  Interval.in_daily,
        '1w':  Interval.in_weekly,
        '1mo': Interval.in_monthly,
    }
    norm = _normalize_interval(interval)
    if norm not in mapping:
        raise ValueError(
            f"Unsupported interval '{interval}' (normalized: '{norm}'). "
            f"Supported: {sorted(mapping)}"
        )
    return mapping[norm]


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class LiveDataFetcher:
    """
    On-demand live data fetcher that upserts fresh bars into the warehouse CSV.

    Incomplete bar policy
    ---------------------
    tvDatafeed always returns the currently-forming bar as the last row.
    Example: at 08:25 UTC, a 1h request returns bars ending at 08:00 (open,
    incomplete). The last VALID bar is 07:00 (closed at 08:00).

    This class always strips the final row from any fetch result, then
    additionally verifies via open_time + interval_duration > now_utc.
    The next scheduled fetch will capture that bar once it has closed.
    """

    def refresh(
        self,
        symbol: str,
        exchange: str,
        interval: str,
        n_bars: int = 500,
    ) -> dict[str, Any]:
        """
        Fetch fresh bars from tvDatafeed and upsert them into the warehouse.

        Args:
            symbol:   Trading symbol, e.g. 'EURUSD', 'AAPL'.
            exchange: Exchange as expected by tvDatafeed, e.g. 'FX', 'NASDAQ'.
            interval: Timeframe string, e.g. '1h', '4h', '1d'.
            n_bars:   Number of *complete* bars to aim for (capped to MAX_BARS).
                      One extra bar is requested internally to account for stripping.

        Returns:
            dict: {symbol, exchange, interval, warehouse_path,
                   new_rows, updated_rows, total_rows, latest_bar,
                   fetch_time_utc, status, message}
        """
        n_bars = min(max(n_bars, 1), MAX_BARS)
        norm_interval = _normalize_interval(interval)
        warehouse_path = self._warehouse_path(symbol, norm_interval)
        fetch_time = datetime.now(tz.utc)

        logger.info(
            f"[LiveDataFetcher] Refreshing {symbol} ({exchange}) {norm_interval} "
            f"n_bars={n_bars}"
        )

        # 1. Fetch: request n_bars + 1 so that after stripping the live bar
        #    we still have n_bars of closed history.
        try:
            raw_df = self._fetch_from_tv(symbol, exchange, norm_interval, n_bars + 1)
        except Exception as exc:
            logger.error(f"[LiveDataFetcher] tvDatafeed fetch failed: {exc}")
            return self._result(
                symbol, exchange, norm_interval, warehouse_path,
                new_rows=0, updated_rows=0, total_rows=None, latest_bar=None,
                fetch_time=fetch_time, status='error', message=str(exc),
            )

        if raw_df is None or raw_df.empty:
            msg = 'No data returned from tvDatafeed.'
            logger.warning(f"[LiveDataFetcher] {msg}")
            return self._result(
                symbol, exchange, norm_interval, warehouse_path,
                new_rows=0, updated_rows=0, total_rows=None, latest_bar=None,
                fetch_time=fetch_time, status='no_data', message=msg,
            )

        # 2. Strip the current incomplete bar (the one still forming).
        complete_df = self._strip_incomplete_bar(raw_df, norm_interval, fetch_time)

        if complete_df.empty:
            msg = (
                'No complete bars available after stripping the live bar. '
                'The market may be at the very start of a new period.'
            )
            logger.warning(f"[LiveDataFetcher] {msg}")
            return self._result(
                symbol, exchange, norm_interval, warehouse_path,
                new_rows=0, updated_rows=0, total_rows=None, latest_bar=None,
                fetch_time=fetch_time, status='no_complete_bars', message=msg,
            )

        # 3. Normalise to warehouse schema.
        normalized_df = self._normalize_to_warehouse(complete_df, symbol)

        # 4. Upsert into warehouse CSV.
        new_rows, updated_rows, total_rows = self._upsert_warehouse(
            normalized_df, warehouse_path
        )

        latest_bar = (
            normalized_df['datetime'].max().isoformat()
            if not normalized_df.empty else None
        )

        logger.info(
            f"[LiveDataFetcher] {symbol} {norm_interval}: "
            f"+{new_rows} new, {updated_rows} updated, {total_rows} total "
            f"→ {warehouse_path.name}"
        )

        return self._result(
            symbol, exchange, norm_interval, warehouse_path,
            new_rows=new_rows, updated_rows=updated_rows,
            total_rows=total_rows, latest_bar=latest_bar,
            fetch_time=fetch_time, status='ok',
            message=f'{new_rows} new bars added, {updated_rows} existing bars refreshed.',
        )

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get_warehouse_status(self, symbol: str, interval: str) -> dict[str, Any]:
        """Return freshness info for a warehouse file without fetching."""
        norm_interval = _normalize_interval(interval)
        path = self._warehouse_path(symbol, norm_interval)

        if not path.exists():
            return {
                'symbol': symbol.upper(),
                'interval': norm_interval,
                'warehouse_path': str(path),
                'exists': False,
                'total_rows': 0,
                'latest_bar': None,
                'oldest_bar': None,
                'stale_minutes': None,
                'status': 'missing',
            }

        try:
            df = pd.read_csv(path)
            df['datetime'] = pd.to_datetime(df['datetime'], utc=True, errors='coerce')
            df = df.dropna(subset=['datetime'])

            latest = df['datetime'].max()
            oldest = df['datetime'].min()
            now_utc = pd.Timestamp.now(tz='UTC')
            stale_minutes = (
                int((now_utc - latest).total_seconds() / 60)
                if not pd.isnull(latest) else None
            )

            return {
                'symbol': symbol.upper(),
                'interval': norm_interval,
                'warehouse_path': str(path),
                'exists': True,
                'total_rows': len(df),
                'latest_bar': latest.isoformat() if not pd.isnull(latest) else None,
                'oldest_bar': oldest.isoformat() if not pd.isnull(oldest) else None,
                'stale_minutes': stale_minutes,
                'status': 'ok',
            }
        except Exception as exc:
            return {
                'symbol': symbol.upper(),
                'interval': norm_interval,
                'warehouse_path': str(path),
                'exists': True,
                'total_rows': 0,
                'latest_bar': None,
                'oldest_bar': None,
                'stale_minutes': None,
                'status': f'read_error: {exc}',
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fetch_from_tv(
        self,
        symbol: str,
        exchange: str,
        interval: str,
        n_bars: int,
    ) -> pd.DataFrame:
        """Call tvDatafeed.get_hist() with a FETCH_TIMEOUT-second daemon-thread timeout.

        tvDatafeed makes a blocking network call (WebSocket/HTTP) that can hang
        indefinitely if TradingView is unreachable.  We run it in a daemon thread
        so the main bot loop is never blocked longer than FETCH_TIMEOUT seconds.
        The daemon thread will not prevent process exit even if it remains stuck.
        """
        from tvDatafeed import TvDatafeed

        result_holder: list = [None]
        exc_holder: list = [None]
        done_event = threading.Event()

        def _worker() -> None:
            try:
                tv = TvDatafeed()
                tv_interval = _interval_to_tvdatafeed(interval)
                data = tv.get_hist(
                    symbol=symbol,
                    exchange=exchange,
                    interval=tv_interval,
                    n_bars=min(n_bars, MAX_BARS),
                )
                result_holder[0] = pd.DataFrame() if data is None else data.reset_index()
            except Exception as exc:  # noqa: BLE001
                exc_holder[0] = exc
            finally:
                done_event.set()

        t = threading.Thread(target=_worker, daemon=True, name=f'tvfetch-{symbol}')
        t.start()

        if not done_event.wait(timeout=FETCH_TIMEOUT):
            raise TimeoutError(
                f"tvDatafeed fetch for {symbol} timed out after {FETCH_TIMEOUT}s"
            )

        if exc_holder[0] is not None:
            raise exc_holder[0]

        # tvDatafeed returns a MultiIndex (symbol, datetime) DataFrame.
        # reset_index() flattens it to columns: symbol, datetime, open...
        return result_holder[0]

    def _strip_incomplete_bar(
        self,
        df: pd.DataFrame,
        interval: str,
        now_utc: datetime,
    ) -> pd.DataFrame:
        """
        Remove the currently-forming (open, incomplete) bar from a fetched DataFrame.

        Logic:
          1. Always remove df.iloc[-1] as a conservative baseline — tvDatafeed's
             last row is always the bar whose period has not yet closed.
          2. After the initial strip, additionally verify the new last row using
             open_time + interval_duration > now_utc, and strip again if needed.
             This handles the rare edge case where the fetch lands exactly on a
             boundary and tvDatafeed has already rolled to the next period.

        Examples (1h interval):
          - Fetch at 08:25 UTC → raw last bar opens at 08:00 (closes 09:00) → strip it.
            Result: latest complete bar = 07:00 ✓
          - Fetch at 09:01 UTC → raw last bar may open at 09:00 (closes 10:00) → strip it.
            Result: latest complete bar = 08:00 ✓
        """
        if df.empty:
            return df

        # Detect datetime column.
        dt_col = None
        for candidate in ('datetime', 'timestamp', 'date', 'time'):
            if candidate in df.columns:
                dt_col = candidate
                break
        if dt_col is None:
            dt_col = df.columns[0]  # fall back to first column

        df = df.copy()
        df[dt_col] = pd.to_datetime(df[dt_col], utc=True, errors='coerce')
        df = df.dropna(subset=[dt_col]).sort_values(dt_col).reset_index(drop=True)

        if df.empty:
            return df

        interval_minutes = INTERVAL_MINUTES.get(_normalize_interval(interval), 0)
        now_ts = pd.Timestamp(now_utc).tz_convert('UTC')

        # Step 1: strip unconditionally (tvDatafeed always includes the live bar).
        df = df.iloc[:-1].reset_index(drop=True)

        if df.empty:
            return df

        # Step 2: verify the new last bar is also complete.
        if interval_minutes > 0:
            last_open = df[dt_col].iloc[-1]
            bar_close = last_open + pd.Timedelta(minutes=interval_minutes)

            if bar_close > now_ts:
                # Still incomplete — strip again (should be rare).
                logger.debug(
                    f"[LiveDataFetcher] Secondary strip: "
                    f"bar_open={last_open.isoformat()}, "
                    f"bar_close={bar_close.isoformat()}, "
                    f"now={now_ts.isoformat()}"
                )
                df = df.iloc[:-1].reset_index(drop=True)

        return df

    def _normalize_to_warehouse(
        self,
        df: pd.DataFrame,
        symbol: str,
    ) -> pd.DataFrame:
        """
        Normalize a fetched DataFrame to warehouse schema:
            datetime, symbol, open, high, low, close, volume  (all lowercase)
        """
        df = df.copy()

        # Lowercase all column names.
        df.columns = [str(c).strip().lower() for c in df.columns]

        # Ensure 'datetime' column exists.
        if 'datetime' not in df.columns:
            for alias in ('timestamp', 'date', 'time'):
                if alias in df.columns:
                    df = df.rename(columns={alias: 'datetime'})
                    break

        df['datetime'] = pd.to_datetime(df['datetime'], utc=True, errors='coerce')
        df = df.dropna(subset=['datetime'])

        # Overwrite symbol column with the canonical symbol name.
        df['symbol'] = symbol.upper()

        # Keep only warehouse columns that are present.
        keep = [
            c for c in ['datetime', 'symbol', 'open', 'high', 'low', 'close', 'volume']
            if c in df.columns
        ]
        df = df[keep]

        # Numeric coercion for OHLCV.
        for col in ('open', 'high', 'low', 'close', 'volume'):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        df = df.dropna(subset=['open', 'high', 'low', 'close'])
        df = df.sort_values('datetime').reset_index(drop=True)
        return df

    def _upsert_warehouse(
        self,
        fresh_df: pd.DataFrame,
        path: Path,
    ) -> tuple[int, int, int]:
        """
        Merge fresh bars into the warehouse CSV, deduplicating by datetime.

        Uses an OS-level exclusive file lock (fcntl.flock) so that multiple
        bot subprocesses serialise writes to the same warehouse file.
        Writes are atomic: data goes to a .tmp file first, then os.replace()
        renames it so concurrent readers never see a partially-written file.

        Returns:
            (new_rows, updated_rows, total_rows)
        """
        WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)

        # Use a per-file .lock sentinel so all bot processes contend on the
        # same inode, giving us true cross-process exclusion via flock(LOCK_EX).
        lock_path = path.with_suffix('.lock')
        lock_path.touch(exist_ok=True)

        with open(lock_path, 'r') as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                if path.exists():
                    existing = pd.read_csv(path)
                    existing['datetime'] = pd.to_datetime(
                        existing['datetime'], utc=True, errors='coerce'
                    )
                    existing = existing.dropna(subset=['datetime'])

                    existing_ts = set(existing['datetime'].astype(str))
                    fresh_ts = set(fresh_df['datetime'].astype(str))

                    new_rows = len(fresh_ts - existing_ts)
                    updated_rows = len(fresh_ts & existing_ts)

                    # Merge, then deduplicate keeping the freshly-fetched version of each bar.
                    combined = pd.concat([existing, fresh_df], ignore_index=True)
                    combined['datetime'] = pd.to_datetime(
                        combined['datetime'], utc=True, errors='coerce'
                    )
                    combined = (
                        combined
                        .sort_values('datetime')
                        .drop_duplicates(subset=['datetime'], keep='last')
                        .reset_index(drop=True)
                    )
                else:
                    combined = fresh_df.copy()
                    combined['datetime'] = pd.to_datetime(
                        combined['datetime'], utc=True, errors='coerce'
                    )
                    new_rows = len(fresh_df)
                    updated_rows = 0

                # Serialize datetime as naive UTC string — matches existing warehouse format
                # and is correctly parsed by Backtest/data_loader.py with utc=True.
                combined['datetime'] = combined['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')

                # Atomic write: write to a temp file then rename so concurrent readers
                # never see a partially-written file.
                tmp_path = path.with_suffix('.tmp')
                combined.to_csv(tmp_path, index=False)
                os.replace(tmp_path, path)
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)

        return new_rows, updated_rows, len(combined)

    @staticmethod
    def _warehouse_path(symbol: str, interval: str) -> Path:
        return WAREHOUSE_DIR / f"{symbol.lower()}_{interval}.csv"

    @staticmethod
    def _result(
        symbol, exchange, interval, warehouse_path,
        new_rows, updated_rows, total_rows, latest_bar,
        fetch_time, status, message,
    ) -> dict[str, Any]:
        return {
            'symbol': symbol.upper(),
            'exchange': exchange.upper() if exchange else '',
            'interval': interval,
            'warehouse_path': str(warehouse_path),
            'new_rows': new_rows,
            'updated_rows': updated_rows,
            'total_rows': total_rows,
            'latest_bar': latest_bar,
            'fetch_time_utc': fetch_time.isoformat(),
            'status': status,
            'message': message,
        }
