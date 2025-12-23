# Phase 3: Account Management UI

This document covers the implementation of the account management UI in the Electron desktop application.

## Overview

We implemented a full account management interface that allows users to:

- **Link Lichess accounts** via OAuth2 PKCE flow
- **View linked accounts** with stats (games count, last sync date)
- **Sync games** from Lichess (incremental or full)
- **Monitor sync progress** in real-time
- **Remove accounts** when no longer needed

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Electron Main Process                     │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │  OAuth Window   │  │  IPC Handlers   │                   │
│  │  (Lichess Auth) │  │  (api-request)  │                   │
│  └────────┬────────┘  └────────┬────────┘                   │
│           │                    │                             │
└───────────┼────────────────────┼─────────────────────────────┘
            │                    │
            ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Electron Renderer                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    ChessQLApp                        │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │    │
│  │  │ Accounts Btn │  │ Accounts     │  │ Sync      │  │    │
│  │  │ (Header)     │  │ Panel        │  │ Toast     │  │    │
│  │  └──────────────┘  └──────────────┘  └───────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  /auth/lichess/start    → OAuth URL + code_verifier         │
│  /auth/lichess/callback → Exchange code for token           │
│  /auth/accounts         → List all accounts                 │
│  /sync/start/{user}     → Start game sync                   │
│  /sync/status/{user}    → Get sync progress                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Files Modified

### UI Files

| File | Changes |
|------|---------|
| `index.html` | Added accounts button, panel, modal, and sync toast |
| `styles.css` | Added styles for all account management components |
| `app.js` | Added account management logic and OAuth flow |
| `main-fixed.js` | Added OAuth window handling and IPC handlers |

### Backend Files

| File | Changes |
|------|---------|
| `server.py` | Updated `AuthStartResponse` to include `code_verifier` |
| `lichess_auth.py` | Updated `complete_authorization` to accept optional `code_verifier` |

---

## UI Components

### 1. Accounts Button (Header)

Located in the header, shows account count badge:

```html
<button id="accountsBtn" class="accounts-btn">
    <span class="accounts-icon">👤</span>
    <span class="accounts-label">Accounts</span>
    <span id="accountsBadge" class="accounts-badge hidden">0</span>
</button>
```

### 2. Accounts Panel (Sidebar)

Slides in from the right, contains:
- Add account button
- List of linked accounts with stats
- Sync controls for each account

```html
<div id="accountsPanel" class="accounts-panel hidden">
    <div class="accounts-panel-header">
        <h2>Lichess Accounts</h2>
        <button id="closeAccountsPanel" class="close-btn">&times;</button>
    </div>
    <div class="accounts-panel-content">
        <div class="add-account-section">
            <button id="addAccountBtn" class="add-account-btn">
                <span class="add-icon">+</span>
                <span>Link Lichess Account</span>
            </button>
        </div>
        <div id="accountsList" class="accounts-list">
            <!-- Account cards rendered dynamically -->
        </div>
    </div>
</div>
```

### 3. Account Card

Each linked account displays:
- Username with avatar
- Connection status
- Stats (games count, last sync date)
- Sync buttons (incremental and full)

```javascript
createAccountCard(account) {
    return `
        <div class="account-card" data-username="${account.username}">
            <div class="account-card-header">
                <div class="account-info">
                    <div class="account-avatar">${initial}</div>
                    <div class="account-details">
                        <span class="account-username">${account.username}</span>
                        <span class="account-status">
                            <span class="status-dot"></span>
                            Connected
                        </span>
                    </div>
                </div>
                <div class="account-actions">
                    <button class="account-action-btn refresh">🔄</button>
                    <button class="account-action-btn delete">🗑️</button>
                </div>
            </div>
            <div class="account-stats">
                <div class="stat-item">
                    <div class="stat-value">${gamesCount}</div>
                    <div class="stat-label">Games</div>
                </div>
                <!-- More stats... -->
            </div>
            <div class="account-sync-section">
                <button class="sync-btn primary">🔄 Sync New Games</button>
                <button class="sync-btn secondary">Full Sync</button>
            </div>
        </div>
    `;
}
```

### 4. OAuth Modal

Modal for initiating Lichess login:

```html
<div id="accountModal" class="modal hidden">
    <div class="modal-content account-modal-content">
        <div class="modal-header">
            <h2>Link Lichess Account</h2>
        </div>
        <div class="modal-body account-modal-body">
            <p class="oauth-description">
                Connect your Lichess account to sync and analyze your games.
            </p>
            <button id="startOAuthBtn" class="oauth-btn">
                <span class="lichess-logo">♞</span>
                Login with Lichess
            </button>
            <div id="oauthStatus" class="oauth-status hidden">
                <div class="spinner"></div>
                <span>Waiting for authorization...</span>
            </div>
        </div>
    </div>
</div>
```

### 5. Sync Progress Toast

Fixed position toast showing real-time sync progress:

```html
<div id="syncToast" class="sync-toast hidden">
    <div class="sync-toast-content">
        <div class="sync-info">
            <span id="syncUsername">-</span>
            <span id="syncStatusText">Syncing...</span>
        </div>
        <div class="sync-progress-bar">
            <div id="syncProgressFill" style="width: 0%"></div>
        </div>
        <div class="sync-stats">
            <span id="syncGamesCount">0 games</span>
            <span id="syncNewGames" class="sync-new">0 new</span>
        </div>
    </div>
</div>
```

---

## OAuth Flow for Desktop Apps

### Challenge: PKCE in Desktop Apps

Desktop apps can't securely store secrets, so we use PKCE (Proof Key for Code Exchange). The challenge is that the `code_verifier` must be:
1. Generated before the auth URL is created
2. Passed back when exchanging the code for a token

### Solution: Client-Side PKCE Management

1. **Backend returns `code_verifier`** in the `/auth/lichess/start` response
2. **Electron main process** stores it temporarily
3. **OAuth window** opens for Lichess login
4. **On callback**, main process passes `code_verifier` back to backend
5. **Backend exchanges** code for token using the provided `code_verifier`

### Implementation

#### Backend Changes

```python
# server.py
class AuthStartResponse(BaseModel):
    auth_url: str
    state: str
    code_verifier: str  # Required for desktop apps

@app.post("/auth/lichess/start")
async def start_lichess_auth():
    auth_url, state, code_verifier = lichess_auth.start_authorization()
    return AuthStartResponse(auth_url=auth_url, state=state, code_verifier=code_verifier)
```

```python
# lichess_auth.py
def start_authorization(self, scopes=None) -> Tuple[str, str, str]:
    pkce = self.generate_pkce_pair()
    # ... build auth_url ...
    return auth_url, pkce.state, pkce.code_verifier

async def complete_authorization(self, code, state, code_verifier=None):
    # Desktop apps pass code_verifier directly
    if code_verifier:
        verifier = code_verifier
    else:
        # Web apps use stored verifier
        pkce = self._pending_auth.pop(state)
        verifier = pkce.code_verifier
    # ... exchange code for token ...
```

#### Electron Main Process

```javascript
// main-fixed.js
ipcMain.handle('start-oauth', async (event, { authUrl, codeVerifier, state }) => {
    return new Promise((resolve, reject) => {
        pendingOAuthData = { codeVerifier, state };
        
        // Create OAuth window
        authWindow = new BrowserWindow({
            width: 600,
            height: 700,
            parent: mainWindow,
            modal: true
        });
        
        authWindow.loadURL(authUrl);
        
        // Listen for callback
        authWindow.webContents.on('will-redirect', (event, url) => {
            handleOAuthCallback(url, resolve, reject);
        });
    });
});

async function handleOAuthCallback(url, resolve, reject) {
    if (url.startsWith(callbackUrl)) {
        const urlObj = new URL(url);
        const code = urlObj.searchParams.get('code');
        
        // Exchange code with stored code_verifier
        const response = await fetch('/auth/lichess/callback', {
            method: 'POST',
            body: JSON.stringify({
                code: code,
                state: urlObj.searchParams.get('state'),
                code_verifier: pendingOAuthData.codeVerifier
            })
        });
        
        resolve({ success: true, data: await response.json() });
        authWindow.close();
    }
}
```

#### Renderer Process

```javascript
// app.js
async startOAuthFlow() {
    // Get auth URL and code_verifier from backend
    const response = await ipcRenderer.invoke('api-request', {
        endpoint: '/auth/lichess/start',
        method: 'POST'
    });
    
    // Open OAuth window via main process
    const oauthResult = await ipcRenderer.invoke('start-oauth', {
        authUrl: response.data.auth_url,
        codeVerifier: response.data.code_verifier,
        state: response.data.state
    });
    
    if (oauthResult.success) {
        await this.loadAccounts();
        this.hideAccountModal();
    }
}
```

---

## Sync Progress Polling

Real-time sync progress is implemented via polling:

```javascript
startSyncPolling(username) {
    this.syncIntervals[username] = setInterval(async () => {
        const response = await ipcRenderer.invoke('api-request', {
            endpoint: `/sync/status/${username}`,
            method: 'GET'
        });
        
        if (response.success) {
            this.updateSyncProgress(username, response.data);
        }
    }, 1000); // Poll every second
}

updateSyncProgress(username, progress) {
    // Update toast UI
    this.syncUsername.textContent = username;
    this.syncStatusText.textContent = progress.status;
    
    // Calculate and update progress bar
    let percentage = 0;
    if (progress.total_games > 0) {
        percentage = (progress.synced_games / progress.total_games) * 100;
    }
    this.syncProgressFill.style.width = `${percentage}%`;
    
    // Check if complete
    if (progress.status === 'completed') {
        clearInterval(this.syncIntervals[username]);
        setTimeout(() => this.hideSyncToast(), 3000);
    }
}
```

---

## Styling Highlights

### Accounts Panel Animation

```css
.accounts-panel {
    position: fixed;
    right: 0;
    width: 380px;
    transform: translateX(100%);
    transition: transform 0.3s ease;
}

.accounts-panel:not(.hidden) {
    transform: translateX(0);
}
```

### Sync Toast Animation

```css
.sync-toast {
    position: fixed;
    bottom: 140px;
    right: 20px;
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
```

### Status Indicator

```css
.status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #4CAF50;
}

.status-dot.syncing {
    background: #ff9800;
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
```

---

## Testing

### Test Account Panel

1. Start the server: `python start_server.py`
2. Start the Electron app: `npm start`
3. Click the "Accounts" button in the header
4. Verify the panel slides in from the right
5. Verify linked accounts are displayed with stats

### Test OAuth Flow

1. Click "Link Lichess Account"
2. Click "Login with Lichess"
3. Verify OAuth window opens with Lichess login page
4. Complete login on Lichess
5. Verify window closes and account appears in the list

### Test Sync

1. Click "Sync New Games" on an account card
2. Verify sync toast appears with progress
3. Monitor progress updates
4. Verify toast auto-hides after completion
5. Verify games count updates in the account card

---

## Next Steps

- **Phase 4**: PyInstaller bundling and electron-builder packaging

