from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading_sessions_api', '0002_brokercredential'),
    ]

    operations = [
        migrations.AddField(
            model_name='livetradingsession',
            name='sl_pips',
            field=models.FloatField(
                blank=True,
                null=True,
                help_text=(
                    'Fixed stop-loss distance in pips from entry price. '
                    'Used as the default SL whenever the bot strategy does not supply one. '
                    'Leave blank to trade without a stop-loss.'
                ),
            ),
        ),
        migrations.AddField(
            model_name='livetradingsession',
            name='tp_pips',
            field=models.FloatField(
                blank=True,
                null=True,
                help_text=(
                    'Fixed take-profit distance in pips from entry price. '
                    'Used as the default TP whenever the bot strategy does not supply one. '
                    'Leave blank to trade without a take-profit.'
                ),
            ),
        ),
    ]
