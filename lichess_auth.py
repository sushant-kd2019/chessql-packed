"""
Lichess OAuth2 PKCE Authentication Module
Handles the OAuth2 authorization flow with PKCE for Lichess API.

Lichess OAuth2 Notes:
- No app registration required! Use any client_id (e.g., "chessql-desktop")
- PKCE (Proof Key for Code Exchange) is used for security
- Redirect URI can be any localhost URL for desktop apps
- Users can also manually create tokens at: https://lichess.org/account/oauth/token
"""

import secrets
import hashlib
import base64
import urllib.parse
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
import httpx


# Lichess OAuth2 configuration
LICHESS_HOST = "https://lichess.org"
LICHESS_AUTHORIZE_URL = f"{LICHESS_HOST}/oauth"
LICHESS_TOKEN_URL = f"{LICHESS_HOST}/api/token"
LICHESS_ACCOUNT_URL = f"{LICHESS_HOST}/api/account"

# Default scopes for ChessQL
# - preference:read: Read user preferences
# - We don't need more scopes since game exports are public
DEFAULT_SCOPES = ["preference:read"]


@dataclass
class PKCEChallenge:
    """PKCE code verifier and challenge pair."""
    code_verifier: str
    code_challenge: str
    state: str


@dataclass
class AuthorizationResult:
    """Result of OAuth2 authorization."""
    access_token: str
    token_type: str
    expires_in: Optional[int]
    username: str


class LichessAuthError(Exception):
    """Custom exception for Lichess authentication errors."""
    pass


class LichessAuth:
    """Handles Lichess OAuth2 PKCE authentication flow."""
    
    def __init__(self, client_id: str, redirect_uri: str):
        """
        Initialize the Lichess OAuth2 handler.
        
        Args:
            client_id: Your Lichess OAuth2 application client ID
            redirect_uri: The callback URL registered with your app
        """
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        
        # Store pending authorizations (state -> PKCEChallenge)
        self._pending_auth: Dict[str, PKCEChallenge] = {}
    
    @staticmethod
    def generate_pkce_pair() -> PKCEChallenge:
        """
        Generate a PKCE code verifier and challenge.
        
        Returns:
            PKCEChallenge with verifier, challenge, and state
        """
        # Generate a random code verifier (43-128 chars, URL-safe)
        code_verifier = secrets.token_urlsafe(64)
        
        # Create code challenge using SHA256
        code_challenge_bytes = hashlib.sha256(code_verifier.encode('ascii')).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge_bytes).decode('ascii').rstrip('=')
        
        # Generate random state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        return PKCEChallenge(
            code_verifier=code_verifier,
            code_challenge=code_challenge,
            state=state
        )
    
    def start_authorization(self, scopes: Optional[list] = None) -> Tuple[str, str]:
        """
        Start the OAuth2 authorization flow.
        
        Args:
            scopes: List of OAuth scopes to request (default: DEFAULT_SCOPES)
        
        Returns:
            Tuple of (authorization_url, state)
        """
        if scopes is None:
            scopes = DEFAULT_SCOPES
        
        # Generate PKCE challenge
        pkce = self.generate_pkce_pair()
        
        # Store for later verification
        self._pending_auth[pkce.state] = pkce
        
        # Build authorization URL
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(scopes),
            'code_challenge_method': 'S256',
            'code_challenge': pkce.code_challenge,
            'state': pkce.state
        }
        
        auth_url = f"{LICHESS_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"
        
        return auth_url, pkce.state
    
    async def complete_authorization(self, code: str, state: str) -> AuthorizationResult:
        """
        Complete the OAuth2 authorization flow by exchanging the code for a token.
        
        Args:
            code: Authorization code from Lichess callback
            state: State parameter from callback (for CSRF verification)
        
        Returns:
            AuthorizationResult with access token and user info
        
        Raises:
            LichessAuthError: If authorization fails
        """
        # Verify state
        if state not in self._pending_auth:
            raise LichessAuthError("Invalid or expired state parameter")
        
        pkce = self._pending_auth.pop(state)
        
        # Exchange code for token
        async with httpx.AsyncClient() as client:
            try:
                token_response = await client.post(
                    LICHESS_TOKEN_URL,
                    data={
                        'grant_type': 'authorization_code',
                        'code': code,
                        'redirect_uri': self.redirect_uri,
                        'client_id': self.client_id,
                        'code_verifier': pkce.code_verifier
                    },
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                )
                
                if token_response.status_code != 200:
                    error_detail = token_response.text
                    raise LichessAuthError(f"Token exchange failed: {error_detail}")
                
                token_data = token_response.json()
                
                # Get user info to retrieve username
                account_response = await client.get(
                    LICHESS_ACCOUNT_URL,
                    headers={
                        'Authorization': f"Bearer {token_data['access_token']}"
                    }
                )
                
                if account_response.status_code != 200:
                    raise LichessAuthError("Failed to fetch account info")
                
                account_data = account_response.json()
                
                return AuthorizationResult(
                    access_token=token_data['access_token'],
                    token_type=token_data.get('token_type', 'Bearer'),
                    expires_in=token_data.get('expires_in'),
                    username=account_data['username']
                )
                
            except httpx.RequestError as e:
                raise LichessAuthError(f"Network error during authorization: {str(e)}")
    
    def clear_pending_auth(self, state: str) -> bool:
        """
        Clear a pending authorization (e.g., if user cancels).
        
        Args:
            state: The state parameter to clear
        
        Returns:
            True if cleared, False if not found
        """
        if state in self._pending_auth:
            del self._pending_auth[state]
            return True
        return False
    
    def has_pending_auth(self, state: str) -> bool:
        """Check if there's a pending authorization for the given state."""
        return state in self._pending_auth


async def verify_token(access_token: str) -> Optional[Dict[str, Any]]:
    """
    Verify an access token by fetching account info.
    
    Args:
        access_token: The token to verify
    
    Returns:
        Account info dict if valid, None if invalid
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                LICHESS_ACCOUNT_URL,
                headers={
                    'Authorization': f"Bearer {access_token}"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except httpx.RequestError:
            return None


async def revoke_token(access_token: str) -> bool:
    """
    Revoke an access token.
    
    Args:
        access_token: The token to revoke
    
    Returns:
        True if revoked successfully, False otherwise
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                LICHESS_TOKEN_URL,
                headers={
                    'Authorization': f"Bearer {access_token}"
                }
            )
            
            return response.status_code == 204
            
        except httpx.RequestError:
            return False


async def add_token_manually(access_token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and get account info for a manually created token.
    
    Users can create personal access tokens at: https://lichess.org/account/oauth/token
    This function verifies the token and returns the account info.
    
    Args:
        access_token: Personal access token from Lichess
    
    Returns:
        Account info dict with 'username' and other details if valid, None if invalid
    """
    return await verify_token(access_token)

