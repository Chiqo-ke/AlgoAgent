"""
GitHub Copilot Device Flow Authentication

Authenticates with GitHub Copilot API using OAuth device flow.

Usage:
    python scripts/github_device_auth_clean.py
"""

import os
import sys
import time
import requests
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# GitHub OAuth credentials (from OpenCode - same as monolithic system)
GITHUB_CLIENT_ID = "Ov23li8tweQw6odWQebz"
DEVICE_CODE_URL = "https://github.com/login/device/code"
ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
COPILOT_API_URL = "https://api.githubcopilot.com/chat/completions"
GITHUB_COPILOT_SCOPE = "read:user"


class GitHubCopilotAuth:
    """GitHub Copilot OAuth device flow authentication."""
    
    def __init__(self, client_id: str = GITHUB_CLIENT_ID):
        self.client_id = client_id
        self.device_code: Optional[str] = None
        self.user_code: Optional[str] = None
        self.verification_uri: Optional[str] = None
        self.expires_in: int = 900
        self.interval: int = 5
        self.access_token: Optional[str] = None
    
    def request_device_code(self) -> bool:
        """Request device code from GitHub."""
        print(f"\n🔐 Requesting device code...")
        
        try:
            response = requests.post(
                DEVICE_CODE_URL,
                headers={"Accept": "application/json"},
                json={
                    "client_id": self.client_id,
                    "scope": GITHUB_COPILOT_SCOPE
                },
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                return False
            
            data = response.json()
            
            self.device_code = data.get("device_code")
            self.user_code = data.get("user_code")
            self.verification_uri = data.get("verification_uri")
            self.expires_in = data.get("expires_in", 900)
            self.interval = data.get("interval", 5)
            
            return all([self.device_code, self.user_code, self.verification_uri])
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def display_instructions(self):
        """Display authentication instructions."""
        print("\n" + "="*60)
        print("🔑 GITHUB COPILOT AUTHENTICATION")
        print("="*60)
        print(f"\n👉 Visit: {self.verification_uri}")
        print(f"\n📝 Enter code: {self.user_code}")
        print(f"\n⏱️  Expires in: {self.expires_in // 60} minutes")
        print("\n" + "="*60)
    
    def poll_for_token(self) -> bool:
        """Poll for access token after user authorizes."""
        print("\n🔄 Waiting for authorization", end="", flush=True)
        
        start_time = time.time()
        interval = self.interval
        
        while time.time() - start_time < self.expires_in:
            time.sleep(interval)
            print(".", end="", flush=True)
            
            try:
                response = requests.post(
                    ACCESS_TOKEN_URL,
                    headers={"Accept": "application/json"},
                    json={
                        "client_id": self.client_id,
                        "device_code": self.device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                    },
                    timeout=10
                )
                
                data = response.json()
                
                if "access_token" in data:
                    print("\n✅ Authorization successful!")
                    self.access_token = data["access_token"]
                    return True
                
                error = data.get("error")
                
                if error == "slow_down":
                    interval += 5
                elif error == "authorization_pending":
                    continue
                elif error == "expired_token":
                    print("\n❌ Code expired")
                    return False
                elif error == "access_denied":
                    print("\n❌ Access denied")
                    return False
                else:
                    print(f"\n❌ Error: {error}")
                    return False
                    
            except Exception as e:
                print(f"\n❌ Error: {e}")
                return False
        
        print("\n❌ Timeout")
        return False
    
    def test_copilot_api(self) -> bool:
        """Test token with GitHub Copilot API."""
        print("\n🧪 Testing token with Copilot API...")
        
        try:
            response = requests.post(
                COPILOT_API_URL,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "User-Agent": "AlgoAgent-MultiAgent/1.0",
                    "X-Initiator": "user",
                    "Openai-Intent": "conversation-edits"
                },
                json={
                    "model": "claude-sonnet-4.5",
                    "messages": [{"role": "user", "content": "Say 'Hello from Copilot!'"}],
                    "stream": False,
                    "temperature": 0.5,
                    "max_tokens": 50
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print("✅ Token works!")
                print(f"   Response: {content}")
                return True
            else:
                print(f"❌ API error: {response.status_code}")
                print(f"   {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    
    def save_token(self, key_id: str = "github-copilot-01"):
        """Save token to .env file."""
        env_path = Path(__file__).parent.parent / ".env"
        
        if not env_path.exists():
            print(f"\n⚠️  .env not found: {env_path}")
            return False
        
        # Read .env
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Update or add key
        env_key = f"API_KEY_{key_id}"
        found = False
        new_lines = []
        
        for line in lines:
            if line.startswith(f"{env_key}="):
                new_lines.append(f"{env_key}={self.access_token}\n")
                found = True
            else:
                new_lines.append(line)
        
        if not found:
            new_lines.append(f"\n{env_key}={self.access_token}\n")
        
        # Write back
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
        
        print(f"\n✅ Token saved as {env_key}")
        return True


def main():
    """Run GitHub Copilot authentication."""
    print("\n" + "="*60)
    print("  GitHub Copilot Authentication")
    print("="*60)
    print("\nAuthenticating with GitHub Copilot API...\n")
    
    auth = GitHubCopilotAuth()
    
    # Step 1: Request device code
    if not auth.request_device_code():
        print("❌ Failed to get device code")
        return 1
    
    # Step 2: Show instructions
    auth.display_instructions()
    
    # Step 3: Poll for token
    if not auth.poll_for_token():
        print("❌ Failed to get token")
        return 1
    
    # Step 4: Test token
    if not auth.test_copilot_api():
        print("❌ Token doesn't work with Copilot API")
        print("\n💡 Make sure you have an active GitHub Copilot subscription")
        print("   Subscribe at: https://github.com/settings/copilot")
        return 1
    
    # Step 5: Save token
    print("\n" + "="*60)
    print("🎉 SUCCESS!")
    print("="*60)
    
    save = input("\n💾 Save token to .env? (y/n): ").strip().lower()
    if save == 'y':
        key_id = input("Key ID (default: github-copilot-01): ").strip()
        if not key_id:
            key_id = "github-copilot-01"
        
        auth.save_token(key_id)
        
        print("\n📝 Next steps:")
        print("   1. Verify keys.json has entry for", key_id)
        print("   2. Test with: python test_multi_provider.py")
    else:
        print(f"\nToken: {auth.access_token}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
