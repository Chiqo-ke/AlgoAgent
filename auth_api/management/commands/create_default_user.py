"""
Django Management Command: Create Default User
===============================================

Creates a default user for testing the AlgoAgent API.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from auth_api.models import UserProfile


class Command(BaseCommand):
    help = 'Create a default user for AlgoAgent API testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='algotrader',
            help='Username for the default user (default: algotrader)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='Trading@2024',
            help='Password for the default user (default: Trading@2024)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='algotrader@example.com',
            help='Email for the default user'
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User "{username}" already exists!')
            )
            user = User.objects.get(username=username)
            self.stdout.write(
                self.style.SUCCESS(f'You can login with username: {username}')
            )
            return

        # Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name='Algo',
            last_name='Trader'
        )

        # Update profile with default trading preferences
        profile = user.profile
        profile.default_risk_tolerance = 'moderate'
        profile.default_timeframe = '1d'
        profile.preferred_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        profile.trading_goals = 'Develop profitable algorithmic trading strategies with consistent returns and controlled risk.'
        profile.strategy_preferences = 'Prefer momentum and trend-following strategies. Interested in technical analysis and machine learning approaches.'
        profile.risk_parameters = {
            'max_position_size': 0.1,
            'max_drawdown': 0.15,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.05
        }
        profile.save()

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created default user!')
        )
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f'  Username: {username}')
        self.stdout.write(f'  Password: {password}')
        self.stdout.write(f'  Email:    {email}')
        self.stdout.write(f'{"="*60}\n')
        self.stdout.write(
            self.style.SUCCESS('You can now use these credentials to login to the API!')
        )
