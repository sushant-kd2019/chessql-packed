# Phase 2: Lichess Game Sync Implementation

This document covers the implementation of game streaming and syncing from Lichess API.

## Overview

We implemented a streaming sync system that downloads games from Lichess API in real-time using NDJSON streaming. The sync supports:

- **Full sync**: Download all games for an account
- **Incremental sync**: Download only new games since last sync
- **Background processing**: Non-blocking sync with progress tracking
- **Duplicate detection**: Skip games already in the database

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   API Request   │────▶│  Sync Manager    │────▶│  Lichess API    │
│  /sync/start    │     │  (Background)    │◀────│  (NDJSON Stream)│
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  Game Processing │
                        │  - Parse NDJSON  │
                        │  - Check dups    │
                        │  - Analyze moves │
                        └──────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  SQLite Database │
                        │  - games table   │
                        │  - captures      │
                        └──────────────────┘
```

## Files Created/Modified

### New Files

| File | Purpose |
|------|---------|
| `lichess_sync.py` | Game streaming and sync logic |

### Modified Files

| File | Changes |
|------|---------|
| `database.py` | Added `lichess_id` column, duplicate checking methods |
| `server.py` | Added sync endpoints, background task handling |

---

## Database Schema Changes

### Games Table

Added `lichess_id` column for duplicate detection:

```sql
ALTER TABLE games ADD COLUMN lichess_id TEXT;
CREATE INDEX idx_lichess_id ON games(lichess_id);
```

### New Methods in `ChessDatabase`

```python
def game_exists(self, lichess_id: str) -> bool:
    """Check if a game with the given Lichess ID already exists."""

def get_games_count_by_account(self, account_id: int) -> int:
    """Get the count of games for a specific account."""
```

---

## Module: `lichess_sync.py`

### Constants

```python
LICHESS_API_BASE = "https://lichess.org/api"
LICHESS_GAMES_EXPORT_URL = f"{LICHESS_API_BASE}/games/user"
REQUEST_DELAY = 0.1  # 100ms between requests
```

### Enums

```python
class SyncStatus(Enum):
    IDLE = "idle"
    STARTING = "starting"
    SYNCING = "syncing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"
```

### Data Classes

#### SyncProgress

Tracks the progress of a sync operation:

```python
@dataclass
class SyncProgress:
    status: SyncStatus = SyncStatus.IDLE
    total_games: Optional[int] = None
    synced_games: int = 0
    new_games: int = 0
    skipped_games: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
```

#### LichessGame

Parsed game data from Lichess NDJSON response:

```python
@dataclass
class LichessGame:
    id: str
    pgn: str
    created_at: int      # Unix timestamp (ms)
    last_move_at: int
    white_player: str
    black_player: str
    white_rating: Optional[int]
    black_rating: Optional[int]
    result: str          # "1-0", "0-1", "1/2-1/2", "*"
    variant: str
    speed: str
    time_control: Optional[str]
    opening_eco: Optional[str]
    opening_name: Optional[str]
    termination: str
    moves: str
    
    @classmethod
    def from_ndjson(cls, data: Dict) -> "LichessGame":
        """Parse from Lichess NDJSON format."""
    
    def to_pgn_dict(self) -> Dict[str, Any]:
        """Convert to format for ChessDatabase.insert_game()."""
```

### Class: `LichessSync`

Main sync handler with singleton pattern.

#### Key Methods

| Method | Description |
|--------|-------------|
| `get_progress(username)` | Get current sync progress |
| `cancel_sync(username)` | Request sync cancellation |
| `is_syncing(username)` | Check if sync is in progress |
| `stream_games(...)` | Async generator for streaming games |
| `sync_account(...)` | Full sync operation |
| `count_user_games(...)` | Get total game count from API |

#### Streaming Implementation

```python
async def stream_games(
    self,
    username: str,
    access_token: str,
    since: Optional[int] = None,    # Unix timestamp (ms)
    until: Optional[int] = None,
    max_games: Optional[int] = None,
    with_pgn: bool = False,
    with_opening: bool = True,
) -> AsyncGenerator[LichessGame, None]:
    """
    Stream games from Lichess API using NDJSON format.
    """
    url = f"{LICHESS_GAMES_EXPORT_URL}/{username}"
    
    params = {
        "pgnInJson": "true" if with_pgn else "false",
        "opening": "true",
        "clocks": "false",
        "evals": "false",
        "moves": "true",
    }
    
    if since:
        params["since"] = str(since)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/x-ndjson",
    }
    
    async with httpx.AsyncClient(timeout=...) as client:
        async with client.stream("GET", url, params=params, headers=headers) as response:
            async for line in response.aiter_lines():
                if line.strip():
                    game_data = json.loads(line)
                    yield LichessGame.from_ndjson(game_data)
```

---

## API Endpoints

### Sync Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sync/start/{username}` | Start background sync |
| GET | `/sync/status/{username}` | Get sync progress |
| POST | `/sync/stop/{username}` | Cancel ongoing sync |
| GET | `/sync/games/{username}` | Get synced games count |

### Request/Response Models

```python
class SyncStartRequest(BaseModel):
    max_games: Optional[int] = None  # Limit for testing

class SyncProgressResponse(BaseModel):
    status: str
    total_games: Optional[int] = None
    synced_games: int = 0
    new_games: int = 0
    skipped_games: int = 0
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
```

### Background Sync Task

The sync runs as an `asyncio.Task` in the background:

```python
@app.post("/sync/start/{username}")
async def start_sync(username: str, request: SyncStartRequest = None):
    # 1. Get account and validate
    account = account_manager.get_account(username)
    
    # 2. Check for existing sync
    if sync_manager.is_syncing(username):
        raise HTTPException(409, "Sync already in progress")
    
    # 3. Get last sync timestamp for incremental sync
    since = account.get('last_game_at')
    
    # 4. Start background task
    task = asyncio.create_task(_run_sync_task(...))
    
    # 5. Return immediately with initial progress
    return SyncProgressResponse(status="syncing", ...)
```

### Sync Task Implementation

```python
async def _run_sync_task(username, access_token, account_id, since, max_games):
    sync_manager = get_sync_manager()
    progress = sync_manager.get_progress(username)
    
    async for game in sync_manager.stream_games(...):
        # Check cancellation
        if sync_manager._cancel_flags.get(username):
            progress.status = SyncStatus.CANCELLED
            break
        
        # Convert game to database format
        game_data = game.to_pgn_dict()
        
        # Check for duplicates
        if chess_db.game_exists(game.id):
            progress.skipped_games += 1
        else:
            # Insert game and analyze captures
            game_id = chess_db.insert_game(game_data, account_id)
            captures = piece_analyzer.analyze_captures(...)
            chess_db.insert_captures(game_id, captures)
            progress.new_games += 1
        
        progress.synced_games += 1
    
    # Update account sync status
    account_manager.update_sync_status(
        username=username,
        last_sync_at=datetime.now(),
        last_game_at=latest_game_ts,
        games_count=chess_db.get_games_count_by_account(account_id)
    )
```

---

## Lichess API Details

### Export Games Endpoint

```
GET /api/games/user/{username}
```

**Headers:**
```
Authorization: Bearer {access_token}
Accept: application/x-ndjson
```

**Query Parameters:**
| Parameter | Description |
|-----------|-------------|
| `since` | Unix timestamp (ms) - games created after this time |
| `until` | Unix timestamp (ms) - games created before this time |
| `max` | Maximum number of games to return |
| `moves` | Include moves (default: true) |
| `pgnInJson` | Include PGN in response |
| `opening` | Include opening info |
| `clocks` | Include clock data |
| `evals` | Include engine evaluations |

**Response Format (NDJSON):**
```json
{"id":"abc123","rated":true,"variant":"standard","speed":"blitz","perf":"blitz","createdAt":1703260800000,"lastMoveAt":1703261100000,"status":"mate","players":{"white":{"user":{"name":"player1","id":"player1"},"rating":1500},"black":{"user":{"name":"player2","id":"player2"},"rating":1520}},"winner":"white","moves":"e4 e5 Nf3 ...","opening":{"eco":"C50","name":"Italian Game"}}
{"id":"def456",...}
```

### Rate Limiting

- **Authenticated requests**: 15 requests/second
- **Streaming**: No limit on stream duration
- **HTTP 429**: Rate limit exceeded, wait before retry

---

## Incremental Sync Strategy

1. **First sync**: No `since` parameter, downloads all games
2. **Subsequent syncs**: Use `last_game_at + 1` as `since` parameter
3. **Duplicate handling**: Check `lichess_id` before inserting

```python
# Get last sync timestamp
since = account.get('last_game_at')
if since:
    since = since + 1  # Start from next millisecond

# After sync, update account
account_manager.update_sync_status(
    username=username,
    last_game_at=latest_game_ts,  # Timestamp of newest game
    ...
)
```

---

## Error Handling

### Sync Errors

| Error | Handling |
|-------|----------|
| Invalid token (401) | `LichessSyncError("Invalid or expired access token")` |
| User not found (404) | `LichessSyncError("User not found")` |
| Rate limited (429) | `LichessSyncError("Rate limited")` |
| Network error | Caught and stored in `progress.error_message` |

### Graceful Cancellation

```python
# User requests cancellation
sync_manager.cancel_sync(username)

# In sync task loop
if sync_manager._cancel_flags.get(username):
    progress.status = SyncStatus.CANCELLED
    break
```

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
# Check sync status (should be idle)
curl http://localhost:9090/sync/status/lecorvus

# Start sync (requires account to be linked first)
curl -X POST http://localhost:9090/sync/start/lecorvus

# Check progress
curl http://localhost:9090/sync/status/lecorvus

# Cancel sync
curl -X POST http://localhost:9090/sync/stop/lecorvus

# Get synced games count
curl http://localhost:9090/sync/games/lecorvus
```

### Test with Limited Games

```bash
# Sync only 10 games for testing
curl -X POST http://localhost:9090/sync/start/lecorvus \
  -H "Content-Type: application/json" \
  -d '{"max_games": 10}'
```

---

## Performance Considerations

1. **Streaming**: Uses NDJSON streaming to avoid loading all games into memory
2. **Async processing**: Games are processed as they arrive
3. **Duplicate checking**: Index on `lichess_id` for O(1) lookup
4. **Background task**: Non-blocking sync doesn't hold up API responses
5. **Capture analysis**: Runs synchronously per game (could be parallelized)

---

## Move Format Handling

### The Problem

Lichess API returns moves in a **space-separated format without move numbers**:

```
e4 e5 Nf3 Nc6 Bb5 a6 Bxc6 dxc6
```

However, the original `piece_analysis.py` parser expected **PGN format with move numbers**:

```
1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Bxc6 dxc6
```

### The Fix

Updated `parse_moves_with_captures()` in `piece_analysis.py` to auto-detect and handle both formats:

```python
def parse_moves_with_captures(self, moves_text: str) -> List[Dict[str, Any]]:
    """Parse moves and track captures with position information.
    
    Supports both formats:
    - PGN format with move numbers: "1. e4 e5 2. Nf3 Nc6"
    - Lichess format without move numbers: "e4 e5 Nf3 Nc6"
    """
    # Check if moves have move numbers (PGN format) or not (Lichess format)
    has_move_numbers = bool(re.search(r'\d+\.', moves_text))
    
    if has_move_numbers:
        # PGN format parsing (original logic)
        move_blocks = re.split(r'(\d+\.)', moves_text)
        # ... process with move numbers
    else:
        # Lichess format: pair moves as white/black alternating
        all_moves = moves_text.split()
        for i in range(0, len(all_moves), 2):
            move_num = (i // 2) + 1
            white_move = all_moves[i]
            black_move = all_moves[i + 1] if i + 1 < len(all_moves) else ''
            # ... process move pair
```

### Capture Analysis Results

After fixing the parser, running capture analysis on synced games produces:

| Metric | Count |
|--------|-------|
| Total captures analyzed | 28,604 |
| Queen sacrifices | 514 |
| Queen captures total | 2,061 |
| Games with captures | 2,041 |

### Re-analyzing Existing Games

If games were synced before the fix, run this to populate captures:

```python
from piece_analysis import ChessPieceAnalyzer
from database import ChessDatabase
import sqlite3

db = ChessDatabase('chess_games.db')
analyzer = ChessPieceAnalyzer(reference_player='lecorvus')

conn = sqlite3.connect('chess_games.db')
cursor = conn.cursor()

cursor.execute('SELECT id, moves, white_player, black_player FROM games')
for game_id, moves, white, black in cursor.fetchall():
    if moves:
        captures = analyzer.analyze_captures(moves, white, black, 'lecorvus')
        if captures:
            db.insert_captures(game_id, captures)
```

---

## Next Steps

- **Phase 3**: Account management UI in Electron app
- **Phase 4**: PyInstaller bundling and electron-builder packaging

