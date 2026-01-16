"""
Chess PGN Database Module
Handles SQLite database operations for storing and retrieving chess games.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime


class ChessDatabase:
    """SQLite database handler for chess PGN files."""
    
    def __init__(self, db_path: str = "chess_games.db"):
        """Initialize the database connection and create tables if they don't exist."""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create the database and tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create accounts table for Lichess authentication
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    access_token TEXT NOT NULL,
                    token_expires_at INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_sync_at TIMESTAMP,
                    last_game_at INTEGER,
                    games_count INTEGER DEFAULT 0
                )
            """)
            
            # Create index for accounts
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_username ON accounts(username)")
            
            # Create games table with tags as columns and moves in one column
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    lichess_id TEXT,
                    pgn_text TEXT NOT NULL,
                    moves TEXT NOT NULL,
                    white_player TEXT,
                    black_player TEXT,
                    result TEXT,
                    date_played TEXT,
                    event TEXT,
                    site TEXT,
                    round TEXT,
                    eco_code TEXT,
                    opening TEXT,
                    time_control TEXT,
                    white_elo TEXT,
                    black_elo TEXT,
                    variant TEXT,
                    termination TEXT,
                    white_result TEXT,
                    black_result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            """)
            
            # Migration: Add lichess_id column if it doesn't exist (for existing databases)
            cursor.execute("PRAGMA table_info(games)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'lichess_id' not in columns:
                cursor.execute("ALTER TABLE games ADD COLUMN lichess_id TEXT")
            
            # Migration: Add speed column if it doesn't exist (bullet/blitz/rapid/classical)
            if 'speed' not in columns:
                cursor.execute("ALTER TABLE games ADD COLUMN speed TEXT")
            
            # Create index for lichess_id for fast duplicate checking
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_lichess_id ON games(lichess_id)")
            
            # Create index for speed for filtering by game type
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_speed ON games(speed)")
            
            # Create captures table for detailed capture information
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS captures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER,
                    move_number INTEGER,
                    side TEXT NOT NULL,
                    capturing_piece TEXT NOT NULL,
                    captured_piece TEXT NOT NULL,
                    from_square TEXT,
                    to_square TEXT,
                    move_notation TEXT,
                    piece_value INTEGER,
                    captured_value INTEGER,
                    is_exchange BOOLEAN,
                    is_sacrifice BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (game_id) REFERENCES games (id)
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_white_player ON games(white_player)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_black_player ON games(black_player)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_result ON games(result)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_eco_code ON games(eco_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_played ON games(date_played)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_event ON games(event)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_variant ON games(variant)")
            
            conn.commit()
    
    def insert_game(self, pgn_data: Dict[str, Any], account_id: Optional[int] = None) -> int:
        """Insert a single game into the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Calculate player results
            result = pgn_data.get('result', '')
            white_result = self._calculate_player_result(result, 'white')
            black_result = self._calculate_player_result(result, 'black')
            
            cursor.execute("""
                INSERT INTO games (
                    account_id, lichess_id, pgn_text, moves, white_player, black_player, 
                    result, date_played, event, site, round, eco_code, opening, time_control,
                    white_elo, black_elo, variant, termination, white_result, black_result, speed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                account_id,
                pgn_data.get('lichess_id'),
                pgn_data.get('pgn_text', ''),
                pgn_data.get('moves', ''),
                pgn_data.get('white_player', ''),
                pgn_data.get('black_player', ''),
                pgn_data.get('result', ''),
                pgn_data.get('date_played', ''),
                pgn_data.get('event', ''),
                pgn_data.get('site', ''),
                pgn_data.get('round', ''),
                pgn_data.get('eco_code', ''),
                pgn_data.get('opening', ''),
                pgn_data.get('time_control', ''),
                pgn_data.get('white_elo', ''),
                pgn_data.get('black_elo', ''),
                pgn_data.get('variant', ''),
                pgn_data.get('termination', ''),
                white_result,
                black_result,
                pgn_data.get('speed', ''),
            ))
            
            game_id = cursor.lastrowid
            conn.commit()
            return game_id
    
    def game_exists(self, lichess_id: str) -> bool:
        """Check if a game with the given Lichess ID already exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM games WHERE lichess_id = ?", (lichess_id,))
            return cursor.fetchone() is not None
    
    def get_latest_game_timestamp(self, account_id: int) -> Optional[int]:
        """Get the timestamp of the latest game for an account (for incremental sync)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(CAST(
                    CASE 
                        WHEN site LIKE 'https://lichess.org/%' 
                        THEN substr(site, 22) 
                        ELSE NULL 
                    END AS TEXT
                )) as latest_id
                FROM games 
                WHERE account_id = ?
            """, (account_id,))
            # This is a simplified approach - we'll use last_game_at from accounts table instead
            return None
    
    def get_games_count_by_account(self, account_id: int) -> int:
        """Get the count of games for a specific account."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM games WHERE account_id = ?", (account_id,))
            return cursor.fetchone()[0]
    
    def delete_games_by_account(self, account_id: int) -> int:
        """Delete all games and their captures for a specific account. Returns count of deleted games."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # First, delete captures for all games belonging to this account
            cursor.execute("""
                DELETE FROM captures WHERE game_id IN (
                    SELECT id FROM games WHERE account_id = ?
                )
            """, (account_id,))
            
            # Then delete the games
            cursor.execute("DELETE FROM games WHERE account_id = ?", (account_id,))
            deleted_count = cursor.rowcount
            
            conn.commit()
            return deleted_count
    
    def _calculate_player_result(self, result: str, player_color: str) -> str:
        """Calculate the result for a specific player (win/loss/draw)."""
        if result == '1-0':
            return 'win' if player_color == 'white' else 'loss'
        elif result == '0-1':
            return 'loss' if player_color == 'white' else 'win'
        elif result == '1/2-1/2':
            return 'draw'
        else:
            return 'unknown'
    
    def insert_captures(self, game_id: int, captures: List[Dict[str, Any]]) -> int:
        """Insert detailed capture information for a game."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for capture in captures:
                cursor.execute("""
                    INSERT INTO captures (
                        game_id, move_number, side, capturing_piece, captured_piece,
                        from_square, to_square, move_notation, piece_value, captured_value,
                        is_exchange, is_sacrifice
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    game_id,
                    capture.get('move_number', 0),
                    capture.get('side', ''),
                    capture.get('capturing_piece', ''),
                    capture.get('captured_piece', ''),
                    capture.get('from_square', ''),
                    capture.get('to_square', ''),
                    capture.get('move_notation', ''),
                    capture.get('piece_value', 0),
                    capture.get('captured_value', 0),
                    capture.get('is_exchange', False),
                    capture.get('is_sacrifice', False)
                ))
            
            conn.commit()
            return len(captures)
    
    def search_moves(self, pattern: str) -> List[Dict[str, Any]]:
        """Search moves using pattern (converted to LIKE for SQLite)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Convert regex-like pattern to SQL LIKE pattern
            like_pattern = pattern.replace('.*', '%').replace('.', '_')
            cursor.execute("SELECT * FROM games WHERE moves LIKE ?", (f"%{like_pattern}%",))
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def execute_sql_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a raw SQL query and return results."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            try:
                cursor.execute(query)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                print(f"SQL Error: {e}")
                return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get total games count
            cursor.execute("SELECT COUNT(*) FROM games")
            total_games = cursor.fetchone()[0]
            
            # Get unique players count
            cursor.execute("SELECT COUNT(DISTINCT white_player) + COUNT(DISTINCT black_player) FROM games")
            unique_players = cursor.fetchone()[0]
            
            # Get games by result
            cursor.execute("SELECT result, COUNT(*) FROM games GROUP BY result")
            results = dict(cursor.fetchall())
            
            return {
                'total_games': total_games,
                'unique_players': unique_players,
                'results': results
            }
    
