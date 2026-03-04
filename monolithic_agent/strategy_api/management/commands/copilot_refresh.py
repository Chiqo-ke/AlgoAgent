"""
Non-interactive GitHub Copilot token refresh command.

Intended to be run by cron to silently refresh the stored OAuth token
before it expires — no human interaction required.

Usage:
    python manage.py copilot_refresh [--settings=...]

Exit codes:
    0  Token is valid (refreshed or was already valid)
    1  Refresh failed and token is expired / missing (action required)
"""

import sys
import logging
from django.core.management.base import BaseCommand
from django.utils.timezone import now

from algoagent_api.copilot_auth import get_auth_manager, CopilotAuthError
from strategy_api.models import CopilotAuth

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Non-interactively refresh the GitHub Copilot OAuth token. "
        "Safe to run from cron — exits 0 if a valid token exists, exits 1 if "
        "re-authentication via 'manage.py copilot_auth' is required."
    )

    def handle(self, *args, **options):
        auth_manager = get_auth_manager()

        # --- 1. Load token from DB ---
        token_data = CopilotAuth.get_latest_token()

        if not token_data:
            self.stderr.write(
                self.style.ERROR(
                    "No Copilot token found in database. "
                    "Run: python manage.py copilot_auth"
                )
            )
            sys.exit(1)

        expires_at = token_data.get("expires_at")
        refresh_token = token_data.get("refresh_token", "")

        # --- 2. Check if token is still well within its valid window ---
        if auth_manager.is_token_valid(token_data):
            time_left = expires_at - now()
            hours_left = time_left.total_seconds() / 3600
            self.stdout.write(
                self.style.SUCCESS(
                    f"Token is valid — expires in {hours_left:.1f}h. No refresh needed."
                )
            )
            sys.exit(0)

        # --- 3. Token is near expiry or expired — attempt silent refresh ---
        if not refresh_token:
            self.stderr.write(
                self.style.ERROR(
                    "Token is expired and no refresh token is stored. "
                    "Run: python manage.py copilot_auth"
                )
            )
            sys.exit(1)

        self.stdout.write("Token is near expiry — attempting silent refresh...")

        try:
            # refresh_access_token() now persists to DB automatically
            refreshed = auth_manager.refresh_access_token(refresh_token)
            new_expires_at = auth_manager._token_cache.get("expires_at")
            self.stdout.write(
                self.style.SUCCESS(
                    f"Token refreshed successfully. "
                    f"New expiry: {new_expires_at}"
                )
            )
            sys.exit(0)

        except CopilotAuthError as e:
            self.stderr.write(
                self.style.ERROR(
                    f"Silent refresh failed: {e}\n"
                    "Run: python manage.py copilot_auth"
                )
            )
            sys.exit(1)
