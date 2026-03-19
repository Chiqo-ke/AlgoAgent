"""
Session Manager
Spawns and manages live trader subprocesses (one per session).

Each subprocess runs live_trader.py with its own .env file containing
per-session MT5 credentials and trading config. The temp .env is deleted
when the session is stopped (not immediately after spawn, to avoid a race
where the child process has not yet loaded it).

MT5 SDK constraint: mt5.initialize() is global-state per Python process.
One subprocess = one MT5 terminal connection = one broker account.
"""
import os
import sys
import time
import uuid
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from trading_sessions_api.models import LiveTradingSession

logger = logging.getLogger(__name__)

# Paths
LIVE_DIR = Path(__file__).parent         # AlgoAgent/monolithic_agent/Live/
LIVE_TRADER = LIVE_DIR / 'live_trader.py'
TEMP_STRATEGIES_DIR = LIVE_DIR / 'temp_strategies'
KILL_SWITCHES_DIR = LIVE_DIR / 'kill_switches'
SESSION_LOGS_DIR = LIVE_DIR / 'session_logs'
VENV_PYTHON = Path(r'C:\Users\nyaga\Documents\.venv\Scripts\python.exe')


class SessionManager:
    """Spawns, tracks, and stops live trading subprocesses."""

    def start_session(self, session: 'LiveTradingSession') -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Write strategy code to a temp file, build a session .env, and spawn live_trader.py.

        Returns:
            (success: bool, pid: int | None, error: str | None)
        """
        TEMP_STRATEGIES_DIR.mkdir(parents=True, exist_ok=True)
        KILL_SWITCHES_DIR.mkdir(parents=True, exist_ok=True)
        SESSION_LOGS_DIR.mkdir(parents=True, exist_ok=True)

        session_id = str(session.pk)
        log_path = SESSION_LOGS_DIR / f'session_{session_id}.log'

        # 1. Write strategy code to temp file
        strategy_file = TEMP_STRATEGIES_DIR / f'strategy_{session_id}_{uuid.uuid4().hex[:8]}.py'
        try:
            strategy_code = session.strategy.strategy_code
            if not strategy_code:
                return False, None, 'Strategy has no code'
            strategy_file.write_text(strategy_code, encoding='utf-8')
        except Exception as e:
            return False, None, f'Failed to write strategy file: {e}'

        # 2. Determine kill switch path
        kill_switch_path = KILL_SWITCHES_DIR / f'STOP_{session_id}'

        # 3. Decrypt MT5 password
        try:
            mt5_password = session.get_mt5_password()
        except Exception as e:
            strategy_file.unlink(missing_ok=True)
            return False, None, f'Failed to decrypt MT5 password: {e}'

        # 4. Build env file contents — pass all config as environment variables
        symbols_str = ','.join(session.symbols) if session.symbols else 'EURUSD'
        env_vars = {
            # MT5 credentials
            'MT5_LOGIN': str(session.mt5_login),
            'MT5_PASSWORD': mt5_password,
            'MT5_SERVER': session.mt5_server,
            'MT5_PATH': session.mt5_terminal_path or '',
            # Trading config
            'DRY_RUN': 'true' if session.dry_run else 'false',
            'SYMBOLS': symbols_str,
            'TIMEFRAME': session.timeframe,
            'DEFAULT_RISK_PCT': str(float(session.risk_pct)),
            'MAGIC_NUMBER': str(session.magic_number),
            'STRATEGY_ID': f'session_{session_id}',
            # Kill switch
            'ENABLE_KILL_SWITCH': 'true',
            'KILL_SWITCH_FILE': str(kill_switch_path),
            # Misc
            'INTERVAL_SECONDS': '60',
        }

        # Write temp .env file
        env_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.env', delete=False, encoding='utf-8'
            ) as f:
                env_file = Path(f.name)
                for k, v in env_vars.items():
                    # Escape any double quotes in values
                    safe_v = str(v).replace('"', '\\"')
                    f.write(f'{k}="{safe_v}"\n')
        except Exception as e:
            strategy_file.unlink(missing_ok=True)
            return False, None, f'Failed to create env file: {e}'

        # 5. Determine Python executable
        python_exe = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

        # 6. Spawn subprocess — redirect stdout/stderr to per-session log file
        log_file_handle = None
        try:
            log_file_handle = open(log_path, 'a', encoding='utf-8', buffering=1)  # line-buffered
        except Exception as e:
            logger.warning(f'Session {session_id}: could not open log file {log_path}: {e}; falling back to DEVNULL')
            log_file_handle = None

        try:
            proc = subprocess.Popen(
                [python_exe, str(LIVE_TRADER), '--strategy', str(strategy_file), '--config', str(env_file)],
                cwd=str(LIVE_DIR),
                stdout=log_file_handle or subprocess.DEVNULL,
                stderr=subprocess.STDOUT if log_file_handle else subprocess.DEVNULL,
                # Detach from parent process so it survives Django worker restarts
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
            )
            pid = proc.pid
            logger.info(f'Session {session_id}: subprocess started (PID={pid})')
        except Exception as e:
            strategy_file.unlink(missing_ok=True)
            if env_file:
                env_file.unlink(missing_ok=True)
            return False, None, f'Failed to spawn subprocess: {e}'
        finally:
            # Close the log file handle in the parent process — the child has its own copy
            if log_file_handle:
                try:
                    log_file_handle.close()
                except Exception:
                    pass
            # NOTE: Do NOT delete the .env file here. The child process loads it via
            # dotenv.load_dotenv() shortly after startup; deleting it before the child
            # has read it causes a race where the child falls back to the global .env.
            # The file is deleted in stop_session() once the process has exited.

        # 7. Persist file paths on session for cleanup
        session.temp_file_path = str(strategy_file)
        session.kill_switch_path = str(kill_switch_path)
        session.log_file_path = str(log_path)
        # (caller must save the session after this returns)

        # 8. Delete the .env file after a short delay so the child process has time
        #    to load it via dotenv.load_dotenv() before it disappears.
        import threading
        def _deferred_delete(path: Path, delay: float = 10.0):
            time.sleep(delay)
            try:
                path.unlink(missing_ok=True)
                logger.debug(f'Session {session_id}: temp env file deleted')
            except Exception:
                pass
        if env_file:
            threading.Thread(target=_deferred_delete, args=(env_file,), daemon=True).start()

        return True, pid, None

    def stop_session(self, session: 'LiveTradingSession') -> bool:
        """
        Gracefully stop a running session by creating the kill-switch file.
        Falls back to process termination if the process is still alive after 30s.

        Returns:
            True if the process was confirmed stopped, False if uncertain.
        """
        # 1. Create kill switch file — LiveTrader polls for this
        if session.kill_switch_path:
            kill_path = Path(session.kill_switch_path)
            try:
                kill_path.touch()
                logger.info(f'Session {session.pk}: kill switch created at {kill_path}')
            except Exception as e:
                logger.warning(f'Session {session.pk}: could not create kill switch: {e}')

        if not session.pid:
            return True

        # 2. Wait up to 30s for graceful exit
        deadline = time.time() + 30
        while time.time() < deadline:
            if not self.is_running(session.pid):
                logger.info(f'Session {session.pk}: process {session.pid} exited gracefully')
                return True
            time.sleep(1)

        # 3. Force-terminate (Windows: taskkill; POSIX: SIGTERM)
        logger.warning(f'Session {session.pk}: process {session.pid} did not exit in 30s, forcing termination')
        try:
            if os.name == 'nt':
                subprocess.run(
                    ['taskkill', '/F', '/PID', str(session.pid)],
                    capture_output=True, timeout=10
                )
            else:
                import signal as _signal
                os.kill(session.pid, _signal.SIGTERM)
        except Exception as e:
            logger.error(f'Session {session.pk}: force-terminate failed: {e}')
            return False

        return not self.is_running(session.pid)

    def is_running(self, pid: int) -> bool:
        """Check whether a PID is still alive on the OS."""
        if not pid:
            return False
        try:
            if os.name == 'nt':
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                    capture_output=True, text=True, timeout=5
                )
                return str(pid) in result.stdout
            else:
                os.kill(pid, 0)  # Signal 0 = existence check only
                return True
        except (ProcessLookupError, PermissionError):
            return False
        except Exception:
            return False

    def cleanup_session_files(self, session: 'LiveTradingSession'):
        """Remove temp strategy file and kill switch file."""
        for path_attr in ('temp_file_path', 'kill_switch_path'):
            path_str = getattr(session, path_attr, '')
            if path_str:
                try:
                    Path(path_str).unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f'Session {session.pk}: cleanup failed for {path_str}: {e}')
