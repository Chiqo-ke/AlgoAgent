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

import requests as _requests  # used for MT5 bridge calls

# MT5 bridge constants (mirrors MetaTrader5 package values)
_MT5_ORDER_TYPE_BUY      = 0
_MT5_ORDER_TYPE_SELL     = 1
_MT5_TRADE_ACTION_DEAL   = 1
_MT5_ORDER_FILLING_FOK   = 0
_MT5_ORDER_FILLING_IOC   = 1
_MT5_ORDER_FILLING_RETURN = 2
_MT5_ORDER_TIME_GTC      = 0
_MT5_RETCODE_DONE        = 10009


def _bridge_url() -> str:
    """Return the MT5 bridge base URL from env (default: http://127.0.0.1:5555)."""
    return os.environ.get('MT5_BRIDGE_URL', 'http://127.0.0.1:5555').rstrip('/')

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
            magic_number=data['magic_number'],
            sl_pips=data.get('sl_pips'),
            tp_pips=data.get('tp_pips'),
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
        Fetch current open positions from the MT5 bridge service.
        The bridge runs on the server (Wine + MT5 terminal) at MT5_BRIDGE_URL.
        Returns an empty list if the bridge is unavailable.
        """
        session = get_object_or_404(LiveTradingSession, pk=pk, created_by=request.user)

        bridge = _bridge_url()
        try:
            resp = _requests.get(f"{bridge}/positions_get", timeout=10)
            resp.raise_for_status()
            raw = resp.json()
        except _requests.exceptions.ConnectionError:
            logger.warning("MT5 bridge unreachable at %s — session %s positions returning empty", bridge, pk)
            return Response(
                {'positions': [], 'warning': f'MT5 bridge not reachable at {bridge}. Ensure the bridge service is running.'},
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            logger.exception("Error querying MT5 bridge positions for session %s: %s", pk, exc)
            return Response(
                {'positions': [], 'warning': str(exc)},
                status=status.HTTP_200_OK,
            )

        # Bridge returns a list of dicts with MT5 field names.
        # Map them to the frontend's expected format.
        positions = []
        for pos in (raw if isinstance(raw, list) else []):
            positions.append({
                'ticket':        pos.get('ticket'),
                'symbol':        pos.get('symbol'),
                'type':          'buy' if pos.get('type') == _MT5_ORDER_TYPE_BUY else 'sell',
                'volume':        pos.get('volume'),
                'open_price':    pos.get('price_open'),
                'current_price': pos.get('price_current'),
                'profit':        pos.get('profit', 0),
                'swap':          pos.get('swap', 0),
                'open_time':     str(pos.get('time', '')),
                'comment':       pos.get('comment', ''),
                'magic':         pos.get('magic'),
            })

        return Response({'positions': positions}, status=status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # POST /api/trading/sessions/{id}/close_position/  — close a trade
    # ------------------------------------------------------------------
    @action(detail=True, methods=['post'], url_path='close_position')
    def close_position(self, request, pk=None):
        """
        Close a specific open position by ticket number via the MT5 bridge.
        Uses a market order to close at the best available price.
        """
        session = get_object_or_404(LiveTradingSession, pk=pk, created_by=request.user)
        ticket = request.data.get('ticket')

        if not ticket:
            return Response({'error': '"ticket" is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ticket = int(ticket)
        except (TypeError, ValueError):
            return Response({'error': '"ticket" must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)

        bridge = _bridge_url()
        try:
            # 1. Retrieve all open positions then filter by ticket.
            pos_resp = _requests.get(f"{bridge}/positions_get", timeout=10)
            pos_resp.raise_for_status()
            all_positions = pos_resp.json()
            if not isinstance(all_positions, list):
                all_positions = []

            matched = [p for p in all_positions if p.get('ticket') == ticket]
            if not matched:
                return Response({'error': f'Position #{ticket} not found.'}, status=status.HTTP_404_NOT_FOUND)

            pos = matched[0]
            pos_type     = pos.get('type', _MT5_ORDER_TYPE_BUY)  # 0=BUY, 1=SELL
            pos_symbol   = pos.get('symbol')
            pos_volume   = pos.get('volume')
            pos_magic    = pos.get('magic', 0)

            # 2. Get current bid/ask and filling mode from bridge symbol_info.
            sym_resp = _requests.get(f"{bridge}/symbol_info", params={'symbol': pos_symbol}, timeout=10)
            sym_resp.raise_for_status()
            sym_data = sym_resp.json()

            # Close price: BUY positions close at Bid, SELL positions close at Ask
            price = sym_data.get('bid') if pos_type == _MT5_ORDER_TYPE_BUY else sym_data.get('ask')

            # Detect filling mode (bitmask: bit-0=FOK, bit-1=IOC; else RETURN)
            filling_mode = sym_data.get('filling_mode', 0) or 0
            if filling_mode & 1:
                type_filling = _MT5_ORDER_FILLING_FOK
            elif filling_mode & 2:
                type_filling = _MT5_ORDER_FILLING_IOC
            else:
                type_filling = _MT5_ORDER_FILLING_RETURN

            # Opposite order type to close
            close_order_type = _MT5_ORDER_TYPE_SELL if pos_type == _MT5_ORDER_TYPE_BUY else _MT5_ORDER_TYPE_BUY

            # 3. Send close order via bridge.
            order_payload = {
                'action':       _MT5_TRADE_ACTION_DEAL,
                'symbol':       pos_symbol,
                'volume':       pos_volume,
                'type':         close_order_type,
                'position':     ticket,
                'price':        price,
                'deviation':    20,
                'magic':        pos_magic,
                'comment':      'AlgoAgent close',
                'type_time':    _MT5_ORDER_TIME_GTC,
                'type_filling': type_filling,
            }
            order_resp = _requests.post(f"{bridge}/order_send", json=order_payload, timeout=30)
            order_resp.raise_for_status()
            result = order_resp.json()

        except _requests.exceptions.ConnectionError:
            logger.warning("MT5 bridge unreachable at %s — cannot close position %s", bridge, ticket)
            return Response(
                {'error': f'MT5 bridge not reachable at {bridge}. Ensure the bridge service is running.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            logger.exception("Error closing MT5 position %s for session %s: %s", ticket, pk, exc)
            return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        retcode = result.get('retcode')
        if retcode != _MT5_RETCODE_DONE:
            return Response(
                {'error': f'Close order failed. MT5 retcode: {retcode}  ({result.get("retcode_message", "")||""})', 'detail': result},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            'detail': f'Position #{ticket} closed successfully.',
            'order':   result.get('order'),
            'retcode': retcode,
        }, status=status.HTTP_200_OK)

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
