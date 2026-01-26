# Chess.com Integration Plan

## Executive Summary

This document outlines the plan to integrate Chess.com game imports into ChessQL, following the existing Lichess integration pattern. Chess.com uses a public API (no authentication required) that returns JSON-LD formatted data.

---

## 1. Chess.com API Analysis

### 1.1 API Overview
- **API Type**: Published-Data API (PubAPI) - Read-only REST API
- **Authentication**: None required (public data access)
- **Data Format**: JSON-LD (standard JSON)
- **Base URL**: `https://api.chess.com/pub`

### 1.2 Key Endpoints

**Monthly Archives** (Primary for bulk import):
```
GET https://api.chess.com/pub/player/{username}/games/{year}/{month}
```

**Available Archives List**:
```
GET https://api.chess.com/pub/player/{username}/games/archives
```

**Game Details** (Individual game):
```
GET https://api.chess.com/pub/player/{username}/games/{year}/{month}
```

### 1.3 Data Structure (Expected)

Based on Chess.com API documentation, the monthly archive endpoint returns:
```json
{
  "games": [
    {
      "url": "https://www.chess.com/game/live/{game_id}",
      "pgn": "Full PGN text...",
      "time_control": "600+0",
      "end_time": 1234567890,
      "rated": true,
      "time_class": "blitz",
      "rules": "chess",
      "white": {
        "rating": 1500,
        "result": "win",
        "@id": "https://api.chess.com/pub/player/{username}",
        "username": "player1"
      },
      "black": {
        "rating": 1600,
        "result": "loss",
        "@id": "https://api.chess.com/pub/player/{username}",
        "username": "player2"
      }
    }
  ]
}
```

### 1.4 Rate Limiting & Constraints
- **Serial requests**: Unlimited
- **Parallel requests**: May trigger 429 (rate limit) errors
- **Cache refresh**: Data updates every 12-24 hours
- **Best practices**:
  - Use serial request queue
  - Include User-Agent header with contact info
  - Implement ETag/Last-Modified header caching
  - Add delays between requests if needed

---

## 2. Current System Architecture

### 2.1 Existing Components

**Lichess Integration**:
- `backend/lichess_sync.py` - Game syncing logic
- `backend/lichess_auth.py` - OAuth2 authentication
- `backend/accounts.py` - Account management
- `backend/database.py` - Database operations

**Database Schema**:
- `accounts` table: Stores username, access_token, sync status
- `games` table: Stores game data with `lichess_id` field
- Currently platform-specific (Lichess-only)

### 2.2 Data Flow (Lichess)
1. User authenticates → OAuth2 flow → Access token stored
2. Sync initiated → `LichessSync.stream_games()` → NDJSON stream
3. Games parsed → `LichessGame.from_ndjson()` → Converted to internal format
4. Games inserted → `ChessDatabase.insert_game()` → Stored with `lichess_id`

---

## 3. Integration Plan

### 3.1 Database Schema Changes

**Option A: Add platform field to accounts table** (Recommended)
```sql
ALTER TABLE accounts ADD COLUMN platform TEXT DEFAULT 'lichess';
-- Values: 'lichess', 'chesscom'
```

**Option B: Separate game ID fields**
```sql
ALTER TABLE games ADD COLUMN chesscom_id TEXT;
-- Keep lichess_id for Lichess games, use chesscom_id for Chess.com games
```

**Recommendation**: Use Option A + Option B
- Platform stored at account level
- Separate ID fields for games (allows future platforms)
- Index both ID fields for duplicate checking

### 3.2 New Files to Create

#### 3.2.1 `backend/chesscom_sync.py`
Similar structure to `lichess_sync.py`:
- `ChessComGame` dataclass (mirrors `LichessGame`)
- `ChessComSync` class (mirrors `LichessSync`)
- `stream_games()` method for monthly archive iteration
- `to_pgn_dict()` method to convert to database format

**Key differences from Lichess**:
- No authentication required (no access_token parameter)
- Monthly archive iteration (not NDJSON stream)
- JSON parsing instead of NDJSON
- Different field mappings

#### 3.2.2 `backend/chesscom_auth.py` (Optional)
Since Chess.com doesn't require authentication, this could be minimal:
- Simple username validation
- Or skip entirely and just use username directly

**Recommendation**: Skip authentication module, add username validation in sync module.

### 3.3 Modified Files

#### 3.3.1 `backend/database.py`
- Add `platform` column to accounts table (migration)
- Add `chesscom_id` column to games table (migration)
- Update `insert_game()` to handle `chesscom_id`
- Add `game_exists_chesscom()` method (similar to `game_exists()`)
- Update `game_exists()` to check both platforms

#### 3.3.2 `backend/accounts.py`
- Add `platform` parameter to `add_account()`
- Update account retrieval to support platform filtering
- Add platform validation

#### 3.3.3 `backend/server.py`
- Add Chess.com sync endpoints (mirror Lichess endpoints):
  - `POST /sync/chesscom/start/{username}`
  - `GET /sync/chesscom/status/{username}`
  - `POST /sync/chesscom/stop/{username}`
- Add account management endpoints:
  - `POST /auth/chesscom/add` (simple username addition)
  - `GET /auth/accounts` (update to show platform)
  - `DELETE /auth/accounts/{username}` (works for both)

#### 3.3.4 `backend/lichess_sync.py` (or create unified sync manager)
- Consider creating unified sync manager
- Or keep separate managers and route in server.py

---

## 4. Implementation Details

### 4.1 Chess.com Game Data Mapping

Map Chess.com JSON to internal format:

| Chess.com Field | Internal Field | Notes |
|----------------|----------------|-------|
| `url` | `site` | Full URL |
| `pgn` | `pgn_text`, `moves` | Extract moves from PGN |
| `time_control` | `time_control` | Format: "600+0" |
| `time_class` | `speed` | Map: blitz→blitz, rapid→rapid, etc. |
| `white.username` | `white_player` | |
| `black.username` | `black_player` | |
| `white.rating` | `white_elo` | |
| `black.rating` | `black_elo` | |
| `white.result` | `white_result` | Map: win→win, loss→loss, etc. |
| `black.result` | `black_result` | |
| `end_time` | `date_played` | Convert timestamp to date |
| `rules` | `variant` | Usually "chess" (standard) |
| Game ID from URL | `chesscom_id` | Extract from URL |

### 4.2 Speed Category Mapping

Chess.com `time_class` → Internal `speed`:
- `bullet` → `bullet`
- `blitz` → `blitz`
- `rapid` → `rapid`
- `daily` → `classical` (or custom handling)
- `classical` → `classical`

### 4.3 Incremental Sync Strategy

**Lichess approach**: Uses `since` timestamp (milliseconds)
**Chess.com approach**: Use monthly archives + date filtering

1. Get list of available archives: `/games/archives`
2. Filter archives by date (compare with `last_game_at`)
3. Process each month's archive sequentially
4. Track latest game timestamp for next sync

### 4.4 PGN Parsing

Chess.com provides full PGN in response. Options:
1. **Use existing PGN parser**: Extract moves from PGN using `ingestion.py` logic
2. **Parse JSON directly**: If PGN parsing is complex, extract metadata from JSON

**Recommendation**: Use existing PGN parsing logic from `ingestion.py` for consistency.

---

## 5. Implementation Steps

### Phase 1: Database Schema Updates
1. Add `platform` column to `accounts` table
2. Add `chesscom_id` column to `games` table
3. Create index on `chesscom_id`
4. Update `game_exists()` to check both platforms

### Phase 2: Chess.com Sync Module
1. Create `backend/chesscom_sync.py`
2. Implement `ChessComGame` dataclass
3. Implement `ChessComSync` class with:
   - `stream_games()` - Iterate monthly archives
   - `get_archives()` - Fetch available archives
   - `parse_game()` - Convert JSON to `ChessComGame`
4. Implement `to_pgn_dict()` for database insertion

### Phase 3: Account Management
1. Update `accounts.py` to support platform
2. Add simple username validation for Chess.com
3. Update account endpoints in `server.py`

### Phase 4: API Endpoints
1. Add Chess.com sync endpoints to `server.py`
2. Create unified sync task runner (or separate)
3. Update UI endpoints if needed

### Phase 5: Testing & Validation
1. Test with real Chess.com usernames
2. Verify duplicate detection works
3. Test incremental sync
4. Verify PGN parsing accuracy

---

## 6. Data Ingestion Pipeline Changes

### 6.1 Current Pipeline (Lichess)
```
Lichess API → NDJSON Stream → LichessGame.from_ndjson() → to_pgn_dict() → insert_game()
```

### 6.2 New Pipeline (Chess.com)
```
Chess.com API → JSON Archive → Parse Games → ChessComGame.from_json() → to_pgn_dict() → insert_game()
```

### 6.3 Unified Approach
Both pipelines converge at `to_pgn_dict()` → `insert_game()`, so:
- ✅ No changes needed to `insert_game()` (already handles optional `lichess_id`)
- ✅ No changes needed to capture analysis (uses moves string)
- ⚠️ Need to handle `chesscom_id` in duplicate checking

---

## 7. Edge Cases & Considerations

### 7.1 Rate Limiting
- Implement request queue with delays
- Handle 429 errors gracefully
- Add retry logic with exponential backoff

### 7.2 Large Archives
- Some users may have thousands of games per month
- Process in batches if needed
- Show progress updates

### 7.3 Missing Data
- Handle missing PGN gracefully
- Default values for optional fields
- Log warnings for malformed data

### 7.4 Platform Identification
- Games table needs to know which platform
- Options:
  - Add `platform` column to games table
  - Infer from `lichess_id` vs `chesscom_id` presence
  - Store in `site` URL pattern

**Recommendation**: Infer from ID fields (simpler, no schema change needed).

### 7.5 Date Handling
- Chess.com uses Unix timestamps (seconds)
- Lichess uses milliseconds
- Standardize to milliseconds internally

---

## 8. API Endpoint Design

### 8.1 Account Management

**Add Chess.com Account**:
```
POST /auth/chesscom/add
{
  "username": "player123"
}
```

**List Accounts** (Updated):
```
GET /auth/accounts
Response includes platform field
```

### 8.2 Sync Endpoints

**Start Sync**:
```
POST /sync/chesscom/start/{username}
{
  "max_games": 100,  // Optional
  "full_sync": false  // Optional
}
```

**Get Status**:
```
GET /sync/chesscom/status/{username}
```

**Stop Sync**:
```
POST /sync/chesscom/stop/{username}
```

---

## 9. Testing Strategy

### 9.1 Unit Tests
- Test `ChessComGame.from_json()` with sample data
- Test `to_pgn_dict()` conversion
- Test duplicate detection

### 9.2 Integration Tests
- Test full sync flow with test account
- Test incremental sync
- Test error handling (rate limits, invalid usernames)

### 9.3 Manual Testing
- Test with real Chess.com accounts
- Verify games appear correctly in UI
- Verify queries work with Chess.com games

---

## 10. Future Enhancements

1. **Unified Sync Manager**: Abstract sync logic for both platforms
2. **Batch Processing**: Process multiple months in parallel (with rate limiting)
3. **PGN Download**: Direct PGN download endpoint support
4. **Tournament Games**: Support tournament/club game imports
5. **Live Games**: Real-time game import (if Chess.com supports it)

---

## 11. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Rate limiting | Medium | Serial requests, delays, retry logic |
| API changes | Low | Version API calls, error handling |
| Large archives | Low | Batch processing, progress updates |
| Data format changes | Medium | Robust parsing, default values |
| Duplicate games | High | Proper ID tracking, duplicate checks |

---

## 12. Success Criteria

✅ Chess.com games can be imported via API
✅ Games stored with correct metadata
✅ Duplicate detection works across platforms
✅ Incremental sync works correctly
✅ UI displays Chess.com games properly
✅ Queries work with Chess.com games
✅ No breaking changes to existing Lichess functionality

---

## Next Steps

1. Review and approve this plan
2. Start with Phase 1 (Database schema updates)
3. Implement incrementally, testing each phase
4. Update UI to support Chess.com accounts (separate task)

