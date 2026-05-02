from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_admin_group(sender, **kwargs):
    """Ensure the AdminUser group exists after migrations."""
    from django.contrib.auth.models import Group
    Group.objects.get_or_create(name='AdminUser')


class AdminApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_api'
    verbose_name = 'Admin API'

    def ready(self):
        post_migrate.connect(create_admin_group, sender=self)
