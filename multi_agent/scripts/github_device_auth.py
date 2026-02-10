"""
GitHub Device Flow Authentication Helper - DEBUG VERSION

This script helps debug GitHub OAuth device flow for GitHub Models/Copilot.

The issue: GitHub's public OAuth client may not support the 'models' scope.
This debug version will:
1. Try multiple scope configurations
2. Show exactly what scopes the token receives
3. Test the token against GitHub Models API
4. Provide detailed error information

Usage:
    python scripts/github_device_auth.py
"""

import os
import sys
import time
import requests
from pathlib import Path
from typing import Dict, Optional, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# GitHub OAuth credentials (from OpenCode codebase - same as monolithic system)
GITHUB_CLIENT_ID = "Ov23li8tweQw6odWQebz"  # OpenCode's GitHub OAuth client ID
DEVICE_CODE_URL = "https://github.com/login/device/code"
ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
POLL_INTERVAL = 5

# Scope for GitHub Copilot API access
GITHUB_COPILOT_SCOPE = "read:user"  # Standard scope that works with Copilot API


class GitHubDeviceAuthDebug:
    """Enhanced device auth with debugging capabilities."""
    
    def __init__(self, client_id: str = GITHUB_CLIENT_ID):
        self.client_id = client_id
        self.device_code: Optional[str] = None
        self.user_code: Optional[str] = None
        self.verification_uri: Optional[str] = None
        self.expires_in: int = 0
        self.interval: int = POLL_INTERVAL
        self.access_token: Optional[str] = None
        self.token_scopes: List[str] = []
    
    def request_device_code(self, scopes: str) -> bool:
        """Request device code with specific scopes."""
        print(f"\n🔐 Requesting device code with scopes: '{scopes}'")
        
        try:
            response = requests.post(
                DEVICE_CODE_URL,
                headers={"Accept": "application/json"},
                json={
                    "client_id": self.client_id,
                    "scope": scopes
                }
            )
            
            if response.status_code != 200:
                print(f"❌ Failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            
            self.device_code = data.get("device_code")
            self.user_code = data.get("user_code")
            self.verification_uri = data.get("verification_uri")
            self.expires_in = data.get("expires_in", 900)
            self.interval = data.get("interval", POLL_INTERVAL)
            
            return all([self.device_code, self.user_code, self.verification_uri])
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def display_instructions(self):
        """Display auth instructions."""
        print("\n" + "="*60)
        print("🔑 GITHUB DEVICE AUTHENTICATION")
        print("="*60)
        print(f"\n👉 Please visit: {self.verification_uri}")
        print(f"\n📝 Enter this code: {self.user_code}")
        print(f"\n⏱️  Code expires in {self.expires_in // 60} minutes")
        print("\n" + "="*60)
    
    def poll_for_token(self) -> bool:
        """Poll GitHub for access token."""
        print("\n🔄 Waiting for authorization...", end="", flush=True)
        
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
                    }
                )
                
                data = response.json()
                
                if "access_token" in data:
                    print("\n✅ Authorization successful!")
                    self.access_token = data["access_token"]
                    self.token_scopes = data.get("scope", "").split(",")
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
                    print("\n❌ Access denied by user")
                    return False
                else:
                    print(f"\n❌ Unexpected error: {error}")
                    return False
                    
            except Exception as e:
                print(f"\n❌ Polling error: {e}")
                return False
        
        print("\n❌ Timeout")
        return False
    
    def check_token_scopes(self):
        """Check what scopes the token actually has."""
        print("\n🔍 Checking token scopes...")
        
        try:
            response = requests.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json"
                }
            )
            
            # Get scopes from response headers
            scopes_header = response.headers.get("X-OAuth-Scopes", "")
            actual_scopes = [s.strip() for s in scopes_header.split(",") if s.strip()]
            
            print(f"📊 Token scopes: {', '.join(actual_scopes) if actual_scopes else '(none)'}")
            
            # Check if models scope is present
            if "models" in actual_scopes:
                print("✅ Token HAS 'models' scope!")
                return True
            else:
                print("❌ Token does NOT have 'models' scope")
                print(f"   Available scopes: {', '.join(actual_scopes)}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking scopes: {e}")
            return False
    
    def test_github_copilot_api(self):
        """Test if token works with GitHub Copilot API."""
        print("\n🧪 Testing token with GitHub Copilot API...")
        
        try:
            import requests
            
            response = requests.post(
                "https://api.githubcopilot.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "User-Agent": "AlgoAgent-MultiAgent/1.0",
                    "X-Initiator": "user",
                    "Openai-Intent": "conversation-edits"
                },
                json={
                    "model": "claude-sonnet-4.5",
                    "messages": [{"role": "user", "content": "Say 'Token works!'"}],
                    "stream": False,
                    "temperature": 0.5,
                    "max_tokens": 20
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print("✅ Token works with GitHub Copilot API!")
                print(f"   Response: {content}")
                return True
            else:
                print(f"❌ API returned {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
            
        except Exception as e:
            print(f"❌ Token test failed: {e}")
            return False
    
    def save_token(self, key_id: str = "github-models-01"):
        """Save token to .env file."""
        env_path = Path(__file__).parent.parent / ".env"
        
        if not env_path.exists():
            print(f"\n⚠️  No .env file found at {env_path}")
            return False
        
        # Read current .env
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
        
        print(f"\n✅ Token saved to .env as {env_key}")
        return True


def main():
    """Run device flow authentication for GitHub Copilot API."""
    print("\n" + "="*60)
    print("  GitHub Copilot Authentication")
    print("="*60)
    print("\nAuthenticating with GitHub Copilot API...\n")
    
    auth = GitHubDeviceAuthDebug()
    
    # Request device code with correct scope
    if not auth.request_device_code(GITHUB_COPILOT_SCOPE):
        print("❌ Failed to get device code")
        return 1
    
    # Show instructions
    auth.display_instructions()
    
    # Poll for token
    if not auth.poll_for_token():
        print("❌ Failed to get token")
        return 1
    
    # Check scopes
    auth.check_token_scopes()
    
    # Test with GitHub Copilot API
    works = auth.test_github_copilot_api()
    
    if works:
        print("\n" + "="*60)
        print("🎉 SUCCESS! Token works with GitHub Copilot API")
        print("="*60)
        
        # Ask to save
        save = input("\n💾 Save this token? (y/n): ").strip().lower()
        if save == 'y':
            key_id = input("Enter key ID (default: github-copilot-01): ").strip()
            if not key_id:
                key_id = "github-copilot-01"
            auth.save_token(key_id)
        
        return 0
    else:
        print("\n❌ Token verification failed")
        print("   Please check your GitHub Copilot subscription")
        return 1


if __name__ == "__main__":
    sys.exit(main())
        print("="*60)
        print(f"\n👉 Please visit: {self.verification_uri}")
        print(f"\n📝 Enter this code: {self.user_code}")
        print(f"\n⏱️  This code expires in {self.expires_in // 60} minutes")
        print("\n" + "="*60)
        print("\n🔄 Waiting for authorization...")
    
    def poll_for_token(self) -> Optional[str]:
        """
        Poll GitHub for access token after user authorizes.
        
        Returns:
            Access token if successful, None otherwise
        """
        start_time = time.time()
        
        while time.time() - start_time < self.expires_in:
            try:
                response = requests.post(
                    ACCESS_TOKEN_URL,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    json={
                        "client_id": self.client_id,
                        "device_code": self.device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                    }
                )
                
                data = response.json()
                
                # Check for errors
                error = data.get("error")
                
                if error == "authorization_pending":
                    # Still waiting for user to authorize
                    print(".", end="", flush=True)
                    time.sleep(self.interval)
                    continue
                
                elif error == "slow_down":
                    # Increase polling interval
                    self.interval += 5
                    print("\n⚠️  Slowing down polling rate...")
                    time.sleep(self.interval)
                    continue
                
                elif error == "expired_token":
                    print("\n❌ Device code expired. Please try again.")
                    return None
                
                elif error == "access_denied":
                    print("\n❌ Authorization denied by user.")
                    return None
                
                elif error:
                    print(f"\n❌ Error: {error}")
                    return None
                
                # Success!
                access_token = data.get("access_token")
                if access_token:
                    print("\n✅ Authorization successful!")
                    return access_token
                
            except Exception as e:
                print(f"\n❌ Error polling for token: {e}")
                return None
        
        print("\n❌ Timeout waiting for authorization")
        return None
    
    def authenticate(self) -> Optional[str]:
        """
        Run the complete device flow authentication.
        
        Returns:
            Access token if successful, None otherwise
        """
        # Step 1: Request device code
        if not self.request_device_code():
            return None
        
        # Step 2: Display instructions
        self.display_instructions()
        
        # Step 3: Poll for token
        token = self.poll_for_token()
        
        return token


def save_token_to_env(token: str, key_id: str = "github-models-01") -> bool:
    """
    Save access token to .env file.
    
    Args:
        token: GitHub access token
        key_id: Key ID to use in .env (default: github-models-01)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        env_path = Path(__file__).parent.parent / ".env"
        env_key = f"API_KEY_{key_id}"
        
        # Read existing .env content
        env_lines = []
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_lines = f.readlines()
        
        # Check if key already exists
        key_exists = False
        for i, line in enumerate(env_lines):
            if line.startswith(f"{env_key}="):
                env_lines[i] = f"{env_key}={token}\n"
                key_exists = True
                break
        
        # Add new key if it doesn't exist
        if not key_exists:
            # Find GitHub Models section or create it
            github_section_idx = None
            for i, line in enumerate(env_lines):
                if "GITHUB MODELS" in line or "GitHub Models" in line:
                    github_section_idx = i
                    break
            
            if github_section_idx is not None:
                # Insert after GitHub Models section header
                insert_idx = github_section_idx + 1
                while insert_idx < len(env_lines) and env_lines[insert_idx].strip().startswith("#"):
                    insert_idx += 1
                env_lines.insert(insert_idx, f"{env_key}={token}\n")
            else:
                # Append to end
                if env_lines and not env_lines[-1].endswith('\n'):
                    env_lines.append('\n')
                env_lines.append(f"\n# GitHub Models (Device Flow)\n")
                env_lines.append(f"{env_key}={token}\n")
        
        # Write back to .env
        with open(env_path, 'w') as f:
            f.writelines(env_lines)
        
        print(f"\n✅ Token saved to .env as {env_key}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error saving token to .env: {e}")
        return False


def verify_token(token: str) -> bool:
    """
    Verify that the token works with GitHub Models API.
    
    Args:
        token: GitHub access token
    
    Returns:
        True if token is valid, False otherwise
    """
    try:
        print("\n🔍 Verifying token...")
        
        # Test with a simple API call
        response = requests.post(
            "https://models.inference.ai.azure.com/chat/completions",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "user", "content": "Say 'token verified' if you can see this"}
                ],
                "max_tokens": 10
            }
        )
        
        if response.status_code == 200:
            print("✅ Token verified! GitHub Models API is accessible.")
            return True
        else:
            print(f"⚠️  Token saved but verification failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"⚠️  Token saved but verification failed: {e}")
        return False


def main():
    """Main entry point for device authentication."""
    print("\n" + "="*60)
    print("  GitHub Models - Device Flow Authentication")
    print("="*60)
    print("\nThis script will help you authenticate with GitHub Models")
    print("using device flow (no manual PAT creation needed).")
    
    # Check if .env exists
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print("\n⚠️  No .env file found. Creating from .env.example...")
        example_path = env_path.parent / ".env.example"
        if example_path.exists():
            import shutil
            shutil.copy(example_path, env_path)
            print("✅ Created .env file")
        else:
            print("❌ .env.example not found. Please create .env manually.")
            return
    
    # Run device authentication
    auth = GitHubDeviceAuth()
    token = auth.authenticate()
    
    if not token:
        print("\n❌ Authentication failed. Please try again.")
        return
    
    # Prompt for key ID
    print("\n" + "="*60)
    key_id = input("Enter a key ID for this token (default: github-models-01): ").strip()
    if not key_id:
        key_id = "github-models-01"
    
    # Save token
    if save_token_to_env(token, key_id):
        # Verify token
        verify_token(token)
        
        print("\n" + "="*60)
        print("🎉 SETUP COMPLETE!")
        print("="*60)
        print(f"\n✅ Token saved as API_KEY_{key_id}")
        print("\n📝 Next steps:")
        print("   1. Update your keys.json with this configuration:")
        print(f'''
   {{
     "key_id": "{key_id}",
     "model_name": "gpt-4o-mini",
     "provider": "github-models",
     "rpm": 15,
     "tpm": 150000,
     "rpd": 150,
     "active": true,
     "tags": {{"workload": "medium", "priority": 1}}
   }}
        ''')
        print("   2. Restart Redis if needed")
        print("   3. Test with: python -c 'from llm.router import RequestRouter; ...'")
        print("\n" + "="*60)
    else:
        print("\n❌ Failed to save token. Please add it manually to .env:")
        print(f"\nAPI_KEY_{key_id}={token}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Authentication cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
