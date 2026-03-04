"""
GitHub Copilot OAuth Authentication Module

Handles device flow authentication, token storage, and automatic refresh
for GitHub Copilot API integration.
"""

import os
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class CopilotAuthError(Exception):
    """Raised when Copilot authentication fails"""
    pass


class CopilotAuthManager:
    """
    Manages GitHub Copilot OAuth authentication using device flow.
    Authenticate once via `python manage.py copilot_auth`; the token is stored
    in the database and refreshed automatically.
    """

    # GitHub OAuth endpoints
    DEVICE_CODE_URL = "https://github.com/login/device/code"
    ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"

    # OpenCode's GitHub OAuth client ID (from opencode codebase)
    DEFAULT_CLIENT_ID = "Ov23li8tweQw6odWQebz"

    # Token expiration buffer (refresh 30 mins before expiry)
    REFRESH_BUFFER_SECONDS = 1800

    # Fallback TTL when GitHub does not return expires_in.
    # GitHub OAuth App tokens (gho_) never expire — using 1 year as a safe
    # sentinel so the refresh machinery stays dormant unless a real expiry
    # is provided (e.g. when migrated to a GitHub App with token expiry).
    OAUTH_APP_DEFAULT_TTL_SECONDS = 365 * 24 * 3600  # 1 year

    def __init__(self, client_id: Optional[str] = None):
        """
        Initialize Copilot auth manager.

        Args:
            client_id: GitHub OAuth client ID (defaults to OpenCode's ID)
        """
        self.client_id = client_id or os.getenv('GITHUB_COPILOT_CLIENT_ID', self.DEFAULT_CLIENT_ID)
        self._token_cache: Optional[Dict[str, Any]] = None
        
    def initiate_device_flow(self) -> Dict[str, str]:
        """
        Initiate OAuth device flow.
        
        Returns:
            Dict with device_code, user_code, verification_uri, interval
            
        Raises:
            CopilotAuthError: If device flow initiation fails
        """
        try:
            response = requests.post(
                self.DEVICE_CODE_URL,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                json={
                    "client_id": self.client_id,
                    "scope": "read:user"
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            logger.info(
                f"Device flow initiated. Visit {data['verification_uri']} "
                f"and enter code: {data['user_code']}"
            )
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"Failed to initiate device flow: {e}")
            raise CopilotAuthError(f"Device flow initiation failed: {e}")
    
    def poll_for_token(
        self, 
        device_code: str, 
        interval: int = 5, 
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Poll for access token after user authorization.
        
        Args:
            device_code: Device code from initiate_device_flow()
            interval: Polling interval in seconds
            timeout: Max time to wait for authorization (seconds)
            
        Returns:
            Dict with access_token, refresh_token, expires_in
            
        Raises:
            CopilotAuthError: If polling fails or times out
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.post(
                    self.ACCESS_TOKEN_URL,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    json={
                        "client_id": self.client_id,
                        "device_code": device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                    },
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    error = data["error"]
                    
                    if error == "authorization_pending":
                        # User hasn't authorized yet, keep polling
                        logger.debug("Authorization pending, continuing to poll...")
                        time.sleep(interval)
                        continue
                        
                    elif error == "slow_down":
                        # Increase polling interval
                        interval += 5
                        logger.debug(f"Slowing down polling to {interval}s")
                        time.sleep(interval)
                        continue
                        
                    elif error == "expired_token":
                        raise CopilotAuthError("Device code expired. Please restart authentication.")
                        
                    elif error == "access_denied":
                        raise CopilotAuthError("User denied authorization.")
                        
                    else:
                        raise CopilotAuthError(f"Unknown error: {error}")
                
                # Success!
                if "access_token" in data:
                    logger.info("Successfully obtained access token")
                    self._token_cache = {
                        "access_token": data["access_token"],
                        "refresh_token": data.get("refresh_token"),
                        "expires_at": datetime.now() + timedelta(seconds=data.get("expires_in", self.OAUTH_APP_DEFAULT_TTL_SECONDS)),
                        "obtained_at": datetime.now(),
                        "token_source": "oauth",
                        "scope": data.get("scope", "")
                    }
                    return data
                    
            except requests.RequestException as e:
                logger.error(f"Error polling for token: {e}")
                time.sleep(interval)
                continue
        
        raise CopilotAuthError(f"Authentication timed out after {timeout} seconds")
    
    def authenticate(self, timeout: int = 300) -> Dict[str, Any]:
        """
        Complete device flow authentication.

        Prints verification URL and user code, then waits for user to authorize.

        Args:
            timeout: Max time to wait for user authorization (seconds)

        Returns:
            Dict with token data including success status

        Raises:
            CopilotAuthError: If authentication fails
        """
        # Initiate device flow
        device_data = self.initiate_device_flow()
        
        print("\n" + "="*60)
        print("  GITHUB COPILOT AUTHENTICATION")
        print("="*60)
        print(f"\n1. Visit: {device_data['verification_uri']}")
        print(f"2. Enter code: {device_data['user_code']}")
        print(f"\nWaiting for authorization (timeout: {timeout}s)...")
        print("="*60 + "\n")
        
        # Poll for token
        token_data = self.poll_for_token(
            device_data['device_code'],
            device_data.get('interval', 5),
            timeout
        )
        
        # Save token to database if Django is available
        if token_data and "access_token" in token_data:
            try:
                from strategy_api.models import CopilotAuth
                from django.utils.timezone import now, make_aware
                
                # Calculate expiration datetime (timezone-aware)
                expires_at = now() + timedelta(seconds=token_data.get("expires_in", self.OAUTH_APP_DEFAULT_TTL_SECONDS))
                
                # Save to database
                CopilotAuth.save_token(
                    access_token=token_data["access_token"],
                    refresh_token=token_data.get("refresh_token", ""),
                    expires_at=expires_at,
                    github_user=token_data.get("user", ""),
                    client_id=self.client_id
                )
                
                logger.info("✓ Token saved to database")
                
                # Return enhanced response
                return {
                    "success": True,
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_at": expires_at.isoformat(),
                    "expires_in": token_data.get("expires_in", self.OAUTH_APP_DEFAULT_TTL_SECONDS),
                    "scope": token_data.get("scope", ""),
                }
                
            except Exception as e:
                logger.warning(f"Failed to save token to database: {e}")
                # Still return the token data even if DB save fails
                return {
                    "success": True,
                    "error": f"Token obtained but not saved to DB: {e}",
                    **token_data
                }
        
        return {"success": False, "error": "Unknown error"}

    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token from previous authentication
            
        Returns:
            Dict with new token data
            
        Raises:
            CopilotAuthError: If refresh fails
        """
        try:
            response = requests.post(
                self.ACCESS_TOKEN_URL,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                json={
                    "client_id": self.client_id,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                raise CopilotAuthError(f"Token refresh failed: {data['error']}")
            
            logger.info("Successfully refreshed access token")

            # Use timezone-aware expiry so it matches DB storage
            try:
                from django.utils.timezone import now as django_now
                expires_at = django_now() + timedelta(seconds=data.get("expires_in", self.OAUTH_APP_DEFAULT_TTL_SECONDS))
            except Exception:
                expires_at = datetime.now() + timedelta(seconds=data.get("expires_in", self.OAUTH_APP_DEFAULT_TTL_SECONDS))

            new_refresh_token = data.get("refresh_token", refresh_token)

            self._token_cache = {
                "access_token": data["access_token"],
                "refresh_token": new_refresh_token,
                "expires_at": expires_at,
                "obtained_at": datetime.now(),
                "token_source": "oauth",
                "scope": data.get("scope", "")
            }

            # Persist the refreshed token to the database so it survives restarts
            try:
                from strategy_api.models import CopilotAuth
                CopilotAuth.save_token(
                    access_token=data["access_token"],
                    refresh_token=new_refresh_token,
                    expires_at=expires_at,
                    client_id=self.client_id,
                )
                logger.info("Refreshed token persisted to database")
            except Exception as db_err:
                logger.warning(f"Refreshed token obtained but DB persist failed: {db_err}")

            return data

        except requests.RequestException as e:
            logger.error(f"Failed to refresh token: {e}")
            raise CopilotAuthError(f"Token refresh failed: {e}")
    
    def get_valid_token(self, stored_token_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Get a valid access token, refreshing if necessary.

        If no stored_token_data is supplied the method fetches the latest token
        from the database automatically, so callers don't have to do it themselves.

        Args:
            stored_token_data: Previously stored token data from database
                              (should include access_token, refresh_token, expires_at).
                              When omitted the DB is queried automatically.

        Returns:
            Valid access token

        Raises:
            CopilotAuthError: If token retrieval/refresh fails and no valid token exists
        """
        from django.utils.timezone import make_aware, now, is_aware

        # Use cached token if available and still valid
        if self._token_cache:
            expires_at = self._token_cache.get("expires_at")
            if expires_at:
                current_time = now() if is_aware(expires_at) else datetime.now()
                if current_time + timedelta(seconds=self.REFRESH_BUFFER_SECONDS) < expires_at:
                    return self._token_cache["access_token"]

        # Auto-load from DB if caller did not supply stored_token_data
        if stored_token_data is None:
            try:
                from strategy_api.models import CopilotAuth
                stored_token_data = CopilotAuth.get_latest_token()
            except Exception as e:
                logger.warning(f"Could not load token from database: {e}")

        # Use stored token data
        if stored_token_data:
            expires_at = stored_token_data.get("expires_at")

            if expires_at:
                if expires_at.tzinfo is None:
                    expires_at = make_aware(expires_at)
                # Token still valid within buffer window
                if now() + timedelta(seconds=self.REFRESH_BUFFER_SECONDS) < expires_at:
                    self._token_cache = stored_token_data
                    return stored_token_data["access_token"]

            # Token is within buffer or expired — try silent refresh
            if stored_token_data.get("refresh_token"):
                try:
                    refreshed = self.refresh_access_token(stored_token_data["refresh_token"])
                    # _token_cache and DB are both updated inside refresh_access_token()
                    return refreshed["access_token"]
                except CopilotAuthError:
                    logger.warning("Token refresh failed, will need to re-authenticate")

        # No valid token available
        raise CopilotAuthError(
            "No valid token available. Please run: python manage.py copilot_auth"
        )
    
    def is_token_valid(self, stored_token_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if stored token is still valid.

        Args:
            stored_token_data: Token data from database

        Returns:
            True if token is valid, False otherwise
        """
        if not stored_token_data:
            return False
        
        expires_at = stored_token_data.get("expires_at")
        if not expires_at:
            return False
        
        # Make datetime timezone-aware for comparison
        from django.utils.timezone import make_aware, now
        if expires_at.tzinfo is None:
            expires_at = make_aware(expires_at)
        
        # Check if token expires within buffer window
        return now() + timedelta(seconds=self.REFRESH_BUFFER_SECONDS) < expires_at


# Singleton instance for application-wide use
_auth_manager: Optional[CopilotAuthManager] = None


def get_auth_manager() -> CopilotAuthManager:
    """Get singleton CopilotAuthManager instance"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = CopilotAuthManager()
    return _auth_manager
