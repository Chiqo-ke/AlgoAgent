"""
Redis Auto-Start Manager
========================
Ensures a Redis server is available on localhost:6379.
Automatically starts a Docker container if Redis is not already running.

Called during Django startup via backtest_api.apps.BacktestApiConfig.ready().
"""
import logging
import socket
import subprocess
import time

logger = logging.getLogger(__name__)

REDIS_HOST = "localhost"
REDIS_PORT = 6379
CONTAINER_NAME = "algent_redis"


def _redis_is_running() -> bool:
    """Return True if something is already accepting connections on port 6379."""
    try:
        with socket.create_connection((REDIS_HOST, REDIS_PORT), timeout=2):
            return True
    except OSError:
        return False


def _docker_available() -> bool:
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _container_exists() -> bool:
    result = subprocess.run(
        ["docker", "ps", "-a",
         "--filter", f"name=^{CONTAINER_NAME}$",
         "--format", "{{.Names}}"],
        capture_output=True, text=True
    )
    return CONTAINER_NAME in result.stdout


def _container_is_running() -> bool:
    result = subprocess.run(
        ["docker", "ps",
         "--filter", f"name=^{CONTAINER_NAME}$",
         "--format", "{{.Names}}"],
        capture_output=True, text=True
    )
    return CONTAINER_NAME in result.stdout


def ensure_redis_running() -> bool:
    """
    Ensure Redis is available. Steps:
      1. If already running → done.
      2. If Docker available and container exists but stopped → start it.
      3. If Docker available and container missing → create & start it.
      4. If Docker unavailable → log warning, return False (non-fatal).

    Returns True if Redis is ready, False otherwise.
    """
    if _redis_is_running():
        logger.info("[Redis] Already running on %s:%s ✅", REDIS_HOST, REDIS_PORT)
        return True

    logger.info("[Redis] Not detected on port %s — attempting to start via Docker...", REDIS_PORT)

    if not _docker_available():
        logger.warning(
            "[Redis] Docker is not available. Redis features will be disabled. "
            "Install Docker Desktop or start Redis manually on port %s.", REDIS_PORT
        )
        return False

    try:
        if _container_exists():
            if not _container_is_running():
                logger.info("[Redis] Starting existing container '%s'...", CONTAINER_NAME)
                subprocess.run(
                    ["docker", "start", CONTAINER_NAME],
                    check=True, capture_output=True
                )
            else:
                logger.info("[Redis] Container '%s' is running but port not open yet — waiting...", CONTAINER_NAME)
        else:
            logger.info("[Redis] Creating container '%s'...", CONTAINER_NAME)
            subprocess.run(
                [
                    "docker", "run", "-d",
                    "--name", CONTAINER_NAME,
                    "--restart", "unless-stopped",
                    "-p", f"{REDIS_PORT}:6379",
                    "redis:latest"
                ],
                check=True, capture_output=True
            )

        # Wait up to 15 seconds for Redis to accept connections
        for attempt in range(1, 16):
            time.sleep(1)
            if _redis_is_running():
                logger.info("[Redis] ✅ Ready after %ds", attempt)
                return True

        logger.error(
            "[Redis] Container started but port %s never became available after 15s.", REDIS_PORT
        )
        return False

    except subprocess.CalledProcessError as exc:
        logger.error("[Redis] Docker command failed: %s", exc.stderr.strip() if exc.stderr else exc)
        return False
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("[Redis] Unexpected error: %s", exc)
        return False
