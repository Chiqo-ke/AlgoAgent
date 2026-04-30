"""
Views for Live Trading Sessions API
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, DestroyModelMixin
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
import logging
import os
import sys
import collections
from pathlib import Path

from .models import LiveTradingSession, BrokerCredential, SessionStatus

# Free-tier limit: max concurrent live bots (PENDING + RUNNING)
FREE_BOT_LIMIT = 5
from .serializers import (
    LiveTradingSessionSerializer, LiveTradingSessionCreateSerializer,
    BrokerCredentialSerializer, BrokerCredentialWriteSerializer,
)

# Import session manager from Live directory
LIVE_DIR = Path(__file__).parent.parent / 'Live'
if str(LIVE_DIR) not in sys.path:
    sys.path.insert(0, str(LIVE_DIR))

from session_manager import SessionManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MT5 connectivity helper
# ---------------------------------------------------------------------------
# The production server (Linux) uses the HTTP bridge connector.
# The developer's Windows machine has the native MetaTrader5 SDK installed.
# MT5_USE_BRIDGE=true in .env (loaded by Daphne's EnvironmentFile) selects
# bridge mode; the dev env leaves it unset or false for native SDK mode.

_USE_BRIDGE = os.getenv('MT5_USE_BRIDGE', 'false').lower() == 'true'
_BRIDGE_URL  = os.getenv('MT5_BRIDGE_URL', 'http://127.0.0.1:5555')


def _get_mt5_positions_bridge() -> list:
    """Return open positions via the HTTP bridge (Linux/production)."""
    import requests
    # Direct HTTP call — no LiveConfig needed, no MT5 credentials required
    # (the bridge is already authenticated to the terminal)
    try:
        resp = requests.get(f"{_BRIDGE_URL}/positions_get", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def _normalize_bridge_position(pos: dict) -> dict:
    """Normalise a bridge position dict to the standard API shape."""
    return {
        'ticket':        pos.get('ticket'),
        'symbol':        pos.get('symbol'),
        'type':          'buy' if pos.get('type') == 0 else 'sell',
        'volume':        pos.get('volume'),
        'open_price':    pos.get('price_open'),
        'current_price': pos.get('price_current'),
        'sl':            pos.get('sl'),
        'tp':            pos.get('tp'),
        'profit':        pos.get('profit'),
        'swap':          pos.get('swap'),
        'open_time':     str(pos.get('time', '')),
        'comment':       pos.get('comment', ''),
        'magic':         pos.get('magic'),
    }


# ===========================================================================
# BrokerCredential endpoints
#   GET  /api/trading/credentials/           — list user's saved credentials
#   POST /api/trading/credentials/           — save new credential
#   GET  /api/trading/credentials/{id}/      — retrieve one
#   PUT  /api/trading/credentials/{id}/      — update
#   DELETE /api/trading/credentials/{id}/    — delete
# ===========================================================================

class BrokerCredentialViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin, DestroyModelMixin):
    """
    Save and manage MT5 broker credentials per user.

    Passwords are stored encrypted (Fernet). The plaintext password is
    never returned by any endpoint.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BrokerCredential.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return BrokerCredentialWriteSerializer
        return BrokerCredentialSerializer

    # POST /api/trading/credentials/
    def create(self, request):
        serializer = BrokerCredentialWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        d = serializer.validated_data

        # If setting this as default, clear other defaults
        if d.get('is_default'):
            BrokerCredential.objects.filter(user=request.user, is_default=True).update(is_default=False)

        cred = BrokerCredential(
            user=request.user,
            label=d['label'],
            mt5_login=d['mt5_login'],
            mt5_server=d['mt5_server'],
            mt5_terminal_path=d.get('mt5_terminal_path', ''),
            is_default=d.get('is_default', False),
        )
        cred.set_password(d['mt5_password'])
        try:
            cred.save()
        except IntegrityError:
            return Response(
                {"label": ["A credential with this label already exists."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(BrokerCredentialSerializer(cred).data, status=status.HTTP_201_CREATED)

    # PUT /api/trading/credentials/{id}/
    def update(self, request, pk=None):
        cred = get_object_or_404(BrokerCredential, pk=pk, user=request.user)
        serializer = BrokerCredentialWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        d = serializer.validated_data

        if d.get('is_default'):
            BrokerCredential.objects.filter(user=request.user, is_default=True).exclude(pk=pk).update(is_default=False)

        cred.label = d['label']
        cred.mt5_login = d['mt5_login']
        cred.mt5_server = d['mt5_server']
        cred.mt5_terminal_path = d.get('mt5_terminal_path', '')
        cred.is_default = d.get('is_default', False)
        cred.set_password(d['mt5_password'])
        cred.save()

        return Response(BrokerCredentialSerializer(cred).data)

    # PATCH /api/trading/credentials/{id}/  — partial update
    def partial_update(self, request, pk=None):
        cred = get_object_or_404(BrokerCredential, pk=pk, user=request.user)
        serializer = BrokerCredentialWriteSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        d = serializer.validated_data

        if d.get('is_default'):
            BrokerCredential.objects.filter(user=request.user, is_default=True).exclude(pk=pk).update(is_default=False)

        if 'label' in d:
            cred.label = d['label']
        if 'mt5_login' in d:
            cred.mt5_login = d['mt5_login']
        if 'mt5_server' in d:
            cred.mt5_server = d['mt5_server']
        if 'mt5_terminal_path' in d:
            cred.mt5_terminal_path = d['mt5_terminal_path']
        if 'is_default' in d:
            cred.is_default = d['is_default']
        if 'mt5_password' in d:
            cred.set_password(d['mt5_password'])
        cred.save()

        return Response(BrokerCredentialSerializer(cred).data)


# ===========================================================================
# LiveTradingSession endpoints
# ===========================================================================

class LiveTradingSessionViewSet(ListModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    """
    Manage live trading sessions.

    list:   GET  /api/trading/sessions/
    retrieve: GET /api/trading/sessions/{id}/
    create: POST /api/trading/sessions/
    stop:   POST /api/trading/sessions/{id}/stop/
    destroy: DELETE /api/trading/sessions/{id}/
    """
    serializer_class = LiveTradingSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LiveTradingSession.objects.filter(created_by=self.request.user)

    # ------------------------------------------------------------------
    # POST /api/trading/sessions/  — start a new session
    # ------------------------------------------------------------------
    def create(self, request):
        serializer = LiveTradingSessionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # ----------------------------------------------------------------
        # Subscription enforcement: free users are limited to FREE_BOT_LIMIT
        # concurrent live bots (PENDING + RUNNING both count).
        # ----------------------------------------------------------------
        profile = getattr(request.user, 'profile', None)
        if profile is None or profile.subscription_plan == 'free':
            active_count = LiveTradingSession.objects.filter(
                created_by=request.user,
                status__in=[SessionStatus.PENDING, SessionStatus.RUNNING],
            ).count()
            if active_count >= FREE_BOT_LIMIT:
                return Response(
                    {
                        'error': (
                            f'Free plan allows up to {FREE_BOT_LIMIT} live bots running at the same time. '
                            f'You currently have {active_count} active. '
                            'Stop or delete an existing bot to free up a slot, '
                            'or upgrade to Premium for unlimited live bots.'
                        ),
                        'code': 'bot_limit_reached',
                        'active_bot_count': active_count,
                        'bot_limit': FREE_BOT_LIMIT,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Resolve MT5 credentials: saved credential or inline
        credential_id = data.get('credential_id')
        if credential_id:
            try:
                cred = BrokerCredential.objects.get(pk=credential_id, user=request.user)
            except BrokerCredential.DoesNotExist:
                return Response(
                    {'error': 'Broker credential not found or access denied.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            mt5_login = cred.mt5_login
            mt5_password = cred.get_password()
            mt5_server = cred.mt5_server
            mt5_terminal_path = cred.mt5_terminal_path
        else:
            mt5_login = data['mt5_login']
            mt5_password = data['mt5_password']
            mt5_server = data['mt5_server']
            mt5_terminal_path = data.get('mt5_terminal_path', '')

        # Validate strategy ownership
        from strategy_api.models import Strategy
        try:
            strategy = Strategy.objects.get(pk=data['strategy_id'], created_by=request.user)
        except Strategy.DoesNotExist:
            return Response(
                {'error': 'Strategy not found or access denied.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not strategy.strategy_code:
            return Response(
                {'error': 'Strategy has no code. Generate and save the strategy first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Build session record
        session = LiveTradingSession(
            strategy=strategy,
            symbols=data['symbols'],
            timeframe=data['timeframe'],
            dry_run=data['dry_run'],
            risk_pct=data['risk_pct'],
            exit_mode=data.get('exit_mode'),
            magic_number=data['magic_number'],
            sl_pips=data.get('sl_pips'),
            tp_pips=data.get('tp_pips'),
            data_bars=data.get('data_bars', 5000),
            max_lots=data.get('max_lots', 1.0),
            lot_size=data.get('lot_size', None),
            mt5_login=mt5_login,
            mt5_server=mt5_server,
            mt5_terminal_path=mt5_terminal_path,
            status=SessionStatus.PENDING,
            created_by=request.user,
        )
        session.set_mt5_password(mt5_password)
        session.save()

        # Spawn subprocess
        manager = SessionManager()
        success, pid, error = manager.start_session(session)

        if not success:
            session.status = SessionStatus.ERROR
            session.error_message = error or 'Failed to start session'
            session.save()
            return Response(
                {'error': session.error_message, 'session_id': session.pk},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        session.status = SessionStatus.RUNNING
        session.pid = pid
        session.started_at = timezone.now()
        session.save()

        return Response(
            LiveTradingSessionSerializer(session).data,
            status=status.HTTP_201_CREATED
        )

    # ------------------------------------------------------------------
    # POST /api/trading/sessions/{id}/stop/  — stop a running session
    # ------------------------------------------------------------------
    @action(detail=True, methods=['post'], url_path='stop')
    def stop(self, request, pk=None):
        session = get_object_or_404(LiveTradingSession, pk=pk, created_by=request.user)

        if session.status != SessionStatus.RUNNING:
            return Response(
                {'detail': f'Session is not running (current status: {session.status}).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        manager = SessionManager()
        stopped = manager.stop_session(session)

        session.status = SessionStatus.STOPPED
        session.stopped_at = timezone.now()
        session.save()

        return Response({
            'detail': 'Session stopped.' if stopped else 'Kill switch sent; process may still be shutting down.',
            'session': LiveTradingSessionSerializer(session).data
        })

    # ------------------------------------------------------------------
    # DELETE /api/trading/sessions/{id}/  — stop + delete
    # ------------------------------------------------------------------
    def destroy(self, request, *args, **kwargs):
        session = self.get_object()

        if session.status == SessionStatus.RUNNING:
            manager = SessionManager()
            manager.stop_session(session)

        # Clean up temp files
        manager = SessionManager()
        manager.cleanup_session_files(session)

        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ------------------------------------------------------------------
    # GET /api/trading/sessions/{id}/positions/  — fetch open MT5 positions
    # ------------------------------------------------------------------
    @action(detail=True, methods=['get'], url_path='positions')
    def positions(self, request, pk=None):
        """
        Fetch current open positions from MT5 for this session's account.

        On the production server MT5_USE_BRIDGE=true routes through the HTTP
        bridge connector (Linux / Wine setup).  On the developer's Windows
        machine the native MetaTrader5 SDK is used instead.
        """
        session = get_object_or_404(LiveTradingSession, pk=pk, created_by=request.user)

        try:
            if _USE_BRIDGE:
                # ── Bridge path (production / Linux) ──────────────────────
                raw = _get_mt5_positions_bridge()
                positions = [_normalize_bridge_position(p) for p in raw]
            else:
                # ── Native SDK path (developer Windows machine) ────────────
                try:
                    import MetaTrader5 as mt5
                except ImportError:
                    return Response(
                        {'positions': [], 'warning': 'MetaTrader5 package not installed.'},
                        status=status.HTTP_200_OK
                    )
                password = session.get_mt5_password()
                init_kwargs = {
                    'login':    session.mt5_login,
                    'password': password,
                    'server':   session.mt5_server,
                }
                if session.mt5_terminal_path:
                    init_kwargs['path'] = session.mt5_terminal_path

                if not mt5.initialize(**init_kwargs):
                    return Response(
                        {'positions': [], 'warning': f'MT5 init failed: {mt5.last_error()}'},
                        status=status.HTTP_200_OK
                    )
                raw = mt5.positions_get()
                mt5.shutdown()

                if raw is None:
                    return Response({'positions': []}, status=status.HTTP_200_OK)

                positions = []
                for pos in raw:
                    positions.append({
                        'ticket':        pos.ticket,
                        'symbol':        pos.symbol,
                        'type':          'buy' if pos.type == mt5.ORDER_TYPE_BUY else 'sell',
                        'volume':        pos.volume,
                        'open_price':    pos.price_open,
                        'current_price': pos.price_current,
                        'sl':            pos.sl,
                        'tp':            pos.tp,
                        'profit':        pos.profit,
                        'swap':          pos.swap,
                        'open_time':     str(pos.time),
                        'comment':       pos.comment,
                        'magic':         pos.magic,
                    })

            return Response({'positions': positions}, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.exception("Error fetching MT5 positions for session %s: %s", pk, exc)
            return Response(
                {'positions': [], 'warning': str(exc)},
                status=status.HTTP_200_OK
            )

    # ------------------------------------------------------------------
    # GET /api/trading/sessions/all_positions/
    #   Optional: ?strategy_id=<int>  — filter to positions opened by that strategy
    # ------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='all_positions')
    def all_positions(self, request):
        """
        Return ALL open MT5 positions directly from the broker account,
        regardless of whether any bot session is running.

        Positions are enriched with session metadata by:
          1. Magic-number lookup across ALL user sessions (any status)
          2. Comment-based lookup (format: <slug>_s<sessionId>_<hash>)

        Optional query param ?strategy_id=<int> filters to positions
        belonging to that specific strategy only.
        """
        import re as _re

        strategy_id_filter = request.query_params.get('strategy_id')
        if strategy_id_filter:
            try:
                strategy_id_filter = int(strategy_id_filter)
            except (ValueError, TypeError):
                strategy_id_filter = None

        # Build lookup maps from ALL sessions for this user (any status)
        all_user_sessions = LiveTradingSession.objects.filter(
            created_by=request.user,
        ).select_related('strategy')

        # magic → session metadata (last session with that magic wins)
        magic_map = {}
        # session_pk (int) → session metadata
        session_pk_map = {}
        for s in all_user_sessions:
            meta = {
                'session_id':    s.pk,
                'strategy_id':   s.strategy_id,
                'strategy_name': str(s.strategy) if s.strategy else None,
                'timeframe':     s.timeframe,
                'symbols':       s.symbols,
            }
            if s.magic_number:
                magic_map[s.magic_number] = meta
            session_pk_map[s.pk] = meta

        # Regex to extract session id from comment (new format: slug_sNN_hash)
        _SESSION_RE = _re.compile(r'_s(\d+)_')

        try:
            if _USE_BRIDGE:
                raw = _get_mt5_positions_bridge()
                all_pos = [_normalize_bridge_position(p) for p in raw]
            else:
                try:
                    import MetaTrader5 as mt5
                except ImportError:
                    return Response(
                        {'positions': [], 'warning': 'MetaTrader5 package not installed.'},
                        status=status.HTTP_200_OK
                    )
                raw = mt5.positions_get() or []
                mt5.shutdown()
                all_pos = [{
                    'ticket':        p.ticket,
                    'symbol':        p.symbol,
                    'type':          'buy' if p.type == mt5.ORDER_TYPE_BUY else 'sell',
                    'volume':        p.volume,
                    'open_price':    p.price_open,
                    'current_price': p.price_current,
                    'sl':            p.sl,
                    'tp':            p.tp,
                    'profit':        p.profit,
                    'swap':          p.swap,
                    'open_time':     str(p.time),
                    'comment':       p.comment,
                    'magic':         p.magic,
                } for p in raw]

            # Enrich each position with session/strategy metadata
            for pos in all_pos:
                meta = None
                # 1. Try magic-number lookup
                if pos.get('magic'):
                    meta = magic_map.get(pos['magic'])
                # 2. Fall back to comment-based session lookup
                if not meta:
                    comment = pos.get('comment', '') or ''
                    m = _SESSION_RE.search(comment)
                    if m:
                        try:
                            sid = int(m.group(1))
                            meta = session_pk_map.get(sid)
                        except (ValueError, TypeError):
                            pass
                pos.update(meta or {
                    'session_id':    None,
                    'strategy_id':   None,
                    'strategy_name': None,
                    'timeframe':     None,
                    'symbols':       None,
                })

            # Filter to specific strategy if requested
            if strategy_id_filter is not None:
                all_pos = [p for p in all_pos if p.get('strategy_id') == strategy_id_filter]

            return Response({
                'positions': all_pos,
                'total':     len(all_pos),
            }, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.exception("Error fetching all positions for user %s: %s", request.user, exc)
            return Response(
                {'positions': [], 'warning': str(exc)},
                status=status.HTTP_200_OK
            )

    # ------------------------------------------------------------------
    # GET /api/trading/sessions/trade_history/?strategy_id=<id>
    # ------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='trade_history')
    def trade_history(self, request):
        """
        Return closed trades from audit.db for all sessions belonging to
        the given strategy_id (scoped to the current user).
        """
        import sqlite3 as _sqlite3

        strategy_id = request.query_params.get('strategy_id')
        if not strategy_id:
            return Response({'error': 'strategy_id query param is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            strategy_id = int(strategy_id)
        except (ValueError, TypeError):
            return Response({'error': 'strategy_id must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)

        sessions = list(
            LiveTradingSession.objects.filter(
                strategy_id=strategy_id,
                created_by=request.user,
            ).select_related('strategy').values('id', 'strategy__name')
        )

        empty = Response({'trades': [], 'total_trades': 0, 'total_pnl': 0.0, 'win_rate': 0.0})

        if not sessions:
            return empty

        # Build lookup: "session_<id>" → human-readable bot/strategy name
        session_name_map = {
            f'session_{s["id"]}': s['strategy__name'] or f'session_{s["id"]}'
            for s in sessions
        }
        strategy_id_keys = list(session_name_map.keys())

        audit_db = Path(__file__).parent.parent / 'Live' / 'data' / 'audit.db'
        if not audit_db.exists():
            return empty

        try:
            conn = _sqlite3.connect(str(audit_db))
            conn.row_factory = _sqlite3.Row
            placeholders = ','.join('?' for _ in strategy_id_keys)
            rows = conn.execute(
                f'SELECT * FROM trades WHERE strategy_id IN ({placeholders}) ORDER BY timestamp DESC',
                strategy_id_keys,
            ).fetchall()
            conn.close()
        except Exception as exc:
            logger.error('trade_history error reading audit.db: %s', exc)
            return empty

        trades = [
            {
                'id': row['id'],
                'timestamp': row['timestamp'],
                'symbol': row['symbol'],
                'side': 'buy' if str(row['side']) == '0' else 'sell',
                'entry_price': row['entry_price'],
                'exit_price': row['exit_price'],
                'volume': row['volume'],
                'profit': row['profit'],
                'commission': row['commission'],
                'swap': row['swap'],
                'duration_seconds': row['duration_seconds'],
                'session_id': row['strategy_id'],
                'bot_name': session_name_map.get(row['strategy_id'], row['strategy_id']),
            }
            for row in rows
        ]

        total_pnl = round(sum(float(t['profit']) for t in trades), 2)
        win_rate = round(sum(1 for t in trades if float(t['profit']) > 0) / len(trades) * 100, 2) if trades else 0.0

        return Response({
            'trades': trades,
            'total_trades': len(trades),
            'total_pnl': total_pnl,
            'win_rate': win_rate,
        })

    # ------------------------------------------------------------------
    # POST /api/trading/sessions/{id}/close_position/  — close a trade
    # ------------------------------------------------------------------
    @action(detail=True, methods=['post'], url_path='close_position')
    def close_position(self, request, pk=None):
        """
        Close a specific open position by ticket number.
        Uses a market order to close at the best available price.

        Respects MT5_USE_BRIDGE to choose bridge (production) or native SDK
        (developer machine) — same pattern as the positions() endpoint.
        """
        session = get_object_or_404(LiveTradingSession, pk=pk, created_by=request.user)
        ticket = request.data.get('ticket')

        if not ticket:
            return Response({'error': '"ticket" is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ticket = int(ticket)
        except (TypeError, ValueError):
            return Response({'error': '"ticket" must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if _USE_BRIDGE:
                # ── Bridge path (production / Linux) ──────────────────────
                import requests as _requests

                # Find the position directly via the bridge HTTP API
                positions = _get_mt5_positions_bridge()
                pos = next((p for p in positions if p.get('ticket') == ticket), None)
                if pos is None:
                    return Response(
                        {'error': f'Position #{ticket} not found.'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # Get current bid/ask from symbol info
                try:
                    sym_resp = _requests.get(
                        f"{_BRIDGE_URL}/symbol_info",
                        params={"symbol": pos['symbol']},
                        timeout=10
                    )
                    sym_resp.raise_for_status()
                    sym_info = sym_resp.json()
                except Exception as e:
                    return Response(
                        {'error': f'Could not get symbol info: {e}'},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )

                # type==0 is BUY → close with SELL at bid; type==1 is SELL → close with BUY at ask
                is_buy = pos.get('type') == 0
                price = sym_info.get('bid') if is_buy else sym_info.get('ask')
                close_type = 1 if is_buy else 0  # SELL=1, BUY=0

                request_payload = {
                    'action':       1,  # TRADE_ACTION_DEAL
                    'symbol':       pos['symbol'],
                    'volume':       pos['volume'],
                    'type':         close_type,
                    'position':     ticket,
                    'price':        price,
                    'deviation':    20,
                    'magic':        pos.get('magic', session.magic_number),
                    'comment':      'AlgoAgent close',
                    'type_time':    0,   # ORDER_TIME_GTC
                    'type_filling': 2,   # ORDER_FILLING_RETURN (market execution)
                }
                try:
                    result_resp = _requests.post(
                        f"{_BRIDGE_URL}/order_send",
                        json=request_payload,
                        timeout=60
                    )
                    result_resp.raise_for_status()
                    result = result_resp.json()
                except Exception as e:
                    return Response({'error': f'Bridge order_send failed: {e}'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

                if result is None or result.get('retcode') not in (10008, 10009):
                    retcode = result.get('retcode', 'unknown') if result else 'unknown'
                    return Response(
                        {'error': f'Close order failed. MT5 retcode: {retcode}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                return Response({
                    'detail':  f'Position #{ticket} closed successfully.',
                    'order':   result.get('order'),
                    'retcode': result.get('retcode'),
                }, status=status.HTTP_200_OK)

            else:
                # ── Native SDK path (developer Windows machine) ────────────
                try:
                    import MetaTrader5 as mt5
                except ImportError:
                    return Response(
                        {'error': 'MetaTrader5 package not installed.'},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )

                password = session.get_mt5_password()
                init_kwargs = {
                    'login':    session.mt5_login,
                    'password': password,
                    'server':   session.mt5_server,
                }
                if session.mt5_terminal_path:
                    init_kwargs['path'] = session.mt5_terminal_path

                if not mt5.initialize(**init_kwargs):
                    return Response(
                        {'error': f'MT5 init failed: {mt5.last_error()}'},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )

                position = mt5.positions_get(ticket=ticket)
                if not position:
                    mt5.shutdown()
                    return Response(
                        {'error': f'Position #{ticket} not found.'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                pos = position[0]
                close_order_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
                tick = mt5.symbol_info_tick(pos.symbol)
                price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask

                sym_info = mt5.symbol_info(pos.symbol)
                filling_mode = sym_info.filling_mode if sym_info else 0
                if filling_mode & 1:
                    type_filling = mt5.ORDER_FILLING_FOK
                elif filling_mode & 2:
                    type_filling = mt5.ORDER_FILLING_IOC
                else:
                    type_filling = mt5.ORDER_FILLING_RETURN

                request_payload = {
                    'action':       mt5.TRADE_ACTION_DEAL,
                    'symbol':       pos.symbol,
                    'volume':       pos.volume,
                    'type':         close_order_type,
                    'position':     ticket,
                    'price':        price,
                    'deviation':    20,
                    'magic':        pos.magic,
                    'comment':      'AlgoAgent close',
                    'type_time':    mt5.ORDER_TIME_GTC,
                    'type_filling': type_filling,
                }
                result = mt5.order_send(request_payload)
                mt5.shutdown()

                if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                    retcode = result.retcode if result else 'unknown'
                    return Response(
                        {'error': f'Close order failed. MT5 retcode: {retcode}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                return Response({
                    'detail':  f'Position #{ticket} closed successfully.',
                    'order':   result.order,
                    'retcode': result.retcode,
                }, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.exception("Error closing MT5 position %s for session %s: %s", ticket, pk, exc)
            return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ------------------------------------------------------------------
    # GET /api/trading/sessions/{id}/logs/  — tail subprocess activity log
    # ------------------------------------------------------------------
    @action(detail=True, methods=['get'], url_path='logs')
    def logs(self, request, pk=None):
        """
        Return the last 5 summary lines from the subprocess log file for this session,
        plus a last-modified timestamp and whether the subprocess is still alive.

        Summary lines are those containing key events:
          Iteration, Processing, Loop completed, ERROR, Kill switch, STARTUP, SHUTDOWN.
        """
        session = get_object_or_404(LiveTradingSession, pk=pk, created_by=request.user)

        # Derive log path from session pk (predictable, no DB field needed)
        log_path = LIVE_DIR / 'session_logs' / f'session_{pk}.log'

        # Check whether the subprocess is still alive
        is_alive = False
        if session.pid:
            try:
                manager = SessionManager()
                is_alive = manager.is_running(session.pid)
            except Exception:
                pass

        if not log_path.exists():
            return Response({
                'lines': [],
                'last_modified_at': None,
                'is_process_alive': is_alive,
            })

        # Read last 80 raw lines efficiently — seek to end rather than reading
        # the entire file (session logs can grow to several GB, which blocks
        # the Daphne thread pool and causes 504s for all other requests).
        try:
            TAIL_BYTES = 131072  # 128 KB — plenty for 80 log lines
            with open(log_path, 'rb') as fb:
                fb.seek(0, 2)
                file_size = fb.tell()
                read_start = max(0, file_size - TAIL_BYTES)
                fb.seek(read_start)
                raw = fb.read()
            text = raw.decode('utf-8', errors='replace')
            # Drop the first (potentially partial) line when we seeked mid-file
            if read_start > 0:
                text = text[text.find('\n') + 1:]
            tail = collections.deque(text.splitlines(), maxlen=80)
        except Exception as exc:
            logger.warning('Could not read log file %s: %s', log_path, exc)
            return Response({
                'lines': [],
                'last_modified_at': None,
                'is_process_alive': is_alive,
            })

        # Filter to summary/signal lines only
        SUMMARY_KEYWORDS = ('Iteration', 'Processing', 'Loop completed', 'ERROR', 'Error',
                            'Kill switch', 'STARTUP', 'SHUTDOWN', '\u2713', '\U0001f680')
        summary_lines = [
            line.rstrip('\n\r')
            for line in tail
            if any(kw in line for kw in SUMMARY_KEYWORDS)
        ]
        # Return last 5 summary lines
        result_lines = summary_lines[-5:]

        # Last-modified timestamp
        import datetime
        mtime = log_path.stat().st_mtime
        last_modified_at = datetime.datetime.fromtimestamp(
            mtime, tz=datetime.timezone.utc
        ).isoformat()

        return Response({
            'lines': result_lines,
            'last_modified_at': last_modified_at,
            'is_process_alive': is_alive,
        })


# ─── Live Analytics ───────────────────────────────────────────────────────────

class LiveAnalyticsView(APIView):
    """
    GET /api/trading/live-analytics/

    Returns aggregate live-trading performance per strategy for the current user.
    Reads closed trades from audit.db, groups them by strategy via session FK,
    and returns metrics compatible with the frontend BotPerformance interface.
    """
    permission_classes = [IsAuthenticated]

    AUDIT_DB = Path(__file__).parent.parent / 'Live' / 'data' / 'audit.db'

    def get(self, request):
        import sqlite3
        from collections import defaultdict

        # All sessions that belong to the current user
        sessions = (
            LiveTradingSession.objects
            .filter(created_by=request.user)
            .select_related('strategy')
            .values('id', 'strategy_id', 'strategy__name')
        )

        if not sessions or not self.AUDIT_DB.exists():
            return Response([])

        # Map "session_<id>" → session info
        session_map = {f'session_{s["id"]}': s for s in sessions}

        try:
            conn = sqlite3.connect(str(self.AUDIT_DB))
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            placeholders = ','.join('?' * len(session_map))
            c.execute(
                f'SELECT strategy_id, profit FROM trades WHERE strategy_id IN ({placeholders})',
                list(session_map.keys()),
            )
            rows = c.fetchall()

            # Get current account balance for rough return % calculation
            c.execute(
                'SELECT balance FROM account_snapshots ORDER BY id DESC LIMIT 1'
            )
            snap = c.fetchone()
            conn.close()

            account_balance = float(snap['balance']) if snap and snap['balance'] else 1.0

        except Exception as exc:
            logger.error(f'LiveAnalyticsView error reading audit.db: {exc}')
            return Response({'error': str(exc)}, status=500)

        # Aggregate per strategy
        stats: dict = defaultdict(lambda: {
            'total_trades': 0, 'wins': 0, 'total_pnl': 0.0, 'strategy_name': '',
        })

        for row in rows:
            info = session_map.get(row['strategy_id'])
            if not info:
                continue
            sid = info['strategy_id']
            s = stats[sid]
            s['total_trades'] += 1
            if row['profit'] > 0:
                s['wins'] += 1
            s['total_pnl'] += float(row['profit'])
            s['strategy_name'] = info['strategy__name'] or ''

        result = []
        for strategy_id, s in stats.items():
            t = s['total_trades']
            win_rate = round(s['wins'] / t * 100, 2) if t else 0.0
            # total_return as % of current account balance (rough live approximation)
            total_return = round(s['total_pnl'] / account_balance * 100, 4) if account_balance else 0.0
            result.append({
                'strategy_id': strategy_id,
                'strategy_name': s['strategy_name'],
                'total_trades': t,
                'win_rate': win_rate,
                'total_pnl': round(s['total_pnl'], 2),
                'total_return': total_return,
                # Fields expected by BotPerformance interface (null = not computed for live)
                'sharpe_ratio': None,
                'max_drawdown': None,
                'is_verified': t > 0,
                'verification_status': 'verified' if t > 0 else 'unverified',
            })

        return Response(result)
