"""
Live Trading Data API — Views

Endpoints
---------
POST /api/live/data/refresh/
    On-demand fetch of fresh bars for a symbol/interval.
    Strips the incomplete (currently forming) bar before writing.

GET  /api/live/data/status/?symbol=&interval=
    Warehouse freshness info (no fetch).

POST /api/live/scheduler/activate/
    Register a recurring cron-based refresh for a symbol/interval feed.

POST /api/live/scheduler/deactivate/
    Remove a recurring refresh feed.

GET  /api/live/scheduler/jobs/
    List all currently scheduled refresh jobs.
"""

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger('live_api.views')

# Max bars allowed per request (tvDatafeed hard limit)
_MAX_BARS = 4000


# ---------------------------------------------------------------------------
# Data endpoints
# ---------------------------------------------------------------------------

class LiveDataRefreshView(APIView):
    """
    POST /api/live/data/refresh/

    Fetch fresh bars from TradingView and upsert them into the local warehouse.
    The currently-forming (incomplete) bar is always excluded from the result.

    Request body (JSON):
        {
            "symbol":   "EURUSD",       required
            "exchange": "FX",           required  (e.g. FX, NASDAQ, BITSTAMP, TVC)
            "interval": "1h",           required  (e.g. 1m, 5m, 15m, 1h, 4h, 1d)
            "n_bars":   500             optional  default=500, max=4000
        }

    Response (200 OK):
        {
            "symbol":         "EURUSD",
            "exchange":       "FX",
            "interval":       "1h",
            "warehouse_path": "/.../.../Data/data/eurusd_1h.csv",
            "new_rows":       42,
            "updated_rows":   3,
            "total_rows":     3847,
            "latest_bar":     "2026-03-11T07:00:00+00:00",
            "fetch_time_utc": "2026-03-11T08:25:17.334521+00:00",
            "status":         "ok",
            "message":        "42 new bars added, 3 existing bars refreshed."
        }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        symbol   = request.data.get('symbol',   '').strip().upper()
        exchange = request.data.get('exchange', '').strip().upper()
        interval = request.data.get('interval', '').strip().lower()
        n_bars   = request.data.get('n_bars', 500)

        if not symbol or not exchange or not interval:
            return Response(
                {'error': 'symbol, exchange, and interval are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            n_bars = int(n_bars)
        except (TypeError, ValueError):
            return Response(
                {'error': 'n_bars must be an integer.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (1 <= n_bars <= _MAX_BARS):
            return Response(
                {'error': f'n_bars must be between 1 and {_MAX_BARS}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from Live.live_data_fetcher import LiveDataFetcher
            result = LiveDataFetcher().refresh(symbol, exchange, interval, n_bars=n_bars)
        except ImportError as exc:
            logger.error(f'tvDatafeed import failed: {exc}')
            return Response(
                {'error': f'tvDatafeed is not installed: {exc}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            logger.error(f'LiveDataRefreshView error: {exc}', exc_info=True)
            return Response(
                {'error': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        http_status = (
            status.HTTP_200_OK
            if result['status'] == 'ok'
            else status.HTTP_206_PARTIAL_CONTENT
        )
        return Response(result, status=http_status)


class LiveDataStatusView(APIView):
    """
    GET /api/live/data/status/?symbol=EURUSD&interval=1h

    Returns freshness information about a warehouse CSV without fetching.

    Response:
        {
            "symbol":        "EURUSD",
            "interval":      "1h",
            "warehouse_path": "...",
            "exists":        true,
            "total_rows":    3805,
            "latest_bar":    "2026-03-11T07:00:00+00:00",
            "oldest_bar":    "2024-09-01T00:00:00+00:00",
            "stale_minutes": 85,
            "status":        "ok"
        }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        symbol   = request.query_params.get('symbol',   '').strip().upper()
        interval = request.query_params.get('interval', '').strip().lower()

        if not symbol or not interval:
            return Response(
                {'error': 'symbol and interval query parameters are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from Live.live_data_fetcher import LiveDataFetcher
            result = LiveDataFetcher().get_warehouse_status(symbol, interval)
        except Exception as exc:
            logger.error(f'LiveDataStatusView error: {exc}', exc_info=True)
            return Response(
                {'error': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(result)


# ---------------------------------------------------------------------------
# Scheduler endpoints
# ---------------------------------------------------------------------------

class LiveSchedulerActivateView(APIView):
    """
    POST /api/live/scheduler/activate/

    Register a recurring cron-based warehouse refresh for a symbol/interval feed.
    The scheduler fires LiveDataFetcher.refresh() at the close of each bar period.

    If a job for the same feed already exists, it is replaced.

    Request body:
        {
            "symbol":   "EURUSD",
            "exchange": "FX",
            "interval": "1h",
            "n_bars":   500       optional, default=500
        }

    Response (200 OK):
        {
            "status":       "activated",
            "job_id":       "live_feed__EURUSD__FX__1h",
            "symbol":       "EURUSD",
            "exchange":     "FX",
            "interval":     "1h",
            "n_bars":       500,
            "cron":         {"minute": "1"},
            "next_run_utc": "2026-03-11T09:01:00+00:00"
        }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        symbol   = request.data.get('symbol',   '').strip().upper()
        exchange = request.data.get('exchange', '').strip().upper()
        interval = request.data.get('interval', '').strip().lower()
        n_bars   = request.data.get('n_bars', 500)

        if not symbol or not exchange or not interval:
            return Response(
                {'error': 'symbol, exchange, and interval are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            n_bars = int(n_bars)
        except (TypeError, ValueError):
            return Response(
                {'error': 'n_bars must be an integer.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (1 <= n_bars <= _MAX_BARS):
            return Response(
                {'error': f'n_bars must be between 1 and {_MAX_BARS}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from live_api.scheduler import get_scheduler
            result = get_scheduler().activate(symbol, exchange, interval, n_bars=n_bars)
        except Exception as exc:
            logger.error(f'LiveSchedulerActivateView error: {exc}', exc_info=True)
            return Response(
                {'error': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        http_status = (
            status.HTTP_200_OK
            if result.get('status') == 'activated'
            else status.HTTP_400_BAD_REQUEST
        )
        return Response(result, status=http_status)


class LiveSchedulerDeactivateView(APIView):
    """
    POST /api/live/scheduler/deactivate/

    Remove a recurring refresh job.

    Request body:
        { "symbol": "EURUSD", "exchange": "FX", "interval": "1h" }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        symbol   = request.data.get('symbol',   '').strip().upper()
        exchange = request.data.get('exchange', '').strip().upper()
        interval = request.data.get('interval', '').strip().lower()

        if not symbol or not exchange or not interval:
            return Response(
                {'error': 'symbol, exchange, and interval are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from live_api.scheduler import get_scheduler
            result = get_scheduler().deactivate(symbol, exchange, interval)
        except Exception as exc:
            logger.error(f'LiveSchedulerDeactivateView error: {exc}', exc_info=True)
            return Response(
                {'error': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(result)


class LiveSchedulerJobsView(APIView):
    """
    GET /api/live/scheduler/jobs/

    List all currently active scheduled refresh jobs and scheduler state.

    Response:
        {
            "is_running": true,
            "jobs": [
                {
                    "job_id":       "live_feed__EURUSD__FX__1h",
                    "name":         "EURUSD 1h warehouse refresh",
                    "next_run_utc": "2026-03-11T09:01:00+00:00"
                },
                ...
            ]
        }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from live_api.scheduler import get_scheduler
            sched = get_scheduler()
            return Response({
                'is_running': sched.is_running,
                'jobs': sched.list_jobs(),
            })
        except Exception as exc:
            logger.error(f'LiveSchedulerJobsView error: {exc}', exc_info=True)
            return Response(
                {'error': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
