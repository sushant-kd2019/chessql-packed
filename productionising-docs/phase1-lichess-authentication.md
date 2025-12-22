# Phase 1: Lichess Authentication Implementation

This document covers the implementation details of Lichess OAuth2 PKCE authentication for ChessQL.

## Overview

We implemented a secure OAuth2 authentication system that allows users to link their Lichess accounts to ChessQL. The implementation supports two methods:

1. **OAuth2 PKCE Flow** - Browser-based authorization
2. **Manual Token Entry** - Direct token input for power users

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   ChessQL UI    │────▶│  FastAPI Server  │────▶│  Lichess API    │
│   (Electron)    │◀────│   (localhost)    │◀────│  (lichess.org)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  SQLite Database │
                        │  (accounts table)│
                        └──────────────────┘
```

## Files Created/Modified

### New Files

| File | Purpose |
|------|---------|
| `accounts.py` | Account management (CRUD operations) |
| `lichess_auth.py` | OAuth2 PKCE flow implementation |

### Modified Files

| File | Changes |
|------|---------|
| `database.py` | Added `accounts` table schema |
| `server.py` | Added auth endpoints and CORS middleware |
| `requirements.txt` | Added HTTP/2 support for httpx |

---

## Database Schema

### Accounts Table

```sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,      -- Lichess username (lowercase)
    access_token TEXT NOT NULL,          -- OAuth2 access token
    token_expires_at INTEGER,            -- Unix timestamp (NULL = never expires)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sync_at TIMESTAMP,              -- Last game sync time
    last_game_at INTEGER,                -- Timestamp of most recent game
    games_count INTEGER DEFAULT 0        -- Total games synced
);

CREATE INDEX idx_accounts_username ON accounts(username);
```

### Games Table Update

Added `account_id` foreign key to associate games with accounts:

```sql
ALTER TABLE games ADD COLUMN account_id INTEGER REFERENCES accounts(id);
```

---

## Module: `accounts.py`

### Class: `AccountManager`

Manages Lichess accounts in SQLite database.

#### Constructor

```python
def __init__(self, db_path: str = "chess_games.db"):
    self.db_path = db_path
    self.init_accounts_table()
```

#### Key Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `add_account(username, access_token, token_expires_at)` | Add or update account | `int` (account ID) |
| `get_account(username)` | Get account by username | `Dict` or `None` |
| `list_accounts()` | List all accounts (no tokens) | `List[Dict]` |
| `remove_account(username)` | Delete account | `bool` |
| `is_token_valid(username)` | Check token expiry | `bool` |
| `get_access_token(username)` | Get valid token | `str` or `None` |
| `update_sync_status(...)` | Update sync metadata | `None` |

#### Example Usage

```python
from accounts import AccountManager

manager = AccountManager("chess_games.db")

# Add account
account_id = manager.add_account(
    username="lecorvus",
    access_token="lip_xxxxx",
    token_expires_at=None  # Personal tokens don't expire
)

# Check if token is valid
if manager.is_token_valid("lecorvus"):
    token = manager.get_access_token("lecorvus")
    
# List all accounts
accounts = manager.list_accounts()
# Returns: [{"id": 1, "username": "lecorvus", "games_count": 0, ...}]

# Remove account
manager.remove_account("lecorvus")
```

---

## Module: `lichess_auth.py`

### OAuth2 PKCE Flow

PKCE (Proof Key for Code Exchange) provides secure authorization for public clients (desktop apps).

#### Constants

```python
LICHESS_HOST = "https://lichess.org"
LICHESS_AUTHORIZE_URL = f"{LICHESS_HOST}/oauth"
LICHESS_TOKEN_URL = f"{LICHESS_HOST}/api/token"
LICHESS_ACCOUNT_URL = f"{LICHESS_HOST}/api/account"

DEFAULT_SCOPES = ["preference:read"]
```

#### Data Classes

```python
@dataclass
class PKCEChallenge:
    code_verifier: str   # Random 64-char URL-safe string
    code_challenge: str  # SHA256 hash of verifier (base64url)
    state: str           # CSRF protection token

@dataclass
class AuthorizationResult:
    access_token: str
    token_type: str
    expires_in: Optional[int]
    username: str
```

### Class: `LichessAuth`

Handles the OAuth2 PKCE authorization flow.

#### Constructor

```python
def __init__(self, client_id: str, redirect_uri: str):
    self.client_id = client_id
    self.redirect_uri = redirect_uri
    self._pending_auth: Dict[str, PKCEChallenge] = {}
```

#### PKCE Generation

```python
@staticmethod
def generate_pkce_pair() -> PKCEChallenge:
    # Generate random verifier (64 bytes, URL-safe)
    code_verifier = secrets.token_urlsafe(64)
    
    # Create SHA256 challenge
    code_challenge_bytes = hashlib.sha256(
        code_verifier.encode('ascii')
    ).digest()
    code_challenge = base64.urlsafe_b64encode(
        code_challenge_bytes
    ).decode('ascii').rstrip('=')
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    return PKCEChallenge(code_verifier, code_challenge, state)
```

#### Start Authorization

```python
def start_authorization(self, scopes: Optional[list] = None) -> Tuple[str, str]:
    """
    Returns: (authorization_url, state)
    """
    pkce = self.generate_pkce_pair()
    self._pending_auth[pkce.state] = pkce  # Store for callback
    
    params = {
        'response_type': 'code',
        'client_id': self.client_id,
        'redirect_uri': self.redirect_uri,
        'scope': ' '.join(scopes or DEFAULT_SCOPES),
        'code_challenge_method': 'S256',
        'code_challenge': pkce.code_challenge,
        'state': pkce.state
    }
    
    auth_url = f"{LICHESS_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"
    return auth_url, pkce.state
```

#### Complete Authorization

```python
async def complete_authorization(self, code: str, state: str) -> AuthorizationResult:
    # Verify state (CSRF protection)
    if state not in self._pending_auth:
        raise LichessAuthError("Invalid state")
    
    pkce = self._pending_auth.pop(state)
    
    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_response = await client.post(
            LICHESS_TOKEN_URL,
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.redirect_uri,
                'client_id': self.client_id,
                'code_verifier': pkce.code_verifier
            }
        )
        
        token_data = token_response.json()
        
        # Get username from account endpoint
        account_response = await client.get(
            LICHESS_ACCOUNT_URL,
            headers={'Authorization': f"Bearer {token_data['access_token']}"}
        )
        
        return AuthorizationResult(
            access_token=token_data['access_token'],
            token_type=token_data.get('token_type', 'Bearer'),
            expires_in=token_data.get('expires_in'),
            username=account_response.json()['username']
        )
```

### Helper Functions

```python
async def verify_token(access_token: str) -> Optional[Dict[str, Any]]:
    """Verify token by fetching account info."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            LICHESS_ACCOUNT_URL,
            headers={'Authorization': f"Bearer {access_token}"}
        )
        return response.json() if response.status_code == 200 else None

async def revoke_token(access_token: str) -> bool:
    """Revoke token on Lichess."""
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            LICHESS_TOKEN_URL,
            headers={'Authorization': f"Bearer {access_token}"}
        )
        return response.status_code == 204

async def add_token_manually(access_token: str) -> Optional[Dict[str, Any]]:
    """Verify a manually-created personal token."""
    return await verify_token(access_token)
```

---

## API Endpoints

### Authentication Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/lichess/start` | Start OAuth flow |
| POST | `/auth/lichess/callback` | Complete OAuth (programmatic) |
| GET | `/auth/lichess/callback` | OAuth callback (browser redirect) |
| POST | `/auth/lichess/token` | Add manual token |
| GET | `/auth/accounts` | List all accounts |
| DELETE | `/auth/accounts/{username}` | Remove account |
| GET | `/auth/accounts/{username}/verify` | Verify token |

### Request/Response Models

```python
class AuthStartResponse(BaseModel):
    auth_url: str  # URL to open in browser
    state: str     # State for verification

class AuthCallbackRequest(BaseModel):
    code: str      # Authorization code from Lichess
    state: str     # State for CSRF verification

class AuthCallbackResponse(BaseModel):
    success: bool
    username: Optional[str] = None
    error: Optional[str] = None

class ManualTokenRequest(BaseModel):
    access_token: str

class AccountResponse(BaseModel):
    id: int
    username: str
    token_expires_at: Optional[int] = None
    created_at: str
    last_sync_at: Optional[str] = None
    last_game_at: Optional[int] = None
    games_count: int
```

### Endpoint Implementations

#### Start OAuth Flow

```python
@app.post("/auth/lichess/start", response_model=AuthStartResponse)
async def start_lichess_auth():
    auth_url, state = lichess_auth.start_authorization()
    return AuthStartResponse(auth_url=auth_url, state=state)
```

#### Browser Callback (GET)

Returns an HTML page showing success/failure:

```python
@app.get("/auth/lichess/callback")
async def lichess_oauth_callback(code: str, state: str):
    result = await lichess_auth.complete_authorization(code, state)
    
    # Calculate expiry
    expires_at = int(time.time()) + result.expires_in if result.expires_in else None
    
    # Save account
    account_manager.add_account(
        username=result.username,
        access_token=result.access_token,
        token_expires_at=expires_at
    )
    
    # Return styled HTML page
    return HTMLResponse(content=f"""
        <html>
        <body style="background: #1a1a2e; color: #fff; ...">
            <h1>✓ Authorization Successful!</h1>
            <p>Logged in as {result.username}</p>
        </body>
        </html>
    """)
```

#### Manual Token Entry

```python
@app.post("/auth/lichess/token", response_model=AuthCallbackResponse)
async def add_manual_token(request: ManualTokenRequest):
    # Verify token with Lichess
    account_info = await add_token_manually(request.access_token)
    
    if not account_info:
        return AuthCallbackResponse(success=False, error="Invalid token")
    
    # Save account (personal tokens don't expire)
    account_manager.add_account(
        username=account_info['username'],
        access_token=request.access_token,
        token_expires_at=None
    )
    
    return AuthCallbackResponse(success=True, username=account_info['username'])
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LICHESS_CLIENT_ID` | `chessql-desktop` | OAuth client ID (any name works) |
| `LICHESS_REDIRECT_URI` | `http://localhost:9090/auth/lichess/callback` | OAuth callback URL |
| `CHESSQL_DB_PATH` | `chess_games.db` | SQLite database path |

### Lichess OAuth Notes

- **No app registration required** - Lichess allows any `client_id`
- PKCE provides security without client secrets
- Personal tokens can be created at: https://lichess.org/account/oauth/token
- Minimum scope needed: `preference:read`

---

## Security Considerations

1. **PKCE Flow**: Uses SHA256 code challenge to prevent authorization code interception
2. **State Parameter**: Random 32-byte token prevents CSRF attacks
3. **Token Storage**: Access tokens stored in local SQLite database
4. **Token Revocation**: Tokens revoked on Lichess when account is removed
5. **No Token Exposure**: `list_accounts()` never returns access tokens

---

## Testing

### Start the Server

```bash
cd /Users/administrator/Music/chessql
source .venv/bin/activate
python start_server.py
```

### Test Endpoints

```bash
# Health check
curl http://localhost:9090/health

# List accounts (empty initially)
curl http://localhost:9090/auth/accounts

# Start OAuth flow
curl -X POST http://localhost:9090/auth/lichess/start

# Add manual token
curl -X POST http://localhost:9090/auth/lichess/token \
  -H "Content-Type: application/json" \
  -d '{"access_token": "lip_xxxxx"}'

# Verify account
curl http://localhost:9090/auth/accounts/username/verify

# Remove account
curl -X DELETE http://localhost:9090/auth/accounts/username
```

### Swagger UI

Interactive API documentation available at: http://localhost:9090/docs

---

## Next Steps

- **Phase 2**: Implement Lichess game streaming and sync
- **Phase 3**: Add account management UI in Electron app
- **Phase 4**: Package with PyInstaller and electron-builder

