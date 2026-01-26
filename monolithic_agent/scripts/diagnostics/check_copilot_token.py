"""
Check existing Copilot token in database
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')

import django
django.setup()

from strategy_api.models import CopilotAuth
from django.utils import timezone

def main():
    print("\n🔍 Checking Copilot Token Database")
    print("=" * 60)
    
    # Get all tokens
    all_tokens = CopilotAuth.objects.all().order_by('-updated_at')
    
    if not all_tokens.exists():
        print("\n❌ No tokens found in database")
        print("\nYou need to authenticate. Try one of these options:")
        print("1. Check your network connection and retry authentication")
        print("2. Use a VPN if GitHub is blocked")
        print("3. Temporarily disable firewall and retry")
        return
    
    print(f"\n📊 Found {all_tokens.count()} token(s) in database:\n")
    
    for idx, token in enumerate(all_tokens, 1):
        print(f"Token #{idx}:")
        print(f"  Created: {token.created_at}")
        print(f"  Updated: {token.updated_at}")
        print(f"  Expires: {token.expires_at}")
        
        # Check if expired
        now = timezone.now()
        if token.expires_at > now:
            time_left = token.expires_at - now
            hours_left = time_left.total_seconds() / 3600
            print(f"  Status: ✅ VALID (expires in {hours_left:.1f} hours)")
            
            # Check if token works
            print(f"\n  Access Token: {token.access_token[:20]}...{token.access_token[-10:]}")
            print(f"  Refresh Token: {token.refresh_token[:20] if token.refresh_token else 'N/A'}...")
            print(f"  GitHub User: {token.github_user or 'N/A'}")
            
        else:
            expired_ago = now - token.expires_at
            hours_ago = expired_ago.total_seconds() / 3600
            print(f"  Status: ⚠️  EXPIRED ({hours_ago:.1f} hours ago)")
            
            # Check if we can refresh
            if token.refresh_token:
                print(f"  Refresh Token: Available - can be refreshed")
            else:
                print(f"  Refresh Token: Not available - need new authentication")
        
        print()
    
    # Try to get latest valid token
    latest = CopilotAuth.get_latest_token()
    if latest:
        expires_at = latest['expires_at']
        if timezone.is_aware(expires_at):
            expires_at_naive = expires_at
        else:
            expires_at_naive = timezone.make_aware(expires_at)
        
        if expires_at_naive > timezone.now():
            print("✅ Latest token is still VALID!")
            print("   The validation endpoint should work now.")
        else:
            print("⚠️  Latest token is EXPIRED")
            if latest.get('refresh_token'):
                print("   Attempting to refresh token...")
                
                try:
                    from algoagent_api.copilot_auth import get_auth_manager
                    manager = get_auth_manager()
                    
                    # Try to refresh
                    new_token_data = manager.refresh_access_token(latest['refresh_token'])
                    
                    # Save refreshed token
                    from datetime import timedelta
                    expires_at_new = timezone.now() + timedelta(seconds=new_token_data.get('expires_in', 28800))
                    
                    CopilotAuth.save_token(
                        access_token=new_token_data['access_token'],
                        refresh_token=new_token_data.get('refresh_token', latest['refresh_token']),
                        expires_at=expires_at_new
                    )
                    
                    print("   ✅ Token refreshed successfully!")
                    
                except Exception as e:
                    print(f"   ❌ Refresh failed: {e}")
                    print("   Network issue - you'll need to wait or try with VPN")
            else:
                print("   No refresh token available - need new authentication")

if __name__ == "__main__":
    main()
