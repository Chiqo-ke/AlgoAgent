from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading_sessions_api', '0004_livetradingsession_data_bars'),
    ]

    operations = [
        migrations.AddField(
            model_name='livetradingsession',
            name='exit_mode',
            field=models.CharField(
                choices=[
                    ('bot', 'Bot Inbuilt'),
                    ('percentage', 'Percentage Risk'),
                    ('fixed_pips', 'Fixed Pips SL/TP'),
                ],
                default='percentage',
                help_text='Exit behavior mode: bot inbuilt, percentage-risk, or fixed pip SL/TP.',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='livetradingsession',
            name='risk_pct',
            field=models.DecimalField(decimal_places=2, default=2.0, max_digits=5),
        ),
    ]
