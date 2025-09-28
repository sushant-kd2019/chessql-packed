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
        
        # Check for piece event queries
        if query.startswith('PIECE_EVENTS:'):
            return self._handle_piece_event_query(query)
        
        # Check if it's a regex query for moves (starts with /regex/)
        if query.startswith('/') and query.endswith('/'):
            regex_pattern = query[1:-1]  # Remove the slashes
            return self.db.search_moves(regex_pattern)
        
        # Check for SQL queries with piece event conditions
        if self._has_piece_event_condition(query):
            return self._handle_sql_with_piece_events(query)
        
        # Otherwise, treat as regular SQL query
        return self.db.execute_sql_query(query)
    
    def _handle_piece_event_query(self, query: str) -> List[Dict[str, Any]]:
        """Handle piece event queries."""
        # Parse query like: PIECE_EVENTS: knight exchanged before move 8
        # or: PIECE_EVENTS: queen not exchanged
        
        query = query[13:]  # Remove "PIECE_EVENTS:"
        
        if "not exchanged" in query.lower():
            # Find games where piece was not exchanged
            piece = self._extract_piece_from_query(query)
            if piece:
                return self.db.find_games_without_piece_exchange(piece)
        
        elif "exchanged" in query.lower():
            # Find games where piece was exchanged
            piece = self._extract_piece_from_query(query)
            max_move = self._extract_move_number_from_query(query)
            
            if piece:
                return self.db.find_piece_events(
                    piece=piece,
                    event_type='piece_exchange',
                    max_move=max_move
                )
        
        elif "sacrificed" in query.lower():
            # Find games where piece was sacrificed
            piece = self._extract_piece_from_query(query)
            max_move = self._extract_move_number_from_query(query)
            
            if piece:
                return self.db.find_piece_events(
                    piece=piece,
                    event_type='piece_sacrifice',
                    max_move=max_move
                )
        
        return []
    
    def _extract_piece_from_query(self, query: str) -> str:
        """Extract piece name from query."""
        piece_mapping = {
            'pawn': 'P',
            'bishop': 'B', 
            'knight': 'N',
            'rook': 'R',
            'queen': 'Q',
            'king': 'K'
        }
        
        query_lower = query.lower()
        for piece_name, piece_symbol in piece_mapping.items():
            if piece_name in query_lower:
                return piece_symbol
        
        return None
    
    def _extract_move_number_from_query(self, query: str) -> int:
        """Extract move number from query."""
        import re
        match = re.search(r'move (\d+)', query.lower())
        if match:
            return int(match.group(1))
        return None
    
    def _has_piece_event_condition(self, query: str) -> bool:
        """Check if SQL query contains piece event conditions."""
        import re
        
        # Look for patterns like "(knight was sacrificed)", "(queen was exchanged)", etc.
        piece_event_patterns = [
            r'\([^)]*\b(pawn|bishop|knight|rook|queen|king)\s+was\s+(exchanged|sacrificed|not\s+exchanged)',
            r'\([^)]*\b(exchanged|sacrificed|not\s+exchanged)\s+(pawn|bishop|knight|rook|queen|king)',
        ]
        
        for pattern in piece_event_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        return False
    
    def _handle_sql_with_piece_events(self, query: str) -> List[Dict[str, Any]]:
        """Handle SQL queries that contain piece event conditions."""
        import re
        
        # Extract the piece event condition
        piece_event_match = re.search(
            r'\(([^)]*\b(pawn|bishop|knight|rook|queen|king)\s+was\s+(exchanged|sacrificed|not\s+exchanged)[^)]*)\)',
            query, re.IGNORECASE
        )
        
        if not piece_event_match:
            # Try alternative pattern
            piece_event_match = re.search(
                r'\(([^)]*\b(exchanged|sacrificed|not\s+exchanged)\s+(pawn|bishop|knight|rook|queen|king)[^)]*)\)',
                query, re.IGNORECASE
            )
        
        if not piece_event_match:
            return []
        
        condition = piece_event_match.group(1)
        
        # Parse the condition
        piece = self._extract_piece_from_query(condition)
        event_type = self._extract_event_type_from_query(condition)
        max_move = self._extract_move_number_from_query(condition)
        
        if not piece or not event_type:
            return []
        
        # Build the SQL query by replacing the piece event condition
        if event_type == 'not exchanged':
            # Use NOT EXISTS for "not exchanged"
            subquery = f"""
                NOT EXISTS (
                    SELECT 1 FROM events e 
                    WHERE e.game_id = games.id 
                    AND e.piece = '{piece.upper()}' 
                    AND e.event_type = 'piece_exchange'
                )
            """
        else:
            # Use EXISTS for "exchanged" or "sacrificed"
            move_condition = f"AND e.move_number <= {max_move}" if max_move else ""
            subquery = f"""
                EXISTS (
                    SELECT 1 FROM events e 
                    WHERE e.game_id = games.id 
                    AND e.piece = '{piece.upper()}' 
                    AND e.event_type = '{event_type}'
                    {move_condition}
                )
            """
        
        # Replace the piece event condition with the subquery
        modified_query = query.replace(piece_event_match.group(0), subquery)
        
        return self.db.execute_sql_query(modified_query)
    
    def _extract_event_type_from_query(self, query: str) -> str:
        """Extract event type from query."""
        query_lower = query.lower()
        
        if 'not exchanged' in query_lower:
            return 'not exchanged'
        elif 'exchanged' in query_lower:
            return 'piece_exchange'
        elif 'sacrificed' in query_lower:
            return 'piece_sacrifice'
        
        return None
    
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
            
            # Piece event queries (old format)
            'PIECE_EVENTS: knight exchanged before move 8',
            'PIECE_EVENTS: queen not exchanged',
            'PIECE_EVENTS: rook exchanged',
            'PIECE_EVENTS: bishop sacrificed',
            
            # SQL-integrated piece event queries
            'SELECT black_elo FROM games WHERE (knight was sacrificed)',
            'SELECT white_player FROM games WHERE (queen was exchanged before move 10)',
            'SELECT * FROM games WHERE (rook was not exchanged)',
            'SELECT COUNT(*) FROM games WHERE (pawn was exchanged before move 5)',
        ]