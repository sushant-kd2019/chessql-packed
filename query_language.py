"""
Chess Query Language Module
Simplified query language for SQL queries on metadata and regex queries on moves.
"""

from typing import List, Dict, Any, Optional
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
        
        # Pre-process player result conditions to convert them to explicit field queries
        query = self._preprocess_player_result_conditions(query)
        
        # Check for SQL queries with capture conditions
        if self._has_capture_condition(query):
            return self._handle_sql_with_captures(query)
        
        # Otherwise, treat as regular SQL query
        return self.db.execute_sql_query(query)
    
    def _preprocess_player_result_conditions(self, query: str) -> str:
        """Pre-process player result conditions to convert them to explicit field queries."""
        import re
        
        # Find all player result conditions and replace them
        def replace_player_result(match):
            condition = match.group(1)
            player_name = self._extract_player_name_from_query(condition)
            result_type = self._extract_result_type_from_query(condition)
            
            if not player_name or not result_type:
                return match.group(0)  # Return original if can't parse
            
            if result_type in ['won', 'win']:
                return f"((white_player = '{player_name}' AND white_result = 'win') OR (black_player = '{player_name}' AND black_result = 'win'))"
            elif result_type in ['lost', 'loss']:
                return f"((white_player = '{player_name}' AND white_result = 'loss') OR (black_player = '{player_name}' AND black_result = 'loss'))"
            elif result_type in ['drew', 'draw']:
                return f"((white_player = '{player_name}' AND white_result = 'draw') OR (black_player = '{player_name}' AND black_result = 'draw'))"
            else:
                return match.group(0)  # Return original if can't parse
        
        # Replace player result conditions
        query = re.sub(
            r'\(([^)]*["\']?(\w+)["\']?\s+(won|lost|drew|win|loss|draw)[^)]*)\)',
            replace_player_result,
            query,
            flags=re.IGNORECASE
        )
        
        return query
    
    def _has_capture_condition(self, query: str) -> bool:
        """Check if SQL query contains capture conditions."""
        import re
        
        # Look for patterns like "(queen captured queen)", "(knight captured rook)", etc.
        capture_patterns = [
            r'\([^)]*\b(pawn|bishop|knight|rook|queen|king)\s+captured\s+(pawn|bishop|knight|rook|queen|king)',
            r'\([^)]*\b(captured|took)\s+(pawn|bishop|knight|rook|queen|king)\s+with\s+(pawn|bishop|knight|rook|queen|king)',
            r'\([^)]*\b(pawn|bishop|knight|rook|queen|king)\s+(exchanged|sacrificed)',
            r'\([^)]*\b(exchanged|sacrificed)\s+(pawn|bishop|knight|rook|queen|king)',
        ]
        
        for pattern in capture_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        return False
    
    def _handle_sql_with_captures(self, query: str) -> List[Dict[str, Any]]:
        """Handle SQL queries that contain capture conditions."""
        import re
        
        # Check for exchange/sacrifice patterns first
        exchange_match = re.search(
            r'\(([^)]*\b(pawn|bishop|knight|rook|queen|king)\s+(exchanged|sacrificed)[^)]*)\)',
            query, re.IGNORECASE
        )
        
        if exchange_match:
            condition = exchange_match.group(1)
            piece = self._extract_piece_from_query(condition)
            event_type = self._extract_exchange_type_from_query(condition)
            move_condition = self._extract_move_condition_from_query(condition)
            
            if not piece or not event_type:
                return []
            
            # Build the SQL query for exchanges/sacrifices
            move_clause = ""
            if move_condition:
                if move_condition['type'] == 'before':
                    move_clause = f"AND c.move_number <= {move_condition['move']}"
                elif move_condition['type'] == 'after':
                    move_clause = f"AND c.move_number >= {move_condition['move']}"
            
            if event_type == 'exchanged':
                subquery = f"""
                    EXISTS (
                        SELECT 1 FROM captures c 
                        WHERE c.game_id = games.id 
                        AND c.capturing_piece = '{piece.upper()}' 
                        AND c.is_exchange = 1
                        {move_clause}
                    )
                """
            else:  # sacrificed
                subquery = f"""
                    EXISTS (
                        SELECT 1 FROM captures c 
                        WHERE c.game_id = games.id 
                        AND c.capturing_piece = '{piece.upper()}' 
                        AND c.is_sacrifice = 1
                        {move_clause}
                    )
                """
            
            # Replace the condition with the subquery
            modified_query = query.replace(exchange_match.group(0), subquery)
            return self.db.execute_sql_query(modified_query)
        
        # Handle specific piece capture patterns
        capture_match = re.search(
            r'\(([^)]*\b(pawn|bishop|knight|rook|queen|king)\s+captured\s+(pawn|bishop|knight|rook|queen|king)[^)]*)\)',
            query, re.IGNORECASE
        )
        
        if not capture_match:
            # Try alternative pattern
            capture_match = re.search(
                r'\(([^)]*\b(captured|took)\s+(pawn|bishop|knight|rook|queen|king)\s+with\s+(pawn|bishop|knight|rook|queen|king)[^)]*)\)',
                query, re.IGNORECASE
            )
        
        if not capture_match:
            return []
        
        condition = capture_match.group(1)
        
        # Parse the condition
        capturing_piece = self._extract_piece_from_query(condition)
        captured_piece = self._extract_captured_piece_from_query(condition)
        move_condition = self._extract_move_condition_from_query(condition)
        
        if not capturing_piece or not captured_piece:
            return []
        
        # Build the SQL query by replacing the capture condition
        move_clause = ""
        if move_condition:
            if move_condition['type'] == 'before':
                move_clause = f"AND c.move_number <= {move_condition['move']}"
            elif move_condition['type'] == 'after':
                move_clause = f"AND c.move_number >= {move_condition['move']}"
        
        subquery = f"""
            EXISTS (
                SELECT 1 FROM captures c 
                WHERE c.game_id = games.id 
                AND c.capturing_piece = '{capturing_piece.upper()}' 
                AND c.captured_piece = '{captured_piece.upper()}'
                {move_clause}
            )
        """
        
        # Replace the capture condition with the subquery
        modified_query = query.replace(capture_match.group(0), subquery)
        
        return self.db.execute_sql_query(modified_query)
    
    def _has_player_result_condition(self, query: str) -> bool:
        """Check if SQL query contains player result conditions."""
        import re
        
        # Look for patterns like "(lecorvus won)", "(player lost)", "(player drew)", etc.
        player_result_patterns = [
            r'\([^)]*["\']?(\w+)["\']?\s+(won|lost|drew|win|loss|draw)',
            r'\([^)]*\b(won|lost|drew|win|loss|draw)\s+["\']?(\w+)["\']?',
        ]
        
        for pattern in player_result_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        return False
    
    def _handle_sql_with_player_results(self, query: str) -> List[Dict[str, Any]]:
        """Handle SQL queries that contain player result conditions."""
        import re
        
        # If query contains AND/OR, we need to handle it differently
        if re.search(r'\b(AND|OR)\b', query, re.IGNORECASE):
            # For combined queries, just return empty and let SQL handle it
            return []
        
        # Extract the player result condition
        player_result_match = re.search(
            r'\(([^)]*["\']?(\w+)["\']?\s+(won|lost|drew|win|loss|draw)[^)]*)\)',
            query, re.IGNORECASE
        )
        
        if not player_result_match:
            # Try alternative pattern
            player_result_match = re.search(
                r'\(([^)]*\b(won|lost|drew|win|loss|draw)\s+["\']?(\w+)["\']?[^)]*)\)',
                query, re.IGNORECASE
            )
        
        if not player_result_match:
            return []
        
        condition = player_result_match.group(1)
        
        # Parse the condition
        player_name = self._extract_player_name_from_query(condition)
        result_type = self._extract_result_type_from_query(condition)
        
        if not player_name or not result_type:
            return []
        
        # Build the SQL query by replacing the player result condition
        if result_type in ['won', 'win']:
            subquery = f"""
                (white_player = '{player_name}' AND white_result = 'win') 
                OR (black_player = '{player_name}' AND black_result = 'win')
            """
        elif result_type in ['lost', 'loss']:
            subquery = f"""
                (white_player = '{player_name}' AND white_result = 'loss') 
                OR (black_player = '{player_name}' AND black_result = 'loss')
            """
        elif result_type in ['drew', 'draw']:
            subquery = f"""
                (white_player = '{player_name}' AND white_result = 'draw') 
                OR (black_player = '{player_name}' AND black_result = 'draw')
            """
        else:
            return []
        
        # Replace the player result condition with the subquery
        modified_query = query.replace(player_result_match.group(0), f"({subquery})")
        
        return self.db.execute_sql_query(modified_query)
    
    def _extract_player_name_from_query(self, query: str) -> str:
        """Extract player name from query."""
        import re
        
        # Look for quoted strings first
        quoted_match = re.search(r'"([^"]+)"', query)
        if quoted_match:
            return quoted_match.group(1)
        
        # Look for single quoted strings
        single_quoted_match = re.search(r"'([^']+)'", query)
        if single_quoted_match:
            return single_quoted_match.group(1)
        
        # Look for unquoted words (simplified)
        words = query.split()
        for word in words:
            if word.lower() not in ['won', 'lost', 'drew', 'win', 'loss', 'draw', 'and', 'or', 'where', '(', ')']:
                return word
        
        return None
    
    def _extract_result_type_from_query(self, query: str) -> str:
        """Extract result type from query (won/lost/drew)."""
        query_lower = query.lower()
        
        if 'won' in query_lower or 'win' in query_lower:
            return 'won'
        elif 'lost' in query_lower or 'loss' in query_lower:
            return 'lost'
        elif 'drew' in query_lower or 'draw' in query_lower:
            return 'drew'
        
        return None
    
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
    
    def _extract_exchange_type_from_query(self, query: str) -> str:
        """Extract exchange type from query (exchanged or sacrificed)."""
        query_lower = query.lower()
        
        if 'exchanged' in query_lower:
            return 'exchanged'
        elif 'sacrificed' in query_lower:
            return 'sacrificed'
        
        return None
    
    def _extract_captured_piece_from_query(self, query: str) -> str:
        """Extract captured piece from query."""
        piece_mapping = {
            'pawn': 'P',
            'bishop': 'B', 
            'knight': 'N',
            'rook': 'R',
            'queen': 'Q',
            'king': 'K'
        }
        
        query_lower = query.lower()
        
        # Split by "captured" and get the second part
        if 'captured' in query_lower:
            parts = query_lower.split('captured')
            if len(parts) > 1:
                captured_part = parts[1].strip()
                for piece_name, piece_symbol in piece_mapping.items():
                    if piece_name in captured_part:
                        return piece_symbol
        
        return None
    
    def _extract_move_condition_from_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract move condition from query (before/after move N)."""
        import re
        
        query_lower = query.lower()
        
        # Look for "before move N" pattern
        before_match = re.search(r'before\s+move\s+(\d+)', query_lower)
        if before_match:
            return {
                'type': 'before',
                'move': int(before_match.group(1))
            }
        
        # Look for "after move N" pattern
        after_match = re.search(r'after\s+move\s+(\d+)', query_lower)
        if after_match:
            return {
                'type': 'after',
                'move': int(after_match.group(1))
            }
        
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
            
            # Capture queries (with position tracking)
            'SELECT white_player FROM games WHERE (queen captured queen)',
            'SELECT black_player FROM games WHERE (knight captured rook)',
            'SELECT COUNT(*) FROM games WHERE (bishop captured bishop)',
            'SELECT * FROM games WHERE (pawn captured queen)',
            
            # Exchange and sacrifice queries
            'SELECT white_player FROM games WHERE (queen exchanged)',
            'SELECT black_player FROM games WHERE (knight sacrificed)',
            'SELECT COUNT(*) FROM games WHERE (pawn exchanged before move 10)',
            'SELECT * FROM games WHERE (rook sacrificed after move 15)',
            
            # Player result queries
            'SELECT white_player, black_player FROM games WHERE (lecorvus won)',
            'SELECT COUNT(*) FROM games WHERE (lecorvus lost)',
            'SELECT * FROM games WHERE (lecorvus drew)',
            'SELECT white_player FROM games WHERE (lecorvus won) AND (queen sacrificed)',
            'SELECT '
            
            # Capture queries with move numbers
            'SELECT white_player FROM games WHERE (queen captured bishop before move 20)',
            'SELECT black_player FROM games WHERE (knight captured pawn after move 10)',
            'SELECT COUNT(*) FROM games WHERE (bishop captured bishop before move 15)',
            'SELECT * FROM games WHERE (pawn captured queen after move 5)',
        ]