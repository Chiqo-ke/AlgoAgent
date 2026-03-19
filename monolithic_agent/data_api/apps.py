from django.apps import AppConfig


class DataApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_api'

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(_seed_symbols_after_migrate, sender=self)


def _seed_symbols_after_migrate(sender, **kwargs):
    """Auto-seed symbols from the data warehouse after every migration run."""
    try:
        from django.core.management import call_command
        call_command("seed_symbols_from_warehouse", verbosity=0)
    except Exception:
        # Never crash the server due to seeding failure
        pass
