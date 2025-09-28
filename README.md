# ChessQL - Chess PGN Database Query Language

A Python-based system for storing, ingesting, and querying chess games in PGN format using SQLite.

## Features

- **SQLite Database**: Efficient storage of chess games with metadata
- **PGN Ingestion**: Parse and import PGN files into the database
- **Query Language**: Flexible query system for searching games
- **CLI Interface**: Command-line tool for database operations
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

Ingest a single PGN file:
```bash
python cli.py ingest games.pgn
```

Ingest all PGN files in a directory:
```bash
python cli.py ingest /path/to/pgn/files/
```

### 2. Query Games

Simple text search:
```bash
python cli.py query "Magnus Carlsen"
```

SQL-like queries:
```bash
python cli.py query "SELECT * FROM games WHERE white_player = 'Magnus Carlsen'"
```

FIND queries:
```bash
python cli.py query "FIND games where result = '1-0' AND eco_code = 'E90'"
```

### 3. Interactive Mode

Start interactive search:
```bash
python cli.py search --interactive
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

## Query Language

### Simple Search
- `"Magnus Carlsen"` - Search for games involving Magnus Carlsen
- `"Sicilian Defense"` - Search for games with Sicilian Defense

### SQL-like Queries
- `SELECT * FROM games WHERE white_player = "Magnus Carlsen"`
- `SELECT * FROM games WHERE result = "1-0"`

### FIND Queries
- `FIND games where white_player = "Magnus Carlsen"`
- `FIND games where result = "1-0" AND eco_code = "E90"`
- `FIND games where opening contains "Sicilian"`
- `FIND games where date_played > "2020-01-01"`

### Available Fields
- `white_player` - White player name
- `black_player` - Black player name
- `result` - Game result (1-0, 0-1, 1/2-1/2)
- `date_played` - Game date
- `event` - Tournament/event name
- `site` - Game location
- `round` - Round number
- `eco_code` - ECO opening code
- `opening` - Opening name
- `time_control` - Time control

## Database Schema

### Games Table
- `id` - Primary key
- `pgn_text` - Full PGN text
- `white_player` - White player name
- `black_player` - Black player name
- `result` - Game result
- `date_played` - Game date
- `event` - Event name
- `site` - Game site
- `round` - Round number
- `eco_code` - ECO code
- `opening` - Opening name
- `time_control` - Time control
- `created_at` - Import timestamp

### Moves Table
- `id` - Primary key
- `game_id` - Foreign key to games
- `move_number` - Move number
- `white_move` - White's move
- `black_move` - Black's move
- `position_fen` - Position FEN (placeholder)

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

# Ingest the file
python cli.py ingest sample.pgn
```

### Query Examples
```bash
# Find all games by a specific player
python cli.py query "FIND games where white_player = 'Player1'"

# Find all wins by white
python cli.py query "FIND games where result = '1-0'"

# Find games in a specific opening
python cli.py query "FIND games where eco_code = 'E90'"

# Search for games containing "Sicilian"
python cli.py query "Sicilian"
```

## Interactive Mode Commands

When in interactive mode (`python cli.py search --interactive`):

- `help` - Show available commands
- `examples` - Show query examples
- `stats` - Show database statistics
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
├── database.py          # SQLite database operations
├── ingestion.py         # PGN file parsing and ingestion
├── query_language.py    # Query language processor
├── cli.py              # Command-line interface
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### Adding New Features

1. **Database Schema**: Modify `database.py` to add new tables or fields
2. **Query Language**: Extend `query_language.py` to support new query types
3. **CLI Commands**: Add new commands in `cli.py`
4. **Ingestion**: Enhance `ingestion.py` to parse additional PGN metadata

## License

This project is open source and available under the MIT License.
