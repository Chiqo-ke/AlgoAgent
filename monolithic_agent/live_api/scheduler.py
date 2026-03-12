"""
Live Data Scheduler — APScheduler-based clock for warehouse refresh.

Fires LiveDataFetcher.refresh() at the close of each interval period for all
activated symbol/interval feeds.

Schedule offsets
----------------
Jobs fire 1–2 minutes *after* the expected bar close to allow for data
propagation on TradingView's end.

  1m  → every minute  (fires at :00, no meaningful offset needed)
  5m  → fires at :01, :06, :11, :16, :21, :26, :31, :36, :41, :46, :51, :56
  15m → fires at :01, :16, :31, :46
  30m → fires at :01, :31
  1h  → fires at minute :01 of every hour
  2h  → fires at minute :01 of 00:00, 02:00, 04:00 ... 22:00
  4h  → fires at minute :01 of 00:00, 04:00, 08:00, 12:00, 16:00, 20:00
  1d  → fires at 00:02 UTC daily
  1w  → fires at 00:05 UTC Monday
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore

logger = logging.getLogger('LiveTrader.Scheduler')

# ---------------------------------------------------------------------------
# Cron specs per interval
# Each value maps directly to CronTrigger(**kwargs).
# ---------------------------------------------------------------------------
_CRON_MAP: dict[str, dict[str, str]] = {
    '1m':  {'minute': '*'},
    '3m':  {'minute': '1,4,7,10,13,16,19,22,25,28,31,34,37,40,43,46,49,52,55,58'},
    '5m':  {'minute': '1,6,11,16,21,26,31,36,41,46,51,56'},
    '10m': {'minute': '1,11,21,31,41,51'},
    '15m': {'minute': '1,16,31,46'},
    '30m': {'minute': '1,31'},
    '45m': {'minute': '1,46'},
    '1h':  {'minute': '1'},
    '2h':  {'hour': '0,2,4,6,8,10,12,14,16,18,20,22', 'minute': '1'},
    '3h':  {'hour': '0,3,6,9,12,15,18,21', 'minute': '1'},
    '4h':  {'hour': '0,4,8,12,16,20', 'minute': '1'},
    '1d':  {'hour': '0', 'minute': '2'},
    '1w':  {'day_of_week': 'mon', 'hour': '0', 'minute': '5'},
}


def _job_id(symbol: str, exchange: str, interval: str) -> str:
    return f"live_feed__{symbol.upper()}__{exchange.upper()}__{interval}"


# ---------------------------------------------------------------------------
# Scheduler class
# ---------------------------------------------------------------------------

class LiveDataScheduler:
    """
    Background scheduler that periodically refreshes warehouse CSVs for all
    activated symbol/interval feeds.

    Thread-safe: activate() and deactivate() can be called from any thread
    (e.g. a Django view handler).
    """

    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler(
            jobstores={'default': MemoryJobStore()},
            job_defaults={
                'coalesce': True,       # Merge missed runs into one
                'max_instances': 1,     # No overlapping executions per job
                'misfire_grace_time': 120,  # Allow 2-min late fires
            },
            timezone='UTC',
        )
        self._lock = threading.Lock()
        self._started = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the background scheduler. Safe to call multiple times."""
        if not self._started:
            self._scheduler.start()
            self._started = True
            logger.info('[LiveScheduler] Background scheduler started (UTC).')

    def stop(self) -> None:
        """Shut down the scheduler gracefully."""
        if self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False
            logger.info('[LiveScheduler] Background scheduler stopped.')

    # ------------------------------------------------------------------
    # Feed management
    # ------------------------------------------------------------------

    def activate(
        self,
        symbol: str,
        exchange: str,
        interval: str,
        n_bars: int = 500,
    ) -> dict[str, Any]:
        """
        Register a recurring warehouse-refresh job for symbol/exchange/interval.

        If a job for this feed already exists, it is replaced.
        The job fires LiveDataFetcher.refresh() on the cron schedule defined in
        _CRON_MAP for the given interval.

        Returns a status dict with next_run_utc.
        """
        from Live.live_data_fetcher import LiveDataFetcher, _normalize_interval

        norm = _normalize_interval(interval)

        if norm not in _CRON_MAP:
            return {
                'status': 'error',
                'message': (
                    f"No cron schedule defined for interval '{interval}' "
                    f"(normalized: '{norm}'). Supported: {sorted(_CRON_MAP)}"
                ),
            }

        job_id = _job_id(symbol, exchange, norm)
        cron_kwargs = _CRON_MAP[norm]

        # Capture variables for the closure.
        _sym, _exch, _norm, _n = symbol, exchange, norm, n_bars

        def _job() -> None:
            logger.info(f'[LiveScheduler] Scheduled refresh → {_sym} {_exch} {_norm}')
            try:
                result = LiveDataFetcher().refresh(_sym, _exch, _norm, n_bars=_n)
                level = logging.INFO if result['status'] == 'ok' else logging.WARNING
                logger.log(
                    level,
                    f'[LiveScheduler] {_sym} {_norm}: {result["message"]} '
                    f'(latest bar: {result["latest_bar"]})'
                )
            except Exception as exc:
                logger.error(
                    f'[LiveScheduler] Refresh failed for {_sym} {_norm}: {exc}',
                    exc_info=True,
                )

        with self._lock:
            if self._scheduler.get_job(job_id):
                self._scheduler.remove_job(job_id)

            trigger = CronTrigger(timezone='UTC', **cron_kwargs)
            self._scheduler.add_job(
                _job,
                trigger=trigger,
                id=job_id,
                name=f'{symbol.upper()} {norm} warehouse refresh',
                replace_existing=True,
            )

        job = self._scheduler.get_job(job_id)
        next_run = job.next_run_time.isoformat() if job and job.next_run_time else None
        logger.info(f'[LiveScheduler] Activated {symbol.upper()} {norm}. Next: {next_run}')

        return {
            'status': 'activated',
            'job_id': job_id,
            'symbol': symbol.upper(),
            'exchange': exchange.upper(),
            'interval': norm,
            'n_bars': n_bars,
            'cron': cron_kwargs,
            'next_run_utc': next_run,
        }

    def deactivate(
        self,
        symbol: str,
        exchange: str,
        interval: str,
    ) -> dict[str, Any]:
        """Remove a previously activated refresh job."""
        from Live.live_data_fetcher import _normalize_interval

        norm = _normalize_interval(interval)
        job_id = _job_id(symbol, exchange, norm)

        with self._lock:
            if self._scheduler.get_job(job_id):
                self._scheduler.remove_job(job_id)
                logger.info(f'[LiveScheduler] Deactivated {symbol.upper()} {norm}.')
                return {'status': 'deactivated', 'job_id': job_id}

        return {
            'status': 'not_found',
            'job_id': job_id,
            'message': f"No active feed found for {symbol.upper()} {norm}.",
        }

    def list_jobs(self) -> list[dict[str, Any]]:
        """Return metadata for all currently scheduled refresh jobs."""
        return [
            {
                'job_id': job.id,
                'name': job.name,
                'next_run_utc': (
                    job.next_run_time.isoformat() if job.next_run_time else None
                ),
            }
            for job in self._scheduler.get_jobs()
        ]

    @property
    def is_running(self) -> bool:
        return self._started and self._scheduler.running


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_instance: LiveDataScheduler | None = None
_lock = threading.Lock()


def get_scheduler() -> LiveDataScheduler:
    """Return the process-wide LiveDataScheduler singleton."""
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = LiveDataScheduler()
    return _instance
