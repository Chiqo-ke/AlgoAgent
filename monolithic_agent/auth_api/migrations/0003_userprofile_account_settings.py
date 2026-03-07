from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_api', '0002_chatsession_strategy_template_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='default_currency',
            field=models.CharField(
                choices=[('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP'), ('JPY', 'JPY')],
                default='USD',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='default_simulation_mode',
            field=models.CharField(
                choices=[('money', 'Money'), ('pips', 'Pips')],
                default='money',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='notification_email',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='notification_push',
            field=models.BooleanField(default=False),
        ),
    ]
