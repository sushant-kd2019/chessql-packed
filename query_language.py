"""
Chess Query Language Module
Simplified query language for SQL queries on metadata and regex queries on moves.
"""

from typing import List, Dict, Any
from database import ChessDatabase
import re


class ChessQueryLanguage:
    """Simplified query language processor for chess game searches."""
    
    def __init__(self, db_path: str = "chess_games.db"):
        """Initialize the query language with database connection."""
        self.db = ChessDatabase(db_path)
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        query = query.strip()
        
        # Check if it's a regex query for moves (starts with /regex/)
        if query.startswith('/') and query.endswith('/'):
            regex_pattern = query[1:-1]  # Remove the slashes
            return self.db.search_moves(regex_pattern)
        
        # Otherwise, treat as SQL query
        return self.db.execute_sql_query(query)
    
    def get_query_examples(self) -> List[str]:
        """Get example queries for the user."""
        return [
            # SQL queries for metadata
            'SELECT white_player, black_player, result FROM games',
            'SELECT * FROM games WHERE white_player = "lecorvus"',
            'SELECT * FROM games WHERE result = "1-0"',
            'SELECT * FROM games WHERE eco_code = "B10"',
            'SELECT COUNT(*) as total_games FROM games',
            'SELECT white_player, COUNT(*) as games FROM games GROUP BY white_player',
            
            # Regex queries for moves
            '/e4.*c5/',  # Games with e4 followed by c5
            '/O-O/',     # Games with castling
            '/Qh5\\+/',   # Games with Qh5+
            '/1\\. e4/',  # Games starting with 1. e4
        ]