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
            
            # Create games table with tags as columns and moves in one column
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_white_player ON games(white_player)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_black_player ON games(black_player)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_result ON games(result)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_eco_code ON games(eco_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_played ON games(date_played)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_event ON games(event)")
            
            conn.commit()
    
    def insert_game(self, pgn_data: Dict[str, Any]) -> int:
        """Insert a single game into the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO games (
                    pgn_text, moves, white_player, black_player, result, date_played,
                    event, site, round, eco_code, opening, time_control,
                    white_elo, black_elo, variant, termination
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
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
                pgn_data.get('termination', '')
            ))
            
            game_id = cursor.lastrowid
            conn.commit()
            return game_id
    
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
