from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('strategy_api', '0009_latestbacktestresult_symbol_stats'),
    ]

    operations = [
        migrations.AddField(
            model_name='latestbacktestresult',
            name='profit_factor',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='latestbacktestresult',
            name='buy_hold_return_pct',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='latestbacktestresult',
            name='best_trade_pct',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='latestbacktestresult',
            name='worst_trade_pct',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=15, null=True),
        ),
    ]
