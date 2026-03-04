from django.apps import AppConfig


class BacktestApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backtest_api'

    def ready(self):
        # Auto-start Redis via Docker if not already running.
        # Non-fatal: if Docker is unavailable the server still starts.
        try:
            from redis_manager import ensure_redis_running
            ensure_redis_running()
        except Exception as exc:  # pylint: disable=broad-except
            import logging
            logging.getLogger(__name__).warning(
                "[Redis] Auto-start skipped: %s", exc
            )
