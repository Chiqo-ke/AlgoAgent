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
    # GET /api/trading/sessions/all_positions/  — positions across all
    #     RUNNING sessions owned by the logged-in user
    # ------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='all_positions')
    def all_positions(self, request):
        """
        Return all open MT5 positions across every RUNNING session for the
        logged-in user.  Each position is enriched with session metadata
        (session_id, strategy name, timeframe, symbols) so the frontend
        knows which bot opened each trade.

        The magic number is used to match a position to its session when
        multiple sessions share the same broker account.
        """
        user_sessions = LiveTradingSession.objects.filter(
            created_by=request.user,
            status=SessionStatus.RUNNING,
        )

        # Build magic-number → session metadata lookup
        magic_map = {
            s.magic_number: {
                'session_id':    s.pk,
                'strategy_name': str(s.strategy),
                'timeframe':     s.timeframe,
                'symbols':       s.symbols,
            }
            for s in user_sessions
        }

        if not magic_map:
            return Response({'positions': [], 'sessions_checked': 0}, status=status.HTTP_200_OK)

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
                # Use credentials from the first running session to authenticate
                first = user_sessions.first()
                password = first.get_mt5_password()
                init_kwargs = {
                    'login':    first.mt5_login,
                    'password': password,
                    'server':   first.mt5_server,
                }
                if first.mt5_terminal_path:
                    init_kwargs['path'] = first.mt5_terminal_path

                if not mt5.initialize(**init_kwargs):
                    return Response(
                        {'positions': [], 'warning': f'MT5 init failed: {mt5.last_error()}'},
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

            # Enrich each position with session metadata via magic number
            for pos in all_pos:
                meta = magic_map.get(pos.get('magic'))
                if meta:
                    pos.update(meta)
                else:
                    # Position exists on account but doesn't match any running session
                    pos.update({
                        'session_id':    None,
                        'strategy_name': None,
                        'timeframe':     None,
                        'symbols':       None,
                    })

            return Response({
                'positions':       all_pos,
                'sessions_checked': user_sessions.count(),
            }, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.exception("Error fetching all positions for user %s: %s", request.user, exc)
            return Response(
                {'positions': [], 'warning': str(exc)},
                status=status.HTTP_200_OK
            )

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

        # Read last 80 raw lines efficiently
        try:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                tail = collections.deque(f, maxlen=80)
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
