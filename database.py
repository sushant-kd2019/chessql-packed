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
            
            # Create games table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pgn_text TEXT NOT NULL,
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create moves table for detailed move analysis
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS moves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER,
                    move_number INTEGER,
                    white_move TEXT,
                    black_move TEXT,
                    position_fen TEXT,
                    FOREIGN KEY (game_id) REFERENCES games (id)
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_white_player ON games(white_player)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_black_player ON games(black_player)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_result ON games(result)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_eco_code ON games(eco_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_played ON games(date_played)")
            
            conn.commit()
    
    def insert_game(self, pgn_data: Dict[str, Any]) -> int:
        """Insert a single game into the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO games (
                    pgn_text, white_player, black_player, result, date_played,
                    event, site, round, eco_code, opening, time_control
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pgn_data.get('pgn_text', ''),
                pgn_data.get('white_player', ''),
                pgn_data.get('black_player', ''),
                pgn_data.get('result', ''),
                pgn_data.get('date_played', ''),
                pgn_data.get('event', ''),
                pgn_data.get('site', ''),
                pgn_data.get('round', ''),
                pgn_data.get('eco_code', ''),
                pgn_data.get('opening', ''),
                pgn_data.get('time_control', '')
            ))
            
            game_id = cursor.lastrowid
            
            # Insert moves if provided
            if 'moves' in pgn_data:
                for move_data in pgn_data['moves']:
                    cursor.execute("""
                        INSERT INTO moves (game_id, move_number, white_move, black_move, position_fen)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        game_id,
                        move_data.get('move_number', 0),
                        move_data.get('white_move', ''),
                        move_data.get('black_move', ''),
                        move_data.get('position_fen', '')
                    ))
            
            conn.commit()
            return game_id
    
    def get_games(self, filters: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve games from the database with optional filters."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM games"
            params = []
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    if value is not None:
                        if key in ['white_player', 'black_player', 'result', 'eco_code']:
                            conditions.append(f"{key} = ?")
                            params.append(value)
                        elif key == 'date_from':
                            conditions.append("date_played >= ?")
                            params.append(value)
                        elif key == 'date_to':
                            conditions.append("date_played <= ?")
                            params.append(value)
                        elif key == 'opening_contains':
                            conditions.append("opening LIKE ?")
                            params.append(f"%{value}%")
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDER BY created_at DESC LIMIT {limit}"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_game_by_id(self, game_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific game by its ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM games WHERE id = ?", (game_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_moves_for_game(self, game_id: int) -> List[Dict[str, Any]]:
        """Get all moves for a specific game."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM moves 
                WHERE game_id = ? 
                ORDER BY move_number
            """, (game_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def search_games(self, query: str) -> List[Dict[str, Any]]:
        """Search games using a text query."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            search_query = f"""
                SELECT * FROM games 
                WHERE pgn_text LIKE ? 
                   OR white_player LIKE ? 
                   OR black_player LIKE ? 
                   OR opening LIKE ?
                ORDER BY created_at DESC
            """
            
            search_term = f"%{query}%"
            cursor.execute(search_query, (search_term, search_term, search_term, search_term))
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
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
