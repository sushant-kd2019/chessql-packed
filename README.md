# ChessQL 🎯♟️

**A powerful desktop application for chess enthusiasts to analyze, search, and explore their game collections using advanced query techniques.**

ChessQL combines SQL-like queries with chess-specific patterns, plus AI-powered natural language search—so you can find exactly the games you're looking for.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey.svg)

---

## ✨ What Can ChessQL Do?

| Feature | Description |
|---------|-------------|
| 🔐 **Lichess Sync** | Connect your account and import all your games automatically |
| 🔍 **CQL Queries** | SQL + chess patterns for precise searches |
| 🤖 **Natural Language** | Ask questions in plain English using AI |
| ♕ **Piece Tracking** | Find sacrifices, exchanges, captures, and promotions |
| 📊 **Game Analytics** | Filter by ELO, time control, date, opening, and more |
| 🎮 **Game Viewer** | Replay games move-by-move with visual board |

---

## 📦 Installation

### Download the App

Download `ChessQL-1.0.0-arm64.dmg` from the [Releases](../../releases) page.

### First Launch (macOS)

Since the app isn't code-signed, macOS will show a security warning:

1. Open the DMG and drag **ChessQL** to Applications
2. Right-click the app → **Open** → **Open**
3. This only needs to be done once

---

## 🚀 Quick Start

1. **Launch ChessQL**
2. **Connect Lichess** — Click "Authenticate with Lichess"
3. **Import Games** — Enter your username and click "Import Games"
4. **Search!** — Use CQL or natural language to explore your games

---

## 📖 Query Language Guide

ChessQL supports three types of queries:

1. **SQL Queries** — Standard SQL on game metadata
2. **Chess Patterns** — Special syntax for chess events
3. **Regex Patterns** — Search move notation directly

---

## 🎯 CQL Query Examples

### Basic SQL Queries

```sql
-- All games by a specific player
SELECT * FROM games WHERE white_player = 'magnus'

-- Games with a specific result
SELECT * FROM games WHERE result = '1-0'

-- Games by opening code
SELECT * FROM games WHERE eco_code = 'B90'

-- Count total games
SELECT COUNT(*) FROM games

-- Games per player
SELECT white_player, COUNT(*) as games FROM games GROUP BY white_player
```

### Player Result Patterns

Find games based on who won, lost, or drew:

```sql
-- Games where a player won
SELECT * FROM games WHERE (magnus won)

-- Games where a player lost
SELECT * FROM games WHERE (hikaru lost)

-- Games that ended in a draw
SELECT * FROM games WHERE (player drew)

-- Count wins
SELECT COUNT(*) FROM games WHERE (lecorvus won)
```

### Piece Sacrifices

Find games with material sacrifices:

```sql
-- Any queen sacrifice
SELECT * FROM games WHERE (queen sacrificed)

-- Knight sacrifices
SELECT * FROM games WHERE (knight sacrificed)

-- Bishop sacrifices
SELECT * FROM games WHERE (bishop sacrificed)

-- Rook sacrifices
SELECT * FROM games WHERE (rook sacrificed)

-- Pawn sacrifices (gambits)
SELECT * FROM games WHERE (pawn sacrificed)
```

### Player-Specific Sacrifices

```sql
-- Games where Magnus sacrificed his queen
SELECT * FROM games WHERE (magnus queen sacrificed)

-- Games where opponent sacrificed their queen
SELECT * FROM games WHERE (opponent queen sacrificed)

-- Player won after sacrificing queen
SELECT * FROM games WHERE (lecorvus won) AND (lecorvus queen sacrificed)

-- Player lost despite opponent's queen sacrifice
SELECT * FROM games WHERE (lecorvus won) AND (opponent queen sacrificed)
```

### Piece Exchanges

Find games with piece exchanges (piece for piece):

```sql
-- Queen exchanges
SELECT * FROM games WHERE (queen exchanged)

-- Knight exchanges
SELECT * FROM games WHERE (knight exchanged)

-- Early pawn exchanges (opening theory)
SELECT * FROM games WHERE (pawn exchanged before move 10)

-- Late rook exchanges (endgame)
SELECT * FROM games WHERE (rook exchanged after move 30)
```

### Specific Captures

```sql
-- Queen takes queen
SELECT * FROM games WHERE (queen captured queen)

-- Knight takes rook (winning exchange)
SELECT * FROM games WHERE (knight captured rook)

-- Pawn takes queen (promotion aftermath or blunder)
SELECT * FROM games WHERE (pawn captured queen)

-- Bishop captures knight
SELECT * FROM games WHERE (bishop captured knight)
```

### Pawn Promotions

```sql
-- Any queen promotion
SELECT * FROM games WHERE (pawn promoted to queen)

-- Knight underpromotion
SELECT * FROM games WHERE (pawn promoted to knight)

-- Rook underpromotion
SELECT * FROM games WHERE (pawn promoted to rook)

-- Bishop underpromotion
SELECT * FROM games WHERE (pawn promoted to bishop)

-- Double queen promotion in one game
SELECT * FROM games WHERE (pawn promoted to queen x 2)

-- Triple promotion (rare!)
SELECT * FROM games WHERE (pawn promoted to queen x 3)

-- Player-specific promotions
SELECT * FROM games WHERE (lecorvus won) AND (pawn promoted to queen)
```

### Move Timing Conditions

```sql
-- Early queen sacrifice (opening)
SELECT * FROM games WHERE (queen sacrificed before move 15)

-- Late knight sacrifice (endgame)
SELECT * FROM games WHERE (knight sacrificed after move 30)

-- Opening pawn exchanges
SELECT * FROM games WHERE (pawn exchanged before move 10)

-- Middlegame bishop sacrifice
SELECT * FROM games WHERE (bishop sacrificed after move 10) 
    AND (bishop sacrificed before move 30)
```

### Time Control / Game Speed

```sql
-- Bullet games only
SELECT * FROM games WHERE speed = 'bullet'

-- Blitz games
SELECT * FROM games WHERE speed = 'blitz'

-- Rapid games
SELECT * FROM games WHERE speed = 'rapid'

-- Classical (long) games
SELECT * FROM games WHERE speed = 'classical'

-- Ultra-bullet games
SELECT * FROM games WHERE speed = 'ultraBullet'

-- Player wins in blitz
SELECT * FROM games WHERE (lecorvus won) AND speed = 'blitz'

-- Queen sacrifices in rapid games
SELECT * FROM games WHERE (queen sacrificed) AND speed = 'rapid'

-- Games by speed category
SELECT speed, COUNT(*) as count FROM games GROUP BY speed
```

### ELO Rating Filters

```sql
-- High-rated games (white over 2000)
SELECT * FROM games WHERE CAST(white_elo AS INTEGER) > 2000

-- Player's games when rated over 1500
SELECT * FROM games WHERE 
    (white_player = 'lecorvus' AND CAST(white_elo AS INTEGER) > 1500) 
    OR (black_player = 'lecorvus' AND CAST(black_elo AS INTEGER) > 1500)

-- Games sorted by rating
SELECT * FROM games ORDER BY CAST(white_elo AS INTEGER) DESC
```

### Sorting & Limiting

```sql
-- Most recent games first
SELECT * FROM games ORDER BY date_played DESC

-- Top 10 highest-rated games
SELECT * FROM games ORDER BY CAST(white_elo AS INTEGER) DESC LIMIT 10

-- Games grouped by opening
SELECT eco_code, opening, COUNT(*) as games 
FROM games 
GROUP BY eco_code 
ORDER BY games DESC

-- Player's wins sorted by date
SELECT * FROM games WHERE (lecorvus won) ORDER BY date_played DESC
```

### Combined Queries

```sql
-- Wins with queen sacrifices
SELECT * FROM games WHERE (lecorvus won) AND (queen sacrificed)

-- Losses despite opponent blundering their queen
SELECT * FROM games WHERE (lecorvus lost) AND (opponent queen sacrificed)

-- High-rated blitz wins with sacrifices
SELECT * FROM games WHERE 
    (lecorvus won) 
    AND speed = 'blitz' 
    AND (queen sacrificed)
    AND CAST(white_elo AS INTEGER) > 1500

-- Draw where both sides had promotions
SELECT * FROM games WHERE 
    (player drew) 
    AND (pawn promoted to queen x 2)
```

### Regex Move Patterns

Search directly in move notation using regex:

```sql
-- Games starting with 1. e4
/1\. e4/

-- Games with Sicilian Defense (e4 c5)
/e4.*c5/

-- Games with kingside castling
/O-O/

-- Games with queenside castling
/O-O-O/

-- Scholar's mate pattern
/Qh5.*Qxf7/

-- Games with check on move
/\+/

-- Games ending in checkmate
/#/

-- Knight to f3 followed by knight to c6
/Nf3.*Nc6/
```

---

## 🤖 Natural Language Examples

Just ask questions in plain English! The AI converts them to CQL automatically.

### Basic Questions

| Natural Language | What It Finds |
|-----------------|---------------|
| "Show me games where I won" | Your victories |
| "Find games where I lost" | Your defeats |
| "Games that ended in a draw" | Drawn games |
| "How many games have I played?" | Total game count |

### Sacrifice Queries

| Natural Language | What It Finds |
|-----------------|---------------|
| "Show me games where I sacrificed my queen" | Your queen sacrifices |
| "Find games where opponent sacrificed their queen" | Opponent's queen sacs |
| "Games where I won after sacrificing a knight" | Winning knight sacs |
| "How many times did I sacrifice a bishop?" | Bishop sacrifice count |
| "Show me queen sacrifices that I lost" | Failed queen sacrifices |

### Exchange & Capture Queries

| Natural Language | What It Finds |
|-----------------|---------------|
| "Find games with early pawn exchanges" | Opening pawn trades |
| "Games where queens were exchanged" | Queen trade games |
| "Show me games where my knight took a rook" | Knight forks? |
| "Find bishop exchanges" | Bishop pair trades |

### Promotion Queries

| Natural Language | What It Finds |
|-----------------|---------------|
| "Games where I promoted a pawn" | Your promotion games |
| "Find games with knight underpromotion" | Rare underpromotions |
| "Show me games where I promoted to queen twice" | Double promotion games |
| "Games with multiple promotions" | Pawn-heavy endgames |

### Time Control Queries

| Natural Language | What It Finds |
|-----------------|---------------|
| "Show me my blitz games" | 3-5 minute games |
| "How many bullet games did I win?" | Fast game wins |
| "Find my rapid losses" | 10-15 min losses |
| "Classical games where I sacrificed my queen" | Long game sacrifices |

### Rating Queries

| Natural Language | What It Finds |
|-----------------|---------------|
| "Games where I was rated over 1500" | Higher-rated games |
| "Show my wins when rated above 1800" | Strong performance |
| "Find games against higher-rated opponents" | Underdog victories |

### Complex Queries

| Natural Language | What It Finds |
|-----------------|---------------|
| "Games where I won after sacrificing queen in blitz" | Clutch blitz sacrifices |
| "Show me losses where I had a queen sacrifice before move 20" | Early failed gambits |
| "Find games where opponent sacrificed queen but I still lost" | Comeback losses |
| "How many times did I promote to queen twice in one game?" | Double promotion count |
| "Rapid games where I exchanged queens and won" | Endgame victories |

### Statistical Queries

| Natural Language | What It Finds |
|-----------------|---------------|
| "Count my wins with queen sacrifices" | Sacrifice win rate |
| "How many games did I play as white?" | Color distribution |
| "Show games grouped by opening" | Opening repertoire |
| "What's my most played time control?" | Preferred speed |

---

## 🗄️ Database Schema

ChessQL stores games with these fields:

| Field | Description |
|-------|-------------|
| `white_player` | White player's username |
| `black_player` | Black player's username |
| `result` | Game result (1-0, 0-1, 1/2-1/2) |
| `white_result` | White's outcome (win/loss/draw) |
| `black_result` | Black's outcome (win/loss/draw) |
| `date_played` | Date of the game |
| `eco_code` | Opening ECO code (e.g., B90) |
| `opening` | Opening name |
| `speed` | Time control category |
| `white_elo` | White's rating |
| `black_elo` | Black's rating |
| `time_control` | Exact time control |
| `termination` | How game ended |
| `site` | Game URL |
| `moves` | Full move notation |

---

## 🏗️ Project Structure

```
chessql-packed/
├── backend/          # Python FastAPI server
│   ├── server.py     # REST API endpoints
│   ├── query_language.py  # CQL parser
│   ├── natural_language_search.py  # AI query conversion
│   └── database.py   # SQLite operations
├── ui/               # Electron desktop app
│   ├── main-fixed.js # Electron main process
│   ├── app.js        # UI logic
│   └── index.html    # Interface
└── scripts/          # Build & run scripts
```

---

## 🛠️ Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm

### Setup

```bash
# Clone and setup
git clone <repo-url>
cd chessql-packed
./scripts/setup.sh
```

### Run in Development

```bash
# Terminal 1: Start backend
./scripts/start-backend.sh

# Terminal 2: Start UI
./scripts/start-ui.sh

# Or both at once:
./scripts/start-all.sh
```

### Build for Distribution

```bash
# Build macOS app
./scripts/build-app.sh --mac

# Output: ui/dist/ChessQL-1.0.0-arm64.dmg
```

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/cql` | POST | Execute CQL queries |
| `/ask` | POST | Natural language queries |
| `/health` | GET | Health check |
| `/examples` | GET | Example queries |
| `/accounts/*` | Various | Lichess account management |
| `/sync/*` | Various | Game synchronization |
| `/settings/openai-key/*` | Various | API key management |

---

## 📁 Data Location

ChessQL stores data in:

```
~/Library/Application Support/ChessQL/
├── chessql.db      # Game database
└── .env            # API keys
```

---

## 🤝 Contributing

Contributions welcome! Please open an issue first to discuss changes.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [Lichess](https://lichess.org) — Open chess platform & API
- [OpenAI](https://openai.com) — Natural language processing
- [Electron](https://electronjs.org) — Desktop framework
- [FastAPI](https://fastapi.tiangolo.com) — Python API framework
