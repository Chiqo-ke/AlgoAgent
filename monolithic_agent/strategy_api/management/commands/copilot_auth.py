"""
Django management command to authenticate with GitHub Copilot

Usage:
    python manage.py copilot_auth

This will:
1. Initiate OAuth device flow via github.com/login/device
2. Display verification URL and one-time code
3. Wait for user authorization
4. Store the OAuth token in the database
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from algoagent_api.copilot_auth import get_auth_manager, CopilotAuthError
from strategy_api.models import CopilotAuth


class Command(BaseCommand):
    help = 'Authenticate with GitHub Copilot via OAuth device flow and store token'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=int,
            default=300,
            help='Authentication timeout in seconds (default: 300)'
        )
        parser.add_argument(
            '--check',
            action='store_true',
            help='Check if a valid OAuth token exists without authenticating'
        )

    def handle(self, *args, **options):
        timeout = options['timeout']
        check_only = options['check']
        auth_manager = get_auth_manager()

        if check_only:
            self._check_token(auth_manager)
            return
        
        self.stdout.write(self.style.WARNING(
            "\n" + "="*70 + "\n"
            "  GitHub Copilot Authentication\n"
            + "="*70
        ))
        
        try:
            # Check if valid token already exists
            existing_token = CopilotAuth.get_latest_token()
            if existing_token and auth_manager.is_token_valid(existing_token):
                self.stdout.write(self.style.SUCCESS(
                    "\n✓ Valid Copilot token already exists!"
                ))
                self.stdout.write(
                    f"  Expires: {existing_token['expires_at']}"
                )
                
                confirm = input("\nRe-authenticate anyway? (y/N): ")
                if confirm.lower() != 'y':
                    self.stdout.write(self.style.SUCCESS("\nUsing existing token."))
                    return
            
            # Perform authentication
            self.stdout.write("\nInitiating GitHub OAuth device flow...")
            token_data = auth_manager.authenticate(timeout=timeout)
            
            # Calculate expiration
            expires_at = timezone.now() + timedelta(seconds=token_data.get('expires_in', 28800))
            
            # Save to database
            CopilotAuth.save_token(
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token', ''),
                expires_at=expires_at,
                client_id=auth_manager.client_id
            )
            
            self.stdout.write(self.style.SUCCESS(
                "\n" + "="*70 + "\n"
                "  ✓ Authentication Successful!\n"
                + "="*70
            ))
            self.stdout.write(f"\nToken expires: {expires_at}")
            self.stdout.write(
                self.style.SUCCESS(
                    "\nYou can now use GitHub Copilot for strategy generation!"
                )
            )
            
        except CopilotAuthError as e:
            self.stdout.write(self.style.ERROR(f"\n✗ Authentication failed: {e}"))
            sys.exit(1)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n\nAuthentication cancelled by user."))
            sys.exit(0)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n✗ Unexpected error: {e}"))
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def _check_token(self, auth_manager):
        """Check if a valid OAuth token exists in the database."""
        try:
            token_data = CopilotAuth.get_latest_token()
            
            if not token_data:
                self.stdout.write(self.style.WARNING("No Copilot token found."))
                self.stdout.write("Run: python manage.py copilot_auth")
                return
            
            is_valid = auth_manager.is_token_valid(token_data)
            
            if is_valid:
                self.stdout.write(self.style.SUCCESS("✓ Valid Copilot token exists"))
                self.stdout.write(f"  Expires: {token_data['expires_at']}")
            else:
                self.stdout.write(self.style.WARNING("✗ Copilot token expired or invalid"))
                self.stdout.write("Run: python manage.py copilot_auth")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error checking token: {e}"))


