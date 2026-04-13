import os
import logging
import threading
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class TradingSessionsApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trading_sessions_api'

    def ready(self):
        # Only start the monitor in the main process (not during migrations,
        # management commands, or Celery workers that import Django apps).
        if os.environ.get('RUN_MAIN') == 'true' or _is_server_process():
            _start_session_monitor()


def _is_server_process():
    """True when running under Daphne/Gunicorn/uWSGI (not manage.py commands)."""
    import sys
    argv0 = os.path.basename(sys.argv[0]) if sys.argv else ''
    # daphne, gunicorn, uvicorn all launch with their own executable name
    server_procs = ('daphne', 'gunicorn', 'uvicorn', 'uwsgi')
    if any(s in argv0 for s in server_procs):
        return True
    # Also catch: python manage.py runserver / runserver_plus
    if 'manage.py' in ' '.join(sys.argv) and 'runserver' in ' '.join(sys.argv):
        return True
    return False


def _start_session_monitor():
    """Start a daemon thread that reconciles RUNNING session DB state with reality."""
    t = threading.Thread(target=_session_monitor_loop, name='session-monitor', daemon=True)
    t.start()
    logger.info('Session monitor started (pid=%s)', os.getpid())


def _session_monitor_loop():
    """
    Every 30 s: find all RUNNING sessions whose subprocess is no longer alive
    and mark them ERROR with the last error line from their session log.
    """
    import time
    # Wait for Django to finish booting before making DB queries
    time.sleep(15)

    while True:
        try:
            _reconcile_sessions()
        except Exception as exc:
            logger.error('Session monitor error: %s', exc)
        time.sleep(30)


def _reconcile_sessions():
    from django.db import close_old_connections
    from django.utils import timezone
    from .models import LiveTradingSession, SessionStatus

    # Close stale/broken DB connections before querying so Django
    # opens a fresh one. This recovers from the "connection already closed"
    # state that persists indefinitely without an explicit reconnect.
    close_old_connections()

    running = LiveTradingSession.objects.filter(status=SessionStatus.RUNNING)
    for session in running:
        if not session.pid:
            continue
        if _pid_alive(session.pid):
            continue

        # Process is dead — mark ERROR and capture last log error
        error_msg = _last_error_from_log(session) or f'Process {session.pid} exited unexpectedly'
        session.status = SessionStatus.ERROR
        session.error_message = error_msg
        session.stopped_at = timezone.now()
        session.save(update_fields=['status', 'error_message', 'stopped_at'])
        logger.warning(
            'Session %d (PID %d) is no longer running — marked ERROR: %s',
            session.id, session.pid, error_msg,
        )


def _pid_alive(pid: int) -> bool:
    """Return True only if the process exists AND is not a zombie."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False   # Process does not exist
    except PermissionError:
        pass  # Process exists but we lack permission to signal it — treat as alive
    except Exception:
        return False
    # os.kill(pid, 0) succeeds (or PermissionError) — check /proc for zombie state.
    try:
        status_path = f'/proc/{pid}/status'
        with open(status_path) as fh:
            for line in fh:
                if line.startswith('State:'):
                    return 'Z' not in line  # 'Z (zombie)' means dead
    except OSError:
        pass
    return True


def _last_error_from_log(session) -> str:
    """Return the last ERROR line from the tail of the session log (≤ 32 KB read)."""
    from pathlib import Path
    log_path = (
        Path(__file__).parent.parent
        / 'Live' / 'session_logs'
        / f'session_{session.pk}.log'
    )
    try:
        with open(log_path, 'rb') as fh:
            fh.seek(0, 2)  # seek to end
            size = fh.tell()
            fh.seek(max(0, size - 32_768))  # read last 32 KB only
            tail = fh.read().decode('utf-8', errors='replace')
        for line in reversed(tail.splitlines()):
            if 'ERROR' in line:
                return line.strip()[:300]
    except Exception:
        pass
    return ''
