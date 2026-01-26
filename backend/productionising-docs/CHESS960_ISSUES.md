# Chess960 Support - Known Issues

**Branch Status:** Under Development  
**Last Updated:** January 23, 2026

## Summary

Chess960 (Fischer Random) games are being ingested from Lichess but have display issues in the UI due to limitations in the `chess.js` library.

## Recent Fix (Jan 23, 2026)

### 1. Switched to void-57:freestyle-support fork
Installed the `void-57:freestyle-support` fork of chess.js which has native Chess960 support:
```json
"chess.js": "github:void-57/chess.js#freestyle-support"
```

### 2. Updated app.js to use Chess960 class
The fork provides a separate `Chess960` class that extends `Chess` with proper Chess960 castling support. Updated the following:

1. **Import both classes:**
   ```javascript
   const { Chess, Chess960 } = require('chess.js');
   ```

2. **Use Chess960 class for Chess960 games in:**
   - `loadGameFromMoves()` - main game loading
   - `resetToStartingPosition()` - position reset
   - `getFinalPosition()` - thumbnails
   - `navigateToMove()` - move animation
   - `animateMovesToPosition()` - move animation

**Status:** Testing required to verify full move display and correct board positions.

## What's Working

1. **Data Ingestion**: Chess960 games are correctly fetched from Lichess API
2. **Database Storage**: Games are stored with `variant = 'chess960'`
3. **ChessQL Queries**: Can filter by `variant = 'chess960'`
4. **Natural Language Search**: Supports "chess960" and "fischer random" queries
5. **UI Variant Badge**: Chess960 games show a dice icon badge on thumbnails and in the game modal

## What's NOT Working

### 1. Incomplete Move Display
Chess960 games often show fewer moves than actually played. For example, a 20-move game might only display 7 moves.

**Root Cause:** The `chess.js` library (v1.0.0-beta.6) doesn't have native Chess960 support. When it encounters a castling move (`O-O` or `O-O-O`) from a non-standard starting position, it fails validation and stops parsing.

### 2. Incorrect Board Position
Thumbnails and the game modal may show:
- The standard starting position instead of the Chess960 starting position
- A position that doesn't match the actual final game state

**Root Cause:** While the PGN contains the correct `[FEN "..."]` tag with the Chess960 starting position, `chess.js` may fail to:
1. Load the FEN correctly (castling rights notation issues)
2. Apply moves correctly after loading the custom FEN

## Technical Details

### Chess960 Castling Notation Problem

Chess960 uses file-based castling notation in FEN strings. For example:
- Standard FEN castling: `KQkq` (King can castle kingside/queenside)
- Chess960 FEN castling: `HAha` (files where rooks are located)

The `chess.js` library expects standard `KQkq` notation, but Lichess provides file-based notation for Chess960. Attempts to convert between formats have been unreliable.

### chess.js Limitations

```javascript
// This does NOT work - chess.js doesn't have a chess960 option
const chess = new Chess(fen, { chess960: true });

// This is the only valid constructor
const chess = new Chess();        // Standard starting position
const chess = new Chess(fen);     // Custom FEN (limited Chess960 support)
```

The library can load a custom FEN, but it validates moves against standard chess rules, causing Chess960 castling to fail.

## Attempted Solutions

1. **FEN Castling Conversion**: Tried converting file-based castling (`HAha`) to standard (`KQkq`) - unreliable
2. **Sloppy Move Parsing**: Using `chess.move(move, { sloppy: true })` - helps with some notation issues but not castling
3. **Skip Invalid Moves**: Continue parsing after failed moves - results in incorrect positions

## Potential Solutions to Explore

### Option 1: Fork or Patch chess.js
Add Chess960 support to the library. The main changes needed:
- Accept file-based castling in FEN
- Validate castling moves based on actual rook/king positions, not standard positions

### Option 2: Use a Different Library
Consider alternatives with Chess960 support:
- `chess-es6.js` - may have better variant support
- `chessground` - Lichess's own board library
- `shakmern` - Rust-based chess library with WASM bindings

### Option 3: Backend Move Validation
Process Chess960 moves on the backend (Python) using `python-chess` which has full Chess960 support, then send validated move data to the frontend.

### Option 4: Store Pre-computed Positions
During Lichess sync, compute and store the final position FEN for each game. The UI would display this directly without needing to replay moves.

## Current Workaround

Standard chess games work correctly. Chess960 games will:
- Display in search results with a dice icon badge
- Show moves up to the first castling (or other Chess960-specific move)
- May show incorrect positions

Users can click through to Lichess using the "View on Lichess" button to see the full game.

## Files Involved

- `backend/lichess_sync.py` - Captures `initialFen` for Chess960 games
- `ui/app.js` - Game loading and display logic
- `ui/styles.css` - Chess960 badge styling

## Testing Chess960

```
# ChessQL query to find Chess960 games
variant = 'chess960'

# Natural language
"show me chess960 games"
"fischer random games where I won"
```

