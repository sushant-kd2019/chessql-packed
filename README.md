# ChessQL - Chess PGN Database Query Language

A Python-based system for storing, ingesting, and querying chess games in PGN format using SQLite with advanced chess analysis capabilities.

## Features

- **SQLite Database**: Efficient storage of chess games with metadata and capture analysis
- **PGN Ingestion**: Parse and import PGN files into the database with reference player support
- **Natural Language Queries**: Ask questions in plain English using AI-powered query generation
- **Chess-Specific Queries**: Find sacrifices, exchanges, pawn promotions, and other chess events
- **Multiple Promotion Support**: Query for games with multiple promotions using `x N` format
- **CLI Interface**: Command-line tool for database operations
- **REST API**: FastAPI server with `/cql` and `/query` endpoints
- **Interactive Mode**: Interactive search and exploration

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Make the CLI executable:
```bash
chmod +x cli.py
```

## Usage

### 1. Ingest PGN Files

Ingest a single PGN file with default reference player:
```bash
python cli.py ingest games.pgn
```

Ingest with custom reference player for sacrifice analysis:
```bash
python cli.py --player magnus_carlsen ingest games.pgn
```

Ingest all PGN files in a directory:
```bash
python cli.py --player hikaru ingest /path/to/pgn/files/
```

### 2. Query Games

#### Natural Language Queries (Recommended)
```bash
python cli.py ask "Show me games where lecorvus won"
python cli.py ask "Find games where queen was sacrificed"
python cli.py ask "Count games where lecorvus promoted to queen x 2"
python cli.py ask "Show games where lecorvus was rated over 1500"
```

#### SQL Queries
```bash
python cli.py query "SELECT * FROM games WHERE white_player = 'lecorvus'"
python cli.py query "SELECT COUNT(*) FROM games WHERE (lecorvus won)"
```

#### Chess-Specific Patterns
```bash
python cli.py query "SELECT * FROM games WHERE (queen sacrificed)"
python cli.py query "SELECT * FROM games WHERE (pawn promoted to queen x 2)"
python cli.py query "SELECT * FROM games WHERE (lecorvus won) AND (queen exchanged)"
```

### 3. Interactive Mode

Start interactive search:
```bash
python cli.py
```

### 4. Database Statistics

View database statistics:
```bash
python cli.py stats
```

### 5. Show Game Details

View detailed information about a specific game:
```bash
python cli.py show 1
```

### 6. REST API Server

Start the FastAPI server:
```bash
python start_server.py
```

Or manually:
```bash
python server.py
```

The server provides two main endpoints:
- **`/cql`**: Execute ChessQL queries (SQL + chess patterns)
- **`/query`**: Execute natural language queries

API Documentation: http://localhost:9090/docs

### API Endpoints

#### POST `/cql`
Execute ChessQL queries (SQL + chess patterns).

**Request Body:**
```json
{
  "query": "SELECT COUNT(*) FROM games WHERE (lecorvus won)",
  "limit": 100
}
```

**Response:**
```json
{
  "success": true,
  "results": [{"COUNT(*)": 825}],
  "count": 1,
  "query": "SELECT COUNT(*) FROM games WHERE (lecorvus won)",
  "error": null
}
```

#### POST `/query`
Execute natural language queries.

**Request Body:**
```json
{
  "question": "Show me games where lecorvus won",
  "limit": 10
}
```

**Response:**
```json
{
  "success": true,
  "results": [...],
  "count": 10,
  "query": "Show me games where lecorvus won",
  "error": null
}
```

#### GET `/health`
Health check endpoint.

#### GET `/examples`
Get example queries for both endpoints.

### API Usage Examples

```bash
# ChessQL query
curl -X POST "http://localhost:9090/cql" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT COUNT(*) FROM games WHERE (queen sacrificed)", "limit": 5}'

# Natural language query
curl -X POST "http://localhost:9090/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Find games where lecorvus promoted to queen x 2", "limit": 3}'

# Health check
curl -X GET "http://localhost:9090/health"

# Get examples
curl -X GET "http://localhost:9090/examples"
```

## Query Language

### Natural Language Queries (Recommended)
Ask questions in plain English - the AI will convert them to SQL:

**Player Results:**
- `"Show me games where lecorvus won"`
- `"Count games where magnus_carlsen lost"`
- `"Find games where hikaru drew"`

**Chess Events:**
- `"Find games where queen was sacrificed"`
- `"Show games where knight was exchanged"`
- `"Count games where pawn was promoted to queen"`

**Multiple Events:**
- `"Find games where lecorvus promoted to queen x 2"`
- `"Count games where lecorvus promoted to knight x 3"`
- `"Show games where pawn was promoted to rook x 1"`

**ELO Ratings:**
- `"Show games where lecorvus was rated over 1500"`
- `"Find games where magnus_carlsen was rated under 2000"`

**Combined Queries:**
- `"Find games where lecorvus won and sacrificed queen"`
- `"Count games where lecorvus promoted to queen twice and won"`

### Chess-Specific Patterns
Use these patterns in SQL queries for chess events:

**Player Results:**
- `(player_name won)` - Player won the game
- `(player_name lost)` - Player lost the game
- `(player_name drew)` - Game was a draw

**Piece Events:**
- `(queen sacrificed)` - Queen was sacrificed
- `(knight exchanged)` - Knight was exchanged
- `(pawn promoted to queen)` - Pawn promoted to queen
- `(pawn promoted to queen x 2)` - Pawn promoted to queen twice

**Captures:**
- `(queen captured rook)` - Queen captured rook
- `(knight captured bishop)` - Knight captured bishop

### SQL Queries
Direct SQL queries for advanced users:

```sql
-- Basic queries
SELECT * FROM games WHERE white_player = 'lecorvus'
SELECT COUNT(*) FROM games WHERE (lecorvus won)

-- Chess events
SELECT * FROM games WHERE (queen sacrificed)
SELECT * FROM games WHERE (pawn promoted to queen x 2)

-- Combined conditions
SELECT * FROM games WHERE (lecorvus won) AND (queen sacrificed)
SELECT * FROM games WHERE (lecorvus won) AND (pawn promoted to queen x 2)
```

### Available Fields
- `white_player` - White player name
- `black_player` - Black player name
- `result` - Game result (1-0, 0-1, 1/2-1/2)
- `white_result` - White player result (win/loss/draw)
- `black_result` - Black player result (win/loss/draw)
- `date_played` - Game date
- `event` - Tournament/event name
- `site` - Game location
- `round` - Round number
- `eco_code` - ECO opening code
- `opening` - Opening name
- `time_control` - Time control
- `white_elo` - White player ELO rating
- `black_elo` - Black player ELO rating

## Reference Player and Multi-Player Support

### Reference Player Concept
The **reference player** is used during ingestion to analyze chess events from a specific player's perspective:

- **Sacrifice Analysis**: Determines if a queen capture is a sacrifice or exchange
- **Event Context**: Provides context for chess events during analysis
- **Ingestion Parameter**: Set during PGN ingestion with `--player` option

### Multi-Player Database Support
The system fully supports games from multiple players in the same database:

- **Player Names**: Stored as simple text fields (`white_player`, `black_player`)
- **Flexible Queries**: Query any player by name regardless of reference player
- **Cross-Player Analysis**: Compare different players' performance
- **Independent Analysis**: Reference player only affects ingestion, not querying

### Usage Examples
```bash
# Ingest games from different players
python cli.py --player lecorvus ingest lecorvus_games.pgn
python cli.py --player magnus_carlsen ingest magnus_games.pgn
python cli.py --player hikaru ingest hikaru_games.pgn

# Query any player (regardless of reference player used during ingestion)
python cli.py ask "Show me games where magnus_carlsen won"
python cli.py ask "Find games where hikaru sacrificed queen"
python cli.py ask "Count games where lecorvus promoted to queen x 2"
```

## Database Schema

### Games Table
- `id` - Primary key
- `pgn_text` - Full PGN text
- `moves` - Game moves in algebraic notation
- `white_player` - White player name
- `black_player` - Black player name
- `result` - Game result (1-0, 0-1, 1/2-1/2)
- `white_result` - White player result (win/loss/draw)
- `black_result` - Black player result (win/loss/draw)
- `date_played` - Game date
- `event` - Event name
- `site` - Game site
- `round` - Round number
- `eco_code` - ECO code
- `opening` - Opening name
- `time_control` - Time control
- `white_elo` - White player ELO rating
- `black_elo` - Black player ELO rating
- `variant` - Game variant
- `termination` - Game termination reason
- `created_at` - Import timestamp

### Captures Table
- `id` - Primary key
- `game_id` - Foreign key to games
- `move_number` - Move number
- `side` - Side that made the capture (white/black)
- `capturing_piece` - Piece that made the capture
- `captured_piece` - Piece that was captured
- `from_square` - Square the capturing piece moved from
- `to_square` - Square the capturing piece moved to
- `move_notation` - Algebraic notation of the move
- `piece_value` - Value of the capturing piece
- `captured_value` - Value of the captured piece
- `is_exchange` - Whether this was an exchange
- `is_sacrifice` - Whether this was a sacrifice
- `white_player` - White player name
- `black_player` - Black player name
- `created_at` - Import timestamp

## Examples

### Ingest Sample Data
```bash
# Create a sample PGN file
echo '[Event "Test Game"]
[Site "Test Site"]
[Date "2023.01.01"]
[Round "1"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]
[ECO "E90"]

1. e4 e5 2. Nf3 Nc6 3. d4 exd4 4. Nxd4 Nf6 5. Nc3 Bb4 6. Nxc6 bxc6 7. Bd3 d5 8. exd5 cxd5 9. O-O O-O 10. Bg5 Be6 11. Qf3 Be7 12. Rfe1 h6 13. Bxf6 Bxf6 14. Qxf6 gxf6 15. Bf5 1-0' > sample.pgn

# Ingest with default reference player
python cli.py ingest sample.pgn

# Ingest with custom reference player
python cli.py --player Player1 ingest sample.pgn
```

### Query Examples

#### Natural Language Queries
```bash
# Player results
python cli.py ask "Show me games where lecorvus won"
python cli.py ask "Count games where magnus_carlsen lost"

# Chess events
python cli.py ask "Find games where queen was sacrificed"
python cli.py ask "Show games where knight was exchanged"

# Multiple promotions
python cli.py ask "Count games where lecorvus promoted to queen x 2"
python cli.py ask "Find games where pawn was promoted to knight x 3"

# ELO ratings
python cli.py ask "Show games where lecorvus was rated over 1500"

# Combined queries
python cli.py ask "Find games where lecorvus won and sacrificed queen"
```

#### SQL Queries
```bash
# Basic queries
python cli.py query "SELECT * FROM games WHERE white_player = 'lecorvus'"
python cli.py query "SELECT COUNT(*) FROM games WHERE (lecorvus won)"

# Chess events
python cli.py query "SELECT * FROM games WHERE (queen sacrificed)"
python cli.py query "SELECT * FROM games WHERE (pawn promoted to queen x 2)"

# Combined conditions
python cli.py query "SELECT * FROM games WHERE (lecorvus won) AND (queen sacrificed)"
```

## Interactive Mode Commands

When in interactive mode (`python cli.py`):

- `help` - Show available commands
- `examples` - Show query examples
- `stats` - Show database statistics
- `ask "question"` - Ask a natural language question
- `query "SQL"` - Execute a SQL query
- `quit` or `exit` - Exit interactive mode

## Output Formats

The CLI supports multiple output formats:

- `table` (default) - Human-readable table format
- `json` - JSON format for programmatic use
- `csv` - CSV format for spreadsheet import

Example:
```bash
python cli.py query "Magnus Carlsen" --format json --limit 5
```

## Development

### Project Structure
```
chessql/
├── database.py              # SQLite database operations
├── ingestion.py             # PGN file parsing and ingestion
├── query_language.py        # Query language processor
├── natural_language_search.py # AI-powered natural language queries
├── piece_analysis.py        # Chess piece analysis and sacrifice detection
├── cli.py                   # Command-line interface
├── server.py                # FastAPI REST API server
├── start_server.py          # Server startup script
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### Key Components

1. **Database Layer** (`database.py`): SQLite operations and schema management
2. **Ingestion Layer** (`ingestion.py`): PGN parsing with reference player support
3. **Query Processing** (`query_language.py`): Chess-specific query patterns
4. **Natural Language** (`natural_language_search.py`): AI-powered query generation
5. **Chess Analysis** (`piece_analysis.py`): Sacrifice and exchange detection
6. **CLI Interface** (`cli.py`): Command-line user interface
7. **REST API** (`server.py`): FastAPI server with `/cql` and `/query` endpoints

### Adding New Features

1. **Database Schema**: Modify `database.py` to add new tables or fields
2. **Query Language**: Extend `query_language.py` to support new query types
3. **Natural Language**: Update `natural_language_search.py` prompts for new patterns
4. **Chess Analysis**: Enhance `piece_analysis.py` for new chess events
5. **CLI Commands**: Add new commands in `cli.py`
6. **Ingestion**: Enhance `ingestion.py` to parse additional PGN metadata

## License

This project is open source and available under the MIT License.
