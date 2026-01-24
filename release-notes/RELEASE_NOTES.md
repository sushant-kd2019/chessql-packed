# ChessQL v0.0.3 — Multi-Platform Support & Enhanced Filtering 🎉

**Release Date:** January 15, 2026

This major release adds Chess.com integration, multi-platform account support, and enhanced query filtering capabilities.

---

## ✨ Major Features

### 🎮 Chess.com Integration
- **Full Chess.com Support** — Import and analyze games from Chess.com alongside Lichess
- **Chess.com Published-Data API** — Seamless integration with Chess.com's public API
- **Monthly Archive Sync** — Efficiently sync games by iterating through monthly archives
- **Platform-Specific Game IDs** — Proper handling of Chess.com game identifiers

### 🔄 Multi-Platform Account Management
- **Same Username Support** — Link accounts with the same username across different platforms (e.g., "lecorvus" on both Lichess and Chess.com)
- **Platform Differentiation** — Visual indicators (♞ for Lichess, ♟ for Chess.com) on accounts and games
- **Unified Account UI** — Single "Add Account" button with platform selection modal
- **Platform-Specific Filtering** — Queries automatically filter by selected account's platform

### 🔍 Enhanced Query Filtering
- **Account ID Filtering** — Queries now filter by specific account ID, ensuring accurate results for multi-platform accounts
- **Platform-Aware Natural Language Search** — Natural language queries automatically understand platform context
- **Improved Query Execution** — Better handling of account and platform filters in both CQL and natural language queries

---

## 🎨 UI Improvements

### Streamlined Account Management
- **Single Add Account Button** — Replaced separate Lichess/Chess.com buttons with unified interface
- **Platform Selection Modal** — Choose platform (Lichess or Chess.com) before adding account
- **Better Visual Hierarchy** — Cleaner, more intuitive account management flow

### Platform Indicators
- **Account Cards** — Platform badges displayed next to usernames
- **Game Cards** — Platform overlay badges on game thumbnails
- **Account Selector** — Platform icons in dropdown menu for easy identification

---

## 🐛 Bug Fixes

### Account Filtering
- **Fixed:** Queries now correctly filter by account ID instead of just username
- **Fixed:** Multi-platform accounts with same username now work correctly
- **Fixed:** Platform filtering properly applied in both CQL and natural language queries

### UI/UX
- **Fixed:** Replaced unsupported `prompt()` function with proper modal for Chess.com account addition
- **Fixed:** Account modal now properly resets to platform selection after closing
- **Fixed:** Better error handling and validation for Chess.com username input

---

## 🔧 Technical Improvements

### Backend
- **Database Schema Updates** — Added `platform` column to accounts table and `chesscom_id` to games table
- **Unique Constraints** — Changed from username-only to (username, platform) unique constraint
- **Query Language Enhancements** — Added `account_id` and `platform` filtering support
- **Natural Language Search** — Enhanced to understand and apply platform context

### API Changes
- **New Endpoints:**
  - `POST /auth/chesscom/add` — Add Chess.com account
  - `POST /sync/chesscom/start/{username}` — Start Chess.com sync
  - `GET /sync/chesscom/status/{username}` — Check sync status
  - `POST /sync/chesscom/stop/{username}` — Stop sync
- **Updated Endpoints:**
  - `POST /cql` — Now accepts `account_id` and `platform` parameters
  - `POST /ask` — Now accepts `account_id` and `platform` parameters

---

## 📦 Database Migration

The database schema has been automatically migrated to support multi-platform accounts:
- `accounts` table: Added `platform` column (default: 'lichess')
- `games` table: Added `chesscom_id` column for Chess.com game identifiers
- Unique index: Changed from `username` to `(username, platform)`

**Note:** Existing accounts will default to 'lichess' platform. No manual migration required.

---

## 🚀 Getting Started with Chess.com

1. **Add Chess.com Account:**
   - Click "Add Account" in the Accounts panel
   - Select "Chess.com" from the platform selection
   - Enter your Chess.com username
   - Click "Add Account"

2. **Sync Games:**
   - Select your Chess.com account from the dropdown
   - Click "Sync Games" to import your Chess.com games

3. **Query Games:**
   - Use natural language: "Show me my Chess.com wins"
   - Or use CQL with account filtering

---

## 📝 Example Queries

### Multi-Platform Queries
```
# Show all games from Lichess account
"Show me my Lichess games"

# Show all games from Chess.com account  
"Show me my Chess.com wins"

# Filter by specific account
Select account → Query runs automatically filtered to that account
```

---

## ⚠️ Breaking Changes

- **Account Selection:** The account selector now uses account IDs internally. Existing code relying on username-only filtering may need updates.
- **API Requests:** New optional parameters `account_id` and `platform` added to query endpoints.

---

## 📦 Installation

### macOS (Apple Silicon)
1. Download `ChessQL-0.0.3-arm64.dmg`
2. Open the DMG and drag **ChessQL** to your Applications folder
3. **First launch:** Right-click the app → Open → Open (required once to bypass Gatekeeper)

---

## 📁 Upgrade Notes

- This is a drop-in replacement for v0.0.2
- Your existing database will be automatically migrated
- All existing Lichess accounts and games will be preserved
- Simply replace the old app with the new version

---

**Full Changelog:** [v0.0.2...v0.0.3](https://github.com/your-repo/chessql/compare/v0.0.2...v0.0.3)

---

---

# ChessQL v1.0.1 — Bug Fixes 🔧

**Release Date:** January 14, 2026

This patch release addresses several bugs and improves overall stability.

---

## 🐛 Bug Fixes

### Pawn Capture Detection Fix
- **Fixed:** Pawn capture analysis now correctly detects left-direction captures (e.g., `exd4`)
- Previously, only right-direction captures (e.g., `dxe4`) were detected due to a missing `abs()` check on file difference
- This fix improves accuracy for CQL queries involving pawn exchanges (e.g., "pawn exchanged before move N")

### Server Startup Conflict Resolution
- **Fixed:** App now checks if the ChessQL server is already running on port 9090 before starting
- Prevents duplicate server instances and port conflicts
- Startup script automatically terminates any existing process on port 9090

### UI Modal Display Fix
- **Fixed:** OpenAI API key modal no longer briefly flashes on app startup
- Modal is now properly hidden by default until explicitly triggered

---

## ✨ New Features

### Full Sync Option
- **New:** Added "Full Sync" functionality for Lichess game imports
- Allows complete re-sync by deleting existing games before importing
- Useful when you want to start fresh or resolve sync inconsistencies

---

## 📦 Installation

### macOS (Apple Silicon)
1. Download `ChessQL-1.0.1-arm64.dmg`
2. Open the DMG and drag **ChessQL** to your Applications folder
3. **First launch:** Right-click the app → Open → Open (required once to bypass Gatekeeper)

---

## 📁 Upgrade Notes

- This is a drop-in replacement for v1.0.0
- Your existing database and settings will be preserved
- Simply replace the old app with the new version

---

**Full Changelog:** [v1.0.0...v1.0.1](https://github.com/your-repo/chessql/compare/v1.0.0...v1.0.1)

---
---

# ChessQL v1.0.0 — Initial Release 🎉

**Release Date:** January 4, 2026

ChessQL is a powerful desktop application for chess enthusiasts who want to analyze, search, and explore their game collections using advanced query techniques.

---

## ✨ Features

### 🔐 Lichess Integration
- **Secure OAuth2 Authentication** — Connect your Lichess account using industry-standard PKCE flow
- **Game Import** — Automatically fetch and store your games from Lichess
- **Reference Player Support** — Track specific players for focused analysis

### 🔍 Chess Query Language (CQL)
- **Pattern Matching** — Search for specific positions, piece configurations, and tactical patterns
- **Advanced Filters** — Filter games by result, date, opening, and more
- **PGN Export** — Export matching games in standard PGN format

### 🤖 AI-Powered Natural Language Search
- **Ask in Plain English** — Query your games using natural language (e.g., "Show me games where I sacrificed a knight")
- **OpenAI Integration** — Powered by GPT for intelligent query translation
- **Secure Key Storage** — API key cached locally for convenience

### 🖥️ Desktop Experience
- **Native Application** — Runs as a standalone desktop app (no browser required)
- **Dark Theme** — Easy on the eyes during long analysis sessions
- **Responsive UI** — Clean, modern interface built with Electron

---

## 📦 Installation

### macOS (Apple Silicon)
1. Download `ChessQL-1.0.0-arm64.dmg`
2. Open the DMG and drag **ChessQL** to your Applications folder
3. **First launch:** Right-click the app → Open → Open (required once to bypass Gatekeeper)

---

## ⚙️ Requirements

| Requirement | Details |
|-------------|---------|
| **Operating System** | macOS (Apple Silicon M1/M2/M3/M4) |
| **Internet** | Required for Lichess sync |
| **OpenAI API Key** | Optional — enables natural language search |

---

## 🚀 Getting Started

1. **Launch ChessQL** from your Applications folder
2. **Connect Lichess** — Click "Authenticate with Lichess" and authorize the app
3. **Import Games** — Enter your Lichess username and click "Import Games"
4. **Start Searching** — Use CQL patterns or natural language queries to explore your games

### Example CQL Queries
```
# Find games with a queen sacrifice
cql() piece q on [a-h][1-8] capture

# Find checkmates with a knight
cql() mate piece n attacks k
```

### Example Natural Language Queries
> "Show me games where I castled queenside"  
> "Find games where my opponent blundered a piece"  
> "Games with a bishop pair in the endgame"

---

## 📁 Data Storage

ChessQL stores your data in:
```
~/Library/Application Support/ChessQL/
├── chessql.db      # Game database
└── .env            # OpenAI API key
```

---

## 🐛 Known Issues

- **Gatekeeper Warning** — Since this release is not code-signed, macOS will show a security warning on first launch. This is expected behavior for unsigned apps.
- **Intel Macs** — This release targets Apple Silicon only. Intel Mac support coming soon.

---

## 🙏 Acknowledgments

- [Lichess](https://lichess.org) — For their excellent open API
- [CQL](http://www.gadycosteff.com/cql/) — Chess Query Language specification
- [OpenAI](https://openai.com) — Natural language processing

---

**Full Changelog:** Initial release

