from django.apps import AppConfig


class LiveApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'live_api'
    verbose_name = 'Live Trading Data API'

    def ready(self) -> None:
        """
        Start the background data scheduler when Django is fully loaded.

        The RUN_MAIN check prevents double-start under Django's auto-reloader:
          - Reloader parent process:  RUN_MAIN is unset → we return early.
          - Actual server subprocess: RUN_MAIN='true' → we start the scheduler.

        In non-runserver environments (gunicorn, tests) RUN_MAIN is not set
        either; the scheduler will not auto-start there (use the activation
        endpoint or Celery-Beat for production scheduling).
        """
        import os

        if os.environ.get('RUN_MAIN') != 'true':
            return

        try:
            from live_api.scheduler import get_scheduler
            get_scheduler().start()
        except Exception as exc:
            import logging
            logging.getLogger('live_api').error(
                f'Failed to start LiveDataScheduler: {exc}', exc_info=True
            )
