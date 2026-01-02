# ChessQL Monorepo

A complete chess game analysis system combining a Python backend with an Electron desktop UI.

## Structure

```
chessql-packed/
├── backend/          # ChessQL Python backend (FastAPI server, CLI, database)
├── ui/               # ChessQL Electron desktop application
└── scripts/          # Convenience scripts for setup and running
```

## Quick Start

### 1. Setup

```bash
# Run the setup script to install all dependencies
./scripts/setup.sh
```

Or manually:

```bash
# Backend (Python)
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# UI (Node.js)
cd ../ui
npm install
```

### 2. Start the Backend Server

```bash
./scripts/start-backend.sh
# Or manually:
cd backend && source .venv/bin/activate && python start_server.py
```

The API server will start on http://localhost:9090

### 3. Start the Desktop UI

```bash
./scripts/start-ui.sh
# Or manually:
cd ui && npm start
```

### 4. Start Everything (Backend + UI)

```bash
./scripts/start-all.sh
```

## Components

### Backend (`backend/`)

Python-based chess game database with:
- **FastAPI REST API** - `/cql` and `/ask` endpoints for querying games
- **Natural Language Search** - AI-powered query generation
- **ChessQL Query Language** - SQL + chess-specific patterns
- **CLI Interface** - Command-line tool for database operations
- **Lichess Integration** - OAuth and game syncing

See [backend/README.md](backend/README.md) for detailed documentation.

### UI (`ui/`)

Electron desktop application with:
- **Search Interface** - Natural language or ChessQL queries
- **Game Thumbnails** - Visual board positions
- **Game Viewer** - Move-by-move navigation
- **Account Management** - Lichess OAuth integration

See [ui/README.md](ui/README.md) for detailed documentation.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/cql` | POST | Execute ChessQL queries |
| `/ask` | POST | Natural language queries |
| `/health` | GET | Health check |
| `/examples` | GET | Example queries |
| `/accounts/*` | Various | Account management |

## Example Queries

### Natural Language
- "Show me games where lecorvus won"
- "Find games where queen was sacrificed"
- "Count games where pawn promoted to queen x 2"

### ChessQL
- `SELECT * FROM games WHERE (lecorvus won)`
- `SELECT * FROM games WHERE (queen sacrificed)`
- `SELECT COUNT(*) FROM games WHERE (pawn promoted to queen x 2)`

## Development

### Project Origins

This monorepo combines two previously separate repositories:
- `chessql` - The Python backend
- `chessql-ui` - The Electron frontend

Full commit history from both projects has been preserved using git subtree.

### Making Changes

Each component can be developed independently:

```bash
# Work on backend
cd backend
source .venv/bin/activate
# make changes...

# Work on UI
cd ui
npm run dev
# make changes...
```

## License

MIT License
