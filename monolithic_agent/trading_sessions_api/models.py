"""
Models for Live Trading Sessions
"""
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from cryptography.fernet import Fernet
import base64
import os


def _get_fernet():
    """Get Fernet cipher using the FERNET_KEY from settings/env."""
    key = getattr(settings, 'FERNET_KEY', None) or os.getenv('FERNET_KEY')
    if not key:
        raise RuntimeError(
            "FERNET_KEY is not configured. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\" "
            "and add it to your .env as FERNET_KEY=<value>"
        )
    # Accept both bytes and str
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


class SessionStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    RUNNING = 'RUNNING', 'Running'
    STOPPED = 'STOPPED', 'Stopped'
    ERROR = 'ERROR', 'Error'


class BrokerCredential(models.Model):
    """
    Saved MT5 broker credentials for a user.

    Passwords are stored encrypted with Fernet at rest.
    Users can save one or more credential sets and reference them
    by ID when starting a live session.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='broker_credentials')
    label = models.CharField(max_length=100, help_text='Human-friendly name e.g. "FBS Demo"')
    mt5_login = models.IntegerField(help_text='Broker account number')
    mt5_password_encrypted = models.TextField(help_text='Fernet-encrypted broker password')
    mt5_server = models.CharField(max_length=100, help_text='e.g. "FBS-Demo"')
    mt5_terminal_path = models.CharField(
        max_length=500, blank=True,
        help_text='Optional: absolute path to terminal64.exe'
    )
    is_default = models.BooleanField(default=False, help_text='Use this credential when none is specified')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']
        unique_together = [('user', 'label')]

    def __str__(self):
        return f"{self.user.username} / {self.label} ({self.mt5_server}:{self.mt5_login})"

    def set_password(self, plaintext: str):
        """Encrypt and store the MT5 password."""
        f = _get_fernet()
        self.mt5_password_encrypted = f.encrypt(plaintext.encode()).decode()

    def get_password(self) -> str:
        """Decrypt and return the MT5 password. Call only at subprocess spawn time."""
        f = _get_fernet()
        return f.decrypt(self.mt5_password_encrypted.encode()).decode()


class LiveTradingSession(models.Model):
    """
    Represents a live trading session for a user's strategy.

    Each session runs as an isolated subprocess (one MT5 terminal per process).
    MT5 credentials are stored encrypted at rest and decrypted only at spawn time.
    """
    # Strategy link
    strategy = models.ForeignKey(
        'strategy_api.Strategy',
        on_delete=models.CASCADE,
        related_name='live_sessions'
    )

    # Session state
    status = models.CharField(
        max_length=20,
        choices=SessionStatus.choices,
        default=SessionStatus.PENDING
    )
    pid = models.IntegerField(null=True, blank=True, help_text="OS process ID of the live trader subprocess")
    temp_file_path = models.CharField(max_length=500, blank=True, help_text="Path to temp strategy .py file")
    kill_switch_path = models.CharField(max_length=500, blank=True, help_text="Path to kill-switch file for graceful stop")

    # Trading config
    symbols = models.JSONField(default=list, help_text='e.g. ["EURUSD", "GBPUSD"]')
    timeframe = models.CharField(max_length=10, default='1h', help_text='e.g. "1h", "1d", "5m"')
    dry_run = models.BooleanField(
        default=True,
        help_text="When True, connection is established but NO real orders are sent. Always start with True."
    )
    risk_pct = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    magic_number = models.IntegerField(default=234567)
    sl_pips = models.FloatField(
        null=True, blank=True,
        help_text=(
            'Fixed stop-loss distance in pips from entry price. '
            'Used as the default SL whenever the bot strategy does not supply one. '
            'Leave blank to trade without a stop-loss.'
        )
    )
    tp_pips = models.FloatField(
        null=True, blank=True,
        help_text=(
            'Fixed take-profit distance in pips from entry price. '
            'Used as the default TP whenever the bot strategy does not supply one. '
            'Leave blank to trade without a take-profit.'
        )
    )
    data_bars = models.IntegerField(
        null=True, blank=True,
        default=5000,
        help_text=(
            'Number of historical bars fetched and used for indicator warm-up '
            '(ATR, EMA, RSI, etc.). Higher values reduce NaN signals. '
            'Max 5000 (tvDatafeed limit). Defaults to 5000.'
        )
    )

    # Per-session MT5 credentials
    mt5_login = models.IntegerField(help_text="Broker account number")
    mt5_password_encrypted = models.TextField(help_text="Fernet-encrypted broker password")
    mt5_server = models.CharField(max_length=100, help_text='e.g. "FBS-Demo"')
    mt5_terminal_path = models.CharField(
        max_length=500, blank=True,
        help_text="Optional: absolute path to terminal64.exe for this user's MT5 installation"
    )

    # Ownership & timestamps
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trading_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    stopped_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Session {self.pk} – {self.strategy} [{self.status}]"

    # ------------------------------------------------------------------
    # Credential helpers
    # ------------------------------------------------------------------

    def set_mt5_password(self, plaintext_password: str):
        """Encrypt and store the MT5 password."""
        f = _get_fernet()
        self.mt5_password_encrypted = f.encrypt(plaintext_password.encode()).decode()

    def get_mt5_password(self) -> str:
        """Decrypt and return the MT5 password. Call only at subprocess spawn."""
        if not self.mt5_password_encrypted:
            return ''
        f = _get_fernet()
        return f.decrypt(self.mt5_password_encrypted.encode()).decode()
