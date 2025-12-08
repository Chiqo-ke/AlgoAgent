# Bot Performance Tracking - Migration
# Generated manually

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('strategy_api', '0001_initial'),  # Adjust to your latest migration
        ('backtest_api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BotPerformance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('verification_status', models.CharField(
                    choices=[
                        ('unverified', 'Unverified'),
                        ('testing', 'Under Testing'),
                        ('verified', 'Verified - Makes Trades'),
                        ('failed', 'Failed - No Trades'),
                    ],
                    default='unverified',
                    max_length=20
                )),
                ('is_verified', models.BooleanField(default=False, help_text='True if bot successfully makes trades')),
                ('total_trades', models.IntegerField(default=0)),
                ('entry_trades', models.IntegerField(default=0)),
                ('exit_trades', models.IntegerField(default=0)),
                ('win_rate', models.DecimalField(blank=True, decimal_places=2, help_text='Win rate percentage', max_digits=5, null=True)),
                ('total_return', models.DecimalField(blank=True, decimal_places=6, help_text='Total return percentage', max_digits=15, null=True)),
                ('sharpe_ratio', models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True)),
                ('max_drawdown', models.DecimalField(blank=True, decimal_places=6, max_digits=15, null=True)),
                ('symbol_tested', models.CharField(blank=True, max_length=20)),
                ('timeframe_tested', models.CharField(blank=True, max_length=10)),
                ('test_period_start', models.DateField(blank=True, null=True)),
                ('test_period_end', models.DateField(blank=True, null=True)),
                ('trades_threshold', models.IntegerField(default=2, help_text='Minimum trades required for verification')),
                ('verification_notes', models.TextField(blank=True, help_text='Automated verification notes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_test_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('strategy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='performance_history', to='strategy_api.strategy')),
            ],
            options={
                'verbose_name': 'Bot Performance',
                'verbose_name_plural': 'Bot Performances',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BotTestRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('passed', models.BooleanField(default=False)),
                ('trades_made', models.IntegerField(default=0)),
                ('execution_errors', models.TextField(blank=True)),
                ('tested_at', models.DateTimeField(auto_now_add=True)),
                ('backtest_run', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='bot_test', to='backtest_api.backtestrun')),
                ('performance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_runs', to='strategy_api.botperformance')),
            ],
            options={
                'ordering': ['-tested_at'],
            },
        ),
    ]
